"""Add author performance tracking for adaptive learning."""

import sqlite3


def up(conn: sqlite3.Connection):
    """Create author_performance table and seed from existing data."""
    # Create the author performance table
    conn.executescript("""
    -- Author performance tracking (adaptive learning)
    CREATE TABLE IF NOT EXISTS author_performance (
        author_name TEXT PRIMARY KEY,

        -- Counts
        total_papers INTEGER DEFAULT 0,
        included_papers INTEGER DEFAULT 0,

        -- Computed metrics
        inclusion_rate REAL DEFAULT 0.0,
        recency_score REAL DEFAULT 0.0,

        -- Tracking
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_included TIMESTAMP,

        -- For trending detection
        recent_velocity REAL DEFAULT 0.0
    );

    CREATE INDEX IF NOT EXISTS idx_author_inclusion ON author_performance(inclusion_rate DESC);
    CREATE INDEX IF NOT EXISTS idx_author_recency ON author_performance(last_included DESC);
    CREATE INDEX IF NOT EXISTS idx_author_composite ON author_performance(inclusion_rate DESC, recency_score DESC);
    """)

    conn.commit()


def down(conn: sqlite3.Connection):
    """Remove author performance tracking."""
    conn.executescript("""
    DROP INDEX IF EXISTS idx_author_composite;
    DROP INDEX IF EXISTS idx_author_recency;
    DROP INDEX IF EXISTS idx_author_inclusion;
    DROP TABLE IF EXISTS author_performance;
    """)

    conn.commit()
