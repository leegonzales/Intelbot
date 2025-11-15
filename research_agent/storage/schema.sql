-- ============================================
-- CORE TABLES
-- ============================================

-- Seen items: deduplication and tracking
CREATE TABLE IF NOT EXISTS seen_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT,
    content TEXT,
    source TEXT NOT NULL,
    source_metadata TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    times_surfaced INTEGER DEFAULT 1,
    included_in_digest BOOLEAN DEFAULT 0,

    -- Metadata
    author TEXT,
    published_date TIMESTAMP,
    category TEXT,
    tags TEXT
);

-- Research runs: audit trail
CREATE TABLE IF NOT EXISTS research_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK(status IN ('success', 'partial', 'failed')),
    items_found INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    items_included INTEGER DEFAULT 0,
    output_path TEXT,
    runtime_seconds REAL,
    error_log TEXT,
    config_snapshot TEXT
);

-- Items included in each run (many-to-many)
CREATE TABLE IF NOT EXISTS run_items (
    run_id INTEGER REFERENCES research_runs(id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES seen_items(id) ON DELETE CASCADE,
    rank INTEGER,
    theme TEXT,
    PRIMARY KEY (run_id, item_id)
);

-- ============================================
-- PREFERENCE LEARNING (Phase 2 - schema ready)
-- ============================================

-- Engagement tracking
CREATE TABLE IF NOT EXISTS item_engagement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES seen_items(id) ON DELETE CASCADE,
    engagement_type TEXT CHECK(engagement_type IN ('opened', 'rated', 'shared', 'archived')),
    engagement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Optional metrics
    time_spent_seconds INTEGER,
    explicit_rating INTEGER CHECK(explicit_rating IN (-1, 0, 1)),
    notes TEXT
);

-- Source performance
CREATE TABLE IF NOT EXISTS source_performance (
    source TEXT PRIMARY KEY,
    total_items INTEGER DEFAULT 0,
    included_items INTEGER DEFAULT 0,
    engaged_items INTEGER DEFAULT 0,

    -- Computed metrics
    inclusion_rate REAL,
    engagement_rate REAL,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topic tracking (auto-extracted from engaged content)
CREATE TABLE IF NOT EXISTS learned_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT UNIQUE NOT NULL,
    relevance_score REAL DEFAULT 0.5,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    engagement_count INTEGER DEFAULT 0
);

-- ============================================
-- FULL-TEXT SEARCH (FTS5)
-- ============================================

-- Virtual FTS table for content search
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    title,
    snippet,
    content,
    tags,
    content='seen_items',
    content_rowid='id',
    tokenize='porter unicode61 remove_diacritics 2'
);

-- ============================================
-- TRIGGERS
-- ============================================

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS items_fts_insert AFTER INSERT ON seen_items BEGIN
    INSERT INTO items_fts(rowid, title, snippet, content, tags)
    VALUES (new.id, new.title, new.snippet, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS items_fts_update AFTER UPDATE ON seen_items BEGIN
    UPDATE items_fts
    SET title = new.title,
        snippet = new.snippet,
        content = new.content,
        tags = new.tags
    WHERE rowid = new.id;
END;

CREATE TRIGGER IF NOT EXISTS items_fts_delete AFTER DELETE ON seen_items BEGIN
    DELETE FROM items_fts WHERE rowid = old.id;
END;

-- ============================================
-- INDICES
-- ============================================

CREATE INDEX IF NOT EXISTS idx_seen_url ON seen_items(url);
CREATE INDEX IF NOT EXISTS idx_seen_source ON seen_items(source);
CREATE INDEX IF NOT EXISTS idx_seen_date ON seen_items(first_seen);
CREATE INDEX IF NOT EXISTS idx_seen_hash ON seen_items(content_hash);
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON research_runs(timestamp);
CREATE INDEX IF NOT EXISTS idx_engagement_item ON item_engagement(item_id);
CREATE INDEX IF NOT EXISTS idx_engagement_type ON item_engagement(engagement_type);
