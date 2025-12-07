"""Source collection agent."""

from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from research_agent.utils.logger import get_logger


class SourceAgent:
    """
    Coordinates collection from multiple sources.

    Runs sources in parallel and aggregates results.
    """

    def __init__(self, config, state_manager):
        self.config = config
        self.state = state_manager
        self.logger = get_logger("agents.source")
        self.sources = []

        # Initialize enabled sources
        self._init_sources()

    def _init_sources(self):
        """Initialize enabled sources from config."""
        from research_agent.sources.arxiv import ArxivSource
        from research_agent.sources.hackernews import HackerNewsSource
        from research_agent.sources.rss import RSSSource
        from research_agent.sources.blog_scraper import BlogScraperSource
        from research_agent.sources.semantic_scholar import SemanticScholarSource

        sources_config = self.config.sources

        # arXiv
        if hasattr(sources_config, 'arxiv') and sources_config.arxiv.get('enabled', False):
            self.sources.append(ArxivSource(sources_config.arxiv))

        # Semantic Scholar (high-impact papers with citation data)
        if hasattr(sources_config, 'semantic_scholar') and sources_config.semantic_scholar.get('enabled', False):
            self.sources.append(SemanticScholarSource(sources_config.semantic_scholar))

        # Hacker News
        if hasattr(sources_config, 'hackernews') and sources_config.hackernews.get('enabled', False):
            self.sources.append(HackerNewsSource(sources_config.hackernews))

        # RSS
        if hasattr(sources_config, 'rss') and sources_config.rss.get('enabled', False):
            self.sources.append(RSSSource(sources_config.rss))

        # Blogs
        if hasattr(sources_config, 'blogs') and sources_config.blogs.get('enabled', False):
            self.sources.append(BlogScraperSource(sources_config.blogs))

    def collect_all(self) -> List[Dict]:
        """
        Collect items from all sources in parallel.

        Returns:
            List of items (not deduplicated)
        """
        all_items = []

        if not self.sources:
            self.logger.warning("No sources enabled")
            return all_items

        with ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            # Submit all source tasks
            futures = {
                executor.submit(source.fetch): source
                for source in self.sources
            }

            # Collect results as they complete
            for future in as_completed(futures):
                source = futures[future]
                try:
                    items = future.result()
                    self.logger.info(f"Collected {len(items)} items from {source.__class__.__name__}")
                    all_items.extend(items)
                except Exception as e:
                    # Log error but continue with other sources
                    self.logger.error(f"Error fetching from {source.__class__.__name__}: {e}")

        self.logger.info(f"Total items collected: {len(all_items)}")
        return all_items
