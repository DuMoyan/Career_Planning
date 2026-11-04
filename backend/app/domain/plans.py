from dataclasses import dataclass, replace
from enum import StrEnum
from uuid import UUID

from app.core.errors import ConflictError


class PlanStatus(StrEnum):
    draft = "draft"
    active = "active"
    archived = "archived"
    discarded = "discarded"


@dataclass(frozen=True, slots=True)
class PlanVersionState:
    id: UUID
    career_plan_id: UUID
    version: int
    status: PlanStatus


def ensure_editable(version: PlanVersionState) -> None:
    if version.status is not PlanStatus.draft:
        raise ConflictError("仅草稿计划可以编辑")


def activate_version(
    version: PlanVersionState, siblings: list[PlanVersionState]
) -> PlanVersionState:
    ensure_editable(version)
    if any(
        item.career_plan_id == version.career_plan_id and item.status is PlanStatus.active
        for item in siblings
    ):
        raise ConflictError("当前职业计划已有激活版本")
    return replace(version, status=PlanStatus.active)
