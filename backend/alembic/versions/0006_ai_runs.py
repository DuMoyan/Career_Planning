"""创建可追踪的规划智能体运行记录。"""

import sqlalchemy as sa

from alembic import op

revision = "0006_ai_runs"
down_revision = "0005_targets_goals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_planning_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("parent_run_id", sa.Uuid(), sa.ForeignKey("ai_planning_runs.id")),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("generation_mode", sa.String(16)),
        sa.Column("fallback_reason", sa.String(64)),
        sa.Column("service_version", sa.String(64), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("prompt_version", sa.String(64), nullable=False),
        sa.Column("input_references", sa.JSON(), nullable=False),
        sa.Column("plan_snapshot", sa.JSON()),
        sa.Column("validation_result", sa.JSON()),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("confirmation_status", sa.String(24), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ai_planning_runs_student_id", "ai_planning_runs", ["student_id"])
    op.create_index("ix_ai_planning_runs_status", "ai_planning_runs", ["status"])
    op.create_index(
        "uq_ai_planning_runs_active_student",
        "ai_planning_runs",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
    )


def downgrade() -> None:
    op.drop_table("ai_planning_runs")
