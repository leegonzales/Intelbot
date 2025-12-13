"""Add QC results column to research_runs table."""

import sqlite3


def up(conn: sqlite3.Connection):
    """Add qc_results column to research_runs."""
    conn.execute("""
        ALTER TABLE research_runs
        ADD COLUMN qc_results TEXT
    """)
    conn.execute("""
        ALTER TABLE research_runs
        ADD COLUMN qc_score REAL
    """)


def down(conn: sqlite3.Connection):
    """Remove qc columns (SQLite doesn't support DROP COLUMN easily)."""
    # SQLite doesn't support DROP COLUMN directly in older versions
    # For rollback, we'd need to recreate the table
    pass
