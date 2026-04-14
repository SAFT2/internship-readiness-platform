# ML Service

This service builds internship market intelligence from cleaned postings and evaluates candidate readiness against target internship roles.

## What it includes

- `src/data_cleaning.py`: Cleans and normalizes raw internship data.
- `src/market_analyzer.py`: Builds `data/market_profile.json` and `data/processed/skill_role_matrix.csv`.
- `src/readiness_assessor.py`: Scores a candidate profile (0–100) against a target role.
- `src/readiness_model.py`: Trains a readiness-level classifier from engineered features.
- `src/resume_parser.py`: Parses uploaded resume PDFs into structured candidate profiles and can run readiness assessment.
- `src/api.py`: FastAPI app for resume upload parsing and optional readiness scoring.
- `src/test_resume_parsing.py`: Batch test parser on a directory of PDF resumes.
- `src/build_student_features.py`: Builds feature vectors per student profile for training/inference.
- `src/generate_synthetic_training_data.py`: Creates synthetic labeled training data.

## Prerequisites

- Python 3.9+
- Project virtual environment activated

## Generate market profile

Run from workspace root:

```powershell
python ml-service/src/market_analyzer.py
```

Outputs:

- `ml-service/data/market_profile.json`
- `ml-service/data/processed/skill_role_matrix.csv`

## Run readiness assessment

Example:

```powershell
python ml-service/src/readiness_assessor.py --role "ML Intern" --skills "python,pytorch,sql,git" --years 0 --projects 2 --experience-type research
```

Output is JSON with:

- Overall readiness score and fit band
- Score breakdown (required skills, preferred skills, experience)
- Matched and missing skills
- Prioritized recommendations

### Scoring design (plan-aligned)

- Skills: `50` points (`40` required + `10` preferred)
- Projects: `30` points
- Experience: `20` points

Readiness levels:

- `0-44` → Not Ready
- `45-69` → Developing
- `70-84` → Ready
- `85-100` → Highly Ready

## Train readiness classification model

Expected dataset columns:

- `skill_score`, `project_score`, `experience_score`, `num_skills`, `label`

Command:

```powershell
python ml-service/src/readiness_model.py --dataset path/to/student_training_data.csv
```

Model output default:

- `ml-service/data/models/readiness_model.pkl`

## Resume parsing (PDF upload flow)

Install parser dependency:

```powershell
pip install pypdf
```

Parse resume only:

```powershell
python ml-service/src/resume_parser.py --resume path/to/resume.pdf
```

Parse + assess against a target role:

```powershell
python ml-service/src/resume_parser.py --resume path/to/resume.pdf --role "ML Intern"
```

Structured output includes:

- Extracted contact info (`email`, `phone`)
- Extracted `skills`
- Estimated `projects_count`
- Inferred `experience_type` and `candidate_years`
- Optional readiness assessment result

Batch test parsing across resume samples:

```powershell
python ml-service/src/test_resume_parsing.py --input-dir path/to/resume_pdfs --role "ML Intern"
```

## Feature engineering

Input profile schema (`CSV` or `JSON`):

- `target_role`
- `skills` (comma-separated string or JSON list)
- `projects_count`
- `candidate_years`
- `experience_type`
- `label` (optional, for supervised training)

Build features:

```powershell
python ml-service/src/build_student_features.py --input path/to/student_profiles.csv --output ml-service/data/processed/student_features.csv
```

## Synthetic training data 

```powershell
python ml-service/src/generate_synthetic_training_data.py --size 1000
```

Then train model:

```powershell
python ml-service/src/readiness_model.py --dataset ml-service/data/processed/synthetic_training_data.csv
```

## Run ML-service API

Install API dependencies:

```powershell
pip install fastapi uvicorn python-multipart pypdf
```

Run from `ml-service/src`:

```powershell
uvicorn api:app --reload --port 8001
```

Endpoints:

- `GET /health`
- `POST /parse-resume`
  - Form fields:
    - `resume` (PDF file, required)
    - `role` (optional, e.g. `ML Intern`)
    - `profile_path` (optional path to `market_profile.json`)

## Deploy (Render Free)

Service settings:

- Root Directory: `ml-service`
- Build Command: `pip install -r requirements.txt`
- Start Command: `cd src && uvicorn api:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

After deploy, copy the public URL and set backend `ML_SERVICE_URL` to:

```bash
https://<your-ml-service>.onrender.com
```

## Scraping notes

Run:

```powershell
python ml-service/src/scrapers/run_scrapers.py
```

Output:

- `ml-service/data/raw/linkedin_internships.csv`
