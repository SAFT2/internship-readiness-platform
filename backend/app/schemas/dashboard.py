from datetime import datetime

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    latest_score: float | None
    readiness_level: str | None
    target_role: str | None
    missing_skills_top5: list[str]
    recommendations_top3: list[str]
    total_assessments: int
    profile_completion: float
    last_assessed_at: datetime | None


class DashboardTrendPoint(BaseModel):
    label: str
    score: float
    readiness_level: str
    target_role: str


class DashboardTrendResponse(BaseModel):
    points: list[DashboardTrendPoint]
    average_score: float | None
    max_score: float | None
    min_score: float | None
