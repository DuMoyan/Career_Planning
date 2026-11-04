from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("student_id", "week_start", name="uq_weekly_report_student_week"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    week_start: Mapped[date] = mapped_column(Date)
    metrics: Mapped[dict] = mapped_column(JSON)
    advice: Mapped[str] = mapped_column(Text)
    advice_mode: Mapped[str] = mapped_column(String(16))
    response_action: Mapped[str | None] = mapped_column(String(16))
    response_text: Mapped[str | None] = mapped_column(Text)
    replan_run_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("ai_planning_runs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
