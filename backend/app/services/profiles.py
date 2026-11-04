from uuid import UUID

from app.core.errors import ForbiddenError
from app.domain.access import AccessContext, Role
from app.repositories.profiles import ProfileRepository, StudentProfileRecord
from app.schemas.profile import ProfileUpdate


class ProfileService:
    def __init__(self, repository: ProfileRepository) -> None:
        self.repository = repository

    async def get(self, context: AccessContext, student_id: UUID) -> StudentProfileRecord:
        if context.role is Role.student and context.user_id != student_id:
            raise ForbiddenError("只能访问本人的学生档案")
        profile = await self.repository.get(student_id)
        return profile or StudentProfileRecord(student_id=student_id)

    async def update_own(
        self, context: AccessContext, payload: ProfileUpdate
    ) -> StudentProfileRecord:
        if context.role is not Role.student:
            raise ForbiddenError("只有学生可以修改本人档案")
        profile = StudentProfileRecord(student_id=context.user_id, **payload.model_dump())
        await self.repository.save(profile)
        return profile

