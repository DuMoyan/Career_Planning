from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, String, Uuid, func
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
    status: Mapped[str] = mapped_column(String(24), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
