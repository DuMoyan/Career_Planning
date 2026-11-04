from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles
from app.schemas.target import GoalCreate, TargetComparisonRequest

router = APIRouter(tags=["职业目标"])


def _target_json(service, target) -> dict:
    return {
        "id": target.id,
        "code": target.code,
        "name": target.name,
        "category": target.category,
        "description": target.description,
        "source": target.source,
        "verified_at": target.verified_at,
        "is_stale": service.is_stale(target.verified_at),
        "interests": target.interests,
        "values": target.values,
    }


@router.get("/targets")
async def list_targets(
    request: Request,
    _context: Annotated[AccessContext, Depends(current_access_context)],
    keyword: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=50),
) -> list[dict]:
    service = request.app.state.target_service
    return [_target_json(service, item) for item in await service.search(keyword, category)]


@router.post("/targets/compare")
async def compare_targets(
    payload: TargetComparisonRequest,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    service = request.app.state.target_service
    comparisons = await service.compare(context.user_id, payload.target_ids)
    return {
        "targets": [
            {
                **_target_json(service, item["target"]),
                "gaps": [
                    {
                        "requirement_id": gap.requirement_id,
                        "competency_code": gap.competency_code,
                        "required_level": gap.required_level,
                        "current_level": gap.current_level,
                        "status": gap.status,
                        "evidence_ids": gap.evidence_ids,
                        "requirement_source": gap.requirement_source,
                        "verified_at": gap.verified_at,
                    }
                    for gap in item["gaps"]
                ],
            }
            for item in comparisons
        ]
    }


@router.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    return _goal_json(await request.app.state.goal_service.create(context.user_id, payload))


@router.get("/goals")
async def list_goals(
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> list[dict]:
    ensure_roles(context, {Role.student})
    return [_goal_json(item) for item in await request.app.state.goal_service.list(context.user_id)]


def _goal_json(goal) -> dict:
    return {
        "id": goal.id,
        "target_id": goal.target_id,
        "deadline": goal.deadline,
        "weekly_hours": goal.weekly_hours,
        "constraints": goal.constraints,
        "primary": goal.primary,
        "created_at": goal.created_at,
    }
