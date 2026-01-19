"""
API configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    app_name: str = "SEO Audit API"
    app_version: str = "1.0.0"
    debug: bool = False
    gemini_api_key: Optional[str] = None
    pagespeed_api_key: Optional[str] = None
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env file
    )


settings = Settings()

