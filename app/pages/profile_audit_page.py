"""CyberTrace Profile Privacy Audit page."""

import streamlit as st
from app.core.auth import require_login, current_user_id
from app.core.profile_audit import validate_profile_url, score_profile_audit, URLValidationError
from app.db.connection import session_scope
from app.db.repository import save_profile_assessment, get_user_profile_assessments, delete_profile_assessment
from app.ui.styles import risk_badge_html
from app.ui.components import footer
import pandas as pd

ANSWER_OPTIONS = ["Yes", "Partially / Unsure", "No", "Not applicable"]
ANSWER_KEY_MAP = {"Yes": "yes", "Partially / Unsure": "partial", "No": "no", "Not applicable": "na"}


def render():
    require_login()
    st.markdown("## 🔎 Public Profile Privacy Audit")
    st.markdown(
        "Manually assess a specific public profile's privacy exposure. "
        "**CyberTrace does not fetch, scrape, or verify this URL** — your answers "
        "below are the only basis for this audit."
    )

    with st.form("profile_audit_form"):
        platform = st.text_input("Platform name (optional)", placeholder="e.g. Instagram, LinkedIn, X")
        url = st.text_input("Profile URL (optional)", placeholder="https://example.com/yourprofile")

        st.markdown("#### Questions")
        is_public = st.radio("Is this profile public (visible to anyone, not just approved connections)?", ANSWER_OPTIONS, index=None)
        contact_visible = st.radio("Are contact details (email/phone) visible on this profile?", ANSWER_OPTIONS, index=None)
        identity_exposed = st.radio("Are identifying details (full name, birthdate, location) exposed?", ANSWER_OPTIONS, index=None)
        routine_revealed = st.radio("Do posts on this profile reveal daily routines or locations?", ANSWER_OPTIONS, index=None)
        links_other = st.radio("Does this profile link to or reveal your other accounts?", ANSWER_OPTIONS, index=None)

        submitted = st.form_submit_button("Run Audit", type="primary")

    if submitted:
        try:
            clean_url = validate_profile_url(url)
        except URLValidationError as e:
            st.error(str(e))
            return

        answers = {
            "is_public": ANSWER_KEY_MAP.get(is_public),
            "contact_visible": ANSWER_KEY_MAP.get(contact_visible),
            "identity_exposed": ANSWER_KEY_MAP.get(identity_exposed),
            "routine_revealed": ANSWER_KEY_MAP.get(routine_revealed),
            "links_other_accounts": ANSWER_KEY_MAP.get(links_other),
        }

        if all(v is None for v in answers.values()):
            st.error("Please answer at least one question.")
            return

        result = score_profile_audit(answers)

        user_id = current_user_id()
        with session_scope() as session:
            save_profile_assessment(session, user_id, {
                "platform_name": platform.strip() or None,
                "profile_url": clean_url or None,
                "is_public": answers["is_public"],
                "contact_visible": answers["contact_visible"],
                "identity_exposed": answers["identity_exposed"],
                "routine_revealed": answers["routine_revealed"],
                "links_other_accounts": answers["links_other_accounts"],
                "audit_score": result.score,
                "audit_risk_level": result.risk_level,
            })

        st.success("Audit saved.")
        if result.score is not None:
            st.markdown(f"### Result: {result.score:.1f}/100 &nbsp; {risk_badge_html(result.risk_level)}", unsafe_allow_html=True)
            if result.concerns:
                st.markdown("**Concerns identified:**")
                for c in result.concerns:
                    st.markdown(f"- {c}")
        else:
            st.info("No applicable answers were recorded, so no score was calculated.")

        st.caption("This result is based entirely on your own answers above, not on any automated inspection of the profile.")

    st.markdown("---")
    st.markdown("### Past Profile Audits")
    user_id = current_user_id()
    with session_scope() as session:
        audits = get_user_profile_assessments(session, user_id)

    if not audits:
        st.info("No profile audits saved yet.")
    else:
        rows = []
        for a in audits:
            rows.append({
                "id": a.id,
                "Date": a.created_at.strftime("%Y-%m-%d %H:%M UTC"),
                "Platform": a.platform_name or "—",
                "Score": a.audit_score if a.audit_score is not None else "N/A",
                "Risk Level": a.audit_risk_level or "N/A",
            })
        df = pd.DataFrame(rows).drop(columns=["id"])
        st.dataframe(df, use_container_width=True, hide_index=True)

        delete_id = st.selectbox(
            "Select an audit to delete:",
            [r["id"] for r in rows],
            format_func=lambda i: next(f"{r['Date']} — {r['Platform']}" for r in rows if r["id"] == i),
        )
        if st.button("Delete selected audit"):
            with session_scope() as session:
                delete_profile_assessment(session, user_id, delete_id)
            st.success("Deleted.")
            st.rerun()

    st.markdown("---")
    footer()
