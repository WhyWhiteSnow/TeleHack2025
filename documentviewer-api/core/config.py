from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    VERSION: str = "0.1.0"
    MODE: Literal["PROD", "DEV"] = "DEV"
    HOST: str = "0.0.0.0"
    PORT: int = 8000


config = Config()
