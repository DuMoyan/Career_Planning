from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.access import Role
from app.models.user import RefreshToken, User


@dataclass(slots=True)
class UserRecord:
    id: UUID
    identifier: str
    password_hash: str
    role: Role
    is_active: bool = True
    failed_login_count: int = 0
    locked_until: datetime | None = None


@dataclass(slots=True)
class RefreshSession:
    digest: str
    user_id: UUID
    expires_at: datetime
    revoked: bool = False


class UserRepository(Protocol):
    async def get_by_identifier(self, identifier: str) -> UserRecord | None: ...
    async def get_by_id(self, user_id: UUID) -> UserRecord | None: ...
    async def save(self, user: UserRecord) -> None: ...
    async def save_refresh_session(self, session: RefreshSession) -> None: ...
    async def consume_refresh_session(
        self, digest: str, now: datetime
    ) -> RefreshSession | None: ...
    async def revoke_refresh_session(self, digest: str) -> None: ...


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users_by_id: dict[UUID, UserRecord] = {}
        self._users_by_identifier: dict[str, UserRecord] = {}
        self._refresh_sessions: dict[str, RefreshSession] = {}

    def add(self, user: UserRecord) -> None:
        self._users_by_id[user.id] = user
        self._users_by_identifier[user.identifier] = user

    async def get_by_identifier(self, identifier: str) -> UserRecord | None:
        return self._users_by_identifier.get(identifier)

    async def get_by_id(self, user_id: UUID) -> UserRecord | None:
        return self._users_by_id.get(user_id)

    async def save(self, user: UserRecord) -> None:
        self.add(user)

    async def save_refresh_session(self, session: RefreshSession) -> None:
        self._refresh_sessions[session.digest] = session

    async def consume_refresh_session(self, digest: str, now: datetime) -> RefreshSession | None:
        session = self._refresh_sessions.get(digest)
        if session is None or session.revoked or session.expires_at <= now:
            return None
        session.revoked = True
        return session

    async def revoke_refresh_session(self, digest: str) -> None:
        session = self._refresh_sessions.get(digest)
        if session is not None:
            session.revoked = True


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_identifier(self, identifier: str) -> UserRecord | None:
        model = await self.session.scalar(select(User).where(User.identifier == identifier))
        return _to_record(model)

    async def get_by_id(self, user_id: UUID) -> UserRecord | None:
        return _to_record(await self.session.get(User, user_id))

    async def save(self, user: UserRecord) -> None:
        model = await self.session.get(User, user.id)
        if model is None:
            model = User(id=user.id, identifier=user.identifier)
            self.session.add(model)
        model.password_hash = user.password_hash
        model.role = user.role
        model.is_active = user.is_active
        model.failed_login_count = user.failed_login_count
        model.locked_until = user.locked_until
        await self.session.commit()

    async def save_refresh_session(self, session: RefreshSession) -> None:
        self.session.add(
            RefreshToken(
                digest=session.digest,
                user_id=session.user_id,
                expires_at=session.expires_at,
                revoked=session.revoked,
            )
        )
        await self.session.commit()

    async def consume_refresh_session(self, digest: str, now: datetime) -> RefreshSession | None:
        model = await self.session.get(RefreshToken, digest)
        if model is None or model.revoked or model.expires_at <= now:
            return None
        model.revoked = True
        await self.session.commit()
        return RefreshSession(
            digest=model.digest,
            user_id=model.user_id,
            expires_at=model.expires_at,
            revoked=True,
        )

    async def revoke_refresh_session(self, digest: str) -> None:
        model = await self.session.get(RefreshToken, digest)
        if model is not None and not model.revoked:
            model.revoked = True
            await self.session.commit()


def _to_record(model: User | None) -> UserRecord | None:
    if model is None:
        return None
    return UserRecord(
        id=model.id,
        identifier=model.identifier,
        password_hash=model.password_hash,
        role=model.role,
        is_active=model.is_active,
        failed_login_count=model.failed_login_count,
        locked_until=model.locked_until,
    )
