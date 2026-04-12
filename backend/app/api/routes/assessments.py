import json
from hashlib import sha256

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.assessment import Assessment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.assessment import (
    AssessmentBenchmarkResponse,
    AssessmentHistoryItem,
    AssessmentHistoryPageResponse,
    AssessmentResumeMetadata,
    AssessmentResponse,
    RoleDetailsResponse,
    AssessmentTrendPoint,
    AssessmentTrendPageResponse,
    AssessmentTrendResponse,
    RoleCatalogResponse,
)
from app.services.ml_client import MLServiceClient


router = APIRouter()


def _to_response(row: Assessment) -> AssessmentResponse:
    resume_metadata = None
    if row.resume_filename or row.resume_sha256 or row.resume_uri:
        resume_metadata = AssessmentResumeMetadata(
            filename=row.resume_filename,
            sha256=row.resume_sha256,
            uri=row.resume_uri,
        )

    return AssessmentResponse(
        id=row.id,
        target_role=row.target_role,
        overall_score=row.overall_score,
        readiness_level=row.readiness_level,
        source_type=row.source_type,
        resume_metadata=resume_metadata,
        score_breakdown=json.loads(row.score_breakdown_json),
        missing_required_skills=json.loads(row.missing_required_skills_json),
        recommendations=json.loads(row.recommendations_json),
        created_at=row.created_at,
    )


@router.get("/roles", response_model=RoleCatalogResponse)
def get_role_catalog() -> RoleCatalogResponse:
    client = MLServiceClient()
    try:
        roles = client.list_roles()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    return RoleCatalogResponse(roles=sorted(set(roles)))


@router.get("/roles/{role_name}", response_model=RoleDetailsResponse)
def get_role_details(role_name: str) -> RoleDetailsResponse:
    client = MLServiceClient()
    try:
        payload = client.get_role_details(role_name=role_name)
    except Exception as exc:
        detail = str(exc)
        if "404" in detail:
            raise HTTPException(status_code=404, detail=f"Unknown role '{role_name}'") from exc
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    return RoleDetailsResponse(
        role=str(payload.get("role", role_name)),
        total_postings=int(payload.get("total_postings", 0)),
        top_required_skills=[str(skill) for skill in payload.get("top_required_skills", [])],
        top_preferred_skills=[str(skill) for skill in payload.get("top_preferred_skills", [])],
        required_skill_frequency={
            str(key): int(value) for key, value in dict(payload.get("required_skill_frequency", {})).items()
        },
        preferred_skill_frequency={
            str(key): int(value) for key, value in dict(payload.get("preferred_skill_frequency", {})).items()
        },
        experience=dict(payload.get("experience", {})),
        remote_percentage=float(payload.get("remote_percentage", 0.0)),
        top_locations={str(key): int(value) for key, value in dict(payload.get("top_locations", {})).items()},
        sample_job_titles=[str(title) for title in payload.get("sample_job_titles", [])],
    )


@router.post("/from-resume", response_model=AssessmentResponse)
def create_assessment_from_resume(
    role: str = Form(...),
    resume: UploadFile = File(...),
    resume_uri: str | None = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    if not resume.filename or not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Resume file must be a PDF")

    content = resume.file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    client = MLServiceClient()
    try:
        result = client.parse_resume_and_assess(content, resume.filename, role)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    assessment = result.get("assessment")
    if not assessment:
        raise HTTPException(status_code=502, detail="ML service response missing assessment payload")

    normalized_resume_uri = resume_uri.strip() if resume_uri and resume_uri.strip() else None

    row = Assessment(
        user_id=current_user.id,
        target_role=assessment.get("target_role", role),
        overall_score=float(assessment.get("overall_score", 0)),
        readiness_level=str(assessment.get("readiness_level", "Unknown")),
        source_type="resume",
        resume_filename=resume.filename,
        resume_sha256=sha256(content).hexdigest(),
        resume_uri=normalized_resume_uri,
        score_breakdown_json=json.dumps(assessment.get("score_breakdown", {})),
        missing_required_skills_json=json.dumps(assessment.get("missing_required_skills", [])),
        recommendations_json=json.dumps(assessment.get("recommendations", [])),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return _to_response(row)


@router.post("/from-profile", response_model=AssessmentResponse)
def create_assessment_from_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")

    candidate_skills = [segment.strip() for segment in profile.skills_csv.split(",") if segment.strip()]
    if not candidate_skills:
        raise HTTPException(status_code=400, detail="Profile has no skills. Update profile first.")

    client = MLServiceClient()
    try:
        assessment = client.assess_profile(
            target_role=profile.target_role,
            candidate_skills=candidate_skills,
            candidate_years=profile.candidate_years,
            projects_count=profile.projects_count,
            experience_type=profile.experience_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    row = Assessment(
        user_id=current_user.id,
        target_role=assessment.get("target_role", profile.target_role),
        overall_score=float(assessment.get("overall_score", 0)),
        readiness_level=str(assessment.get("readiness_level", "Unknown")),
        source_type="profile",
        score_breakdown_json=json.dumps(assessment.get("score_breakdown", {})),
        missing_required_skills_json=json.dumps(assessment.get("missing_required_skills", [])),
        recommendations_json=json.dumps(assessment.get("recommendations", [])),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return _to_response(row)


@router.get("/latest", response_model=AssessmentResponse | None)
def get_latest_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentResponse | None:
    row = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    if not row:
        return None

    return _to_response(row)


@router.get("/history", response_model=list[AssessmentHistoryItem])
def get_assessment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AssessmentHistoryItem]:
    rows = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        AssessmentHistoryItem(
            id=row.id,
            target_role=row.target_role,
            overall_score=row.overall_score,
            readiness_level=row.readiness_level,
            source_type=row.source_type,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/history/query", response_model=AssessmentHistoryPageResponse)
def get_assessment_history_query(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role_name: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
) -> AssessmentHistoryPageResponse:
    query = db.query(Assessment).filter(Assessment.user_id == current_user.id)

    if role_name and role_name.strip():
        query = query.filter(Assessment.target_role == role_name.strip())
    if source_type and source_type.strip():
        query = query.filter(Assessment.source_type == source_type.strip().lower())

    total = query.count()
    rows = query.order_by(Assessment.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        AssessmentHistoryItem(
            id=row.id,
            target_role=row.target_role,
            overall_score=row.overall_score,
            readiness_level=row.readiness_level,
            source_type=row.source_type,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return AssessmentHistoryPageResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


@router.get("/trend", response_model=AssessmentTrendResponse)
def get_assessment_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssessmentTrendResponse:
    rows = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.asc())
        .limit(100)
        .all()
    )

    points = [
        AssessmentTrendPoint(
            id=row.id,
            overall_score=row.overall_score,
            readiness_level=row.readiness_level,
            target_role=row.target_role,
            created_at=row.created_at,
        )
        for row in rows
    ]

    if len(points) < 2:
        return AssessmentTrendResponse(
            points=points,
            delta_from_previous=None,
            delta_from_first=None,
        )

    latest = points[-1].overall_score
    previous = points[-2].overall_score
    first = points[0].overall_score

    return AssessmentTrendResponse(
        points=points,
        delta_from_previous=round(latest - previous, 2),
        delta_from_first=round(latest - first, 2),
    )


@router.get("/trend/query", response_model=AssessmentTrendPageResponse)
def get_assessment_trend_query(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    role_name: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
) -> AssessmentTrendPageResponse:
    query = db.query(Assessment).filter(Assessment.user_id == current_user.id)

    if role_name and role_name.strip():
        query = query.filter(Assessment.target_role == role_name.strip())
    if source_type and source_type.strip():
        query = query.filter(Assessment.source_type == source_type.strip().lower())

    total = query.count()
    rows = query.order_by(Assessment.created_at.asc()).offset(offset).limit(limit).all()

    points = [
        AssessmentTrendPoint(
            id=row.id,
            overall_score=row.overall_score,
            readiness_level=row.readiness_level,
            target_role=row.target_role,
            created_at=row.created_at,
        )
        for row in rows
    ]

    if len(points) < 2:
        return AssessmentTrendPageResponse(
            items=points,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(points)) < total,
            delta_from_previous=None,
            delta_from_first=None,
        )

    latest = points[-1].overall_score
    previous = points[-2].overall_score
    first = points[0].overall_score

    return AssessmentTrendPageResponse(
        items=points,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(points)) < total,
        delta_from_previous=round(latest - previous, 2),
        delta_from_first=round(latest - first, 2),
    )


@router.get("/benchmark", response_model=AssessmentBenchmarkResponse)
def get_assessment_benchmark(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    role_name: str | None = Query(default=None),
) -> AssessmentBenchmarkResponse:
    latest = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No assessment found for user")

    compared_role = role_name.strip() if role_name and role_name.strip() else latest.target_role

    client = MLServiceClient()
    try:
        role_details = client.get_role_details(compared_role)
    except Exception as exc:
        detail = str(exc)
        if "404" in detail:
            raise HTTPException(status_code=404, detail=f"Unknown role '{compared_role}'") from exc
        raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    required_total = len(role_details.get("top_required_skills", []))
    missing_required = len(json.loads(latest.missing_required_skills_json))
    covered = max(required_total - missing_required, 0)
    coverage_pct = round((covered / required_total) * 100, 2) if required_total > 0 else 0.0

    experience_payload = role_details.get("experience", {})
    new_grad_friendly = experience_payload.get("new_grad_friendly_percentage")

    target_ready_score = 70.0
    return AssessmentBenchmarkResponse(
        compared_role=compared_role,
        latest_assessment_id=latest.id,
        latest_score=latest.overall_score,
        target_ready_score=target_ready_score,
        score_gap_to_ready=round(latest.overall_score - target_ready_score, 2),
        required_skills_total=required_total,
        missing_required_skills_count=missing_required,
        required_skill_coverage_pct=coverage_pct,
        market_new_grad_friendly_percentage=(
            float(new_grad_friendly) if new_grad_friendly is not None else None
        ),
        market_remote_percentage=float(role_details.get("remote_percentage", 0.0)),
    )
