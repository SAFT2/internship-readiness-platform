from fastapi import APIRouter

from app.api.routes import assessments, auth, dashboard, profile


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
