from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CareerGoal(Base):
    __tablename__ = "career_goals"
    __table_args__ = (
        Index(
            "uq_career_goals_primary_student",
            "student_id",
            unique=True,
            postgresql_where=text('"primary" = true'),
            sqlite_where=text('"primary" = 1'),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("career_targets.id"))
    deadline: Mapped[date] = mapped_column(Date)
    weekly_hours: Mapped[int | None] = mapped_column(Integer)
    constraints: Mapped[str | None] = mapped_column(Text)
    primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
