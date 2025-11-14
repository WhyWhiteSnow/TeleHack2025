from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    PORT: int = 8000
    MODE: Literal["PROD", "DEV"] = "DEV"


config = Config()
