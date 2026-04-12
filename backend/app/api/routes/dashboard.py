import json
from datetime import timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.assessment import Assessment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, DashboardTrendPoint, DashboardTrendResponse


router = APIRouter()


def _profile_completion(profile: StudentProfile | None) -> float:
    if not profile:
        return 0.0

    checks = [
        bool(profile.target_role.strip()),
        bool(profile.skills_csv.strip()),
        profile.projects_count > 0,
        profile.candidate_years >= 0,
        bool(profile.experience_type.strip()),
    ]
    return round((sum(1 for item in checks if item) / len(checks)) * 100, 1)


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummary:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()

    latest = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    total_assessments = db.query(Assessment).filter(Assessment.user_id == current_user.id).count()

    if not latest:
        return DashboardSummary(
            latest_score=None,
            readiness_level=None,
            target_role=profile.target_role if profile else None,
            missing_skills_top5=[],
            recommendations_top3=[],
            total_assessments=total_assessments,
            profile_completion=_profile_completion(profile),
            last_assessed_at=None,
        )

    missing_skills = json.loads(latest.missing_required_skills_json)
    recommendations = json.loads(latest.recommendations_json)

    recommendation_actions = [
        str(item.get("action", ""))
        for item in recommendations
        if isinstance(item, dict) and str(item.get("action", "")).strip()
    ]

    return DashboardSummary(
        latest_score=latest.overall_score,
        readiness_level=latest.readiness_level,
        target_role=latest.target_role,
        missing_skills_top5=missing_skills[:5],
        recommendations_top3=recommendation_actions[:3],
        total_assessments=total_assessments,
        profile_completion=_profile_completion(profile),
        last_assessed_at=latest.created_at,
    )


@router.get("/trend", response_model=DashboardTrendResponse)
def get_dashboard_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    points: int = Query(default=12, ge=1, le=50),
    role_name: str | None = Query(default=None),
):
    query = db.query(Assessment).filter(Assessment.user_id == current_user.id)
    if role_name and role_name.strip():
        query = query.filter(Assessment.target_role == role_name.strip())

    rows = query.order_by(Assessment.created_at.desc()).limit(points).all()
    ordered_rows = list(reversed(rows))

    trend_points = [
        DashboardTrendPoint(
            label=row.created_at.replace(tzinfo=timezone.utc).date().isoformat(),
            score=row.overall_score,
            readiness_level=row.readiness_level,
            target_role=row.target_role,
        )
        for row in ordered_rows
    ]

    if not trend_points:
        return DashboardTrendResponse(points=[], average_score=None, max_score=None, min_score=None)

    scores = [point.score for point in trend_points]
    return DashboardTrendResponse(
        points=trend_points,
        average_score=round(sum(scores) / len(scores), 2),
        max_score=max(scores),
        min_score=min(scores),
    )
