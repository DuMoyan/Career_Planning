from fastapi import APIRouter, Request, Response, status

from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["身份认证"])


def _service(request: Request) -> AuthService:
    return request.app.state.auth_service


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request) -> TokenPair:
    return await _service(request).login(payload.identifier, payload.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, request: Request) -> TokenPair:
    return await _service(request).refresh(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, request: Request) -> Response:
    await _service(request).logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
