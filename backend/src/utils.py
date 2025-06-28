"""
Utility functions and helpers for the Public Health Intelligence Platform.
"""

import os
import sys
import logging
import json
import hashlib
import secrets
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
from flask import current_app
import structlog


def setup_logging(app):
    """Setup comprehensive logging for the application."""

    # Create logs directory
    log_dir = Path(app.instance_path) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging level
    log_level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper())

    # Setup structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if not app.debug
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure Flask logger
    if not app.debug:
        # File handler for application logs
        app_log_file = log_dir / "application.log"
        file_handler = logging.FileHandler(app_log_file)
        file_handler.setLevel(log_level)

        # Error log file
        error_log_file = log_dir / "errors.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)

        # Security log file
        security_log_file = log_dir / "security.log"
        security_handler = logging.FileHandler(security_log_file)
        security_handler.setLevel(logging.WARNING)

        # Formatters
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [%(pathname)s:%(lineno)d] %(message)s"
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        security_handler.setFormatter(formatter)

        # Add handlers to app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(error_handler)
        app.logger.addHandler(security_handler)
        app.logger.setLevel(log_level)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

    # Add structured logger to app
    app.structured_logger = structlog.get_logger()

    app.logger.info("Logging configured successfully")


def generate_secure_filename(original_filename: str, user_id: int = None) -> str:
    """Generate a secure filename for uploaded files."""

    # Get file extension
    file_ext = Path(original_filename).suffix.lower()

    # Generate secure base name
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    random_suffix = secrets.token_hex(8)

    if user_id:
        base_name = f"user_{user_id}_{timestamp}_{random_suffix}"
    else:
        base_name = f"{timestamp}_{random_suffix}"

    return f"{base_name}{file_ext}"


def validate_file_size(file_size: int, max_size: int = None) -> bool:
    """Validate file size against maximum allowed size."""
    if max_size is None:
        max_size = current_app.config.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)

    return file_size <= max_size


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """Calculate hash of a file."""
    hash_algo = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_algo.update(chunk)

    return hash_algo.hexdigest()


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely load JSON string with error handling."""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """Safely dump object to JSON string with error handling."""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(default) if default is not None else "{}"


def paginate_query(query, page: int = 1, per_page: int = 20, max_per_page: int = 100):
    """Paginate a SQLAlchemy query with safety limits."""

    # Validate parameters
    page = max(1, page)
    per_page = min(max(1, per_page), max_per_page)

    # Apply pagination
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": [
            item.to_dict() if hasattr(item, "to_dict") else item
            for item in paginated.items
        ],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": paginated.total,
            "pages": paginated.pages,
            "has_next": paginated.has_next,
            "has_prev": paginated.has_prev,
            "next_page": paginated.next_num if paginated.has_next else None,
            "prev_page": paginated.prev_num if paginated.has_prev else None,
        },
    }


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable string."""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = size_bytes

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f}{size_names[i]}"


def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
    """Generate a cryptographically secure random string."""

    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*"

    return "".join(secrets.choice(chars) for _ in range(length))


def validate_email_format(email: str) -> bool:
    """Validate email format using regex."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data for logging."""
    if len(data) <= visible_chars:
        return mask_char * len(data)

    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def convert_timezone(
    dt: datetime, from_tz: str = "UTC", to_tz: str = "UTC"
) -> datetime:
    """Convert datetime between timezones."""
    import pytz

    if dt.tzinfo is None:
        dt = pytz.timezone(from_tz).localize(dt)

    target_tz = pytz.timezone(to_tz)
    return dt.astimezone(target_tz)


class DataValidator:
    """Data validation utilities."""

    @staticmethod
    def validate_dataframe(
        df: pd.DataFrame, required_columns: List[str] = None
    ) -> Dict[str, Any]:
        """Validate pandas DataFrame."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {
                "rows": len(df),
                "columns": len(df.columns),
                "memory_usage": df.memory_usage(deep=True).sum(),
                "dtypes": df.dtypes.to_dict(),
            },
        }

        # Check if DataFrame is empty
        if df.empty:
            validation_result["valid"] = False
            validation_result["errors"].append("DataFrame is empty")
            return validation_result

        # Check required columns
        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Missing required columns: {missing_columns}"
                )

        # Check for duplicate columns
        duplicate_columns = df.columns[df.columns.duplicated()].tolist()
        if duplicate_columns:
            validation_result["warnings"].append(
                f"Duplicate columns found: {duplicate_columns}"
            )

        # Check for null values
        null_counts = df.isnull().sum()
        null_columns = null_counts[null_counts > 0].to_dict()
        if null_columns:
            validation_result["warnings"].append(
                f"Null values found in columns: {null_columns}"
            )

        # Check data types
        for column, dtype in df.dtypes.items():
            if dtype == "object":
                # Check if string columns contain numeric data
                try:
                    pd.to_numeric(df[column], errors="raise")
                    validation_result["warnings"].append(
                        f"Column {column} contains numeric data but is stored as object"
                    )
                except (ValueError, TypeError):
                    pass

        return validation_result

    @staticmethod
    def validate_json_schema(
        data: Dict[str, Any], schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate JSON data against a schema."""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # Check required fields
        required_fields = schema.get("required", [])
        missing_fields = set(required_fields) - set(data.keys())
        if missing_fields:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Missing required fields: {missing_fields}"
            )

        # Check field types
        field_types = schema.get("properties", {})
        for field, expected_type in field_types.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if actual_type != expected_type:
                    validation_result["warnings"].append(
                        f"Field {field} has type {actual_type}, expected {expected_type}"
                    )

        return validation_result


class CacheHelper:
    """Caching utilities."""

    @staticmethod
    def generate_cache_key(*args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_parts = []

        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))

        # Add keyword arguments
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")

        # Create hash
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    @staticmethod
    def cached_result(cache, timeout: int = 300):
        """Decorator for caching function results."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = (
                    f"{func.__name__}:{CacheHelper.generate_cache_key(*args, **kwargs)}"
                )

                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    current_app.cache_hits.labels(cache_type="function").inc()
                    return result

                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
                current_app.cache_misses.labels(cache_type="function").inc()

                return result

            return wrapper

        return decorator


class PerformanceProfiler:
    """Performance profiling utilities."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        current_app.logger.info(
            f"Performance: {self.name} completed in {self.duration:.3f}s",
            extra={
                "performance_metric": True,
                "operation": self.name,
                "duration": self.duration,
            },
        )


class ConfigValidator:
    """Configuration validation utilities."""

    @staticmethod
    def validate_config(config) -> Dict[str, Any]:
        """Validate application configuration."""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        # Required configuration (Redis is optional in development)
        required_configs = ["SECRET_KEY", "SQLALCHEMY_DATABASE_URI"]

        for config_key in required_configs:
            # Check if config key exists in Flask config
            config_value = config.get(config_key, None)
            if not config_value or config_value == "":
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Missing required configuration: {config_key}"
                )

        # Validate SECRET_KEY strength
        secret_key = config.get("SECRET_KEY", "")
        if len(secret_key) < 32:
            validation_result["warnings"].append(
                "SECRET_KEY should be at least 32 characters long"
            )

        # Validate database URL
        db_url = config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_url.startswith("sqlite://") and not config.get("TESTING", False):
            validation_result["warnings"].append(
                "SQLite not recommended for production"
            )

        # Validate Redis URL
        redis_url = config.get("REDIS_URL", "")
        if redis_url and not redis_url.startswith("redis://"):
            validation_result["warnings"].append("Invalid Redis URL format")

        return validation_result


def cleanup_old_files(
    directory: Path, max_age_days: int = 30, pattern: str = "*"
) -> int:
    """Clean up old files in a directory."""
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    removed_count = 0

    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff_date:
                    file_path.unlink()
                    removed_count += 1
    except Exception as e:
        current_app.logger.error(f"Error cleaning up files: {e}")

    return removed_count


def health_check_database() -> Dict[str, Any]:
    """Perform database health check."""
    from src.models.database import db
    from sqlalchemy import text

    try:
        start_time = time.time()
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        response_time = time.time() - start_time

        return {
            "status": "healthy",
            "response_time": response_time,
            "connection_pool_size": db.engine.pool.size(),
            "checked_out_connections": db.engine.pool.checkedout(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def health_check_redis() -> Dict[str, Any]:
    """Perform Redis health check."""
    try:
        start_time = time.time()
        current_app.redis.ping()
        response_time = time.time() - start_time

        info = current_app.redis.info()

        return {
            "status": "healthy",
            "response_time": response_time,
            "memory_usage": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def backup_database(backup_path: Path) -> bool:
    """Create a database backup."""
    try:
        import subprocess

        db_url = current_app.config["SQLALCHEMY_DATABASE_URI"]

        if db_url.startswith("postgresql://"):
            # PostgreSQL backup
            cmd = f"pg_dump {db_url} > {backup_path}"
            subprocess.run(cmd, shell=True, check=True)
        elif db_url.startswith("sqlite://"):
            # SQLite backup
            import shutil

            db_file = db_url.replace("sqlite:///", "")
            shutil.copy2(db_file, backup_path)
        else:
            raise ValueError("Unsupported database type for backup")

        current_app.logger.info(f"Database backup created: {backup_path}")
        return True

    except Exception as e:
        current_app.logger.error(f"Database backup failed: {e}")
        return False
