"""创建计划版本与激活时生成的成长任务。"""

import sqlalchemy as sa

from alembic import op

revision = "0007_plans"
down_revision = "0006_ai_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "career_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_career_plans_student_id", "career_plans", ["student_id"])
    op.create_table(
        "plan_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "career_plan_id",
            sa.Uuid(),
            sa.ForeignKey("career_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ai_run_id", sa.Uuid(), sa.ForeignKey("ai_planning_runs.id"), nullable=False),
        sa.Column("parent_version_id", sa.Uuid(), sa.ForeignKey("plan_versions.id")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("career_plan_id", "version", name="uq_plan_version_number"),
    )
    op.create_index("ix_plan_versions_career_plan_id", "plan_versions", ["career_plan_id"])
    op.create_index("ix_plan_versions_status", "plan_versions", ["status"])
    op.create_index(
        "uq_plan_versions_active_career_plan",
        "plan_versions",
        ["career_plan_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "growth_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_version_id",
            sa.Uuid(),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_task_id", sa.Uuid(), sa.ForeignKey("growth_tasks.id")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("competency_code", sa.String(64), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("weekly_hours", sa.Float(), nullable=False),
        sa.Column("source_refs", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_growth_tasks_student_id", "growth_tasks", ["student_id"])
    op.create_index("ix_growth_tasks_plan_version_id", "growth_tasks", ["plan_version_id"])


def downgrade() -> None:
    op.drop_table("growth_tasks")
    op.drop_table("plan_versions")
    op.drop_table("career_plans")
