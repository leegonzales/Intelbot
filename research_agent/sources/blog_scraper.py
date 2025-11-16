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

        for url_config in urls:
            try:
                # Handle both string URLs and dict configs
                if isinstance(url_config, dict):
                    url = url_config.get('url')
                    blog_name = url_config.get('name', url)
                    tier = url_config.get('tier', 3)
                    priority = url_config.get('priority', 'medium')
                else:
                    url = url_config
                    blog_name = url
                    tier = 3
                    priority = 'medium'

                # Fetch homepage
                response = requests.get(url, timeout=15, headers={
                    'User-Agent': 'ResearchAgent/1.0 (AI research tracking bot)'
                })
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Try to find article links (this is generic and may need customization)
                articles = self._find_articles(soup, url, blog_name, tier, priority)

                items.extend(articles)

            except Exception as e:
                self.logger.error(f"Error scraping blog {blog_name}: {e}")
                continue

        return items

    def _find_articles(self, soup: BeautifulSoup, base_url: str, blog_name: str = None, tier: int = 3, priority: str = 'medium') -> List[Dict]:
        """
        Find article links on page.

        This is a generic implementation that tries common patterns.
        May need customization for specific blogs.
        """
        articles = []

        if blog_name is None:
            blog_name = base_url

        # Site-specific selectors for Anthropic pages
        if 'anthropic.com/engineering' in base_url or 'anthropic.com/news' in base_url:
            return self._scrape_anthropic(soup, base_url, blog_name, tier, priority)

        # Look for common article selectors
        # More comprehensive list including research page patterns
        selectors = [
            'article',
            '.post',
            '.blog-post',
            '[class*="article"]',
            '[class*="post"]',
            # Research page patterns
            '[class*="card"]',
            '[class*="research"]',
            '[class*="paper"]',
            '[class*="publication"]',
            'li a[href*="/research/"]',  # Deep links to research
            'li a[href*="/blog/"]',      # Deep links to blog posts
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

                    # Extract content/snippet from homepage
                    content_elem = element.find(['p', '.excerpt', '.summary'])
                    snippet = content_elem.get_text().strip() if content_elem else ''

                    # Try to find date
                    date_elem = element.find(['time', '.date', '[class*="date"]'])
                    published_date = None
                    if date_elem:
                        date_str = date_elem.get('datetime') or date_elem.get_text()
                        published_date = self._parse_date(date_str)

                    # Fetch full article content for all sources
                    self.logger.info(f"Fetching full article: {title[:50]}...")
                    full_content = self._fetch_full_article(link, title)
                    if not snippet and full_content:
                        # If we didn't get a snippet from homepage, extract from full content
                        snippet = full_content[:500]
                    elif not full_content:
                        # If fetching failed, use snippet as fallback
                        full_content = snippet

                    article = self._create_item(
                        url=link,
                        title=title,
                        source=f"blog:{blog_name}",
                        snippet=extract_snippet(snippet, 500),
                        content=full_content,  # Full article for tier 1, snippet otherwise
                        source_metadata={
                            'blog_url': base_url,
                            'blog_name': blog_name,
                            'tier': tier,
                            'priority': priority,
                        },
                        published_date=published_date,
                        tags=['blog', 'article']
                    )

                    articles.append(article)

                except Exception as e:
                    self.logger.error(f"Error parsing article from {blog_name}: {e}")
                    continue

            if articles:  # If we found articles with this selector, stop trying others
                break

        return articles

    def _scrape_anthropic(self, soup: BeautifulSoup, base_url: str, blog_name: str, tier: int, priority: str) -> List[Dict]:
        """
        Custom scraper for Anthropic blog pages (/engineering and /news).

        These pages have a specific structure with article cards.
        For Tier 1 sources, fetches full article content.
        """
        articles = []

        # Determine the path segment to look for
        path_segment = '/engineering/' if 'engineering' in base_url else '/news/'

        # Find all links on the page
        links = soup.find_all('a', href=True)

        for link in links[:30]:  # Limit to first 30 links
            href = link.get('href', '')

            # Look for article links (e.g., /engineering/something or /news/something)
            if path_segment in href:
                # Make absolute URL
                if href.startswith('/'):
                    from urllib.parse import urljoin
                    href = urljoin('https://www.anthropic.com', href)

                # Get title from link text or nearby heading
                title = link.get_text().strip()
                if not title:
                    # Try to find title in parent heading
                    parent_heading = link.find_parent(['h1', 'h2', 'h3', 'h4'])
                    if parent_heading:
                        title = parent_heading.get_text().strip()

                if not title or len(title) < 5:
                    continue

                # Try to find description from nearby text (for snippet)
                parent = link.find_parent(['div', 'section', 'article', 'li'])
                snippet = ''
                if parent:
                    # Look for paragraph or description
                    desc_elem = parent.find('p') or parent.find('[class*="description"]')
                    if desc_elem:
                        snippet = desc_elem.get_text().strip()[:500]

                # Try to find date
                date_elem = None
                if parent:
                    date_elem = parent.find(['time', '[class*="date"]'])
                published_date = None
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text()
                    published_date = self._parse_date(date_str)

                # Fetch full article content for all sources
                self.logger.info(f"Fetching full article: {title[:50]}...")
                full_content = self._fetch_full_article(href, title)
                if not snippet and full_content:
                    # If we didn't get a snippet from homepage, extract from full content
                    snippet = full_content[:500]
                elif not full_content:
                    # If fetching failed, use snippet as fallback
                    full_content = snippet

                # Determine tags based on blog type
                tags = ['anthropic']
                if 'engineering' in base_url:
                    tags.extend(['engineering', 'blog'])
                else:
                    tags.extend(['news', 'announcement'])

                article = self._create_item(
                    url=href,
                    title=title,
                    source=f"blog:{blog_name}",
                    snippet=snippet,
                    content=full_content,  # Full article content for tier 1
                    source_metadata={
                        'blog_url': base_url,
                        'blog_name': blog_name,
                        'tier': tier,
                        'priority': priority,
                    },
                    published_date=published_date,
                    tags=tags
                )

                articles.append(article)

        self.logger.info(f"Found {len(articles)} articles from {blog_name}")
        return articles

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
            # These sites use <main> for article content, not <article>
            if 'deepmind.google' in url or 'googleblog.com' in url or 'blog.google' in url:
                main_tag = soup.find('main') or soup.find('[role="main"]')
                if main_tag:
                    article_content = main_tag

            # Strategy 1: Look for article tag (if not already handled)
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
                import re
                full_text = re.sub(r'\n{3,}', '\n\n', full_text)
                full_text = re.sub(r' {2,}', ' ', full_text)

                self.logger.debug(f"Extracted {len(full_text)} chars from {url}")
                return full_text

            return ''

        except Exception as e:
            self.logger.error(f"Error fetching full article from {url}: {e}")
            return ''

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime."""
        from dateutil import parser

        try:
            return parser.parse(date_str)
        except Exception:
            return None
