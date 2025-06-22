#!/usr/bin/env python3
"""
Startup script for the Public Health Intelligence Platform backend.
This script handles different ways of running the application.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def main():
    """Main entry point for the application."""
    try:
        # Try to import and run the main application
        from src.main import app, initialize_database

        print("=" * 60)
        print("Public Health Intelligence Platform")
        print("=" * 60)
        print("Starting application...")

        # Initialize database
        with app.app_context():
            if not initialize_database():
                print("Failed to initialize database. Exiting...")
                sys.exit(1)

        print("✓ Application initialized successfully")
        print()
        print("Server Information:")
        print(f"  Backend API: http://localhost:5000")
        print(f"  Health Check: http://localhost:5000/api/health")
        print(f"  API Documentation: http://localhost:5000/")
        print()
        print("Available endpoints:")
        print("  Authentication: /api/auth/*")
        print("  Datasets: /api/datasets/*")
        print("  Simulations: /api/simulations/*")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)

        # Run the application
        app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)

    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped by user")
        print("=" * 60)
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you're in the backend directory")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Check that all files are in the correct location")
        sys.exit(1)
    except Exception as e:
        print(f"Startup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
