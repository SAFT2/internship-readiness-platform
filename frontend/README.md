# Frontend (Vite + React + TypeScript)

This frontend is wired to the internship-readiness backend.

## Routes

- `/` Home
- `/auth` Login/Register
- `/upload` Resume assessment upload
- `/dashboard` Readiness summary + trend chart
- `/history` Assessment history
- `/profile` Candidate profile update

## API Base URL

Set optional env var in `frontend/.env`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8100
```

If not set, it defaults to `http://127.0.0.1:8100`.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://127.0.0.1:5173`).

## Build

```bash
cd frontend
npm run build
```

## Deploy (Vercel Hobby)

1. Import repository in Vercel.
2. Set Root Directory to `frontend`.
3. Build settings:
	- Install Command: `npm install`
	- Build Command: `npm run build`
	- Output Directory: `dist`
4. Add env variable:

```bash
VITE_API_BASE_URL=https://your-backend-service.onrender.com
```

`frontend/vercel.json` includes SPA rewrites so route refresh works for dashboard/history/profile URLs.
