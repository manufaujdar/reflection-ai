from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="REFLECTION_")

    app_name: str = "Reflection AI"
    database_url: str = "sqlite:///./data/reflection.db"
    model_provider: str = "mock"
    model_name: str = "local-development-model"
    model_base_url: str | None = None
    model_api_key: str | None = None
    training_min_events: int = 20
    profile_refresh_events: int = 5
    chat_style_min_samples: int = 3
    chat_history_messages: int = 20
    memory_backend: str | None = None
    memory_base_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
