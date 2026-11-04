"""创建幂等周报与调整反馈表。"""

import sqlalchemy as sa

from alembic import op

revision = "0009_weekly_reports"
down_revision = "0008_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("advice", sa.Text(), nullable=False),
        sa.Column("advice_mode", sa.String(16), nullable=False),
        sa.Column("response_action", sa.String(16)),
        sa.Column("response_text", sa.Text()),
        sa.Column("replan_run_id", sa.Uuid(), sa.ForeignKey("ai_planning_runs.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "week_start", name="uq_weekly_report_student_week"),
    )
    op.create_index("ix_weekly_reports_student_id", "weekly_reports", ["student_id"])


def downgrade() -> None:
    op.drop_table("weekly_reports")
