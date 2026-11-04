from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.main import create_app
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.competencies import EvidenceRecord, InMemoryCompetencyRepository
from app.repositories.targets import InMemoryTargetRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.seed.targets import build_demo_targets
from app.services.auth import AuthService
from app.services.targets import GoalService, TargetService


def build_client() -> tuple[TestClient, InMemoryCompetencyRepository, dict[str, str]]:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="s" * 32,
    )
    users = InMemoryUserRepository()
    credentials = {"student-a": "20260001", "student-b": "20260002"}
    for identifier in credentials.values():
        users.add(
            UserRecord(
                id=uuid4(),
                identifier=identifier,
                password_hash=hash_password("Career!2026"),
                role=Role.student,
            )
        )
    audits = InMemoryAuditRepository()
    competencies = InMemoryCompetencyRepository()
    targets = InMemoryTargetRepository(build_demo_targets())
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.target_service = TargetService(targets, competencies)
    app.state.goal_service = GoalService(targets)
    client = TestClient(app)
    tokens = {}
    for key, identifier in credentials.items():
        tokens[key] = client.post(
            "/api/v1/auth/login",
            json={"identifier": identifier, "password": "Career!2026"},
        ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {tokens['student-a']}"
    return client, competencies, tokens


def test_target_catalog_supports_keyword_category_and_freshness_metadata() -> None:
    client, _, _ = build_client()

    result = client.get("/api/v1/targets", params={"keyword": "软件", "category": "技术"})

    assert result.status_code == 200
    assert [item["name"] for item in result.json()] == ["软件开发工程师"]
    assert result.json()[0]["source"] == "教学演示岗位数据"
    assert result.json()[0]["verified_at"]
    assert result.json()[0]["is_stale"] is False
    product = client.get("/api/v1/targets", params={"category": "产品"}).json()[0]
    assert product["is_stale"] is True


def test_comparison_requires_two_to_three_targets_and_traces_gap_evidence() -> None:
    client, competencies, _ = build_client()
    targets = client.get("/api/v1/targets").json()
    software = next(item for item in targets if item["name"] == "软件开发工程师")
    data = next(item for item in targets if item["name"] == "数据分析师")
    algorithm = next(item for item in targets if item["name"] == "算法工程师")
    student_id = client.app.state.auth_service.users._users_by_identifier["20260001"].id
    evidence_id = uuid4()
    competencies.evidence[evidence_id] = EvidenceRecord(
        id=evidence_id,
        student_id=student_id,
        resume_id=None,
        competency_code="programming",
        demonstrated_level=3,
        description="独立完成课程项目",
    )

    too_few = client.post("/api/v1/targets/compare", json={"target_ids": [software["id"]]})
    compared = client.post(
        "/api/v1/targets/compare",
        json={"target_ids": [software["id"], data["id"], algorithm["id"]]},
    )

    assert too_few.status_code == 422
    assert compared.status_code == 200
    assert len(compared.json()["targets"]) == 3
    programming = next(
        gap
        for target in compared.json()["targets"]
        for gap in target["gaps"]
        if gap["competency_code"] == "programming"
    )
    assert programming["evidence_ids"] == [str(evidence_id)]
    assert programming["requirement_source"] == "教学演示岗位数据"
    assert compared.json()["targets"][0]["interests"]
    assert compared.json()["targets"][0]["values"]


def test_primary_goal_requires_deadline_is_unique_and_private_to_student() -> None:
    client, _, tokens = build_client()
    target_ids = [item["id"] for item in client.get("/api/v1/targets").json()[:2]]

    missing_deadline = client.post(
        "/api/v1/goals", json={"target_id": target_ids[0], "primary": True}
    )
    first = client.post(
        "/api/v1/goals",
        json={"target_id": target_ids[0], "deadline": str(date.today()), "primary": True},
    )
    second = client.post(
        "/api/v1/goals",
        json={"target_id": target_ids[1], "deadline": "2027-06-30", "primary": True},
    )

    assert missing_deadline.status_code == 422
    assert first.status_code == 201
    assert second.status_code == 201
    goals = client.get("/api/v1/goals").json()
    assert sum(goal["primary"] for goal in goals) == 1
    assert next(goal for goal in goals if goal["primary"])["id"] == second.json()["id"]

    client.headers["Authorization"] = f"Bearer {tokens['student-b']}"
    assert client.get("/api/v1/goals").json() == []
