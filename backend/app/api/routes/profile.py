from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.profile import ProfileOut, ProfileUpdate


router = APIRouter()


def _skills_to_csv(skills: list[str]) -> str:
    cleaned = [skill.strip().lower() for skill in skills if str(skill).strip()]
    return ",".join(sorted(set(cleaned)))


def _csv_to_skills(skills_csv: str) -> list[str]:
    if not skills_csv:
        return []
    return [segment.strip() for segment in skills_csv.split(",") if segment.strip()]


@router.get("/me", response_model=ProfileOut)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ProfileOut:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()

    if not profile:
        return ProfileOut(
            target_role="ML Intern",
            skills=[],
            projects_count=0,
            candidate_years=0.0,
            experience_type="none",
        )

    return ProfileOut(
        target_role=profile.target_role,
        skills=_csv_to_skills(profile.skills_csv),
        projects_count=profile.projects_count,
        candidate_years=profile.candidate_years,
        experience_type=profile.experience_type,
    )


@router.patch("/me", response_model=ProfileOut)
def upsert_my_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()

    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)

    profile.target_role = payload.target_role.strip()
    profile.skills_csv = _skills_to_csv(payload.skills)
    profile.projects_count = payload.projects_count
    profile.candidate_years = payload.candidate_years
    profile.experience_type = payload.experience_type.strip().lower()

    db.commit()
    db.refresh(profile)

    return ProfileOut(
        target_role=profile.target_role,
        skills=_csv_to_skills(profile.skills_csv),
        projects_count=profile.projects_count,
        candidate_years=profile.candidate_years,
        experience_type=profile.experience_type,
    )
