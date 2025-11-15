"""Database migration system."""

import sqlite3
from pathlib import Path
import importlib.util


def run_migrations(db_path: Path):
    """
    Run all pending migrations.

    Args:
        db_path: Path to SQLite database file
    """
    conn = sqlite3.connect(db_path)

    try:
        # Create migrations table if not exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Get applied migrations
        cursor = conn.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cursor.fetchall()}

        # Find all migration files
        migrations_dir = Path(__file__).parent
        migration_files = sorted(migrations_dir.glob("[0-9]*.py"))

        # Run pending migrations
        for migration_file in migration_files:
            # Extract version from filename (e.g., 001_initial.py -> 1)
            version = int(migration_file.stem.split('_')[0])

            if version not in applied:
                print(f"Running migration {version}...")

                # Load migration module
                spec = importlib.util.spec_from_file_location(
                    f"migration_{version}",
                    migration_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Run up migration
                module.up(conn)

                # Record migration
                conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES (?)",
                    (version,)
                )

                conn.commit()
                print(f"Migration {version} completed")

    finally:
        conn.close()
