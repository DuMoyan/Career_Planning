import asyncio
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.agents.planning_graph import PlanningGraph
from app.core.config import Settings
from app.core.errors import ConflictError
from app.core.security import hash_password
from app.domain.access import Role
from app.domain.plans import PlanStatus
from app.main import create_app
from app.repositories.ai_runs import InMemoryAIRunRepository
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.plans import InMemoryPlanRepository
from app.repositories.tasks import InMemoryTaskRepository, TaskStatus
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.schemas.planning import MilestoneDraft, PlanDraft, PlanningContext, PlanningGap, TaskDraft
from app.services.ai_runs import AIRunService
from app.services.auth import AuthService
from app.services.plans import PlanService


def plan(title: str = "完成编程作品") -> PlanDraft:
    return PlanDraft(
        milestones=[
            MilestoneDraft(
                title="完成作品集",
                due_date=date(2027, 6, 1),
                acceptance_criteria=["作品可运行并有说明文档"],
            )
        ],
        tasks=[
            TaskDraft(
                title=title,
                competency_code="programming",
                due_date=date(2027, 5, 1),
                weekly_hours=3,
                source_refs=["教学演示岗位数据"],
            )
        ],
        sources=["教学演示岗位数据"],
        unknowns=[],
        risks=["时间变化"],
        generation_mode="rules",
    )


def service() -> tuple[PlanService, InMemoryPlanRepository, InMemoryTaskRepository]:
    plans = InMemoryPlanRepository()
    tasks = InMemoryTaskRepository()
    return PlanService(plans, tasks), plans, tasks


async def test_concurrent_idempotent_activation_creates_one_version_and_task_set() -> None:
    subject, plans, tasks = service()
    student_id = uuid4()
    draft = await subject.create_draft(student_id, uuid4(), plan())

    results = await asyncio.gather(
        *(subject.activate(student_id, draft.id, "activate-1") for _ in range(50))
    )

    assert {result.id for result in results} == {draft.id}
    assert plans.versions[draft.id].status is PlanStatus.active
    assert len(await tasks.list_for_version(draft.id)) == 1
    assert len([item for item in plans.versions.values() if item.status is PlanStatus.active]) == 1


async def test_replan_archives_old_version_and_migrates_only_unfinished_tasks() -> None:
    subject, plans, tasks = service()
    student_id = uuid4()
    original = await subject.create_draft(student_id, uuid4(), plan("原任务"))
    await subject.activate(student_id, original.id, "activate-original")
    original_task = (await tasks.list_for_version(original.id))[0]
    original_task.status = TaskStatus.in_progress

    replacement = await subject.create_replan(student_id, original.id, uuid4(), plan("新任务"))
    preview = await subject.preview_replan(student_id, replacement.id)
    activated = await subject.activate_replan(
        student_id,
        replacement.id,
        {original_task.id: "continue"},
        "activate-replan",
    )

    assert preview[0]["task_id"] == original_task.id
    assert plans.versions[original.id].status is PlanStatus.archived
    assert activated.status is PlanStatus.active
    migrated = await tasks.list_for_version(replacement.id)
    assert any(item.source_task_id == original_task.id for item in migrated)
    assert (await tasks.list_for_version(original.id))[0].status is TaskStatus.in_progress


async def test_completed_tasks_remain_history_and_replace_cancel_choices_are_applied() -> None:
    subject, plans, tasks = service()
    student_id = uuid4()
    original = await subject.create_draft(student_id, uuid4(), plan())
    await subject.activate(student_id, original.id, "initial")
    old_task = (await tasks.list_for_version(original.id))[0]
    old_task.status = TaskStatus.completed
    replacement = await subject.create_replan(student_id, original.id, uuid4(), plan("替代任务"))

    await subject.activate_replan(
        student_id,
        replacement.id,
        {old_task.id: "replace"},
        "replacement",
    )

    assert all(
        item.source_task_id != old_task.id for item in await tasks.list_for_version(replacement.id)
    )
    assert (await tasks.list_for_version(original.id))[0].status is TaskStatus.completed
    assert [item.version for item in await subject.history(student_id)] == [2, 1]


async def test_same_goal_cannot_have_two_independently_active_plans() -> None:
    subject, _plans, _tasks = service()
    student_id = uuid4()
    goal_reference = str(uuid4())
    first = await subject.create_draft(
        student_id, uuid4(), plan("第一版"), goal_reference=goal_reference
    )
    second = await subject.create_draft(
        student_id, uuid4(), plan("第二版"), goal_reference=goal_reference
    )

    await subject.activate(student_id, first.id, "activate-first")

    assert first.career_plan_id == second.career_plan_id
    with pytest.raises(ConflictError, match="已有激活版本"):
        await subject.activate(student_id, second.id, "activate-second")


def test_plan_draft_activation_and_history_api() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="s" * 32,
    )
    student_id = uuid4()
    users = InMemoryUserRepository()
    users.add(
        UserRecord(
            id=student_id,
            identifier="20260001",
            password_hash=hash_password("Career!2026"),
            role=Role.student,
        )
    )
    audits = InMemoryAuditRepository()
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.ai_run_service = AIRunService(
        repository=InMemoryAIRunRepository(),
        graph=PlanningGraph(None),
        context_provider=lambda _student_id: PlanningContext(
            goal_deadline=date(2027, 6, 30),
            weekly_hours=3,
            gaps=[
                PlanningGap(
                    competency_code="programming",
                    status="developable_gap",
                    required_level=3,
                    current_level=2,
                    source="教学演示岗位数据",
                )
            ],
            input_references={"goal_id": "goal-1"},
        ),
        audits=audits,
    )
    app.state.plan_service = PlanService(InMemoryPlanRepository(), InMemoryTaskRepository())
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    run = client.post("/api/v1/plans/generations").json()

    draft = client.post("/api/v1/plans/drafts", json={"ai_run_id": run["id"]})
    activated = client.post(
        f"/api/v1/plans/versions/{draft.json()['id']}/activate",
        headers={"Idempotency-Key": "activate-api-1"},
    )
    repeated = client.post(
        f"/api/v1/plans/versions/{draft.json()['id']}/activate",
        headers={"Idempotency-Key": "activate-api-1"},
    )

    assert draft.status_code == 201
    assert activated.json()["status"] == "active"
    assert repeated.json()["id"] == activated.json()["id"]
    assert client.get("/api/v1/plans/history").json()[0]["version"] == 1
