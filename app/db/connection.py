"""
CyberTrace Database Connection & Storage Configuration
=========================================================
Decides which database backend to use:

1. If a `[connections.postgresql]` / `[connections.mysql]`-style
   secret or a `DATABASE_URL` is configured in Streamlit secrets,
   use that hosted database (durable storage).
2. Otherwise, fall back to a local SQLite file for single-instance
   demonstration use. This is NOT guaranteed to persist on Streamlit
   Community Cloud, because the filesystem there is ephemeral and can
   be wiped on redeploys, reboots, or app sleep/wake cycles.

The rest of the application only depends on `get_engine()` /
`get_session()` here, so swapping the backend never requires changes
elsewhere.
"""

import os
import streamlit as st
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from app.db.models import Base

DEFAULT_SQLITE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "cybertrace.db"
)


def _hosted_database_url() -> str | None:
    """Look for a hosted database URL in Streamlit secrets or env vars.
    Returns None if not configured, triggering the SQLite fallback."""
    try:
        if "database" in st.secrets and st.secrets["database"].get("url"):
            return st.secrets["database"]["url"]
    except Exception:
        pass
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    return None


def using_hosted_database() -> bool:
    return _hosted_database_url() is not None


@st.cache_resource(show_spinner=False)
def get_engine():
    """Create (once per process) the SQLAlchemy engine and ensure
    tables exist. Uses an idempotent create_all — never drops or
    recreates existing tables/data."""
    hosted_url = _hosted_database_url()

    if hosted_url:
        engine = create_engine(hosted_url, pool_pre_ping=True)
    else:
        os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)
        engine = create_engine(
            f"sqlite:///{DEFAULT_SQLITE_PATH}",
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Idempotent: only creates tables that don't already exist.
    Base.metadata.create_all(engine)
    return engine


def get_sessionmaker():
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Session:
    """Provide a transactional scope for a series of DB operations."""
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
