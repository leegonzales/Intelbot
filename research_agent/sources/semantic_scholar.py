"""Semantic Scholar source collector for trending AI/ML papers."""

import time
import requests
from typing import List, Dict
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class SemanticScholarSource(ResearchSource):
    """
    Collect trending and highly-cited papers from Semantic Scholar.

    Semantic Scholar provides:
    - Citation counts and velocity
    - Influential citations
    - Paper abstracts and metadata
    - Related papers

    This source focuses on finding high-impact recent papers that may
    not appear in basic arXiv searches.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    # AI/ML focused search queries
    DEFAULT_QUERIES = [
        "large language model",
        "transformer neural network",
        "reinforcement learning human feedback",
        "multimodal AI",
        "AI agents autonomous",
        "prompt engineering LLM",
        "neural network reasoning",
    ]

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.semantic_scholar")
        self.tier = config.get('tier', 1)  # Tier 1 - primary academic source
        self.priority = config.get('priority', 'high')

        # Configuration
        self.max_results = config.get('max_results', 30)
        self.min_citations = config.get('min_citations', 3)
        self.days_lookback = config.get('days_lookback', 30)
        self.queries = config.get('queries', self.DEFAULT_QUERIES)

        # API key (optional but recommended for higher rate limits)
        self.api_key = config.get('api_key')

        # Rate limiting (unauthenticated: ~100 req/5min = 1 req/3sec)
        self.request_delay = config.get('request_delay', 3.0 if not self.api_key else 0.5)

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch trending papers from Semantic Scholar.

        Returns:
            List of paper items
        """
        items = []
        seen_paper_ids = set()

        headers = {}
        if self.api_key:
            headers['x-api-key'] = self.api_key

        for i, query in enumerate(self.queries):
            # Rate limiting between queries
            if i > 0 and self.request_delay > 0:
                self.logger.debug(f"Rate limiting: waiting {self.request_delay}s before next query")
                time.sleep(self.request_delay)

            try:
                papers = self._search_papers(query, headers)

                for paper in papers:
                    paper_id = paper.get('paperId')
                    if not paper_id or paper_id in seen_paper_ids:
                        continue

                    seen_paper_ids.add(paper_id)

                    # Filter by publication date
                    pub_date = self._parse_publication_date(paper)
                    if pub_date:
                        age_days = (datetime.now() - pub_date).days
                        if age_days > self.days_lookback:
                            continue

                    # Filter by citation count (quality signal)
                    citation_count = paper.get('citationCount', 0)
                    if citation_count < self.min_citations:
                        continue

                    item = self._paper_to_item(paper, pub_date, citation_count)
                    if item:
                        items.append(item)

            except Exception as e:
                self.logger.error(f"Error searching Semantic Scholar for '{query}': {e}")
                continue

        self.logger.info(f"Collected {len(items)} papers from Semantic Scholar")
        return items[:self.max_results]

    def _search_papers(self, query: str, headers: dict) -> List[Dict]:
        """Search for papers matching query with rate limit handling."""
        url = f"{self.BASE_URL}/paper/search"

        params = {
            'query': query,
            'limit': 20,
            'fields': 'paperId,title,abstract,url,venue,year,authors,citationCount,influentialCitationCount,publicationDate,externalIds',
        }

        # Retry with backoff on rate limit
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code == 429:
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                self.logger.warning(f"Rate limited by Semantic Scholar, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()
            return data.get('data', [])

        self.logger.error(f"Failed to fetch '{query}' after {max_retries} rate limit retries")
        return []

    def _parse_publication_date(self, paper: Dict) -> datetime:
        """Parse publication date from paper metadata."""
        pub_date_str = paper.get('publicationDate')

        if pub_date_str:
            try:
                return datetime.strptime(pub_date_str, '%Y-%m-%d')
            except ValueError:
                pass

        # Fallback to year
        year = paper.get('year')
        if year:
            try:
                return datetime(int(year), 1, 1)
            except ValueError:
                pass

        return None

    def _paper_to_item(self, paper: Dict, pub_date: datetime, citation_count: int) -> Dict:
        """Convert Semantic Scholar paper to standard item format."""
        title = paper.get('title')
        abstract = paper.get('abstract', '')

        if not title:
            return None

        # Build URL - prefer arXiv if available
        external_ids = paper.get('externalIds', {})
        arxiv_id = external_ids.get('ArXiv')

        if arxiv_id:
            url = f"https://arxiv.org/abs/{arxiv_id}"
        else:
            url = paper.get('url') or f"https://www.semanticscholar.org/paper/{paper.get('paperId')}"

        # Format authors
        authors = paper.get('authors', [])
        author_str = ', '.join([a.get('name', '') for a in authors[:5]])
        if len(authors) > 5:
            author_str += f" et al. ({len(authors)} authors)"

        # Build metadata
        influential_citations = paper.get('influentialCitationCount', 0)
        venue = paper.get('venue', '')

        return self._create_item(
            url=url,
            title=title,
            source='semantic_scholar',
            # Use full abstract for richer content
            snippet=extract_snippet(abstract, 1500) if abstract else None,
            content=abstract,
            source_metadata={
                'paper_id': paper.get('paperId'),
                'arxiv_id': arxiv_id,
                'citation_count': citation_count,
                'influential_citations': influential_citations,
                'venue': venue,
                'tier': self.tier,
                'priority': self.priority,
            },
            published_date=pub_date,
            author=author_str,
            category='research',
            tags=self._extract_tags(paper, abstract)
        )

    def _extract_tags(self, paper: Dict, abstract: str) -> List[str]:
        """Extract tags from paper metadata and content."""
        tags = ['research', 'paper', 'semantic-scholar']

        # Add venue as tag
        venue = paper.get('venue', '')
        if venue:
            venue_clean = venue.lower().replace(' ', '-')[:30]
            tags.append(venue_clean)

        # Extract keywords from abstract
        if abstract:
            text = abstract.lower()
            keywords = [
                'llm', 'transformer', 'attention', 'agent', 'rlhf',
                'alignment', 'prompt', 'multimodal', 'reasoning',
                'benchmark', 'fine-tuning', 'pre-training'
            ]
            for keyword in keywords:
                if keyword in text:
                    tags.append(keyword)

        return list(set(tags))
