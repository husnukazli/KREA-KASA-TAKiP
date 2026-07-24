import streamlit as st
import hashlib
import time
from supabase import create_client, Client
import pandas as pd

# --- SUPABASE BAĞLANTISI ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Sayfa Ayarları (Tam ekran, resmi başlık)
st.set_page_config(page_title="Ticari Yönetim Sistemi", layout="wide", initial_sidebar_state="expanded")

# Özel CSS ile daha sade ve kurumsal görünüm
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
        st.subheader("Yeni Personel Kaydı")
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
    display_role = "Yönetici" if st.session_state['role'] == "admin" else "Personel" if st.session_state['role'] == "onaylı" else "Beklemede"
    st.caption(f"Yetki Grubu: {display_role}")
    st.divider()
    
    # Modern Navigasyon
    menu_secenekleri = ["Cari Hareketler & Fişler", "Cari Kart Tanımları", "Profil ve Ayarlar"]
    if st.session_state["role"] == "admin":
        menu_secenekleri.insert(0, "Yönetim Paneli (Admin)")
        
    secili_menu = st.radio("Sistem Menüsü", menu_secenekleri)
    
    st.divider()
    if st.button("Güvenli Çıkış", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ==========================================
# MENÜ 1: CARİ KART TANIMLARI
# ==========================================
if secili_menu == "Cari Kart Tanımları":
    if st.session_state["role"] not in ["onaylı", "admin"]:
        st.warning("Bu ekranı görüntüleme yetkiniz yok.")
    else:
        st.header("Cari Kart Tanımları")
        st.write("Sistemdeki müşteri, tedarikçi veya personellerin ana verilerini buradan yönetebilirsiniz.")
        
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
                cariler_data = cariler_res.data
                if cariler_data:
                    # Gelişmiş tablo görünümü için Pandas kullanımı
                    df_cariler = pd.DataFrame(cariler_data)
                    df_gosterim = df_cariler[["cari_kodu", "unvan", "doviz_tipi", "vkn_tckn", "telefon", "email"]]
                    df_gosterim.columns = ["Kodu", "Ünvan / İsim", "Döviz", "VKN/TCKN", "Telefon", "E-Posta"]
                    
                    st.dataframe(df_gosterim, use_container_width=True, hide_index=True)
                else:
                    st.info("Sistemde kayıtlı cari bulunmamaktadır.")
            except Exception as e:
                st.error(f"Veri çekme hatası: {e}")

# ==========================================
# MENÜ 2: CARİ HAREKETLER & FİŞLER (MİZAN MANTIĞI)
# ==========================================
elif secili_menu == "Cari Hareketler & Fişler":
    if st.session_state["role"] not in ["onaylı", "admin"]:
        st.warning("Bu ekranı görüntüleme yetkiniz yok.")
    else:
        st.header("Cari Hareket Föyü (Ekstre)")
        
        # 1. Cari Seçimi
        cariler_res = supabase.table("cariler").select("id, cari_kodu, unvan, doviz_tipi").order("unvan").execute()
        cariler_listesi = cariler_res.data
        
        if not cariler_listesi:
            st.warning("İşlem yapabilmek için önce 'Cari Kart Tanımları' menüsünden cari açmalısınız.")
        else:
            cari_opsiyonlari = {f"{c['cari_kodu']} - {c['unvan']} ({c['doviz_tipi']})": c for c in cariler_listesi}
            secilen_cari_etiketi = st.selectbox("Hareketleri Görüntülenecek Cariyi Seçin:", ["Seçiniz..."] + list(cari_opsiyonlari.keys()))
            
            if secilen_cari_etiketi != "Seçiniz...":
                aktif_cari = cari_opsiyonlari[secilen_cari_etiketi]
                cari_id = aktif_cari["id"]
                cari_doviz = aktif_cari["doviz_tipi"]
                
                st.write("---")
                
                # 2. Hareket Verilerini Çekme ve Bakiye Hesaplama
                islemler_res = supabase.table("islemler").select("*").eq("cari_id", cari_id).order("created_at", desc=False).execute()
                islemler = islemler_res.data
                
                toplam_borc = 0.0
                toplam_alacak = 0.0
                ekstre_listesi = []
                
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
                    
                    # Resmi gösterim için format
                    ekstre_listesi.append({
                        "Tarih": islem["created_at"][:16].replace("T", " "),
                        "Evrak Tipi": islem["evrak_tipi"],
                        "Belge No": islem.get("belge_no", "-"),
                        "B/A": islem["islem_yonu"],
                        "Borç": f"{satir_borc:,.2f}",
                        "Alacak": f"{satir_alacak:,.2f}",
                        "Bakiye": f"{bakiye:,.2f}",
                        "Açıklama": islem.get("aciklama", ""),
                        "İşleyen": islem["isleyen_kisi"],
                        "Dosya": "Var" if islem.get("dosya_url") else "Yok"
                    })
                
                guncel_bakiye = toplam_borc - toplam_alacak
                bakiye_durumu = "Borçlu" if guncel_bakiye > 0 else "Alacaklı" if guncel_bakiye < 0 else "Kapandı"
                
                # Bakiye Özet Kartları
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Toplam Borç", f"{toplam_borc:,.2f} {cari_doviz}")
                m2.metric("Toplam Alacak", f"{toplam_alacak:,.2f} {cari_doviz}")
                m3.metric("Güncel Bakiye", f"{abs(guncel_bakiye):,.2f} {cari_doviz}")
                m4.metric("Bakiye Durumu", bakiye_durumu)
                
                # Fiş Giriş Paneli
                with st.expander("➕ Yeni Fiş / İşlem Girişi Yap"):
                    if "form_seed" not in st.session_state:
                        st.session_state["form_seed"] = 0
                    fs = st.session_state["form_seed"]
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        f_evrak = st.selectbox("Evrak Tipi", ["Fatura", "Nakit Tahsilat", "Nakit Tediye (Ödeme)", "Banka Havalesi/EFT", "Devir/Açılış"], key=f"f_evrak_{fs}")
                        f_yon = st.radio("İşlem Yönü (Cari Hesap İçin)", ["Borç", "Alacak"], horizontal=True, key=f"f_yon_{fs}", help="Satış yaptıysanız veya nakit verdiyseniz 'Borç'. Mal aldıysanız veya tahsilat yaptıysanız 'Alacak' seçin.")
                    with c2:
                        f_tutar = st.number_input(f"Tutar ({cari_doviz})", min_value=0.0, step=10.0, format="%.2f", key=f"f_tutar_{fs}")
                        f_belge = st.text_input("Belge/Fatura No", key=f"f_belge_{fs}")
                    
                    f_aciklama = st.text_input("Açıklama / İşlem Detayı", key=f"f_aciklama_{fs}")
                    f_dosya = st.file_uploader("Evrak Belgesi (Opsiyonel)", type=["pdf", "jpg", "png"], key=f"f_dosya_{fs}")
                    
                    col_kaydet, col_temizle = st.columns([3, 1])
                    if col_kaydet.button("İşlemi Cari Hesaba İşle", type="primary", use_container_width=True):
                        if f_tutar <= 0:
                            st.error("Tutar 0'dan büyük olmalıdır.")
                        else:
                            with st.spinner("Kayıt işleniyor..."):
                                dosya_url = None
                                dosya_path = None
                                if f_dosya:
                                    safe_name = f_dosya.name.replace(" ", "_")
                                    dosya_path = f"cariler/{cari_id}/{int(time.time())}_{safe_name}"
                                    supabase.storage.from_("belgeler").upload(
                                        path=dosya_path, 
                                        file=f_dosya.getvalue(), 
                                        file_options={"content_type": f_dosya.type or "application/octet-stream"}
                                    )
                                    dosya_url = supabase.storage.from_("belgeler").get_public_url(dosya_path)
                                
                                supabase.table("islemler").insert({
                                    "cari_id": cari_id,
                                    "evrak_tipi": f_evrak,
                                    "islem_yonu": f_yon,
                                    "tutar": f_tutar,
                                    "belge_no": f_belge,
                                    "aciklama": f_aciklama.strip(),
                                    "dosya_url": dosya_url,
                                    "dosya_path": dosya_path,
                                    "isleyen_kisi": st.session_state["ad_soyad"]
                                }).execute()
                                
                                st.session_state["form_seed"] += 1
                                st.success("Fiş başarıyla işlendi!")
                                time.sleep(1)
                                st.rerun()
                                
                    if col_temizle.button("Formu Temizle", use_container_width=True):
                        st.session_state["form_seed"] += 1
                        st.rerun()
                
                # Ekstre Tablosu
                st.write("#### Hareket Dökümü (Yeniden Eskiye)")
                if ekstre_listesi:
                    # En yeni işlemin üstte görünmesi için listeyi ters çeviriyoruz
                    ekstre_listesi.reverse()
                    df_ekstre = pd.DataFrame(ekstre_listesi)
                    st.dataframe(df_ekstre, use_container_width=True, hide_index=True)
                else:
                    st.info("Bu cariye ait henüz bir finansal hareket bulunmamaktadır.")

# ==========================================
# MENÜ 3: PROFİL VE AYARLAR
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
# MENÜ 4: YÖNETİM PANELİ (SADECE ADMIN)
# ==========================================
elif secili_menu == "Yönetim Paneli (Admin)":
    st.header("Sistem Yönetim Paneli")
    
    tab_ozet, tab_kullanici = st.tabs(["Mali Özet (Döviz Bazlı)", "Personel ve Yetki Yönetimi"])
    
    with tab_ozet:
        # Tüm cari ve işlemleri birleştirerek genel bakiye bulma
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
                        ozet[d_tip] += t  # Piyasadan Alacağımız
                    else:
                        ozet[d_tip] -= t  # Piyasaya Borcumuz
                        
            st.write("#### Genel Şirket Bakiyesi (Müşteri/Tedarikçi Net Durum)")
            st.caption("Pozitif değerler piyasadan toplam alacağınızı, negatif değerler piyasaya olan toplam borcunuzu temsil eder.")
            
            k1, k2, k3 = st.columns(3)
            k1.metric("TL Net Durum", f"{ozet['TL']:,.2f} TL")
            k2.metric("USD Net Durum", f"{ozet['USD']:,.2f} USD")
            k3.metric("EUR Net Durum", f"{ozet['EUR']:,.2f} EUR")
        else:
            st.info("Hesaplanacak yeterli veri bulunamadı.")

    with tab_kullanici:
        # Onay bekleyenler
        bekleyenler = supabase.table("app_users").select("*").eq("role", "beklemede").execute().data
        if bekleyenler:
            st.warning("Onay Bekleyen Personeller")
            for b in bekleyenler:
                c1, c2 = st.columns([4,1])
                c1.write(f"{b['ad_soyad']} ({b['email']})")
                if c2.button("Yetki Ver", key=f"onay_{b['id']}"):
                    supabase.table("app_users").update({"role":"onaylı"}).eq("id", b["id"]).execute()
                    st.rerun()
                    
        st.divider()
        st.write("#### Kayıtlı Personeller ve Şifre Sıfırlama")
        all_users = supabase.table("app_users").select("*").execute().data
        if all_users:
            secili_u_mail = st.selectbox("Personel Seçin", [u["email"] for u in all_users])
            secili_u = next(u for u in all_users if u["email"] == secili_u_mail)
            
            st.write(f"**İsim:** {secili_u.get('ad_soyad')} | **Yetki:** {secili_u['role']}")
            if st.button("Bu personelin şifresini '1234' olarak sıfırla", type="primary"):
                temiz_mail = secili_u["email"].strip().lower()
                supabase.table("app_users").update({
                    "password": hash_password("1234"),
                    "email": temiz_mail
                }).eq("id", secili_u["id"]).execute()
                st.success("Şifre sıfırlandı!")
                time.sleep(1.5)
                st.rerun()
