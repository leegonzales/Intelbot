"""RSS feed source collector."""

import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime, timedelta
import re

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet, clean_html
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class RSSSource(ResearchSource):
    """Collect items from RSS feeds."""

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.rss")

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
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

                    # Extract content from RSS feed
                    rss_content = self._extract_content(entry)
                    snippet = extract_snippet(clean_html(rss_content), 500)

                    # Extract tier and priority from feed config
                    tier = feed_config.get('tier', 3)  # Default to tier 3
                    priority = feed_config.get('priority', 'medium')
                    perspective = feed_config.get('perspective')
                    focus = feed_config.get('focus')

                    # Fetch full article content from URL for Tier 1 and 2 sources
                    full_content = clean_html(rss_content)
                    if tier in [1, 2]:
                        article_url = entry.get('link', '')
                        if article_url:
                            self.logger.info(f"Fetching full article: {entry.get('title', '')[:50]}...")
                            fetched_content = self._fetch_full_article(article_url, entry.get('title', ''))
                            if fetched_content and len(fetched_content) > len(full_content):
                                full_content = fetched_content
                                # Update snippet if we got better content
                                if not snippet or len(fetched_content) > len(snippet):
                                    snippet = fetched_content[:500]

                    item = self._create_item(
                        url=entry.get('link', ''),
                        title=entry.get('title', ''),
                        source=f"rss:{feed_name}",
                        snippet=snippet,
                        content=full_content,
                        source_metadata={
                            'feed_name': feed_name,
                            'feed_url': feed_url,
                            'tier': tier,
                            'priority': priority,
                            'perspective': perspective,
                            'focus': focus,
                            'author': feed_config.get('author'),
                        },
                        published_date=published_date,
                        author=entry.get('author') or feed_config.get('author'),
                        tags=self._extract_tags(entry, feed_name)
                    )

                    items.append(item)

            except Exception as e:
                self.logger.error(f"Error fetching RSS feed {feed_config.get('url')}: {e}")
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

    def _fetch_full_article(self, url: str, title: str) -> str:
        """
        Fetch and extract full article content from a URL.

        Args:
            url: Article URL
            title: Article title (for logging)

        Returns:
            Full article text or empty string if failed
        """
        try:
            # Fetch the article page
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'ResearchAgent/1.0 (AI research tracking bot)'
            })
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()

            # Try multiple content extraction strategies
            article_content = None

            # Site-specific handling for DeepMind and Google blogs
            if 'deepmind.google' in url or 'googleblog.com' in url or 'blog.google' in url:
                main_tag = soup.find('main') or soup.find('[role="main"]')
                if main_tag:
                    article_content = main_tag

            # Strategy 1: Look for article tag
            if not article_content:
                article_tag = soup.find('article')
                if article_tag:
                    article_content = article_tag

            # Strategy 2: Look for main content area
            if not article_content:
                main_tag = soup.find('main') or soup.find('[role="main"]')
                if main_tag:
                    article_content = main_tag

            # Strategy 3: Look for common blog content classes
            if not article_content:
                for selector in ['[class*="content"]', '[class*="article"]', '[class*="post"]']:
                    content = soup.select_one(selector)
                    if content:
                        article_content = content
                        break

            # Strategy 4: Fall back to body
            if not article_content:
                article_content = soup.find('body')

            if article_content:
                # Extract all text, preserving paragraph structure
                paragraphs = []
                for elem in article_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                    text = elem.get_text().strip()
                    if text and len(text) > 20:  # Skip very short snippets
                        paragraphs.append(text)

                full_text = '\n\n'.join(paragraphs)

                # Clean up extra whitespace
                full_text = re.sub(r'\n{3,}', '\n\n', full_text)
                full_text = re.sub(r' {2,}', ' ', full_text)

                self.logger.debug(f"Extracted {len(full_text)} chars from {url}")
                return full_text

            return ''

        except Exception as e:
            self.logger.error(f"Error fetching full article from {url}: {e}")
            return ''
