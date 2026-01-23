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
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,400..900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400..900;1,400..900&family=Roboto:ital,wght@0,100..900;1,100..900&display=swap');
        
        .landing-header {
            text-align: left;
            font-size: 3rem !important;
            font-weight: 700 !important;
            font-family: 'Playfair Display', serif !important;
            font-style: italic !important;
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
            background: linear-gradient(135deg, #f5b3fd 0%, #f9879b 100%);
        }
        .card-title {
            font-size: 2rem;
            font-weight: 700;
            color: white;
            margin-bottom: 1rem;
            font-family: 'Roboto', sans-serif;
        }
        .custom-card.analyse .card-title {
            color: #1a1a1a;
            font-weight: 700 !important;
        }
        .card-desc {
            font-size: 1rem;
            color: rgba(255,255,255,0.9);
            text-align: left;
            margin-left: 2rem;
            font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;
        }
        .custom-card.analyse .card-desc {
            color: rgba(26,26,26,0.9);
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
                <div class='card-title'>SOURCING AUTOMATION</div>
                <div class='card-desc'>
                <br>
                    • BOM validation & cleanup<br>
                    • Smart supplier matching<br>
                    • Automated RFI outreach
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Go to Sourcing Automation", key="dash_btn", use_container_width=True):
            st.session_state.in_app = True
            st.session_state.active_tab = "SourcingAutomation"
            st.rerun()
    
    with col4:
        st.markdown(
            """
            <div class='custom-card analyse'>
                <div class='card-title'>SOURCING INSIGHTS</div>
                <br>
                <div class='card-desc'>
                    • Live request tracking<br>
                    • Supplier & RFI insights<br>
                    • Status-based analytics
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Go to Sourcing Insights", key="analyse_btn", use_container_width=True):
            st.session_state.in_app = True
            st.session_state.active_tab = "SourcingInsights"
            st.rerun()

def login():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600;700&family=Poppins:wght@500;700&display=swap');
        
        .login-header {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            color: #2c3e50;
            font-family: 'Playfair Display', serif;
            margin-bottom: 0.5rem;
            letter-spacing: 2px;
        }
        
        .login-subtitle {
            text-align: center;
            color: #7f8c8d;
            font-size: 1rem;
            font-family: 'Inter', sans-serif;
            margin-bottom: 3rem;
        }
        
        .login-card {
            background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 20px;
            padding: 1rem 1rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
        
        .login-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1e293b;
            font-family: 'Poppins', sans-serif;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        /* Style the input containers */
        div[data-testid="stTextInput"] > div > div {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        div[data-testid="stTextInput"] > div > div:focus-within {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Style the input fields */
        input {
            font-family: 'Inter', sans-serif !important;
            font-size: 0.95rem !important;
            padding: 0.75rem 1rem !important;
        }
        
        /* Style the login button */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            font-weight: 600 !important;
            font-family: 'Poppins', sans-serif !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-size: 1rem !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("<h1 class='login-header'>PROCUREMENT MANAGER</h1>", unsafe_allow_html=True)
    # st.markdown("<p class='login-subtitle'>Request Processing & Supplier Management</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-card login-title'>🔐 Sign In</div>", unsafe_allow_html=True)
        
        user = st.text_input("Username", label_visibility="collapsed", placeholder="Enter username", key="login_user")
        pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password", key="login_pwd")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Sign In", use_container_width=True, key="login_btn"):
            if user == USERNAME and pwd == PASSWORD:
                st.session_state.logged_in = True
                st.session_state.in_app = False
                st.session_state.active_tab = "SourcingAutomation"
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        # st.markdown("</div>", unsafe_allow_html=True)

def app_with_tabs():

    # ---------------- SLIDER POSITION ----------------
    slider_left = "0%" if st.session_state.active_tab == "SourcingAutomation" else "42%"

    st.markdown(
        f"""
        <style>
        /* ========== NAVBAR CONTAINER ========== */
        .nav-bar-container {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: white;
            padding-bottom: 1.4rem;
            border-bottom: 1px solid #e2e8f0;
            margin-bottom: 1.5rem;
        }}

        .nav-inner {{
            position: relative;
        }}

        /* ONLY NAVBAR BUTTONS */
        .nav-inner button {{
            height: 60px !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            transition: all 0.25s ease !important;
        }}

        /* ACTIVE / INACTIVE STATES */
        .nav-supplier {{
            background: {"linear-gradient(135deg, #667eea 0%, #764ba2 100%)" if st.session_state.active_tab == "SourcingAutomation" else "#f8fafc"} !important;
            color: {"white" if st.session_state.active_tab == "SourcingAutomation" else "#64748b"} !important;
        }}

        .nav-dashboard {{
            background: {"linear-gradient(135deg, #f5b3fd 0%, #f9879b 100%)" if st.session_state.active_tab == "SourcingInsights" else "#f8fafc"} !important;
            color: {"white" if st.session_state.active_tab == "SourcingInsights" else "#64748b"} !important;
        }}
        
        /* ========== PRIMARY BUTTON STYLING ========== */
        button[kind="primary"] {{
            background-color: #589532 !important;
            color: white !important;
            border: 2px solid #4a7d2a !important;
        }}

        button[kind="primary"]:hover {{
            background-color: #4a7d2a !important;
            border-color: #3d6622 !important;
        }}

        button[data-testid="baseButton-primary"]:not([key*="nav_"]) {{
            background-color: #589444 !important;
            color: white !important;
        }}
        
        button[data-testid="baseButton-primary"]:not([key*="nav_"]):hover {{
            background-color: #4a7d2a !important;
        }}
        
        
        
        .nav-logout {{
            background: #ef4444 !important;
            color: white !important;
        }}
        
        /* Override button styling for navigation buttons specifically */
        .stButton:has(+ div.nav-supplier) button,
        .stButton:has(+ div.nav-dashboard) button,
        .stButton:has(+ div.nav-logout) button {{
            border: none !important;
        }}
        
        .stButton:has(+ div.nav-supplier) button {{
            background: {"linear-gradient(135deg, #667eea 0%, #764ba2 100%)" if st.session_state.active_tab == "SourcingAutomation" else "#f8fafc"} !important;
            color: {"white" if st.session_state.active_tab == "SourcingAutomation" else "#64748b"} !important;
        }}
        
        .stButton:has(+ div.nav-dashboard) button {{
            background: {"linear-gradient(135deg, #f5b3fd 0%, #f9879b 100%)" if st.session_state.active_tab == "SourcingInsights" else "#f8fafc"} !important;
            color: {"white" if st.session_state.active_tab == "SourcingInsights" else "#64748b"} !important;
        }}
        
        .stButton:has(+ div.nav-logout) button {{
            background: #ef4444 !important;
            color: white !important;
        }}

        /* SLIDER */
        .nav-slider {{
            position: absolute;
            bottom: -6px;
            left: {slider_left};
            width: 41.5%;
            height: 4px;
            background: {"linear-gradient(135deg, #667eea 0%, #764ba2 100%)" if st.session_state.active_tab == "SourcingAutomation" else "linear-gradient(135deg, #f5b3fd 0%, #f9879b 100%)"};
            border-radius: 4px;
            transition: left 0.35s ease;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    # ---------------- NAVBAR START ----------------
    # st.markdown(
    #     '<div class="nav-bar-container"><div class="nav-inner">',
    #     unsafe_allow_html=True
    # )

    col1, col2, col3 = st.columns([2.5, 2.5, 1])

    with col1:
        if st.button("Sourcing Automation", key="nav_supplier", use_container_width=True):
            st.session_state.active_tab = "SourcingAutomation"
            st.rerun()
        st.markdown('<div class="nav-supplier"></div>', unsafe_allow_html=True)

    with col2:
        if st.button("Sourcing Insights", key="nav_dashboard", use_container_width=True):
            st.session_state.active_tab = "SourcingInsights"
            st.rerun()
        st.markdown('<div class="nav-dashboard"></div>', unsafe_allow_html=True)

    with col3:
        if st.button("Logout", key="nav_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.in_app = False
            st.session_state.active_tab = "SourcingAutomation"
            st.rerun()
        st.markdown('<div class="nav-logout"></div>', unsafe_allow_html=True)

    # SLIDER
    st.markdown('<div class="nav-slider"></div>', unsafe_allow_html=True)

    # NAVBAR END
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ---------------- PAGE CONTENT ----------------
    if st.session_state.active_tab == "SourcingAutomation":
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
    st.session_state.active_tab = "SourcingAutomation"

if not st.session_state.logged_in:
    login()
else:
    if not st.session_state.in_app:
        landing_page()
    else:
        app_with_tabs()
