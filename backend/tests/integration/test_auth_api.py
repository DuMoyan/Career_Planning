from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.main import create_app
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.services.auth import AuthService


def build_client(*, active: bool = True) -> tuple[TestClient, InMemoryAuditRepository]:
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
            is_active=active,
        )
    )
    audits = InMemoryAuditRepository()
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    return TestClient(app), audits


def test_valid_login_returns_token_pair_and_writes_audit() -> None:
    client, audits = build_client()

    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]
    assert [event.event_type for event in audits.events] == ["login_success"]


def test_invalid_credentials_and_disabled_account_use_same_public_message() -> None:
    normal_client, _ = build_client()
    disabled_client, _ = build_client(active=False)

    wrong = normal_client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "wrong"},
    )
    disabled = disabled_client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    )

    assert wrong.status_code == disabled.status_code == 401
    assert (
        wrong.json()
        == disabled.json()
        == {"error": {"code": "INVALID_CREDENTIALS", "message": "账号或密码错误"}}
    )


def test_five_failed_logins_temporarily_lock_account() -> None:
    client, _ = build_client()

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"identifier": "20260001", "password": "wrong"},
        )
        assert response.status_code == 401

    locked = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    )

    assert locked.status_code == 423
    assert locked.json()["error"]["code"] == "ACCOUNT_LOCKED"


def test_refresh_rotates_token_and_logout_revokes_latest_token() -> None:
    client, _ = build_client()
    login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "20260001", "password": "Career!2026"},
    ).json()

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    old_again = client.post("/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]})
    logout = client.post(
        "/api/v1/auth/logout", json={"refresh_token": rotated.json()["refresh_token"]}
    )
    after_logout = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}
    )

    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != login["refresh_token"]
    assert old_again.status_code == 401
    assert logout.status_code == 204
    assert after_logout.status_code == 401
