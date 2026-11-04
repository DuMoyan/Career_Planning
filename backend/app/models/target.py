from datetime import date
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CareerTarget(Base):
    __tablename__ = "career_targets"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(255))
    verified_at: Mapped[date] = mapped_column(Date)
    interests: Mapped[list] = mapped_column(JSON)
    values: Mapped[list] = mapped_column(JSON)


class CareerTargetRequirement(Base):
    __tablename__ = "career_target_requirements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    target_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("career_targets.id", ondelete="CASCADE"), index=True
    )
    competency_code: Mapped[str] = mapped_column(String(64), index=True)
    required_level: Mapped[int] = mapped_column(Integer)
    hard: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(255))
    verified_at: Mapped[date] = mapped_column(Date)
