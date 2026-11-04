from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from uuid import UUID

from app.domain.reports import WeeklyMetrics


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
