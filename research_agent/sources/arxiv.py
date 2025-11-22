"""arXiv source collector."""

import arxiv
from typing import List, Dict
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class ArxivSource(ResearchSource):
    """Collect papers from arXiv."""

    def __init__(self, config, state_manager=None):
        super().__init__(config)
        self.logger = get_logger("sources.arxiv")
        self.tier = config.get('tier', 1)  # arXiv is tier 1 by default
        self.priority = config.get('priority', 'high')
        self.state_manager = state_manager  # For author-based queries

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch recent papers from arXiv using multi-pass strategy.

        Pass 1: Category-based search (existing behavior)
        Pass 2: High-value author search (adaptive learning)
        Pass 3: Keyword-based search (targeted discovery)

        Returns:
            List of paper items
        """
        items = []
        seen_urls = set()  # Deduplicate across passes

        # Pass 1: Category-based search
        self.logger.info("Pass 1: Category-based search")
        category_items = self._category_search(seen_urls)
        items.extend(category_items)
        self.logger.info(f"  Found {len(category_items)} papers from categories")

        # Pass 2: Author-based search (if state manager provided)
        if self.state_manager and self.config.get('author_tracking_enabled', True):
            self.logger.info("Pass 2: High-value author search")
            author_items = self._author_search(seen_urls)
            items.extend(author_items)
            self.logger.info(f"  Found {len(author_items)} papers from tracked authors")

        # Pass 3: Keyword-based search (if enabled)
        if self.config.get('keyword_search_enabled', False):
            self.logger.info("Pass 3: Keyword-based search")
            keyword_items = self._keyword_search(seen_urls)
            items.extend(keyword_items)
            self.logger.info(f"  Found {len(keyword_items)} papers from keywords")

        self.logger.info(f"Total items collected: {len(items)}")
        return items

    def _category_search(self, seen_urls: set) -> List[Dict]:
        """Pass 1: Category-based search (existing behavior)."""
        items = []
        categories = self.config.get('categories', ['cs.AI', 'cs.LG', 'cs.CL'])
        max_results = self.config.get('max_results', 20)
        lookback_days = self.config.get('lookback_days', 7)

        for category in categories:
            try:
                search = arxiv.Search(
                    query=f"cat:{category}",
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in search.results():
                    # Only include recent papers
                    published_naive = result.published.replace(tzinfo=None)
                    if (datetime.now() - published_naive).days > lookback_days:
                        continue

                    # Skip if already seen
                    if result.entry_id in seen_urls:
                        continue

                    item = self._create_item_from_result(result, category)
                    items.append(item)
                    seen_urls.add(result.entry_id)

            except Exception as e:
                self.logger.error(f"Error fetching arXiv category {category}: {e}")
                continue

        return items

    def _author_search(self, seen_urls: set) -> List[Dict]:
        """Pass 2: Search for papers by high-performing authors."""
        if not self.state_manager:
            return []

        items = []

        # Get top authors from state manager
        top_authors = self.state_manager.get_top_authors(
            limit=self.config.get('max_tracked_authors', 20),
            min_inclusion_rate=self.config.get('min_author_inclusion_rate', 0.3),
            min_papers=self.config.get('min_author_papers', 2)
        )

        if not top_authors:
            self.logger.info("  No high-value authors found yet")
            return []

        self.logger.info(f"  Searching for papers by {len(top_authors)} top authors")

        # Limit papers per author to avoid spam
        max_per_author = self.config.get('max_papers_per_author', 5)
        lookback_days = self.config.get('lookback_days', 7)

        for author_name in top_authors:
            try:
                # arXiv author search
                search = arxiv.Search(
                    query=f"au:{author_name}",
                    max_results=max_per_author,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in search.results():
                    # Only include recent papers
                    published_naive = result.published.replace(tzinfo=None)
                    if (datetime.now() - published_naive).days > lookback_days:
                        continue

                    # Skip if already seen
                    if result.entry_id in seen_urls:
                        continue

                    item = self._create_item_from_result(result, 'author-tracked')
                    # Mark as author-tracked for debugging
                    item['source_metadata']['discovery_method'] = 'author'
                    item['source_metadata']['tracked_author'] = author_name

                    items.append(item)
                    seen_urls.add(result.entry_id)

            except Exception as e:
                self.logger.error(f"Error fetching papers for author {author_name}: {e}")
                continue

        return items

    def _keyword_search(self, seen_urls: set) -> List[Dict]:
        """Pass 3: Search for papers by high-value keywords."""
        items = []
        keywords = self.config.get('search_keywords', [
            'constitutional AI',
            'RLHF',
            'prompt engineering',
            'tool use',
            'retrieval augmented',
            'agent',
            'alignment'
        ])

        max_results_per_keyword = self.config.get('max_results_per_keyword', 5)
        lookback_days = self.config.get('lookback_days', 7)

        for keyword in keywords:
            try:
                # Search across all CS categories
                search = arxiv.Search(
                    query=f'all:"{keyword}" AND (cat:cs.* OR cat:stat.ML)',
                    max_results=max_results_per_keyword,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in search.results():
                    # Only include recent papers
                    published_naive = result.published.replace(tzinfo=None)
                    if (datetime.now() - published_naive).days > lookback_days:
                        continue

                    # Skip if already seen
                    if result.entry_id in seen_urls:
                        continue

                    item = self._create_item_from_result(result, 'keyword-tracked')
                    item['source_metadata']['discovery_method'] = 'keyword'
                    item['source_metadata']['search_keyword'] = keyword

                    items.append(item)
                    seen_urls.add(result.entry_id)

            except Exception as e:
                self.logger.error(f"Error fetching papers for keyword '{keyword}': {e}")
                continue

        return items

    def _create_item_from_result(self, result, category: str) -> Dict:
        """Create item dict from arXiv search result."""
        return self._create_item(
            url=result.entry_id,
            title=result.title,
            source='arxiv',
            snippet=extract_snippet(result.summary, 500),
            content=result.summary,
            source_metadata={
                'arxiv_id': result.entry_id.split('/')[-1],
                'categories': [c.name if hasattr(c, 'name') else str(c) for c in result.categories],
                'pdf_url': result.pdf_url,
                'tier': self.tier,
                'priority': self.priority,
            },
            published_date=result.published,
            author=', '.join([a.name for a in result.authors[:3]]),
            category=category,
            tags=self._extract_tags(result)
        )

    def _extract_tags(self, result) -> List[str]:
        """Extract tags from arXiv result."""
        tags = ['research', 'paper']

        # Add primary category
        if result.primary_category:
            tags.append(result.primary_category.replace('.', '-'))

        # Extract keywords from title and summary
        keywords = ['agent', 'llm', 'transformer', 'rlhf', 'prompt', 'alignment']
        text = (result.title + ' ' + result.summary).lower()

        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)

        return list(set(tags))
