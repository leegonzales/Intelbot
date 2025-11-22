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

    # ============================================
    # AUTHOR PERFORMANCE TRACKING
    # ============================================

    def record_author_inclusion(
        self,
        author_name: str,
        item_id: int,
        included: bool,
        published_date: Optional[datetime] = None
    ):
        """
        Record an author appearance and update performance metrics.

        Args:
            author_name: Normalized author name
            item_id: Item ID from seen_items
            included: Whether item was included in digest
            published_date: Publication date for recency scoring
        """
        from research_agent.utils.authors import normalize_author_name

        # Normalize the author name
        author_name = normalize_author_name(author_name)

        with self._get_conn() as conn:
            # Check if author exists
            cursor = conn.execute(
                "SELECT total_papers, included_papers FROM author_performance WHERE author_name = ?",
                (author_name,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing author
                total = row['total_papers'] + 1
                included_count = row['included_papers'] + (1 if included else 0)
                inclusion_rate = included_count / total if total > 0 else 0.0

                if included:
                    conn.execute("""
                        UPDATE author_performance
                        SET total_papers = ?,
                            included_papers = ?,
                            inclusion_rate = ?,
                            last_seen = CURRENT_TIMESTAMP,
                            last_included = CURRENT_TIMESTAMP
                        WHERE author_name = ?
                    """, (total, included_count, inclusion_rate, author_name))
                else:
                    conn.execute("""
                        UPDATE author_performance
                        SET total_papers = ?,
                            included_papers = ?,
                            inclusion_rate = ?,
                            last_seen = CURRENT_TIMESTAMP
                        WHERE author_name = ?
                    """, (total, included_count, inclusion_rate, author_name))
            else:
                # Insert new author
                inclusion_rate = 1.0 if included else 0.0
                last_included = datetime.now() if included else None

                conn.execute("""
                    INSERT INTO author_performance (
                        author_name, total_papers, included_papers,
                        inclusion_rate, last_included
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    author_name,
                    1,
                    1 if included else 0,
                    inclusion_rate,
                    last_included
                ))

    def update_author_scores(self):
        """
        Update recency and velocity scores for all authors.

        Should be called periodically (e.g., after each research run).
        """
        import math

        with self._get_conn() as conn:
            # Get all authors
            cursor = conn.execute("""
                SELECT author_name, last_included, first_seen, last_seen, total_papers
                FROM author_performance
            """)

            now = datetime.now()

            for row in cursor:
                author_name = row['author_name']
                last_included = row['last_included']
                first_seen = datetime.fromisoformat(row['first_seen']) if row['first_seen'] else now
                last_seen = datetime.fromisoformat(row['last_seen']) if row['last_seen'] else now
                total_papers = row['total_papers']

                # Calculate recency score (exponential decay)
                # 1.0 at t=0, 0.5 at t=90 days, 0.1 at t=180 days
                if last_included:
                    last_included_dt = datetime.fromisoformat(last_included)
                    days_since_inclusion = (now - last_included_dt).days
                    recency_score = math.exp(-days_since_inclusion / 90.0)
                else:
                    recency_score = 0.0

                # Calculate velocity (papers per month)
                days_active = max((last_seen - first_seen).days, 1)
                months_active = days_active / 30.0
                velocity = total_papers / months_active if months_active > 0 else 0.0

                # Update scores
                conn.execute("""
                    UPDATE author_performance
                    SET recency_score = ?,
                        recent_velocity = ?
                    WHERE author_name = ?
                """, (recency_score, velocity, author_name))

    def get_top_authors(
        self,
        limit: int = 20,
        min_inclusion_rate: float = 0.3,
        min_papers: int = 2
    ) -> List[str]:
        """
        Get top-performing authors for enhanced arXiv queries.

        Scoring formula: 0.5 * inclusion_rate + 0.3 * recency_score + 0.2 * velocity

        Args:
            limit: Max number of authors to return
            min_inclusion_rate: Minimum inclusion rate (0.0-1.0)
            min_papers: Minimum number of papers

        Returns:
            List of author names, sorted by composite score
        """
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT
                    author_name,
                    inclusion_rate,
                    recency_score,
                    recent_velocity,
                    (0.5 * inclusion_rate + 0.3 * recency_score + 0.2 * LEAST(recent_velocity, 1.0)) as composite_score
                FROM author_performance
                WHERE inclusion_rate >= ?
                  AND total_papers >= ?
                ORDER BY composite_score DESC
                LIMIT ?
            """, (min_inclusion_rate, min_papers, limit))

            return [row['author_name'] for row in cursor]

    def get_author_stats(self, author_name: str) -> Optional[Dict]:
        """
        Get detailed statistics for an author.

        Args:
            author_name: Author name

        Returns:
            Dict with author stats or None if not found
        """
        from research_agent.utils.authors import normalize_author_name

        author_name = normalize_author_name(author_name)

        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT *
                FROM author_performance
                WHERE author_name = ?
            """, (author_name,))

            row = cursor.fetchone()
            return dict(row) if row else None

    def seed_authors_from_existing_items(self):
        """
        Seed author_performance table from existing seen_items.

        This is called during migration or when enabling author tracking
        for the first time to bootstrap from historical data.
        """
        from research_agent.utils.authors import parse_author_string

        self.logger.info("Seeding author performance from existing items...")

        with self._get_conn() as conn:
            # Get all arXiv items with authors
            cursor = conn.execute("""
                SELECT id, author, included_in_digest, published_date
                FROM seen_items
                WHERE source = 'arxiv'
                  AND author IS NOT NULL
                  AND author != ''
            """)

            items = cursor.fetchall()
            self.logger.info(f"Found {len(items)} arXiv items to process")

            author_counts = {}  # author_name -> {total, included, dates}

            # First pass: collect all author data
            for item in items:
                authors = parse_author_string(item['author'])
                included = bool(item['included_in_digest'])
                pub_date = item['published_date']

                for author in authors:
                    if author not in author_counts:
                        author_counts[author] = {
                            'total': 0,
                            'included': 0,
                            'dates': []
                        }

                    author_counts[author]['total'] += 1
                    if included:
                        author_counts[author]['included'] += 1
                    if pub_date:
                        author_counts[author]['dates'].append(pub_date)

            # Second pass: insert/update author records
            for author_name, stats in author_counts.items():
                total = stats['total']
                included = stats['included']
                inclusion_rate = included / total if total > 0 else 0.0

                # Get most recent date where this author was included
                if stats['dates']:
                    last_pub = max(stats['dates'])
                else:
                    last_pub = None

                # Check if author already exists
                cursor = conn.execute(
                    "SELECT author_name FROM author_performance WHERE author_name = ?",
                    (author_name,)
                )

                if cursor.fetchone():
                    # Update existing
                    conn.execute("""
                        UPDATE author_performance
                        SET total_papers = total_papers + ?,
                            included_papers = included_papers + ?,
                            inclusion_rate = (included_papers + ?) / (total_papers + ?),
                            last_seen = CURRENT_TIMESTAMP
                        WHERE author_name = ?
                    """, (total, included, included, total, author_name))
                else:
                    # Insert new
                    conn.execute("""
                        INSERT INTO author_performance (
                            author_name, total_papers, included_papers,
                            inclusion_rate, last_included
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (author_name, total, included, inclusion_rate, last_pub))

            self.logger.info(f"Seeded {len(author_counts)} authors")

            # Update all scores
            self.update_author_scores()

            self.logger.info("Author seeding complete")
