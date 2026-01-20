import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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


# ================= ANALYSE DASHBOARD =================

def analyse_dashboard():
    st.markdown("## 📈 Analyse Requests")
    st.caption("View all procurement requests and optionally filter by status")

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

    # ---------- FILTERS ----------
    st.markdown("### 🔍 Filters")

    col1, col2 = st.columns([1, 3])

    with col1:
        status_options = ["All"] + sorted(
            full_df["status"].dropna().astype(str).unique().tolist()
        )
        selected_status = st.selectbox(
            "Request Status",
            status_options,
            index=0   # 👈 Always default to "All"
        )

    # ---------- APPLY FILTER (VIEW ONLY) ----------
    if selected_status == "All":
        view_df = full_df.copy()
    else:
        view_df = full_df[full_df["status"] == selected_status]

    # ---------- METRICS ----------
    c1, c2, c3 = st.columns(3)

    c1.metric("Total Requests", len(view_df))
    c2.metric(
        "Unique Suppliers",
        view_df["supplier"].nunique() if "supplier" in view_df.columns else "—"
    )
    c3.metric("Statuses Visible", view_df["status"].nunique())

    st.divider()

    # ---------- TABLE ----------
    st.markdown("### 📋 Requests Overview")

    styled_df = (
        view_df
        .style
        .set_properties(**{
            "background-color": "#ffffff",
            "border-color": "#e0e0e0",
            "font-size": "13px"
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#f5f7fa"),
                    ("color", "#2c3e50"),
                    ("font-weight", "600"),
                    ("border", "1px solid #e0e0e0")
                ]
            }
        ])
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=520
    )
