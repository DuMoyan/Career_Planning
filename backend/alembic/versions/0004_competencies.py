"""创建简历、能力证据与画像版本表。"""

from alembic import op
import sqlalchemy as sa

revision = "0004_competencies"
down_revision = "0003_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_files",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_key", sa.String(128), nullable=False, unique=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("candidates", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "competency_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resume_files.id")),
        sa.Column("competency_code", sa.String(64), nullable=False),
        sa.Column("demonstrated_level", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_deleted", sa.Boolean(), nullable=False),
        sa.Column("confirmed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("demonstrated_level BETWEEN 1 AND 4", name="ck_evidence_level"),
    )
    op.create_table(
        "competency_profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("dimensions", sa.JSON(), nullable=False),
        sa.Column("data_completeness", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "version", name="uq_competency_profile_version"),
    )


def downgrade() -> None:
    op.drop_table("competency_profiles")
    op.drop_table("competency_evidence")
    op.drop_table("resume_files")
