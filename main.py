import streamlit as st
import requests

# ================= CONFIG =================

N8N_BASE_URL = "http://localhost:5678/webhook/"
PROCESS_EMAILS_URL = f"{N8N_BASE_URL}process-emails"

USERNAME = "manager"
PASSWORD = "manager123"

# ================= LOGIN =================

def login():
    st.markdown("<h1 style='text-align: center; color: #2c3e50;'>PROCUREMENT MANAGER</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #7f8c8d; font-size: 14px, text-align:center;'>Email Processing & Supplier Management</p>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Sign In")
        user = st.text_input("Username", label_visibility="collapsed", placeholder="Enter username")
        pwd = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Enter password")
        
        if st.button("Sign In", use_container_width=True):
            if user == USERNAME and pwd == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid username or password")

# ================= EMAIL VIEW =================

def render_email_details(email):
    st.markdown("### Email Details")
    st.markdown(f"**Subject:** {email.get('subject', 'N/A')}")
    st.markdown(f"**From:** {email.get('from', {}).get('text', 'N/A')}")
    
    # Format the date
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

# ================= FOLLOW-UP PREVIEW =================

@st.dialog("Follow-up Email Preview")
def show_followup_dialog(preview):
    # Handle if preview is a list, take the first item
    if isinstance(preview, list):
        preview = preview[0] if preview else {}
    
    # Check if BOM is complete
    
    st.divider()
    
    st.markdown(f"**To:** {preview.get('email_to')}")
    st.markdown(f"**Subject:** {preview.get('email_subject')}")

    st.divider()
    st.components.v1.html(preview.get("email_body", ""), height=600, scrolling=True)
    st.divider()
    # Display attachment if present
    if preview.get('drive_web_link'):
        st.subheader("📎 Attachments")
        st.markdown(
            f"[📄 {preview.get('drive_file_name', 'Attachment')}]({preview.get('drive_web_link')})"
        )
        st.divider()
    
    

# ================= SUPPLIER MATCHING =================

def trigger_supplier_matching(request_id):
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

# ================= SUPPLIER SELECTION TABLE =================

def render_supplier_selection_table(item, email_index):
    st.markdown(f"#### {item['item_code']} — {item['item_description']}")
    st.markdown(f"*Spec:* {item['item_specification']} | *Material:* {item['item_material']}")
    st.divider()

    selected = st.session_state.setdefault("selected_suppliers", {})
    
    # Create table data
    supplier_data = []
    for s in item.get("suppliers", []):
        key = f"{item['item_code']}::{s['supplier_id']}"
        
        # Get current selection status
        is_checked = selected.get(key, s.get("rank") == 1)
        
        supplier_data.append({
            "Select": is_checked,
            "Rank": f"#{s['rank']}",
            "Supplier": s['supplier_name'],
            "Email": s.get('supplier_email', 'N/A'),
            "City": s.get('supplier_city', 'N/A'),
            "Country": s.get('supplier_country', 'N/A'),
            "Confidence": s.get('confidence', 'N/A').upper(),
            "Score": s.get('match_score', 'N/A'),
            "Recommended": "⭐" if s.get('recommended') else ""
        })
    
    # Display table with checkboxes
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

# ================= INLINE RFI VIEW (NO DIALOG) =================

def render_rfi_inline(rfi):
    st.divider()
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
        height=900,
        scrolling=True
    )

    # ---------- SUPPLIERS WITHOUT EMAIL ----------
    if st.session_state.get("suppliers_without_email"):
        st.divider()
        with st.expander("⚠ Suppliers Not Contacted (Missing Email)", expanded=False):
            for item_code, supplier_list in st.session_state.suppliers_without_email.items():
                st.markdown(f"**Item:** {item_code}")
                
                # Create a formatted table for suppliers
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

# ================= DASHBOARD =================

def dashboard():
    st.markdown("<h1 style='color: #2c3e50; text-align:center;'>Email Processing Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #7f8c8d; margin-top: -10px; text-align:center;'>Manage emails, match suppliers, and send RFIs</p>", unsafe_allow_html=True)
    st.divider()

    # ---------- INIT STATE ----------
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
        "followup_preview": None,
        "followup_sent": False,
        "processed_email_index": None,
        "show_followup_preview": False,
    }.items():
        st.session_state.setdefault(k, v)

    # ---------- FETCH EMAILS ----------
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Fetch Unread Emails", use_container_width=True, type="primary"):
            res = requests.post(PROCESS_EMAILS_URL, timeout=120)
            res.raise_for_status()
            st.session_state.emails = res.json() if res.text.strip() else []
            
            if not st.session_state.emails:
                st.info("No new emails received")

    # ---------- EMAIL LIST ----------
    for i, email in enumerate(st.session_state.emails):
        # Format the email date
        date_str = email.get('date', 'N/A')
        formatted_date = 'N/A'
        if date_str != 'N/A':
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
            except:
                formatted_date = date_str
        
        # Create two columns for subject and date
        col1, col2 = st.columns([3, 1])
        with col1:
            expander_label = f"📧 {email.get('subject')}"
        with col2:
            expander_label += f"    {formatted_date}"
        
        with st.expander(expander_label):
            render_email_details(email)

            if st.button("Process Email", key=f"proc_{i}", use_container_width=True, type="primary"):
                res = requests.post(
                    f"{N8N_BASE_URL}process-single-email",
                    json=email,
                    timeout=300
                )
                res.raise_for_status()
                response_data = res.json()
                
                # Handle array response - take the first item
                if isinstance(response_data, list) and len(response_data) > 0:
                    response_data = response_data[0]
                
                st.session_state.process_result = response_data
                st.session_state.current_request_id = response_data.get("request_id")
                st.session_state.processed_email_index = i
                st.rerun()
            
            # ---------- PROCESS RESULT (Inside Email Expander) ----------
            # Only show results if this email was just processed
            if st.session_state.get("processed_email_index") == i:
                result = st.session_state.process_result
                if result:
                    st.divider()
                    
                    # Check if status is success and display message
                    if result.get("status") == "success":
                        message = result.get("message", "Processing successful")
                        st.success(f"{message}")
                    
                    if result.get("next_action") == "match_suppliers":
                        if st.button("Match Suppliers", key=f"match_{i}", use_container_width=True, type="primary"):
                            matches = trigger_supplier_matching(st.session_state.current_request_id)
                            st.session_state.supplier_matches = matches
                            st.session_state.selected_suppliers = {}
                            st.rerun()
                        
                        # ---------- BOM ITEMS & RFI SUBMISSION ----------
                        # Show BOM items after matching suppliers
                        if st.session_state.supplier_matches:
                            st.divider()
                            st.markdown("### Bill of Materials (BOM)")
                            
                            for item in st.session_state.supplier_matches:
                                with st.expander(f"🔍 {item['item_code']} — {item['item_description']}", expanded=False):
                                    render_supplier_selection_table(item, i)

                            # ---------- SUBMIT RFIs ----------
                            st.divider()
                            if st.button("Send RFIs", key=f"submit_rfi_{i}", use_container_width=True, type="primary"):
                                st.session_state.active_item = None  # 🔑 Close dialog immediately
                                
                                payload = []
                                suppliers_without_email = {}
                                
                                for item in st.session_state.supplier_matches:
                                    suppliers = []
                                    missing_email = []
                                    
                                    for s in item["suppliers"]:
                                        key = f"{item['item_code']}::{s['supplier_id']}"
                                        if st.session_state.selected_suppliers.get(key):
                                            # Check if supplier has email
                                            if s.get("supplier_email"):
                                                suppliers.append(s)
                                            else:
                                                # Store suppliers without email
                                                missing_email.append(s)

                                    if suppliers:
                                        payload.append({**item, "suppliers": suppliers})
                                    
                                    # Store missing email suppliers by item code
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
                                    st.session_state.suppliers_without_email = suppliers_without_email  # 🔑 Store missing suppliers
                                    st.rerun()

                            # ---------- VIEW RFIs ----------
                            if st.session_state.rfi_sent:
                                st.success("RFIs successfully sent")
                                if st.button("View RFIs", key=f"view_rfi_{i}", use_container_width=True, type="secondary"):
                                    st.session_state.active_item = None
                                    st.session_state.show_rfi = True
                                    st.rerun()

                                if st.session_state.show_rfi and st.session_state.rfi_result:
                                    render_rfi_inline(st.session_state.rfi_result)
                    
                    # Handle follow-up case
                    if result.get("next_action") == "send-followup":
                        st.warning("BOM Incomplete — Follow-up Required")
                        
                        if not st.session_state.followup_preview:
                            if st.button("Process Follow-up Email", key=f"followup_process_{i}", use_container_width=True, type="primary"):
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
                            # Show follow-up options
                            preview = st.session_state.followup_preview
                            
                            st.divider()
                            
                            # Display preview in an expander
                            if isinstance(preview, list):
                                preview_data = preview[0] if preview else {}
                            else:
                                preview_data = preview
                            
                            with st.expander(f"View Follow-up", expanded=st.session_state.get("show_followup_preview", False)):
                                st.markdown(f"**To:** {preview_data.get('email_to')}")
                                st.markdown(f"**Subject:** {preview_data.get('email_subject')}")
                                st.divider()
                                
                                
                                st.components.v1.html(preview_data.get("email_body", ""), height=400, scrolling=True)
                                st.divider()
                                # Display attachment if present
                                if preview_data.get('drive_web_link'):
                                    st.markdown("#### Attachments")
                                    st.markdown(
                                        f"[{preview_data.get('drive_file_name', 'Attachment')}]({preview_data.get('drive_web_link')})"
                                    )
                                    st.divider()
                                
                            # Send Follow-up button after expander
                            if not st.session_state.followup_sent:
                                if st.button("Send Follow-up", key=f"send_followup_{i}", use_container_width=True, type="primary"):
                                    try:
                                        res = requests.post(
                                            f"{N8N_BASE_URL}send-followup",
                                            json=st.session_state.followup_preview,
                                            timeout=120
                                        )
                                        res.raise_for_status()
                                        response_data = res.json()
                                        
                                        # Handle list response (array of objects)
                                        if isinstance(response_data, list) and len(response_data) > 0:
                                            response_obj = response_data[0]
                                            if response_obj.get("followup_sent_at"):
                                                st.session_state.followup_sent = True
                                                # Get recipient from preview
                                                if isinstance(preview, list):
                                                    preview = preview[0] if preview else {}
                                                recipient = preview.get('email_to', 'Unknown')
                                                st.success(f"Follow-up email sent successfully to {recipient}")
                                            else:
                                                st.error(f"Error: Failed to send follow-up")
                                        # Handle dict response
                                        elif isinstance(response_data, dict):
                                            if response_data.get("success") or response_data.get("followup_sent_at"):
                                                st.session_state.followup_sent = True
                                                # Get recipient from preview
                                                if isinstance(preview, list):
                                                    preview = preview[0] if preview else {}
                                                recipient = preview.get('email_to', 'Unknown')
                                                st.success(f"Follow-up email sent successfully to {recipient}")
                                            else:
                                                st.error(f"Error: {response_data.get('message', 'Failed to send follow-up')}")
                                        else:
                                            st.error("Error: Invalid response format")
                                    except requests.RequestException as e:
                                        st.error(f"Error sending follow-up: {str(e)}")
                            
                            # Show success message if already sent
                            # if st.session_state.followup_sent:
                            #     # st.success("Follow-up email sent successfully")
                            #     # st.button("Send Follow-up", key=f"send_followup_done_{i}", use_container_width=True, disabled=True)

    # ---------- LOGOUT ----------
    st.divider()
    if st.button("Logout", use_container_width=True, type="secondary"):
        st.session_state.clear()
        st.rerun()

# ================= ENTRY =================

st.set_page_config(page_title="Procurement Manager", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    dashboard()
