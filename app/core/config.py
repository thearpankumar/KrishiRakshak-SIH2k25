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