"""
CyberTrace Database Models
=============================
SQLAlchemy ORM models. Works with SQLite by default; the engine URL
can be swapped for a hosted Postgres/MySQL database via Streamlit
secrets without changing this file (see app/db/connection.py).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    profile_assessments = relationship("ProfileAssessment", back_populates="user", cascade="all, delete-orphan")
    user_recommendations = relationship("UserRecommendation", back_populates="user", cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    overall_score = Column(Float, nullable=True)
    overall_risk_level = Column(String(16), nullable=True)
    total_applicable = Column(Integer, nullable=False, default=0)
    total_concerns = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="assessments")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")
    category_scores = relationship("AssessmentCategoryScore", back_populates="assessment", cascade="all, delete-orphan")
    user_recommendations = relationship("UserRecommendation", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(16), nullable=False)
    category = Column(String(32), nullable=False)
    answer_key = Column(String(16), nullable=False)
    risk_value = Column(Float, nullable=True)   # None if N/A
    weight = Column(Float, nullable=False)

    assessment = relationship("Assessment", back_populates="responses")

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_id", name="uq_assessment_question"),
    )


class AssessmentCategoryScore(Base):
    __tablename__ = "assessment_category_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(32), nullable=False)
    score = Column(Float, nullable=True)
    risk_level = Column(String(16), nullable=True)
    applicable_count = Column(Integer, nullable=False, default=0)
    concern_count = Column(Integer, nullable=False, default=0)

    assessment = relationship("Assessment", back_populates="category_scores")

    __table_args__ = (
        UniqueConstraint("assessment_id", "category", name="uq_assessment_category"),
    )


class UserRecommendation(Base):
    """Tracks completion status of recommendations tied to a specific
    assessment. Completing one never mutates the historical score."""
    __tablename__ = "user_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    rec_id = Column(String(32), nullable=False)   # e.g. "REC-ID-01"
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_recommendations")
    assessment = relationship("Assessment", back_populates="user_recommendations")

    __table_args__ = (
        UniqueConstraint("assessment_id", "rec_id", name="uq_assessment_rec"),
    )


class ProfileAssessment(Base):
    """Manual, user-entered public profile privacy audit entries."""
    __tablename__ = "profile_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    platform_name = Column(String(128), nullable=True)
    profile_url = Column(String(512), nullable=True)
    is_public = Column(String(16), nullable=True)        # yes/partial/no
    contact_visible = Column(String(16), nullable=True)
    identity_exposed = Column(String(16), nullable=True)
    routine_revealed = Column(String(16), nullable=True)
    links_other_accounts = Column(String(16), nullable=True)
    audit_score = Column(Float, nullable=True)
    audit_risk_level = Column(String(16), nullable=True)

    user = relationship("User", back_populates="profile_assessments")


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
