"""CyberTrace Assessment Results page."""

import streamlit as st
from app.core.auth import require_login, current_user_id
from app.core.scoring import compute_scores
from app.db.connection import session_scope
from app.db.repository import (
    get_user_assessments, get_assessment_for_user, get_assessment_answers
)
from app.ui.components import render_score_display, render_category_cards, limitations_notice, footer
from app.ui.charts import category_bar_chart
import plotly.graph_objects as go


def render():
    require_login()
    st.markdown("## 📊 Assessment Results")

    user_id = current_user_id()
    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)
        if not assessments:
            st.info("You haven't completed an assessment yet.")
            if st.button("Start Assessment →", type="primary"):
                st.session_state["nav_target"] = "Start Assessment"
                st.rerun()
            footer()
            return

        # Default to most recent, or the one just submitted
        target_id = st.session_state.get("last_assessment_id", assessments[0].id)
        options = {f"{a.created_at.strftime('%Y-%m-%d %H:%M UTC')} — Score: {a.overall_score if a.overall_score is not None else 'N/A'}": a.id
                   for a in assessments}
        default_label = next((k for k, v in options.items() if v == target_id), list(options.keys())[0])

        selected_label = st.selectbox("Select assessment:", list(options.keys()),
                                        index=list(options.keys()).index(default_label))
        selected_id = options[selected_label]

        assessment = get_assessment_for_user(session, user_id, selected_id)
        if assessment is None:
            st.error("That assessment could not be found.")
            return

        answers = get_assessment_answers(session, assessment)
        result = compute_scores(answers)

    render_score_display(result)

    st.markdown("### Category Breakdown")
    render_category_cards(result)

    st.markdown("### Visual Summary")
    st.plotly_chart(category_bar_chart(result), use_container_width=True)

    st.markdown("### How This Score Was Calculated")
    with st.expander("Scoring methodology"):
        st.markdown("""
        Each applicable question contributes a **risk value** between 0 and 1, scaled by
        the question's **weight**. Scores are summed and divided by the total applicable
        weight, then multiplied by 100:

        ```
        Risk Score = 100 × Σ(risk_value × weight) / Σ(applicable weights)
        ```

        Questions marked **"Not applicable"** are excluded entirely — they neither help
        nor hurt your score. Protective-practice questions (like using MFA) are scored in
        reverse: doing the protective thing lowers your risk value.
        """)

    st.markdown("### Main Contributing Factors")
    all_factors = []
    for cat_key, cs in result.category_scores.items():
        all_factors.extend(cs.contributing_factors)
    if all_factors:
        from app.core.questions import get_question
        for fid in all_factors[:10]:
            q = get_question(fid)
            if q:
                st.markdown(f"- **{q.id}** ({q.category}): {q.text}")
    else:
        st.markdown("No significant concerns were identified in this assessment. 🎉")

    st.markdown("---")
    limitations_notice()
    footer()
