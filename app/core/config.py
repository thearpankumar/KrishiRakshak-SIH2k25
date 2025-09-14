from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://n8n:n8npassword@localhost:5432/krishi_officer")
    database_url_sync: str = os.getenv("DATABASE_URL_SYNC", "postgresql://n8n:n8npassword@localhost:5432/krishi_officer")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://:redispassword@localhost:6379/1")
    
    # Qdrant Vector Database
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_collection_name: str = os.getenv("QDRANT_COLLECTION", "qa_embeddings")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

    # N8N Integration
    n8n_webhook_base_url: str = os.getenv("N8N_WEBHOOK_BASE_URL", "http://n8n:5678/webhook")
    n8n_api_base_url: str = os.getenv("N8N_API_BASE_URL", "http://n8n:5678/api/v1")
    n8n_api_key: Optional[str] = os.getenv("N8N_API_KEY")

    # External APIs
    openweather_api_key: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    data_gov_in_api_key: Optional[str] = os.getenv("DATA_GOV_IN_API_KEY")

    # Workflow Configuration
    enable_ai_enhancement: bool = os.getenv("ENABLE_AI_ENHANCEMENT", "true").lower() == "true"
    enable_content_moderation: bool = os.getenv("ENABLE_CONTENT_MODERATION", "true").lower() == "true"
    enable_smart_notifications: bool = os.getenv("ENABLE_SMART_NOTIFICATIONS", "true").lower() == "true"
    enable_weather_sync: bool = os.getenv("ENABLE_WEATHER_SYNC", "true").lower() == "true"

    # File uploads
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # CORS
    @property
    def allowed_origins(self) -> list[str]:
        origins_str = os.getenv("ALLOWED_ORIGINS", "")
        if origins_str:
            return [origin.strip() for origin in origins_str.split(',') if origin.strip()]
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
        ]
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"  # Ignore extra environment variables
    }


settings = Settings()