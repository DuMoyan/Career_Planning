from datetime import UTC, date, datetime
from uuid import uuid4

from app.domain.reports import ReportCheckIn, ReportTask, aggregate_week
from app.domain.tasks import TaskStatus


def test_weekly_metrics_include_completion_hours_and_delayed_prompt() -> None:
    first, second = uuid4(), uuid4()
    tasks = [
        ReportTask(first, TaskStatus.completed, 3),
        ReportTask(second, TaskStatus.delayed, 2),
    ]
    checkins = [
        ReportCheckIn(first, 2.5, datetime(2026, 11, 4, 12, tzinfo=UTC)),
        ReportCheckIn(second, 1, datetime(2026, 11, 5, 12, tzinfo=UTC)),
    ]

    metrics = aggregate_week(tasks, checkins, date(2026, 11, 2), "Asia/Shanghai")

    assert metrics.task_count == 2
    assert metrics.completed_count == 1
    assert metrics.completion_rate == 50
    assert metrics.estimated_hours == 5
    assert metrics.actual_hours == 3.5
    assert metrics.needs_adjustment is True


def test_zero_task_week_is_defined_without_division_error() -> None:
    metrics = aggregate_week([], [], date(2026, 11, 2), "Asia/Shanghai")

    assert metrics.task_count == 0
    assert metrics.completion_rate == 0
    assert metrics.actual_hours == 0
    assert metrics.needs_adjustment is False


def test_shanghai_sunday_2359_included_but_next_monday_0000_excluded() -> None:
    task_id = uuid4()
    tasks = [ReportTask(task_id, TaskStatus.in_progress, 1)]
    # 上海周日 23:59 = UTC 15:59；下周一 00:00 = UTC 16:00。
    checkins = [
        ReportCheckIn(task_id, 1, datetime(2026, 11, 8, 15, 59, tzinfo=UTC)),
        ReportCheckIn(task_id, 4, datetime(2026, 11, 8, 16, 0, tzinfo=UTC)),
    ]

    metrics = aggregate_week(tasks, checkins, date(2026, 11, 2), "Asia/Shanghai")

    assert metrics.actual_hours == 1
