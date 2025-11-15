"""arXiv source collector."""

import arxiv
from typing import List, Dict
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet


class ArxivSource(ResearchSource):
    """Collect papers from arXiv."""

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
                    if (datetime.now() - result.published).days > 7:
                        continue

                    item = self._create_item(
                        url=result.entry_id,
                        title=result.title,
                        source='arxiv',
                        snippet=extract_snippet(result.summary, 500),
                        content=result.summary,
                        source_metadata={
                            'arxiv_id': result.entry_id.split('/')[-1],
                            'categories': [c.name for c in result.categories],
                            'pdf_url': result.pdf_url,
                        },
                        published_date=result.published,
                        author=', '.join([a.name for a in result.authors[:3]]),
                        category=category,
                        tags=self._extract_tags(result)
                    )

                    items.append(item)

            except Exception as e:
                print(f"Error fetching arXiv category {category}: {e}")
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
