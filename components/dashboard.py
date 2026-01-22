import streamlit as st
import requests
import time
from streamlit_lottie import st_lottie
import json
from enum import Enum

class ProcessingState(str, Enum):
    IDLE = "idle"
    START_EXECUTION = "start_execution"
    SHOW_STATUS = "show_status"
    SECOND_INTERMEDIATE = "second_intermediate"
    SHOW_STATUS_2 = "show_status_2"
    RESUME_EXECUTION = "resume_execution"
    DONE = "done"
    ERROR = "error"
    # Supplier matching states
    SUPPLIER_START = "supplier_start"
    SUPPLIER_SHOW_1 = "supplier_show_1"
    SUPPLIER_CALL_2 = "supplier_call_2"
    SUPPLIER_SHOW_2 = "supplier_show_2"
    SUPPLIER_CALL_3 = "supplier_call_3"
    SUPPLIER_SHOW_3 = "supplier_show_3"
    SUPPLIER_CALL_4 = "supplier_call_4"
    SUPPLIER_SHOW_4 = "supplier_show_4"
    SUPPLIER_FINAL = "supplier_final"
    SUPPLIER_DONE = "supplier_done"
    SUPPLIER_ERROR = "supplier_error"
    # RFI sending states
    RFI_START = "rfi_start"
    RFI_SHOW_1 = "rfi_show_1"
    RFI_CALL_2 = "rfi_call_2"
    RFI_SHOW_2 = "rfi_show_2"
    RFI_CALL_3 = "rfi_call_3"
    RFI_DONE = "rfi_done"
    RFI_ERROR = "rfi_error"


def load_lottie_file(filepath):
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception:
        return None

# Try to load lottie animation; capture failure as None so UI can show an error
lottie_animation = load_lottie_file("assets/plane_animation.json")
lottie_load_error = None
if lottie_animation is None:
    lottie_load_error = "Could not load animation from assets/plane_animation.json"

ANIMATION_DURATION_SECONDS = 10  # 121 frames @ ~60 FPS

# You'll need to pass config from main.py or define here
N8N_BASE_URL = "http://localhost:5678/webhook-test/"
SHEET_ID = "1U6ml01UyidEPDYVqs994oSHV0eLaPX89yCG-QflD9Vc"

# ================= ALL HELPER FUNCTIONS =================


def is_bom_validation_locked(email_index):
    return (
        st.session_state.get("processed_email_index") == email_index
        and st.session_state.get("process_result")
        and st.session_state.get("process_result").get("next_action") == "send-followup"
    )


def process_email_api_call(email, email_index):
    try:
        res = requests.post(
            f"{N8N_BASE_URL}process-single-email",
            json=email,
            timeout=300
        )
        res.raise_for_status()
        response_data = res.json()

        if isinstance(response_data, list) and len(response_data) > 0:
            response_data = response_data[0]

        # Store results
        st.session_state.process_result = response_data
        st.session_state.current_request_id = response_data.get("request_id")
        st.session_state.processed_email_index = email_index

        # ✅ ROUTE IMMEDIATELY BASED ON ACTION
        next_action = response_data.get("next_action")

        if next_action == "match_suppliers":
            st.session_state["tab_unlocked"][2] = True
            st.session_state.current_tab = 2

        elif next_action == "send-followup":
            st.session_state["tab_unlocked"][3] = True   # BOM Validation
            st.session_state.current_tab = 3

        # Status update
        request_id = response_data.get("request_id")
        if request_id:
            latest_status = fetch_status_from_sheet(request_id)
            st.session_state.email_status_map[email_index] = latest_status

        st.session_state.process_success = True
        st.session_state.is_processing = False
        st.session_state.process_error = None

        return response_data

    except Exception as e:
        st.session_state.is_processing = False
        st.session_state.process_success = False
        st.session_state.process_error = str(e)
        return None



def render_email_details(email):
    """Render email details"""
    st.markdown("### Email Details")
    st.markdown(f"**Subject:** {email.get('subject', 'N/A')}")
    st.markdown(f"**From:** {email.get('from', {}).get('text', 'N/A')}")
    
    date_str = email.get('date', 'N/A')
    if date_str != 'N/A':
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%B %d, %Y at %I:%M %p")
            st.markdown(f"**Date:** {formatted_date}")
        except:
            st.markdown(f"**Date:** {date_str}")
    else:
        st.markdown(f"**Date:** {date_str}")
    
    st.divider()

    if email.get("html"):
        st.components.v1.html(email["html"], height=400, scrolling=True)
    else:
        st.text(email.get("text", ""))


@st.dialog("Processing Complete")
def show_processing_complete_dialog(status_message, next_action):
    """Show final processing status with OK button"""
    
    # Show different message based on next_action
    if next_action == "send-followup":
        st.error("❌ Processing incomplete — BOM requires follow-up!")
        bom_status = "BOM Incomplete"
    else:
        st.success("✅ Processing complete!")
        bom_status = "BOM Complete" if next_action == "match_suppliers" else "Processing Complete"
    
    st.info(f"**Status:** {bom_status}")
    
    st.divider()
    
    if next_action == "match_suppliers":
        st.markdown("**Next Step:** Supplier Shortlisting")
    elif next_action == "send-followup":
        st.markdown("**Next Step:** BOM Validation")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("OK", use_container_width=True, type="primary"):
            st.session_state.show_completion_dialog = False
            st.session_state.current_tab = 0
            st.rerun()

@st.dialog("Supplier Matching Complete")
def show_supplier_matching_complete_dialog():
    """Show supplier matching completion dialog"""
    st.success("✅ Supplier matching complete!")
    
    st.info(f"**Status:** Suppliers matched")
    st.divider()
    
    st.markdown("**Next Action:** Select suppliers and send RFIs")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("OK", use_container_width=True, type="primary"):
            st.session_state.show_supplier_completion_dialog = False
            st.session_state.current_tab = 1
            st.rerun()

@st.dialog("RFI Distribution Complete")
def show_rfi_complete_dialog():
    """Show RFI sending completion dialog"""
    st.success("✅ RFI distribution complete!")
    
    st.info(f"**Status:** RFIs sent successfully")
    st.divider()
    st.markdown("**Next Action:** View RFI Summary")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("OK", use_container_width=True, type="primary"):
            st.session_state.show_rfi_completion_dialog = False
            st.session_state.current_tab = 1
            st.rerun()

@st.dialog("Follow-up Sent")
def show_followup_sent_dialog(recipient_email):
    """Show follow-up sent confirmation dialog"""
    st.success(f"The follow-up email has been sent to {recipient_email}")
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("OK", use_container_width=True, type="primary"):
            st.session_state.show_followup_sent_dialog = False
            # Update status to Complete and show request complete dialog
            email_index = st.session_state.selected_email_index
            if email_index is not None:
                st.session_state.email_status_map[email_index] = "Complete"
            st.session_state.show_request_complete_dialog = True
            # Navigate to email details tab
            st.session_state.current_tab = 1
            st.rerun()

@st.dialog("Request Complete")
def show_request_complete_dialog(request_id):
    """Show request completion dialog with link to analyse dashboard"""
    st.success(f"✅ Finished processing request: {request_id}")
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("View in Analytics Dashboard", use_container_width=True, type="primary"):
            st.session_state.show_request_complete_dialog = False
            # Navigate to analyse dashboard
            st.session_state.show_dashboard = False
            st.session_state.show_analyse = True
            st.session_state.analyse_request_id = request_id
            st.rerun()

@st.dialog("Follow-up Email Preview")
def show_followup_dialog(preview):
    if isinstance(preview, list):
        preview = preview[0] if preview else {}
    
    st.divider()
    st.markdown(f"**To:** {preview.get('email_to')}")
    st.markdown(f"**Subject:** {preview.get('email_subject')}")
    st.divider()
    st.components.v1.html(preview.get("email_body", ""), height=600, scrolling=True)
    st.divider()
    
    if preview.get('drive_web_link'):
        st.subheader("📎 Attachments")
        render_attachment_preview(
            preview.get('drive_file_name', 'Attachment'),
            preview.get('drive_web_link')
        )
        st.divider()


def fetch_status_from_sheet(request_id):
    """Fetch status from Google Sheets via API"""
    try:
        res = requests.post(
            f"{N8N_BASE_URL}get-status",
            json={"request_id": request_id},
            timeout=10
        )
        if res.ok:
            return res.json().get("status", "Unknown")
    except Exception:
        pass
    return "Status unavailable"


def is_email_processing_complete(status):
    """Check if email processing is complete based on status"""
    completed_statuses = ["Complete", "Follow-up sent"]
    return status in completed_statuses


def reset_processing_states():
    """Reset all processing states for a new email"""
    st.session_state.process_result = None
    st.session_state.processing_state = ProcessingState.IDLE
    st.session_state.resume_url = None
    st.session_state.status_message = None
    st.session_state.process_error = None
    st.session_state.show_completion_dialog = False
    
    # Reset supplier matching
    st.session_state.supplier_matching_state = ProcessingState.IDLE
    st.session_state.supplier_resume_url = None
    st.session_state.supplier_status_message = None
    st.session_state.supplier_matching_error = None
    st.session_state.show_supplier_completion_dialog = False
    st.session_state.supplier_matches = []
    st.session_state.selected_suppliers = {}
    
    # Reset RFI sending
    st.session_state.rfi_sending_state = ProcessingState.IDLE
    st.session_state.rfi_resume_url = None
    st.session_state.rfi_status_message = None
    st.session_state.rfi_sending_error = None
    st.session_state.show_rfi_completion_dialog = False
    st.session_state.rfi_sent = False
    st.session_state.rfi_result = None
    st.session_state.rfi_payload = None
    st.session_state.suppliers_without_email = {}
    st.session_state.suppliers_contacted_list = {}
    
    # Reset follow-up
    st.session_state.followup_preview = None
    st.session_state.followup_sent = False
    st.session_state.is_preparing_followup = False
    st.session_state.followup_prep_error = None


# Removed synchronous trigger_supplier_matching - now using state machine


def render_supplier_selection_table(item, email_index):
    """Render supplier selection table with enhanced styling and features"""
    st.markdown(f"#### {item['item_code']} — {item['item_description']}")
    st.markdown(f"*Spec:* {item['item_specification']} | *Material:* {item['item_material']}")
    st.divider()

    selected = st.session_state.setdefault("selected_suppliers", {})
    
    # Add select all / deselect all buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    with col1:
        if st.button("✓ Select All", key=f"select_all_{item['item_code']}_{email_index}", use_container_width=True):
            for s in item.get("suppliers", []):
                key = f"{item['item_code']}::{s['supplier_id']}"
                selected[key] = True
            st.rerun()
    with col2:
        if st.button("✗ Clear All", key=f"clear_all_{item['item_code']}_{email_index}", use_container_width=True):
            for s in item.get("suppliers", []):
                key = f"{item['item_code']}::{s['supplier_id']}"
                selected[key] = False
            st.rerun()
    with col3:
        selected_count = sum(1 for s in item.get("suppliers", []) if selected.get(f"{item['item_code']}::{s['supplier_id']}", False))
        st.info(f"**{selected_count}** selected")
    
    st.divider()
    
    # Helper function to get confidence badge color
    def get_confidence_badge(confidence):
        conf = str(confidence).upper()
        if conf == 'HIGH':
            return '<span style="background-color: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">🔥 HIGH</span>'
        elif conf == 'MEDIUM':
            return '<span style="background-color: #ffc107; color: black; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">⚡ MEDIUM</span>'
        elif conf == 'LOW':
            return '<span style="background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">⚠️ LOW</span>'
        else:
            return '<span style="background-color: #6c757d; color: white; padding: 4px 12px; border-radius: 12px; font-weight: 600; font-size: 0.85em;">N/A</span>'
    
    # Display each supplier as a card
    for idx, s in enumerate(item.get("suppliers", [])):
        key = f"{item['item_code']}::{s['supplier_id']}"
        is_checked = selected.get(key, s.get("rank") == 1)
        
        # Determine card border color based on rank
        if s.get("rank") == 1:
            border_color = "#28a745"  # Green for rank 1
            border_style = "3px solid"
        elif s.get("recommended"):
            border_color = "#ffc107"  # Yellow for recommended
            border_style = "2px solid"
        else:
            border_color = "#dee2e6"  # Gray for others
            border_style = "1px solid"
        
        # Card container with styling
        card_style = f"""
        <div style="
            border: {border_style} {border_color};
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
        ">
        """
        
        st.markdown(card_style, unsafe_allow_html=True)
        
        cols = st.columns([0.5, 0.4, 2, 2.5, 1.2, 1.2, 1.5, 0.8])
        
        with cols[0]:
            selected[key] = st.checkbox("", value=is_checked, key=f"chk_{key}_{email_index}", label_visibility="collapsed")
        
        with cols[1]:
            # Rank badge
            if s.get("rank") == 1:
                st.markdown('<div style="background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 8px; border-radius: 50%; text-align: center; font-weight: bold; font-size: 1.1em; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">🥇</div>', unsafe_allow_html=True)
            elif s.get("rank") == 2:
                st.markdown('<div style="background: linear-gradient(135deg, #6c757d, #adb5bd); color: white; padding: 8px; border-radius: 50%; text-align: center; font-weight: bold; font-size: 1.1em; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">🥈</div>', unsafe_allow_html=True)
            elif s.get("rank") == 3:
                st.markdown('<div style="background: linear-gradient(135deg, #cd7f32, #d4a76a); color: white; padding: 8px; border-radius: 50%; text-align: center; font-weight: bold; font-size: 1.1em; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">🥉</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background: #f8f9fa; color: #495057; padding: 8px; border-radius: 50%; text-align: center; font-weight: bold; border: 2px solid #dee2e6; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">#{s.get("rank")}</div>', unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown(f"**{s['supplier_name']}**")
            if s.get('recommended'):
                st.markdown('<span style="background-color: #ffc107; color: black; padding: 2px 8px; border-radius: 8px; font-size: 0.75em; font-weight: 600;">⭐ RECOMMENDED</span>', unsafe_allow_html=True)
        
        with cols[3]:
            if s.get('supplier_email'):
                st.markdown(f"📧 {s.get('supplier_email')}")
            else:
                st.markdown('<span style="color: #dc3545;">⚠️ No email</span>', unsafe_allow_html=True)
        
        with cols[4]:
            st.markdown(f"📍 {s.get('supplier_city', 'N/A')}")
        
        with cols[5]:
            st.markdown(f"🌍 {s.get('supplier_country', 'N/A')}")
        
        with cols[6]:
            st.markdown(get_confidence_badge(s.get('confidence', 'N/A')), unsafe_allow_html=True)
        
        with cols[7]:
            score = s.get('match_score', 'N/A')
            if score != 'N/A':
                score_val = float(score)
                if score_val >= 80:
                    color = "#28a745"
                elif score_val >= 60:
                    color = "#ffc107"
                else:
                    color = "#dc3545"
                st.markdown(f'<div style="background-color: {color}; color: white; padding: 6px 12px; border-radius: 8px; text-align: center; font-weight: bold;">{score}</div>', unsafe_allow_html=True)
            else:
                st.write(score)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.write("")  # Small spacing
    
    st.divider()
    st.session_state.selected_suppliers = selected


def render_attachment_preview(file_name, file_link, file_size=None):
    """Render attachment as a styled card preview"""
    file_ext = file_name.split('.')[-1].lower() if '.' in file_name else 'file'
    
    icon_map = {
        'pdf': '📄', 'doc': '📝', 'docx': '📝',
        'xls': '📊', 'xlsx': '📊', 'csv': '📊',
        'ppt': '🎬', 'pptx': '🎬',
        'zip': '📦', 'rar': '📦', 'txt': '📄',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
    }
    
    icon = icon_map.get(file_ext, '📎')
    
    col1, col2, col3 = st.columns([0.5, 3, 1])
    
    with col1:
        st.markdown(f"<div style='font-size: 24px; text-align: center;'>{icon}</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{file_name}**")
        if file_size:
            st.caption(f"Size: {file_size}")
    
    with col3:
        st.markdown(f"[Download]({file_link})")


def render_rfi_inline(rfi):
    """Render RFI distribution summary"""
    with st.expander("📊 RFI Distribution Summary", expanded=False):
        st.markdown("### RFI Distribution Summary")

        st.markdown(
            f"""
            **Request ID:** {rfi['request_id']}  
            **Project Code:** {rfi['project_code']}  
            **Total RFIs Sent:** {rfi['total_rfis_sent']}  
            **Suppliers Contacted:** {rfi['suppliers_contacted']}
            """
        )

        st.divider()

        st.components.v1.html(
            rfi["email_body"],
            height=500,
            scrolling=True
        )

    st.divider()

    # Suppliers successfully contacted
    if st.session_state.get("suppliers_contacted_list"):
        with st.expander("Suppliers Successfully Contacted", expanded=False):
            st.divider()
            for item_code, supplier_list in st.session_state.suppliers_contacted_list.items():
                st.markdown(f"**Item:** {item_code}")
                
                supplier_data = []
                for supplier in supplier_list:
                    supplier_data.append({
                        "Supplier": supplier.get('supplier_name', 'N/A'),
                        "Email": supplier.get('supplier_email', 'N/A'),
                        "ID": supplier.get('supplier_id', 'N/A'),
                        "City": supplier.get('supplier_city', 'N/A'),
                        "Country": supplier.get('supplier_country', 'N/A'),
                        "Confidence": supplier.get('confidence', 'N/A').upper(),
                        "Match Score": supplier.get('match_score', 'N/A'),
                        "Rank": supplier.get('rank', 'N/A'),
                    })
                
                st.dataframe(supplier_data, use_container_width=True, hide_index=True)
                st.divider()

    # Suppliers without email
    if st.session_state.get("suppliers_without_email"):
        with st.expander("Suppliers Not Contacted (Missing Email)", expanded=False):
            st.divider()
            for item_code, supplier_list in st.session_state.suppliers_without_email.items():
                st.markdown(f"**Item:** {item_code}")
                
                supplier_data = []
                for supplier in supplier_list:
                    supplier_data.append({
                        "Supplier": supplier.get('supplier_name', 'N/A'),
                        "ID": supplier.get('supplier_id', 'N/A'),
                        "City": supplier.get('supplier_city', 'N/A'),
                        "Country": supplier.get('supplier_country', 'N/A'),
                        "Confidence": supplier.get('confidence', 'N/A').upper(),
                        "Match Score": supplier.get('match_score', 'N/A'),
                        "Rank": supplier.get('rank', 'N/A'),
                    })
                
                st.dataframe(supplier_data, use_container_width=True, hide_index=True)
                st.divider()
    else:
        st.divider()
        st.success("All selected suppliers were contacted successfully with their email addresses!")


# ================= MAIN DASHBOARD FUNCTION =================
def render_processing_inline():
    st.markdown("### Processing Email")
    st.caption("Please wait while the email is being processed.")

    if lottie_animation:
        st_lottie(
            lottie_animation,
            height=180,
            loop=False,          # play once
            speed=1,
            key="inline_processing_once",
        )
    else:
        st.spinner("Processing email...")

def dashboard():
    """Main email processing dashboard"""
    # Scroll to top of page
    st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
    
    # Top navigation bar with title and logout
    col1, col2, col3 = st.columns([1.6,4, 0.1])
    
    with col2:
        st.markdown("<h1 style='color: #2c3e50; margin-bottom: -10px;'>Supplier Discovery</h1>", unsafe_allow_html=True)
    
    st.markdown("<p style='color: #7f8c8d; text-align:center; margin-top: -10px;'>Manage requests, match suppliers, and send RFIs</p>", unsafe_allow_html=True)
    st.divider()
    
    # Auto-scroll to top when switching tabs
    st.write('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)

    # Initialize session state
    for k, v in {
        "emails": [],
        "process_result": None,
        "current_request_id": None,
        "supplier_matches": [],
        "active_item": None,
        "selected_suppliers": {},
        "rfi_result": None,
        "rfi_sent": False,
        "show_rfi": False,
        "suppliers_without_email": {},
        "suppliers_contacted_list": {},
        "followup_preview": None,
        "followup_sent": False,
        "processed_email_index": None,
        "show_followup_preview": False,
        "current_tab": 0,
        "selected_email_index": None,
        "email_status_map": {},
        "is_processing": False,
        "process_error": None,
        "process_success": False,
        # "processing_started": False,
        "processing_email_index": None,
        "is_preparing_followup": False,
        "followup_prep_error": None,
        "followup_prep_success": False,
        "processing_state" : ProcessingState.IDLE,
        "processing_email_index": None,
        "resume_url": None,
        "status_message": None,
        "process_result": None,
        "process_error" : None,
        # Supplier matching state variables
        "supplier_matching_state": ProcessingState.IDLE,
        "supplier_resume_url": None,
        "supplier_status_message": None,
        "supplier_matching_error": None,
        "show_supplier_completion_dialog": False,
        # RFI sending state variables
        "rfi_sending_state": ProcessingState.IDLE,
        "rfi_resume_url": None,
        "rfi_status_message": None,
        "rfi_sending_error": None,
        "show_rfi_completion_dialog": False,
        "rfi_payload": None,
        # Follow-up dialog
        "show_followup_sent_dialog": False,
        "followup_recipient_email": None,
        # Request complete dialog
        "show_request_complete_dialog": False
    }.items():
        st.session_state.setdefault(k, v)

    # Defaults for lottie animation controls
    st.session_state.setdefault("lottie_height", 80)
    st.session_state.setdefault("lottie_position", "center")

    # Track which tabs have been unlocked (visible) to the user.
    # By default only the first tab (Fetch Emails) is visible.
    st.session_state.setdefault("tab_unlocked", {0: True})

    # Sidebar controls for animation settings
    # with st.sidebar.expander("Animation Settings", expanded=False):
        # st.slider("Animation height (px)", 40, 400, value=st.session_state.get("lottie_height", 80), key="lottie_height")
        # st.selectbox("Animation position", ["left", "center", "right"], index=["left", "center", "right"].index(st.session_state.get("lottie_position", "center")), key="lottie_position")

    # Tab navigation - only show Inbox (0) and current active tab
    tab_names = ["Requests", "Request Review", "Supplier Shortlisting", "BOM Validation", "RFI Review"]

    # Always show Inbox (index 0) + current active tab only
    visible_indices = [0]  # Always include Inbox
    if st.session_state.current_tab != 0:
        visible_indices.append(st.session_state.current_tab)
    
    if visible_indices:
        cols = st.columns(len(visible_indices))
        for col, idx in zip(cols, visible_indices):
            tab_name = tab_names[idx]
            with col:
                is_active = st.session_state.current_tab == idx
                # Disable inbox tab when on other tabs (can only return via action buttons)
                is_disabled = (idx == 0 and st.session_state.current_tab != 0)
                if st.button(tab_name, use_container_width=True, key=f"tab_btn_{idx}", 
                            type="primary" if is_active else "secondary",
                            disabled=is_disabled):
                    st.session_state.current_tab = idx
                    st.rerun()
    
    st.divider()

    # TAB 1: Fetch Emails
    if st.session_state.current_tab == 0:
        st.markdown("### Fetch Unread Emails")
        st.divider()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Fetch Unread Emails", use_container_width=True, type="primary", key="fetch_emails_btn"):
                with st.spinner("Fetching unread emails..."):
                    res = requests.post(f"{N8N_BASE_URL}process-emails", timeout=120)
                    res.raise_for_status()
                    st.session_state.emails = res.json() if res.text.strip() else []
                
                if not st.session_state.emails:
                    st.info("No new emails received")
                else:
                    st.success(f"Found {len(st.session_state.emails)} unread email(s)")

        st.divider()
        
        # Display email list
        if st.session_state.emails:
            st.markdown("### Email List")
            for i, email in enumerate(st.session_state.emails):
                # Check if we have cached status
                if i in st.session_state.email_status_map:
                    status_text = st.session_state.email_status_map[i]
                else:
                    status_text = "Not processed"
                
                # Skip completed emails
                if is_email_processing_complete(status_text):
                    continue
                
                date_str = email.get('date', 'N/A')
                formatted_date = 'N/A'
                if date_str != 'N/A':
                    try:
                        from datetime import datetime
                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
                    except:
                        formatted_date = date_str
                
                email_container = st.container(border=True)
                with email_container:
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"📧 **{email.get('subject', 'No Subject')}**")
                        st.caption(f"From: {email.get('from', {}).get('text', 'Unknown')}")
                        st.caption(f"Date: {formatted_date}")

                        st.markdown(f"**Status:** `{status_text}`")

                    with col3:
                        # Determine button text based on status
                        if status_text == "Not processed":
                            button_text = "Process"
                        elif status_text == "BOM Complete":
                            button_text = "Match Suppliers"
                        elif status_text == "BOM Incomplete":
                            button_text = "Preview Follow-up"
                        elif status_text == "Suppliers matched":
                            button_text = "Send RFIs"
                        elif status_text == "RFIs sent":
                            button_text = "View RFI Summary"
                        else:
                            button_text = "Open"
                        
                        if st.button(button_text, key=f"open_email_{i}", use_container_width=True):
                            # Only reset states if switching to a different email
                            if st.session_state.selected_email_index != i:
                                reset_processing_states()
                            
                            st.session_state.selected_email_index = i
                            st.session_state["tab_unlocked"][1] = True
                            
                            # Navigate to appropriate tab based on status
                            if status_text == "BOM Complete":
                                st.session_state["tab_unlocked"][2] = True
                                st.session_state.current_tab = 2
                            elif status_text == "BOM Incomplete":
                                st.session_state["tab_unlocked"][3] = True
                                st.session_state.current_tab = 3
                            elif status_text == "Suppliers matched":
                                st.session_state["tab_unlocked"][2] = True
                                st.session_state.current_tab = 2
                            elif status_text == "RFIs sent":
                                st.session_state["tab_unlocked"][4] = True
                                st.session_state.current_tab = 4
                            else:
                                st.session_state.current_tab = 1
                            st.rerun()

    # TAB 2: Email Details
    elif st.session_state.current_tab == 1:

        # ================= UI ================= #

        st.markdown("### 📄 Email Details")
        st.divider()

        if st.session_state.selected_email_index is not None:
            i = st.session_state.selected_email_index
            email = st.session_state.emails[i]
            render_email_details(email)

            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])

            state = st.session_state.processing_state
            supplier_state = st.session_state.supplier_matching_state
            rfi_state = st.session_state.rfi_sending_state
            
            # Get current email status
            email_status = st.session_state.email_status_map.get(i, "Not processed")
            
            # Show Complete dialog if status is Complete
            if email_status == "Complete" and st.session_state.get("show_request_complete_dialog", False):
                show_request_complete_dialog(st.session_state.current_request_id)
            
            # Show different buttons based on workflow state
            with col2:
                # Show View RFI Summary button if RFIs were sent
                if rfi_state == ProcessingState.RFI_DONE and st.session_state.rfi_sent:
                    if st.button("View RFI Summary", use_container_width=True, type="primary", key="goto_view_rfi_btn"):
                        st.session_state.current_tab = 4
                        st.rerun()
                # Show Send RFIs button if supplier matching is complete
                elif supplier_state == ProcessingState.SUPPLIER_DONE and st.session_state.supplier_matches:
                    if st.button("Send RFIs", use_container_width=True, type="primary", key="goto_send_rfis_btn"):
                        st.session_state.current_tab = 2
                        st.rerun()
                # Show Process Email button if not yet processed
                elif state == ProcessingState.IDLE:
                    if st.button("Process Email", use_container_width=True, type="primary", key="process_email_btn"):
                        st.session_state.processing_email_index = i
                        st.session_state.processing_state = ProcessingState.START_EXECUTION
                        st.rerun()

            st.divider()

            # ================= STATE MACHINE ================= #

            # ────────────────────────────────────────────────
            # START EXECUTION (1st API CALL)
            # ────────────────────────────────────────────────
            if state == ProcessingState.START_EXECUTION:
                with st.spinner("Starting email processing..."):
                    try:
                        res = requests.post(
                            f"{N8N_BASE_URL}process-single-email",
                            json=email,
                            timeout=300
                        )
                        res.raise_for_status()
                        data = res.json()

                        # Expected intermediate response
                        # {
                        #   executionID,
                        #   resumeURL,
                        #   status
                        # }

                        st.session_state.resume_url = data.get("resumeURL")
                        st.session_state.status_message = data.get("status", "Processing...")

                        st.session_state.processing_state = ProcessingState.SHOW_STATUS

                    except Exception as e:
                        st.session_state.process_error = str(e)
                        st.session_state.processing_state = ProcessingState.ERROR

                st.rerun()

            # ────────────────────────────────────────────────
            # SHOW INTERMEDIATE STATUS
            # ────────────────────────────────────────────────
            if state == ProcessingState.SHOW_STATUS:
                st.info(st.session_state.status_message)

                # Small delay so user sees it
                time.sleep(1)

                st.session_state.processing_state = ProcessingState.SECOND_INTERMEDIATE
                st.rerun()

            # ────────────────────────────────────────────────            # SECOND INTERMEDIATE (2nd API CALL)
            # ────────────────────────────────────────────────
            if state == ProcessingState.SECOND_INTERMEDIATE:
                if st.session_state.status_message:
                    st.info(st.session_state.status_message)

                with st.spinner("Continuing processing..."):
                    try:
                        res = requests.post(st.session_state.resume_url, timeout=300)
                        res.raise_for_status()
                        data = res.json()

                        # Expected second intermediate response
                        # {
                        #   executionID,
                        #   resumeURL,
                        #   status
                        # }

                        st.session_state.resume_url = data.get("resumeURL")
                        st.session_state.status_message = data.get("status", "Processing...")

                        st.session_state.processing_state = ProcessingState.SHOW_STATUS_2

                    except Exception as e:
                        st.session_state.process_error = str(e)
                        st.session_state.processing_state = ProcessingState.ERROR

                st.rerun()

            # ────────────────────────────────────────────────
            # SHOW SECOND INTERMEDIATE STATUS
            # ────────────────────────────────────────────────
            if state == ProcessingState.SHOW_STATUS_2:
                st.info(st.session_state.status_message)

                # Small delay so user sees it
                time.sleep(1)

                st.session_state.processing_state = ProcessingState.RESUME_EXECUTION
                st.rerun()

            # ────────────────────────────────────────────────            # RESUME EXECUTION (FINAL API CALL)
            # ────────────────────────────────────────────────
            if state == ProcessingState.RESUME_EXECUTION:
                if st.session_state.status_message:
                    st.info(st.session_state.status_message)

                with st.spinner("Finalizing request..."):
                    try:
                        res = requests.post(st.session_state.resume_url, timeout=300)
                        res.raise_for_status()
                        response_data = res.json()

                        if isinstance(response_data, list) and response_data:
                            response_data = response_data[0]

                        # Save final result
                        st.session_state.process_result = response_data
                        st.session_state.process_success = True
                        
                        # Update request_id and status in email object
                        request_id = response_data.get("request_id")
                        next_action = response_data.get("next_action")
                        
                        if request_id:
                            st.session_state.current_request_id = request_id
                            email_index = st.session_state.selected_email_index
                            
                            # Update the email object with request_id
                            if email_index is not None and email_index < len(st.session_state.emails):
                                st.session_state.emails[email_index]["request_id"] = request_id
                            
                            # Set status based on next_action
                            if next_action == "match_suppliers":
                                st.session_state.email_status_map[email_index] = "BOM Complete"
                            elif next_action == "send-followup":
                                st.session_state.email_status_map[email_index] = "BOM Incomplete"

                        # Routing
                        if next_action == "match_suppliers":
                            st.session_state["tab_unlocked"][2] = True

                        elif next_action == "send-followup":
                            st.session_state["tab_unlocked"][3] = True

                        st.session_state.processing_state = ProcessingState.DONE
                        st.session_state.show_completion_dialog = True

                    except Exception as e:
                        st.session_state.process_error = str(e)
                        st.session_state.processing_state = ProcessingState.ERROR

                st.rerun()

            # ────────────────────────────────────────────────
            # DONE STATE - Show success message and routing
            # ────────────────────────────────────────────────
            if state == ProcessingState.DONE:
                result = st.session_state.process_result
                next_action = result.get("next_action") if result else None
                
                # Show dialog on first completion
                if st.session_state.get("show_completion_dialog", False):
                    show_processing_complete_dialog(
                        st.session_state.status_message,
                        next_action
                    )

            # ────────────────────────────────────────────────
            # ERROR STATE
            # ────────────────────────────────────────────────
            if state == ProcessingState.ERROR:
                if st.session_state.status_message:
                    st.info(st.session_state.status_message)

                st.error(f"❌ Processing failed: {st.session_state.process_error}")
                if st.button("Reset", use_container_width=True):
                    st.session_state.processing_state = ProcessingState.IDLE
                    st.session_state.process_error = None
                    st.session_state.status_message = None
                    st.rerun()

    # TAB 3: Supplier Matching
    elif st.session_state.current_tab == 2:
        st.markdown("### Supplier Matching & RFI")
        st.divider()
        
        result = st.session_state.process_result
        
        if result and result.get("next_action") == "match_suppliers":
            # Determine whether the current processed email matches the selected one
            processed_for_current = (
                st.session_state.get("processed_email_index") is not None
                and st.session_state.get("selected_email_index") is not None
                and st.session_state.get("processed_email_index") == st.session_state.get("selected_email_index")
            )

            # If RFIs were already sent for this request, disable matching and offer navigation to RFI Summary
            match_disabled = bool(st.session_state.get("rfi_sent") and processed_for_current)

            state = st.session_state.supplier_matching_state
            button_disabled = state != ProcessingState.IDLE or match_disabled
            
            # Debug: Show current state
            print(f"DEBUG - Tab 3 - Current supplier matching state: {state}")
            print(f"DEBUG - Tab 3 - Button disabled: {button_disabled}")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Match Suppliers", key=f"match_btn", use_container_width=True, type="primary", disabled=button_disabled):
                    st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_START
                    st.session_state.selected_suppliers = {}
                    st.rerun()

                if match_disabled:
                    if st.button("Go to RFI Summary", key="goto_rfi_from_match", use_container_width=True, type="primary"):
                        st.session_state["tab_unlocked"][4] = True
                        st.session_state.current_tab = 4
                        st.rerun()
            
            st.divider()

            # ================= SUPPLIER MATCHING STATE MACHINE ================= #
            
            # Debug: Check if we reach the state machine
            print(f"DEBUG - Entering state machine with state: {state}")

            # ──────────────────────────────────────────────────
            # SUPPLIER START (1st API CALL)
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_START:
                print("DEBUG - Inside SUPPLIER_START block")
                with st.spinner("Starting supplier matching..."):
                    try:
                        print(f"DEBUG - About to call API: {N8N_BASE_URL}supplier-matching")
                        print(f"DEBUG - With request_id: {st.session_state.current_request_id}")
                        
                        res = requests.post(
                            f"{N8N_BASE_URL}supplier-matching",
                            json={"request_id": st.session_state.current_request_id},
                            timeout=300
                        )
                        print(f"DEBUG - API call completed, status code: {res.status_code}")
                        res.raise_for_status()
                        data = res.json()
                        print(f"DEBUG - Response data: {data}")

                        st.session_state.supplier_resume_url = data.get("resumeURL")
                        st.session_state.supplier_status_message = data.get("status", "Processing...")
                        
                        # Debug: Show the resume URL
                        print(f"DEBUG - First call response: {data}")
                        print(f"DEBUG - Resume URL stored: {st.session_state.supplier_resume_url}")

                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_SHOW_1

                    except Exception as e:
                        st.session_state.supplier_matching_error = str(e)
                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_ERROR
                        print(f"DEBUG - First call error: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # SHOW STATUS 1
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_SHOW_1:
                st.info(st.session_state.supplier_status_message)
                time.sleep(1)
                st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_CALL_2
                st.rerun()

            # ──────────────────────────────────────────────────
            # CALL 2
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_CALL_2:
                if st.session_state.supplier_status_message:
                    st.info(st.session_state.supplier_status_message)

                # Debug: Show what URL we're calling
                print(f"DEBUG - Call 2 - About to POST to: {st.session_state.supplier_resume_url}")

                with st.spinner("Continuing supplier matching..."):
                    try:
                        res = requests.post(st.session_state.supplier_resume_url, timeout=300)
                        print(f"DEBUG - Call 2 - Response status: {res.status_code}")
                        print(f"DEBUG - Call 2 - Response text: {res.text}")
                        res.raise_for_status()
                        data = res.json()
                        print(f"DEBUG - Call 2 - Parsed response: {data}")
                        print(f"DEBUG - Call 2 - Response type: {type(data)}")
                        
                        # Handle list response
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        st.session_state.supplier_resume_url = data.get("resumeURL")
                        st.session_state.supplier_status_message = data.get("status", "Processing...")
                        
                        print(f"DEBUG - Call 2 - Resume URL: {st.session_state.supplier_resume_url}")
                        print(f"DEBUG - Call 2 - Status message: {st.session_state.supplier_status_message}")
                        
                        if not st.session_state.supplier_resume_url:
                            raise ValueError(f"No resumeURL in Call 2 response. Data: {data}")

                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_SHOW_2

                    except Exception as e:
                        st.session_state.supplier_matching_error = str(e)
                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_ERROR
                        print(f"DEBUG - Call 2 - Error occurred: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # SHOW STATUS 2
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_SHOW_2:
                st.info(st.session_state.supplier_status_message)
                time.sleep(1)
                st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_CALL_3
                st.rerun()

            # ──────────────────────────────────────────────────
            # CALL 3
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_CALL_3:
                if st.session_state.supplier_status_message:
                    st.info(st.session_state.supplier_status_message)

                with st.spinner("Processing supplier data..."):
                    try:
                        res = requests.post(st.session_state.supplier_resume_url, timeout=300)
                        res.raise_for_status()
                        data = res.json()
                        print(f"DEBUG - Call 3 - Response type: {type(data)}")
                        
                        # Handle list response
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        st.session_state.supplier_resume_url = data.get("resumeURL")
                        st.session_state.supplier_status_message = data.get("status", "Processing...")
                        
                        print(f"DEBUG - Call 3 - Resume URL: {st.session_state.supplier_resume_url}")
                        print(f"DEBUG - Call 3 - Status message: {st.session_state.supplier_status_message}")
                        
                        if not st.session_state.supplier_resume_url:
                            raise ValueError(f"No resumeURL in Call 3 response. Data: {data}")

                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_SHOW_3

                    except Exception as e:
                        st.session_state.supplier_matching_error = str(e)
                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_ERROR

                st.rerun()

            # ──────────────────────────────────────────────────
            # SHOW STATUS 3
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_SHOW_3:
                st.info(st.session_state.supplier_status_message)
                time.sleep(1)
                st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_CALL_4
                st.rerun()

            # ──────────────────────────────────────────────────
            # CALL 4 (FINAL CALL)
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_CALL_4:
                print("DEBUG - Entered SUPPLIER_CALL_4 block")
                if st.session_state.supplier_status_message:
                    st.info(st.session_state.supplier_status_message)

                print(f"DEBUG - Call 4 - About to POST to: {st.session_state.supplier_resume_url}")
                
                with st.spinner("Finalizing supplier matches..."):
                    try:
                        res = requests.post(st.session_state.supplier_resume_url, timeout=300)
                        res.raise_for_status()
                        matches = res.json()
                        print(f"DEBUG - Call 4 - Response type: {type(matches)}")
                        print(f"DEBUG - Call 4 - Response data: {matches}")
                        
                        # Handle response format - this is the FINAL data
                        if not matches:
                            matches = []
                        elif isinstance(matches, dict) and "item_code" in matches:
                            matches = [matches]
                        elif isinstance(matches, list):
                            matches = matches
                        else:
                            matches = []

                        st.session_state.supplier_matches = matches
                        
                        # Update email status
                        email_index = st.session_state.selected_email_index
                        if email_index is not None:
                            st.session_state.email_status_map[email_index] = "Suppliers matched"

                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_DONE
                        st.session_state.show_supplier_completion_dialog = True

                    except Exception as e:
                        st.session_state.supplier_matching_error = str(e)
                        st.session_state.supplier_matching_state = ProcessingState.SUPPLIER_ERROR
                        print(f"DEBUG - Call 4 - Error occurred: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # DONE STATE
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_DONE:
                # Show dialog on first completion
                if st.session_state.get("show_supplier_completion_dialog", False):
                    show_supplier_matching_complete_dialog()

            # ──────────────────────────────────────────────────
            # ERROR STATE
            # ──────────────────────────────────────────────────
            if state == ProcessingState.SUPPLIER_ERROR:
                if st.session_state.supplier_status_message:
                    st.info(st.session_state.supplier_status_message)

                st.error(f"❌ Supplier matching failed: {st.session_state.supplier_matching_error}")
                if st.button("Reset", use_container_width=True, key="reset_supplier_error"):
                    st.session_state.supplier_matching_state = ProcessingState.IDLE
                    st.session_state.supplier_matching_error = None
                    st.session_state.supplier_status_message = None
                    st.rerun()

            # ──────────────────────────────────────────────────
            # DISPLAY SUPPLIER MATCHES
            # ──────────────────────────────────────────────────
            if st.session_state.supplier_matches:
                st.markdown("### Bill of Materials (BOM)")
                st.divider()
                
                for item in st.session_state.supplier_matches:
                    with st.expander(f"🔍 {item['item_code']} — {item['item_description']}", expanded=False):
                        render_supplier_selection_table(item, st.session_state.selected_email_index or 0)

                st.divider()
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    # Disable sending RFIs if RFIs were already sent for this processed request
                    rfi_state = st.session_state.rfi_sending_state
                    send_disabled = bool(st.session_state.get("rfi_sent") and processed_for_current) or rfi_state != ProcessingState.IDLE

                    if st.button("Send RFIs", key=f"submit_rfi_btn", use_container_width=True, type="primary", disabled=send_disabled):
                        st.session_state.active_item = None
                        
                        payload = []
                        suppliers_without_email = {}
                        suppliers_contacted_list = {}
                        
                        for item in st.session_state.supplier_matches:
                            suppliers = []
                            missing_email = []
                            
                            for s in item["suppliers"]:
                                key = f"{item['item_code']}::{s['supplier_id']}"
                                if st.session_state.selected_suppliers.get(key):
                                    if s.get("supplier_email"):
                                        suppliers.append(s)
                                    else:
                                        missing_email.append(s)

                            if suppliers:
                                payload.append({**item, "suppliers": suppliers})
                                suppliers_contacted_list[item['item_code']] = suppliers
                            
                            if missing_email:
                                suppliers_without_email[item['item_code']] = missing_email

                        if not payload:
                            st.error("No suppliers with email addresses selected")
                        else:
                            # Store payload and metadata for state machine
                            st.session_state.rfi_payload = payload
                            st.session_state.suppliers_without_email = suppliers_without_email
                            st.session_state.suppliers_contacted_list = suppliers_contacted_list
                            st.session_state.rfi_sending_state = ProcessingState.RFI_START
                            st.rerun()

                    if send_disabled and st.session_state.get("rfi_sent"):
                        if st.button("View RFI Summary", key="view_rfi_summary_btn", use_container_width=True, type="primary"):
                            st.session_state["tab_unlocked"][4] = True
                            st.session_state.current_tab = 4
                            st.rerun()

            # ================= RFI SENDING STATE MACHINE ================= #

            rfi_state = st.session_state.rfi_sending_state
            print(f"DEBUG - RFI State: {rfi_state}")

            # ──────────────────────────────────────────────────
            # RFI START (1st API CALL)
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_START:
                print("DEBUG - Inside RFI_START block")
                with st.spinner("Starting RFI distribution..."):
                    try:
                        print(f"DEBUG - About to call send-RFI API")
                        print(f"DEBUG - Payload: {st.session_state.rfi_payload}")
                        
                        res = requests.post(
                            f"{N8N_BASE_URL}send-RFI",
                            json=st.session_state.rfi_payload,
                            timeout=300
                        )
                        print(f"DEBUG - RFI Call 1 - Status code: {res.status_code}")
                        res.raise_for_status()
                        data = res.json()
                        print(f"DEBUG - RFI Call 1 - Response: {data}")

                        # Handle list response
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        st.session_state.rfi_resume_url = data.get("resumeURL")
                        st.session_state.rfi_status_message = data.get("status", "Processing...")
                        
                        print(f"DEBUG - RFI Call 1 - Resume URL: {st.session_state.rfi_resume_url}")

                        st.session_state.rfi_sending_state = ProcessingState.RFI_SHOW_1

                    except Exception as e:
                        st.session_state.rfi_sending_error = str(e)
                        st.session_state.rfi_sending_state = ProcessingState.RFI_ERROR
                        print(f"DEBUG - RFI Call 1 error: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # SHOW STATUS 1
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_SHOW_1:
                st.info(st.session_state.rfi_status_message)
                time.sleep(1)
                st.session_state.rfi_sending_state = ProcessingState.RFI_CALL_2
                st.rerun()

            # ──────────────────────────────────────────────────
            # CALL 2
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_CALL_2:
                if st.session_state.rfi_status_message:
                    st.info(st.session_state.rfi_status_message)

                print(f"DEBUG - RFI Call 2 - About to POST to: {st.session_state.rfi_resume_url}")

                with st.spinner("Processing RFI distribution..."):
                    try:
                        res = requests.post(st.session_state.rfi_resume_url, timeout=300)
                        print(f"DEBUG - RFI Call 2 - Status code: {res.status_code}")
                        res.raise_for_status()
                        data = res.json()
                        print(f"DEBUG - RFI Call 2 - Response: {data}")
                        
                        # Handle list response
                        if isinstance(data, list) and len(data) > 0:
                            data = data[0]

                        st.session_state.rfi_resume_url = data.get("resumeURL")
                        st.session_state.rfi_status_message = data.get("status", "Processing...")
                        
                        print(f"DEBUG - RFI Call 2 - Resume URL: {st.session_state.rfi_resume_url}")
                        
                        if not st.session_state.rfi_resume_url:
                            raise ValueError(f"No resumeURL in RFI Call 2 response. Data: {data}")

                        st.session_state.rfi_sending_state = ProcessingState.RFI_SHOW_2

                    except Exception as e:
                        st.session_state.rfi_sending_error = str(e)
                        st.session_state.rfi_sending_state = ProcessingState.RFI_ERROR
                        print(f"DEBUG - RFI Call 2 error: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # SHOW STATUS 2
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_SHOW_2:
                st.info(st.session_state.rfi_status_message)
                time.sleep(1)
                st.session_state.rfi_sending_state = ProcessingState.RFI_CALL_3
                st.rerun()

            # ──────────────────────────────────────────────────
            # CALL 3 (FINAL CALL)
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_CALL_3:
                print("DEBUG - Entered RFI_CALL_3 block")
                if st.session_state.rfi_status_message:
                    st.info(st.session_state.rfi_status_message)

                print(f"DEBUG - RFI Call 3 - About to POST to: {st.session_state.rfi_resume_url}")
                
                with st.spinner("Finalizing RFI distribution..."):
                    try:
                        res = requests.post(st.session_state.rfi_resume_url, timeout=300)
                        res.raise_for_status()
                        rfi_data = res.json()
                        print(f"DEBUG - RFI Call 3 - Response type: {type(rfi_data)}")
                        print(f"DEBUG - RFI Call 3 - Response data: {rfi_data}")
                        
                        # Handle response format
                        if isinstance(rfi_data, list) and len(rfi_data) > 0:
                            rfi_data = rfi_data[0]

                        st.session_state.rfi_result = rfi_data
                        st.session_state.rfi_sent = True
                        
                        # Update email status
                        email_index = st.session_state.selected_email_index
                        if email_index is not None:
                            st.session_state.email_status_map[email_index] = "RFIs sent"

                        st.session_state.rfi_sending_state = ProcessingState.RFI_DONE
                        st.session_state.show_rfi_completion_dialog = True

                    except Exception as e:
                        st.session_state.rfi_sending_error = str(e)
                        st.session_state.rfi_sending_state = ProcessingState.RFI_ERROR
                        print(f"DEBUG - RFI Call 3 error: {str(e)}")

                st.rerun()

            # ──────────────────────────────────────────────────
            # DONE STATE
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_DONE:
                # Show dialog on first completion
                if st.session_state.get("show_rfi_completion_dialog", False):
                    show_rfi_complete_dialog()

            # ──────────────────────────────────────────────────
            # ERROR STATE
            # ──────────────────────────────────────────────────
            if rfi_state == ProcessingState.RFI_ERROR:
                if st.session_state.rfi_status_message:
                    st.info(st.session_state.rfi_status_message)

                st.error(f"❌ RFI distribution failed: {st.session_state.rfi_sending_error}")
                if st.button("Reset", use_container_width=True, key="reset_rfi_error"):
                    st.session_state.rfi_sending_state = ProcessingState.IDLE
                    st.session_state.rfi_sending_error = None
                    st.session_state.rfi_status_message = None
                    st.rerun()
        else:
            st.info("Process an email with BOM Complete status to access supplier matching")

    # TAB 4: Follow-up
    # TAB 4: Follow-up
    elif st.session_state.current_tab == 3:

        st.markdown("### Follow-up Processing")
        st.divider()

        result = st.session_state.process_result

        if result and result.get("next_action") == "send-followup":

            st.warning("BOM Incomplete — Follow-up Required")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if not st.session_state.followup_preview:
                    if st.button(
                        "Prepare Follow-up",
                        type="primary",
                        use_container_width=True,
                        disabled=st.session_state.get("is_preparing_followup")
                    ):
                        st.session_state.is_preparing_followup = True
                        st.session_state.followup_prep_error = None
                        st.rerun()
                else:
                    st.success("Follow-up prepared successfully")


            # BLOCKING PREP FLOW (mirrors supplier matching) - Rendered below button
            if st.session_state.get("is_preparing_followup"):
                with st.spinner("Preparing follow-up email..."):
                    try:
                        res = requests.post(
                            f"{N8N_BASE_URL}preview-followup",
                            json={"request_id": st.session_state.current_request_id},
                            timeout=120
                        )
                        res.raise_for_status()
                        st.session_state.followup_preview = res.json()
                        st.session_state.followup_prep_success = True
                        st.session_state.followup_prep_error = None
                    except Exception as e:
                        st.session_state.followup_prep_error = str(e)
                    finally:
                        st.session_state.is_preparing_followup = False

                st.rerun()

            
            # Show error if preparation failed
            if st.session_state.get("followup_prep_error") and not st.session_state.get("is_preparing_followup"):
                st.divider()
                st.error(f"Error preparing follow-up: {st.session_state.followup_prep_error}")
                if st.button("Dismiss Error", key="dismiss_followup_error_btn"):
                    st.session_state.followup_prep_error = None
                    st.rerun()
            
            
            
            if st.session_state.followup_preview:
                preview = st.session_state.followup_preview
                
                if isinstance(preview, list):
                    preview_data = preview[0] if preview else {}
                else:
                    preview_data = preview
                
                with st.expander(f"View Follow-up Email", expanded=True):
                    st.markdown(f"**To:** {preview_data.get('email_to')}")
                    st.markdown(f"**Subject:** {preview_data.get('email_subject')}")
                    st.divider()
                    
                    st.components.v1.html(preview_data.get("email_body", ""), height=400, scrolling=True)
                    st.divider()
                    
                    if preview_data.get('drive_web_link'):
                        st.markdown("#### 📎 Attachments")
                        render_attachment_preview(
                            preview_data.get('drive_file_name', 'Attachment'),
                            preview_data.get('drive_web_link')
                        )
                        st.divider()
                
                if not st.session_state.followup_sent:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("Send Follow-up", key=f"send_followup_btn", use_container_width=True, type="primary"):
                            try:
                                with st.spinner("Sending follow-up email..."):
                                    res = requests.post(
                                        f"{N8N_BASE_URL}send-followup",
                                        json=st.session_state.followup_preview,
                                        timeout=120
                                    )
                                    res.raise_for_status()
                                    response_data = res.json()
                                
                                # Get recipient email
                                if isinstance(preview, list):
                                    recipient = preview[0].get('email_to', 'Unknown') if preview else 'Unknown'
                                else:
                                    recipient = preview.get('email_to', 'Unknown')
                                
                                success = False
                                if isinstance(response_data, list) and len(response_data) > 0:
                                    response_obj = response_data[0]
                                    if response_obj.get("followup_sent_at"):
                                        success = True
                                elif isinstance(response_data, dict):
                                    if response_data.get("success") or response_data.get("followup_sent_at"):
                                        success = True
                                
                                if success:
                                    st.session_state.followup_sent = True
                                    
                                    # Store recipient and show dialog
                                    st.session_state.followup_recipient_email = recipient
                                    st.session_state.show_followup_sent_dialog = True
                                    st.rerun()
                                else:
                                    st.error(f"Error: Failed to send follow-up")
                            except requests.RequestException as e:
                                st.error(f"Error sending follow-up: {str(e)}")
                else:
                    # Show dialog if flag is set
                    if st.session_state.get("show_followup_sent_dialog", False):
                        show_followup_sent_dialog(st.session_state.followup_recipient_email)
                    else:
                        st.success("Follow-up email sent successfully")
                        st.divider()
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            if st.button("Process Another Email", key=f"tab4_back_to_tab1", use_container_width=True, type="secondary"):
                                st.session_state.current_tab = 0
                                st.session_state.selected_email_index = None
                                st.session_state.process_result = None
                                st.session_state.followup_preview = None
                                st.session_state.followup_sent = False
                                st.session_state.current_request_id = None
                                st.rerun()
        else:
            st.info("Process an email with BOM Incomplete status to access follow-up processing")

    # TAB 5: RFI Summary
    elif st.session_state.current_tab == 4:
        st.markdown("### 📤 RFI Distribution Summary")
        st.divider()
        
        # Scroll to top when entering this tab
        st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
        
        if st.session_state.rfi_sent and st.session_state.rfi_result:
            render_rfi_inline(st.session_state.rfi_result)
            
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Done", key=f"tab5_done_btn", use_container_width=True, type="primary"):
                    # Update status to Complete
                    email_index = st.session_state.selected_email_index
                    if email_index is not None:
                        st.session_state.email_status_map[email_index] = "Complete"
                    
                    # Set flag to show completion dialog
                    st.session_state.show_request_complete_dialog = True
                    st.session_state.current_tab = 1
                    st.rerun()
        else:
            st.info("Send RFIs from Tab 3 to view the distribution summary")