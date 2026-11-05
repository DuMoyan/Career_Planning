import inspect
from datetime import date, timedelta
from uuid import UUID, uuid4

from app.core.errors import ConflictError, ForbiddenError
from app.domain.reports import ReportCheckIn, ReportTask, aggregate_week
from app.repositories.reports import WeeklyReportRecord


class ReportService:
    def __init__(
        self,
        reports,
        tasks,
        plans,
        *,
        adviser=None,
        replan_callback=None,
        timezone: str = "Asia/Shanghai",
    ) -> None:
        self.reports = reports
        self.tasks = tasks
        self.plans = plans
        self.adviser = adviser
        self.replan_callback = replan_callback
        self.timezone = timezone

    async def generate(self, student_id: UUID, week_start: date) -> WeeklyReportRecord:
        existing = await self.reports.get_by_week(student_id, week_start)
        if existing:
            return existing
        week_end = week_start + timedelta(days=7)
        task_records = []
        for task in await self.tasks.list_student(student_id):
            if week_start <= task.due_date < week_end:
                task_records.append(task)
        report_tasks = [
            ReportTask(item.id, item.status, item.weekly_hours) for item in task_records
        ]
        report_checkins = [
            ReportCheckIn(item.task_id, item.actual_hours, item.created_at)
            for item in await self.tasks.list_student_checkins(student_id)
        ]
        metrics = aggregate_week(report_tasks, report_checkins, week_start, self.timezone)
        advice_mode = "rules"
        advice = self._rule_advice(metrics)
        if self.adviser:
            try:
                candidate = self.adviser(metrics)
                advice = await candidate if inspect.isawaitable(candidate) else candidate
                advice_mode = "model"
            except (TimeoutError, ValueError):
                pass
        report = WeeklyReportRecord(
            id=uuid4(),
            student_id=student_id,
            week_start=week_start,
            metrics=metrics,
            advice=advice,
            advice_mode=advice_mode,
        )
        await self.reports.save(report)
        return report

    async def respond(
        self, student_id: UUID, report_id: UUID, action: str, text: str | None
    ) -> WeeklyReportRecord:
        report = await self.reports.get(report_id)
        if report is None or report.student_id != student_id:
            raise ForbiddenError("周报不存在或无权访问")
        if action not in {"accept", "modify", "reject"}:
            raise ConflictError("反馈动作无效")
        if action == "modify" and not (text and text.strip()):
            raise ConflictError("修改建议时必须填写调整内容")
        report.response_action = action
        report.response_text = text.strip() if text else None
        if action in {"accept", "modify"} and self.replan_callback:
            result = self.replan_callback(student_id, report.response_text)
            report.replan_run_id = await result if inspect.isawaitable(result) else result
        await self.reports.save(report)
        return report

    @staticmethod
    def _rule_advice(metrics) -> str:
        if metrics.delayed_count:
            return "本周存在延期任务，建议调整下周任务量并重新确认截止日期。"
        if metrics.task_count == 0:
            return "本周暂无计划任务，可检查是否需要补充下一步行动。"
        return "继续保持当前节奏，并在下周复盘实际投入与预估差异。"
