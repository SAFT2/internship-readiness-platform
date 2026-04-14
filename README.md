# 🎯 AI-Powered Internship Readiness Evaluator

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-blue)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/Bekafi01/internship-readiness-platform/pulls)

> **A comprehensive ML-powered platform that evaluates student readiness for technical internships by analyzing resumes, identifying skill gaps, and providing personalized recommendations aligned with market demands.**

## 🎯 Overview

The **Internship Readiness Evaluator** helps students understand their preparedness for technical internships by:

- 📄 **Parsing resumes** to extract skills, projects, and experience
- 🔍 **Comparing against real market requirements** from thousands of internship postings
- 📊 **Generating a readiness score** (0-100) with detailed breakdown
- 🎯 **Identifying skill gaps** with prioritized recommendations
- 📈 **Providing learning pathways** tailored to target roles

### Problem Statement

Students often struggle to understand what skills they need for internships and how their current profile compares to market demands. This platform bridges that gap by providing data-driven insights and personalized guidance.

## Free-Tier Production Deployment

Recommended zero-cost stack:

- Frontend: Vercel (Hobby)
- Backend API: Render Web Service (Free)
- ML service: Render Web Service (Free)
- Database: Neon Postgres (Free)

### 1) Deploy ML service on Render

1. Create a new Web Service from your GitHub repo.
2. Set:
	- Root Directory: `ml-service`
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `cd src && uvicorn api:app --host 0.0.0.0 --port $PORT`
3. Deploy and confirm health: `https://<ml-service>.onrender.com/health`.

### 2) Create free Postgres on Neon

1. Create a Neon project.
2. Copy the SQLAlchemy-compatible connection string (`postgresql://...`).

### 3) Deploy backend API on Render

1. Create another Web Service from the same repo.
2. Set:
	- Root Directory: `backend`
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add environment variables:
	- `DATABASE_URL` = your Neon connection string
	- `JWT_SECRET_KEY` = long random secret
	- `ML_SERVICE_URL` = your ML Render URL
	- `CORS_ORIGINS` = `["https://<your-frontend>.vercel.app"]`
4. Deploy and confirm health: `https://<backend>.onrender.com/health`.

### 4) Deploy frontend on Vercel

1. Import the repo into Vercel.
2. Set project Root Directory to `frontend`.
3. Build config:
	- Install: `npm install`
	- Build: `npm run build`
	- Output: `dist`
4. Add env var:
	- `VITE_API_BASE_URL` = `https://<backend>.onrender.com`
5. Deploy.

### 5) Final wiring and smoke test

1. Add your Vercel domain to backend `CORS_ORIGINS`.
2. From browser, test:
	- frontend loads
	- register/login works
	- resume upload returns readiness response
	- dashboard/report endpoint works

### Free-tier behavior to expect

- Render free services spin down after inactivity (cold starts are normal).
- Keep request timeouts reasonable in the frontend for first-hit wakeups.
