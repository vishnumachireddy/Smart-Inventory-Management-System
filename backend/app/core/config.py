import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "StockSense"
    PROJECT_DESCRIPTION: str = "Smart Inventory & Expiry Tracker for Small Retailers"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "stocksense-super-secret-production-key-change-in-env-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database: Neon Serverless PostgreSQL is mandatory for primary persistence
    # Format: postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Inventory & Expiry Business Defaults
    DEFAULT_NEAR_EXPIRY_DAYS: int = 30
    DEFAULT_LEAD_TIME_DAYS: int = 7
    DEFAULT_SAFETY_STOCK_FACTOR: float = 1.5
    CURRENCY_CODE: str = "INR"
    CURRENCY_SYMBOL: str = "₹"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def is_neon_configured(self) -> bool:
        """Verify if DATABASE_URL is configured and not the sample placeholder."""
        if not self.DATABASE_URL or not self.DATABASE_URL.strip():
            return False
        placeholder = "postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require"
        if self.DATABASE_URL.strip() == placeholder:
            return False
        return True


settings = Settings()
