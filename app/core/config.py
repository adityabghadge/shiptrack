from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "ShipTrack"
    env: str = "local"
    log_level: str = "INFO"

    # Security
    api_key: str = "change-me"

    # Services (we'll use these soon)
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    slack_webhook_url: str | None = None


settings = Settings()