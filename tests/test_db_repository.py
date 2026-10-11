"""
Integration tests for the database repository layer.

Uses a temporary, isolated SQLite file per test run (never touches
data/cybertrace.db) to verify: idempotent schema creation, assessment
save/retrieve round-trips, and strict per-user ownership enforcement.

Run with: pytest tests/test_db_repository.py -v
"""
import sys
import os
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.db.models import Base
from app.core.scoring import compute_scores
from app.core.auth import hash_password
from app.db import repository as repo


@pytest.fixture
def db_session_factory():
    """Isolated in-memory SQLite DB per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    @contextmanager
    def scope():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    yield scope


class TestSchemaIdempotency:
    def test_create_all_is_idempotent(self, db_session_factory):
        # Calling create_all twice on the same engine should not error
        # or drop data.
        with db_session_factory() as session:
            user = repo.create_user(session, "testuser1", hash_password("correcthorsebattery"))
            user_id = user.id

        with db_session_factory() as session:
            fetched = repo.get_user_by_id(session, user_id)
            assert fetched is not None
            assert fetched.username == "testuser1"


class TestAssessmentRoundTrip:
    def test_save_and_retrieve_assessment(self, db_session_factory):
        with db_session_factory() as session:
            user = repo.create_user(session, "alice", hash_password("correcthorsebattery"))
            user_id = user.id

        answers = {"ID-01": "yes", "SEC-01": "no"}
        result = compute_scores(answers)

        with db_session_factory() as session:
            assessment = repo.save_assessment(session, user_id, answers, result)
            assessment_id = assessment.id

        with db_session_factory() as session:
            fetched = repo.get_assessment_for_user(session, user_id, assessment_id)
            assert fetched is not None
            assert fetched.overall_score == result.overall_score
            rebuilt_answers = repo.get_assessment_answers(session, fetched)
            assert rebuilt_answers == answers

    def test_historical_assessment_unchanged_by_new_assessment(self, db_session_factory):
        with db_session_factory() as session:
            user = repo.create_user(session, "bob", hash_password("correcthorsebattery"))
            user_id = user.id

        answers1 = {"ID-01": "yes"}
        result1 = compute_scores(answers1)
        with db_session_factory() as session:
            a1 = repo.save_assessment(session, user_id, answers1, result1)
            a1_id = a1.id
            a1_score = a1.overall_score

        answers2 = {"ID-01": "no"}
        result2 = compute_scores(answers2)
        with db_session_factory() as session:
            repo.save_assessment(session, user_id, answers2, result2)

        with db_session_factory() as session:
            refetched = repo.get_assessment_for_user(session, user_id, a1_id)
            assert refetched.overall_score == a1_score  # unchanged


class TestOwnershipIsolation:
    def test_user_cannot_access_other_users_assessment(self, db_session_factory):
        with db_session_factory() as session:
            user_a = repo.create_user(session, "usera", hash_password("correcthorsebattery"))
            user_b = repo.create_user(session, "userb", hash_password("correcthorsebattery"))
            user_a_id, user_b_id = user_a.id, user_b.id

        answers = {"ID-01": "yes"}
        result = compute_scores(answers)
        with db_session_factory() as session:
            assessment = repo.save_assessment(session, user_a_id, answers, result)
            assessment_id = assessment.id

        with db_session_factory() as session:
            # User B tries to access User A's assessment
            fetched = repo.get_assessment_for_user(session, user_b_id, assessment_id)
            assert fetched is None  # must be None, not User A's data

    def test_user_cannot_delete_other_users_assessment(self, db_session_factory):
        with db_session_factory() as session:
            user_a = repo.create_user(session, "usera2", hash_password("correcthorsebattery"))
            user_b = repo.create_user(session, "userb2", hash_password("correcthorsebattery"))
            user_a_id, user_b_id = user_a.id, user_b.id

        answers = {"ID-01": "yes"}
        result = compute_scores(answers)
        with db_session_factory() as session:
            assessment = repo.save_assessment(session, user_a_id, answers, result)
            assessment_id = assessment.id

        with db_session_factory() as session:
            deleted = repo.delete_assessment(session, user_b_id, assessment_id)
            assert deleted is False

        with db_session_factory() as session:
            still_there = repo.get_assessment_for_user(session, user_a_id, assessment_id)
            assert still_there is not None

    def test_recommendation_completion_requires_ownership(self, db_session_factory):
        with db_session_factory() as session:
            user_a = repo.create_user(session, "usera3", hash_password("correcthorsebattery"))
            user_b = repo.create_user(session, "userb3", hash_password("correcthorsebattery"))
            user_a_id, user_b_id = user_a.id, user_b.id

        answers = {"ID-01": "yes"}
        result = compute_scores(answers)
        with db_session_factory() as session:
            assessment = repo.save_assessment(session, user_a_id, answers, result)
            assessment_id = assessment.id

        with db_session_factory() as session:
            with pytest.raises(PermissionError):
                repo.set_recommendation_completion(session, user_b_id, assessment_id, "REC-ID-01", True)


class TestAccountDeletion:
    def test_deleting_user_cascades_assessments(self, db_session_factory):
        with db_session_factory() as session:
            user = repo.create_user(session, "charlie", hash_password("correcthorsebattery"))
            user_id = user.id

        answers = {"ID-01": "yes"}
        result = compute_scores(answers)
        with db_session_factory() as session:
            assessment = repo.save_assessment(session, user_id, answers, result)
            assessment_id = assessment.id

        with db_session_factory() as session:
            repo.delete_user_account(session, user_id)

        with db_session_factory() as session:
            assert repo.get_user_by_id(session, user_id) is None
            assert repo.get_assessment_for_user(session, user_id, assessment_id) is None


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
