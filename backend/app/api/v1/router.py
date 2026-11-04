from fastapi import APIRouter

from app.api.v1.ai_runs import router as ai_runs_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.competencies import router as competencies_router
from app.api.v1.consents import router as consents_router
from app.api.v1.health import router as health_router
from app.api.v1.plans import router as plans_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.targets import router as targets_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(profiles_router)
api_router.include_router(consents_router)
api_router.include_router(assessments_router)
api_router.include_router(resumes_router)
api_router.include_router(competencies_router)
api_router.include_router(targets_router)
api_router.include_router(ai_runs_router)
api_router.include_router(plans_router)
