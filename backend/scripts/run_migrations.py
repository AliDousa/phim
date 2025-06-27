#!/usr/bin/env python3
"""
Database migration runner for the Public Health Intelligence Platform.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.main import create_app
from src.models.database import db


def run_migrations():
    """Run database migrations."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Check if database is accessible
            from sqlalchemy import text
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                print("✓ Database connection verified")
            
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            return False


if __name__ == "__main__":
    print("=" * 60)
    print("Public Health Intelligence Platform - Database Migration")
    print("=" * 60)
    
    success = run_migrations()
    
    if success:
        print("✓ All migrations completed successfully")
        sys.exit(0)
    else:
        print("✗ Migration failed")
        sys.exit(1)