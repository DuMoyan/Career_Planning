import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.models.audit import AuditLog  # noqa: F401
from app.models.assessment import (  # noqa: F401
    AssessmentItemModel,
    AssessmentProgressModel,
    AssessmentRecordModel,
    AssessmentScaleModel,
)
from app.models.base import Base
from app.models.consent import UserConsent  # noqa: F401
from app.models.competency import CompetencyEvidence, CompetencyProfile  # noqa: F401
from app.models.goal import CareerGoal  # noqa: F401
from app.models.mentor import MentorGrantModel  # noqa: F401
from app.models.profile import StudentProfile  # noqa: F401
from app.models.preference import CareerPreference  # noqa: F401
from app.models.resume import ResumeFile  # noqa: F401
from app.models.target import CareerTarget, CareerTargetRequirement  # noqa: F401
from app.models.user import RefreshToken, User  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())

