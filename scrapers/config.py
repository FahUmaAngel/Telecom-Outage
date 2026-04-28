"""
Configuration management.
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/telecom_outage"
    SCRAPER_INTERVAL_MINUTES: int = 5
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: Optional[str] = None
    ALLOWED_ORIGINS: Optional[str] = None
    APP_ENV: str = "development"
    ADMIN_USERNAME: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
