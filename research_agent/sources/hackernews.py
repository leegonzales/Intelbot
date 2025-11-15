"""Hacker News source collector."""

import requests
from typing import List, Dict
from datetime import datetime

from research_agent.sources.base import ResearchSource
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class HackerNewsSource(ResearchSource):
    """Collect items from Hacker News."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.hackernews")

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch items from Hacker News.

        Returns:
            List of HN items
        """
        items = []

        endpoints = self.config.get('endpoints', ['topstories', 'beststories'])
        max_items = self.config.get('max_items', 30)
        filter_keywords = self.config.get('filter_keywords', [])

        for endpoint in endpoints:
            try:
                # Fetch story IDs
                response = requests.get(
                    f"{self.BASE_URL}/{endpoint}.json",
                    timeout=10
                )
                response.raise_for_status()
                story_ids = response.json()[:max_items]

                # Fetch story details
                for story_id in story_ids:
                    try:
                        story = self._fetch_story(story_id)

                        if not story:
                            continue

                        # Filter by keywords
                        if filter_keywords and not self._matches_keywords(story, filter_keywords):
                            continue

                        # Only include stories with significant engagement
                        if story.get('score', 0) < 100:
                            continue

                        item = self._create_item(
                            url=story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                            title=story.get('title', ''),
                            source='hackernews',
                            snippet=story.get('text', '')[:500] if story.get('text') else None,
                            source_metadata={
                                'hn_id': story_id,
                                'points': story.get('score', 0),
                                'comments': story.get('descendants', 0),
                                'hn_url': f"https://news.ycombinator.com/item?id={story_id}",
                            },
                            published_date=datetime.fromtimestamp(story.get('time', 0)),
                            author=story.get('by'),
                            tags=self._extract_tags(story, filter_keywords)
                        )

                        items.append(item)

                    except Exception as e:
                        self.logger.error(f"Error fetching HN story {story_id}: {e}")
                        continue

            except Exception as e:
                self.logger.error(f"Error fetching HN {endpoint}: {e}")
                continue

        return items

    def _fetch_story(self, story_id: int) -> Dict:
        """Fetch single story details."""
        response = requests.get(
            f"{self.BASE_URL}/item/{story_id}.json",
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def _matches_keywords(self, story: Dict, keywords: List[str]) -> bool:
        """Check if story matches any keyword."""
        text = (story.get('title', '') + ' ' + story.get('text', '')).lower()
        return any(keyword.lower() in text for keyword in keywords)

    def _extract_tags(self, story: Dict, filter_keywords: List[str]) -> List[str]:
        """Extract tags from story."""
        tags = ['hackernews']

        text = (story.get('title', '') + ' ' + story.get('text', '')).lower()

        # Add matching keywords as tags
        for keyword in filter_keywords:
            if keyword.lower() in text:
                tags.append(keyword.lower().replace(' ', '-'))

        return list(set(tags))
