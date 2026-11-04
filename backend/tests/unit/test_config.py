import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_rejects_missing_jwt_secret() -> None:
    """删除 JWT 必填约束时必须失败，否则服务可能用空密钥签发令牌。"""
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            database_url="postgresql+asyncpg://user:pass@localhost/career",
            redis_url="redis://localhost:6379/0",
        )


def test_settings_use_required_mvp_defaults() -> None:
    """默认时区或上传上限变化时必须失败，避免周报错周或超限文件进入解析。"""
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://user:pass@localhost/career",
        redis_url="redis://localhost:6379/0",
        jwt_secret="a" * 32,
    )

    assert settings.timezone == "Asia/Shanghai"
    assert settings.upload_max_bytes == 10_485_760

