# Backend Service

Main website backend for user auth, profile management, and assessment history.

## Stack

- FastAPI
- SQLAlchemy
- JWT auth
- SQLite (default for local dev; switch to PostgreSQL in production)

## What is implemented

- `GET /health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/profile/me`
- `PATCH /api/v1/profile/me`
- `POST /api/v1/assessments/from-resume` (forwards resume PDF + role to ML service)
- `POST /api/v1/assessments/from-profile` (scores using stored student profile)
- `GET /api/v1/assessments/roles`
- `GET /api/v1/assessments/roles/{role_name}`
- `GET /api/v1/assessments/latest`
- `GET /api/v1/assessments/history`
- `GET /api/v1/assessments/history/query` (pagination + filters)
- `GET /api/v1/assessments/trend`
- `GET /api/v1/assessments/trend/query` (pagination + filters)
- `GET /api/v1/assessments/benchmark`
- `GET /api/v1/dashboard/summary`
- `GET /api/v1/dashboard/trend` (chart-ready trend points)
- `GET /api/v1/dashboard/report.pdf` (backend-generated PDF summary report)

### Query examples

History with pagination/filtering:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
	"http://localhost:8000/api/v1/assessments/history/query?limit=20&offset=0&source_type=profile&role_name=ML%20Intern"
```

Trend with pagination/filtering:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
	"http://localhost:8000/api/v1/assessments/trend/query?limit=20&offset=0&source_type=profile"
```

Role benchmark vs market profile:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
	"http://localhost:8000/api/v1/assessments/benchmark?role_name=ML%20Intern"
```

Dashboard chart data:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
	"http://localhost:8000/api/v1/dashboard/trend?points=12&role_name=ML%20Intern"
```

### Resume metadata persistence

- `POST /api/v1/assessments/from-resume` now stores assessment source metadata.
- Optional form field: `resume_uri`.
- API responses for assessment endpoints include:
	- `source_type` (`resume` or `profile`)
	- `resume_metadata` (`filename`, `sha256`, `uri`) when source is resume

## Local setup

1. Create virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Copy env file and edit values:

```bash
cp backend/.env.example backend/.env
```

4. Run ML service first (port 8001):

```bash
cd ml-service/src
uvicorn api:app --reload --port 8001
```

5. Run backend service (port 8000):

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Database migrations (Alembic)

Apply migrations:

```bash
cd backend
.venv/bin/alembic upgrade head
```

If you already have tables created before Alembic adoption, run one-time stamp:

```bash
cd backend
.venv/bin/alembic stamp head
```

Create a new migration after model changes:

```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "describe change"
```

Rollback one revision:

```bash
cd backend
.venv/bin/alembic downgrade -1
```

6. Open docs:

- Backend Swagger: `http://localhost:8000/docs`
- ML Swagger: `http://localhost:8001/docs`

## Tests

Install dev dependencies:

```bash
pip install -r backend/requirements-dev.txt
```

Run tests:

```bash
cd backend
pytest -q
```

## Notes

- Database migrations are managed by Alembic in `backend/alembic`.
- For production, set `DATABASE_URL` to PostgreSQL and secure `JWT_SECRET_KEY`.
- Auth now supports refresh-token rotation via `/api/v1/auth/refresh`.
