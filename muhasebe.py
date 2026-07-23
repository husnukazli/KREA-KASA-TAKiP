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
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": "", "user_id": ""})

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
        if st.button("Giriş Yap", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    u = users[0]
                    st.session_state.update({
                        "logged_in": True, 
                        "email": login_email, 
                        "ad_soyad": u.get("ad_soyad", login_email), 
                        "role": u["role"],
                        "user_id": u["id"]
                    })
                    st.success("Giriş başarılı, yönlendiriliyorsunuz...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Hatalı e-posta veya şifre!")
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
                        st.warning("⚠️ Bu e-posta zaten kayıtlı!")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": reg_ad_soyad, 
                            "email": reg_email, 
                            "password": hash_password(reg_pass), 
                            "role": "beklemede"
                        }).execute()
                        st.success("✅ Kayıt başarılı! Yönetici onayından sonra sisteme girebilirsiniz.")
                except Exception as e:
                    st.error(f"Kayıt hatası: {e}")
            else:
                st.error("⚠️ Lütfen tüm zorunlu alanları doldurun.")

    with st.expander("🛡️ Yönetici (Admin) Girişi"):
        admin_pass = st.text_input("Yönetici Şifresi", type="password", key="admin_pass")
        if st.button("Yönetici Olarak Gir"):
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
                 st.error("⚠️ Hatalı yönetici şifresi!")
    st.stop()

# ==========================================
# 2. ANA UYGULAMA
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['ad_soyad']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    display_role = "Onaylı Kullanıcı" if st.session_state['role'] == "onaylı" else "Beklemede" if st.session_state['role'] == "beklemede" else "Yönetici"
    st.write(f"🔑 Yetki: {role_color} {display_role}")
    
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("💼 Şirket Kasa ve Belge Yönetimi")

# ==========================================
# YÖNETİCİ PANELİ
# ==========================================
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Yönetici Kontrol Paneli**")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "📊 Güncel Kasa Durumu", 
        "⏳ Bekleyen Onaylar", 
        "👥 Sistem Kullanıcıları", 
        "📈 Personel İstatistikleri"
    ])
    
    # 1. KASA ÖZETİ
    with admin_tab1:
        st.markdown("### 🏦 Genel Kasa Bakiyeleri")
        try:
            tum_islemler = supabase.table("islemler").select("*").execute().data
            
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

    # 2. ONAYLAR
    with admin_tab2:
        res_pending = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
        if res_pending.data:
            for user in res_pending.data:
                col1, col2 = st.columns([4, 1])
                col1.write(f"- 👤 **{user.get('ad_soyad', 'İsimsiz')}** ({user['email']})")
                if col2.button("Onayla", key=f"onay_{user['id']}"):
                    supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                    st.success("Kullanıcı onaylandı!")
                    st.rerun()
        else:
            st.info("Onay bekleyen yeni kullanıcı yok.")

    # 3. SİSTEM KULLANICILARI VE PROFİL İNCELEME
    with admin_tab3:
        st.markdown("### 👥 Sistem Kullanıcıları Listesi")
        all_users = supabase.table("app_users").select("*").execute().data
        if all_users:
            selected_user_email = st.selectbox("Profili incelenecek kullanıcıyı seçin:", [u["email"] for u in all_users])
            selected_u = next((u for u in all_users if u["email"] == selected_user_email), None)
            
            if selected_u:
                st.info(f"📋 **{selected_u.get('ad_soyad', 'İsimsiz')}** Kullanıcısının Profil Bilgileri:")
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    st.write(f"**E-posta:** {selected_u.get('email', '-')}")
                    st.write(f"**Telefon:** {selected_u.get('telefon', 'Belirtilmemiş')}")
                    st.write(f"**Şirket Konum:** {selected_u.get('konum', 'Belirtilmemiş')}")
                with c_p2:
                    st.write(f"**Pozisyon:** {selected_u.get('pozisyon', 'Belirtilmemiş')}")
                    st.write(f"**Birim:** {selected_u.get('birim', 'Belirtilmemiş')}")
                    st.write(f"**Yetki Durumu:** {selected_u.get('role', '-')}")
        else:
            st.info("Kayıtlı kullanıcı bulunamadı.")

    # 4. PERSONEL İSTATİSTİKLERİ
    with admin_tab4:
        st.markdown("### 📈 Kullanıcı Bazlı İşlem İstatistikleri")
        if all_users and tum_islemler:
            stat_user = st.selectbox("İstatistikleri görmek için kullanıcı seçin:", [u.get('ad_soyad', u['email']) for u in all_users], key="stat_user_sel")
            user_islemleri = [i for i in tum_islemler if i.get("isleyen_kisi") == stat_user]
            
            if user_islemleri:
                st.success(f"Toplam {len(user_islemleri)} adet işlem kaydı bulundu.")
                # Tür bazlı sayım ve tutar
                tur_ozet = {}
                for ui in user_islemleri:
                    turu = ui["islem_turu"]
                    pb = ui["para_birimi"]
                    tutar = float(ui["tutar"])
                    if turu not in tur_ozet:
                        tur_ozet[turu] = {"adet": 0, "tutar": {}}
                    tur_ozet[turu]["adet"] += 1
                    if pb not in tur_ozet[turu]["tutar"]:
                        tur_ozet[turu]["tutar"][pb] = 0.0
                    tur_ozet[turu]["tutar"][pb] += tutar
                
                for tur, detay in tur_ozet.items():
                    tutar_str = ", ".join([f"{val:,.2f} {curr}" for curr, val in detay["tutar"].items()])
                    st.write(- **{tur}**: {detay['adet']} adet | Toplam Tutar: {tutar_str})
            else:
                st.info("Bu kullanıcının henüz sisteme işlenmiş bir kaydı yok.")
        else:
            st.info("İstatistik için yeterli veri bulunamadı.")
            
    st.divider()

# ==========================================
# ANA SEKMELER: İŞLEM EKLEME, GEÇMİŞ VE PROFİL
# ==========================================
tab_yeni, tab_gecmis, tab_profil = st.tabs(["💸 Yeni İşlem & Belge Ekle", "🧾 İşlem Geçmişi", "⚙️ Profil & Şifre Bilgileri"])

# 1. YENİ İŞLEM EKLEME SEKMESİ
with tab_yeni:
    if st.session_state["role"] in ["onaylı", "admin"]:
        st.markdown("### Yeni Finansal Kayıt Oluştur")
        
        # State tabanlı form temizliği kontrolü (Menüler kalır, tutar/açıklama/dosya sıfırlanır)
        if "f_tutar" not in st.session_state: st.session_state["f_tutar"] = 0.0
        if "f_belge_no" not in st.session_state: st.session_state["f_belge_no"] = ""
        if "f_aciklama" not in st.session_state: st.session_state["f_aciklama"] = ""

        f_yon = st.radio("İşlem Yönü", ["Giriş (Gelir)", "Çıkış (Gider)"], horizontal=True, key="f_yon_sel")
        f_turu = st.selectbox("İşlem Türü", ["Fatura", "İrsaliye", "Tahsilat Makbuzu", "Fiş", "Dekont", "Sözleşme", "Diğer"], key="f_turu_sel")
        
        c1, c2 = st.columns(2)
        with c1:
            f_tutar = st.number_input("Tutar (Rakam ile)", min_value=0.0, format="%.2f", step=10.0, key="f_tutar_input")
            f_para_birimi = st.selectbox("Para Birimi", ["TL", "USD", "EUR"], key="f_pb_sel")
        with c2:
            f_odeme_yontemi = st.selectbox("Ödeme Yöntemi", ["Nakit", "Kredi Kartı", "Çek", "Senet", "Banka Havalesi/EFT"], key="f_odeme_sel")
            f_belge_no = st.text_input("Belge/Fatura No (İsteğe Bağlı)", key="f_belge_input")
            
        f_aciklama = st.text_area("Açıklama (Firma adı, İşlem detayı vs.)", key="f_aciklama_input")
            
        uploaded_file = st.file_uploader("Belge/Fotoğraf Yükle", type=["pdf", "jpg", "png", "jpeg"])
        
        if uploaded_file is not None:
            st.success("✅ Belge başarıyla yüklendi. Şimdi kaydı tamamlayabilirsiniz.")

        if st.button("💾 Kaydı Tamamla ve Kasaya İşle", use_container_width=True):
            if f_tutar <= 0:
                st.error("⚠️ Lütfen 0'dan büyük geçerli bir tutar giriniz!")
            elif not uploaded_file:
                st.error("⚠️ Lütfen işleme ait belgeyi (PDF veya Fotoğraf) yükleyiniz!")
            else:
                with st.spinner("Sisteme işleniyor..."):
                    try:
                        guvenli_yon = "giris" if f_yon == "Giriş (Gelir)" else "cikis"
                        guvenli_dosya_adi = uploaded_file.name.replace(" ", "_").replace("ş", "s").replace("ı", "i").replace("ğ", "g").replace("ç", "c").replace("ö", "o").replace("ü", "u")
                        
                        zaman_damgasi = int(time.time())
                        file_path = f"{guvenli_yon}/{f_para_birimi}/{zaman_damgasi}_{guvenli_dosya_adi}"
                        
                        content_type = uploaded_file.type if uploaded_file.type else "application/octet-stream"
                        
                        # Storage Yükleme
                        upload_res = supabase.storage.from_("belgeler").upload(
                            path=file_path, 
                            file=uploaded_file.getvalue(), 
                            file_options={"content_type": content_type}
                        )
                        
                        dosya_url = supabase.storage.from_("belgeler").get_public_url(file_path)
                        
                        # Veritabanına Kayıt
                        db_res = supabase.table("islemler").insert({
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
                        
                        st.success("✅ İşlem başarıyla kaydedildi ve kasa güncellendi!")
                        time.sleep(1.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ İşlem sırasında hata oluştu, lütfen tekrar deneyin: {e}")
                            
    elif st.session_state["role"] == "beklemede":
        st.info("⏳ Hesabınız henüz onaylanmadı. İşlem yapabilmek için yöneticinin onayını bekleyin.")

# 2. İŞLEM GEÇMİŞİ VE SİLME (EMİN MİSİNİZ KORUMALI & KASA SENKRONİZASYONLU)
with tab_gecmis:
    st.markdown("### İşlem Kayıtları Filtreleme ve Yönetimi")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        s_yon = st.selectbox("Yön Filtresi", ["Tümü", "Giriş (Gelir)", "Çıkış (Gider)"], key="f_s_yon")
    with col2:
        s_turu = st.selectbox("Tür Filtresi", ["Tümü", "Fatura", "İrsaliye", "Tahsilat Makbuzu", "Fiş", "Dekont", "Sözleşme", "Diğer"], key="f_s_tur")
    with col3:
        s_pb = st.selectbox("Para Birimi", ["Tümü", "TL", "USD", "EUR"], key="f_s_pb")

    if st.button("🔄 İşlemleri Listele", use_container_width=True):
        with st.spinner("Kayıtlar getiriliyor..."):
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
                        renk = "🟢" if islem['yon'] == "Giriş (Gelir)" else "🔴"
                        
                        c1, c2, c3 = st.columns([5, 3, 2])
                        c1.markdown(f"**{renk} {islem['islem_turu']}** ({islem['odeme_yontemi']}) <br><small>Açıklama: {islem['aciklama']}<br>İşleyen: {islem['isleyen_kisi']} | Belge No: {islem.get('belge_no','-')}</small>", unsafe_allow_html=True)
                        c2.markdown(f"<h3 style='margin:0;'>{islem['tutar']:,.2f} {islem['para_birimi']}</h3>", unsafe_allow_html=True)
                        
                        if st.session_state["role"] in ["onaylı", "admin"]:
                            with c3:
                                st.markdown(f"[👁️ İncele/İndir]({islem['dosya_url']})", unsafe_allow_html=True)
                                
                                # Silme yetkisi (Admin veya kaydı giren kişi)
                                if st.session_state["role"] == "admin" or st.session_state["ad_soyad"] == islem['isleyen_kisi']:
                                    del_key = f"del_btn_{islem['id']}"
                                    confirm_key = f"confirm_box_{islem['id']}"
                                    
                                    if st.button("🗑️ Sil", key=del_key):
                                        st.session_state[confirm_key] = True
                                        
                                    if st.session_state.get(confirm_key, False):
                                        st.warning("⚠️ Bu kayıt kalıcı olarak silinecek ve kasadan düşülecek. Emin misiniz?")
                                        col_evet, col_hayir = st.columns(2)
                                        if col_evet.button("✅ Evet, Sil", key=f"yes_del_{islem['id']}"):
                                            try:
                                                # Depodan dosyayı sil
                                                if islem.get("dosya_path"):
                                                    supabase.storage.from_("belgeler").remove([islem["dosya_path"]])
                                                # Veritabanından kaydı sil (Bu sayede kasa anında güncellenir)
                                                supabase.table("islemler").delete().eq("id", islem['id']).execute()
                                                st.success("Kayıt başarıyla silindi ve kasa güncellendi!")
                                                st.session_state[confirm_key] = False
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Silme hatası: {e}")
                                        if col_hayir.button("❌ Vazgeç", key=f"no_del_{islem['id']}"):
                                            st.session_state[confirm_key] = False
                                            st.rerun()
                        st.divider()

# 3. PROFİL VE ŞİFRE DEĞİŞTİRME SEKMESİ
with tab_profil:
    st.markdown("### ⚙️ Kullanıcı Profili ve Şifre Yönetimi")
    try:
        user_data_res = supabase.table("app_users").select("*").eq("email", st.session_state["email"]).execute()
        if user_data_res.data:
            u_info = user_data_res.data[0]
            
            with st.form("profil_guncelleme_formu"):
                st.subheader("Temel Bilgiler")
                p_ad = st.text_input("Ad Soyad", value=u_info.get("ad_soyad", ""))
                p_tel = st.text_input("Telefon Numarası", value=u_info.get("telefon", ""))
                p_konum = st.text_input("Şirket Konum", value=u_info.get("konum", ""))
                p_pozisyon = st.text_input("Pozisyon", value=u_info.get("pozisyon", ""))
                p_birim = st.text_input("Birim", value=u_info.get("birim", ""))
                
                st.divider()
                st.subheader("Şifre Değiştirme (İsteğe Bağlı)")
                p_yeni_sifre = st.text_input("Yeni Şifre (Değiştirmek istemiyorsanız boş bırakın)", type="password")
                
                profil_kaydet = st.form_submit_button("💾 Bilgileri Güncelle", use_container_width=True)
                
                if profil_kaydet:
                    update_payload = {
                        "ad_soyad": p_ad,
                        "telefon": p_tel,
                        "konum": p_konum,
                        "pozisyon": p_pozisyon,
                        "birim": p_birim
                    }
                    if p_yeni_sifre:
                        update_payload["password"] = hash_password(p_yeni_sifre)
                        
                    supabase.table("app_users").update(update_payload).eq("email", st.session_state["email"]).execute()
                    st.session_state["ad_soyad"] = p_ad
                    st.success("✅ Profil bilgileriniz başarıyla güncellendi!")
                    time.sleep(1)
                    st.rerun()
    except Exception as e:
        st.error(f"Profil bilgileri yüklenirken hata oluştu: {e}")
