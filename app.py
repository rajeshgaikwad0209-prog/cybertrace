"""
CyberTrace — Digital Footprint & Privacy Risk Analyzer
==========================================================
Main Streamlit application entrypoint.

Run locally with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="CyberTrace — Privacy Risk Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.ui.styles import inject_css
from app.core.auth import is_authenticated, current_username

# Ensure DB tables exist (idempotent) as early as possible.
from app.db.connection import get_engine
get_engine()

from app.pages import (
    home, assessment, results, exposure_map, recommendations_page,
    history, compare, profile_audit_page, download_report, about, account
)

inject_css()

NAV_ITEMS = [
    ("🏠 Home", "Home"),
    ("📝 Start Assessment", "Start Assessment"),
    ("📊 Assessment Results", "Assessment Results"),
    ("🗺️ Digital Exposure Map", "Digital Exposure Map"),
    ("💡 Privacy Recommendations", "Privacy Recommendations"),
    ("📈 Assessment History", "Assessment History"),
    ("⚖️ Compare Assessments", "Compare Assessments"),
    ("🔎 Profile Privacy Audit", "Profile Privacy Audit"),
    ("📄 Download Report", "Download Report"),
    ("ℹ️ About & Limitations", "About & Limitations"),
]

PAGES_REQUIRING_LOGIN = {
    "Start Assessment", "Assessment Results", "Digital Exposure Map",
    "Privacy Recommendations", "Assessment History", "Compare Assessments",
    "Profile Privacy Audit", "Download Report",
}

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 1rem 0;">
        <div style="font-size:1.6rem; font-weight:800; color:#E8EEF3;">
            Cyber<span style="color:#2FD3E8;">Trace</span>
        </div>
        <div style="color:#9FB3C4; font-size:0.78rem;">Privacy Risk Analyzer</div>
    </div>
    """, unsafe_allow_html=True)

    if is_authenticated():
        st.markdown(f"**👤 {current_username()}**")
    else:
        st.caption("Not logged in")

    st.markdown("---")

    nav_labels = [label for label, _ in NAV_ITEMS]
    nav_values = [value for _, value in NAV_ITEMS]

    default_target = st.session_state.pop("nav_target", "Home")
    default_index = nav_values.index(default_target) if default_target in nav_values else 0

    selected_label = st.radio("Navigation", nav_labels, index=default_index, label_visibility="collapsed")
    selected_page = nav_values[nav_labels.index(selected_label)]

    st.markdown("---")

    if is_authenticated():
        account_label = "🔐 Account"
    else:
        account_label = "🔐 Log In / Sign Up"
    if st.button(account_label, use_container_width=True):
        selected_page = "Account"

    st.markdown("---")
    st.caption("CyberTrace v1.0 — Educational privacy assessment tool.")

# Route to the selected page
if selected_page == "Account":
    account.render()
elif selected_page in PAGES_REQUIRING_LOGIN and not is_authenticated():
    st.warning("Please log in or create an account to access this feature.")
    account.render()
elif selected_page == "Home":
    home.render()
elif selected_page == "Start Assessment":
    assessment.render()
elif selected_page == "Assessment Results":
    results.render()
elif selected_page == "Digital Exposure Map":
    exposure_map.render()
elif selected_page == "Privacy Recommendations":
    recommendations_page.render()
elif selected_page == "Assessment History":
    history.render()
elif selected_page == "Compare Assessments":
    compare.render()
elif selected_page == "Profile Privacy Audit":
    profile_audit_page.render()
elif selected_page == "Download Report":
    download_report.render()
elif selected_page == "About & Limitations":
    about.render()
