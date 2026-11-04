from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from docx import Document
from pypdf import PdfReader

from app.core.errors import DomainError, ForbiddenError, PayloadTooLargeError
from app.repositories.competencies import (
    ResumeCandidate,
    ResumeDraft,
)


class MemoryFileStore:
    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def save(self, content: bytes) -> str:
        key = str(uuid4())
        self.files[key] = content
        return key

    async def delete(self, key: str) -> None:
        self.files.pop(key, None)


class ResumeParser:
    KEYWORDS = {
        "programming": ("python", "java", "开发", "编程"),
        "data_analysis": ("数据分析", "sql", "统计"),
        "communication": ("沟通", "演讲", "汇报"),
        "project_execution": ("项目", "实习", "交付"),
    }

    def parse(self, file_name: str, media_type: str, content: bytes) -> tuple[ResumeCandidate, ...]:
        suffix = Path(file_name).suffix.lower()
        try:
            if suffix == ".txt":
                text = content.decode("utf-8")
            elif suffix == ".pdf":
                text = "\n".join(
                    page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages
                )
            else:
                text = "\n".join(p.text for p in Document(BytesIO(content)).paragraphs)
        except Exception as exc:
            raise DomainError("简历文件无法解析，请检查文件是否完整") from exc
        lowered = text.lower()
        return tuple(
            ResumeCandidate(code, f"简历中识别到与“{keyword}”相关的经历")
            for code, keywords in self.KEYWORDS.items()
            for keyword in keywords
            if keyword.lower() in lowered
        )


class ResumeService:
    MEDIA_TYPES = {
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self, *, repository, files, parser, max_bytes: int) -> None:
        self.repository = repository
        self.files = files
        self.parser = parser
        self.max_bytes = max_bytes

    async def upload(
        self, student_id: UUID, file_name: str, media_type: str, content: bytes
    ) -> ResumeDraft:
        if len(content) > self.max_bytes:
            raise PayloadTooLargeError("简历文件不能超过10 MB")
        suffix = Path(file_name).suffix.lower()
        if suffix not in self.MEDIA_TYPES:
            raise DomainError("仅支持PDF、DOCX和TXT简历")
        if self.MEDIA_TYPES[suffix] != media_type:
            raise DomainError("文件扩展名与MIME类型不一致")
        candidates = self.parser.parse(file_name, media_type, content)
        key = await self.files.save(content)
        draft = ResumeDraft(uuid4(), student_id, key, file_name, media_type, candidates)
        await self.repository.save_resume(draft)
        return draft

    async def delete(self, student_id: UUID, resume_id: UUID) -> None:
        draft = await self.repository.delete_resume(resume_id, student_id)
        if draft is None:
            raise ForbiddenError("无权删除该简历")
        await self.files.delete(draft.file_key)
