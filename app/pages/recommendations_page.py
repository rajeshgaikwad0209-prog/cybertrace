"""CyberTrace Privacy Recommendations page."""

import streamlit as st
from app.core.auth import require_login, current_user_id
from app.core.recommendations import generate_recommendations, recommendation_summary
from app.db.connection import session_scope
from app.db.repository import (
    get_latest_assessment, get_assessment_answers,
    get_recommendation_completions, set_recommendation_completion
)
from app.ui.components import render_recommendation_card, footer


def render():
    require_login()
    st.markdown("## 💡 Privacy Recommendations")
    st.markdown(
        "Personalized, actionable recommendations generated directly from your most "
        "recent assessment answers."
    )

    user_id = current_user_id()
    with session_scope() as session:
        assessment = get_latest_assessment(session, user_id)
        if assessment is None:
            st.info("Complete an assessment first to receive personalized recommendations.")
            if st.button("Start Assessment →", type="primary"):
                st.session_state["nav_target"] = "Start Assessment"
                st.rerun()
            footer()
            return
        answers = get_assessment_answers(session, assessment)
        completions = get_recommendation_completions(session, user_id, assessment.id)
        assessment_id = assessment.id

    recs = generate_recommendations(answers)

    if not recs:
        st.success("No specific concerns were flagged based on your last assessment. Keep up the good habits!")
        footer()
        return

    summary = recommendation_summary(recs)
    cols = st.columns(4)
    priority_order = ["Critical", "High", "Medium", "Low"]
    colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    for i, p in enumerate(priority_order):
        cols[i].metric(f"{colors[p]} {p}", summary.get(p, 0))

    st.markdown("---")

    filter_priority = st.multiselect(
        "Filter by priority:", priority_order, default=priority_order
    )
    show_completed = st.checkbox("Show completed recommendations", value=True)

    for rec in recs:
        if rec.priority not in filter_priority:
            continue
        completed = completions.get(rec.rec_id, False)
        if completed and not show_completed:
            continue

        toggle_key = f"complete_{rec.rec_id}"
        render_recommendation_card(rec, completed, toggle_key)

        new_value = st.session_state.get(toggle_key, completed)
        if new_value != completed:
            with session_scope() as session:
                set_recommendation_completion(session, user_id, assessment_id, rec.rec_id, new_value)
            st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="ct-notice">Completing a recommendation updates your progress tracking '
        'only. It does not retroactively change this assessment\'s score — complete a new '
        'assessment to see an updated score.</div>',
        unsafe_allow_html=True
    )
    footer()
