from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    force_local_storage: bool = False
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_storage_bucket: str = "book-drafts"
    notification_mode: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    notification_email_to: str = ""
    teams_webhook_url: str = ""
    export_dir: Path = Path("exports")
    data_dir: Path = Path("data")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
