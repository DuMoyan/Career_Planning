import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.domain.grants import GrantScope
from app.main import create_app
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.grants import InMemoryGrantCache, InMemoryGrantRepository
from app.repositories.profiles import InMemoryProfileRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.services.auth import AuthService
from app.services.grants import GrantService
from app.services.profiles import ProfileService


def build_app() -> tuple[TestClient, UUID, UUID, GrantService, InMemoryAuditRepository]:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="s" * 32,
    )
    student_id, mentor_id = uuid4(), uuid4()
    users = InMemoryUserRepository()
    users.add(
        UserRecord(
            id=student_id,
            identifier="20260001",
            password_hash=hash_password("Career!2026"),
            role=Role.student,
        )
    )
    users.add(
        UserRecord(
            id=mentor_id,
            identifier="M0001",
            password_hash=hash_password("Mentor!2026"),
            role=Role.mentor,
        )
    )
    audits = InMemoryAuditRepository()
    grants = GrantService(
        repository=InMemoryGrantRepository(),
        cache=InMemoryGrantCache(),
        audits=audits,
    )
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.profile_service = ProfileService(InMemoryProfileRepository())
    app.state.grant_service = grants
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client, student_id, mentor_id, grants, audits


def test_student_can_update_and_read_own_profile_but_not_another_student() -> None:
    client, _student_id, _mentor_id, _grants, _audits = build_app()

    updated = client.put(
        "/api/v1/profiles/me",
        json={
            "department": "计算机学院",
            "major": "软件工程",
            "grade_level": "大四",
            "gpa": 3.72,
            "available_hours": 12.5,
            "constraints": {"city": "上海"},
        },
    )
    own = client.get("/api/v1/profiles/me")
    other = client.get(f"/api/v1/profiles/{uuid4()}")

    assert updated.status_code == 200
    assert own.json()["major"] == "软件工程"
    assert own.json()["available_hours"] == 12.5
    assert other.status_code == 403


def test_mentor_cannot_read_full_student_profile_without_using_scoped_summary() -> None:
    client, student_id, _mentor_id, _grants, _audits = build_app()
    mentor_token = client.post(
        "/api/v1/auth/login",
        json={"identifier": "M0001", "password": "Mentor!2026"},
    ).json()["access_token"]

    response = client.get(
        f"/api/v1/profiles/{student_id}",
        headers={"Authorization": f"Bearer {mentor_token}"},
    )

    assert response.status_code == 403


def test_grant_defaults_to_90_days_writes_audit_and_revoke_invalidates_cache() -> None:
    client, student_id, mentor_id, grants, audits = build_app()

    created = client.post(
        "/api/v1/consents/mentor-grants",
        json={
            "mentor_id": str(mentor_id),
            "scopes": ["profile_summary", "goals"],
        },
    )
    grant_id = UUID(created.json()["id"])
    expires_at = datetime.fromisoformat(created.json()["expires_at"])
    remaining_days = (expires_at - datetime.now(UTC)).days

    assert created.status_code == 201
    assert remaining_days in {89, 90}
    assert asyncio.run(grants.can_read(mentor_id, student_id, GrantScope.profile_summary)) is True

    revoked = client.delete(f"/api/v1/consents/mentor-grants/{grant_id}")

    assert revoked.status_code == 204
    assert asyncio.run(grants.can_read(mentor_id, student_id, GrantScope.profile_summary)) is False
    assert [event.event_type for event in audits.events][-2:] == [
        "mentor_grant_created",
        "mentor_grant_revoked",
    ]


def test_grant_accepts_explicit_expiry_and_never_returns_raw_assessment_scope() -> None:
    client, _student_id, mentor_id, _grants, _audits = build_app()

    response = client.post(
        "/api/v1/consents/mentor-grants",
        json={
            "mentor_id": str(mentor_id),
            "scopes": ["plan_progress"],
            "expires_at": "2027-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 201
    assert response.json()["scopes"] == ["plan_progress"]
    assert "assessment_answers" not in response.text


def test_cached_grant_is_rejected_immediately_after_expiry() -> None:
    now = datetime(2026, 11, 5, tzinfo=UTC)

    def clock() -> datetime:
        return now

    repository = InMemoryGrantRepository()
    service = GrantService(
        repository=repository,
        cache=InMemoryGrantCache(),
        audits=InMemoryAuditRepository(),
        now_provider=clock,
    )
    student_id, mentor_id = uuid4(), uuid4()
    grant = asyncio.run(
        service.create(
            student_id=student_id,
            mentor_id=mentor_id,
            scopes=frozenset({GrantScope.profile_summary}),
            expires_at=now + timedelta(seconds=1),
        )
    )
    assert grant.expires_at == now + timedelta(seconds=1)
    assert asyncio.run(service.can_read(mentor_id, student_id, GrantScope.profile_summary)) is True

    now += timedelta(seconds=2)

    assert asyncio.run(service.can_read(mentor_id, student_id, GrantScope.profile_summary)) is False
