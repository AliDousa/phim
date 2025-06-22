"""
Configuration settings for the Public Health Intelligence Platform.
"""

import os
from pathlib import Path


class Config:
    """Base configuration class."""

    # Secret key for JWT and sessions
    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production-2024"
    )

    # Database configuration
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{DATA_DIR}/phip.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # File upload settings
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    UPLOAD_FOLDER = DATA_DIR / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # JWT settings
    JWT_EXPIRATION_DELTA = 3600  # 1 hour
    JWT_ALGORITHM = "HS256"

    # Pagination settings
    DATASETS_PER_PAGE = 25
    SIMULATIONS_PER_PAGE = 25
    DATA_POINTS_PER_PAGE = 100

    # Rate limiting (requests per minute)
    RATE_LIMIT_LOGIN = 5
    RATE_LIMIT_REGISTER = 3
    RATE_LIMIT_API = 100

    # Security settings
    WTF_CSRF_ENABLED = False  # Disabled for API
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False

    # Enable SQL query logging in development
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

    # Less strict security in development
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or f"sqlite:///{Config.DATA_DIR}/phip_prod.db"
    )

    # Stricter security settings
    SESSION_COOKIE_SECURE = True
    SECRET_KEY = os.environ.get("SECRET_KEY")  # Must be set in production

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True

    # Use in-memory database for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable CSRF for easier testing
    WTF_CSRF_ENABLED = False

    # Shorter JWT expiration for testing
    JWT_EXPIRATION_DELTA = 300  # 5 minutes


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get the configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    return config.get(env, config["default"])
