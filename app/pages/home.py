"""CyberTrace Home / Landing page."""

import streamlit as st
from app.ui.components import render_feature_card, privacy_notice, limitations_notice, footer


def render():
    st.markdown("""
    <div class="ct-hero">
        <div class="ct-hero-badge">PRIVACY ASSESSMENT PLATFORM</div>
        <div class="ct-logo-text">Cyber<span>Trace</span></div>
        <div class="ct-tagline">Understand Your Digital Footprint. Take Control of Your Privacy.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <h2 style="text-align:center;">Your Digital Footprint, Made Visible.</h2>
        <p style="text-align:center; color:#9FB3C4; font-size:1.05rem;">
        CyberTrace helps you understand the privacy risks associated with information
        you choose to share, identify unnecessary exposure, and build a practical plan
        to improve your digital privacy.
        </p>
        """, unsafe_allow_html=True)

        if st.button("Start Assessment →", type="primary", use_container_width=True):
            st.session_state["nav_target"] = "Start Assessment"
            st.rerun()

    st.markdown('<div class="ct-notice" style="text-align:center;">'
                'CyberTrace evaluates information supplied by the user. It does not claim to '
                'discover every public record, exposed account, or data breach.</div>',
                unsafe_allow_html=True)

    st.markdown("### What CyberTrace Does")
    cols = st.columns(3)
    with cols[0]:
        render_feature_card("🧭", "Guided Assessment", "A structured questionnaire covering six key digital privacy categories.")
    with cols[1]:
        render_feature_card("📊", "Risk Scoring", "A transparent, weighted scoring engine — no black-box AI guesswork.")
    with cols[2]:
        render_feature_card("🗺️", "Exposure Map", "Visualize risk across categories with interactive charts.")

    cols2 = st.columns(3)
    with cols2[0]:
        render_feature_card("💡", "Recommendations", "Personalized, actionable steps tied directly to your answers.")
    with cols2[1]:
        render_feature_card("📈", "Track Progress", "Save assessments over time and compare how your exposure changes.")
    with cols2[2]:
        render_feature_card("📄", "PDF Reports", "Download a professional report summarizing your results.")

    st.markdown("---")
    st.markdown("### The Six Exposure Categories")
    categories_preview = [
        ("🪪", "Identity Exposure", "How visible your core identifying details are."),
        ("🔗", "Account Exposure", "Whether your accounts can be linked together."),
        ("📱", "Social Media Exposure", "What your activity reveals about your routines."),
        ("✉️", "Contact Information", "How exposed your personal contact details are."),
        ("🌐", "Public Information", "Details that may appear in public-facing pages."),
        ("🛡️", "Security Practices", "The protective habits that reduce your risk."),
    ]
    cols3 = st.columns(3)
    for i, (icon, title, desc) in enumerate(categories_preview):
        with cols3[i % 3]:
            render_feature_card(icon, title, desc)

    st.markdown("---")
    st.markdown("### How the Assessment Works")
    steps = st.columns(4)
    step_text = [
        ("1", "Answer Questions", "Work through ~24 questions across 6 categories at your own pace."),
        ("2", "Get Your Score", "A transparent, weighted formula calculates your risk score."),
        ("3", "Review Insights", "See your exposure map and category-by-category breakdown."),
        ("4", "Take Action", "Follow personalized recommendations and track your progress."),
    ]
    for i, (num, title, desc) in enumerate(step_text):
        with steps[i]:
            st.markdown(f"""
            <div class="ct-card" style="text-align:center;">
                <div style="font-size:1.6rem; color:#2FD3E8; font-weight:800;">{num}</div>
                <h4>{title}</h4>
                <p style="color:#9FB3C4; font-size:0.85rem;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    privacy_notice()
    limitations_notice()
    footer()
