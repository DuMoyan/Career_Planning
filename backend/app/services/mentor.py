from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.errors import ForbiddenError
from app.domain.access import Role
from app.domain.grants import GrantPolicy, GrantScope


@dataclass(frozen=True, slots=True)
class MentorCommentRecord:
    id: UUID
    mentor_id: UUID
    student_id: UUID
    plan_version_id: UUID
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class MentorService:
    def __init__(self, grants, plans) -> None:
        self.grants = grants
        self.plans = plans
        self.comments: dict[UUID, MentorCommentRecord] = {}

    async def list_students(self, mentor_id: UUID) -> list[dict]:
        now = datetime.now(UTC)
        return [
            {
                "student_id": grant.student_id,
                "scopes": sorted(scope.value for scope in grant.scopes),
                "expires_at": grant.expires_at,
            }
            for grant in self.grants.records.values()
            if grant.mentor_id == mentor_id and grant.revoked_at is None and grant.expires_at > now
        ]

    async def detail(self, mentor_id: UUID, student_id: UUID) -> dict:
        await self._require(mentor_id, student_id, GrantScope.plan_progress)
        versions = [item for item in await self.plans.list_student(student_id)]
        return {
            "student_id": student_id,
            "plan_versions": [
                {
                    "id": item.id,
                    "version": item.version,
                    "status": item.status,
                    "sources": item.snapshot.sources,
                }
                for item in versions
            ],
        }

    async def add_comment(
        self, mentor_id: UUID, version_id: UUID, content: str
    ) -> MentorCommentRecord:
        version = await self.plans.get(version_id)
        if version is None:
            raise ForbiddenError("计划版本不存在或无权访问")
        await self._require(mentor_id, version.student_id, GrantScope.plan_progress)
        comment = MentorCommentRecord(
            uuid4(), mentor_id, version.student_id, version.id, content.strip()
        )
        self.comments[comment.id] = comment
        return comment

    async def list_comments(self, actor_id: UUID, role: Role, version_id: UUID):
        version = await self.plans.get(version_id)
        if version is None:
            raise ForbiddenError("计划版本不存在或无权访问")
        if role is Role.student:
            if version.student_id != actor_id:
                raise ForbiddenError("无权查看该计划评论")
        elif role is Role.mentor:
            await self._require(actor_id, version.student_id, GrantScope.plan_progress)
        else:
            raise ForbiddenError("当前账号无权查看学生评论")
        return [item for item in self.comments.values() if item.plan_version_id == version_id]

    async def _require(self, mentor_id: UUID, student_id: UUID, scope: GrantScope) -> None:
        grant = await self.grants.find_active(mentor_id, student_id)
        if not GrantPolicy.can_read(grant, scope, datetime.now(UTC)):
            raise ForbiddenError("导师授权不存在、已过期或已撤销")
