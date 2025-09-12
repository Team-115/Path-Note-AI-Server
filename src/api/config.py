from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API
    api_version: str = "v1"
    api_title: str = "Travel AI Search API"
    
    # Database - PostgreSQL with docker-compose
    database_url: str = "postgresql+asyncpg://pathnote_user:12345@localhost:5432/pathnote"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False
    
    # Legacy Supabase settings (for compatibility)
    supabase_url: str = "http://localhost:5432"
    supabase_key: str = "local-key"
    supabase_service_key: str = "local-service-key"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Model
    model_name: str = "BM-K/KoSimCSE-roberta"
    model_cache_dir: str = "./models"
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    
    # Environment
    environment: str = "development"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "protected_namespaces": ('settings_',)
    }

@lru_cache()
def get_settings():
    return Settings()
