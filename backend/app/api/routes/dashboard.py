import json
from io import BytesIO
from textwrap import wrap
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.assessment import Assessment
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, DashboardTrendPoint, DashboardTrendResponse
from app.services.ml_client import MLServiceClient


router = APIRouter()


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf(
    *,
    user_email: str,
    target_role: str,
    latest_score: str,
    readiness_level: str,
    total_assessments: int,
    benchmark_line: str,
    missing_skills: list[str],
    recommendations: list[str],
    trend_points: list[tuple[str, float]],
) -> bytes:
    content_commands = ["BT"]

    # Header block
    content_commands.append("/F2 18 Tf")
    content_commands.append("44 760 Td")
    content_commands.append("14 TL")
    content_commands.append("(InternReady AI Readiness Report) Tj")
    content_commands.append("/F1 10 Tf")
    content_commands.append("0 -22 Td")
    content_commands.append(f"(User: {_escape_pdf_text(user_email)}) Tj")
    content_commands.append("T*")
    content_commands.append(f"(Target Role: {_escape_pdf_text(target_role)}) Tj")
    content_commands.append("T*")
    content_commands.append(f"(Latest Score: {_escape_pdf_text(latest_score)}) Tj")
    content_commands.append("T*")
    content_commands.append(f"(Readiness Level: {_escape_pdf_text(readiness_level)}) Tj")
    content_commands.append("T*")
    content_commands.append(f"(Total Assessments: {total_assessments}) Tj")
    content_commands.append("T*")
    content_commands.append(f"({_escape_pdf_text(benchmark_line)}) Tj")

    # Missing skills section
    content_commands.append("/F2 12 Tf")
    content_commands.append("0 -20 Td")
    content_commands.append("(Top Missing Skills) Tj")
    content_commands.append("/F1 10 Tf")
    for skill in (missing_skills or ["No major missing skills detected"]):
        content_commands.append("T*")
        content_commands.append(f"(- {_escape_pdf_text(skill)}) Tj")

    # Recommendations section
    content_commands.append("/F2 12 Tf")
    content_commands.append("0 -20 Td")
    content_commands.append("(Top Recommendations) Tj")
    content_commands.append("/F1 10 Tf")
    for item in (recommendations or ["No recommendations available yet"]):
        wrapped = wrap(item, width=88)
        if not wrapped:
            continue
        content_commands.append("T*")
        content_commands.append(f"(- {_escape_pdf_text(wrapped[0])}) Tj")
        for continuation in wrapped[1:]:
            content_commands.append("T*")
            content_commands.append(f"(  {_escape_pdf_text(continuation)}) Tj")

    # Trend section
    content_commands.append("/F2 12 Tf")
    content_commands.append("0 -20 Td")
    content_commands.append("(Trend Points) Tj")
    content_commands.append("/F1 10 Tf")
    for label, score in (trend_points or [("No trend data", 0.0)]):
        row = f"{label}: {round(score, 2)}" if label != "No trend data" else label
        content_commands.append("T*")
        content_commands.append(f"(- {_escape_pdf_text(row)}) Tj")

    content_commands.append("/F1 9 Tf")
    content_commands.append("0 -24 Td")
    content_commands.append("(Note: Compatibility mode report generated without external PDF/chart libraries.) Tj")
    content_commands.append("ET")
    stream_text = "\n".join(content_commands)
    stream_bytes = stream_text.encode("latin-1", errors="replace")

    objects: list[bytes] = []
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    )
    objects.append(b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj\n")
    objects.append(
        f"6 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )

    # Update page object to include both fonts and new content object ref
    objects[2] = (
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>\n"
        b"endobj\n"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


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
    normalized_role_name = role_name.strip() if isinstance(role_name, str) and role_name.strip() else None
    if normalized_role_name:
        query = query.filter(Assessment.target_role == normalized_role_name)

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


@router.get("/report.pdf")
def download_dashboard_report_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    points: int = Query(default=10, ge=1, le=30),
) -> StreamingResponse:
    summary = get_dashboard_summary(current_user=current_user, db=db)

    latest = (
        db.query(Assessment)
        .filter(Assessment.user_id == current_user.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )

    benchmark_line = "Benchmark: unavailable"
    if latest and summary.target_role:
        try:
            role_details = MLServiceClient().get_role_details(summary.target_role)
            required_total = len(role_details.get("top_required_skills", []))
            missing_required = len(json.loads(latest.missing_required_skills_json))
            covered = max(required_total - missing_required, 0)
            coverage_pct = round((covered / required_total) * 100, 2) if required_total > 0 else 0.0
            benchmark_line = f"Benchmark coverage: {coverage_pct}% ({covered}/{required_total} required skills)"
        except Exception:
            benchmark_line = "Benchmark: unavailable"

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        trend = get_dashboard_trend(current_user=current_user, db=db, points=points, role_name=None)
        fallback_pdf = _build_simple_pdf(
            user_email=current_user.email,
            target_role=summary.target_role or "Not set",
            latest_score=str(summary.latest_score if summary.latest_score is not None else "N/A"),
            readiness_level=summary.readiness_level or "N/A",
            total_assessments=summary.total_assessments,
            benchmark_line=benchmark_line,
            missing_skills=summary.missing_skills_top5 or [],
            recommendations=summary.recommendations_top3 or [],
            trend_points=[(point.label, point.score) for point in trend.points],
        )
        fallback_headers = {"Content-Disposition": 'attachment; filename="internready-report.pdf"'}
        return StreamingResponse(BytesIO(fallback_pdf), media_type="application/pdf", headers=fallback_headers)

    pdf_buffer = BytesIO()
    page_width, page_height = letter
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)

    y = page_height - 48
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(44, y, "InternReady AI Readiness Report")

    y -= 20
    pdf.setFont("Helvetica", 10)
    pdf.drawString(44, y, f"Generated for: {current_user.email}")
    y -= 14
    pdf.drawString(44, y, f"Target Role: {summary.target_role or 'Not set'}")
    y -= 14
    pdf.drawString(44, y, f"Latest Score: {summary.latest_score if summary.latest_score is not None else 'N/A'}")
    y -= 14
    pdf.drawString(44, y, f"Readiness Level: {summary.readiness_level or 'N/A'}")
    y -= 14
    pdf.drawString(44, y, f"Total Assessments: {summary.total_assessments}")
    y -= 14
    pdf.drawString(44, y, benchmark_line)

    y -= 18
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(44, y, "Top Missing Skills")
    y -= 14
    pdf.setFont("Helvetica", 10)
    missing_skills = summary.missing_skills_top5 or []
    if not missing_skills:
        pdf.drawString(52, y, "- No major missing skills detected")
        y -= 12
    for skill in missing_skills:
        pdf.drawString(52, y, f"- {skill}")
        y -= 12

    y -= 6
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(44, y, "Top Recommendations")
    y -= 14
    pdf.setFont("Helvetica", 10)
    recommendations = summary.recommendations_top3 or []
    if not recommendations:
        pdf.drawString(52, y, "- No recommendations available yet")
        y -= 12
    for recommendation in recommendations:
        lines = wrap(recommendation, width=90)
        if not lines:
            continue
        pdf.drawString(52, y, f"- {lines[0]}")
        y -= 12
        for extra_line in lines[1:]:
            pdf.drawString(66, y, extra_line)
            y -= 12

    if y < 96:
        pdf.showPage()
        y = page_height - 60

    pdf.showPage()
    pdf.save()
    pdf_buffer.seek(0)

    filename = f"internready-report-{(summary.target_role or 'general').lower().replace(' ', '-')}.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
