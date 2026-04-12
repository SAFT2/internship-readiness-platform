import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.dependencies import get_current_user, get_db
from app.main import app
from app.models.assessment import Assessment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.db.session import Base
from app.services.ml_client import MLServiceClient


@pytest.fixture()
def client_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    setup_db = TestingSessionLocal()
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
    )
    setup_db.add(user)
    setup_db.commit()
    setup_db.refresh(user)

    profile = StudentProfile(
        user_id=user.id,
        target_role="ML Intern",
        skills_csv="python,sql,git",
        projects_count=2,
        candidate_years=0.5,
        experience_type="research",
    )
    setup_db.add(profile)
    setup_db.commit()

    user_id = user.id
    user_email = user.email
    setup_db.close()

    current_user = SimpleNamespace(id=user_id, email=user_email)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user():
        return current_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client, TestingSessionLocal, current_user

    app.dependency_overrides.clear()


def _insert_assessment(db, user_id: int, score: float, created_at: datetime) -> None:
    db.add(
        Assessment(
            user_id=user_id,
            target_role="ML Intern",
            overall_score=score,
            readiness_level="Developing" if score < 70 else "Ready",
            source_type="profile",
            score_breakdown_json=json.dumps(
                {
                    "skills_total": score - 22,
                    "required_skills": score - 27,
                    "preferred_skills": 5,
                    "projects": 12,
                    "experience": 10,
                }
            ),
            missing_required_skills_json=json.dumps(["pytorch"] if score < 70 else []),
            recommendations_json=json.dumps(
                [
                    {
                        "skill": "pytorch",
                        "priority": "High",
                        "action": "Build one pytorch project",
                    }
                ]
            ),
            created_at=created_at,
        )
    )
    db.commit()


def test_history_and_trend_query_endpoints(client_and_db):
    client, SessionLocal, current_user = client_and_db
    now = datetime.now(UTC)

    db = SessionLocal()
    _insert_assessment(db, current_user.id, 52.5, now - timedelta(days=2))
    _insert_assessment(db, current_user.id, 76.0, now - timedelta(days=1))
    db.close()

    history = client.get(
        "/api/v1/assessments/history/query",
        params={"limit": 1, "offset": 0, "source_type": "profile", "role_name": "ML Intern"},
    )
    assert history.status_code == 200
    history_body = history.json()
    assert history_body["total"] == 2
    assert history_body["has_more"] is True
    assert len(history_body["items"]) == 1

    trend = client.get(
        "/api/v1/assessments/trend/query",
        params={"limit": 2, "offset": 0, "source_type": "profile"},
    )
    assert trend.status_code == 200
    trend_body = trend.json()
    assert len(trend_body["items"]) == 2
    assert trend_body["delta_from_previous"] == pytest.approx(23.5)


def test_benchmark_and_dashboard_trend(client_and_db, monkeypatch):
    client, SessionLocal, current_user = client_and_db
    now = datetime.now(UTC)

    db = SessionLocal()
    _insert_assessment(db, current_user.id, 60.0, now - timedelta(days=2))
    _insert_assessment(db, current_user.id, 80.0, now - timedelta(days=1))
    db.close()

    def fake_get_role_details(self, role_name: str):
        return {
            "role": role_name,
            "total_postings": 100,
            "top_required_skills": ["python", "sql", "git", "pytorch"],
            "top_preferred_skills": ["docker", "aws"],
            "required_skill_frequency": {"python": 90, "sql": 80, "git": 70, "pytorch": 60},
            "preferred_skill_frequency": {"docker": 30, "aws": 25},
            "experience": {"new_grad_friendly_percentage": 40.0},
            "remote_percentage": 35.0,
            "top_locations": {"CA": 50},
            "sample_job_titles": ["ML Intern"],
        }

    monkeypatch.setattr(MLServiceClient, "get_role_details", fake_get_role_details)

    benchmark = client.get("/api/v1/assessments/benchmark", params={"role_name": "ML Intern"})
    assert benchmark.status_code == 200
    benchmark_body = benchmark.json()
    assert benchmark_body["compared_role"] == "ML Intern"
    assert benchmark_body["latest_score"] == 80.0
    assert benchmark_body["required_skills_total"] == 4

    chart = client.get("/api/v1/dashboard/trend", params={"points": 10, "role_name": "ML Intern"})
    assert chart.status_code == 200
    chart_body = chart.json()
    assert len(chart_body["points"]) == 2
    assert chart_body["average_score"] == pytest.approx(70.0)
