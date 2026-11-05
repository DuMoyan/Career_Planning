from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CareerPlan(Base):
    __tablename__ = "career_plans"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PlanVersion(Base):
    __tablename__ = "plan_versions"
    __table_args__ = (
        UniqueConstraint("career_plan_id", "version", name="uq_plan_version_number"),
        Index(
            "uq_plan_versions_active_career_plan",
            "career_plan_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    career_plan_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("career_plans.id", ondelete="CASCADE"), index=True
    )
    ai_run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ai_planning_runs.id"))
    parent_version_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("plan_versions.id"), nullable=True
    )
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), index=True)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlanActivationRequest(Base):
    __tablename__ = "plan_activation_requests"
    __table_args__ = (
        UniqueConstraint("student_id", "idempotency_key", name="uq_plan_activation_student_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    idempotency_key: Mapped[str] = mapped_column(String(128))
    version_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("plan_versions.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
