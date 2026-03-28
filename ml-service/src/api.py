from pathlib import Path
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from resume_parser import ResumeParser


app = FastAPI(title="Internship Readiness ML Service", version="1.0.0")


def _save_upload_to_temp(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "resume.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = upload.file.read()
        temp_file.write(content)
        return Path(temp_file.name)


@app.get("/health")
def health_check():
    return {"status": "ok"}


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