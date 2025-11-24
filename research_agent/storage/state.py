"""State management using SQLite with FTS5."""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager


class StateManager:
    """
    Manages SQLite database for:
    - Item deduplication
    - Run history tracking
    - Preference learning (phase 2)
    - Full-text search via FTS5
    """

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        # Check FTS5 support (Issue #4 - Critical Fix)
        with self._get_conn() as conn:
            cursor = conn.execute("PRAGMA compile_options")
            options = [row[0] for row in cursor.fetchall()]

            has_fts5 = any('FTS5' in opt for opt in options)

            if not has_fts5:
                raise RuntimeError(
                    "SQLite does not have FTS5 support.\n\n"
                    "On macOS: brew install sqlite\n"
                    "On Ubuntu: sudo apt-get install sqlite3\n"
                    "On Fedora: sudo dnf install sqlite\n\n"
                    "Then reinstall Python to use system SQLite:\n"
                    "pyenv install --force 3.10.x"
                )

        from research_agent.storage.migrations import run_migrations
        run_migrations(self.db_path)

    def is_duplicate(
        self,
        url: str,
        title: str,
        content: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if item is duplicate.

        Returns:
            (is_duplicate, reason)
        """
        with self._get_conn() as conn:
            # 1. Exact URL match
            cursor = conn.execute(
                "SELECT id FROM seen_items WHERE url = ?",
                (url,)
            )
            if cursor.fetchone():
                return (True, "exact_url")

            # 2. Content hash match (if content provided)
            if content:
                content_hash = self._hash_content(content)
                cursor = conn.execute(
                    "SELECT id FROM seen_items WHERE content_hash = ?",
                    (content_hash,)
                )
                if cursor.fetchone():
                    return (True, "content_hash")

            # 3. FTS title similarity
            similar = self._find_similar_titles(title, threshold=0.85)
            if similar:
                return (True, f"similar_title:{similar[0]['id']}")

            return (False, None)

    def _hash_content(self, content: str) -> str:
        """Generate SHA256 hash of normalized content."""
        # Handle None values
        if content is None:
            content = ''
        normalized = content.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _find_similar_titles(
        self,
        title: str,
        threshold: float = 0.85,
        limit: int = 5
    ) -> List[Dict]:
        """
        Use FTS5 to find similar titles.

        Args:
            title: Title to search for
            threshold: BM25 score threshold (0.0-1.0)
            limit: Max results

        Returns:
            List of similar items with scores
        """
        with self._get_conn() as conn:
            # Extract key terms from title for FTS query
            # Simple approach: use all words > 3 chars
            terms = [
                word for word in title.split()
                if len(word) > 3 and word.isalnum()
            ]

            if not terms:
                return []

            # Build FTS query
            fts_query = " OR ".join(terms)

            cursor = conn.execute("""
                SELECT
                    seen_items.id,
                    seen_items.title,
                    seen_items.url,
                    bm25(items_fts) as score
                FROM items_fts
                JOIN seen_items ON items_fts.rowid = seen_items.id
                WHERE items_fts MATCH ?
                ORDER BY score
                LIMIT ?
            """, (fts_query, limit))

            # Normalize BM25 scores and filter by threshold
            results = []
            for row in cursor:
                # BM25 scores are negative (lower is better)
                # Normalize to 0-1 range (higher is better)
                normalized_score = 1 / (1 + abs(row['score']))

                if normalized_score >= threshold:
                    results.append({
                        'id': row['id'],
                        'title': row['title'],
                        'url': row['url'],
                        'score': normalized_score
                    })

            return results

    def add_item(self, item: Dict, conn=None) -> int:
        """
        Add new item to database or return existing ID.

        Issue #5 Fix: Use INSERT OR IGNORE to handle duplicates gracefully.

        Args:
            item: Item dictionary
            conn: Optional database connection (if None, creates new one)

        Returns:
            Item ID (new or existing)
        """
        # Use provided connection or create new one
        if conn is not None:
            return self._add_item_with_conn(conn, item)

        with self._get_conn() as conn:
            return self._add_item_with_conn(conn, item)

    def _add_item_with_conn(self, conn, item: Dict) -> int:
        """Internal method to add item with existing connection."""
        # Try to insert (will be ignored if URL already exists)
        cursor = conn.execute("""
                INSERT OR IGNORE INTO seen_items (
                    url, content_hash, title, snippet, content,
                    source, source_metadata, published_date,
                    author, category, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['url'],
                self._hash_content(item.get('content', '')),
                item['title'],
                item.get('snippet'),
                item.get('content'),
                item['source'],
                json.dumps(item.get('source_metadata')) if item.get('source_metadata') else None,
                item.get('published_date'),
                item.get('author'),
                item.get('category'),
                ','.join(item.get('tags', []))
        ))

        # Get ID (either newly inserted or existing)
        if cursor.lastrowid:
            return cursor.lastrowid
        else:
            # Item already existed, get its ID
            cursor = conn.execute("SELECT id FROM seen_items WHERE url = ?", (item['url'],))
            return cursor.fetchone()[0]

    def filter_new(self, items: List[Dict]) -> List[Dict]:
        """
        Filter list of items to only new ones.

        Args:
            items: List of items to check

        Returns:
            List of new items (not in database)
        """
        new_items = []

        for item in items:
            is_dup, reason = self.is_duplicate(
                item['url'],
                item['title'],
                item.get('content')
            )

            if not is_dup:
                new_items.append(item)

        return new_items

    def get_recent_items(self, days: int = 7, limit: int = 20, max_age_days: int = 30) -> List[Dict]:
        """
        Get recent items from database to supplement digest when few new items.

        CRITICAL: Filters by BOTH first_seen and published_date to prevent stale content.

        Args:
            days: Number of days to look back for first_seen
            limit: Maximum items to return
            max_age_days: Maximum age of published_date (default: 30 days)

        Returns:
            List of recent items formatted like collected items
        """
        with self._get_conn() as conn:
            # TRUST FIX: Prevent old content from appearing in "recent" supplements
            # Must satisfy BOTH conditions:
            # 1. We collected it recently (first_seen within 'days')
            # 2. It was published recently (published_date within 'max_age_days')
            cursor = conn.execute("""
                SELECT
                    url, title, snippet, content, source, source_metadata,
                    author, published_date, category, tags
                FROM seen_items
                WHERE datetime(first_seen) >= datetime('now', '-' || ? || ' days')
                AND (
                    -- Include items with no published_date (will be scored low by recency)
                    published_date IS NULL
                    OR
                    -- Or items published within max_age_days
                    datetime(published_date) >= datetime('now', '-' || ? || ' days')
                )
                ORDER BY first_seen DESC
                LIMIT ?
            """, (days, max_age_days, limit))

            items = []
            for row in cursor.fetchall():
                # Parse source_metadata JSON
                metadata = {}
                if row['source_metadata']:
                    try:
                        metadata = json.loads(row['source_metadata'])
                    except:
                        pass

                # Parse tags
                tags = []
                if row['tags']:
                    try:
                        tags = json.loads(row['tags'])
                    except:
                        tags = row['tags'].split(',') if row['tags'] else []

                # TRUST FIX: Extract date from title if published_date is NULL
                published_date = row['published_date']
                if not published_date:
                    extracted = self._extract_date_from_title(row['title'])
                    if extracted:
                        published_date = extracted

                item = {
                    'url': row['url'],
                    'title': row['title'],
                    'snippet': row['snippet'],
                    'content': row['content'],
                    'source': row['source'],
                    'source_metadata': metadata,
                    'author': row['author'],
                    'published_date': published_date,
                    'category': row['category'],
                    'tags': tags
                }

                # TRUST FIX: Skip items older than max_age_days after extraction
                if published_date:
                    from datetime import datetime, timedelta
                    try:
                        if isinstance(published_date, str):
                            pub_dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        else:
                            pub_dt = published_date

                        # Remove timezone for comparison
                        if hasattr(pub_dt, 'tzinfo') and pub_dt.tzinfo:
                            pub_dt = pub_dt.replace(tzinfo=None)

                        age_days = (datetime.now() - pub_dt).days
                        if age_days > max_age_days:
                            continue  # Skip this item
                    except:
                        pass  # If date parsing fails, include the item

                items.append(item)

            return items

    def record_run(
        self,
        items_found: List[Dict],
        items_new: List[Dict],
        items_included: List[Dict],
        output_path: Optional[Path],
        runtime_seconds: float,
        status: str = 'success',
        error_log: Optional[str] = None
    ) -> int:
        """
        Record a research run in database.

        Returns:
            Run ID
        """
        with self._get_conn() as conn:
            # Insert run record
            cursor = conn.execute("""
                INSERT INTO research_runs (
                    status, items_found, items_new, items_included,
                    output_path, runtime_seconds, error_log
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                status,
                len(items_found),
                len(items_new),
                len(items_included),
                str(output_path) if output_path else None,
                runtime_seconds,
                error_log
            ))

            run_id = cursor.lastrowid

            # Issue #5 Fix: Build URL-to-rank mapping for correct item linking
            url_to_rank = {
                item['url']: idx
                for idx, item in enumerate(items_included)
            }

            # Add new items to seen_items and link to run
            for item in items_new:
                item_id = self.add_item(item, conn=conn)

                # Link to run if included in digest (compare by URL, not object reference)
                if item['url'] in url_to_rank:
                    rank = url_to_rank[item['url']]
                    conn.execute("""
                        INSERT INTO run_items (run_id, item_id, rank)
                        VALUES (?, ?, ?)
                    """, (run_id, item_id, rank))

            return run_id

    def get_recent_runs(self, limit: int = 10) -> List[Dict]:
        """Get recent research runs."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM research_runs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor]

    def search_history(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search historical items using FTS5.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching items with snippets
        """
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT
                    seen_items.*,
                    snippet(items_fts, 1, '<mark>', '</mark>', '...', 32) as snippet_html,
                    bm25(items_fts) as relevance
                FROM items_fts
                JOIN seen_items ON items_fts.rowid = seen_items.id
                WHERE items_fts MATCH ?
                ORDER BY relevance
                LIMIT ?
            """, (query, limit))

            return [dict(row) for row in cursor]

    def _extract_date_from_title(self, title: str) -> str:
        """
        Extract date from title for blog posts that embed dates.

        Example: "Building Effective AgentsDec 19, 2024" -> "2024-12-19"
        """
        import re
        from dateutil import parser as date_parser

        # Common patterns in Anthropic blog titles
        # Pattern: "MonthName DD, YYYY" (e.g., "Dec 19, 2024")
        month_day_year = re.search(r'([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(\d{4})', title)
        if month_day_year:
            try:
                date_str = f"{month_day_year.group(1)} {month_day_year.group(2)}, {month_day_year.group(3)}"
                parsed = date_parser.parse(date_str)
                return parsed.strftime('%Y-%m-%d')
            except:
                pass

        # Fallback: try dateutil's fuzzy parsing
        try:
            parsed = date_parser.parse(title, fuzzy=True)
            # Only return if year is reasonable (2020-2030)
            if 2020 <= parsed.year <= 2030:
                return parsed.strftime('%Y-%m-%d')
        except:
            pass

        return None

    def get_database_stats(self) -> Dict:
        """
        Get comprehensive database statistics.

        Returns:
            Dict with database metrics including:
            - total_items: Total items in database
            - total_runs: Total completed runs
            - oldest_item_date: Date of oldest item
            - newest_item_date: Date of newest item
            - items_last_7_days: Items collected in last 7 days
            - items_last_30_days: Items collected in last 30 days
            - top_sources: Most active sources (top 5)
        """
        with self._get_conn() as conn:
            stats = {}

            # Total items
            cursor = conn.execute("SELECT COUNT(*) as count FROM seen_items")
            stats['total_items'] = cursor.fetchone()['count']

            # Total runs
            cursor = conn.execute("SELECT COUNT(*) as count FROM research_runs")
            stats['total_runs'] = cursor.fetchone()['count']

            # Date range
            cursor = conn.execute("""
                SELECT
                    MIN(published_date) as oldest,
                    MAX(published_date) as newest
                FROM seen_items
                WHERE published_date IS NOT NULL
            """)
            row = cursor.fetchone()
            stats['oldest_item_date'] = row['oldest']
            stats['newest_item_date'] = row['newest']

            # Recent items (last 7 and 30 days)
            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM seen_items
                WHERE first_seen >= datetime('now', '-7 days')
            """)
            stats['items_last_7_days'] = cursor.fetchone()['count']

            cursor = conn.execute("""
                SELECT COUNT(*) as count
                FROM seen_items
                WHERE first_seen >= datetime('now', '-30 days')
            """)
            stats['items_last_30_days'] = cursor.fetchone()['count']

            # Top sources
            cursor = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM seen_items
                GROUP BY source
                ORDER BY count DESC
                LIMIT 5
            """)
            stats['top_sources'] = [
                {'source': row['source'], 'count': row['count']}
                for row in cursor.fetchall()
            ]

            return stats
