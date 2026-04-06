from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent.parent / '.env'),
        env_file_encoding='utf-8'
    )

    app_name: str = 'Lookback API'
    openai_api_key: str = Field(default='')
    gemini_api_key: str = Field(default='')
    database_url: str = Field(default='sqlite:///./lookback.db')
    allowed_origins: str = Field(default='*')


@lru_cache
def get_settings() -> Settings:
    return Settings()