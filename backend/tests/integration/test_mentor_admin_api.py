from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.domain.grants import GrantScope, MentorGrant
from app.domain.plans import PlanStatus
from app.main import create_app
from app.repositories.audits import AuditEvent, InMemoryAuditRepository
from app.repositories.grants import InMemoryGrantRepository
from app.repositories.plans import InMemoryPlanRepository, PlanVersionRecord
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.schemas.planning import PlanDraft
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.mentor import MentorService


def build_client():
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://u:p@localhost/x",
        redis_url="redis://localhost",
        jwt_secret="s" * 32,
    )
    ids = {role: uuid4() for role in ("student", "mentor", "admin", "operator")}
    users = InMemoryUserRepository()
    for role, identifier in (
        (Role.student, "S1"),
        (Role.mentor, "M1"),
        (Role.admin, "A1"),
        (Role.mentor, "M2"),
    ):
        key = "operator" if identifier == "M2" else role.value
        users.add(
            UserRecord(
                id=ids[key],
                identifier=identifier,
                password_hash=hash_password("Pass!2026"),
                role=role,
            )
        )
    audits = InMemoryAuditRepository()
    grants = InMemoryGrantRepository()
    plans = InMemoryPlanRepository()
    version = PlanVersionRecord(
        id=uuid4(),
        career_plan_id=uuid4(),
        student_id=ids["student"],
        ai_run_id=uuid4(),
        version=1,
        status=PlanStatus.active,
        snapshot=PlanDraft(
            milestones=[],
            tasks=[],
            sources=["岗位样本"],
            unknowns=[],
            risks=[],
            generation_mode="rules",
        ),
    )
    import asyncio

    asyncio.run(plans.save(version))
    asyncio.run(
        grants.save(
            MentorGrant(
                id=uuid4(),
                student_id=ids["student"],
                mentor_id=ids["mentor"],
                scopes=frozenset({GrantScope.plan_progress}),
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
    )
    asyncio.run(
        audits.append(
            AuditEvent(
                event_type="login",
                actor_id=ids["student"],
                target_type="session",
                target_id=None,
                result="success",
            )
        )
    )
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.mentor_service = MentorService(grants, plans)
    app.state.admin_service = AdminService(audits)
    client = TestClient(app)
    tokens = {}
    for key, identifier in (
        ("student", "S1"),
        ("mentor", "M1"),
        ("admin", "A1"),
        ("operator", "M2"),
    ):
        tokens[key] = client.post(
            "/api/v1/auth/login", json={"identifier": identifier, "password": "Pass!2026"}
        ).json()["access_token"]
    return client, ids, tokens, grants, version


def auth(client, token):
    client.headers["Authorization"] = f"Bearer {token}"


def test_active_scope_allows_safe_summary_and_plan_comment_visible_to_student() -> None:
    client, ids, tokens, _, version = build_client()
    auth(client, tokens["mentor"])
    students = client.get("/api/v1/mentor/students")
    detail = client.get(f"/api/v1/mentor/students/{ids['student']}")
    comment = client.post(
        f"/api/v1/mentor/plan-versions/{version.id}/comments", json={"content": "建议拆分里程碑"}
    )
    assert students.status_code == 200 and students.json()[0]["student_id"] == str(ids["student"])
    assert detail.status_code == 200
    assert "assessment_answers" not in detail.text and "resume_text" not in detail.text
    auth(client, tokens["student"])
    visible = client.get(f"/api/v1/mentor/plan-versions/{version.id}/comments")
    assert visible.json()[0]["id"] == comment.json()["id"]


def test_expired_or_ungranted_mentor_is_forbidden_and_operator_has_no_student_access() -> None:
    client, ids, tokens, grants, _ = build_client()
    auth(client, tokens["operator"])
    assert client.get(f"/api/v1/mentor/students/{ids['student']}").status_code == 403
    grant = next(iter(grants.records.values()))
    grants.records[grant.id] = replace(grant, expires_at=datetime.now(UTC) - timedelta(seconds=1))
    auth(client, tokens["mentor"])
    assert client.get(f"/api/v1/mentor/students/{ids['student']}").status_code == 403


def test_admin_audit_is_admin_only_and_read_only_overview_has_tabs() -> None:
    client, _, tokens, _, _ = build_client()
    auth(client, tokens["mentor"])
    assert client.get("/api/v1/admin/overview").status_code == 403
    auth(client, tokens["admin"])
    response = client.get("/api/v1/admin/overview")
    assert response.status_code == 200
    assert set(response.json()) == {"targets", "scale_versions", "audits"}
