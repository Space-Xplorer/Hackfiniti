import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Niyati"
    env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./daksha.db"
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    ocr_mode: str = "mock"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context) -> None:
        if self.env != "development" and self.secret_key == "change-me":
            print("FATAL: SECRET_KEY must be changed in non-development environments.", file=sys.stderr)
            sys.exit(1)


settings = Settings()
