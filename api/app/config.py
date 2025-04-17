from pydantic import BaseSettings, validator
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Grabarr"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # API Key
    API_KEY: str
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/grabarr.db"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3456"]
    
    # Sonarr
    SONARR_API_KEY: Optional[str] = None
    SONARR_BASE_URL: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 300  # 5 minutes
    MAX_REQUESTS_PER_WINDOW: int = 100
    
    @validator("API_KEY")
    def validate_api_key(cls, v):
        if len(v) < 16:
            raise ValueError("API_KEY must be at least 16 characters long")
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings() 