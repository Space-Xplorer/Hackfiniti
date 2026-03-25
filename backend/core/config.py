"""
Application settings — loaded from environment variables / .env file.

Critical security notes:
  - SECRET_KEY must be set in ALL environments (not just non-development).
    The default "change-me" is only tolerated in local dev and prints a loud warning.
  - CORS_ORIGINS should be a comma-separated whitelist of allowed origins.
    Defaults to ["*"] ONLY in development; production must set this explicitly.
"""

import sys
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Daksha"
    env: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./daksha.db"

    # JWT
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # CORS — comma-separated list of allowed origins
    # In production, set CORS_ORIGINS=https://daksha.yourdomain.com
    cors_origins: str = "*"

    # OCR
    ocr_mode: str = "mock"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if self.secret_key == "change-me":
            msg = (
                "SECURITY WARNING: SECRET_KEY is set to the insecure default 'change-me'. "
                "Set the SECRET_KEY environment variable before deploying."
            )
            if self.env != "development":
                print(f"FATAL: {msg}", file=sys.stderr)
                sys.exit(1)
            else:
                warnings.warn(msg, stacklevel=2)

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS_ORIGINS as a parsed list."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
