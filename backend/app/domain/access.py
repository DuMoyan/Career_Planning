from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from app.core.errors import ForbiddenError


class Role(StrEnum):
    student = "student"
    mentor = "mentor"
    admin = "admin"


@dataclass(frozen=True, slots=True)
class AccessContext:
    user_id: UUID
    role: Role


def ensure_roles(context: AccessContext, allowed_roles: set[Role]) -> None:
    if context.role not in allowed_roles:
        raise ForbiddenError("当前账号无权执行此操作")

