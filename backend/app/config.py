from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    app_name: str = 'Lookback API'
    openai_api_key: str = Field(default='')
    gemini_api_key: str = Field(default='')
    database_url: str = Field(default='sqlite:///./lookback.db')


settings = Settings()
