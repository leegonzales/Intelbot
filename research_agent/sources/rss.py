"""RSS feed source collector."""

import feedparser
from typing import List, Dict
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet, clean_html


class RSSSource(ResearchSource):
    """Collect items from RSS feeds."""

    def fetch(self) -> List[Dict]:
        """
        Fetch items from RSS feeds.

        Returns:
            List of feed items
        """
        items = []

        feeds = self.config.get('feeds', [])

        for feed_config in feeds:
            try:
                feed_url = feed_config.get('url')
                feed_name = feed_config.get('name', feed_url)

                # Parse feed
                feed = feedparser.parse(feed_url)

                for entry in feed.entries:
                    # Only include items from last 7 days
                    published_date = self._parse_date(entry)
                    if published_date and (datetime.now() - published_date).days > 7:
                        continue

                    # Extract content
                    content = self._extract_content(entry)

                    item = self._create_item(
                        url=entry.get('link', ''),
                        title=entry.get('title', ''),
                        source=f"rss:{feed_name}",
                        snippet=extract_snippet(clean_html(content), 500),
                        content=clean_html(content),
                        source_metadata={
                            'feed_name': feed_name,
                            'feed_url': feed_url,
                        },
                        published_date=published_date,
                        author=entry.get('author'),
                        tags=self._extract_tags(entry, feed_name)
                    )

                    items.append(item)

            except Exception as e:
                print(f"Error fetching RSS feed {feed_config.get('url')}: {e}")
                continue

        return items

    def _parse_date(self, entry) -> datetime:
        """Parse date from entry."""
        # Try different date fields
        for field in ['published_parsed', 'updated_parsed']:
            if hasattr(entry, field) and getattr(entry, field):
                import time
                return datetime.fromtimestamp(time.mktime(getattr(entry, field)))

        return None

    def _extract_content(self, entry) -> str:
        """Extract content from entry."""
        # Try different content fields
        if hasattr(entry, 'content') and entry.content:
            return entry.content[0].get('value', '')

        if hasattr(entry, 'summary'):
            return entry.summary

        if hasattr(entry, 'description'):
            return entry.description

        return ''

    def _extract_tags(self, entry, feed_name: str) -> List[str]:
        """Extract tags from entry."""
        tags = ['rss', feed_name.lower().replace(' ', '-')]

        # Add entry tags if available
        if hasattr(entry, 'tags'):
            tags.extend([tag.term.lower() for tag in entry.tags])

        # Extract keywords
        keywords = ['ai', 'llm', 'agent', 'rlhf', 'claude', 'gpt']
        text = (entry.get('title', '') + ' ' + self._extract_content(entry)).lower()

        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)

        return list(set(tags))
