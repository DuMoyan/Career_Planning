from collections.abc import Mapping

from alembic.config import Config


def apply_database_url_override(config: Config, environ: Mapping[str, str]) -> None:
    """让容器和部署环境通过 DATABASE_URL 指定迁移数据库。"""

    database_url = environ.get("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
