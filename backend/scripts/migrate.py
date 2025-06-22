#!/usr/bin/env python3
"""
Database migration script for the Public Health Intelligence Platform.
Handles database schema updates, data migrations, and rollbacks.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.main import create_app
from src.models.database import db
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError


class DatabaseMigrator:
    """Database migration manager."""

    def __init__(self, app):
        self.app = app
        self.migrations_dir = project_root / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def get_current_schema_version(self) -> str:
        """Get the current database schema version."""
        try:
            with self.app.app_context():
                result = db.session.execute(
                    text(
                        """
                    SELECT version FROM schema_migrations 
                    ORDER BY applied_at DESC LIMIT 1
                """
                    )
                )
                row = result.fetchone()
                return row[0] if row else "0.0.0"
        except Exception:
            # Schema migrations table doesn't exist yet
            return "0.0.0"

    def create_migrations_table(self):
        """Create the schema migrations tracking table."""
        try:
            with self.app.app_context():
                db.session.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        applied_by VARCHAR(100),
                        checksum VARCHAR(64)
                    )
                """
                    )
                )
                db.session.commit()
                self.logger.info("Schema migrations table created")
        except Exception as e:
            self.logger.error(f"Failed to create migrations table: {e}")
            raise

    def record_migration(self, version: str, description: str):
        """Record a completed migration."""
        try:
            with self.app.app_context():
                db.session.execute(
                    text(
                        """
                    INSERT INTO schema_migrations (version, description, applied_by)
                    VALUES (:version, :description, :applied_by)
                """
                    ),
                    {
                        "version": version,
                        "description": description,
                        "applied_by": os.environ.get("USER", "system"),
                    },
                )
                db.session.commit()
                self.logger.info(f"Recorded migration: {version}")
        except Exception as e:
            self.logger.error(f"Failed to record migration: {e}")
            raise

    def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file."""
        try:
            self.logger.info(f"Applying migration: {migration_file.name}")

            # Read migration content
            with open(migration_file, "r") as f:
                content = f.read()

            # Parse migration metadata
            if content.startswith("-- Migration:"):
                lines = content.split("\n")
                metadata_line = lines[0]
                description = (
                    metadata_line.split(":", 2)[2].strip()
                    if ":" in metadata_line
                    else "No description"
                )
                version = migration_file.stem
            else:
                description = "Legacy migration"
                version = migration_file.stem

            # Execute migration
            with self.app.app_context():
                # Split into individual statements
                statements = [
                    stmt.strip() for stmt in content.split(";") if stmt.strip()
                ]

                for stmt in statements:
                    if stmt.startswith("--"):
                        continue
                    try:
                        db.session.execute(text(stmt))
                    except Exception as e:
                        self.logger.error(f"Error executing statement: {stmt[:100]}...")
                        raise e

                db.session.commit()

                # Record the migration
                self.record_migration(version, description)

            self.logger.info(f"Successfully applied migration: {version}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            with self.app.app_context():
                db.session.rollback()
            return False

    def run_migrations(self, target_version: Optional[str] = None) -> bool:
        """Run database migrations up to target version."""
        try:
            self.logger.info("Starting database migrations...")

            # Create migrations table if it doesn't exist
            self.create_migrations_table()

            # Get current version
            current_version = self.get_current_schema_version()
            self.logger.info(f"Current schema version: {current_version}")

            # Find migration files
            migration_files = sorted(
                [
                    f
                    for f in self.migrations_dir.glob("*.sql")
                    if f.stem > current_version
                ]
            )

            if target_version:
                migration_files = [
                    f for f in migration_files if f.stem <= target_version
                ]

            if not migration_files:
                self.logger.info("No migrations to apply")
                return True

            self.logger.info(f"Found {len(migration_files)} migrations to apply")

            # Apply migrations
            for migration_file in migration_files:
                if not self.apply_migration(migration_file):
                    return False

            self.logger.info("All migrations applied successfully")
            return True

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            return False

    def generate_migration(self, description: str) -> str:
        """Generate a new migration file template."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{description.lower().replace(' ', '_')}"

        migration_content = f"""-- Migration: {version}: {description}
-- Created: {datetime.now().isoformat()}
-- Description: {description}

-- Add your migration SQL here
-- Example:
-- ALTER TABLE users ADD COLUMN new_field VARCHAR(100);
-- CREATE INDEX idx_users_new_field ON users(new_field);

-- Remember to:
-- 1. Test your migration on a copy of production data
-- 2. Consider the impact on running applications
-- 3. Plan for rollback if needed
-- 4. Update model definitions if schema changes affect them

"""

        migration_file = self.migrations_dir / f"{version}.sql"
        with open(migration_file, "w") as f:
            f.write(migration_content)

        self.logger.info(f"Generated migration file: {migration_file}")
        return str(migration_file)

    def show_migration_status(self):
        """Show current migration status."""
        try:
            with self.app.app_context():
                # Get applied migrations
                result = db.session.execute(
                    text(
                        """
                    SELECT version, description, applied_at, applied_by
                    FROM schema_migrations
                    ORDER BY applied_at DESC
                """
                    )
                )

                applied_migrations = result.fetchall()

                # Get pending migrations
                current_version = self.get_current_schema_version()
                pending_files = sorted(
                    [
                        f
                        for f in self.migrations_dir.glob("*.sql")
                        if f.stem > current_version
                    ]
                )

                print("\n=== Migration Status ===")
                print(f"Current Version: {current_version}")
                print(f"Applied Migrations: {len(applied_migrations)}")
                print(f"Pending Migrations: {len(pending_files)}")

                if applied_migrations:
                    print("\nRecent Applied Migrations:")
                    for migration in applied_migrations[:5]:
                        print(f"  {migration[0]} - {migration[1]} ({migration[2]})")

                if pending_files:
                    print("\nPending Migrations:")
                    for migration_file in pending_files:
                        print(f"  {migration_file.stem}")

        except Exception as e:
            self.logger.error(f"Failed to show migration status: {e}")

    def rollback_migration(self, target_version: str) -> bool:
        """Rollback to a specific version (requires rollback scripts)."""
        try:
            current_version = self.get_current_schema_version()

            if target_version >= current_version:
                self.logger.warning("Target version is not older than current version")
                return False

            # Find rollback files
            rollback_files = sorted(
                [
                    f
                    for f in self.migrations_dir.glob("rollback_*.sql")
                    if f.stem.replace("rollback_", "") > target_version
                    and f.stem.replace("rollback_", "") <= current_version
                ],
                reverse=True,
            )

            if not rollback_files:
                self.logger.error("No rollback scripts found")
                return False

            self.logger.info(f"Rolling back from {current_version} to {target_version}")

            # Apply rollback scripts
            with self.app.app_context():
                for rollback_file in rollback_files:
                    self.logger.info(f"Applying rollback: {rollback_file.name}")

                    with open(rollback_file, "r") as f:
                        content = f.read()

                    statements = [
                        stmt.strip() for stmt in content.split(";") if stmt.strip()
                    ]

                    for stmt in statements:
                        if stmt.startswith("--"):
                            continue
                        db.session.execute(text(stmt))

                    # Remove migration record
                    version = rollback_file.stem.replace("rollback_", "")
                    db.session.execute(
                        text(
                            """
                        DELETE FROM schema_migrations WHERE version = :version
                    """
                        ),
                        {"version": version},
                    )

                db.session.commit()

            self.logger.info(f"Successfully rolled back to {target_version}")
            return True

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            with self.app.app_context():
                db.session.rollback()
            return False

    def backup_database(self, backup_file: Optional[str] = None) -> str:
        """Create a database backup before migration."""
        if not backup_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_before_migration_{timestamp}.sql"

        backup_path = project_root / "backups" / backup_file
        backup_path.parent.mkdir(exist_ok=True)

        try:
            # Get database URL
            database_url = self.app.config["SQLALCHEMY_DATABASE_URI"]

            if database_url.startswith("postgresql://"):
                # PostgreSQL backup
                import subprocess

                cmd = f"pg_dump {database_url} > {backup_path}"
                subprocess.run(cmd, shell=True, check=True)
            elif database_url.startswith("sqlite://"):
                # SQLite backup
                import shutil

                db_file = database_url.replace("sqlite:///", "")
                shutil.copy2(db_file, backup_path)
            else:
                raise ValueError("Unsupported database type for backup")

            self.logger.info(f"Database backup created: {backup_path}")
            return str(backup_path)

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise

    def validate_schema(self) -> bool:
        """Validate database schema integrity."""
        try:
            with self.app.app_context():
                inspector = inspect(db.engine)

                # Check if all expected tables exist
                expected_tables = [
                    "users",
                    "datasets",
                    "data_points",
                    "simulations",
                    "forecasts",
                    "model_comparisons",
                    "audit_logs",
                    "schema_migrations",
                ]

                existing_tables = inspector.get_table_names()
                missing_tables = set(expected_tables) - set(existing_tables)

                if missing_tables:
                    self.logger.error(f"Missing tables: {missing_tables}")
                    return False

                # Check critical indexes
                critical_indexes = {
                    "users": ["idx_users_email_active", "idx_users_username_active"],
                    "data_points": ["idx_data_points_dataset_timestamp"],
                    "simulations": ["idx_simulations_user_created"],
                    "forecasts": ["idx_forecasts_simulation_target"],
                }

                for table, indexes in critical_indexes.items():
                    table_indexes = [
                        idx["name"] for idx in inspector.get_indexes(table)
                    ]
                    missing_indexes = set(indexes) - set(table_indexes)

                    if missing_indexes:
                        self.logger.warning(
                            f"Missing indexes on {table}: {missing_indexes}"
                        )

                self.logger.info("Schema validation completed")
                return True

        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            return False


def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "command",
        choices=["migrate", "status", "generate", "rollback", "backup", "validate"],
        help="Migration command",
    )
    parser.add_argument("--version", help="Target version for migration/rollback")
    parser.add_argument("--description", help="Description for new migration")
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before migration"
    )
    parser.add_argument("--env", default="production", help="Environment to use")

    args = parser.parse_args()

    # Create Flask app
    app = create_app(args.env)
    migrator = DatabaseMigrator(app)

    try:
        if args.command == "migrate":
            if args.backup:
                migrator.backup_database()

            success = migrator.run_migrations(args.version)
            sys.exit(0 if success else 1)

        elif args.command == "status":
            migrator.show_migration_status()

        elif args.command == "generate":
            if not args.description:
                print("Error: --description is required for generate command")
                sys.exit(1)
            migrator.generate_migration(args.description)

        elif args.command == "rollback":
            if not args.version:
                print("Error: --version is required for rollback command")
                sys.exit(1)
            success = migrator.rollback_migration(args.version)
            sys.exit(0 if success else 1)

        elif args.command == "backup":
            migrator.backup_database()

        elif args.command == "validate":
            success = migrator.validate_schema()
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
