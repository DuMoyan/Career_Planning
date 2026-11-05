from alembic.config import Config

from app.core.migration_config import apply_database_url_override


def test_database_url_environment_overrides_alembic_default() -> None:
    config = Config()
    config.set_main_option(
        "sqlalchemy.url",
        "postgresql+asyncpg://career:career@localhost:5432/career",
    )

    apply_database_url_override(
        config,
        {"DATABASE_URL": "postgresql+asyncpg://career:career@postgres/career"},
    )

    assert (
        config.get_main_option("sqlalchemy.url")
        == "postgresql+asyncpg://career:career@postgres/career"
    )
