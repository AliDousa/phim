"""
Main application entry point for the Public Health Intelligence Platform.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
# Try to load from current directory first, then parent directory
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# This block allows the script to be run directly for development.
# It adds the parent directory of 'src' ('backend') to the system path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

# Import database and models
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.datasets import datasets_bp
from src.routes.simulations import simulations_bp
from src.routes.admin import admin_bp
from src.tasks import make_celery
from src.config import get_config
from src.security import SecurityException
from src.utils import setup_logging as setup_app_logging


def create_app(config_name=None):
    """Application factory for creating Flask app instances."""

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config = get_config(config_name)
    app.config.from_object(config)

    # Disable automatic trailing slash redirects
    app.url_map.strict_slashes = False

    # Setup structured logging
    setup_app_logging(app)

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

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
    )

    # Celery
    app.celery = make_celery(app)


def register_blueprints(app):
    """Register application blueprints."""

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(datasets_bp, url_prefix="/api/datasets")
    app.register_blueprint(simulations_bp, url_prefix="/api/simulations")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")


def register_error_handlers(app):
    """Register application error handlers."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        response = e.get_response()
        response.data = jsonify(
            {
                "code": e.code,
                "name": e.name,
                "description": e.description,
            }
        ).data
        response.content_type = "application/json"
        return response

    @app.errorhandler(SecurityException)
    def handle_security_exception(e):
        """Handle custom security exceptions for validation errors."""
        app.logger.warning(
            f"Security exception: {e.message} from {request.remote_addr if request else 'unknown'}"
        )
        response_data = {
            "code": e.status_code,
            "name": "Validation Error",
            "description": e.message,
        }
        return jsonify(response_data), e.status_code

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
        return (
            jsonify(
                {
                    "code": 500,
                    "name": "Internal Server Error",
                    "description": "An unexpected internal error occurred.",
                }
            ),
            500,
        )


def setup_health_checks(app):
    """Setup health check endpoints."""

    @app.route("/")
    def index():
        """Root endpoint - API information."""
        return jsonify(
            {
                "name": "Public Health Intelligence Platform API",
                "description": "API for epidemiological modeling and forecasting",
                "version": "v1",
                "status": "running",
                "environment": os.environ.get("FLASK_ENV", "development"),
                "endpoints": {
                    "auth": "/api/auth",
                    "datasets": "/api/datasets",
                    "simulations": "/api/simulations",
                    "admin": "/api/admin",
                    "health": "/health",
                },
            }
        )

    @app.route("/health")
    def health_check():
        """Basic health check endpoint."""
        try:
            # Test database connection
            from sqlalchemy import text

            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"

        overall_status = "healthy" if db_status == "healthy" else "degraded"

        return jsonify(
            {"status": overall_status, "services": {"database": db_status}}
        ), (200 if overall_status == "healthy" else 503)

    @app.route("/api/health")
    def api_health_check():
        """API health check endpoint."""
        return health_check()


def initialize_database(app):
    """Initialize database tables."""
    try:
        # Use absolute import now that the path is set
        from src.models.database import (
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

        app.logger.info("[OK] Database tables created successfully")
        return True

    except Exception as e:
        app.logger.error(f"[ERROR] Database initialization error: {e}")
        return False


# This is the application instance that a WSGI server like Gunicorn will use.
# It respects the FLASK_ENV environment variable for production deployments.
app = create_app(os.environ.get("FLASK_ENV", "development"))


def run_development_server():
    """
    Sets up and runs the application with a development configuration.
    This function is intended to be called only when running the script directly.
    """
    # When running directly, ALWAYS use the development configuration.
    # This prevents accidentally running with production settings locally.
    dev_app = create_app("development")
    # Development server only
    dev_app.logger.info("=" * 60)
    dev_app.logger.info("Public Health Intelligence Platform - Development")
    dev_app.logger.info("=" * 60)
    dev_app.logger.info(
        f"Starting development server in '{dev_app.config.get('ENV', 'unknown')}' mode..."
    )

    # Initialize database
    with dev_app.app_context():
        if not initialize_database(dev_app):
            dev_app.logger.error("Failed to initialize database. Exiting...")
            sys.exit(1)

    dev_app.logger.info("[OK] Application initialized successfully")
    dev_app.logger.info("Server Information:")
    dev_app.logger.info(f"  Backend API: http://localhost:5000")
    dev_app.logger.info(f"  Health Check: http://localhost:5000/health")
    dev_app.logger.info("")
    dev_app.logger.info("Available endpoints:")
    dev_app.logger.info("  Authentication: /api/auth/*")
    dev_app.logger.info("  Datasets: /api/datasets/*")
    dev_app.logger.info("  Simulations: /api/simulations/*")
    dev_app.logger.info("  Admin: /api/admin/*")
    dev_app.logger.info("")
    dev_app.logger.info("Press Ctrl+C to stop the server")
    dev_app.logger.info("=" * 60)

    try:
        dev_app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            debug=dev_app.config.get("DEBUG", False),
            threaded=True,
        )
    except KeyboardInterrupt:
        dev_app.logger.info("\nServer stopped by user")
    except Exception as e:
        dev_app.logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_development_server()
