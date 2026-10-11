"""CyberTrace Start Assessment page — interactive questionnaire."""

import streamlit as st
from app.core.questions import QUESTIONS, CATEGORY_ORDER, CATEGORIES, CATEGORY_DESCRIPTIONS, get_questions_by_category
from app.core.session import get_answers, set_answer, progress_fraction, clear_assessment_state
from app.core.scoring import compute_scores, validate_answers_complete
from app.core.auth import require_login, current_user_id
from app.db.connection import session_scope
from app.db.repository import save_assessment


OPTION_LABELS_CACHE = {}


def _option_index(question, current_value):
    for i, opt in enumerate(question.options):
        if opt.key == current_value:
            return i
    return None


def render():
    require_login()
    st.markdown("## 📝 Start Assessment")
    st.markdown(
        "Answer honestly based on what's currently true. You can leave questions "
        "marked **Not applicable** if they don't apply to you — this will not count "
        "against your score."
    )

    answers = get_answers()
    progress = progress_fraction()
    st.progress(progress, text=f"{len(answers)} of {len(QUESTIONS)} questions answered")

    st.markdown("---")

    for cat_key in CATEGORY_ORDER:
        questions = get_questions_by_category(cat_key)
        answered_in_cat = sum(1 for q in questions if q.id in answers)
        with st.expander(
            f"**{CATEGORIES[cat_key]}** ({answered_in_cat}/{len(questions)} answered)",
            expanded=(answered_in_cat < len(questions))
        ):
            st.caption(CATEGORY_DESCRIPTIONS[cat_key])
            for q in questions:
                st.markdown(f"**{q.text}**" + (" *" if q.required else ""))
                st.caption(q.explanation)
                option_labels = [opt.label for opt in q.options]
                current_value = answers.get(q.id)
                idx = _option_index(q, current_value)
                selected_label = st.radio(
                    label=q.id,
                    options=option_labels,
                    index=idx,
                    key=f"radio_{q.id}",
                    label_visibility="collapsed",
                )
                # Map label back to key and store
                if selected_label is not None:
                    for opt in q.options:
                        if opt.label == selected_label:
                            set_answer(q.id, opt.key)
                            break
                st.markdown("&nbsp;", unsafe_allow_html=True)

    st.markdown("---")

    missing = validate_answers_complete(answers)
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Clear All Answers", use_container_width=True):
            clear_assessment_state()
            st.rerun()

    with col2:
        submit_disabled = len(missing) > 0
        if submit_disabled:
            st.caption(f"⚠ {len(missing)} required question(s) remaining before you can submit.")
        if st.button("Submit Assessment →", type="primary", use_container_width=True, disabled=submit_disabled):
            try:
                result = compute_scores(answers)
            except Exception as e:
                st.error(f"Could not calculate your score: {e}")
                return

            if result.overall_score is None:
                st.error(
                    "No applicable answers were recorded, so a score cannot be calculated. "
                    "Please answer at least one applicable question."
                )
                return

            user_id = current_user_id()
            with session_scope() as session:
                assessment = save_assessment(session, user_id, answers, result)
                st.session_state["last_assessment_id"] = assessment.id

            clear_assessment_state()
            st.session_state["nav_target"] = "Assessment Results"
            st.success("Assessment submitted! Redirecting to your results...")
            st.rerun()
