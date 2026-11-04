import asyncio
from datetime import date
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import ConflictError, ForbiddenError
from app.core.security import hash_password
from app.domain.access import Role
from app.domain.plans import PlanStatus
from app.domain.tasks import TaskStatus
from app.main import create_app
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.plans import InMemoryPlanRepository, PlanVersionRecord
from app.repositories.tasks import GrowthTaskRecord, InMemoryTaskRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.schemas.planning import PlanDraft
from app.services.auth import AuthService
from app.services.tasks import TaskService


async def setup_task(*, plan_status: PlanStatus = PlanStatus.active):
    student_id = uuid4()
    plans = InMemoryPlanRepository()
    tasks = InMemoryTaskRepository()
    version = PlanVersionRecord(
        id=uuid4(),
        career_plan_id=uuid4(),
        student_id=student_id,
        ai_run_id=uuid4(),
        version=1,
        status=plan_status,
        snapshot=PlanDraft(
            milestones=[],
            tasks=[],
            sources=[],
            unknowns=[],
            risks=[],
            generation_mode="rules",
        ),
    )
    task = GrowthTaskRecord(
        id=uuid4(),
        student_id=student_id,
        plan_version_id=version.id,
        title="完成编程练习",
        competency_code="programming",
        due_date=date(2026, 11, 5),
        weekly_hours=3,
        source_refs=["教学演示岗位数据"],
    )
    await plans.save(version)
    await tasks.save(task)
    return TaskService(tasks, plans), tasks, task, student_id


async def test_list_by_week_and_status_and_transition_with_reason() -> None:
    service, _, task, student_id = await setup_task()

    listed = await service.list(student_id, week_start=date(2026, 11, 2), status=TaskStatus.todo)
    started = await service.transition(student_id, task.id, TaskStatus.in_progress)
    assert started.status is TaskStatus.in_progress
    delayed = await service.transition(
        student_id, task.id, TaskStatus.delayed, reason="期中考试占用时间"
    )

    assert [item.id for item in listed] == [task.id]
    assert delayed.status is TaskStatus.delayed
    assert delayed.status_reason == "期中考试占用时间"


async def test_concurrent_same_key_checkin_is_append_only_and_idempotent() -> None:
    service, repository, task, student_id = await setup_task()

    checkins = await asyncio.gather(
        *(
            service.check_in(
                student_id,
                task.id,
                content="完成数组练习",
                actual_hours=1.5,
                proof_url="https://example.edu/proof/1",
                idempotency_key="checkin-1",
            )
            for _ in range(50)
        )
    )

    assert len({item.id for item in checkins}) == 1
    assert len(repository.checkins) == 1
    assert task.status is TaskStatus.in_progress
    saved = next(iter(repository.checkins.values()))
    assert saved.actual_hours == 1.5
    assert saved.proof_url == "https://example.edu/proof/1"


async def test_archived_plan_and_cross_student_mutation_are_rejected() -> None:
    service, _, task, student_id = await setup_task(plan_status=PlanStatus.archived)

    with pytest.raises(ForbiddenError):
        await service.transition(uuid4(), task.id, TaskStatus.in_progress)
    with pytest.raises(ConflictError, match="当前激活计划"):
        await service.check_in(
            student_id,
            task.id,
            content="不应保存",
            actual_hours=1,
            proof_url=None,
            idempotency_key="archived",
        )


def test_task_list_transition_and_checkin_api() -> None:
    subject, _, task, student_id = asyncio.run(setup_task())
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="s" * 32,
    )
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
    app.state.task_service = subject
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"

    listed = client.get("/api/v1/tasks?week_start=2026-11-02&status=todo")
    checked = client.post(
        f"/api/v1/tasks/{task.id}/check-ins",
        headers={"Idempotency-Key": "api-checkin-1"},
        json={
            "content": "完成第一阶段练习",
            "actual_hours": 1.25,
            "proof_url": "https://example.edu/proof/1",
        },
    )
    repeated = client.post(
        f"/api/v1/tasks/{task.id}/check-ins",
        headers={"Idempotency-Key": "api-checkin-1"},
        json={"content": "重复请求", "actual_hours": 9},
    )
    completed = client.post(f"/api/v1/tasks/{task.id}/transition", json={"status": "completed"})

    assert listed.status_code == 200 and listed.json()[0]["id"] == str(task.id)
    assert checked.status_code == 201
    assert repeated.json()["id"] == checked.json()["id"]
    assert completed.json()["status"] == "completed"
