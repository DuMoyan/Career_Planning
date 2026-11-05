import asyncio
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import create_engine
from app.main import create_app
from app.models.base import Base
from app.repositories.grants import InMemoryGrantCache


def _settings(database_url: str, upload_dir: Path) -> Settings:
    return Settings(
        _env_file=None,
        app_env="production",
        database_url=database_url,
        redis_url="redis://localhost:6379/15",
        jwt_secret="s" * 32,
        upload_dir=str(upload_dir),
    )


async def _create_schema(database_url: str) -> None:
    engine = create_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    await engine.dispose()


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "demo-student", "password": "Demo!2026"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _login_as(client: TestClient, identifier: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": identifier, "password": "Demo!2026"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _wait_for_run(client: TestClient, headers: dict[str, str], run_id: str) -> dict:
    for _ in range(100):
        run = client.get(f"/api/v1/plans/generations/{run_id}", headers=headers).json()
        if run["status"] in {"completed", "failed"}:
            return run
        time.sleep(0.01)
    raise AssertionError("规划生成未在预期时间内结束")


def test_production_runtime_persists_profile_across_application_restart(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'career.db').as_posix()}"
    settings = _settings(database_url, tmp_path / "uploads")
    asyncio.run(_create_schema(database_url))

    with TestClient(create_app(settings)) as first:
        token = _login(first)
        response = first.put(
            "/api/v1/profiles/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"major": "软件工程", "available_hours": 9, "constraints": {}},
        )
        assert response.status_code == 200

    with TestClient(create_app(settings)) as restarted:
        token = _login(restarted)
        profile = restarted.get(
            "/api/v1/profiles/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert profile.status_code == 200
    assert profile.json()["major"] == "软件工程"
    assert profile.json()["available_hours"] == 9


def test_production_runtime_persists_goal_plan_task_and_checkin(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'career-flow.db').as_posix()}"
    settings = _settings(database_url, tmp_path / "uploads")
    asyncio.run(_create_schema(database_url))

    with TestClient(create_app(settings)) as first:
        token = _login(first)
        headers = {"Authorization": f"Bearer {token}"}
        target_id = first.get("/api/v1/targets", headers=headers).json()[0]["id"]
        goal = first.post(
            "/api/v1/goals",
            headers=headers,
            json={
                "target_id": target_id,
                "deadline": "2027-06-30",
                "weekly_hours": 6,
                "primary": True,
            },
        )
        assert goal.status_code == 201
        created_run = first.post("/api/v1/plans/generations", headers=headers).json()
        run = _wait_for_run(first, headers, created_run["id"])
        assert run["status"] == "completed"
        draft = first.post(
            "/api/v1/plans/drafts",
            headers=headers,
            json={"ai_run_id": run["id"]},
        ).json()
        first.post(
            f"/api/v1/plans/versions/{draft['id']}/activate",
            headers={**headers, "Idempotency-Key": "persistent-activation"},
        )
        task = first.get("/api/v1/tasks", headers=headers).json()[0]
        checkin = first.post(
            f"/api/v1/tasks/{task['id']}/check-ins",
            headers={**headers, "Idempotency-Key": "persistent-checkin"},
            json={"content": "完成持久化练习", "actual_hours": 1.5},
        ).json()

    with TestClient(create_app(settings)) as restarted:
        token = _login(restarted)
        headers = {"Authorization": f"Bearer {token}"}
        goals = restarted.get("/api/v1/goals", headers=headers).json()
        history = restarted.get("/api/v1/plans/history", headers=headers).json()
        tasks = restarted.get("/api/v1/tasks", headers=headers).json()
        checkins = restarted.get(
            f"/api/v1/tasks/{task['id']}/check-ins", headers=headers
        ).json()

    assert any(item["id"] == goal.json()["id"] for item in goals)
    assert history[0]["status"] == "active"
    assert tasks[0]["id"] == task["id"]
    assert checkins[0]["id"] == checkin["id"]


def test_production_runtime_persists_assessment_resume_evidence_and_report(
    tmp_path: Path,
) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'student-data.db').as_posix()}"
    upload_dir = tmp_path / "uploads"
    settings = _settings(database_url, upload_dir)
    asyncio.run(_create_schema(database_url))

    with TestClient(create_app(settings)) as first:
        token = _login(first)
        headers = {"Authorization": f"Bearer {token}"}
        scale = first.get("/api/v1/assessments/scales", headers=headers).json()[0]
        detail = first.get(
            f"/api/v1/assessments/scales/{scale['id']}", headers=headers
        ).json()
        answers = {item["id"]: 4 for item in detail["items"]}
        assert first.put(
            f"/api/v1/assessments/scales/{scale['id']}/progress",
            headers=headers,
            json={"answers": answers},
        ).status_code == 200
        assessment = first.post(
            f"/api/v1/assessments/scales/{scale['id']}/submit",
            headers={**headers, "Idempotency-Key": "persistent-assessment"},
        ).json()
        resume = first.post(
            "/api/v1/resumes",
            headers=headers,
            files={"file": ("resume.txt", "Python 项目开发".encode(), "text/plain")},
        ).json()
        candidate = resume["candidates"][0]
        evidence = first.post(
            "/api/v1/competencies/evidence",
            headers=headers,
            json={
                "resume_id": resume["id"],
                "competency_code": candidate["competency_code"],
                "demonstrated_level": 3,
                "description": candidate["description"],
            },
        ).json()
        assert first.post("/api/v1/competencies/profiles", headers=headers).status_code == 201
        report = first.post(
            "/api/v1/reports/weekly",
            headers=headers,
            json={"week_start": "2026-11-02"},
        ).json()
        response = first.post(
            f"/api/v1/reports/weekly/{report['id']}/response",
            headers=headers,
            json={"action": "modify", "text": "减少任务量，保留核心练习"},
        ).json()
        replanning = _wait_for_run(first, headers, response["replan_run_id"])

    assert any(upload_dir.iterdir())
    with TestClient(create_app(settings)) as restarted:
        token = _login(restarted)
        headers = {"Authorization": f"Bearer {token}"}
        resumed = restarted.get(
            f"/api/v1/assessments/scales/{scale['id']}/progress", headers=headers
        ).json()
        assessment_report = restarted.get(
            f"/api/v1/assessments/records/{assessment['id']}/report", headers=headers
        )
        evidence_list = restarted.get(
            "/api/v1/competencies/evidence", headers=headers
        ).json()
        same_report = restarted.post(
            "/api/v1/reports/weekly",
            headers=headers,
            json={"week_start": "2026-11-02"},
        ).json()
        deleted = restarted.delete(f"/api/v1/resumes/{resume['id']}", headers=headers)

    assert resumed["answers"] == answers
    assert assessment_report.status_code == 200
    assert evidence_list[0]["id"] == evidence["id"]
    assert same_report["id"] == report["id"]
    assert response["response_text"] == "减少任务量，保留核心练习"
    assert replanning["status"] == "completed"
    assert replanning["input_references"]["weekly_feedback"] == response["response_text"]
    assert deleted.status_code == 204
    assert not any(upload_dir.iterdir())


def test_production_runtime_persists_grant_mentor_comment_and_audit(tmp_path: Path) -> None:
    database_url = f"sqlite+aiosqlite:///{(tmp_path / 'mentor-data.db').as_posix()}"
    settings = _settings(database_url, tmp_path / "uploads")
    asyncio.run(_create_schema(database_url))
    mentor_id = uuid5(NAMESPACE_URL, "career-planning/demo-mentor")

    with TestClient(create_app(settings)) as first:
        first.app.state.grant_service.cache = InMemoryGrantCache()
        student_token = _login(first)
        student_headers = {"Authorization": f"Bearer {student_token}"}
        created_run = first.post(
            "/api/v1/plans/generations", headers=student_headers
        ).json()
        run = _wait_for_run(first, student_headers, created_run["id"])
        draft = first.post(
            "/api/v1/plans/drafts",
            headers=student_headers,
            json={"ai_run_id": run["id"]},
        ).json()
        active = first.post(
            f"/api/v1/plans/versions/{draft['id']}/activate",
            headers={**student_headers, "Idempotency-Key": "mentor-persistent-plan"},
        ).json()
        grant = first.post(
            "/api/v1/consents/mentor-grants",
            headers=student_headers,
            json={
                "mentor_id": str(mentor_id),
                "scopes": ["plan_progress"],
                "expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
            },
        )
        assert grant.status_code == 201
        mentor_headers = {
            "Authorization": f"Bearer {_login_as(first, 'demo-mentor')}"
        }
        comment = first.post(
            f"/api/v1/mentor/plan-versions/{active['id']}/comments",
            headers=mentor_headers,
            json={"content": "建议保持每周复盘"},
        ).json()

    with TestClient(create_app(settings)) as restarted:
        student_headers = {
            "Authorization": f"Bearer {_login_as(restarted, 'demo-student')}"
        }
        comments = restarted.get(
            f"/api/v1/mentor/plan-versions/{active['id']}/comments",
            headers=student_headers,
        ).json()
        mentor_headers = {
            "Authorization": f"Bearer {_login_as(restarted, 'demo-mentor')}"
        }
        students = restarted.get("/api/v1/mentor/students", headers=mentor_headers).json()
        admin_headers = {
            "Authorization": f"Bearer {_login_as(restarted, 'demo-admin')}"
        }
        overview = restarted.get("/api/v1/admin/overview", headers=admin_headers).json()

    assert comments[0]["id"] == comment["id"]
    assert students[0]["student_id"] == grant.json()["student_id"]
    assert overview["audits"]
