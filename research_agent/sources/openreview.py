"""OpenReview source collector for ML conference papers (NeurIPS, ICML, ICLR)."""

import openreview
from typing import List, Dict
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class OpenReviewSource(ResearchSource):
    """
    Collect papers from ML conferences via OpenReview API.

    Supports:
    - NeurIPS (Neural Information Processing Systems)
    - ICML (International Conference on Machine Learning)
    - ICLR (International Conference on Learning Representations)

    OpenReview provides:
    - Paper titles, abstracts, authors
    - Decision status (oral, spotlight, poster)
    - Keywords and primary areas
    """

    # Conference venue IDs for OpenReview API
    VENUE_IDS = {
        'neurips': 'NeurIPS.cc/{year}/Conference',
        'icml': 'ICML.cc/{year}/Conference',
        'iclr': 'ICLR.cc/{year}/Conference',
    }

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.openreview")
        self.tier = config.get('tier', 1)  # Tier 1 - primary academic source
        self.priority = config.get('priority', 'high')

        # Configuration
        self.max_results = config.get('max_results', 50)
        self.conferences = config.get('conferences', ['neurips', 'icml', 'iclr'])
        self.years = config.get('years', [2025, 2024])  # Recent years
        self.decision_filter = config.get('decision_filter', ['oral', 'spotlight', 'poster'])

        # Keywords to filter for AI/ML agent-related papers
        self.keywords = config.get('keywords', [
            'agent', 'llm', 'large language model', 'transformer',
            'reinforcement learning', 'rlhf', 'alignment', 'reasoning',
            'multimodal', 'prompt', 'in-context learning', 'chain-of-thought'
        ])

        # Initialize OpenReview client (API v2 for 2023+ conferences)
        try:
            self.client = openreview.api.OpenReviewClient(
                baseurl='https://api2.openreview.net'
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenReview client: {e}")
            self.client = None

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch papers from ML conferences via OpenReview.

        Returns:
            List of paper items
        """
        if not self.client:
            self.logger.error("OpenReview client not initialized")
            return []

        items = []
        seen_paper_ids = set()

        for conference in self.conferences:
            for year in self.years:
                try:
                    venue_id = self.VENUE_IDS.get(conference, '').format(year=year)
                    if not venue_id:
                        continue

                    papers = self._fetch_conference_papers(venue_id, conference, year)

                    for paper in papers:
                        paper_id = paper.get('id')
                        if paper_id in seen_paper_ids:
                            continue
                        seen_paper_ids.add(paper_id)

                        # Filter by keywords if specified
                        if self.keywords and not self._matches_keywords(paper):
                            continue

                        item = self._paper_to_item(paper, conference, year)
                        if item:
                            items.append(item)

                        if len(items) >= self.max_results:
                            break

                except Exception as e:
                    self.logger.error(f"Error fetching {conference} {year}: {e}")
                    continue

                if len(items) >= self.max_results:
                    break

            if len(items) >= self.max_results:
                break

        self.logger.info(f"Collected {len(items)} papers from OpenReview")
        return items[:self.max_results]

    def _fetch_conference_papers(self, venue_id: str, conference: str, year: int) -> List[Dict]:
        """Fetch papers from a specific conference venue."""
        papers = []

        try:
            # Get accepted submissions
            submissions = self.client.get_all_notes(
                content={'venueid': venue_id},
                details='directReplies'
            )

            for submission in submissions:
                content = submission.content

                # Extract paper info
                paper = {
                    'id': submission.id,
                    'title': content.get('title', {}).get('value', ''),
                    'abstract': content.get('abstract', {}).get('value', ''),
                    'authors': self._extract_authors(content),
                    'keywords': content.get('keywords', {}).get('value', []),
                    'primary_area': content.get('primary_area', {}).get('value', ''),
                    'venue': f"{conference.upper()} {year}",
                    'url': f"https://openreview.net/forum?id={submission.id}",
                    'pdf_url': f"https://openreview.net/pdf?id={submission.id}",
                    'decision': self._extract_decision(submission),
                    'created_date': datetime.fromtimestamp(submission.cdate / 1000) if submission.cdate else None,
                }

                # Filter by decision if specified
                if self.decision_filter:
                    decision_lower = paper['decision'].lower()
                    if not any(d in decision_lower for d in self.decision_filter):
                        continue

                papers.append(paper)

        except Exception as e:
            self.logger.error(f"Error querying OpenReview for {venue_id}: {e}")

        return papers

    def _extract_authors(self, content: Dict) -> str:
        """Extract author names from paper content."""
        authors = content.get('authors', {}).get('value', [])
        if isinstance(authors, list):
            if len(authors) > 5:
                return ', '.join(authors[:5]) + f' et al. ({len(authors)} authors)'
            return ', '.join(authors)
        return str(authors)

    def _extract_decision(self, submission) -> str:
        """Extract decision from submission replies."""
        try:
            # Check venue field which often contains decision
            venue = submission.content.get('venue', {}).get('value', '')
            if venue:
                if 'oral' in venue.lower():
                    return 'Oral'
                elif 'spotlight' in venue.lower():
                    return 'Spotlight'
                elif 'poster' in venue.lower():
                    return 'Poster'
            return 'Accepted'
        except Exception:
            return 'Accepted'

    def _matches_keywords(self, paper: Dict) -> bool:
        """Check if paper matches any configured keywords."""
        text = (
            paper.get('title', '') + ' ' +
            paper.get('abstract', '') + ' ' +
            ' '.join(paper.get('keywords', []))
        ).lower()

        return any(keyword.lower() in text for keyword in self.keywords)

    def _paper_to_item(self, paper: Dict, conference: str, year: int) -> Dict:
        """Convert OpenReview paper to standard item format."""
        title = paper.get('title')
        abstract = paper.get('abstract', '')

        if not title:
            return None

        return self._create_item(
            url=paper.get('url'),
            title=title,
            source='openreview',
            # Use full abstract for richer content
            snippet=extract_snippet(abstract, 1500) if abstract else None,
            content=abstract,
            source_metadata={
                'paper_id': paper.get('id'),
                'conference': conference.upper(),
                'year': year,
                'venue': paper.get('venue'),
                'decision': paper.get('decision'),
                'primary_area': paper.get('primary_area'),
                'keywords': paper.get('keywords', []),
                'pdf_url': paper.get('pdf_url'),
                'tier': self.tier,
                'priority': self.priority,
            },
            published_date=paper.get('created_date'),
            author=paper.get('authors'),
            category=f"{conference}-{year}",
            tags=self._extract_tags(paper, conference)
        )

    def _extract_tags(self, paper: Dict, conference: str) -> List[str]:
        """Extract tags from paper metadata."""
        tags = ['research', 'paper', 'conference', conference.lower()]

        # Add decision as tag
        decision = paper.get('decision', '').lower()
        if decision:
            tags.append(decision)

        # Add paper keywords (limit to 5)
        keywords = paper.get('keywords', [])
        for keyword in keywords[:5]:
            if isinstance(keyword, str):
                tags.append(keyword.lower().replace(' ', '-'))

        # Extract common ML keywords
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        ml_keywords = ['llm', 'transformer', 'agent', 'rlhf', 'alignment', 'multimodal']
        for keyword in ml_keywords:
            if keyword in text:
                tags.append(keyword)

        return list(set(tags))
