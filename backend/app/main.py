from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    application = FastAPI(title="AI智能体大学生职业生涯规划系统")
    application.state.settings = settings or Settings()
    application.include_router(api_router, prefix="/api/v1")
    return application
