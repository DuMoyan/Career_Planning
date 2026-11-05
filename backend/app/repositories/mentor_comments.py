from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mentor_comment import MentorPlanComment
from app.services.mentor import MentorCommentRecord


class InMemoryMentorCommentRepository:
    def __init__(self) -> None:
        self.records: dict[UUID, MentorCommentRecord] = {}

    async def save(self, comment: MentorCommentRecord) -> None:
        self.records[comment.id] = comment

    async def list_version(self, version_id: UUID) -> list[MentorCommentRecord]:
        return [
            item for item in self.records.values() if item.plan_version_id == version_id
        ]


class SqlAlchemyMentorCommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, comment: MentorCommentRecord) -> None:
        self.session.add(
            MentorPlanComment(
                id=comment.id,
                mentor_id=comment.mentor_id,
                student_id=comment.student_id,
                plan_version_id=comment.plan_version_id,
                content=comment.content,
                created_at=comment.created_at,
            )
        )
        await self.session.commit()

    async def list_version(self, version_id: UUID) -> list[MentorCommentRecord]:
        models = list(
            (
                await self.session.scalars(
                    select(MentorPlanComment)
                    .where(MentorPlanComment.plan_version_id == version_id)
                    .order_by(MentorPlanComment.created_at)
                )
            ).all()
        )
        return [
            MentorCommentRecord(
                id=item.id,
                mentor_id=item.mentor_id,
                student_id=item.student_id,
                plan_version_id=item.plan_version_id,
                content=item.content,
                created_at=item.created_at,
            )
            for item in models
        ]
