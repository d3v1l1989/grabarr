from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Grabarr"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"  # Change this in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "sqlite:///./grabarr.db"
    
    # Sonarr
    SONARR_API_KEY: Optional[str] = None
    SONARR_BASE_URL: Optional[str] = None
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 