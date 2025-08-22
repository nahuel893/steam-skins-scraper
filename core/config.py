"""
Configuración centralizada para el Steam Skin Scraper.
Utiliza variables de entorno con valores por defecto seguros.
"""
import os
from typing import Final
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL: Final[str] = os.getenv("DATABASE_URL", "sqlite:///database.db")
DATABASE_ECHO: Final[bool] = os.getenv("DATABASE_ECHO", "False").lower() == "true"

# Steam API Configuration  
STEAM_APP_ID: Final[int] = int(os.getenv("STEAM_APP_ID", "730"))  # CS2/CS:GO
STEAM_CURRENCY: Final[int] = int(os.getenv("STEAM_CURRENCY", "1"))  # USD
STEAM_BASE_URL: Final[str] = "https://steamcommunity.com"
STEAM_LIST_URL: Final[str] = "https://steamcommunity.com/market/search/render/"

# Rate Limiting Configuration - Configuración conservadora para evitar 429s
MAX_REQUESTS_BEFORE_THROTTLE: Final[int] = int(os.getenv("MAX_REQUESTS_BEFORE_THROTTLE", "1"))
THROTTLE_WAIT_MIN_SECONDS: Final[int] = int(os.getenv("THROTTLE_WAIT_MIN_SECONDS", "20"))  # 20 seconds entre requests
REQUEST_TIMEOUT: Final[int] = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
BACKOFF_BASE_SECONDS: Final[int] = int(os.getenv("BACKOFF_BASE_SECONDS", "30"))  # Backoff inicial más agresivo
JITTER_PERCENTAGE: Final[float] = float(os.getenv("JITTER_PERCENTAGE", "0.3"))  # 30% jitter

# Scraping Configuration
BATCH_SIZE: Final[int] = int(os.getenv("BATCH_SIZE", "10"))
MAX_RETRIES: Final[int] = int(os.getenv("MAX_RETRIES", "3"))

# Logging Configuration
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_MAX_BYTES: Final[int] = int(os.getenv("LOG_MAX_BYTES", "5000000"))  # 5MB
LOG_BACKUP_COUNT: Final[int] = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# User Agents reales para rotación
USER_AGENTS: Final[list] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

DEFAULT_USER_AGENT: Final[str] = os.getenv("USER_AGENT", USER_AGENTS[0])

class Config:
    """
    Clase de configuración que valida y expone todas las configuraciones.
    Implementa el patrón Singleton para garantizar una única instancia.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._validate_config()
        return cls._instance
    
    def _validate_config(self) -> None:
        """Valida que la configuración sea correcta."""
        if STEAM_APP_ID <= 0:
            raise ValueError("STEAM_APP_ID debe ser un entero positivo")
        if MAX_REQUESTS_BEFORE_THROTTLE <= 0:
            raise ValueError("MAX_REQUESTS_BEFORE_THROTTLE debe ser positivo")
        if BATCH_SIZE <= 0:
            raise ValueError("BATCH_SIZE debe ser positivo")
    
    @property
    def database_url(self) -> str:
        return DATABASE_URL
    
    @property
    def steam_config(self) -> dict:
        return {
            "app_id": STEAM_APP_ID,
            "currency": STEAM_CURRENCY,
            "base_url": STEAM_BASE_URL,
            "timeout": REQUEST_TIMEOUT,
            "user_agent": DEFAULT_USER_AGENT,
            "list_url": STEAM_LIST_URL
        }
    
    @property
    def rate_limit_config(self) -> dict:
        return {
            "max_requests": MAX_REQUESTS_BEFORE_THROTTLE,
            "wait_seconds": THROTTLE_WAIT_MIN_SECONDS,
            "max_retries": MAX_RETRIES,
            "backoff_base": BACKOFF_BASE_SECONDS,
            "jitter_percentage": JITTER_PERCENTAGE
        }
    
    @property
    def user_agents(self) -> list:
        return USER_AGENTS

# Instancia global de configuración
config = Config()
