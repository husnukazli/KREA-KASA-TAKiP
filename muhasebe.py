import streamlit as st
import hashlib
import time
from supabase import create_client, Client

# --- SUPABASE BAĞLANTISI ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Sayfa Ayarları
st.set_page_config(page_title="Kasa & Belge Takip", page_icon="💰", layout="wide")

# --- OTURUM YÖNETİMİ ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": ""})

# ==========================================
# 1. GİRİŞ VE KAYIT EKRANI
# ==========================================
if not st.session_state["logged_in"]:
    st.title("💰 Ön Muhasebe & Kasa Takip Sistemi")
    st.write("Sisteme erişmek için lütfen giriş yapın veya kayıt olun.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Giriş Yap")
        login_email = st.text_input("E-posta Adresi", key="log_email")
        login_pass = st.text_input("Şifre", type="password", key="log_pass")
        if st.button("Giriş", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    ad = users[0].get("ad_soyad", login_email)
                    st.session_state.update({"logged_in": True, "email": login_email, "ad_soyad": ad, "role": users[0]["role"]})
                    st.rerun()
                else:
                    st.error("Hatalı e-posta veya şifre!")
            except Exception as e:
                st.error(f"Giriş hatası: {e}")

    with col2:
        st.subheader("Kayıt Ol")
        reg_ad_soyad = st.text_input("Ad Soyad", key="reg_name")
        reg_email = st.text_input("E-posta Adresi", key="reg_email")
        reg_pass = st.text_input("Şifre Belirle", type="password", key="reg_pass")
        if st.button("Kayıt Ol", use_container_width=True):
            if reg_email and reg_pass and reg_ad_soyad:
                try:
                    existing = supabase.table("app_users").select("*").eq("email", reg_email).execute()
                    if existing.data:
                        st.warning("Bu e-posta zaten kayıtlı!")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": reg_ad_soyad, "email": reg_email, "password": hash_password(reg_pass), "role": "beklemede"
                        }).execute()
                        st.success("Kayıt başarılı! Yönetici onayından sonra sisteme girebilirsiniz.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
            else:
                st.error("Lütfen tüm alanları doldurun.")

    with st.expander("🛡️ Yönetici (Admin) Girişi"):
        admin_pass = st.text_input("Yönetici Şifresi", type="password", key="admin_pass")
        if st.button("Yönetici Olarak Gir"):
            if admin_pass == "admin123": 
                st.session_state.update({"logged_in": True, "ad_soyad": "Sistem Yöneticisi", "email": "admin", "role": "admin"})
                st.rerun()
            else:
                 st.error("Hatalı yönetici şifresi!")
    st.stop()

# ==========================================
# 2. ANA UYGULAMA (KASA VE BELGELER)
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['ad_soyad']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    
    display_role = "Onaylı Personel" if st.session_state['role'] == "onaylı" else "Beklemede" if st.session_state['role'] == "beklemede" else "Yönetici"
    st.write(f"🔑 Yetki: {role_color} {display_role}")
    
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("💼 Şirket Kasa ve Belge Yönetimi")

# ==========================================
# YÖNETİCİ PANELİ (ONAY VE KASA DURUMU)
# ==========================================
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Yönetici Kontrol Paneli**")
    
    admin_tab1, admin_tab2 = st.tabs(["📊 Güncel Kasa Durumu", "⏳ Bekleyen Kullanıcı Onayları"])
    
    # KASA ÖZETİ (GİRDİ / ÇIKTI HESAPLAMALARI)
    with admin_tab1:
        st.markdown("### 🏦 Genel Kasa Bakiyeleri")
        try:
            tum_islemler = supabase.table("islemler").select("*").execute().data
            
            # Kasalarımız (Başlangıçta 0)
            kasa = {"TL": 0.0, "USD": 0.0, "EUR": 0.0}
            toplam_giren = {"TL": 0.0, "USD": 0.0, "EUR": 0.0}
            toplam_cikan = {"TL": 0.0, "USD": 0.0, "EUR": 0.0}
            
            if tum_islemler:
                for islem in tum_islemler:
                    pb = islem["para_birimi"]
                    miktar = float(islem["tutar"])
                    if islem["yon"] == "Giriş (Gelir)":
                        kasa[pb] += miktar
                        toplam_giren[pb] += miktar
                    elif islem["yon"] == "Çıkış (Gider)":
                        kasa[pb] -= miktar
                        toplam_cikan[pb] += miktar
            
            # Ekrana Şık Metrikler Olarak Basma
            k1, k2, k3 = st.columns(3)
            k1.metric("₺ TL Kasası", f"{kasa['TL']:,.2f} TL")
            k2.metric("$ Dolar Kasası", f"{kasa['USD']:,.2f} USD")
            k3.metric("€ Euro Kasası", f"{kasa['EUR']:,.2f} EUR")
            
            with st.expander("📈 Detaylı Girdi/Çıktı Analizi"):
                det_col1, det_col2 = st.columns(2)
                with det_col1:
                    st.success("🟢 TOPLAM GİREN (GELİR)")
                    st.write(f"**TL:** {toplam_giren['TL']:,.2f}")
                    st.write(f"**USD:** {toplam_giren['USD']:,.2f}")
                    st.write(f"**EUR:** {toplam_giren['EUR']:,.2f}")
                with det_col2:
                    st.error("🔴 TOPLAM ÇIKAN (GİDER)")
                    st.write(f"**TL:** {toplam_cikan['TL']:,.2f}")
                    st.write(f"**USD:** {toplam_cikan['USD']:,.2f}")
                    st.write(f"**EUR:** {toplam_cikan['EUR']:,.2f}")
                    
        except Exception as e:
            st.error(f"Kasa verileri yüklenirken hata oluştu: {e}")

    # KULLANICI ONAYLARI
    with admin_tab2:
        res_pending = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
        if res_pending.data:
            for user in res_pending.data:
                col1, col2 = st.columns([4, 1])
                col1.write(f"- 👤 **{user.get('ad_soyad', 'İsimsiz')}** ({user['email']})")
                if col2.button("Onayla", key=f"onay_{user['id']}"):
                    supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                    st.rerun()
        else:
            st.info("Onay bekleyen yeni personel yok.")
    st.divider()


# ==========================================
# İŞLEM SEKMELERİ (EKLEME VE GEÇMİŞ)
# ==========================================
tab_yeni, tab_gecmis = st.tabs(["💸 Yeni İşlem & Belge Ekle", "🧾 İşlem Geçmişi ve Arama"])

with tab_yeni:
    if st.session_state["role"] in ["onaylı", "admin"]:
        st.markdown("### Yeni Finansal Kayıt Oluştur")
        
        with st.form("yeni_islem_formu"):
            c1, c2 = st.columns(2)
            
            with c1:
                f_yon = st.radio("İşlem Yönü", ["Giriş (Gelir)", "Çıkış (Gider)"], horizontal=True)
                f_turu = st.selectbox("İşlem Türü", ["Fatura", "İrsaliye", "Tahsilat Makbuzu", "Fiş", "Dekont", "Sözleşme", "Diğer"])
                f_tutar = st.number_input("Tutar (Rakam ile)", min_value=0.0, format="%.2f", step=10.0)
                f_para_birimi = st.selectbox("Para Birimi", ["TL", "USD", "EUR"])
            
            with c2:
                f_odeme_yontemi = st.selectbox("Ödeme Yöntemi", ["Nakit", "Kredi Kartı", "Çek", "Senet", "Banka Havalesi/EFT"])
                f_belge_no = st.text_input("Belge/Fatura No (İsteğe Bağlı)")
                f_aciklama = st.text_area("Açıklama (Firma adı, İşlem detayı vs.)")
                
            uploaded_file = st.file_uploader("Belge/Fotoğraf Yükle", type=["pdf", "jpg", "png", "jpeg"])
            
            submitted = st.form_submit_button("💾 Kaydı Tamamla ve Kasaya İşle", use_container_width=True)
            
            if submitted:
                if f_tutar <= 0:
                    st.error("Lütfen geçerli bir tutar giriniz!")
                elif not uploaded_file:
                    st.error("Lütfen işleme ait belgeyi (PDF veya Fotoğraf) yükleyiniz!")
                else:
                    with st.spinner("Sisteme işleniyor..."):
                        try:
                            # Benzersiz dosya ismi oluşturma (üzerine yazmayı engeller)
                            zaman_damgasi = int(time.time())
                            file_path = f"{f_yon}/{f_para_birimi}/{zaman_damgasi}_{uploaded_file.name}"
                            
                            content_type = uploaded_file.type if uploaded_file.type else "application/octet-stream"
                            
                            # Supabase Storage'a Yükleme
                            supabase.storage.from_("belgeler").upload(
                                path=file_path, 
                                file=uploaded_file.getvalue(), 
                                file_options={"content_type": content_type}
                            )
                            dosya_url = supabase.storage.from_("belgeler").get_public_url(file_path)
                            
                            # Veritabanına Kaydetme
                            supabase.table("islemler").insert({
                                "islem_turu": f_turu,
                                "yon": f_yon,
                                "tutar": float(f_tutar),
                                "para_birimi": f_para_birimi,
                                "odeme_yontemi": f_odeme_yontemi,
                                "belge_no": f_belge_no,
                                "aciklama": f_aciklama,
                                "dosya_url": dosya_url,
                                "dosya_path": file_path,
                                "isleyen_kisi": st.session_state['ad_soyad']
                            }).execute()
                            
                            st.success(f"✅ İşlem başarıyla kaydedildi! Kasa güncellendi.")
                            time.sleep(2) # Mesajı 2 saniye gösterip sayfayı yeniler
                            st.rerun()
                        except Exception as e:
                            st.error(f"Yükleme hatası: {e}")
                            
    elif st.session_state["role"] == "beklemede":
        st.info("⏳ Hesabınız henüz onaylanmadı. İşlem yapabilmek için yöneticinin onayını bekleyin.")

with tab_gecmis:
    st.markdown("### İşlem Kayıtları Filtreleme")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        s_yon = st.selectbox("Yön Filtresi", ["Tümü", "Giriş (Gelir)", "Çıkış (Gider)"])
    with col2:
        s_turu = st.selectbox("Tür Filtresi", ["Tümü", "Fatura", "İrsaliye", "Tahsilat Makbuzu", "Fiş", "Dekont", "Sözleşme", "Diğer"])
    with col3:
        s_pb = st.selectbox("Para Birimi", ["Tümü", "TL", "USD", "EUR"])

    if st.button("🔄 İşlemleri Getir", use_container_width=True):
        with st.spinner("Kayıtlar aranıyor..."):
            query = supabase.table("islemler").select("*").order("created_at", desc=True)
            if s_yon != "Tümü": query = query.eq("yon", s_yon)
            if s_turu != "Tümü": query = query.eq("islem_turu", s_turu)
            if s_pb != "Tümü": query = query.eq("para_birimi", s_pb)
            
            islemler = query.execute().data
            
            if not islemler:
                st.warning("Bu filtrelere uygun kayıt bulunamadı.")
            else:
                st.success(f"{len(islemler)} adet işlem listelendi.")
                
                for islem in islemler:
                    with st.container():
                        # Renk belirleme: Giriş yeşil, çıkış kırmızı
                        renk = "🟢" if islem['yon'] == "Giriş (Gelir)" else "🔴"
                        
                        c1, c2, c3 = st.columns([5, 3, 2])
                        c1.markdown(f"**{renk} {islem['islem_turu']}** ({islem['odeme_yontemi']}) <br><small>Açıklama: {islem['aciklama']}<br>İşleyen: {islem['isleyen_kisi']} | Belge No: {islem.get('belge_no','-')}</small>", unsafe_allow_html=True)
                        
                        # Tutarı net ve kalın yazdırma
                        c2.markdown(f"<h3 style='margin:0;'>{islem['tutar']:,.2f} {islem['para_birimi']}</h3>", unsafe_allow_html=True)
                        
                        if st.session_state["role"] in ["onaylı", "admin"]:
                            with c3:
                                st.markdown(f"[👁️ Belgeyi Gör / İndir]({islem['dosya_url']})", unsafe_allow_html=True)
                                
                                # Sadece admin veya işleyen kişi silebilir
                                if st.session_state["role"] == "admin" or st.session_state["ad_soyad"] == islem['isleyen_kisi']:
                                    if st.button("🗑️ İptal/Sil", key=f"del_{islem['id']}"):
                                        try:
                                            # Önce dosyayı depodan sil
                                            if islem.get("dosya_path"):
                                                supabase.storage.from_("belgeler").remove([islem["dosya_path"]])
                                            # Sonra veritabanından kaydı sil
                                            supabase.table("islemler").delete().eq("id", islem['id']).execute()
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Silme hatası: {e}")
                        st.divider()
