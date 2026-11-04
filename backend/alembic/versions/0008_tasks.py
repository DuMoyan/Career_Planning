"""扩展任务状态并创建幂等打卡表。"""

import sqlalchemy as sa

from alembic import op

revision = "0008_tasks"
down_revision = "0007_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("growth_tasks", sa.Column("status_reason", sa.Text()))
    op.execute("UPDATE growth_tasks SET status = 'todo' WHERE status = 'pending'")
    op.alter_column("growth_tasks", "status", server_default="todo")
    op.create_table(
        "task_checkins",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            sa.Uuid(),
            sa.ForeignKey("growth_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("actual_hours", sa.Float(), nullable=False),
        sa.Column("proof_url", sa.String(2048)),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("actual_hours > 0", name="ck_task_checkin_actual_hours"),
        sa.UniqueConstraint("student_id", "idempotency_key", name="uq_task_checkin_idempotency"),
    )
    op.create_index("ix_task_checkins_student_id", "task_checkins", ["student_id"])
    op.create_index("ix_task_checkins_task_id", "task_checkins", ["task_id"])


def downgrade() -> None:
    op.drop_table("task_checkins")
    op.execute("UPDATE growth_tasks SET status = 'pending' WHERE status = 'todo'")
    op.alter_column("growth_tasks", "status", server_default="pending")
    op.drop_column("growth_tasks", "status_reason")
