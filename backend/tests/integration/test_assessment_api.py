from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.main import create_app
from app.repositories.assessments import InMemoryAssessmentRepository
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.seed.assessments import build_demo_scales
from app.services.assessments import AssessmentService
from app.services.auth import AuthService


def build_client() -> TestClient:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="s" * 32,
    )
    users = InMemoryUserRepository()
    users.add(
        UserRecord(
            id=uuid4(),
            identifier="20260001",
            password_hash=hash_password("Career!2026"),
            role=Role.student,
        )
    )
    audits = InMemoryAuditRepository()
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.assessment_service = AssessmentService(
        InMemoryAssessmentRepository(build_demo_scales())
    )
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_demo_scales_have_required_item_counts_and_are_separate() -> None:
    client = build_client()

    response = client.get("/api/v1/assessments/scales")

    assert response.status_code == 200
    assert [(item["kind"], item["item_count"]) for item in response.json()] == [
        ("interest", 36),
        ("work_values", 21),
    ]


def test_progress_resumes_and_submission_is_idempotent_and_private() -> None:
    client = build_client()
    scale = client.get("/api/v1/assessments/scales").json()[0]
    detail = client.get(f"/api/v1/assessments/scales/{scale['id']}").json()
    answers = {item["id"]: 4 for item in detail["items"]}

    saved = client.put(
        f"/api/v1/assessments/scales/{scale['id']}/progress",
        json={"answers": answers},
    )
    resumed = client.get(f"/api/v1/assessments/scales/{scale['id']}/progress")
    first = client.post(
        f"/api/v1/assessments/scales/{scale['id']}/submit",
        headers={"Idempotency-Key": "assessment-001"},
    )
    second = client.post(
        f"/api/v1/assessments/scales/{scale['id']}/submit",
        headers={"Idempotency-Key": "assessment-001"},
    )

    assert saved.status_code == 200
    assert resumed.json()["answers"] == answers
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert "answers" not in first.json()
    assert first.json()["visibility"] == "private"


def test_report_contains_versions_date_disclaimer_and_dimension_scores() -> None:
    client = build_client()
    scale = client.get("/api/v1/assessments/scales").json()[1]
    detail = client.get(f"/api/v1/assessments/scales/{scale['id']}").json()
    client.put(
        f"/api/v1/assessments/scales/{scale['id']}/progress",
        json={"answers": {item["id"]: 3 for item in detail["items"]}},
    )
    record = client.post(
        f"/api/v1/assessments/scales/{scale['id']}/submit",
        headers={"Idempotency-Key": "values-001"},
    ).json()

    report = client.get(f"/api/v1/assessments/records/{record['id']}/report")

    assert report.status_code == 200
    assert report.json()["kind"] == "work_values"
    assert report.json()["scale_version"] == "1.0"
    assert report.json()["completed_at"]
    assert report.json()["dimension_scores"]
    assert "不代表能力" in report.json()["disclaimer"]
