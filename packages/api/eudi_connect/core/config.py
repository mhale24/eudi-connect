from typing import Any

# Auto-load .env.test or .env before settings instantiation
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env.test'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        # fallback to .env
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
except ImportError:
    pass

from pydantic import AnyHttpUrl, EmailStr, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API configuration settings."""
    model_config = SettingsConfigDict(
        env_file=['.env', '.env.test'],
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # API settings
    PROJECT_NAME: str = "EUDI-Connect"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: SecretStr
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database settings
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str
    DATABASE_URI: PostgresDsn | None = None

    @field_validator("DATABASE_URI", mode="before")
    def assemble_db_uri(cls, v: str | None, values: Any) -> str:
        """Assemble database URI from components."""
        if v:
            return v
        
        if isinstance(values, dict):
            user = values.get("POSTGRES_USER")
            password = values.get("POSTGRES_PASSWORD")
            host = values.get("POSTGRES_HOST")
            port = values.get("POSTGRES_PORT")
            db = values.get("POSTGRES_DB")
        else:
            user = values.data.get("POSTGRES_USER")
            password = values.data.get("POSTGRES_PASSWORD")
            host = values.data.get("POSTGRES_HOST")
            port = values.data.get("POSTGRES_PORT")
            db = values.data.get("POSTGRES_DB")

        if not all([user, password, host, port, db]):
            return ""
        
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=user,
            password=password.get_secret_value() if password else "",
            host=host,
            port=int(port),
            path=db,
        )

    # CORS settings
    CORS_ORIGINS: list[AnyHttpUrl] = []

    # Email settings
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    # Telemetry settings
    TELEMETRY_ENABLED: bool = False
    OTLP_ENDPOINT: str | None = None

    # Stripe settings
    STRIPE_API_KEY: SecretStr | None = None
    STRIPE_WEBHOOK_SECRET: SecretStr | None = None

    # DIDKit settings
    DIDKIT_KEY_PATH: str | None = None


# Create settings instance
settings = Settings()
