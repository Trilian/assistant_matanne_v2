"""
Configuration centralisée de l'application
Utilise Pydantic Settings pour la validation
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, field_validator
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Configuration de l'application"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ===================================
    # APPLICATION
    # ===================================

    APP_NAME: str = "Assistant MaTanne v2"
    APP_VERSION: str = "2.0.0"
    ENV: str = Field(default="development", pattern="^(development|production|test)$")
    DEBUG: bool = Field(default=True)
    SECRET_KEY: str = Field(default="dev-secret-key-CHANGE-IN-PRODUCTION")

    # ===================================
    # DATABASE
    # ===================================

    # PostgreSQL
    POSTGRES_USER: str = Field(default="matanne")
    POSTGRES_PASSWORD: str = Field(default="matanne_secret")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="matanne")

    # URL construite automatiquement
    DATABASE_URL: str = Field(default="")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info) -> str:
        """Construit l'URL de connexion PostgreSQL"""
        if v:
            return v

        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )

    # ===================================
    # REDIS (Cache & Celery)
    # ===================================

    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: Optional[str] = Field(default=None)

    REDIS_URL: str = Field(default="")

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: Optional[str], info) -> str:
        """Construit l'URL Redis"""
        if v:
            return v

        values = info.data
        password = values.get('REDIS_PASSWORD')
        auth = f":{password}@" if password else ""

        return (
            f"redis://{auth}{values.get('REDIS_HOST')}:"
            f"{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        )

    # ===================================
    # OLLAMA (IA)
    # ===================================

    OLLAMA_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama2")
    OLLAMA_TIMEOUT: int = Field(default=30)  # secondes

    # Paramètres par défaut de l'IA
    AI_DEFAULT_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    AI_DEFAULT_MAX_TOKENS: int = Field(default=500, ge=1, le=2000)
    AI_CACHE_TTL: int = Field(default=300)  # secondes (5 min)

    # ===================================
    # API MÉTÉO
    # ===================================

    WEATHER_API_KEY: Optional[str] = Field(default=None)
    WEATHER_API_URL: str = Field(default="https://api.openweathermap.org/data/2.5")
    WEATHER_CITY: str = Field(default="Clermont-Ferrand")
    WEATHER_COUNTRY: str = Field(default="FR")
    WEATHER_UNITS: str = Field(default="metric")

    # ===================================
    # STREAMLIT
    # ===================================

    STREAMLIT_SERVER_PORT: int = Field(default=8501)
    STREAMLIT_SERVER_ADDRESS: str = Field(default="0.0.0.0")
    STREAMLIT_THEME: str = Field(default="light")

    # ===================================
    # CHEMINS
    # ===================================

    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    DATA_DIR: Path = Field(default_factory=lambda: Path("data"))
    BACKUP_DIR: Path = Field(default_factory=lambda: Path("data/backups"))
    LOGS_DIR: Path = Field(default_factory=lambda: Path("logs"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Créer les répertoires s'ils n'existent pas
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # ===================================
    # SÉCURITÉ
    # ===================================

    ALLOWED_HOSTS: list[str] = Field(default=["localhost", "127.0.0.1", "*.streamlit.app"])
    CORS_ORIGINS: list[str] = Field(default=["*"])

    # ===================================
    # CELERY (Tâches asynchrones)
    # ===================================

    CELERY_BROKER_URL: Optional[str] = Field(default=None)
    CELERY_RESULT_BACKEND: Optional[str] = Field(default=None)

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def set_celery_broker(cls, v: Optional[str], info) -> str:
        """Utilise Redis comme broker Celery"""
        if v:
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def set_celery_backend(cls, v: Optional[str], info) -> str:
        """Utilise Redis comme backend de résultats"""
        if v:
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    # ===================================
    # FONCTIONNALITÉS
    # ===================================

    # Modules activés
    ENABLE_AI: bool = Field(default=True)
    ENABLE_WEATHER: bool = Field(default=True)
    ENABLE_CALENDAR_SYNC: bool = Field(default=False)
    ENABLE_NOTIFICATIONS: bool = Field(default=True)

    # Tâches automatiques (heures)
    AUTO_TASK_MORNING: str = Field(default="08:00")
    AUTO_TASK_EVENING: str = Field(default="18:00")
    AUTO_BACKUP_TIME: str = Field(default="02:00")

    # Limites
    MAX_RECIPES_PER_USER: int = Field(default=1000)
    MAX_PROJECTS_PER_USER: int = Field(default=100)
    MAX_FILE_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024)  # 10 MB

    # ===================================
    # LOGGING
    # ===================================

    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # ===================================
    # HELPERS
    # ===================================

    @property
    def is_production(self) -> bool:
        """Vérifie si on est en production"""
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        """Vérifie si on est en développement"""
        return self.ENV == "development"

    @property
    def is_test(self) -> bool:
        """Vérifie si on est en mode test"""
        return self.ENV == "test"

    def get_database_url(self, hide_password: bool = True) -> str:
        """
        Retourne l'URL de la base (avec ou sans mot de passe)
        """
        if not hide_password:
            return self.DATABASE_URL

        # Masquer le mot de passe
        if "@" in self.DATABASE_URL:
            before_at, after_at = self.DATABASE_URL.split("@")
            if ":" in before_at:
                user = before_at.split(":")[0].split("//")[1]
                return f"postgresql://{user}:****@{after_at}"

        return self.DATABASE_URL

    def to_dict(self) -> dict:
        """Convertit la config en dictionnaire (pour affichage)"""
        return {
            "app_name": self.APP_NAME,
            "version": self.APP_VERSION,
            "environment": self.ENV,
            "debug": self.DEBUG,
            "database": self.get_database_url(hide_password=True),
            "redis": self.REDIS_URL.split("@")[-1] if "@" in self.REDIS_URL else self.REDIS_URL,
            "ollama": {
                "url": self.OLLAMA_URL,
                "model": self.OLLAMA_MODEL
            },
            "features": {
                "ai": self.ENABLE_AI,
                "weather": self.ENABLE_WEATHER,
                "notifications": self.ENABLE_NOTIFICATIONS
            }
        }


# ===================================
# INSTANCE GLOBALE
# ===================================

settings = Settings()


# ===================================
# LOGGING CONFIGURATION
# ===================================

import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": settings.LOG_FORMAT,
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "detailed",
            "filename": settings.LOGS_DIR / "app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {
        "level": settings.LOG_LEVEL,
        "handlers": ["console", "file"],
    },
    "loggers": {
        "sqlalchemy.engine": {
            "level": "WARNING" if not settings.DEBUG else "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "httpx": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)