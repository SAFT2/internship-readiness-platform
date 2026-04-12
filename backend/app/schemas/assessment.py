from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AssessmentResumeMetadata(BaseModel):
    filename: str | None
    sha256: str | None
    uri: str | None


class AssessmentResponse(BaseModel):
    id: int
    target_role: str
    overall_score: float
    readiness_level: str
    source_type: str
    resume_metadata: AssessmentResumeMetadata | None
    score_breakdown: dict[str, Any]
    missing_required_skills: list[str]
    recommendations: list[dict[str, Any]]
    created_at: datetime


class AssessmentHistoryItem(BaseModel):
    id: int
    target_role: str
    overall_score: float
    readiness_level: str
    source_type: str
    created_at: datetime


class RoleCatalogResponse(BaseModel):
    roles: list[str]


class RoleDetailsResponse(BaseModel):
    role: str
    total_postings: int
    top_required_skills: list[str]
    top_preferred_skills: list[str]
    required_skill_frequency: dict[str, int]
    preferred_skill_frequency: dict[str, int]
    experience: dict[str, Any]
    remote_percentage: float
    top_locations: dict[str, int]
    sample_job_titles: list[str]


class AssessmentTrendPoint(BaseModel):
    id: int
    overall_score: float
    readiness_level: str
    target_role: str
    created_at: datetime


class AssessmentTrendResponse(BaseModel):
    points: list[AssessmentTrendPoint]
    delta_from_previous: float | None
    delta_from_first: float | None


class AssessmentHistoryPageResponse(BaseModel):
    items: list[AssessmentHistoryItem]
    total: int
    limit: int
    offset: int
    has_more: bool


class AssessmentTrendPageResponse(BaseModel):
    items: list[AssessmentTrendPoint]
    total: int
    limit: int
    offset: int
    has_more: bool
    delta_from_previous: float | None
    delta_from_first: float | None


class AssessmentBenchmarkResponse(BaseModel):
    compared_role: str
    latest_assessment_id: int
    latest_score: float
    target_ready_score: float
    score_gap_to_ready: float
    required_skills_total: int
    missing_required_skills_count: int
    required_skill_coverage_pct: float
    market_new_grad_friendly_percentage: float | None
    market_remote_percentage: float | None


class ProfileAssessmentRequest(BaseModel):
    role: str | None = Field(default=None, min_length=2, max_length=120)
