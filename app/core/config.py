from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Thantrajnana Unified API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./thantrajnana.db"
    secret_key: str = "change-this-secret-before-production"
    access_token_expire_minutes: int = 1440

    frontend_url: str = "http://localhost:3000"
    student_frontend_url: str = "http://localhost:3001"
    teacher_frontend_url: str = "http://localhost:3002"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3002,http://127.0.0.1:3002"
    environment: str = "development"

    arduino_cli_path: str = "arduino-cli"
    arduino_cli_timeout_seconds: int = Field(default=180, ge=10, le=900)
    enable_device_upload: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        values = [self.frontend_url, self.student_frontend_url, self.teacher_frontend_url]
        values.extend(item.strip() for item in self.cors_origins.split(","))
        return list(dict.fromkeys(item for item in values if item))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
