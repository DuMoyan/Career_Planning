"""创建计划激活幂等请求表。"""

import sqlalchemy as sa

from alembic import op

revision = "0011_plan_activation_requests"
down_revision = "0010_mentor_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plan_activation_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column(
            "version_id",
            sa.Uuid(),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "student_id", "idempotency_key", name="uq_plan_activation_student_key"
        ),
    )
    op.create_index(
        "ix_plan_activation_requests_student_id",
        "plan_activation_requests",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_table("plan_activation_requests")
