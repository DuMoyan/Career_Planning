from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AssessmentScaleModel(Base):
    __tablename__ = "assessment_scales"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(32))
    version: Mapped[str] = mapped_column(String(32))
    scoring_version: Mapped[str] = mapped_column(String(32))
    interpretation_version: Mapped[str] = mapped_column(String(32))
    license_note: Mapped[str] = mapped_column(String(128))


class AssessmentItemModel(Base):
    __tablename__ = "assessment_items"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scale_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("assessment_scales.id", ondelete="CASCADE"), index=True
    )
    dimension: Mapped[str] = mapped_column(String(64))
    prompt: Mapped[str] = mapped_column(Text)


class AssessmentRecordModel(Base):
    __tablename__ = "assessment_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    scale_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("assessment_scales.id"))
    scale_version: Mapped[str] = mapped_column(String(32))
    answers: Mapped[dict] = mapped_column(JSON)
    dimension_scores: Mapped[dict] = mapped_column(JSON)
    visibility: Mapped[str] = mapped_column(String(16), default="private")
    idempotency_key: Mapped[str] = mapped_column(String(128))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AssessmentProgressModel(Base):
    __tablename__ = "assessment_progress"

    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    scale_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("assessment_scales.id", ondelete="CASCADE"), primary_key=True
    )
    answers: Mapped[dict] = mapped_column(JSON)
