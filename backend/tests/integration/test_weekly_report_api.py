from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.core.errors import ForbiddenError
from app.domain.plans import PlanStatus
from app.domain.tasks import TaskStatus
from app.repositories.plans import InMemoryPlanRepository, PlanVersionRecord
from app.repositories.reports import InMemoryReportRepository
from app.repositories.tasks import GrowthTaskRecord, InMemoryTaskRepository, TaskCheckInRecord
from app.schemas.planning import PlanDraft
from app.services.reports import ReportService


async def build_service(adviser=None, replan=None):
    student_id = uuid4()
    plans = InMemoryPlanRepository()
    tasks = InMemoryTaskRepository()
    version = PlanVersionRecord(
        id=uuid4(),
        career_plan_id=uuid4(),
        student_id=student_id,
        ai_run_id=uuid4(),
        version=1,
        status=PlanStatus.active,
        snapshot=PlanDraft(
            milestones=[], tasks=[], sources=[], unknowns=[], risks=[], generation_mode="rules"
        ),
    )
    task = GrowthTaskRecord(
        id=uuid4(),
        student_id=student_id,
        plan_version_id=version.id,
        title="练习",
        competency_code="programming",
        due_date=date(2026, 11, 5),
        weekly_hours=3,
        source_refs=["岗位样本"],
        status=TaskStatus.delayed,
    )
    await plans.save(version)
    await tasks.save(task)
    await tasks.save_checkin(
        TaskCheckInRecord(
            id=uuid4(),
            student_id=student_id,
            task_id=task.id,
            content="练习",
            actual_hours=1,
            proof_url=None,
        ),
        "seed",
    )
    reports = InMemoryReportRepository()
    service = ReportService(reports, tasks, plans, adviser=adviser, replan_callback=replan)
    return service, reports, plans, student_id


async def test_generation_is_idempotent_and_advice_falls_back() -> None:
    async def unavailable(_metrics):
        raise TimeoutError

    service, reports, _, student_id = await build_service(adviser=unavailable)

    first = await service.generate(student_id, date(2026, 11, 2))
    second = await service.generate(student_id, date(2026, 11, 2))

    assert first.id == second.id
    assert len(reports.reports) == 1
    assert first.advice_mode == "rules"
    assert first.metrics.delayed_count == 1
    assert "调整" in first.advice


async def test_accept_starts_replan_without_changing_active_plan_and_feedback_is_saved() -> None:
    created_runs = []

    async def start_replan(student_id, feedback=None):
        run_id = uuid4()
        created_runs.append((student_id, feedback, run_id))
        return run_id

    service, _, plans, student_id = await build_service(replan=start_replan)
    report = await service.generate(student_id, date(2026, 11, 2))
    active_before = next(iter(plans.versions.values())).status

    accepted = await service.respond(student_id, report.id, "accept", None)

    assert accepted.response_action == "accept"
    assert accepted.replan_run_id == created_runs[0][2]
    assert next(iter(plans.versions.values())).status is active_before is PlanStatus.active

    modified = await service.respond(student_id, report.id, "modify", "保留课程任务，减少练习量")
    assert modified.response_text == "保留课程任务，减少练习量"
    assert modified.replan_run_id == created_runs[1][2]
    assert created_runs[1][1] == "保留课程任务，减少练习量"
    rejected = await service.respond(student_id, report.id, "reject", "本周是考试周")
    assert rejected.response_text == "本周是考试周"


async def test_report_ownership_is_enforced() -> None:
    service, _, _, student_id = await build_service()
    report = await service.generate(student_id, date(2026, 11, 2))

    with pytest.raises(ForbiddenError):
        await service.respond(uuid4(), report.id, "reject", None)


async def test_archived_cross_week_task_checkin_is_counted_by_occurrence_time() -> None:
    student_id = uuid4()
    plans = InMemoryPlanRepository()
    tasks = InMemoryTaskRepository()
    version = PlanVersionRecord(
        id=uuid4(),
        career_plan_id=uuid4(),
        student_id=student_id,
        ai_run_id=uuid4(),
        version=1,
        status=PlanStatus.archived,
        snapshot=PlanDraft(
            milestones=[], tasks=[], sources=[], unknowns=[], risks=[], generation_mode="rules"
        ),
    )
    task = GrowthTaskRecord(
        id=uuid4(),
        student_id=student_id,
        plan_version_id=version.id,
        title="跨周练习",
        competency_code="programming",
        due_date=date(2026, 11, 8),
        weekly_hours=2,
        source_refs=["岗位样本"],
        status=TaskStatus.completed,
    )
    await plans.save(version)
    await tasks.save(task)
    await tasks.save_checkin(
        TaskCheckInRecord(
            id=uuid4(),
            student_id=student_id,
            task_id=task.id,
            content="周一凌晨完成",
            actual_hours=2,
            proof_url=None,
            created_at=datetime(2026, 11, 8, 16, 30, tzinfo=UTC),
        ),
        "cross-week",
    )
    service = ReportService(InMemoryReportRepository(), tasks, plans)

    report = await service.generate(student_id, date(2026, 11, 9))

    assert report.metrics.actual_hours == 2
