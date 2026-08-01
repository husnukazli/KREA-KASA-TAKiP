import streamlit as st
import hashlib
import time
import random
import pandas as pd
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Sayfa Ayarları
st.set_page_config(page_title="Ticari Yönetim Sistemi", page_icon="💼", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .stDataFrame {font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
    .css-1d391kg {padding-top: 1rem;}
    h1, h2, h3 {color: #1E3A8A; font-weight: 600;}
    </style>
""", unsafe_allow_html=True)

# --- OTURUM YÖNETİMİ ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": "", "user_id": ""})

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANI
# ==========================================
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>Ticari Sistem Girişi</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("Sisteme Giriş")
        login_email = st.text_input("E-posta Adresi", key="log_email")
        login_pass = st.text_input("Şifre", type="password", key="log_pass")
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            clean_email = login_email.strip().lower()
            clean_pass = login_pass.strip()
            try:
                response = supabase.table("app_users").select("*").eq("email", clean_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(clean_pass):
                    u = users[0]
                    st.session_state.update({
                        "logged_in": True, 
                        "email": clean_email, 
                        "ad_soyad": u.get("ad_soyad", clean_email), 
                        "role": u["role"],
                        "user_id": u["id"]
                    })
                    st.success("Doğrulama başarılı. Sisteme giriliyor...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Kimlik doğrulama hatası! Bilgilerinizi kontrol ediniz.")
            except Exception as e:
                st.error(f"Sistem Hatası: {e}")

    with col2:
        st.subheader("Yeni Kullanıcı Kaydı")
        reg_ad_soyad = st.text_input("Ad Soyad", key="reg_name")
        reg_email = st.text_input("E-posta Adresi", key="reg_email")
        reg_pass = st.text_input("Şifre", type="password", key="reg_pass")
        if st.button("Kayıt Talebi Oluştur", use_container_width=True):
            clean_reg_email = reg_email.strip().lower()
            clean_reg_pass = reg_pass.strip()
            clean_reg_ad = reg_ad_soyad.strip()
            
            if clean_reg_email and clean_reg_pass and clean_reg_ad:
                try:
                    existing = supabase.table("app_users").select("*").eq("email", clean_reg_email).execute()
                    if existing.data:
                        st.warning("Bu adres sistemde kayıtlı.")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": clean_reg_ad, 
                            "email": clean_reg_email, 
                            "password": hash_password(clean_reg_pass), 
                            "role": "beklemede"
                        }).execute()
                        st.success("Kayıt alındı. Yönetici onayı bekleniyor.")
                except Exception as e:
                    st.error(f"İşlem Hatası: {e}")
            else:
                st.error("Tüm alanlar zorunludur.")
                
    st.write("---")
    with st.expander("Yönetici (Sistem) Girişi"):
        admin_pass = st.text_input("Yönetici Şifresi", type="password", key="admin_pass")
        if st.button("Sistem Yöneticisi Olarak Gir"):
            if admin_pass == "admin123": 
                st.session_state.update({
                    "logged_in": True, 
                    "ad_soyad": "Sistem Yöneticisi", 
                    "email": "admin", 
                    "role": "admin",
                    "user_id": "admin_id"
                })
                st.rerun()
            else:
                 st.error("Yetkisiz giriş denemesi!")
    st.stop()

# ==========================================
# 2. ANA UYGULAMA & YAN MENÜ (NAVIGATION)
# ==========================================
with st.sidebar:
    st.markdown(f"### {st.session_state['ad_soyad']}")
    display_role = "Yönetici" if st.session_state['role'] == "admin" else "Kullanıcı" if st.session_state['role'] == "onaylı" else "Beklemede"
    st.caption(f"Yetki Grubu: {display_role}")
    st.divider()
    
    menu_secenekleri = ["Cari Hareketler & Fişler", "Tahsilat ve Ödeme (Kasa)", "Cari Kart Tanımları", "Kasa Tanımları", "Profil ve Ayarlar"]
    if st.session_state["role"] == "admin":
        menu_secenekleri.insert(0, "Yönetim Paneli (Admin)")
        
    secili_menu = st.radio("Sistem Menüsü", menu_secenekleri)
    
    st.divider()
    if st.button("Güvenli Çıkış", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ==========================================
# MENÜ: KASA TANIMLARI
# ==========================================
if secili_menu == "Kasa Tanımları":
    if st.session_state["role"] not in ["onaylı", "admin"]:
        st.warning("Bu ekranı görüntüleme yetkiniz yok.")
    else:
        st.header("Kasa ve Banka Tanımları")
        st.write("Sistemdeki nakit kasaları veya banka hesaplarını buradan yönetebilirsiniz.")
        
        tab_liste, tab_yeni = st.tabs(["Kasa Listesi", "Yeni Kasa Aç"])
        
        with tab_yeni:
            with st.form("yeni_kasa_formu", clear_on_submit=True):
                k_kodu = st.text_input("Kasa Kodu (Örn: K-001, B-001)")
                k_adi = st.text_input("Kasa / Banka Adı (Örn: Merkez TL Kasası, Akbank USD)")
                k_doviz = st.selectbox("Döviz Cinsi", ["TL", "USD", "EUR"])
                k_aciklama = st.text_area("Açıklama")
                
                if st.form_submit_button("Kasayı Kaydet", type="primary"):
                    if not k_kodu or not k_adi:
                        st.error("Kasa Kodu ve Adı zorunludur!")
                    else:
                        try:
                            supabase.table("kasalar").insert({
                                "kasa_kodu": k_kodu.strip(),
                                "kasa_adi": k_adi.strip(),
                                "doviz_tipi": k_doviz,
                                "aciklama": k_aciklama.strip(),
                                "olusturan": st.session_state["ad_soyad"]
                            }).execute()
                            st.success(f"[{k_kodu}] kodlu kasa başarıyla oluşturuldu.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt Hatası: {e}")

        with tab_liste:
            try:
                kasalar_res = supabase.table("kasalar").select("*").order("created_at", desc=True).execute()
                if kasalar_res.data:
                    df_kasalar = pd.DataFrame(kasalar_res.data)[["kasa_kodu", "kasa_adi", "doviz_tipi", "aciklama"]]
                    df_kasalar.columns = ["Kodu", "Kasa Adı", "Döviz", "Açıklama"]
                    st.dataframe(df_kasalar, use_container_width=True, hide_index=True)
                else:
                    st.info("Sistemde kayıtlı kasa bulunmamaktadır.")
            except Exception as e:
                st.error(f"Veri çekme hatası: {e}")

# ==========================================
# MENÜ: CARİ KART TANIMLARI
# ==========================================
elif secili_menu == "Cari Kart Tanımları":
    if st.session_state["role"] not in ["onaylı", "admin"]:
        st.warning("Bu ekranı görüntüleme yetkiniz yok.")
    else:
        st.header("Cari Kart Tanımları")
        
        tab_liste, tab_yeni = st.tabs(["Cari Listesi", "Yeni Cari Kart Aç"])
        
        with tab_yeni:
            with st.form("yeni_cari_formu", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    c_kodu = st.text_input("Cari Kodu (Örn: C-001)")
                    c_unvan = st.text_input("Cari Ünvanı / Adı Soyadı")
                    c_vkn = st.text_input("VKN / TCKN")
                    c_vergid = st.text_input("Vergi Dairesi")
                with col2:
                    c_doviz = st.selectbox("Döviz Cinsi", ["TL", "USD", "EUR"])
                    c_tel = st.text_input("Telefon")
                    c_email = st.text_input("E-posta Adresi")
                    
                c_adres = st.text_area("Açık Adres")
                c_not = st.text_area("Özel Notlar (Vade anlaşması vb.)")
                
                if st.form_submit_button("Cari Kartı Kaydet", type="primary"):
                    if not c_kodu or not c_unvan:
                        st.error("Cari Kodu ve Ünvanı zorunludur!")
                    else:
                        try:
                            supabase.table("cariler").insert({
                                "cari_kodu": c_kodu.strip(),
                                "unvan": c_unvan.strip(),
                                "vkn_tckn": c_vkn.strip(),
                                "vergi_dairesi": c_vergid.strip(),
                                "doviz_tipi": c_doviz,
                                "telefon": c_tel.strip(),
                                "email": c_email.strip(),
                                "adres": c_adres.strip(),
                                "notlar": c_not.strip(),
                                "olusturan": st.session_state["ad_soyad"]
                            }).execute()
                            st.success(f"[{c_kodu}] kodlu cari başarıyla oluşturuldu.")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Kayıt Hatası (Kod benzersiz olmalıdır): {e}")

        with tab_liste:
            try:
                cariler_res = supabase.table("cariler").select("*").order("created_at", desc=True).execute()
                if cariler_res.data:
                    df_cariler = pd.DataFrame(cariler_res.data)
                    df_gosterim = df_cariler[["cari_kodu", "unvan", "doviz_tipi", "vkn_tckn", "telefon", "email"]]
                    df_gosterim.columns = ["Kodu", "Ünvan / İsim", "Döviz", "VKN/TCKN", "Telefon", "E-Posta"]
                    st.dataframe(df_gosterim, use_container_width=True, hide_index=True)
                else:
                    st.info("Sistemde kayıtlı cari bulunmamaktadır.")
            except Exception as e:
                st.error(f"Veri çekme hatası: {e}")

# ==========================================
# MENÜ: TAHSİLAT VE ÖDEME
# ==========================================
elif secili_menu == "Tahsilat ve Ödeme (Kasa)":
    st.header("Hızlı Tahsilat ve Ödeme Ekranı")
    st.write("Carilerden gelen ödemeleri (Tahsilat) veya carilere yapılan ödemeleri (Tediye) buradan işleyebilirsiniz.")
    
    cariler = supabase.table("cariler").select("id, cari_kodu, unvan, doviz_tipi").execute().data
    kasalar = supabase.table("kasalar").select("id, kasa_kodu, kasa_adi, doviz_tipi").execute().data
    
    if not cariler or not kasalar:
        st.warning("İşlem yapabilmek için sistemde en az bir Cari Kart ve bir Kasa/Banka tanımı olmalıdır.")
    else:
        islem_tipi = st.radio("İşlem Türü Seçiniz", ["Tahsilat Yap (Kasaya Para Girişi)", "Ödeme Yap (Kasadan Para Çıkışı)"], horizontal=True)
        
        with st.form("tahsilat_odeme_formu"):
            c1, c2 = st.columns(2)
            cari_opsiyonlari = {f"{c['unvan']} ({c['doviz_tipi']})": c for c in cariler}
            kasa_opsiyonlari = {f"{k['kasa_adi']} ({k['doviz_tipi']})": k for k in kasalar}
            
            with c1:
                secilen_cari = st.selectbox("İlgili Cari", options=list(cari_opsiyonlari.keys()))
            with c2:
                secilen_kasa = st.selectbox("İşlem Yapılacak Kasa/Banka", options=list(kasa_opsiyonlari.keys()))
                
            tutar = st.number_input("Tutar", min_value=0.01, format="%.2f")
            aciklama = st.text_input("Açıklama")
            belge_no = st.text_input("Makbuz / Dekont No")
            
            submit_btn = st.form_submit_button("İşlemi Kaydet", type="primary")
            
            if submit_btn:
                cari_id = cari_opsiyonlari[secilen_cari]["id"]
                kasa_id = kasa_opsiyonlari[secilen_kasa]["id"]
                
                if "Tahsilat" in islem_tipi:
                    islem_yonu = "Alacak" 
                    evrak_tipi = "Nakit Tahsilat"
                else:
                    islem_yonu = "Borç" 
                    evrak_tipi = "Nakit Tediye (Ödeme)"
                    
                try:
                    supabase.table("islemler").insert({
                        "cari_id": cari_id,
                        "kasa_id": kasa_id,
                        "evrak_tipi": evrak_tipi,
                        "islem_yonu": islem_yonu,
                        "tutar": tutar,
                        "belge_no": belge_no,
                        "aciklama": aciklama.strip(),
                        "isleyen_kisi": st.session_state["ad_soyad"]
                    }).execute()
                    st.success("İşlem başarıyla kaydedildi!")
                except Exception as e:
                    st.error(f"Hata oluştu: {e}")

# ==========================================
# MENÜ: CARİ HAREKETLER & FİŞLER
# ==========================================
elif secili_menu == "Cari Hareketler & Fişler":
    st.header("Cari Hareket Föyü (Ekstre)")
    
    cariler_res = supabase.table("cariler").select("id, cari_kodu, unvan, doviz_tipi").order("unvan").execute()
    cariler_listesi = cariler_res.data
    
    if not cariler_listesi:
        st.warning("İşlem yapabilmek için önce cari açmalısınız.")
    else:
        cari_opsiyonlari = {f"{c['cari_kodu']} - {c['unvan']} ({c['doviz_tipi']})": c for c in cariler_listesi}
        secilen_cari_etiketi = st.selectbox("Hareketleri Görüntülenecek Cariyi Seçin:", ["Seçiniz..."] + list(cari_opsiyonlari.keys()))
        
        if secilen_cari_etiketi != "Seçiniz...":
            aktif_cari = cari_opsiyonlari[secilen_cari_etiketi]
            cari_id = aktif_cari["id"]
            cari_doviz = aktif_cari["doviz_tipi"]
            
            st.write("---")
            
            islemler_res = supabase.table("islemler").select("*").eq("cari_id", cari_id).order("created_at", desc=False).execute()
            islemler = islemler_res.data
            
            toplam_borc = 0.0
            toplam_alacak = 0.0
            ekstre_listesi = []
            revize_opsiyonlari = {}
            
            for islem in islemler:
                tutar = float(islem["tutar"])
                if islem["islem_yonu"] == "Borç":
                    toplam_borc += tutar
                    satir_borc = tutar
                    satir_alacak = 0.0
                else:
                    toplam_alacak += tutar
                    satir_borc = 0.0
                    satir_alacak = tutar
                    
                bakiye = toplam_borc - toplam_alacak
                
                gorunum_tarih = islem["created_at"][:16].replace("T", " ")
                revize_opsiyonlari[f"{gorunum_tarih} | {islem['evrak_tipi']} | {tutar} {cari_doviz}"] = islem
                
                ekstre_listesi.append({
                    "ID": islem["id"],
                    "Tarih": gorunum_tarih,
                    "Evrak Tipi": islem["evrak_tipi"],
                    "Belge No": islem.get("belge_no", "-"),
                    "B/A": islem["islem_yonu"],
                    "Borç": f"{satir_borc:,.2f}",
                    "Alacak": f"{satir_alacak:,.2f}",
                    "Bakiye": f"{bakiye:,.2f}",
                    "Açıklama": islem.get("aciklama", ""),
                    "İşleyen": islem["isleyen_kisi"]
                })
            
            guncel_bakiye = toplam_borc - toplam_alacak
            bakiye_durumu = "Borçlu (Bizden Alacaklı)" if guncel_bakiye > 0 else "Alacaklı (Bize Borçlu)" if guncel_bakiye < 0 else "Kapandı"
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Cari Borç (Bize Çalışan)", f"{toplam_borc:,.2f} {cari_doviz}")
            m2.metric("Cari Alacak (Bizden Çıkan)", f"{toplam_alacak:,.2f} {cari_doviz}")
            m3.metric("Güncel Bakiye", f"{abs(guncel_bakiye):,.2f} {cari_doviz}")
            m4.metric("Bakiye Durumu", bakiye_durumu)
            
            with st.expander("➕ Sadece Fatura / Devir Fişi Gir (Kasa Etkilenmez)"):
                c1, c2 = st.columns(2)
                f_evrak = c1.selectbox("Evrak Tipi", ["Satış Faturası (Cariyi Borçlandır)", "Alış Faturası (Cariyi Alacaklandır)", "Açılış/Devir (Borç)", "Açılış/Devir (Alacak)"])
                f_tutar = c2.number_input(f"Tutar ({cari_doviz})", min_value=0.0, step=10.0, format="%.2f")
                
                f_belge = st.text_input("Fatura No")
                f_aciklama = st.text_input("Açıklama / İşlem Detayı")
                
                if st.button("Fişi İşle", type="primary"):
                    if f_tutar > 0:
                        islem_yonu = "Borç" if "Borç" in f_evrak or "Satış" in f_evrak else "Alacak"
                        temiz_evrak = "Fatura" if "Fatura" in f_evrak else "Devir"
                        
                        supabase.table("islemler").insert({
                            "cari_id": cari_id,
                            "evrak_tipi": temiz_evrak,
                            "islem_yonu": islem_yonu,
                            "tutar": f_tutar,
                            "belge_no": f_belge,
                            "aciklama": f_aciklama.strip(),
                            "isleyen_kisi": st.session_state["ad_soyad"]
                        }).execute()
                        st.success("İşlem kaydedildi!")
                        time.sleep(1)
                        st.rerun()

            st.write("#### Hareket Dökümü")
            if ekstre_listesi:
                ekstre_listesi.reverse()
                st.dataframe(pd.DataFrame(ekstre_listesi), use_container_width=True, hide_index=True)
                
                with st.expander("✏️ Seçili İşlemi Revize Et veya Sil"):
                    st.info("Aşağıdan bir işlem seçerek tutar veya açıklama gibi detaylarını güncelleyebilirsiniz.")
                    secili_revize_etiketi = st.selectbox("Düzenlenecek İşlemi Seçin:", ["Seçiniz..."] + list(revize_opsiyonlari.keys()))
                    
                    if secili_revize_etiketi != "Seçiniz...":
                        hedef_islem = revize_opsiyonlari[secili_revize_etiketi]
                        
                        with st.form("revize_formu"):
                            r_tutar = st.number_input("Tutar", value=float(hedef_islem["tutar"]))
                            r_belge = st.text_input("Belge No", value=hedef_islem.get("belge_no") or "")
                            r_aciklama = st.text_input("Açıklama", value=hedef_islem.get("aciklama") or "")
                            
                            c_btn1, c_btn2 = st.columns(2)
                            if c_btn1.form_submit_button("Güncelle", type="primary"):
                                supabase.table("islemler").update({
                                    "tutar": r_tutar,
                                    "belge_no": r_belge,
                                    "aciklama": r_aciklama
                                }).eq("id", hedef_islem["id"]).execute()
                                st.success("İşlem güncellendi!")
                                time.sleep(1)
                                st.rerun()
                                
                        if st.button("Sil (İptal Et)", type="secondary", key="del_btn"):
                            supabase.table("islemler").delete().eq("id", hedef_islem["id"]).execute()
                            st.warning("İşlem silindi!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("Bu cariye ait finansal hareket bulunmamaktadır.")

# ==========================================
# MENÜ: PROFİL VE AYARLAR
# ==========================================
elif secili_menu == "Profil ve Ayarlar":
    st.header("Kullanıcı Profili")
    
    if st.session_state["email"] == "admin":
        st.info("Sistem Yöneticisi profili teknik olarak sabittir. Güncelleme yapılamaz.")
    else:
        try:
            user_res = supabase.table("app_users").select("*").eq("id", st.session_state["user_id"]).execute()
            if user_res.data:
                u_info = user_res.data[0]
                
                with st.form("profil_formu"):
                    st.subheader("Kurumsal Bilgiler")
                    p_ad = st.text_input("Ad Soyad", value=u_info.get("ad_soyad") or "")
                    p_tel = st.text_input("Telefon", value=u_info.get("telefon") or "")
                    p_pozisyon = st.text_input("Görev/Pozisyon", value=u_info.get("pozisyon") or "")
                    
                    st.divider()
                    st.subheader("Güvenlik (Şifre Değişimi)")
                    p_sifre = st.text_input("Yeni Şifre (Boş bırakırsanız değişmez)", type="password")
                    p_sifre_tekrar = st.text_input("Yeni Şifre Tekrar", type="password")
                    
                    if st.form_submit_button("Bilgileri Kaydet", type="primary"):
                        if p_sifre and p_sifre != p_sifre_tekrar:
                            st.error("Şifreler uyuşmuyor!")
                        else:
                            up_data = {
                                "ad_soyad": (p_ad or "").strip(),
                                "telefon": (p_tel or "").strip(),
                                "pozisyon": (p_pozisyon or "").strip()
                            }
                            if p_sifre.strip():
                                up_data["password"] = hash_password(p_sifre.strip())
                            
                            supabase.table("app_users").update(up_data).eq("id", st.session_state["user_id"]).execute()
                            st.session_state["ad_soyad"] = (p_ad or "").strip()
                            st.success("Profil güncellendi.")
                            time.sleep(1)
                            st.rerun()
        except Exception as e:
            st.error(f"Profil hatası: {e}")

# ==========================================
# MENÜ: YÖNETİM PANELİ (SADECE ADMIN)
# ==========================================
elif secili_menu == "Yönetim Paneli (Admin)":
    st.header("Sistem Yönetim Paneli")
    
    tab_ozet, tab_kullanici, tab_test = st.tabs(["Mali Özet (Döviz Bazlı)", "Kullanıcı ve Yetki Yönetimi", "🧪 Test & Simülasyon Araçları"])
    
    with tab_ozet:
        cariler_db = supabase.table("cariler").select("id, doviz_tipi").execute().data
        islemler_db = supabase.table("islemler").select("cari_id, islem_yonu, tutar").execute().data
        
        if cariler_db and islemler_db:
            ozet = {"TL": 0.0, "USD": 0.0, "EUR": 0.0}
            cari_doviz_map = {c["id"]: c["doviz_tipi"] for c in cariler_db}
            
            for ism in islemler_db:
                c_id = ism.get("cari_id")
                if c_id in cari_doviz_map:
                    d_tip = cari_doviz_map[c_id]
                    t = float(ism["tutar"])
                    if ism["islem_yonu"] == "Borç":
                        ozet[d_tip] += t  
                    else:
                        ozet[d_tip] -= t  
                        
            st.write("#### Genel Şirket Bakiyesi (Müşteri/Tedarikçi Net Durum)")
            st.caption("Pozitif değerler piyasadan toplam alacağınızı, negatif değerler piyasaya olan toplam borcunuzu temsil eder.")
            
            k1, k2, k3 = st.columns(3)
            k1.metric("TL Net Durum", f"{ozet['TL']:,.2f} TL")
            k2.metric("USD Net Durum", f"{ozet['USD']:,.2f} USD")
            k3.metric("EUR Net Durum", f"{ozet['EUR']:,.2f} EUR")
        else:
            st.info("Hesaplanacak yeterli veri bulunamadı.")

    with tab_kullanici:
        bekleyenler = supabase.table("app_users").select("*").eq("role", "beklemede").execute().data
        if bekleyenler:
            st.warning("Onay Bekleyen Kullanıcılar")
            for b in bekleyenler:
                c1, c2 = st.columns([4,1])
                c1.write(f"{b['ad_soyad']} ({b['email']})")
                if c2.button("Yetki Ver", key=f"onay_{b['id']}"):
                    supabase.table("app_users").update({"role":"onaylı"}).eq("id", b["id"]).execute()
                    st.rerun()
                    
        st.divider()
        st.write("#### Kayıtlı Kullanıcılar ve Şifre Sıfırlama")
        all_users = supabase.table("app_users").select("*").execute().data
        if all_users:
            secili_u_mail = st.selectbox("Kullanıcı Seçin", [u["email"] for u in all_users])
            secili_u = next(u for u in all_users if u["email"] == secili_u_mail)
            
            st.write(f"**İsim:** {secili_u.get('ad_soyad')} | **Yetki:** {secili_u['role']}")
            if st.button("Bu kullanıcının şifresini '1234' olarak sıfırla", type="primary"):
                temiz_mail = secili_u["email"].strip().lower()
                supabase.table("app_users").update({
                    "password": hash_password("1234"),
                    "email": temiz_mail
                }).eq("id", secili_u["id"]).execute()
                st.success("Şifre sıfırlandı!")
                time.sleep(1.5)
                st.rerun()
                
    with tab_test:
        st.write("#### 🧪 Genişletilmiş Otomatik Veri Simülasyonu")
        st.write("Sistemi test etmek için tek tıkla **Çoklu Kasalar (TL, USD, EUR)**, **Farklı Dövizlerde Cariler** ve bu parametreleri tam kullanan **zenginleştirilmiş finansal hareketler ve örnek belgeler** üretin.")
        
        if st.button("🚀 Kapsamlı Test Verilerini Yükle", type="secondary"):
            with st.spinner("Çoklu Kasalar, Dövizli Cariler ve Belgeli Entegre Hareketler Üretiliyor..."):
                
                # 1. Kullanıcılar
                dummy_users = [
                    {"ad_soyad": "Test Finans Sorumlusu", "email": "finans@sistem.com", "password": hash_password("1234"), "role": "onaylı", "pozisyon": "Muhasebe Uzmanı"},
                    {"ad_soyad": "Test Satış Yetkilisi", "email": "satis@sistem.com", "password": hash_password("1234"), "role": "onaylı", "pozisyon": "Satış Temsilcisi"}
                ]
                for du in dummy_users:
                    try:
                        supabase.table("app_users").insert(du).execute()
                    except:
                        pass 
                
                # 2. Çoklu Kasalar (TL, USD, EUR)
                dummy_kasalar = [
                    {"kasa_kodu": f"K-TL-{random.randint(100,999)}", "kasa_adi": "Merkez TL Kasası", "doviz_tipi": "TL", "aciklama": "Nakit TL işlemler için ana kasa", "olusturan": "Sistem Admin"},
                    {"kasa_kodu": f"K-USD-{random.randint(100,999)}", "kasa_adi": "Merkez USD Kasası", "doviz_tipi": "USD", "aciklama": "Dövizli tahsilat kasası", "olusturan": "Sistem Admin"},
                    {"kasa_kodu": f"K-EUR-{random.randint(100,999)}", "kasa_adi": "Avrupa EUR Banka Hesabı", "doviz_tipi": "EUR", "aciklama": "İthalat ihracat EUR hesabı", "olusturan": "Sistem Admin"}
                ]
                for dk in dummy_kasalar:
                    try:
                        supabase.table("kasalar").insert(dk).execute()
                    except:
                        pass

                # 3. Çoklu Cariler (TL, USD, EUR)
                dummy_cariler = [
                    {"cari_kodu": f"C-TL-{random.randint(100,999)}", "unvan": "Mavi Bilişim Teknolojileri A.Ş.", "doviz_tipi": "TL", "vergi_dairesi": "Bornova", "vkn_tckn": "11111111111", "olusturan": "Sistem Admin"},
                    {"cari_kodu": f"C-USD-{random.randint(100,999)}", "unvan": "Global Tech Supply Inc.", "doviz_tipi": "USD", "vergi_dairesi": "Yabancı", "vkn_tckn": "22222222222", "olusturan": "Sistem Admin"},
                    {"cari_kodu": f"C-EUR-{random.randint(100,999)}", "unvan": "Eurotrade GmbH", "doviz_tipi": "EUR", "vergi_dairesi": "Dış Ticaret", "vkn_tckn": "33333333333", "olusturan": "Sistem Admin"},
                    {"cari_kodu": f"C-TL2-{random.randint(100,999)}", "unvan": "Anadolu Lojistik ve Nakliyat", "doviz_tipi": "TL", "vergi_dairesi": "Konak", "vkn_tckn": "44444444444", "olusturan": "Sistem Admin"}
                ]
                for dc in dummy_cariler:
                    try:
                        supabase.table("cariler").insert(dc).execute()
                    except:
                        pass
                
                # 4. Veritabanından ID'leri çekerek akıllı ve entegre işlemler üretelim (Belge detayları eklendi)
                cariler_db_test = supabase.table("cariler").select("id, doviz_tipi").execute().data
                kasalar_db_test = supabase.table("kasalar").select("id, doviz_tipi").execute().data
                
                if cariler_db_test and kasalar_db_test:
                    evrak_tipleri = ["Fatura", "Nakit Tahsilat", "Nakit Tediye (Ödeme)", "Devir"]
                    
                    for _ in range(20): 
                        secili_cari = random.choice(cariler_db_test)
                        
                        uygun_kasalar = [k for k in kasalar_db_test if k["doviz_tipi"] == secili_cari["doviz_tipi"]]
                        secili_kasa = random.choice(uygun_kasalar) if uygun_kasalar else random.choice(kasalar_db_test)
                        
                        evrak = random.choice(evrak_tipleri)
                        
                        if "Tahsilat" in evrak:
                            islem_yonu = "Alacak"
                        elif "Tediye" in evrak:
                            islem_yonu = "Borç"
                        else:
                            islem_yonu = random.choice(["Borç", "Alacak"])
                        
                        rastgele_id = random.randint(10000, 99999)
                        supabase.table("islemler").insert({
                            "cari_id": secili_cari["id"],
                            "kasa_id": secili_kasa["id"],
                            "evrak_tipi": evrak,
                            "islem_yonu": islem_yonu,
                            "tutar": round(random.uniform(2500, 75000), 2),
                            "belge_no": f"TEST-DEC-{rastgele_id}",
                            "aciklama": f"Otomatik simülasyon [{evrak}] kaydı.",
                            "isleyen_kisi": "Test Robotu",
                            "dosya_url": f"https://ornek-depolama.com/belgeler/dekont_{rastgele_id}.pdf",
                            "dosya_path": f"belgeler/dekont_{rastgele_id}.pdf"
                        }).execute()
                
                st.success("✅ Çoklu kasalar, dövizli cariler, belgeli ve entegre test hareketleri başarıyla oluşturuldu!")
                time.sleep(2)
                st.rerun()
