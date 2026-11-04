from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AIPlanningRun(Base):
    __tablename__ = "ai_planning_runs"
    __table_args__ = (
        Index(
            "uq_ai_planning_runs_active_student",
            "student_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    parent_run_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_planning_runs.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(24), index=True)
    generation_mode: Mapped[str | None] = mapped_column(String(16))
    fallback_reason: Mapped[str | None] = mapped_column(String(64))
    service_version: Mapped[str] = mapped_column(String(64))
    model_version: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64))
    input_references: Mapped[dict] = mapped_column(JSON)
    plan_snapshot: Mapped[dict | None] = mapped_column(JSON)
    validation_result: Mapped[dict | None] = mapped_column(JSON)
    sources: Mapped[list] = mapped_column(JSON)
    confirmation_status: Mapped[str] = mapped_column(String(24), default="pending")
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
