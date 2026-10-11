"""CyberTrace Login / Register / Account management page."""

import streamlit as st
from app.core.auth import (
    register_user, login_user, logout_user, is_authenticated,
    current_username, current_user_id, AuthError
)
from app.db.connection import session_scope
from app.db.repository import delete_user_account
from app.ui.components import footer


def render_login_form():
    st.markdown("## 🔐 Account")
    tab_login, tab_register = st.tabs(["Log In", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)
        if submitted:
            if not username or not password:
                st.error("Please enter both a username and password.")
            elif login_user(username, password):
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Choose a username", key="reg_username")
            new_password = st.text_input("Choose a password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm password", type="password", key="reg_confirm")
            st.caption("Password must be at least 10 characters.")
            submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        if submitted:
            try:
                register_user(new_username, new_password, confirm_password)
                st.success("Account created! You can now log in from the 'Log In' tab.")
            except AuthError as e:
                st.error(str(e))

    st.markdown("---")
    st.markdown("""
    <div class="ct-notice">
    Your account only stores a hashed password and your assessment data — never a
    plaintext password. This single-user-per-account model keeps your assessment
    history private to you; every record is checked against your account before
    being shown or modified.
    </div>
    """, unsafe_allow_html=True)
    footer()


def render_account_management():
    st.markdown("## 🔐 Account")
    st.markdown(f"Logged in as **{current_username()}**")

    if st.button("Log Out"):
        logout_user()
        st.rerun()

    st.markdown("---")
    st.markdown("### Delete Account")
    st.warning(
        "Deleting your account permanently removes all your assessments, "
        "recommendations progress, and profile audits. This cannot be undone."
    )
    confirm = st.text_input("Type DELETE to confirm account deletion:")
    if st.button("Permanently Delete My Account", type="secondary"):
        if confirm.strip() == "DELETE":
            user_id = current_user_id()
            with session_scope() as session:
                delete_user_account(session, user_id)
            logout_user()
            st.success("Your account and all associated data have been deleted.")
            st.rerun()
        else:
            st.error("Please type DELETE exactly to confirm.")

    st.markdown("---")
    footer()


def render():
    if is_authenticated():
        render_account_management()
    else:
        render_login_form()
