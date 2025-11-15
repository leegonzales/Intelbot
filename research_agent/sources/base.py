"""Base class for research sources."""

from abc import ABC, abstractmethod
from typing import List, Dict


class ResearchSource(ABC):
    """
    Abstract base class for research sources.

    Each source must implement fetch() to return a list of items.
    """

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def fetch(self) -> List[Dict]:
        """
        Fetch items from source.

        Returns:
            List of items with standardized fields:
            - url: str (required)
            - title: str (required)
            - snippet: str (optional)
            - content: str (optional)
            - source: str (required)
            - source_metadata: dict (optional)
            - published_date: datetime (optional)
            - author: str (optional)
            - category: str (optional)
            - tags: List[str] (optional)
        """
        pass

    def _create_item(
        self,
        url: str,
        title: str,
        source: str,
        snippet: str = None,
        content: str = None,
        source_metadata: dict = None,
        published_date = None,
        author: str = None,
        category: str = None,
        tags: List[str] = None
    ) -> Dict:
        """
        Create standardized item dict.

        Args:
            url: Item URL
            title: Item title
            source: Source name
            snippet: Short excerpt
            content: Full content
            source_metadata: Source-specific metadata
            published_date: Publication date
            author: Author name
            category: Category/topic
            tags: List of tags

        Returns:
            Standardized item dict
        """
        return {
            'url': url,
            'title': title,
            'source': source,
            'snippet': snippet,
            'content': content,
            'source_metadata': source_metadata or {},
            'published_date': published_date,
            'author': author,
            'category': category,
            'tags': tags or []
        }
