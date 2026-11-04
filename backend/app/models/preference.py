from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CareerPreference(Base):
    __tablename__ = "career_preferences"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    interest_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    value_ranking: Mapped[dict] = mapped_column(JSON, default=dict)
    work_environment: Mapped[dict] = mapped_column(JSON, default=dict)
    self_reflection: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

