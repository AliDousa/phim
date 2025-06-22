"""
Production-ready Flask application entry point.
Public Health Intelligence Platform with full production features.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from prometheus_flask_exporter import PrometheusMetrics
import structlog
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sqlalchemy import text
import redis
import time

# Import configuration
from .config import get_config

# Import database and models
from .models.database import db
from .routes.auth import auth_bp
from .routes.datasets import datasets_bp
from .routes.simulations import simulations_bp

# Import tasks
from .tasks import make_celery

# Import security utilities
from .security import SecurityManager
from .monitoring import setup_monitoring
from .utils import setup_logging


def create_app(config_name=None):
    """Application factory for creating Flask app instances."""

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = get_config()
    app.config.from_object(config_class)

    # Setup logging
    setup_logging(app)

    # Setup Sentry for error tracking
    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                CeleryIntegration(),
            ],
            traces_sample_rate=0.1,
            environment=config_name,
        )

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Setup security
    setup_security(app)

    # Setup monitoring
    if app.config.get("PROMETHEUS_METRICS"):
        setup_monitoring(app)

    # Setup health checks
    setup_health_checks(app)

    return app


def initialize_extensions(app):
    """Initialize Flask extensions."""

    # Database
    db.init_app(app)

    # CORS
    CORS(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        expose_headers=["X-Total-Count", "X-Page-Count"],
    )

    # Rate limiting
    app.limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=[app.config["RATELIMIT_DEFAULT"]],
        storage_uri=app.config["RATELIMIT_STORAGE_URL"],
        headers_enabled=app.config.get("RATELIMIT_HEADERS_ENABLED", True),
    )

    # Caching
    app.cache = Cache(app)

    # Celery
    app.celery = make_celery(app)

    # Redis connection
    app.redis = redis.from_url(app.config["REDIS_URL"])


def register_blueprints(app):
    """Register application blueprints."""

    # API version prefix
    api_prefix = f"/api/{app.config.get('API_VERSION', 'v1')}"

    # Register blueprints with versioning
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(datasets_bp, url_prefix=f"{api_prefix}/datasets")
    app.register_blueprint(simulations_bp, url_prefix=f"{api_prefix}/simulations")

    # Legacy support (remove in future versions)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(datasets_bp, url_prefix="/api/datasets")
    app.register_blueprint(simulations_bp, url_prefix="/api/simulations")


def register_error_handlers(app):
    """Register application error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors."""
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "message": "The request could not be understood by the server",
                    "status_code": 400,
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors."""
        return (
            jsonify(
                {
                    "error": "Unauthorized",
                    "message": "Authentication required",
                    "status_code": 401,
                }
            ),
            401,
        )

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors."""
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "Insufficient permissions",
                    "status_code": 403,
                }
            ),
            403,
        )

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return (
            jsonify(
                {
                    "error": "Not found",
                    "message": "The requested resource was not found",
                    "status_code": 404,
                }
            ),
            404,
        )

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 errors."""
        return (
            jsonify(
                {
                    "error": "File too large",
                    "message": f"File size exceeds maximum allowed size",
                    "status_code": 413,
                }
            ),
            413,
        )

    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 errors."""
        return (
            jsonify(
                {
                    "error": "Unprocessable entity",
                    "message": "The request was well-formed but was unable to be processed",
                    "status_code": 422,
                }
            ),
            422,
        )

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 errors."""
        return (
            jsonify(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later",
                    "status_code": 429,
                    "retry_after": error.retry_after,
                }
            ),
            429,
        )

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        db.session.rollback()

        # Log the error
        app.logger.error(f"Internal server error: {error}", exc_info=True)

        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "status_code": 500,
                }
            ),
            500,
        )

    @app.errorhandler(502)
    def bad_gateway(error):
        """Handle 502 errors."""
        return (
            jsonify(
                {
                    "error": "Bad gateway",
                    "message": "The server received an invalid response",
                    "status_code": 502,
                }
            ),
            502,
        )

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 errors."""
        return (
            jsonify(
                {
                    "error": "Service unavailable",
                    "message": "The service is temporarily unavailable",
                    "status_code": 503,
                }
            ),
            503,
        )


def setup_security(app):
    """Setup security features."""

    security_manager = SecurityManager(app)

    @app.before_request
    def before_request():
        """Security checks before each request."""

        # Request timing
        g.start_time = time.time()

        # Security headers
        security_manager.apply_security_headers()

        # Rate limiting bypass for health checks
        if request.endpoint in ["health_check", "health_detail", "metrics"]:
            return

        # Request validation
        security_manager.validate_request()

    @app.after_request
    def after_request(response):
        """Security processing after each request."""

        # Calculate request duration
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

        # Apply security headers
        security_manager.apply_response_headers(response)

        return response


def setup_health_checks(app):
    """Setup health check endpoints."""

    @app.route("/")
    def index():
        """Root endpoint - API information."""
        return jsonify(
            {
                "name": app.config.get(
                    "API_TITLE", "Public Health Intelligence Platform API"
                ),
                "description": app.config.get(
                    "API_DESCRIPTION",
                    "API for epidemiological modeling and forecasting",
                ),
                "version": app.config.get("API_VERSION", "v1"),
                "status": "running",
                "environment": os.environ.get("FLASK_ENV", "development"),
                "endpoints": {
                    "auth": f"/api/{app.config.get('API_VERSION', 'v1')}/auth",
                    "datasets": f"/api/{app.config.get('API_VERSION', 'v1')}/datasets",
                    "simulations": f"/api/{app.config.get('API_VERSION', 'v1')}/simulations",
                    "health": "/health",
                    "metrics": (
                        "/metrics" if app.config.get("PROMETHEUS_METRICS") else None
                    ),
                },
            }
        )

    @app.route("/health")
    def health_check():
        """Basic health check endpoint."""
        try:
            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        # Test Redis connection
        try:
            app.redis.ping()
            redis_status = "healthy"
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"

        # Test Celery
        try:
            celery_inspect = app.celery.control.inspect()
            active_workers = celery_inspect.active()
            celery_status = "healthy" if active_workers else "no_workers"
        except Exception as e:
            celery_status = f"unhealthy: {str(e)}"

        overall_status = (
            "healthy"
            if all(status == "healthy" for status in [db_status, redis_status])
            else "degraded"
        )

        return jsonify(
            {
                "status": overall_status,
                "timestamp": time.time(),
                "services": {
                    "database": db_status,
                    "redis": redis_status,
                    "celery": celery_status,
                },
            }
        ), (200 if overall_status == "healthy" else 503)

    @app.route("/health/detail")
    def health_detail():
        """Detailed health check endpoint."""
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "environment": os.environ.get("FLASK_ENV", "development"),
            "version": app.config.get("API_VERSION", "v1"),
            "uptime": time.time() - app.start_time if hasattr(app, "start_time") else 0,
            "services": {},
            "metrics": {},
        }

        # Database health
        try:
            start_time = time.time()
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT COUNT(*) FROM users"))
                user_count = result.scalar()
            db_response_time = time.time() - start_time

            health_data["services"]["database"] = {
                "status": "healthy",
                "response_time": f"{db_response_time:.3f}s",
                "user_count": user_count,
            }
        except Exception as e:
            health_data["services"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_data["status"] = "degraded"

        # Redis health
        try:
            start_time = time.time()
            app.redis.ping()
            redis_response_time = time.time() - start_time
            redis_info = app.redis.info()

            health_data["services"]["redis"] = {
                "status": "healthy",
                "response_time": f"{redis_response_time:.3f}s",
                "memory_usage": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
            }
        except Exception as e:
            health_data["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_data["status"] = "degraded"

        # Celery health
        try:
            celery_inspect = app.celery.control.inspect()
            active_workers = celery_inspect.active()
            registered_tasks = celery_inspect.registered()

            health_data["services"]["celery"] = {
                "status": "healthy" if active_workers else "no_workers",
                "active_workers": len(active_workers) if active_workers else 0,
                "registered_tasks": (
                    sum(len(tasks) for tasks in registered_tasks.values())
                    if registered_tasks
                    else 0
                ),
            }
        except Exception as e:
            health_data["services"]["celery"] = {"status": "unhealthy", "error": str(e)}

        return jsonify(health_data), 200 if health_data["status"] == "healthy" else 503


def initialize_database():
    """Initialize database tables and create indexes."""
    try:
        # Import all models to ensure they're registered
        from .models.database import (
            User,
            Dataset,
            DataPoint,
            Simulation,
            Forecast,
            ModelComparison,
            AuditLog,
        )

        # Create all tables
        db.create_all()

        # Create additional indexes for performance
        with db.engine.connect() as connection:
            # Data points indexes
            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_data_points_dataset_timestamp 
                ON data_points(dataset_id, timestamp)
            """
                )
            )

            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_data_points_location_timestamp 
                ON data_points(location, timestamp)
            """
                )
            )

            # Simulations indexes
            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_simulations_user_created 
                ON simulations(user_id, created_at)
            """
                )
            )

            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_simulations_status_created 
                ON simulations(status, created_at)
            """
                )
            )

            # Forecasts indexes
            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_forecasts_simulation_target 
                ON forecasts(simulation_id, target_date)
            """
                )
            )

            # Audit logs indexes
            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_audit_logs_user_timestamp 
                ON audit_logs(user_id, timestamp)
            """
                )
            )

            connection.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS idx_audit_logs_action_timestamp 
                ON audit_logs(action, timestamp)
            """
                )
            )

            connection.commit()

        app.logger.info("✓ Database tables and indexes created successfully")
        return True

    except Exception as e:
        app.logger.error(f"✗ Database initialization error: {e}")
        return False


# Create application instance
app = create_app()

# Record start time for uptime calculation
app.start_time = time.time()

# Initialize database on startup
with app.app_context():
    if not initialize_database():
        app.logger.error("Failed to initialize database")
        sys.exit(1)


if __name__ == "__main__":
    # Development server only
    app.logger.info("=" * 60)
    app.logger.info("Public Health Intelligence Platform")
    app.logger.info("=" * 60)
    app.logger.info("Starting development server...")

    # Initialize database
    with app.app_context():
        if not initialize_database():
            app.logger.error("Failed to initialize database. Exiting...")
            sys.exit(1)

    app.logger.info("✓ Application initialized successfully")
    app.logger.info("")
    app.logger.info("Server Information:")
    app.logger.info(f"  Backend API: http://localhost:5000")
    app.logger.info(f"  Health Check: http://localhost:5000/health")
    app.logger.info(f"  API Documentation: http://localhost:5000/")
    app.logger.info("")
    app.logger.info("Available endpoints:")
    app.logger.info("  Authentication: /api/v1/auth/*")
    app.logger.info("  Datasets: /api/v1/datasets/*")
    app.logger.info("  Simulations: /api/v1/simulations/*")
    app.logger.info("")
    app.logger.info("Press Ctrl+C to stop the server")
    app.logger.info("=" * 60)

    try:
        app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            debug=app.config.get("DEBUG", False),
            threaded=True,
        )
    except KeyboardInterrupt:
        app.logger.info("\nServer stopped by user")
    except Exception as e:
        app.logger.error(f"Server error: {e}")
        sys.exit(1)
