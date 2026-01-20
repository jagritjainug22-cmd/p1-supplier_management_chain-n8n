import streamlit as st
import requests
import time

# You'll need to pass config from main.py or define here
N8N_BASE_URL = "http://localhost:5678/webhook/"
SHEET_ID = "1U6ml01UyidEPDYVqs994oSHV0eLaPX89yCG-QflD9Vc"

# ================= ALL HELPER FUNCTIONS =================

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


def trigger_supplier_matching(request_id):
    """Trigger supplier matching workflow"""
    res = requests.post(
        f"{N8N_BASE_URL}supplier-matching",
        json={"request_id": request_id},
        timeout=240
    )
    res.raise_for_status()

    if not res.text.strip():
        return []

    data = res.json()

    if isinstance(data, dict) and "item_code" in data:
        return [data]

    if isinstance(data, list):
        return data

    return []


def render_supplier_selection_table(item, email_index):
    """Render supplier selection table with checkboxes"""
    st.markdown(f"#### {item['item_code']} — {item['item_description']}")
    st.markdown(f"*Spec:* {item['item_specification']} | *Material:* {item['item_material']}")
    st.divider()

    selected = st.session_state.setdefault("selected_suppliers", {})
    
    # Display table headers
    cols = st.columns([0.8, 0.5, 2, 2, 1.5, 1.5, 1.2, 0.8, 0.6])
    
    with cols[0]:
        st.write("**Select**")
    with cols[1]:
        st.write("**Rank**")
    with cols[2]:
        st.write("**Supplier**")
    with cols[3]:
        st.write("**Email**")
    with cols[4]:
        st.write("**City**")
    with cols[5]:
        st.write("**Country**")
    with cols[6]:
        st.write("**Confidence**")
    with cols[7]:
        st.write("**Score**")
    with cols[8]:
        st.write("**Rec**")
    
    st.divider()
    
    # Display each supplier row with checkbox
    for s in item.get("suppliers", []):
        key = f"{item['item_code']}::{s['supplier_id']}"
        is_checked = selected.get(key, s.get("rank") == 1)
        
        cols = st.columns([0.8, 0.5, 2, 2, 1.5, 1.5, 1.2, 0.8, 0.6])
        
        with cols[0]:
            selected[key] = st.checkbox("", value=is_checked, key=f"chk_{key}_{email_index}")
        with cols[1]:
            st.write(f"#{s['rank']}")
        with cols[2]:
            st.write(s['supplier_name'])
        with cols[3]:
            st.write(s.get('supplier_email', 'N/A'))
        with cols[4]:
            st.write(s.get('supplier_city', 'N/A'))
        with cols[5]:
            st.write(s.get('supplier_country', 'N/A'))
        with cols[6]:
            st.write(s.get('confidence', 'N/A').upper())
        with cols[7]:
            st.write(str(s.get('match_score', 'N/A')))
        with cols[8]:
            st.write("⭐" if s.get('recommended') else "")
    
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
    with st.expander("📊 RFI Distribution Summary", expanded=True):
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
        with st.expander("Suppliers Successfully Contacted", expanded=True):
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
        with st.expander("Suppliers Not Contacted (Missing Email)", expanded=True):
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

def dashboard():
    """Main email processing dashboard"""
    st.markdown("<h1 style='color: #2c3e50; text-align:center;'>Email Processing Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #7f8c8d; margin-top: -10px; text-align:center;'>Manage emails, match suppliers, and send RFIs</p>", unsafe_allow_html=True)
    st.divider()

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
        "email_status_map": {}
    }.items():
        st.session_state.setdefault(k, v)

    # Tab navigation
    tab_names = ["Fetch Emails", "Email Details", "Supplier Matching", "Follow-up", "RFI Summary"]
    cols = st.columns(5)
    
    for idx, (col, tab_name) in enumerate(zip(cols, tab_names)):
        with col:
            is_active = st.session_state.current_tab == idx
            if st.button(tab_name, use_container_width=True, key=f"tab_btn_{idx}", 
                        type="primary" if is_active else "secondary"):
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

                        request_id = email.get("request_id")
                        status_text = "Not processed"
                        if request_id:
                            status_text = fetch_status_from_sheet(request_id)
                        st.markdown(f"**Status:** `{status_text}`")

                    with col3:
                        if st.button("Open", key=f"open_email_{i}", use_container_width=True):
                            st.session_state.selected_email_index = i
                            st.session_state.current_tab = 1
                            st.rerun()

    # TAB 2: Email Details
    elif st.session_state.current_tab == 1:
        st.markdown("### 📄 Email Details")
        st.divider()
        
        if st.session_state.selected_email_index is not None and st.session_state.selected_email_index < len(st.session_state.emails):
            i = st.session_state.selected_email_index
            email = st.session_state.emails[i]
            
            render_email_details(email)
            
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                process_clicked = st.button("Process Email", key=f"proc_btn_{i}", use_container_width=True, type="primary")
                status_placeholder = st.empty()

                if process_clicked:
                    import threading

                    polling_status = {"text": "Polling Google Sheet..."}
                    polling_active = {"running": True}

                    def poll_google_sheet():
                        for _ in range(75):
                            if not polling_active["running"]:
                                break
                            fetched_status = f"Sheet status at {time.strftime('%X')}"
                            polling_status["text"] = fetched_status
                            status_placeholder.info(fetched_status)
                            time.sleep(4)

                    poll_thread = threading.Thread(target=poll_google_sheet)
                    poll_thread.start()

                    res = requests.post(
                        f"{N8N_BASE_URL}process-single-email",
                        json=email,
                        timeout=300
                    )
                    res.raise_for_status()
                    response_data = res.json()

                    polling_active["running"] = False
                    poll_thread.join()

                    if isinstance(response_data, list) and len(response_data) > 0:
                        response_data = response_data[0]

                    st.session_state.process_result = response_data
                    st.session_state.current_request_id = response_data.get("request_id")
                    st.session_state.processed_email_index = i
                    
                    request_id = response_data.get("request_id")
                    if request_id is not None:
                        latest_status = fetch_status_from_sheet(request_id)
                        st.session_state.email_status_map[i] = latest_status

                    if response_data.get("status") == "success":
                        message = response_data.get("message", "Processing successful")
                        st.success(f"{message}")
                        if response_data.get("next_action") == "match_suppliers":
                            st.info("BOM Complete — Switching to Supplier Matching...")
                        elif response_data.get("next_action") == "send-followup":
                            st.warning("BOM Incomplete — Switching to Follow-up...")

                    time.sleep(2)

                    if response_data.get("next_action") == "match_suppliers":
                        st.session_state.current_tab = 2
                    elif response_data.get("next_action") == "send-followup":
                        st.session_state.current_tab = 3

                    st.rerun()
            
            result = st.session_state.process_result
            if result and st.session_state.get("processed_email_index") == i:
                st.divider()
                if result.get("status") == "success":
                    message = result.get("message", "Processing successful")
                    st.success(f"{message}")
                    
                    if result.get("next_action") == "match_suppliers":
                        st.info("🔄Switching to Supplier Matching tab...")
                    elif result.get("next_action") == "send-followup":
                        st.warning("BOM Incomplete — Follow-up Required")
                        st.info("🔄 Switching to Follow-up tab...")
        else:
            st.info("Select an email from Tab 1 to view details")

    # TAB 3: Supplier Matching
    elif st.session_state.current_tab == 2:
        st.markdown("### Supplier Matching & RFI")
        st.divider()
        
        result = st.session_state.process_result
        
        if result and result.get("next_action") == "match_suppliers":
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Match Suppliers", key=f"match_btn", use_container_width=True, type="primary"):
                    matches = trigger_supplier_matching(st.session_state.current_request_id)
                    st.session_state.supplier_matches = matches
                    st.session_state.selected_suppliers = {}
                    st.rerun()
            
            st.divider()
            
            if st.session_state.supplier_matches:
                st.markdown("### Bill of Materials (BOM)")
                st.divider()
                
                for item in st.session_state.supplier_matches:
                    with st.expander(f"🔍 {item['item_code']} — {item['item_description']}", expanded=False):
                        render_supplier_selection_table(item, st.session_state.selected_email_index or 0)

                st.divider()
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("Send RFIs", key=f"submit_rfi_btn", use_container_width=True, type="primary"):
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
                            res = requests.post(
                                f"{N8N_BASE_URL}send-RFI",
                                json=payload,
                                timeout=180
                            )
                            res.raise_for_status()

                            data = res.json()
                            st.session_state.rfi_result = data[0]
                            st.session_state.rfi_sent = True
                            latest_status = fetch_status_from_sheet(st.session_state.current_request_id)
                            st.session_state.email_status_map[st.session_state.selected_email_index] = latest_status

                            st.session_state.suppliers_without_email = suppliers_without_email
                            st.session_state.suppliers_contacted_list = suppliers_contacted_list
                            st.session_state.current_tab = 4
                            st.rerun()
        else:
            st.info("Process an email with BOM Complete status to access supplier matching")

    # TAB 4: Follow-up
    elif st.session_state.current_tab == 3:
        st.markdown("### Follow-up Processing")
        st.divider()
        
        result = st.session_state.process_result
        
        if result and result.get("next_action") == "send-followup":
            st.warning("BOM Incomplete — Follow-up Required")
            st.divider()
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if not st.session_state.followup_preview:
                    if st.button("Prepare Follow-up", key=f"followup_prep_btn", use_container_width=True, type="primary"):
                        try:
                            res = requests.post(
                                f"{N8N_BASE_URL}preview-followup",
                                json={"request_id": st.session_state.current_request_id},
                                timeout=120
                            )
                            res.raise_for_status()
                            st.session_state.followup_preview = res.json()
                            st.rerun()
                        except requests.RequestException as e:
                            st.error(f"Error generating follow-up: {str(e)}")
                else:
                    st.success("Follow-up prepared successfully")
            
            st.divider()
            
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
                                res = requests.post(
                                    f"{N8N_BASE_URL}send-followup",
                                    json=st.session_state.followup_preview,
                                    timeout=120
                                )
                                res.raise_for_status()
                                response_data = res.json()
                                
                                if isinstance(response_data, list) and len(response_data) > 0:
                                    response_obj = response_data[0]
                                    if response_obj.get("followup_sent_at"):
                                        st.session_state.followup_sent = True
                                        latest_status = fetch_status_from_sheet(st.session_state.current_request_id)
                                        st.session_state.email_status_map[st.session_state.selected_email_index] = latest_status
                                        
                                        if isinstance(preview, list):
                                            preview = preview[0] if preview else {}
                                        recipient = preview.get('email_to', 'Unknown')
                                        st.success(f"Follow-up email sent successfully to {recipient}")
                                    else:
                                        st.error(f"Error: Failed to send follow-up")
                                elif isinstance(response_data, dict):
                                    if response_data.get("success") or response_data.get("followup_sent_at"):
                                        st.session_state.followup_sent = True
                                        if isinstance(preview, list):
                                            preview = preview[0] if preview else {}
                                        recipient = preview.get('email_to', 'Unknown')
                                        st.success(f"Follow-up email sent successfully to {recipient}")
                                    else:
                                        st.error(f"Error: {response_data.get('message', 'Failed to send follow-up')}")
                                else:
                                    st.error("Error: Invalid response format")
                                st.rerun()
                            except requests.RequestException as e:
                                st.error(f"Error sending follow-up: {str(e)}")
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
        
        if st.session_state.rfi_sent and st.session_state.rfi_result:
            render_rfi_inline(st.session_state.rfi_result)
            
            st.divider()
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Process Another Email", key=f"tab5_back_to_tab1", use_container_width=True, type="secondary"):
                    st.session_state.current_tab = 0
                    st.session_state.selected_email_index = None
                    st.session_state.process_result = None
                    st.session_state.rfi_sent = False
                    st.session_state.rfi_result = None
                    st.session_state.suppliers_without_email = {}
                    st.session_state.suppliers_contacted_list = {}
                    st.session_state.supplier_matches = []
                    st.session_state.selected_suppliers = {}
                    st.session_state.current_request_id = None
                    st.rerun()
        else:
            st.info("Send RFIs from Tab 3 to view the distribution summary")