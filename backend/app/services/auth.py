from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe

from app.core.config import Settings
from app.core.errors import (
    AccountLockedError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.core.security import create_access_token, verify_password
from app.repositories.audits import AuditEvent, AuditRepository
from app.repositories.users import RefreshSession, UserRecord, UserRepository
from app.schemas.auth import TokenPair


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        audits: AuditRepository,
        settings: Settings,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.users = users
        self.audits = audits
        self.settings = settings
        self.clock = clock or (lambda: datetime.now(UTC))

    async def login(self, identifier: str, password: str) -> TokenPair:
        now = self.clock()
        user = await self.users.get_by_identifier(identifier)
        if user is not None and user.locked_until is not None and user.locked_until > now:
            raise AccountLockedError()

        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            if user is not None and user.is_active:
                user.failed_login_count += 1
                if user.failed_login_count >= 5:
                    user.locked_until = now + timedelta(minutes=15)
                await self.users.save(user)
            raise InvalidCredentialsError()

        user.failed_login_count = 0
        user.locked_until = None
        await self.users.save(user)
        tokens = await self._issue_pair(user, now)
        await self.audits.append(
            AuditEvent(
                event_type="login_success",
                actor_id=user.id,
                target_type="user",
                target_id=str(user.id),
                result="success",
            )
        )
        return tokens

    async def refresh(self, refresh_token: str) -> TokenPair:
        now = self.clock()
        session = await self.users.consume_refresh_session(_digest(refresh_token), now)
        if session is None:
            raise InvalidRefreshTokenError()
        user = await self.users.get_by_id(session.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError()
        return await self._issue_pair(user, now)

    async def logout(self, refresh_token: str) -> None:
        await self.users.revoke_refresh_session(_digest(refresh_token))

    async def _issue_pair(self, user: UserRecord, now: datetime) -> TokenPair:
        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
            secret=self.settings.jwt_secret,
            expires_delta=timedelta(minutes=self.settings.jwt_access_minutes),
        )
        refresh_token = token_urlsafe(48)
        await self.users.save_refresh_session(
            RefreshSession(
                digest=_digest(refresh_token),
                user_id=user.id,
                expires_at=now + timedelta(days=7),
            )
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            role=user.role,
        )


def _digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
