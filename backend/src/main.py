"""
Main Flask application entry point.
Optimized for cross-platform compatibility including Windows.
"""

import os
from pathlib import Path
import sys

from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text

# --- REFACTORED IMPORTS ---
# Use explicit relative imports when running as module, absolute when running directly
try:
    # When running as module (python -m src.main)
    from .models.database import db
    from .routes.auth import auth_bp
    from .routes.datasets import datasets_bp
    from .routes.simulations import simulations_bp
except ImportError:
    try:
        # When running directly (python main.py)
        from models.database import db
        from routes.auth import auth_bp
        from routes.datasets import datasets_bp
        from routes.simulations import simulations_bp
    except ImportError as e:
        print(f"Import error: {e}")
        print(
            "This indicates a problem with the package structure or how the app is being run."
        )
        print("Try running with: python -m src.main")
        sys.exit(1)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# Database configuration
data_dir = Path(__file__).resolve().parent.parent / "data"
data_dir.mkdir(exist_ok=True)
database_path = data_dir / "phip.db"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-secret-key-change-in-production"
)

# Initialize database
db.init_app(app)

# Register API blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(datasets_bp, url_prefix="/api/datasets")
app.register_blueprint(simulations_bp, url_prefix="/api/simulations")


@app.route("/")
def index():
    """Root endpoint - API status."""
    return jsonify(
        {
            "message": "Public Health Intelligence Platform API",
            "version": "1.0.0",
            "status": "running",
            "platform": "Cross-Platform Compatible",
            "endpoints": {
                "auth": "/api/auth",
                "datasets": "/api/datasets",
                "simulations": "/api/simulations",
                "health": "/api/health",
            },
        }
    )


@app.route("/api/health")
def health_check():
    """Health check endpoint."""
    try:
        # Test database connection using modern SQLAlchemy syntax
        with app.app_context():
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify(
        {
            "status": "healthy" if db_status == "connected" else "unhealthy",
            "database": db_status,
            "models": "loaded",
            "platform": "Cross-Platform Compatible",
        }
    )


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(400)
def bad_request(error):
    """Handle 400 errors."""
    return jsonify({"error": "Bad request"}), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors."""
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return jsonify({"error": "Forbidden"}), 403


# Create database tables
def initialize_database():
    """Initialize database tables."""
    try:
        with app.app_context():
            # Import all models to ensure they're registered
            from models.database import (
                User,
                Dataset,
                DataPoint,
                Simulation,
                Forecast,
                ModelComparison,
                AuditLog,
            )

            db.create_all()
            print("✓ Database tables created successfully")

            # Test database connection
            with db.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("✓ Database connection verified")

            return True
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        print("  Make sure your database server is running (if using MySQL)")
        print("  Or check file permissions (if using SQLite)")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Public Health Intelligence Platform")
    print("=" * 60)
    print("Initializing application...")

    # Initialize database
    if not initialize_database():
        print("Failed to initialize database. Exiting...")
        sys.exit(1)

    print("✓ Application initialized successfully")
    print()
    print("Server Information:")
    print(f"  Backend API: http://localhost:5000")
    print(f"  Frontend:    http://localhost:5173 (if running)")
    print(f"  Health Check: http://localhost:5000/api/health")
    print()
    print("Available API Endpoints:")
    print("  POST /api/auth/register - User registration")
    print("  POST /api/auth/login    - User login")
    print("  GET  /api/datasets      - List datasets")
    print("  POST /api/datasets      - Upload dataset")
    print("  GET  /api/simulations   - List simulations")
    print("  POST /api/simulations   - Create simulation")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    # Run the Flask development server
    # Listen on all interfaces (0.0.0.0) for Windows compatibility
    try:
        app.run(
            host="0.0.0.0",  # Allow external connections
            port=5000,
            debug=True,
            threaded=True,  # Enable threading for better performance
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
