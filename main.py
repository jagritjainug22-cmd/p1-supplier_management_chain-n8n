import streamlit as st
# from google.oauth2.service_account import Credentials
from components.dashboard import dashboard
from components.analyse_dashboard import analyse_dashboard
import streamlit_shadcn_ui as ui


# ================= CONFIG =================

N8N_BASE_URL = "http://localhost:5678/webhook-test/"
PROCESS_EMAILS_URL = f"{N8N_BASE_URL}process-emails"

USERNAME = "manager"
PASSWORD = "manager123"

# ================= LOGIN =================

def login():
    st.markdown(
        "<h1 style='text-align: center; color: #2c3e50;'>PROCUREMENT MANAGER</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align: center; color: #7f8c8d;'>Email Processing & Supplier Management</p>",
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Sign In")
        user = st.text_input("Username", label_visibility="collapsed", placeholder="Enter username")
        pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        
        if st.button("Sign In", use_container_width=True):
            if user == USERNAME and pwd == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.sidebar_page = "Dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password")

# ================= SIDEBAR =================

def sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center;">
                <h2 style="margin-bottom:0;">Procurement</h2>
                <p style="color:#7f8c8d; font-size:13px;">
                    Manager Console
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.divider()
        # st.markdown('<div class="sidebar-title">Navigation</div>', unsafe_allow_html=True)

        # Custom button navigation with icons
        options = ["Dashboard", "Analyse"]
        icons = {"Dashboard": "", "Analyse": ""}
        if "sidebar_page" not in st.session_state:
            st.session_state.sidebar_page = "Dashboard"

        for opt in options:
            selected = st.session_state.sidebar_page == opt
            btn = st.sidebar.button(
                f"{icons[opt]}  {opt}",
                key=f"sidebar_btn_{opt}",
                use_container_width=True,
                help=f"Go to {opt}"
            )
            if btn:
                st.session_state.sidebar_page = opt
                st.rerun()
            # Custom highlight for selected
            if selected:
                st.sidebar.markdown(
                    f"<style>div[data-testid='stSidebar'] button[data-testid='baseButton'][key='sidebar_btn_{opt}'] {{background: linear-gradient(90deg, #eaf6fb 0%, #b2e0fb 100%); color: #0077b6; font-weight: bold;}}</style>",
                    unsafe_allow_html=True
                )
        

        # Removed reference to page variable

        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.sidebar_page = "Dashboard"
            st.rerun()

            # Navigation handled by custom buttons above; removed old radio and page assignment

st.set_page_config(
    page_title="Procurement Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "sidebar_page" not in st.session_state:
    st.session_state.sidebar_page = "Dashboard"

import streamlit as st
import streamlit_shadcn_ui as ui

st.title("Shadcn UI Button Example")

btn_clicked = ui.button(
    text="Click Me!",
    key="shadcn_btn"
)

if btn_clicked:
    st.write("Button was clicked!")

if not st.session_state.logged_in:
    login()
else:
    sidebar()

    # ================= ROUTING =================
    if st.session_state.sidebar_page == "Dashboard":
        dashboard()
    elif st.session_state.sidebar_page == "Analyse":
        analyse_dashboard()
