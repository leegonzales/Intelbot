"""Blog scraper source collector."""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet, clean_html
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class BlogScraperSource(ResearchSource):
    """Scrape articles from blog homepages."""

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.blog_scraper")

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch articles from blog URLs.

        Returns:
            List of blog articles
        """
        items = []

        urls = self.config.get('urls', [])

        for url in urls:
            try:
                # Fetch homepage
                response = requests.get(url, timeout=15, headers={
                    'User-Agent': 'ResearchAgent/1.0 (AI research tracking bot)'
                })
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Try to find article links (this is generic and may need customization)
                articles = self._find_articles(soup, url)

                items.extend(articles)

            except Exception as e:
                self.logger.error(f"Error scraping blog {url}: {e}")
                continue

        return items

    def _find_articles(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """
        Find article links on page.

        This is a generic implementation that tries common patterns.
        May need customization for specific blogs.
        """
        articles = []

        # Look for common article selectors
        selectors = [
            'article',
            '.post',
            '.blog-post',
            '[class*="article"]',
            '[class*="post"]',
        ]

        for selector in selectors:
            for element in soup.select(selector)[:10]:  # Limit to 10 per blog
                try:
                    # Find title and link
                    title_elem = element.find(['h1', 'h2', 'h3'])
                    if not title_elem:
                        continue

                    link_elem = title_elem.find('a') or element.find('a')
                    if not link_elem:
                        continue

                    title = title_elem.get_text().strip()
                    link = link_elem.get('href', '')

                    # Make absolute URL
                    if link.startswith('/'):
                        from urllib.parse import urljoin
                        link = urljoin(base_url, link)

                    # Extract content/snippet
                    content_elem = element.find(['p', '.excerpt', '.summary'])
                    content = content_elem.get_text().strip() if content_elem else ''

                    # Try to find date
                    date_elem = element.find(['time', '.date', '[class*="date"]'])
                    published_date = None
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text()
                        published_date = self._parse_date(date_str)

                    article = self._create_item(
                        url=link,
                        title=title,
                        source=f"blog:{base_url}",
                        snippet=extract_snippet(content, 500),
                        content=content,
                        source_metadata={
                            'blog_url': base_url,
                        },
                        published_date=published_date,
                        tags=['blog', 'article']
                    )

                    articles.append(article)

                except Exception as e:
                    self.logger.error(f"Error parsing article from {base_url}: {e}")
                    continue

            if articles:  # If we found articles with this selector, stop trying others
                break

        return articles

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        from dateutil import parser

        try:
            return parser.parse(date_str)
        except Exception:
            return None
