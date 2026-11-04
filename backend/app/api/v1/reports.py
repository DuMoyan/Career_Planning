from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import current_access_context
from app.domain.access import AccessContext, Role, ensure_roles
from app.schemas.report import ReportResponseCreate, WeeklyReportCreate

router = APIRouter(prefix="/reports/weekly", tags=["周报复盘"])


def _json(report) -> dict:
    return {
        "id": report.id,
        "week_start": report.week_start,
        "metrics": {
            "task_count": report.metrics.task_count,
            "completed_count": report.metrics.completed_count,
            "completion_rate": report.metrics.completion_rate,
            "estimated_hours": report.metrics.estimated_hours,
            "actual_hours": report.metrics.actual_hours,
            "delayed_count": report.metrics.delayed_count,
            "needs_adjustment": report.metrics.needs_adjustment,
        },
        "advice": report.advice,
        "advice_mode": report.advice_mode,
        "response_action": report.response_action,
        "response_text": report.response_text,
        "replan_run_id": report.replan_run_id,
        "created_at": report.created_at,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: WeeklyReportCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    ensure_roles(context, {Role.student})
    return _json(
        await request.app.state.report_service.generate(context.user_id, payload.week_start)
    )


@router.post("/{report_id}/response")
async def respond_to_report(
    report_id: UUID,
    payload: ReportResponseCreate,
    request: Request,
    context: Annotated[AccessContext, Depends(current_access_context)],
) -> dict:
    return _json(
        await request.app.state.report_service.respond(
            context.user_id, report_id, payload.action, payload.text
        )
    )
