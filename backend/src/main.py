"""
Minimal Flask application entry point for development.
Public Health Intelligence Platform - simplified version.
"""

import os
import sys
import logging

# This block allows the script to be run directly for development.
# It adds the parent directory of 'src' ('backend') to the system path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify
from flask_cors import CORS

# Import database and models
from src.models.database import db
from src.routes.auth import auth_bp
from src.routes.datasets import datasets_bp
from src.routes.simulations import simulations_bp
from src.tasks import make_celery
from src.utils import ConfigValidator


def create_app(config_name=None):
    """Application factory for creating Flask app instances."""

    # Create Flask app
    app = Flask(__name__)

    # Basic configuration
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-for-testing"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///app.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS origins
    cors_origins = os.environ.get(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    )
    app.config["CORS_ORIGINS"] = cors_origins.split(",")

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Setup health checks
    setup_health_checks(app)

    # Validate configuration
    try:
        validation_result = ConfigValidator.validate_config(app.config)
        if validation_result["warnings"]:
            for warning in validation_result["warnings"]:
                app.logger.warning(f"Configuration warning: {warning}")
        if not validation_result["valid"]:
            for error in validation_result["errors"]:
                app.logger.error(f"Configuration error: {error}")
    except Exception as e:
        app.logger.warning(f"Configuration validation failed: {e}")

    return app


def initialize_extensions(app):
    """Initialize Flask extensions."""

    # Database
    db.init_app(app)

    # CORS
    CORS(
        app,
        origins=app.config.get(
            "CORS_ORIGINS", ["http://localhost:3000", "http://localhost:5173"]
        ),
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


def register_error_handlers(app):
    """Register application error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify(
                {
                    "error": "Bad request",
                    "message": "The request could not be understood",
                    "status_code": 400,
                }
            ),
            400,
        )

    @app.errorhandler(401)
    def unauthorized(error):
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

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f"Internal server error: {error}")
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


def initialize_database():
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

        app.logger.info("✓ Database tables created successfully")
        return True

    except Exception as e:
        app.logger.error(f"✗ Database initialization error: {e}")
        return False


# Create application instance
app = create_app()

# Initialize database on startup
with app.app_context():
    if not initialize_database():
        app.logger.error("Failed to initialize database")
        sys.exit(1)


if __name__ == "__main__":
    # Development server only
    app.logger.info("=" * 60)
    app.logger.info("Public Health Intelligence Platform - Development")
    app.logger.info("=" * 60)
    app.logger.info("Starting development server...")

    # Initialize database
    with app.app_context():
        if not initialize_database():
            app.logger.error("Failed to initialize database. Exiting...")
            sys.exit(1)

    app.logger.info("✓ Application initialized successfully")
    app.logger.info("Server Information:")
    app.logger.info(f"  Backend API: http://localhost:5000")
    app.logger.info(f"  Health Check: http://localhost:5000/health")
    app.logger.info("")
    app.logger.info("Available endpoints:")
    app.logger.info("  Authentication: /api/auth/*")
    app.logger.info("  Datasets: /api/datasets/*")
    app.logger.info("  Simulations: /api/simulations/*")
    app.logger.info("")
    app.logger.info("Press Ctrl+C to stop the server")
    app.logger.info("=" * 60)

    try:
        app.run(
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            debug=True,
            threaded=True,
        )
    except KeyboardInterrupt:
        app.logger.info("\nServer stopped by user")
    except Exception as e:
        app.logger.error(f"Server error: {e}")
        sys.exit(1)
