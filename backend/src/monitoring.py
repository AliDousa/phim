"""
Monitoring and metrics collection for the Public Health Intelligence Platform.
Includes Prometheus metrics, structured logging, and performance monitoring.
"""

import time
import functools
from flask import request, g, current_app
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge, Summary
import structlog
import logging
import sys
from datetime import datetime


def setup_monitoring(app):
    """Setup comprehensive monitoring for the Flask application."""

    # Setup Prometheus metrics
    metrics = PrometheusMetrics(app)

    # Custom metrics
    setup_custom_metrics(app, metrics)

    # Setup request monitoring
    setup_request_monitoring(app)

    # Setup business metrics
    setup_business_metrics(app)

    return metrics


def setup_custom_metrics(app, metrics):
    """Setup custom Prometheus metrics."""

    # Database connection pool metrics
    app.db_connection_pool_size = Gauge(
        "db_connection_pool_size", "Number of database connections in pool"
    )

    app.db_connection_pool_checked_out = Gauge(
        "db_connection_pool_checked_out",
        "Number of database connections currently checked out",
    )

    # Cache metrics
    app.cache_hits = Counter(
        "cache_hits_total", "Total number of cache hits", ["cache_type"]
    )

    app.cache_misses = Counter(
        "cache_misses_total", "Total number of cache misses", ["cache_type"]
    )

    # Task queue metrics
    app.celery_task_total = Counter(
        "celery_tasks_total", "Total number of Celery tasks", ["task_name", "status"]
    )

    app.celery_task_duration = Histogram(
        "celery_task_duration_seconds", "Time spent on Celery tasks", ["task_name"]
    )

    # Simulation metrics
    app.simulations_total = Counter(
        "simulations_total", "Total number of simulations", ["model_type", "status"]
    )

    app.simulation_duration = Histogram(
        "simulation_duration_seconds", "Time spent on simulations", ["model_type"]
    )

    # File upload metrics
    app.file_uploads_total = Counter(
        "file_uploads_total", "Total number of file uploads", ["file_type", "status"]
    )

    app.file_upload_size = Histogram(
        "file_upload_size_bytes", "Size of uploaded files", ["file_type"]
    )

    # Security metrics
    app.security_events = Counter(
        "security_events_total",
        "Total number of security events",
        ["event_type", "severity"],
    )

    app.failed_logins = Counter(
        "failed_logins_total", "Total number of failed login attempts"
    )

    app.rate_limit_exceeded = Counter(
        "rate_limit_exceeded_total",
        "Total number of rate limit violations",
        ["endpoint"],
    )


def setup_request_monitoring(app):
    """Setup request-level monitoring."""

    @app.before_request
    def before_request_monitoring():
        """Record request start time and metadata."""
        g.start_time = time.time()
        g.request_id = generate_request_id()

        # Log request start
        app.logger.info(
            "Request started",
            extra={
                "request_id": g.request_id,
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", ""),
            },
        )

    @app.after_request
    def after_request_monitoring(response):
        """Record request completion metrics."""
        if hasattr(g, "start_time"):
            request_duration = time.time() - g.start_time

            # Log request completion
            app.logger.info(
                "Request completed",
                extra={
                    "request_id": getattr(g, "request_id", "unknown"),
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration": request_duration,
                    "response_size": response.content_length or 0,
                },
            )

        return response


def setup_business_metrics(app):
    """Setup business-specific metrics."""

    # Dataset metrics
    app.datasets_created = Counter(
        "datasets_created_total", "Total number of datasets created", ["data_type"]
    )

    app.data_points_processed = Counter(
        "data_points_processed_total", "Total number of data points processed"
    )

    # User activity metrics
    app.user_registrations = Counter(
        "user_registrations_total", "Total number of user registrations"
    )

    app.active_users = Gauge(
        "active_users", "Number of active users in the last 24 hours"
    )

    # Model performance metrics
    app.model_accuracy = Gauge(
        "model_accuracy", "Model accuracy scores", ["model_type", "metric"]
    )


def monitor_performance(metric_name):
    """Decorator to monitor function performance."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Record success
                if hasattr(current_app, f"{metric_name}_duration"):
                    duration = time.time() - start_time
                    getattr(current_app, f"{metric_name}_duration").observe(duration)

                return result

            except Exception as e:
                # Record failure
                if hasattr(current_app, f"{metric_name}_errors"):
                    getattr(current_app, f"{metric_name}_errors").inc()
                raise

        return wrapper

    return decorator


def monitor_celery_task(task_name):
    """Decorator to monitor Celery task performance."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Record successful task
                current_app.celery_task_total.labels(
                    task_name=task_name, status="success"
                ).inc()

                duration = time.time() - start_time
                current_app.celery_task_duration.labels(task_name=task_name).observe(
                    duration
                )

                return result

            except Exception as e:
                # Record failed task
                current_app.celery_task_total.labels(
                    task_name=task_name, status="failure"
                ).inc()
                raise

        return wrapper

    return decorator


def generate_request_id():
    """Generate a unique request ID for tracing."""
    import uuid

    return str(uuid.uuid4())[:8]


class StructuredLogger:
    """Structured logging utility."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize structured logging."""

        # Configure structlog
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
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Setup Flask logging
        if not app.debug:
            # Production logging configuration
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)

            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
            handler.setFormatter(formatter)

            app.logger.addHandler(handler)
            app.logger.setLevel(logging.INFO)

        # Add structured logger to app
        app.structured_logger = structlog.get_logger()


class MetricsCollector:
    """Collect and update application metrics."""

    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize metrics collector."""
        self.app = app

        # Schedule periodic metrics collection
        if hasattr(app, "celery"):
            self.setup_periodic_metrics(app.celery)

    def setup_periodic_metrics(self, celery):
        """Setup periodic metrics collection tasks."""

        @celery.task(bind=True)
        def collect_database_metrics(self):
            """Collect database connection pool metrics."""
            try:
                from sqlalchemy import inspect

                # Get database engine
                engine = current_app.extensions["sqlalchemy"].db.engine
                pool = engine.pool

                # Update connection pool metrics
                current_app.db_connection_pool_size.set(pool.size())
                current_app.db_connection_pool_checked_out.set(pool.checkedout())

            except Exception as e:
                current_app.logger.error(f"Failed to collect database metrics: {e}")

        @celery.task(bind=True)
        def collect_user_metrics(self):
            """Collect user activity metrics."""
            try:
                from .models.database import User, AuditLog
                from datetime import datetime, timedelta

                # Count active users in last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                active_count = (
                    AuditLog.query.filter(
                        AuditLog.timestamp >= yesterday, AuditLog.user_id.isnot(None)
                    )
                    .distinct(AuditLog.user_id)
                    .count()
                )

                current_app.active_users.set(active_count)

            except Exception as e:
                current_app.logger.error(f"Failed to collect user metrics: {e}")

        # Schedule tasks
        celery.conf.beat_schedule.update(
            {
                "collect-database-metrics": {
                    "task": "collect_database_metrics",
                    "schedule": 60.0,  # Every minute
                },
                "collect-user-metrics": {
                    "task": "collect_user_metrics",
                    "schedule": 300.0,  # Every 5 minutes
                },
            }
        )


class HealthChecker:
    """Health check utilities."""

    @staticmethod
    def check_database_health():
        """Check database connection health."""
        try:
            from .models.database import db
            from sqlalchemy import text

            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True, "Database connection healthy"

        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    @staticmethod
    def check_redis_health():
        """Check Redis connection health."""
        try:
            current_app.redis.ping()
            return True, "Redis connection healthy"

        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"

    @staticmethod
    def check_celery_health():
        """Check Celery worker health."""
        try:
            inspect = current_app.celery.control.inspect()
            stats = inspect.stats()

            if stats:
                return True, f"Celery workers healthy: {len(stats)} workers"
            else:
                return False, "No Celery workers available"

        except Exception as e:
            return False, f"Celery health check failed: {str(e)}"

    @staticmethod
    def check_disk_space():
        """Check available disk space."""
        try:
            import shutil

            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100

            if free_percent < 10:  # Less than 10% free
                return False, f"Low disk space: {free_percent:.1f}% free"
            else:
                return True, f"Disk space healthy: {free_percent:.1f}% free"

        except Exception as e:
            return False, f"Disk space check failed: {str(e)}"


def setup_logging(app):
    """Setup application logging."""

    # Create logs directory
    log_dir = app.config.get("LOG_DIR", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Setup structured logging
    structured_logger = StructuredLogger(app)

    # Setup metrics collector
    metrics_collector = MetricsCollector(app)

    return structured_logger


# Custom log filters
class SecurityLogFilter(logging.Filter):
    """Filter for security-related log messages."""

    def filter(self, record):
        return (
            hasattr(record, "security_event")
            or "security" in record.getMessage().lower()
        )


class PerformanceLogFilter(logging.Filter):
    """Filter for performance-related log messages."""

    def filter(self, record):
        return (
            hasattr(record, "performance_metric") or record.levelno >= logging.WARNING
        )
