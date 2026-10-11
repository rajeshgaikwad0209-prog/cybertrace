"""CyberTrace Compare Assessments page."""

import streamlit as st
from app.core.auth import require_login, current_user_id
from app.core.scoring import compute_scores
from app.core.questions import CATEGORY_ORDER, CATEGORIES, get_question
from app.db.connection import session_scope
from app.db.repository import get_user_assessments, get_assessment_answers
from app.ui.charts import comparison_bar_chart
from app.ui.styles import risk_badge_html
from app.ui.components import footer


def render():
    require_login()
    st.markdown("## ⚖️ Compare Assessments")
    st.markdown(
        "Compare two of your saved assessments to see how your reported exposure has changed. "
        "Historical assessments are never modified by this comparison."
    )

    user_id = current_user_id()
    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)

    if len(assessments) < 2:
        st.info("You need at least two completed assessments to use this comparison tool.")
        footer()
        return

    options = {f"{a.created_at.strftime('%Y-%m-%d %H:%M UTC')} — Score: {a.overall_score}": a.id
               for a in assessments}
    labels = list(options.keys())

    col1, col2 = st.columns(2)
    with col1:
        prev_label = st.selectbox("Previous assessment:", labels, index=min(1, len(labels) - 1))
    with col2:
        curr_label = st.selectbox("Current assessment:", labels, index=0)

    prev_id, curr_id = options[prev_label], options[curr_label]
    if prev_id == curr_id:
        st.warning("Please select two different assessments to compare.")
        footer()
        return

    with session_scope() as session:
        assessments = get_user_assessments(session, user_id)
        prev_assessment = next(a for a in assessments if a.id == prev_id)
        curr_assessment = next(a for a in assessments if a.id == curr_id)
        prev_answers = get_assessment_answers(session, prev_assessment)
        curr_answers = get_assessment_answers(session, curr_assessment)

    prev_result = compute_scores(prev_answers)
    curr_result = compute_scores(curr_answers)

    st.markdown("### Overall Comparison")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Previous Score", f"{prev_result.overall_score:.1f}" if prev_result.overall_score is not None else "N/A")
    with col2:
        st.metric("Current Score", f"{curr_result.overall_score:.1f}" if curr_result.overall_score is not None else "N/A")
    with col3:
        if prev_result.overall_score is not None and curr_result.overall_score is not None:
            diff = curr_result.overall_score - prev_result.overall_score
            st.metric("Change", f"{diff:+.1f}", delta=f"{diff:+.1f}", delta_color="inverse")
        else:
            st.metric("Change", "N/A")

    labels_chart = [CATEGORIES[c] for c in CATEGORY_ORDER]
    before_scores = [prev_result.category_scores[c].score or 0 for c in CATEGORY_ORDER]
    after_scores = [curr_result.category_scores[c].score or 0 for c in CATEGORY_ORDER]
    st.plotly_chart(comparison_bar_chart(labels_chart, before_scores, after_scores), use_container_width=True)

    st.markdown("### Category-by-Category Changes")
    for cat_key in CATEGORY_ORDER:
        prev_cs = prev_result.category_scores[cat_key]
        curr_cs = curr_result.category_scores[cat_key]
        with st.expander(f"{CATEGORIES[cat_key]}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Previous", f"{prev_cs.score:.1f}" if prev_cs.score is not None else "N/A")
            c2.metric("Current", f"{curr_cs.score:.1f}" if curr_cs.score is not None else "N/A")
            if prev_cs.score is not None and curr_cs.score is not None:
                diff = curr_cs.score - prev_cs.score
                c3.metric("Change", f"{diff:+.1f}")
            else:
                c3.metric("Change", "N/A")

    # Newly reported vs resolved concerns
    prev_concerns = set()
    curr_concerns = set()
    for cat_key in CATEGORY_ORDER:
        prev_concerns.update(prev_result.category_scores[cat_key].contributing_factors)
        curr_concerns.update(curr_result.category_scores[cat_key].contributing_factors)

    new_concerns = curr_concerns - prev_concerns
    resolved_concerns = prev_concerns - curr_concerns

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🆕 Newly Reported Concerns")
        if new_concerns:
            for fid in sorted(new_concerns):
                q = get_question(fid)
                if q:
                    st.markdown(f"- {q.text}")
        else:
            st.markdown("None — no new concerns reported.")

    with col2:
        st.markdown("#### ✅ Concerns No Longer Reported")
        if resolved_concerns:
            for fid in sorted(resolved_concerns):
                q = get_question(fid)
                if q:
                    st.markdown(f"- {q.text}")
        else:
            st.markdown("None resolved since the previous assessment.")

    st.markdown("---")
    st.markdown(
        '<div class="ct-notice">A lower score reflects fewer reported risks under the '
        'current assessment rules — it is not a guarantee of safety, and both assessments '
        'remain unchanged in your history.</div>',
        unsafe_allow_html=True
    )
    footer()
