import streamlit as st
from components.dashboard import dashboard
from components.analyse_dashboard import analyse_dashboard
import streamlit_shadcn_ui as ui


N8N_BASE_URL = "http://localhost:5678/webhook-test/"
PROCESS_EMAILS_URL = f"{N8N_BASE_URL}process-emails"

USERNAME = "manager"
PASSWORD = "manager123"

def landing_page():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@700&display=swap');
        
        .landing-header {
            text-align: left;
            font-size: 3rem !important;
            font-weight: 700 !important;
            font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif !important;
            color: #2c3e50 !important;
            margin-top: 1rem !important;
            margin-bottom: 4rem !important;  /* HEADING-CARD SPACING: Increase/decrease this value (e.g., 6rem for more space, 2rem for less) */
            margin-left: 10.5rem !important;  /* LEFT MARGIN: Adjust to move heading left/right */
        }
        .card-container {
            display: flex;
            justify-content: center;
            gap: 3rem;
            margin-top: 2rem;
            margin-bottom: 2rem;
        }
        .custom-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 3rem 2rem 4rem;
            width: 100%;  /* CARD SIZE: Change this to control card width (100% fills the column) */
            min-height: 350px;  /* CARD HEIGHT: Adjust this for card height */
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .custom-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        .custom-card.analyse {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .card-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1rem;
        }
        .card-desc {
            font-size: 1rem;
            color: rgba(255,255,255,0.9);
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h1 class='landing-header'>Hi Manager 👋</h1>", unsafe_allow_html=True)
    
    # CARD SPACING: Adjust the middle number (1) to control gap between cards
    # Format: [left_margin, card1_width, gap, card2_width, right_margin]
    col1, col2, col3, col4, col5 = st.columns([1, 2, 0.6, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div class='custom-card'>
                <div class='card-title'>DASHBOARD</div>
                <div class='card-desc'>View and manage your procurement emails</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Go to Dashboard", key="dash_btn", use_container_width=True):
            st.session_state.in_app = True
            st.session_state.active_tab = "Dashboard"
            st.rerun()
    
    with col4:
        st.markdown(
            """
            <div class='custom-card analyse'>
                <div class='card-title'>ANALYSE</div>
                <div class='card-desc'>Analyze supplier data and insights</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Go to Analyse", key="analyse_btn", use_container_width=True):
            st.session_state.in_app = True
            st.session_state.active_tab = "Analyse"
            st.rerun()

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
                st.session_state.in_app = False
                st.session_state.active_tab = "Dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password")

def app_with_tabs():
    # Custom CSS for sticky navigation bar with custom tabs
    st.markdown(
        """
        <style>
        /* Sticky navigation container */
        .nav-bar-container {
            position: sticky;
            top: 0;
            z-index: 999;
            background: white;
            padding-bottom: 1rem;
        }
        
        /* All buttons - remove default styling */
        div[data-testid="column"] button {
            height: 60px !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            border-radius: 8px 8px 0 0 !important;
            border: none !important;
            background: #1e293b !important;
            color: white !important;
            position: relative !important;
            box-shadow: none !important;
        }
        
        /* Dashboard button specific */
        button[key="tab_dashboard"] {
            background: """ + ("#1e293b" if st.session_state.active_tab != "Dashboard" else "linear-gradient(135deg, #667eea 0%, #764ba2 100%)") + """ !important;
            box-shadow: """ + ("inset 0 -4px 0 0 #667eea" if st.session_state.active_tab == "Dashboard" else "none") + """ !important;
        }
        
        /* Analyse button specific */
        button[key="tab_analyse"] {
            background: """ + ("#1e293b" if st.session_state.active_tab != "Analyse" else "linear-gradient(135deg, #667eea 0%, #764ba2 100%)") + """ !important;
            box-shadow: """ + ("inset 0 -4px 0 0 #667eea" if st.session_state.active_tab == "Analyse" else "none") + """ !important;
        }
        
        /* Logout button */
        button[key="logout_btn"] {
            background: #1e293b !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    # Create sticky navigation bar
    st.markdown('<div class="nav-bar-container">', unsafe_allow_html=True)
    
    # # Dark container for tabs
    # st.markdown(
    #     """
    #     <div style='background: linear-gradient(135deg, #020617 0%, #050b1a 45%, #0a1025 100%); 
    #          padding: 1.5rem 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )
    
    # Tab buttons in columns - remove type parameter
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("📊 DASHBOARD", key="tab_dashboard", use_container_width=True):
            st.session_state.active_tab = "Dashboard"
            st.rerun()
    
    with col2:
        if st.button("📈 ANALYSE", key="tab_analyse", use_container_width=True):
            st.session_state.active_tab = "Analyse"
            st.rerun()
    
    with col3:
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.in_app = False
            st.session_state.active_tab = "Dashboard"
            st.rerun()
    st.divider()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Render content based on active_tab
    if st.session_state.active_tab == "Dashboard":
        dashboard()
    else:
        analyse_dashboard()

st.set_page_config(
    page_title="Procurement Manager",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "in_app" not in st.session_state:
    st.session_state.in_app = False

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"

if not st.session_state.logged_in:
    login()
else:
    if not st.session_state.in_app:
        landing_page()
    else:
        app_with_tabs()
