"""创建职业目标、岗位要求与学生目标表。"""

import sqlalchemy as sa

from alembic import op

revision = "0005_targets_goals"
down_revision = "0004_competencies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "career_targets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("verified_at", sa.Date(), nullable=False),
        sa.Column("interests", sa.JSON(), nullable=False),
        sa.Column("values", sa.JSON(), nullable=False),
    )
    op.create_index("ix_career_targets_name", "career_targets", ["name"])
    op.create_index("ix_career_targets_category", "career_targets", ["category"])
    op.create_table(
        "career_target_requirements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "target_id",
            sa.Uuid(),
            sa.ForeignKey("career_targets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("competency_code", sa.String(64), nullable=False),
        sa.Column("required_level", sa.Integer(), nullable=False),
        sa.Column("hard", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("verified_at", sa.Date(), nullable=False),
        sa.CheckConstraint("required_level BETWEEN 1 AND 4", name="ck_target_requirement_level"),
    )
    op.create_index(
        "ix_career_target_requirements_target_id",
        "career_target_requirements",
        ["target_id"],
    )
    op.create_index(
        "ix_career_target_requirements_competency_code",
        "career_target_requirements",
        ["competency_code"],
    )
    op.create_table(
        "career_goals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_id", sa.Uuid(), sa.ForeignKey("career_targets.id"), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("weekly_hours", sa.Integer()),
        sa.Column("constraints", sa.Text()),
        sa.Column("primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "weekly_hours IS NULL OR weekly_hours BETWEEN 1 AND 168",
            name="ck_career_goal_weekly_hours",
        ),
    )
    op.create_index("ix_career_goals_student_id", "career_goals", ["student_id"])
    op.create_index(
        "uq_career_goals_primary_student",
        "career_goals",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text('"primary" = true'),
    )


def downgrade() -> None:
    op.drop_table("career_goals")
    op.drop_table("career_target_requirements")
    op.drop_table("career_targets")
