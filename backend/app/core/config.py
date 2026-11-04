from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量加载的应用配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    timezone: str = "Asia/Shanghai"
    database_url: str
    redis_url: str
    jwt_secret: str = Field(min_length=32)
    jwt_access_minutes: int = Field(default=30, gt=0)
    upload_max_bytes: int = Field(default=10_485_760, gt=0)
    model_base_url: str | None = None
    model_api_key: str | None = None
    model_name: str | None = None
    model_timeout_seconds: int = Field(default=20, gt=0)
