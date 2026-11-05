from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.reports import WeeklyMetrics
from app.models.report import WeeklyReport


@dataclass(slots=True)
class WeeklyReportRecord:
    id: UUID
    student_id: UUID
    week_start: date
    metrics: WeeklyMetrics
    advice: str
    advice_mode: str
    response_action: str | None = None
    response_text: str | None = None
    replan_run_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class InMemoryReportRepository:
    def __init__(self) -> None:
        self.reports: dict[UUID, WeeklyReportRecord] = {}
        self.by_week: dict[tuple[UUID, date], UUID] = {}

    async def get(self, report_id: UUID) -> WeeklyReportRecord | None:
        return self.reports.get(report_id)

    async def get_by_week(self, student_id: UUID, week_start: date) -> WeeklyReportRecord | None:
        report_id = self.by_week.get((student_id, week_start))
        return self.reports.get(report_id) if report_id else None

    async def save(self, report: WeeklyReportRecord) -> None:
        self.reports[report.id] = report
        self.by_week[(report.student_id, report.week_start)] = report.id


class SqlAlchemyReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, report_id: UUID) -> WeeklyReportRecord | None:
        return self._record(await self.session.get(WeeklyReport, report_id))

    async def get_by_week(
        self, student_id: UUID, week_start: date
    ) -> WeeklyReportRecord | None:
        model = await self.session.scalar(
            select(WeeklyReport).where(
                WeeklyReport.student_id == student_id,
                WeeklyReport.week_start == week_start,
            )
        )
        return self._record(model)

    async def save(self, report: WeeklyReportRecord) -> None:
        model = await self.session.get(WeeklyReport, report.id)
        if model is None:
            model = WeeklyReport(
                id=report.id,
                student_id=report.student_id,
                week_start=report.week_start,
            )
            self.session.add(model)
        model.metrics = {
            "week_start": report.metrics.week_start.isoformat(),
            "task_count": report.metrics.task_count,
            "completed_count": report.metrics.completed_count,
            "completion_rate": report.metrics.completion_rate,
            "estimated_hours": report.metrics.estimated_hours,
            "actual_hours": report.metrics.actual_hours,
            "delayed_count": report.metrics.delayed_count,
            "needs_adjustment": report.metrics.needs_adjustment,
        }
        model.advice = report.advice
        model.advice_mode = report.advice_mode
        model.response_action = report.response_action
        model.response_text = report.response_text
        model.replan_run_id = report.replan_run_id
        model.created_at = report.created_at
        await self.session.commit()

    @staticmethod
    def _record(model: WeeklyReport | None) -> WeeklyReportRecord | None:
        if model is None:
            return None
        metrics = dict(model.metrics)
        metrics["week_start"] = date.fromisoformat(metrics["week_start"])
        return WeeklyReportRecord(
            id=model.id,
            student_id=model.student_id,
            week_start=model.week_start,
            metrics=WeeklyMetrics(**metrics),
            advice=model.advice,
            advice_mode=model.advice_mode,
            response_action=model.response_action,
            response_text=model.response_text,
            replan_run_id=model.replan_run_id,
            created_at=model.created_at,
        )
