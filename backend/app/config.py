"""
Configuration management for Luma backend
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path

# Get the backend directory (parent of app)
BACKEND_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    # Database
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Email
    RESEND_API_KEY: str
    ADMIN_EMAIL: str
    
    # Frontend
    FRONTEND_URL: str = "https://getluma.es"
    ALLOWED_ORIGINS: str = "https://getluma.es,https://lumaapp-liard.vercel.app,http://localhost:5173"
    
    # Google Form
    GOOGLE_FORM_URL: str
    
    # Emission Factors (kg CO2e per unit)
    ELECTRICITY_FACTOR_KG_PER_KWH: float = 0.231
    NATURAL_GAS_FACTOR_KG_PER_KWH: float = 0.202
    DIESEL_FACTOR_KG_PER_L: float = 2.680
    GASOLINE_FACTOR_KG_PER_L: float = 2.310
    ROAD_FREIGHT_FACTOR_KG_PER_TKM: float = 0.062
    RAIL_FREIGHT_FACTOR_KG_PER_TKM: float = 0.018
    SEA_FREIGHT_FACTOR_KG_PER_TKM: float = 0.010
    AIR_FREIGHT_FACTOR_KG_PER_TKM: float = 0.500
    
    # Natural Gas Conversion
    NATURAL_GAS_M3_TO_KWH: float = 11.63
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,csv,xlsx,xls,txt,jpg,png"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse comma-separated origins into list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse comma-separated extensions into list"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]


settings = Settings()
