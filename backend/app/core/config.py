"""
Application configuration and settings.
"""
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # App settings
    APP_NAME: str = Field(default="Stock Predictor")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")

    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///./test.db")
    DATABASE_ECHO: bool = Field(default=False)
    DATABASE_POOL_SIZE: int = Field(default=20)
    DATABASE_POOL_RECYCLE: int = Field(default=3600)
    
    def model_post_init(self, __context):
        """Convert relative database path to absolute path."""
        url = self.DATABASE_URL
        
        # If it's a relative SQLite path, convert to absolute
        if url.startswith("sqlite:///./"):
            file_path = url.replace("sqlite:///./", "")
            project_root = Path(__file__).parent.parent.parent
            absolute_path = project_root / file_path
            self.DATABASE_URL = f"sqlite:///{absolute_path}"

    # Server settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=False)

    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]
    )
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"])

    # Security settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # External APIs
    ALPHA_VANTAGE_API_KEY: str = Field(default="https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=TCS.BSE&apikey=ALPHA_VANTAGE_API_KEY")
    NEWSAPI_API_KEY: str = Field(default="https://newsapi.org/v2/everything?q=Indian+stock+market&sortBy=publishedAt&language=en&apiKey=NEWSAPI_API_KEY")
    POLYGON_API_KEY: str = Field(default="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-02-01?apiKey=POLYGON_API_KEY")

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


settings = Settings()
