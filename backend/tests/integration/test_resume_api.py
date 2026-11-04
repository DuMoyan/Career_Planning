from io import BytesIO
from uuid import uuid4

from docx import Document
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.core.config import Settings
from app.core.security import hash_password
from app.domain.access import Role
from app.main import create_app
from app.repositories.audits import InMemoryAuditRepository
from app.repositories.competencies import InMemoryCompetencyRepository
from app.repositories.users import InMemoryUserRepository, UserRecord
from app.services.auth import AuthService
from app.services.competencies import CompetencyService
from app.services.resumes import MemoryFileStore, ResumeParser, ResumeService


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
    repository = InMemoryCompetencyRepository()
    app = create_app(settings)
    app.state.auth_service = AuthService(users=users, audits=audits, settings=settings)
    app.state.resume_service = ResumeService(
        repository=repository,
        files=MemoryFileStore(),
        parser=ResumeParser(),
        max_bytes=settings.upload_max_bytes,
    )
    app.state.competency_service = CompetencyService(repository)
    client = TestClient(app)
    token = client.post(
        "/api/v1/auth/login", json={"identifier": "20260001", "password": "Career!2026"}
    ).json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_txt_resume_creates_draft_only_until_student_confirms_evidence() -> None:
    client = build_client()
    uploaded = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.txt", "Python 项目开发与数据分析", "text/plain")},
    )

    assert uploaded.status_code == 201
    assert uploaded.json()["candidates"]
    assert client.get("/api/v1/competencies/evidence").json() == []

    candidate = uploaded.json()["candidates"][0]
    confirmed = client.post(
        "/api/v1/competencies/evidence",
        json={
            "resume_id": uploaded.json()["id"],
            "competency_code": candidate["competency_code"],
            "demonstrated_level": 3,
            "description": candidate["description"],
        },
    )
    profile = client.post("/api/v1/competencies/profiles")

    assert confirmed.status_code == 201
    assert profile.status_code == 201
    assert profile.json()["dimensions"][candidate["competency_code"]]["level"] == 3


def test_upload_rejects_disallowed_extension_mime_mismatch_and_oversize() -> None:
    client = build_client()

    disallowed = client.post(
        "/api/v1/resumes", files={"file": ("resume.exe", b"x", "application/octet-stream")}
    )
    mismatch = client.post(
        "/api/v1/resumes", files={"file": ("resume.txt", b"x", "application/pdf")}
    )
    oversized = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.txt", BytesIO(b"x" * (10_485_760 + 1)), "text/plain")},
    )

    assert disallowed.status_code == 400
    assert mismatch.status_code == 400
    assert oversized.status_code == 413


def test_pdf_and_docx_resumes_are_accepted() -> None:
    client = build_client()
    pdf_buffer = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf_buffer)
    docx_buffer = BytesIO()
    document = Document()
    document.add_paragraph("Python 项目开发")
    document.save(docx_buffer)

    pdf = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", pdf_buffer.getvalue(), "application/pdf")},
    )
    docx = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "resume.docx",
                docx_buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert pdf.status_code == 201
    assert docx.status_code == 201
    assert docx.json()["candidates"]


def test_corrupt_document_returns_safe_error_without_partial_evidence() -> None:
    client = build_client()

    response = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", b"not-a-pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "简历文件无法解析，请检查文件是否完整"
    assert client.get("/api/v1/competencies/evidence").json() == []


def test_deleting_resume_removes_draft_but_retains_confirmed_evidence_marker() -> None:
    client = build_client()
    resume = client.post(
        "/api/v1/resumes", files={"file": ("resume.txt", "Python 项目", "text/plain")}
    ).json()
    candidate = resume["candidates"][0]
    evidence = client.post(
        "/api/v1/competencies/evidence",
        json={
            "resume_id": resume["id"],
            "competency_code": candidate["competency_code"],
            "demonstrated_level": 2,
            "description": candidate["description"],
        },
    ).json()

    deleted = client.delete(f"/api/v1/resumes/{resume['id']}")
    remaining = client.get("/api/v1/competencies/evidence").json()

    assert deleted.status_code == 204
    assert remaining[0]["id"] == evidence["id"]
    assert remaining[0]["source_deleted"] is True
