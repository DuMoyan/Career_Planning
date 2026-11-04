from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.domain.access import AccessContext

_bearer = HTTPBearer(auto_error=False)


async def current_access_context(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> AccessContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("请先登录")
    return decode_access_token(
        credentials.credentials,
        secret=request.app.state.settings.jwt_secret,
    )
