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

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.arxiv")
        self.tier = config.get('tier', 1)  # arXiv is tier 1 by default
        self.priority = config.get('priority', 'high')

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch recent papers from arXiv.

        Returns:
            List of paper items
        """
        items = []

        # Get categories from config
        categories = self.config.get('categories', ['cs.AI', 'cs.LG', 'cs.CL'])
        max_results = self.config.get('max_results', 20)

        for category in categories:
            try:
                # Search for recent papers in category
                search = arxiv.Search(
                    query=f"cat:{category}",
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in search.results():
                    # Only include papers from last 7 days
                    # Remove timezone info for comparison
                    published_naive = result.published.replace(tzinfo=None)
                    if (datetime.now() - published_naive).days > 7:
                        continue

                    item = self._create_item(
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

                    items.append(item)

            except Exception as e:
                self.logger.error(f"Error fetching arXiv category {category}: {e}")
                continue

        return items

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
