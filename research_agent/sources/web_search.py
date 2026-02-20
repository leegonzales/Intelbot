"""Brave Search web search source collector."""

import os
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet, clean_html
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class WebSearchSource(ResearchSource):
    """
    Collect items from Brave Search News API.

    Targets AI agent marketplace and crypto-related topics
    that aren't well covered by academic/RSS sources.
    """

    BASE_URL = "https://api.search.brave.com/res/v1/news/search"

    DEFAULT_QUERIES = [
        "AI agent marketplace platform",
        "AI agents crypto blockchain marketplace",
        "autonomous AI agents token economy",
        "decentralized AI agent marketplace",
        "AI agent crypto trading autonomous",
    ]

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.web_search")

        self.api_key = os.environ.get('BRAVE_SEARCH_API_KEY', '')
        self.queries = config.get('queries', self.DEFAULT_QUERIES)
        self.tier = config.get('tier', 3)
        self.freshness = config.get('freshness', 'pw')  # past week
        self.results_per_query = config.get('results_per_query', 10)
        self.max_queries_per_run = config.get('max_queries_per_run', 5)
        self.request_delay = config.get('request_delay', 1.0)
        self.use_news_api = config.get('use_news_api', True)

    def fetch(self) -> List[Dict]:
        """
        Fetch items from Brave Search across configured queries.

        Returns:
            List of search result items, deduplicated by URL.
        """
        if not self.api_key:
            self.logger.warning(
                "BRAVE_SEARCH_API_KEY not set, skipping web search source"
            )
            return []

        all_items = []
        seen_urls = set()

        queries = self.queries[:self.max_queries_per_run]

        for i, query in enumerate(queries):
            try:
                results = self._search(query)

                for result in results:
                    item = self._result_to_item(result, query)
                    if item and item['url'] not in seen_urls:
                        seen_urls.add(item['url'])
                        all_items.append(item)

                self.logger.info(
                    f"Query '{query}': {len(results)} results"
                )

            except Exception as e:
                self.logger.error(f"Error searching '{query}': {e}")
                continue

            # Rate limit between queries (skip delay after last query)
            if i < len(queries) - 1:
                time.sleep(self.request_delay)

        self.logger.info(
            f"Web search collected {len(all_items)} unique items "
            f"from {len(queries)} queries"
        )
        return all_items

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(requests.RequestException,))
    def _search(self, query: str) -> List[Dict]:
        """
        Execute a single search query against Brave Search API.

        Args:
            query: Search query string

        Returns:
            List of raw result dicts from Brave API
        """
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.api_key,
        }

        params = {
            'q': query,
            'count': self.results_per_query,
            'freshness': self.freshness,
        }

        response = requests.get(
            self.BASE_URL,
            headers=headers,
            params=params,
            timeout=30,
        )

        # Handle rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            self.logger.warning(
                f"Rate limited, waiting {retry_after}s"
            )
            time.sleep(retry_after)
            raise requests.RequestException("Rate limited by Brave API")

        response.raise_for_status()

        data = response.json()
        return data.get('results', [])

    def _result_to_item(self, result: Dict, query: str) -> Optional[Dict]:
        """
        Convert a Brave Search result to a standardized item.

        Args:
            result: Raw Brave API result dict
            query: The query that produced this result

        Returns:
            Standardized item dict, or None if invalid
        """
        url = result.get('url', '')
        title = result.get('title', '')

        if not url or not title:
            return None

        # Clean HTML from title and description
        title = clean_html(title)
        description = clean_html(result.get('description', ''))

        # Parse publication date
        published_date = self._parse_date(result)

        # Extract tags from content
        tags = self._extract_tags(title, description, query)

        # Fetch full article content for richer synthesis
        full_content = description
        fetched = self._fetch_full_article(url, title)
        if fetched and len(fetched) > len(full_content):
            full_content = fetched

        return self._create_item(
            url=url,
            title=title,
            source='web_search:brave',
            snippet=extract_snippet(description) if description else None,
            content=full_content,
            source_metadata={
                'query': query,
                'tier': self.tier,
                'priority': self.config.get('priority', 'medium'),
                'age': result.get('age', ''),
                'source_name': result.get('meta_url', {}).get(
                    'hostname', ''
                ) if isinstance(result.get('meta_url'), dict) else '',
                'type': 'web_search',
            },
            published_date=published_date,
            author=result.get('meta_url', {}).get(
                'hostname', ''
            ) if isinstance(result.get('meta_url'), dict) else None,
            category='ai-agents',
            tags=tags,
        )

    def _parse_date(self, result: Dict) -> Optional[datetime]:
        """
        Parse date from Brave Search result.

        Handles both ISO format (page_age) and relative format (age).

        Args:
            result: Brave API result dict

        Returns:
            Parsed datetime or None
        """
        # Try page_age first (ISO format)
        page_age = result.get('page_age')
        if page_age:
            try:
                return datetime.fromisoformat(
                    page_age.replace('Z', '+00:00')
                )
            except (ValueError, TypeError):
                pass

        # Fall back to relative age string ("2 hours ago", "3 days ago")
        age_str = result.get('age', '')
        if age_str:
            return self._parse_relative_age(age_str)

        return None

    def _parse_relative_age(self, age_str: str) -> Optional[datetime]:
        """
        Parse relative age string into datetime.

        Args:
            age_str: Relative time string (e.g., "2 hours ago")

        Returns:
            Approximate datetime or None
        """
        now = datetime.now()

        patterns = [
            (r'(\d+)\s*hour', 'hours'),
            (r'(\d+)\s*day', 'days'),
            (r'(\d+)\s*week', 'weeks'),
            (r'(\d+)\s*minute', 'minutes'),
            (r'(\d+)\s*month', 'months'),
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, age_str, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if unit == 'months':
                    return now - timedelta(days=value * 30)
                elif unit == 'weeks':
                    return now - timedelta(weeks=value)
                elif unit == 'days':
                    return now - timedelta(days=value)
                elif unit == 'hours':
                    return now - timedelta(hours=value)
                elif unit == 'minutes':
                    return now - timedelta(minutes=value)

        return None

    def _extract_tags(
        self, title: str, description: str, query: str
    ) -> List[str]:
        """
        Extract topic tags from search result content.

        Args:
            title: Result title
            description: Result description
            query: Source query

        Returns:
            List of tag strings
        """
        tags = ['web-search', 'ai-agents']
        text = f"{title} {description}".lower()

        topic_keywords = {
            'marketplace': 'marketplace',
            'crypto': 'crypto',
            'blockchain': 'blockchain',
            'token': 'tokenomics',
            'tokenomics': 'tokenomics',
            'decentralized': 'decentralized',
            'web3': 'web3',
            'defi': 'defi',
            'smart contract': 'smart-contract',
            'dao': 'dao',
            'on-chain': 'on-chain',
            'autonomous': 'autonomous-agents',
            'trading': 'trading',
            'nft': 'nft',
            'wallet': 'wallet',
        }

        for keyword, tag in topic_keywords.items():
            if keyword in text and tag not in tags:
                tags.append(tag)

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
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'ResearchAgent/1.0 (AI research tracking bot)'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove non-content elements
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()

            # Try content extraction strategies
            article_content = (
                soup.find('article')
                or soup.find('main')
                or soup.select_one('[class*="content"]')
                or soup.select_one('[class*="article"]')
                or soup.find('body')
            )

            if article_content and hasattr(article_content, 'find_all'):
                paragraphs = []
                for elem in article_content.find_all(
                    ['p', 'h1', 'h2', 'h3', 'h4', 'li']
                ):
                    text = elem.get_text().strip()
                    if text and len(text) > 20:
                        paragraphs.append(text)

                full_text = '\n\n'.join(paragraphs)
                full_text = re.sub(r'\n{3,}', '\n\n', full_text)
                full_text = re.sub(r' {2,}', ' ', full_text)

                self.logger.debug(
                    f"Extracted {len(full_text)} chars from {url}"
                )
                return full_text

            return ''

        except Exception as e:
            self.logger.debug(f"Could not fetch article {url}: {e}")
            return ''
