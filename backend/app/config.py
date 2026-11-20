from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JOBRADAR_", env_file=".env", extra="ignore")

    env: str = "development"
    database_url: str = "sqlite+pysqlite:///./jobradar.db"
    secret: str = "dev-only-change-me-not-for-production-use"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    sample_source: bool = True
    crawl_interval_minutes: int = 180
    scheduler: bool = True
    storage_dir: str = "./storage"
    public_api_url: str = "http://localhost:8000"
    resend_api_key: str = ""
    email_from: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_bucket: str = "cvs"
    playwright: bool = False
    chrome_path: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def storage_path(self) -> Path:
        return Path(self.storage_dir)

    @property
    def email_configured(self) -> bool:
        return bool(self.resend_api_key and self.email_from)

    @property
    def supabase_storage_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key and self.supabase_bucket)


def get_settings() -> Settings:
    return Settings()
