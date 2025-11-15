"""Initial database schema migration."""

import sqlite3
from pathlib import Path


def up(conn: sqlite3.Connection):
    """Create initial schema."""
    schema_path = Path(__file__).parent.parent / "schema.sql"
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)


def down(conn: sqlite3.Connection):
    """Rollback initial schema."""
    conn.executescript("""
    DROP TRIGGER IF EXISTS items_fts_delete;
    DROP TRIGGER IF EXISTS items_fts_update;
    DROP TRIGGER IF EXISTS items_fts_insert;
    DROP TABLE IF EXISTS items_fts;
    DROP TABLE IF EXISTS learned_topics;
    DROP TABLE IF EXISTS source_performance;
    DROP TABLE IF EXISTS item_engagement;
    DROP TABLE IF EXISTS run_items;
    DROP TABLE IF EXISTS research_runs;
    DROP TABLE IF EXISTS seen_items;
    """)
