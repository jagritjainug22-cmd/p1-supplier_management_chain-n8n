import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ================= GOOGLE SHEETS =================

SHEET_ID = "1U6ml01UyidEPDYVqs994oSHV0eLaPX89yCG-QflD9Vc"
SHEET_NAME = "Requests"
CREDS_PATH = "creds/service_account.json"


@st.cache_data(show_spinner=False)
def load_sheet_data():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        CREDS_PATH,
        scopes=scopes
    )

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

    data = sheet.get_all_records()
    return pd.DataFrame(data)


def render_recent_request_card(request_data):
    """Render the most recent request as a highlighted card"""
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #d4a574 0%, #c89968 100%);
            padding: 1rem;
            border-radius: 16px;
            color: white;
            box-shadow: 0 8px 24px rgba(212, 165, 116, 0.4);
            margin-bottom: 1rem;
                margin-top: 1.2rem;
            font-family: 'Roboto', sans-serif;
            width: 22%;
        ">
            <p style="margin: 0; color: white; font-size: 1.2rem; margin-left: 1rem;">Most Recent Request</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Request ID</p><p style='font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;'>{request_data.get('request_id', 'N/A')}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Project Code</p><p style='font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;'>{request_data.get('project_code', 'N/A')}</p>", unsafe_allow_html=True)
    with col3:
        status = request_data.get('status', 'N/A')
        if status == "RFIs sent":
            st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Status</p><p style='font-size: 1rem; font-weight: 600; margin-top: 0.2rem; color: #28a745;'>✅ {status}</p>", unsafe_allow_html=True)
        elif status == "Follow-up sent":
            st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Status</p><p style='font-size: 1rem; font-weight: 600; margin-top: 0.2rem; color: #ffc107;'>⏳ {status}</p>", unsafe_allow_html=True)
        elif status == "Complete":
            st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Status</p><p style='font-size: 1rem; font-weight: 600; margin-top: 0.2rem; color: #28a745;'>🎉 {status}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Status</p><p style='font-size: 1rem; font-weight: 600; margin-top: 0.2rem; color: #17a2b8;'>📝 {status}</p>", unsafe_allow_html=True)
    with col4:
        created_at = request_data.get('created_at', 'N/A')
        # Convert pandas Timestamp to string if needed
        if isinstance(created_at, pd.Timestamp):
            created_at = created_at.strftime('%Y-%m-%d %H:%M')
        elif created_at != 'N/A':
            created_at = str(created_at)
        st.markdown(f"<p style='font-size: 0.85rem; margin-bottom: 0; color: #7f8c8d;'>Created</p><p style='font-size: 1.1rem; font-weight: 600; margin-top: 0.2rem;'>{created_at}</p>", unsafe_allow_html=True)
    
    
    # Show RFI Summary or Follow-up report if available in session
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.get('rfi_result') and st.session_state.get('current_request_id') == request_data.get('request_id'):
            with st.expander("📤 Recent RFI Summary", expanded=False):
                rfi = st.session_state.rfi_result
                st.markdown(f"**Total RFIs Sent:** {rfi.get('total_rfis_sent', 0)}")
                st.markdown(f"**Suppliers Contacted:** {rfi.get('suppliers_contacted', 0)}")
                st.markdown(f"**Project Code:** {rfi.get('project_code', 'N/A')}")
    
    with col2:
        if st.session_state.get('followup_preview') and st.session_state.get('current_request_id') == request_data.get('request_id'):
            with st.expander("📧 Recent Follow-up Preview", expanded=False):
                preview = st.session_state.followup_preview
                if isinstance(preview, list):
                    preview = preview[0] if preview else {}
                st.markdown(f"**To:** {preview.get('email_to', 'N/A')}")
                st.markdown(f"**Subject:** {preview.get('email_subject', 'N/A')}")


# ================= ANALYSE DASHBOARD =================

def analyse_dashboard():
    """Enhanced analyse dashboard with recent requests and pending items"""
    # Add Google Fonts and Card Styles
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&family=Poppins:wght@500;700&family=Roboto+Mono:wght@400&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap');
    
    .custom-card {
        background: linear-gradient(135deg, #f5b3fd 0%, #f9879b 100%);
        border-radius: 20px;
        border-left: 5px solid rgba(0, 0, 0, 0.9);
        padding: 0.5rem;
        width: 80%;
        min-height: 150px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2), -3px 0 15px rgba(0,0,0,0.6);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 1.2rem;
        position: relative;
    }
    .custom-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.3), -3px 0 20px rgba(0,0,0,0.8);
    }
    .card-title {
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0;
        margin-left: 2rem;
        text-align: left;
        font-family: 'Playfair Display', serif;
    }
    .card-desc {
        font-size: 1rem;
        color: rgba(26,26,26,0.9);
        text-align: left;
        margin-left: 2rem;
        margin-top: 0;
        font-family: 'Roboto', 'Segoe UI', 'Poppins', sans-serif;
    }
    
    /* Span tab buttons wider */
    div[data-baseweb="tab-list"] button {
        flex-grow: 1;
        min-width: 200px;
    }
    
    /* Make dropdown cursors clickable */
    div[data-baseweb="select"] {
        cursor: pointer;
    }
    div[data-baseweb="select"] > div {
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Scroll to top of page
    st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
    
    # Top navigation bar with title card
    col1, col2, col3 = st.columns([0.0000001,4.5, 0.1])
    
    with col2:
        st.markdown("""
            <div class='custom-card'>
                <div class='card-title'>Sourcing Insights</div>
                <div class='card-desc'>
                    Manage sourcing requests, track RFIs, and monitor follow-ups all in one place.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ---------- LOAD DATA ----------
    try:
        full_df = load_sheet_data()
    except Exception as e:
        st.error("Failed to load Google Sheet data")
        st.exception(e)
        return

    if full_df.empty:
        st.warning("No data found in the sheet")
        return

    # Sort by created_at to get most recent
    if 'created_at' in full_df.columns:
        full_df['created_at'] = pd.to_datetime(full_df['created_at'], errors='coerce')
        full_df = full_df.sort_values('created_at', ascending=False)
    
    # Normalize status column
    if 'status' in full_df.columns:
        full_df['status'] = full_df['status'].astype(str).str.strip()
    
    # Calculate metrics
    total_requests = len(full_df)
    if 'status' in full_df.columns:
        pending_requests = len(full_df[full_df['status'].str.lower() == 'awaiting additional info'])
        rfis_sent = len(full_df[full_df['status'].str.lower().str.contains('rfi', na=False)])
        # Completed = RFIs Sent + Awaiting additional info
        completed_requests = rfis_sent + pending_requests
    else:
        pending_requests = 0
        completed_requests = 0
        rfis_sent = 0
    
    # ---------- MOST RECENT REQUEST ----------
    if len(full_df) > 0:
        most_recent = full_df.iloc[0].to_dict()
        render_recent_request_card(most_recent)
        st.divider()
    
    # ---------- KEY METRICS ----------
    st.markdown("### 📊 Overview Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("📋 Total Requests", total_requests)
    col2.metric("⏳ Pending Follow-ups", pending_requests, 
                delta=f"{(pending_requests/total_requests*100):.1f}%" if total_requests > 0 else "0%",
                delta_color="inverse")
    col3.metric("✅ Completed", completed_requests,
                delta=f"{(completed_requests/total_requests*100):.1f}%" if total_requests > 0 else "0%",
                delta_color="normal")
    col4.metric("📤 RFIs Sent", rfis_sent,
                delta=f"{(rfis_sent/total_requests*100):.1f}%" if total_requests > 0 else "0%",
                delta_color="normal")
    
    st.divider()
    
    # ---------- TAB NAVIGATION ----------
    tab1, tab2, tab3 = st.tabs(["📊 All Requests", "📤 RFIs Sent", "⏳ Pending Follow-ups"])
    
    # ========== TAB 1: ALL REQUESTS ==========
    with tab1:
        col1, col2, col3 = st.columns(3)

        with col1:
            status_options = ["All"] + sorted(
                full_df["status"].dropna().astype(str).unique().tolist()
            )
            selected_status = st.selectbox(
                "Request Status",
                status_options,
                index=0,
                key="tab1_status"
            )
        
        with col2:
            if 'project_code' in full_df.columns:
                project_options = ["All"] + sorted(
                    full_df["project_code"].dropna().astype(str).unique().tolist()
                )
                selected_project = st.selectbox(
                    "Project Code",
                    project_options,
                    index=0,
                    key="tab1_project"
                )
            else:
                selected_project = "All"
        
        with col3:
            # Date range filter
            if 'created_at' in full_df.columns:
                date_filter = st.selectbox(
                    "Time Period",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"],
                    index=0,
                    key="tab1_date"
                )
            else:
                date_filter = "All Time"

        # ---------- APPLY FILTERS ----------
        view_df = full_df.copy()
        
        if selected_status != "All":
            view_df = view_df[view_df["status"] == selected_status]
        
        if selected_project != "All" and 'project_code' in view_df.columns:
            view_df = view_df[view_df["project_code"] == selected_project]
        
        if date_filter != "All Time" and 'created_at' in view_df.columns:
            now = pd.Timestamp.now()
            if date_filter == "Last 7 Days":
                cutoff = now - pd.Timedelta(days=7)
            elif date_filter == "Last 30 Days":
                cutoff = now - pd.Timedelta(days=30)
            elif date_filter == "Last 90 Days":
                cutoff = now - pd.Timedelta(days=90)
            view_df = view_df[view_df['created_at'] >= cutoff]
        
        st.divider()
        
        # ---------- FILTERED METRICS ----------
        if len(view_df) < len(full_df):
            st.markdown(f"### 📋 Filtered Results ({len(view_df)} requests)")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Showing", len(view_df))
            col2.metric("Unique Projects", view_df["project_code"].nunique() if "project_code" in view_df.columns else 0)
            col3.metric("Statuses", view_df["status"].nunique() if "status" in view_df.columns else 0)
            
            st.divider()

        # ---------- DATA TABLE ----------
        st.markdown("### 📋 Requests Data Table")
        
        # Add download button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            csv = view_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"requests_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Style the dataframe
        def highlight_status(row):
            if row.get('status') == 'Complete':
                return ['background-color: #d4edda'] * len(row)
            elif row.get('status') == 'Awaiting additional info':
                return ['background-color: #fff3cd'] * len(row)
            elif 'RFI' in str(row.get('status', '')):
                return ['background-color: #d1ecf1'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = (
            view_df
            .style
            .apply(highlight_status, axis=1)
            .set_properties(**{
                "border-color": "#e0e0e0",
                "font-size": "13px",
                "padding": "8px"
            })
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#2c3e50"),
                        ("color", "white"),
                        ("font-weight", "600"),
                        ("border", "1px solid #e0e0e0"),
                        ("padding", "12px")
                    ]
                }
            ])
        )

        st.dataframe(
            styled_df,
            use_container_width=True,
            height=520
        )
    
    # ========== TAB 2: RFIs SENT ==========
    with tab2:
        st.markdown("### 📤 RFIs Sent")
        
        if rfis_sent > 0:
            rfi_df = full_df[full_df['status'].str.lower().str.contains('rfi', na=False)].copy()
            
            st.caption(f"Showing {len(rfi_df)} requests with RFIs sent")
            st.divider()
            
            # Display RFI requests in cards
            for idx, row in rfi_df.iterrows():
                created = row.get('created_at', 'N/A')
                if isinstance(created, pd.Timestamp):
                    created = created.strftime('%Y-%m-%d %H:%M')
                
                with st.container():
                    st.markdown(f"""
                        <div style="
                            border-left: 4px solid #17a2b8;
                            padding: 16px;
                            background-color: #d1ecf1;
                            border-radius: 8px;
                            margin-bottom: 12px;
                        ">
                            <strong>📤 Request ID:</strong> {row.get('request_id', 'N/A')} | 
                            <strong>Project:</strong> {row.get('project_code', 'N/A')} | 
                            <strong>Created:</strong> {created}
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Download button for RFI data
            csv = rfi_df.to_csv(index=False)
            st.download_button(
                label="📥 Download RFI Data",
                data=csv,
                file_name=f"rfi_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=False
            )
        else:
            st.info("No requests with RFIs sent found.")
    
    # ========== TAB 3: PENDING FOLLOW-UPS ==========
    with tab3:
        st.markdown("### Pending Follow-ups")
        
        if pending_requests > 0:
            pending_df = full_df[full_df['status'].str.lower() == 'awaiting additional info'].copy()
            
            st.caption(f"Showing {len(pending_df)} requests awaiting follow-up responses")
            st.divider()
            
            # Display pending requests in cards
            for idx, row in pending_df.iterrows():
                created = row.get('created_at', 'N/A')
                if isinstance(created, pd.Timestamp):
                    created = created.strftime('%Y-%m-%d %H:%M')
                
                with st.container():
                    st.markdown(f"""
                        <div style="
                            border-left: 4px solid #ffc107;
                            padding: 16px;
                            background-color: #fff9e6;
                            border-radius: 8px;
                            margin-bottom: 12px;
                        ">
                            <strong>Request ID:</strong> {row.get('request_id', 'N/A')} | 
                            <strong>Project:</strong> {row.get('project_code', 'N/A')} | 
                            <strong>Created:</strong> {created}
                        </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Download button for pending data
            csv = pending_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Pending Data",
                data=csv,
                file_name=f"pending_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=False
            )
        else:
            st.success("✅ No pending follow-ups! All requests have been addressed.")
