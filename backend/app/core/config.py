from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NeetCode SRS"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/neetcode_auto"
    api_key: str = "dev-api-key-change-me"
    resend_api_key: str = ""
    email_from: str = "NeetCode SRS <onboarding@resend.dev>"
    email_to: str = "owenfisher46@gmail.com"
    timezone: str = "America/Vancouver"
    srs_config_path: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
