from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.tasks import TaskStatus


@dataclass(frozen=True, slots=True)
class ReportTask:
    id: UUID
    status: TaskStatus
    estimated_hours: float


@dataclass(frozen=True, slots=True)
class ReportCheckIn:
    task_id: UUID
    actual_hours: float
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class WeeklyMetrics:
    week_start: date
    task_count: int
    completed_count: int
    completion_rate: float
    estimated_hours: float
    actual_hours: float
    delayed_count: int
    needs_adjustment: bool


def aggregate_week(
    tasks: list[ReportTask],
    checkins: list[ReportCheckIn],
    week_start: date,
    timezone_name: str,
) -> WeeklyMetrics:
    try:
        zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name != "Asia/Shanghai":
            raise
        zone = timezone(timedelta(hours=8), name="Asia/Shanghai")
    start = datetime.combine(week_start, time.min, tzinfo=zone)
    end = start + timedelta(days=7)
    actual = sum(
        item.actual_hours
        for item in checkins
        if start <= item.occurred_at.astimezone(zone) < end
    )
    completed = sum(task.status is TaskStatus.completed for task in tasks)
    delayed = sum(task.status is TaskStatus.delayed for task in tasks)
    count = len(tasks)
    return WeeklyMetrics(
        week_start=week_start,
        task_count=count,
        completed_count=completed,
        completion_rate=round(completed / count * 100, 2) if count else 0,
        estimated_hours=round(sum(task.estimated_hours for task in tasks), 2),
        actual_hours=round(actual, 2),
        delayed_count=delayed,
        needs_adjustment=delayed > 0,
    )
