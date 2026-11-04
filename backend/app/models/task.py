from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GrowthTask(Base):
    __tablename__ = "growth_tasks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("plan_versions.id", ondelete="CASCADE"), index=True
    )
    source_task_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("growth_tasks.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255))
    competency_code: Mapped[str] = mapped_column(String(64))
    due_date: Mapped[date] = mapped_column(Date)
    weekly_hours: Mapped[float] = mapped_column(Float)
    source_refs: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="todo")
    status_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TaskCheckIn(Base):
    __tablename__ = "task_checkins"
    __table_args__ = (
        UniqueConstraint("student_id", "idempotency_key", name="uq_task_checkin_idempotency"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    task_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("growth_tasks.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    actual_hours: Mapped[float] = mapped_column(Float)
    proof_url: Mapped[str | None] = mapped_column(String(2048))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
