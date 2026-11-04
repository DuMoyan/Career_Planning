from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import Settings
from app.core.errors import DomainError


def create_app(settings: Settings | None = None) -> FastAPI:
    application = FastAPI(title="AI智能体大学生职业生涯规划系统")
    application.state.settings = settings or Settings()
    application.include_router(api_router, prefix="/api/v1")

    @application.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    return application
