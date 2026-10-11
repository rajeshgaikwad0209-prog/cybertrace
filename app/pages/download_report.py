"""CyberTrace Download Report page."""

import streamlit as st
from app.core.auth import require_login, current_user_id, current_username
from app.core.scoring import compute_scores
from app.core.recommendations import generate_recommendations
from app.core.pdf_report import generate_pdf_report
from app.db.connection import session_scope
from app.db.repository import get_user_assessments, get_assessment_answers
from app.ui.components import footer


def render():
    require_login()
    st.markdown("## 📄 Download Report")
    st.markdown("Generate a professional PDF summary of any completed assessment.")

    user_id = current_user_id()
    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)

    if not assessments:
        st.info("Complete an assessment first to generate a report.")
        if st.button("Start Assessment →", type="primary"):
            st.session_state["nav_target"] = "Start Assessment"
            st.rerun()
        footer()
        return

    options = {f"{a.created_at.strftime('%Y-%m-%d %H:%M UTC')} — Score: {a.overall_score}": a.id
               for a in assessments}
    selected_label = st.selectbox("Select assessment to export:", list(options.keys()))
    selected_id = options[selected_label]

    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)
        assessment = next(a for a in assessments if a.id == selected_id)
        answers = get_assessment_answers(session, assessment)
        assessment_date = assessment.created_at

    result = compute_scores(answers)
    recs = generate_recommendations(answers)

    st.markdown("### Report Preview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Overall Score", f"{result.overall_score:.1f}" if result.overall_score is not None else "N/A")
    col2.metric("Risk Level", result.overall_risk_level or "N/A")
    col3.metric("Recommendations", len(recs))

    st.markdown(
        "This report includes your scores, category breakdown, personalized "
        "recommendations, scoring methodology, and limitations. It does **not** "
        "include passwords, credentials, or raw session data."
    )

    if st.button("Generate PDF Report", type="primary"):
        with st.spinner("Generating report..."):
            pdf_bytes = generate_pdf_report(
                username=current_username(),
                assessment_date=assessment_date,
                result=result,
                recommendations=recs,
            )
        st.session_state["generated_pdf"] = pdf_bytes
        st.success("Report generated.")

    if "generated_pdf" in st.session_state:
        st.download_button(
            label="⬇ Download PDF",
            data=st.session_state["generated_pdf"],
            file_name=f"cybertrace_report_{assessment_date.strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            type="primary",
        )

    st.markdown("---")
    footer()
