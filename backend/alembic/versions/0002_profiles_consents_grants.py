"""创建学生档案、用户授权与导师授权表。"""

from alembic import op
import sqlalchemy as sa

revision = "0002_profiles_consents_grants"
down_revision = "0001_users_and_audits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("department", sa.String(64)),
        sa.Column("major", sa.String(64)),
        sa.Column("grade_level", sa.String(16)),
        sa.Column("gpa", sa.Float()),
        sa.Column("available_hours", sa.Float(), nullable=False, server_default="0"),
        sa.Column("constraints", sa.JSON(), nullable=False),
    )
    op.create_table(
        "user_consents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(128), nullable=False),
        sa.Column("data_scopes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "mentor_grants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mentor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("mentor_grants")
    op.drop_table("user_consents")
    op.drop_table("student_profiles")
