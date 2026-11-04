from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.errors import UnauthorizedError
from app.domain.access import AccessContext, Role

_password_hash = PasswordHash.recommended()


class TokenExpiredError(UnauthorizedError):
    code = "TOKEN_EXPIRED"


class InvalidAccessTokenError(UnauthorizedError):
    code = "INVALID_TOKEN"


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return _password_hash.verify(password, encoded)


def create_access_token(
    *,
    user_id: UUID,
    role: Role,
    secret: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, *, secret: str) -> AccessContext:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise TokenExpiredError("访问令牌已过期") from exc
    except InvalidTokenError as exc:
        raise InvalidAccessTokenError("访问令牌无效") from exc

    if payload.get("type") != "access":
        raise InvalidAccessTokenError("令牌类型无效")
    try:
        return AccessContext(user_id=UUID(payload["sub"]), role=Role(payload["role"]))
    except (KeyError, ValueError, TypeError) as exc:
        raise InvalidAccessTokenError("访问令牌声明无效") from exc
