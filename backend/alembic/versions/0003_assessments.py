"""创建版本化测评与职业偏好表。"""

from alembic import op
import sqlalchemy as sa

revision = "0003_assessments"
down_revision = "0002_profiles_consents_grants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assessment_scales",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("scoring_version", sa.String(32), nullable=False),
        sa.Column("interpretation_version", sa.String(32), nullable=False),
        sa.Column("license_note", sa.String(128), nullable=False),
        sa.UniqueConstraint("code", "version", name="uq_assessment_scale_version"),
    )
    op.create_table(
        "assessment_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scale_id", sa.Uuid(), sa.ForeignKey("assessment_scales.id", ondelete="CASCADE")),
        sa.Column("dimension", sa.String(64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
    )
    op.create_table(
        "assessment_progress",
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("scale_id", sa.Uuid(), sa.ForeignKey("assessment_scales.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("answers", sa.JSON(), nullable=False),
    )
    op.create_table(
        "assessment_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scale_id", sa.Uuid(), sa.ForeignKey("assessment_scales.id"), nullable=False),
        sa.Column("scale_version", sa.String(32), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("dimension_scores", sa.JSON(), nullable=False),
        sa.Column("visibility", sa.String(16), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "idempotency_key", name="uq_assessment_idempotency"),
    )
    op.create_table(
        "career_preferences",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interest_profile", sa.JSON(), nullable=False),
        sa.Column("value_ranking", sa.JSON(), nullable=False),
        sa.Column("work_environment", sa.JSON(), nullable=False),
        sa.Column("self_reflection", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("career_preferences")
    op.drop_table("assessment_records")
    op.drop_table("assessment_progress")
    op.drop_table("assessment_items")
    op.drop_table("assessment_scales")
