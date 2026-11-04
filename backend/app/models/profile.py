from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    department: Mapped[str | None] = mapped_column(String(64), nullable=True)
    major: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    available_hours: Mapped[float] = mapped_column(Float, default=0)
    constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
