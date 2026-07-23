import streamlit as st
import hashlib
from supabase import create_client, Client

# --- SUPABASE CONNECTION ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Page Config
st.set_page_config(page_title="Material Share", page_icon="📚", layout="wide")

# --- SESSION MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "email": "", "ad_soyad": "", "role": ""})

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = None

# ==========================================
# 1. LOGIN & REGISTER SCREEN
# ==========================================
if not st.session_state["logged_in"]:
    st.title("📚 Material Share")
    st.write("Please log in or register to continue.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Login")
        login_email = st.text_input("Email Address", key="log_email")
        login_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Log In", use_container_width=True):
            try:
                response = supabase.table("app_users").select("*").eq("email", login_email).execute()
                users = response.data
                if users and users[0]["password"] == hash_password(login_pass):
                    ad = users[0].get("ad_soyad", login_email)
                    st.session_state.update({"logged_in": True, "email": login_email, "ad_soyad": ad, "role": users[0]["role"]})
                    st.rerun()
                else:
                    st.error("Invalid email or password!")
            except Exception as e:
                st.error(f"Login error: {e}")

    with col2:
        st.subheader("Register")
        reg_ad_soyad = st.text_input("Full Name", key="reg_name")
        reg_email = st.text_input("Email Address", key="reg_email")
        reg_pass = st.text_input("Create Password", type="password", key="reg_pass")
        if st.button("Register", use_container_width=True):
            if reg_email and reg_pass and reg_ad_soyad:
                try:
                    existing = supabase.table("app_users").select("*").eq("email", reg_email).execute()
                    if existing.data:
                        st.warning("This email is already registered!")
                    else:
                        supabase.table("app_users").insert({
                            "ad_soyad": reg_ad_soyad, "email": reg_email, "password": hash_password(reg_pass), "role": "beklemede"
                        }).execute()
                        st.success("Registration successful! You can access the system after admin approval.")
                except Exception as e:
                    st.error(f"Registration error: {e}")
            else:
                st.error("Please fill in all fields.")

    with st.expander("🛡️ Admin Access"):
        admin_pass = st.text_input("Admin Password", type="password", key="admin_pass")
        if st.button("Log In as Admin"):
            if admin_pass == "admin123": 
                st.session_state.update({"logged_in": True, "ad_soyad": "System Admin", "email": "admin", "role": "admin"})
                st.rerun()
            else:
                 st.error("Invalid admin password!")
    st.stop()

# ==========================================
# 2. MAIN APP
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state['ad_soyad']}**")
    role_color = "🟢" if st.session_state['role'] in ['onaylı', 'admin'] else "🟠"
    
    display_role = "Approved" if st.session_state['role'] == "onaylı" else "Pending" if st.session_state['role'] == "beklemede" else "Admin"
    st.write(f"🔑 Status: {role_color} {display_role.upper()}")
    
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.title("📚 Material Share")

# ==========================================
# ADMIN PANEL (ONAY, İSTATİSTİK VE STORAGE)
# ==========================================
if st.session_state["role"] == "admin":
    st.warning("🛠️ **Admin Dashboard**")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["⏳ Pending Approvals", "📊 Teacher Statistics", "💾 Storage Health"])
    
    # 1. Onay Bekleyenler Sekmesi
    with admin_tab1:
        res_pending = supabase.table("app_users").select("*").eq("role", "beklemede").execute()
        if res_pending.data:
            for user in res_pending.data:
                col1, col2 = st.columns([4, 1])
                col1.write(f"- 👤 **{user.get('ad_soyad', 'No Name')}** ({user['email']})")
                if col2.button("Approve", key=f"onay_{user['id']}"):
                    supabase.table("app_users").update({"role": "onaylı"}).eq("id", user["id"]).execute()
                    st.rerun()
        else:
            st.info("No pending users.")
            
    # 2. Öğretmen İstatistikleri Sekmesi
    with admin_tab2:
        res_approved = supabase.table("app_users").select("*").eq("role", "onaylı").execute()
        if res_approved.data:
            teacher_list = [u.get("ad_soyad", "Unknown") for u in res_approved.data]
            selected_teacher = st.selectbox("Select a Teacher to View Stats", ["Select..."] + teacher_list)
            
            if selected_teacher != "Select...":
                res_files = supabase.table("files").select("*").eq("uploaded_by", selected_teacher).execute()
                teacher_files = res_files.data
                
                if teacher_files:
                    st.success(f"**{selected_teacher}** has shared a total of **{len(teacher_files)}** materials.")
                    
                    stats_dict = {}
                    for f in teacher_files:
                        level = f.get('kur', 'Unknown Level')
                        skill = f.get('alt_beceri', 'Unknown Focus')
                        
                        if level not in stats_dict:
                            stats_dict[level] = {}
                        if skill not in stats_dict[level]:
                            stats_dict[level][skill] = 0
                        stats_dict[level][skill] += 1
                    
                    c1, c2, c3 = st.columns(3)
                    col_idx = 0
                    cols = [c1, c2, c3]
                    
                    for level, skills in stats_dict.items():
                        with cols[col_idx % 3].expander(f"📁 {level} ({sum(skills.values())} files)", expanded=True):
                            for skill, count in skills.items():
                                st.write(f"- {skill}: **{count}**")
                        col_idx += 1
                else:
                    st.info(f"**{selected_teacher}** hasn't uploaded any materials yet.")
        else:
            st.info("No approved teachers found in the system.")
            
    # 3. Storage Health (Kapasite) Sekmesi
    with admin_tab3:
        try:
            res_all_files = supabase.table("files").select("*").execute()
            total_files = len(res_all_files.data) if res_all_files.data else 0
            
            # Ortalama bir eğitim dosyası (PDF/Word/PPT) ~2 MB kabul edilerek hesaplanır
            avg_mb_per_file = 2 
            total_capacity_mb = 1024 # 1 GB
            max_files = total_capacity_mb // avg_mb_per_file
            
            used_mb = total_files * avg_mb_per_file
            remaining_mb = total_capacity_mb - used_mb
            usage_percent = min(total_files / max_files, 1.0)
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Total Uploaded Files", f"{total_files}")
            sc2.metric("Estimated Used Space", f"~{used_mb} MB")
            sc3.metric("Estimated Remaining", f"~{remaining_mb} MB")
            
            st.markdown(f"**Storage Capacity Usage (Estimated limit: ~{max_files} files)**")
            st.progress(usage_percent)
            
            if usage_percent > 0.8:
                st.error("⚠️ Storage is getting full! Consider deleting old or unnecessary files.")
            else:
                st.success("✅ System storage health is excellent.")
        except Exception as e:
            st.error(f"Could not load storage stats: {e}")
            
    st.divider()

# TABS
tab_upload, tab_search = st.tabs(["📤 Upload Material", "🔍 Search & Download"])

# ==========================================
# UPLOAD TAB
# ==========================================
with tab_upload:
    if st.session_state["role"] == "onaylı":
        st.markdown("### Share a New Material")
        
        f_level = st.selectbox("1. Level", ["Select...", "Alpha", "Beta", "Gamma", "Delta"], key="yk_kur")
        f_class = st.selectbox("2. Class", ["Select...", "Integrated Skills 1", "Integrated Skills 2"], key="yk_omurga")
        f_focus = st.selectbox("3. Focus", ["Speaking", "Reading", "Listening", "Writing", "Vocabulary", "Use of English"], key="yk_beceri")
        f_week = st.selectbox("4. Week", [f"Week {i}" for i in range(1, 15)], key="yk_hafta")
        f_type = st.selectbox("5. Type of Material", ["Link (Kahoot, Bamboozle, etc.)", "Worksheet", "Exam Practice", "Presentation", "Games & Ideas"], key="yk_turu")
        
        uploaded_file = st.file_uploader("Select File", type=["pdf", "ppt", "pptx", "docx", "xlsx", "mp3", "jpg", "png", "jpeg"])
        
        if st.button("🚀 Share to Pool", use_container_width=True):
            if f_level == "Select..." or f_class == "Select...":
                st.error("Level and Class selection is required.")
            elif not uploaded_file:
                st.error("Please select a file to upload.")
            else:
                with st.spinner("Uploading..."):
                    try:
                        file_path = f"{f_level}/{f_week}/{uploaded_file.name}"
                        content_type = uploaded_file.type if uploaded_file.type else "application/octet-stream"
                        
                        supabase.storage.from_("materyaller").upload(
                            path=file_path, 
                            file=uploaded_file.getvalue(), 
                            file_options={"content_type": content_type, "upsert": "true"}
                        )
                        final_file_url = supabase.storage.from_("materyaller").get_public_url(file_path)
                        
                        supabase.table("files").insert({
                            "file_name": uploaded_file.name, 
                            "file_url": final_file_url, 
                            "file_path": file_path, 
                            "kur": f_level, 
                            "omurga": f_class, 
                            "alt_beceri": f_focus, 
                            "hafta": f_week, 
                            "materyal_turu": f_type, 
                            "uploaded_by": st.session_state['ad_soyad']
                        }).execute()
                        
                        st.success(f"✅ Shared successfully!")
                    except Exception as e:
                        st.error(f"Upload error: {e}")
                        
    elif st.session_state["role"] == "beklemede":
        st.info("⏳ Your upload access will be activated after admin approval.")
    else:
        st.info("Admins cannot upload files. Please log in with a teacher account.")

# ==========================================
# SEARCH, DOWNLOAD, EDIT & DELETE TAB
# ==========================================
with tab_search:
    st.markdown("### Filter Materials")
    
    col1, col2 = st.columns(2)
    with col1:
        s_level = st.selectbox("Level", ["All", "Alpha", "Beta", "Gamma", "Delta"], key="ara_kur")
        s_class = st.selectbox("Class", ["All", "Integrated Skills 1", "Integrated Skills 2"], key="ara_omurga")
        s_focus = st.selectbox("Focus", ["All", "Speaking", "Reading", "Listening", "Writing", "Vocabulary", "Use of English"], key="ara_beceri")
            
    with col2:
        s_week = st.selectbox("Week", ["All"] + [f"Week {i}" for i in range(1, 15)], key="ara_hafta")
        s_type = st.selectbox("Type of Material", ["All", "Link (Kahoot, Bamboozle, etc.)", "Worksheet", "Exam Practice", "Presentation", "Games & Ideas"], key="ara_turu")

    if st.button("🔄 Search & List", use_container_width=True):
        st.session_state.edit_mode = None 
        
    with st.spinner("Searching..."):
        query = supabase.table("files").select("*")
        if s_level != "All": query = query.eq("kur", s_level)
        if s_class != "All": query = query.eq("omurga", s_class)
        if s_focus != "All": query = query.eq("alt_beceri", s_focus)
        if s_week != "All": query = query.eq("hafta", s_week)
        if s_type != "All": query = query.eq("materyal_turu", s_type)
        
        files = query.execute().data
        
        if not files:
            st.warning("No materials found for these filters.")
        else:
            st.success(f"{len(files)} material(s) found.")
            for file in files:
                
                # EĞER YÖNETİCİ DÜZENLEME (EDIT) MODUNDAYSA
                if st.session_state.edit_mode == file['id']:
                    with st.expander(f"✏️ Editing: {file['file_name']}", expanded=True):
                        e_level = st.selectbox("New Level", ["Alpha", "Beta", "Gamma", "Delta"], index=["Alpha", "Beta", "Gamma", "Delta"].index(file['kur']) if file['kur'] in ["Alpha", "Beta", "Gamma", "Delta"] else 0, key=f"el_{file['id']}")
                        e_class = st.selectbox("New Class", ["Integrated Skills 1", "Integrated Skills 2"], index=["Integrated Skills 1", "Integrated Skills 2"].index(file['omurga']) if file['omurga'] in ["Integrated Skills 1", "Integrated Skills 2"] else 0, key=f"ec_{file['id']}")
                        focus_opts = ["Speaking", "Reading", "Listening", "Writing", "Vocabulary", "Use of English"]
                        safe_focus_idx = focus_opts.index(file['alt_beceri']) if file['alt_beceri'] in focus_opts else 0
                        e_focus = st.selectbox("New Focus", focus_opts, index=safe_focus_idx, key=f"ef_{file['id']}")
                        
                        colA, colB = st.columns(2)
                        with colA:
                            if st.button("💾 Save Changes", key=f"save_{file['id']}", use_container_width=True):
                                supabase.table("files").update({"kur": e_level, "omurga": e_class, "alt_beceri": e_focus}).eq("id", file['id']).execute()
                                st.session_state.edit_mode = None
                                st.rerun()
                        with colB:
                            if st.button("❌ Cancel", key=f"cancel_{file['id']}", use_container_width=True):
                                st.session_state.edit_mode = None
                                st.rerun()
                
                # NORMAL GÖRÜNÜM
                else:
                    with st.container():
                        c1, c2, c3 = st.columns([6, 2, 2])
                        c1.markdown(f"📄 **{file['file_name']}**<br><small>{file['kur']} | {file['omurga']} | {file.get('alt_beceri','')} | {file['hafta']} | {file['materyal_turu']} <br> Uploaded by: {file['uploaded_by']}</small>", unsafe_allow_html=True)
                        
                        if st.session_state["role"] == "beklemede":
                            c2.info("🔒 Pending Approval")
                        else:
                            c2.markdown(f"[👁️ View]({file['file_url']}) | [⬇️ Download]({file['file_url']}?download=)", unsafe_allow_html=True)
                        
                        if st.session_state["role"] == "admin" or st.session_state["ad_soyad"] == file['uploaded_by']:
                            with c3:
                                if st.session_state["role"] == "admin":
                                    if st.button("✏️ Edit", key=f"edit_{file['id']}", help="Change category"):
                                        st.session_state.edit_mode = file['id']
                                        st.rerun()
                                        
                                if st.button("🗑️ Delete", key=f"del_{file['id']}"):
                                    try:
                                        if file.get("file_path"):
                                            supabase.storage.from_("materyaller").remove([file["file_path"]])
                                        supabase.table("files").delete().eq("id", file['id']).execute()
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error deleting file: {e}")
                        st.divider()
