from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+psycopg://aiportal:change_me@db:5432/aiportal"

    # JWT
    jwt_secret: str = "change_me_to_long_random"
    jwt_expire_minutes: int = 120
    jwt_algorithm: str = "HS256"

    # LLM Provider (openai, azure_openai, anthropic, google)
    llm_provider: str = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Azure OpenAI (optional)
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = ""
    azure_openai_api_version: str = "2024-02-15-preview"

    # Anthropic Claude (optional)
    anthropic_api_key: str = ""

    # Google AI (optional)
    google_api_key: str = ""

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
