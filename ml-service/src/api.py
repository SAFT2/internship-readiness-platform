from pathlib import Path
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from readiness_assessor import ReadinessAssessor
from resume_parser import ResumeParser


app = FastAPI(title="Internship Readiness ML Service", version="1.0.0")


class ProfileAssessmentRequest(BaseModel):
    target_role: str = Field(min_length=2)
    candidate_skills: list[str] = Field(default_factory=list)
    candidate_years: float = 0.0
    projects_count: int = 0
    experience_type: str = "none"
    project_quality_score: float | None = None
    project_relevance_score: float | None = None
    profile_path: str | None = None


def _save_upload_to_temp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "resume.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = upload.file.read()
        temp_file.write(content)
        return Path(temp_file.name)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/roles")
def list_roles(profile_path: str | None = None):
    try:
        assessor = ReadinessAssessor(profile_path=profile_path)
        roles = sorted(assessor.market_profile.keys())
        return {
            "roles": roles,
            "count": len(roles),
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to load roles: {exc}") from exc


@app.get("/roles/{role_name}")
def get_role_details(role_name: str, profile_path: str | None = None):
    try:
        assessor = ReadinessAssessor(profile_path=profile_path)
        role_data = assessor.market_profile.get(role_name)
        if not role_data:
            raise HTTPException(status_code=404, detail=f"Unknown role '{role_name}'")

        return {
            "role": role_name,
            "total_postings": int(role_data.get("total_postings", 0)),
            "top_required_skills": list(role_data.get("top_required_skills", []))[:15],
            "top_preferred_skills": list(role_data.get("top_preferred_skills", []))[:15],
            "required_skill_frequency": dict(role_data.get("required_skill_frequency", {})),
            "preferred_skill_frequency": dict(role_data.get("preferred_skill_frequency", {})),
            "experience": dict(role_data.get("experience", {})),
            "remote_percentage": float(role_data.get("remote_percentage", 0.0)),
            "top_locations": dict(role_data.get("top_locations", {})),
            "sample_job_titles": list(role_data.get("sample_job_titles", []))[:5],
        }
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to load role details: {exc}") from exc


@app.post("/parse-resume")
def parse_resume(
    resume: UploadFile = File(...),
    role: str | None = Form(default=None),
    profile_path: str | None = Form(default=None),
):
    if not resume.filename:
        raise HTTPException(status_code=400, detail="No resume file provided")

    if not resume.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_path = None
    try:
        temp_path = _save_upload_to_temp(resume)
        parser = ResumeParser(profile_path=profile_path)

        if role:
            result = parser.parse_and_assess(temp_path, role)
        else:
            result = parser.parse_resume(temp_path)

        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Resume parsing failed: {exc}") from exc
    finally:
        try:
            resume.file.close()
        except Exception:
            pass

        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass


@app.post("/assess-profile")
def assess_profile(payload: ProfileAssessmentRequest):
    try:
        assessor = ReadinessAssessor(profile_path=payload.profile_path)
        result = assessor.assess(
            target_role=payload.target_role,
            candidate_skills=payload.candidate_skills,
            candidate_years=payload.candidate_years,
            projects_count=payload.projects_count,
            experience_type=payload.experience_type,
            project_quality_score=payload.project_quality_score,
            project_relevance_score=payload.project_relevance_score,
        )
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Profile assessment failed: {exc}") from exc