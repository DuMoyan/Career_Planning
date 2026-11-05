from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.bootstrap import configure_demo_services
from app.core.config import Settings
from app.core.errors import DomainError
from app.runtime import persistent_lifespan


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    application = FastAPI(
        title="AI智能体大学生职业生涯规划系统",
        lifespan=persistent_lifespan if resolved_settings.app_env == "production" else None,
    )
    application.state.settings = resolved_settings
    if resolved_settings.app_env != "production":
        configure_demo_services(application, application.state.settings)
    application.include_router(api_router, prefix="/api/v1")

    @application.middleware("http")
    async def close_request_session(request: Request, call_next):
        scope = getattr(request.app.state, "db_request_scope", None)
        token = scope.set(object()) if scope is not None else None
        try:
            return await call_next(request)
        finally:
            sessions = getattr(request.app.state, "db_sessions", None)
            if sessions is not None:
                await sessions.remove()
            if scope is not None and token is not None:
                scope.reset(token)

    @application.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, error: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    return application
