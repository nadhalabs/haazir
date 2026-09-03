from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "Haazir API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "super-secret-key-change-in-production-haazir-platform"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = "postgresql://kailasanadhg:@localhost:5432/haazir_db"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "kailasanadhg"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "haazir_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Business Rules & Pricing Defaults
    PLATFORM_COMMISSION_PERCENTAGE: float = 15.0  # 15% platform fee
    DEFAULT_TAX_PERCENTAGE: float = 5.0           # 5% tax
    DEFAULT_EMERGENCY_SURCHARGE: float = 150.0    # Fixed emergency surcharge
    DEFAULT_SERVICE_FEE: float = 30.0             # Platform convenience fee
    CANCELLATION_FEE: float = 50.0                # Base cancellation charge if cancelled after en route

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    CORS_ORIGINS: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_production_safety(self):
        if self.CORS_ORIGINS is not None:
            self.BACKEND_CORS_ORIGINS = self.CORS_ORIGINS
        if self.ENVIRONMENT.lower() == "production":
            if "change-in-production" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
                raise ValueError("Production requires a strong SECRET_KEY")
            if "localhost" in self.DATABASE_URL or "localhost" in self.REDIS_URL:
                raise ValueError("Production database and Redis URLs must be configured")
            if "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Production CORS origins must be explicit")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
