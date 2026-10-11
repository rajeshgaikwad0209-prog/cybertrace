"""
CyberTrace Data Access Layer
===============================
Every function here that touches assessment or profile data requires
a `user_id` and filters strictly by it, so one user can never read or
modify another user's records. All queries go through SQLAlchemy's
parameterized ORM layer (no raw string-built SQL).
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.connection import session_scope
from app.db.models import (
    User, Assessment, AssessmentResponse, AssessmentCategoryScore,
    UserRecommendation, ProfileAssessment
)
from app.core.scoring import compute_scores, ScoringResult
from app.core.questions import get_question


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user_by_username(session: Session, username: str) -> Optional[User]:
    stmt = select(User).where(User.username == username)
    return session.execute(stmt).scalar_one_or_none()


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    return session.get(User, user_id)


def create_user(session: Session, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    session.add(user)
    session.flush()
    return user


def update_last_login(session: Session, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    session.add(user)


def delete_user_account(session: Session, user_id: int) -> bool:
    """Deletes a user and all owned records (cascades configured in models)."""
    user = session.get(User, user_id)
    if user is None:
        return False
    session.delete(user)
    return True


# ---------------------------------------------------------------------------
# Assessments
# ---------------------------------------------------------------------------

def save_assessment(session: Session, user_id: int, answers: Dict[str, str],
                     result: ScoringResult, notes: Optional[str] = None) -> Assessment:
    """Persist a completed assessment, its per-question responses, and
    per-category scores in a single transaction."""
    assessment = Assessment(
        user_id=user_id,
        overall_score=result.overall_score,
        overall_risk_level=result.overall_risk_level,
        total_applicable=result.total_applicable,
        total_concerns=result.total_concerns,
        notes=notes,
    )
    session.add(assessment)
    session.flush()  # get assessment.id

    for question_id, answer_key in answers.items():
        q = get_question(question_id)
        if q is None:
            continue
        option = q.option_by_key(answer_key)
        risk_value = option.risk_value if option else None
        response = AssessmentResponse(
            assessment_id=assessment.id,
            question_id=question_id,
            category=q.category,
            answer_key=answer_key,
            risk_value=risk_value,
            weight=q.weight,
        )
        session.add(response)

    for category, cat_score in result.category_scores.items():
        cs = AssessmentCategoryScore(
            assessment_id=assessment.id,
            category=category,
            score=cat_score.score,
            risk_level=cat_score.risk_level,
            applicable_count=cat_score.applicable_count,
            concern_count=cat_score.concern_count,
        )
        session.add(cs)

    session.flush()
    return assessment


def get_user_assessments(session: Session, user_id: int) -> List[Assessment]:
    """Return all assessments owned by this user, most recent first."""
    stmt = (
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
    )
    return list(session.execute(stmt).scalars().all())


def get_assessment_for_user(session: Session, user_id: int, assessment_id: int) -> Optional[Assessment]:
    """Fetch a single assessment, but ONLY if it belongs to this user.
    This is the core ownership check used before any read/export."""
    stmt = (
        select(Assessment)
        .where(Assessment.id == assessment_id, Assessment.user_id == user_id)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_latest_assessment(session: Session, user_id: int) -> Optional[Assessment]:
    stmt = (
        select(Assessment)
        .where(Assessment.user_id == user_id)
        .order_by(Assessment.created_at.desc())
        .limit(1)
    )
    return session.execute(stmt).scalar_one_or_none()


def get_assessment_answers(session: Session, assessment: Assessment) -> Dict[str, str]:
    """Rebuild the answers dict from stored responses for a given
    (already ownership-checked) assessment."""
    return {r.question_id: r.answer_key for r in assessment.responses}


def delete_assessment(session: Session, user_id: int, assessment_id: int) -> bool:
    assessment = get_assessment_for_user(session, user_id, assessment_id)
    if assessment is None:
        return False
    session.delete(assessment)
    return True


# ---------------------------------------------------------------------------
# Recommendation completion tracking
# ---------------------------------------------------------------------------

def set_recommendation_completion(session: Session, user_id: int, assessment_id: int,
                                   rec_id: str, completed: bool) -> None:
    # Ownership check: the assessment must belong to this user.
    assessment = get_assessment_for_user(session, user_id, assessment_id)
    if assessment is None:
        raise PermissionError("Assessment does not belong to this user.")

    stmt = select(UserRecommendation).where(
        UserRecommendation.assessment_id == assessment_id,
        UserRecommendation.rec_id == rec_id,
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        existing.completed = completed
        existing.completed_at = datetime.now(timezone.utc) if completed else None
    else:
        session.add(UserRecommendation(
            user_id=user_id,
            assessment_id=assessment_id,
            rec_id=rec_id,
            completed=completed,
            completed_at=datetime.now(timezone.utc) if completed else None,
        ))


def get_recommendation_completions(session: Session, user_id: int, assessment_id: int) -> Dict[str, bool]:
    assessment = get_assessment_for_user(session, user_id, assessment_id)
    if assessment is None:
        return {}
    stmt = select(UserRecommendation).where(
        UserRecommendation.user_id == user_id,
        UserRecommendation.assessment_id == assessment_id,
    )
    results = session.execute(stmt).scalars().all()
    return {r.rec_id: r.completed for r in results}


# ---------------------------------------------------------------------------
# Profile privacy audits
# ---------------------------------------------------------------------------

def save_profile_assessment(session: Session, user_id: int, data: dict) -> ProfileAssessment:
    pa = ProfileAssessment(user_id=user_id, **data)
    session.add(pa)
    session.flush()
    return pa


def get_user_profile_assessments(session: Session, user_id: int) -> List[ProfileAssessment]:
    stmt = (
        select(ProfileAssessment)
        .where(ProfileAssessment.user_id == user_id)
        .order_by(ProfileAssessment.created_at.desc())
    )
    return list(session.execute(stmt).scalars().all())


def delete_profile_assessment(session: Session, user_id: int, profile_assessment_id: int) -> bool:
    stmt = select(ProfileAssessment).where(
        ProfileAssessment.id == profile_assessment_id,
        ProfileAssessment.user_id == user_id,
    )
    pa = session.execute(stmt).scalar_one_or_none()
    if pa is None:
        return False
    session.delete(pa)
    return True
