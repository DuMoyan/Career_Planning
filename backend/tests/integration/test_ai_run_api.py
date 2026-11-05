import asyncio
from datetime import date
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.agents.model import InvalidModelOutput, ModelRateLimited, ModelTimeout
from app.agents.planning_graph import PlanningGraph
from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.main import create_app
from app.repositories.ai_runs import InMemoryAIRunRepository
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.schemas.planning import PlanningContext, PlanningGap
from app.services.ai_runs import AIRunService
from app.services.auth import AuthService


class ScriptedModel:
    service_version = "fake-service-1"
    model_version = "fake-model-1"
    prompt_version = "prompt-1"

    def __init__(self, failures: list[Exception] | None = None) -> None:
        self.failures = failures or []
        self.calls = 0

    async def generate(self, _context):
        self.calls += 1
        raise self.failures.pop(0)

    async def repair(self, _context, _errors):
        self.calls += 1
        raise self.failures.pop(0)


def planning_context() -> PlanningContext:
    return PlanningContext(
        goal_deadline=date(2027, 6, 30),
        weekly_hours=5,
        gaps=[
            PlanningGap(
                competency_code="programming",
                status="developable_gap",
                required_level=3,
                current_level=2,
                source="教学演示岗位数据",
            )
        ],
        input_references={"goal_id": "goal-1", "profile_version": "2"},
    )


def build_client(model=None, *, auto_process: bool = True):
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
    repository = InMemoryAIRunRepository()
    graph = PlanningGraph(model)
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.ai_run_service = AIRunService(
        repository=repository,
        graph=graph,
        context_provider=lambda _student_id: planning_context(),
        audits=audits,
        auto_process=auto_process,
    )
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, repository


@pytest.mark.parametrize(
    ("model", "reason"),
    [
        (None, "missing_api_key"),
        (ScriptedModel([ModelTimeout()]), "model_timeout"),
        (ScriptedModel([ModelRateLimited()]), "rate_limited"),
    ],
)
def test_model_unavailability_falls_back_to_rules(model, reason) -> None:
    client, _ = build_client(model)

    created = client.post("/api/v1/plans/generations")
    status = client.get(f"/api/v1/plans/generations/{created.json()['id']}")

    assert created.status_code == 202
    assert status.json()["status"] == "completed"
    assert status.json()["generation_mode"] == "rules"
    assert status.json()["fallback_reason"] == reason


def test_invalid_model_output_gets_one_repair_then_falls_back() -> None:
    model = ScriptedModel([InvalidModelOutput(), InvalidModelOutput()])
    client, _ = build_client(model)

    run = client.post("/api/v1/plans/generations").json()

    assert model.calls == 2
    assert run["generation_mode"] == "rules"
    assert run["fallback_reason"] == "invalid_model_output"
    assert run["validation_result"]["valid"] is True


def test_sse_disconnect_does_not_cancel_run_and_status_remains_pollable() -> None:
    client, _ = build_client(None)
    run = client.post("/api/v1/plans/generations").json()

    with client.stream("GET", f"/api/v1/plans/generations/{run['id']}/events") as response:
        assert response.status_code == 200
        assert "event: started" in next(response.iter_text())

    assert client.get(f"/api/v1/plans/generations/{run['id']}").json()["status"] == "completed"


def test_only_one_running_job_per_student_returns_conflict() -> None:
    client, _ = build_client(None, auto_process=False)

    first = client.post("/api/v1/plans/generations")
    second = client.post("/api/v1/plans/generations")

    assert first.status_code == 202
    assert second.status_code == 409


def test_deferred_run_can_be_processed_and_unexpected_failure_reaches_terminal_state() -> None:
    client, repository = build_client(None, auto_process=False)
    created = client.post("/api/v1/plans/generations").json()
    run_id = UUID(created["id"])
    student_id = repository.runs[run_id].student_id

    completed = asyncio.run(client.app.state.ai_run_service.process(run_id, student_id))

    assert created["status"] == "running"
    assert completed.status == "completed"
    assert completed.generation_mode == "rules"

    class BrokenGraph:
        async def run(self, _context):
            raise RuntimeError("unexpected")

    service = client.app.state.ai_run_service
    service.graph = BrokenGraph()
    failed_run = asyncio.run(service.create(student_id))
    failed = asyncio.run(service.process(failed_run.id, student_id))

    assert failed.status == "failed"
    assert failed.error_code == "RuntimeError"


def test_retry_creates_new_immutable_snapshot() -> None:
    client, repository = build_client(None)
    original = client.post("/api/v1/plans/generations").json()
    original_id = UUID(original["id"])
    original_snapshot = repository.runs[original_id].plan_snapshot.copy()

    retried = client.post(f"/api/v1/plans/generations/{original['id']}/retry")

    assert retried.status_code == 202
    assert retried.json()["id"] != original["id"]
    assert retried.json()["parent_run_id"] == original["id"]
    assert repository.runs[original_id].plan_snapshot == original_snapshot
