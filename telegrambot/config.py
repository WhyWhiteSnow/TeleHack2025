from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    MODE: Literal["PROD", "DEV"] = "DEV"
    BOT_TOKEN: SecretStr = Field(..., env="BOT_TOKEN")
    SERVER_URL: str


config = Config()
