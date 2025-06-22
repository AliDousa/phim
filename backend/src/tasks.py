"""
Production-ready configuration settings for the Public Health Intelligence Platform.
"""

import os
from pathlib import Path
from datetime import timedelta


class Config:
    """Base configuration class."""

    # Secret key for JWT and sessions
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")

    # Database configuration
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    DATA_DIR.mkdir(exist_ok=True)

    # Database URLs
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATA_DIR}/phip.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.environ.get("DB_POOL_SIZE", "10")),
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", "300")),
        "pool_pre_ping": True,
        "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", "20")),
    }

    # Redis configuration
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    # Celery configuration
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_TASK_SERIALIZER = "json"
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_RESULT_SERIALIZER = "json"
    CELERY_TIMEZONE = "UTC"
    CELERY_ENABLE_UTC = True
    CELERY_TASK_ROUTES = {
        "src.tasks.run_simulation_task": {"queue": "simulations"},
        "src.tasks.process_dataset_task": {"queue": "datasets"},
    }

    # Caching configuration
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", "104857600"))  # 100MB
    UPLOAD_FOLDER = DATA_DIR / "uploads"
    UPLOAD_FOLDER.mkdir(exist_ok=True)

    # Security settings
    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT", "your-password-salt"
    )
    WTF_CSRF_ENABLED = False  # Disabled for API
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # CORS settings
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")

    # JWT settings
    JWT_EXPIRATION_DELTA = int(os.environ.get("JWT_EXPIRATION_DELTA", "3600"))  # 1 hour
    JWT_ALGORITHM = "HS256"
    JWT_REFRESH_EXPIRATION_DELTA = int(
        os.environ.get("JWT_REFRESH_EXPIRATION_DELTA", "2592000")
    )  # 30 days

    # Rate limiting configuration
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "1000 per hour"
    RATELIMIT_HEADERS_ENABLED = True

    # Pagination settings
    DATASETS_PER_PAGE = int(os.environ.get("DATASETS_PER_PAGE", "25"))
    SIMULATIONS_PER_PAGE = int(os.environ.get("SIMULATIONS_PER_PAGE", "25"))
    DATA_POINTS_PER_PAGE = int(os.environ.get("DATA_POINTS_PER_PAGE", "100"))

    # Logging configuration
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

    # Monitoring
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    PROMETHEUS_METRICS = True

    # API Configuration
    API_VERSION = "v1"
    API_TITLE = "Public Health Intelligence Platform API"
    API_DESCRIPTION = "API for epidemiological modeling and forecasting"

    # Task timeouts
    SIMULATION_TIMEOUT = int(os.environ.get("SIMULATION_TIMEOUT", "3600"))  # 1 hour
    DATASET_PROCESSING_TIMEOUT = int(
        os.environ.get("DATASET_PROCESSING_TIMEOUT", "1800")
    )  # 30 minutes

    # File validation
    ALLOWED_EXTENSIONS = {"csv", "json", "xlsx"}
    ALLOWED_MIME_TYPES = {
        "text/csv": [".csv"],
        "application/json": [".json"],
        "text/plain": [".txt"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    }


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False

    # Less strict security in development
    SESSION_COOKIE_SECURE = False

    # Development database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{Config.DATA_DIR}/phip_dev.db"
    )

    # Reduced rate limits for development
    RATELIMIT_DEFAULT = "10000 per hour"

    # Enable SQL query logging in development
    SQLALCHEMY_ECHO = os.environ.get("SQLALCHEMY_ECHO", "False").lower() == "true"


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False

    # Ensure PostgreSQL in production
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
        raise ValueError(
            "Production requires PostgreSQL. Set DATABASE_URL environment variable."
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    # Stricter security settings
    if not Config.SECRET_KEY or len(Config.SECRET_KEY) < 32:
        raise ValueError("Production requires a strong SECRET_KEY (32+ characters)")

    # Production logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING")

    # Require HTTPS in production
    PREFERRED_URL_SCHEME = "https"

    # Production rate limits
    RATELIMIT_DEFAULT = "1000 per hour"


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

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    # Test-specific settings
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


class DockerConfig(Config):
    """Docker-specific configuration."""

    # Use environment variables for all external services
    REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
    )

    # Database for Docker
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://phip_user:phip_password@postgres:5432/phip_db"
    )


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "docker": DockerConfig,
    "default": DevelopmentConfig,
}


def get_config():
    """Get the configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    config_class = config.get(env, config["default"])

    # Validate configuration
    if hasattr(config_class, "validate"):
        config_class.validate()

    return config_class
