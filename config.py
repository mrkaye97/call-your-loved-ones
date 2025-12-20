from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: Literal["DEV", "PROD", "TEST"] = "DEV"

    jwt_secret_key: SecretStr = SecretStr("your-secret-key-change-this-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7 * 52  # 1 year

    database_url: SecretStr = SecretStr(
        "postgresql://postgres:postgres@localhost:5432/call_your_loved_ones"
    )

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")


settings = Settings()
