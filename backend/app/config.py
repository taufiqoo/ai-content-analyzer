import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://pipeline_user:pipeline_pass@localhost:5432/content_pipeline"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # Gemini (Google AI Studio)
    GEMINI_API_KEY: str = ""

    # OpenRouter
    OPENROUTER_API_KEY: str = ""

    # Twitter
    TWITTER_USERNAME: str = ""
    TWITTER_PASSWORD: str = ""
    TWITTER_AUTH_TOKEN: str = ""
    TWITTER_CT0: str = ""

    # App
    SECRET_KEY: str = "dev-secret-key"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = str(ROOT_DIR / ".env")
        extra = "ignore"


settings = Settings()
