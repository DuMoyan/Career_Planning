"""创建导师计划版本评论表。"""

import sqlalchemy as sa

from alembic import op

revision = "0010_mentor_comments"
down_revision = "0009_weekly_reports"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mentor_plan_comments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "mentor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "plan_version_id",
            sa.Uuid(),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_mentor_plan_comments_mentor_id", "mentor_plan_comments", ["mentor_id"])
    op.create_index("ix_mentor_plan_comments_student_id", "mentor_plan_comments", ["student_id"])
    op.create_index(
        "ix_mentor_plan_comments_plan_version_id", "mentor_plan_comments", ["plan_version_id"]
    )


def downgrade() -> None:
    op.drop_table("mentor_plan_comments")
