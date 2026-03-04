"""
Application configuration and settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # App settings
    APP_NAME: str = Field(default="Stock Predictor")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Database settings
    DATABASE_URL: str = Field(default="postgresql://user:password@localhost:5432/stock_predictor")
    DATABASE_ECHO: bool = Field(default=False)
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_POOL_RECYCLE: int = Field(default=3600)

    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=False)

    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"]
    )
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"])

    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # External APIs
    ALPHA_VANTAGE_API_KEY: str = Field(default="https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=TCS.BSE&apikey=HSZRNW95MJ9CMO5Y")
    NEWSAPI_API_KEY: str = Field(default="https://newsapi.org/v2/everything?q=Indian+stock+market&sortBy=publishedAt&language=en&apiKey=2e3320bb1d764c42ad0b8fc78fe5a44d")
    POLYGON_API_KEY: str = Field(default="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01?apiKey=tfBFG7EkCZXxi1PArUw7Ln9EmJbVwteV")

    # ML Model paths
    PRICE_PREDICTION_MODEL_PATH: str = Field(default="artifacts/models/price_predictor.pkl")
    RECOMMENDATION_MODEL_PATH: str = Field(default="artifacts/models/recommendation.pkl")
    PRICE_SCALER_PATH: str = Field(default="artifacts/scalers/price_scaler.pkl")

    # Cache settings
    REDIS_URL: str = Field(default="redis://localhost:6379")
    CACHE_EXPIRY_HOURS: int = Field(default=24)

    # Logging settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="logs/app.log")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
