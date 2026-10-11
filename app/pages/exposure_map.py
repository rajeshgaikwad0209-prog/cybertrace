"""CyberTrace Digital Exposure Map page."""

import streamlit as st
from app.core.auth import require_login, current_user_id
from app.core.scoring import compute_scores
from app.core.questions import CATEGORY_ORDER, CATEGORIES, CATEGORY_DESCRIPTIONS, get_question
from app.db.connection import session_scope
from app.db.repository import get_latest_assessment, get_assessment_answers
from app.ui.charts import exposure_radar_chart, risk_level_summary_chart
from app.ui.styles import risk_badge_html
from app.ui.components import footer
import pandas as pd


def render():
    require_login()
    st.markdown("## 🗺️ Digital Exposure Map")
    st.markdown("A visual map of your privacy risk across all six assessment categories.")

    user_id = current_user_id()
    with session_scope() as session:
        assessment = get_latest_assessment(session, user_id)
        if assessment is None:
            st.info("Complete an assessment first to see your exposure map.")
            if st.button("Start Assessment →", type="primary"):
                st.session_state["nav_target"] = "Start Assessment"
                st.rerun()
            footer()
            return
        answers = get_assessment_answers(session, assessment)

    result = compute_scores(answers)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.plotly_chart(exposure_radar_chart(result), use_container_width=True)
    with col2:
        st.plotly_chart(risk_level_summary_chart(result), use_container_width=True)

    st.markdown("### Category Details")
    st.caption("Select a category to see its detailed results.")

    selected = st.selectbox("Category:", [CATEGORIES[c] for c in CATEGORY_ORDER])
    selected_key = [c for c in CATEGORY_ORDER if CATEGORIES[c] == selected][0]
    cs = result.category_scores.get(selected_key)

    if cs is None or cs.score is None:
        st.warning(f"No applicable answers recorded for **{selected}** in this assessment.")
    else:
        colA, colB, colC, colD = st.columns(4)
        colA.metric("Score", f"{cs.score:.1f}")
        colB.markdown(f"**Risk Level**<br>{risk_badge_html(cs.risk_level)}", unsafe_allow_html=True)
        colC.metric("Applicable Questions", cs.applicable_count)
        colD.metric("Concerns", cs.concern_count)

        st.caption(CATEGORY_DESCRIPTIONS[selected_key])

        if cs.contributing_factors:
            st.markdown("**Main contributing concerns:**")
            for fid in cs.contributing_factors:
                q = get_question(fid)
                if q:
                    st.markdown(f"- {q.text}")
                    st.caption(f"  Suggested action: {q.recommended_action}")
        else:
            st.markdown("No concerns reported in this category. ✅")

    # Accessible table alternative to the chart
    st.markdown("### Accessible Summary Table")
    rows = []
    for cat_key in CATEGORY_ORDER:
        c = result.category_scores.get(cat_key)
        rows.append({
            "Category": CATEGORIES[cat_key],
            "Score": c.score if c and c.score is not None else "N/A",
            "Risk Level": c.risk_level if c and c.risk_level else "N/A",
            "Applicable Qs": c.applicable_count if c else 0,
            "Concerns": c.concern_count if c else 0,
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    footer()
