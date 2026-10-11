"""CyberTrace Assessment History page."""

import streamlit as st
import pandas as pd
from app.core.auth import require_login, current_user_id
from app.core.scoring import compute_scores
from app.core.recommendations import generate_recommendations
from app.db.connection import session_scope
from app.db.repository import get_user_assessments, get_assessment_answers, delete_assessment
from app.ui.charts import history_trend_chart
from app.ui.styles import risk_badge_html
from app.ui.components import footer


def render():
    require_login()
    st.markdown("## 📈 Assessment History")

    user_id = current_user_id()
    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)
        if not assessments:
            st.info("You haven't completed any assessments yet.")
            if st.button("Start Assessment →", type="primary"):
                st.session_state["nav_target"] = "Start Assessment"
                st.rerun()
            footer()
            return

        rows = []
        dates, scores = [], []
        for a in reversed(assessments):  # chronological for the chart
            if a.overall_score is not None:
                dates.append(a.created_at)
                scores.append(a.overall_score)

        for a in assessments:  # most recent first for the table
            rows.append({
                "id": a.id,
                "Date": a.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                "Score": a.overall_score if a.overall_score is not None else "N/A",
                "Risk Level": a.overall_risk_level or "N/A",
                "Concerns": a.total_concerns,
                "Applicable Qs": a.total_applicable,
            })

    if len(scores) >= 2:
        st.plotly_chart(history_trend_chart(dates, scores), use_container_width=True)
        st.caption(
            "A lower score indicates fewer reported risks under the current assessment "
            "rules. It does not guarantee safety."
        )
    elif len(scores) == 1:
        st.info("Complete another assessment to see your trend over time.")
    else:
        st.info("No scored assessments yet.")

    st.markdown("### All Assessments")
    df = pd.DataFrame(rows).drop(columns=["id"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Assessment Details")
    selected_idx = st.selectbox(
        "View details for:",
        range(len(rows)),
        format_func=lambda i: f"{rows[i]['Date']} — Score: {rows[i]['Score']}"
    )
    selected_id = rows[selected_idx]["id"]

    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)
        assessment = next((a for a in assessments if a.id == selected_id), None)
        if assessment:
            answers = get_assessment_answers(session, assessment)

    if assessment:
        result = compute_scores(answers)
        recs = generate_recommendations(answers)

        col1, col2, col3 = st.columns(3)
        col1.metric("Overall Score", f"{result.overall_score:.1f}" if result.overall_score is not None else "N/A")
        with col2:
            st.markdown("**Risk Level**")
            if result.overall_risk_level:
                st.markdown(risk_badge_html(result.overall_risk_level), unsafe_allow_html=True)
        col3.metric("Recommendations Generated", len(recs))

        with st.expander("Delete this assessment"):
            st.warning("This action is permanent and cannot be undone.")
            if st.button(f"Permanently delete assessment #{selected_id}", type="secondary"):
                with session_scope() as session:
                    delete_assessment(session, user_id, selected_id)
                st.success("Assessment deleted.")
                st.rerun()

    st.markdown("---")
    footer()
