"""
CyberTrace Authentication
============================
Implements registration, login, logout, and session management.

- Passwords are hashed with bcrypt (via passlib-free direct bcrypt
  calls) and never stored or logged in plaintext.
- Streamlit session_state holds only the authenticated user's id and
  username for the duration of the browser session; it is not used
  as a substitute for verifying ownership server-side. Every data
  access still re-checks `user_id` against the database record
  (see app/db/repository.py).
- No secrets, hashes, or tokens are ever written to logs or shown in
  error messages.
"""

import re
import secrets
import bcrypt
import streamlit as st

from app.db.connection import session_scope
from app.db.repository import get_user_by_username, create_user, update_last_login

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
MIN_PASSWORD_LENGTH = 10


class AuthError(Exception):
    pass


def validate_username(username: str) -> None:
    if not username or not USERNAME_PATTERN.match(username):
        raise AuthError(
            "Username must be 3-32 characters and contain only letters, "
            "numbers, underscores, hyphens, or periods."
        )


def validate_password(password: str) -> None:
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    if password.lower() in ("password", "123456789", "qwertyuiop"):
        raise AuthError("This password is too common. Please choose a stronger password.")


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def register_user(username: str, password: str, confirm_password: str) -> None:
    username = username.strip()
    validate_username(username)
    validate_password(password)
    if password != confirm_password:
        raise AuthError("Passwords do not match.")

    with session_scope() as session:
        existing = get_user_by_username(session, username)
        if existing is not None:
            raise AuthError("That username is already taken.")
        pw_hash = hash_password(password)
        create_user(session, username, pw_hash)


def login_user(username: str, password: str) -> bool:
    """Attempt login. On success, populates st.session_state with the
    authenticated user's id/username and returns True."""
    username = username.strip()
    with session_scope() as session:
        user = get_user_by_username(session, username)
        if user is None or not user.is_active:
            # Avoid revealing whether the username exists.
            # Still perform a dummy hash check to reduce timing signal.
            bcrypt.checkpw(b"dummy", bcrypt.gensalt())
            return False
        if not verify_password(password, user.password_hash):
            return False
        update_last_login(session, user)
        st.session_state["auth_user_id"] = user.id
        st.session_state["auth_username"] = user.username
        st.session_state["session_token"] = secrets.token_hex(16)
        return True


def logout_user() -> None:
    for key in ("auth_user_id", "auth_username", "session_token"):
        st.session_state.pop(key, None)
    # Clear in-progress assessment / sensitive page state on logout.
    for key in list(st.session_state.keys()):
        if key.startswith("assess_") or key.startswith("profile_audit_") \
                or key.startswith("radio_") or key.startswith("complete_") \
                or key in ("last_assessment_id", "generated_pdf"):
            del st.session_state[key]


def is_authenticated() -> bool:
    return "auth_user_id" in st.session_state and st.session_state.get("auth_user_id") is not None


def current_user_id() -> int | None:
    return st.session_state.get("auth_user_id")


def current_username() -> str | None:
    return st.session_state.get("auth_username")


def require_login():
    """Call at the top of any page that requires authentication.
    Stops page execution and shows a friendly message if not logged in."""
    if not is_authenticated():
        st.warning("Please log in or create an account to use this feature.")
        st.stop()
