"""
CyberTrace Session State Management
=======================================
Manages the in-progress assessment answers in Streamlit session_state.
All keys are namespaced with `assess_` so they are easy to find and
clear on logout, and so they never collide with other pages' state.

IMPORTANT: session_state is per-browser-session in Streamlit, not a
global variable, so this is safe for concurrent users. We still never
store cross-user data here, and sensitive in-progress answers are
cleared on logout (see app/core/auth.py:logout_user).
"""

import streamlit as st
from app.core.questions import QUESTIONS, all_question_ids

ANSWERS_KEY = "assess_answers"
CURRENT_INDEX_KEY = "assess_current_index"


def init_assessment_state():
    if ANSWERS_KEY not in st.session_state:
        st.session_state[ANSWERS_KEY] = {}
    if CURRENT_INDEX_KEY not in st.session_state:
        st.session_state[CURRENT_INDEX_KEY] = 0


def get_answers() -> dict:
    init_assessment_state()
    return st.session_state[ANSWERS_KEY]


def set_answer(question_id: str, answer_key: str):
    init_assessment_state()
    st.session_state[ANSWERS_KEY][question_id] = answer_key


def clear_assessment_state():
    st.session_state[ANSWERS_KEY] = {}
    st.session_state[CURRENT_INDEX_KEY] = 0
    # Also clear each question's radio widget state so the UI resets
    # visually, not just the underlying answers dict.
    for q in QUESTIONS:
        st.session_state.pop(f"radio_{q.id}", None)


def progress_fraction() -> float:
    answers = get_answers()
    total = len(all_question_ids())
    if total == 0:
        return 0.0
    return min(1.0, len(answers) / total)


def answered_count() -> int:
    return len(get_answers())


def total_question_count() -> int:
    return len(QUESTIONS)
