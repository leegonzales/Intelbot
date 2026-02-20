"""Relevance scoring for research items."""

from typing import Dict, List
from datetime import datetime, timedelta
import math

from research_agent.utils.priority_authors import get_author_boost, check_priority_author
from research_agent.utils.slop_detector import score_paper_quality


class RelevanceScorer:
    """
    Score items by relevance using multiple signals.

    Scoring factors:
    - Keyword matching
    - Source tier
    - Engagement metrics (citations, points, etc.)
    - Recency
    - Novelty (similarity to history)
    """

    def __init__(self, config, state_manager):
        self.config = config
        self.state = state_manager

        # Define source tiers
        self.source_tiers = {
            'arxiv': 1.0,
            'anthropic': 1.0,
            'openai': 1.0,
            'deepmind': 1.0,
            'hackernews': 0.8,
            'rss': 0.7,
            'blog': 0.7,
            'web_search': 0.7,
        }

        # High-value keywords (expanded for academic papers)
        self.high_value_keywords = {
            # Practitioner/industry terms
            'multi-agent', 'agent', 'rlhf', 'alignment', 'prompt engineering',
            'tool use', 'autonomous', 'framework', 'production', 'benchmark',
            'claude', 'gpt', 'llm', 'transformer', 'in-context', 'chain-of-thought',

            # Academic equivalents
            'reinforcement learning from human feedback', 'optimization',
            'fine-tuning', 'pre-training', 'inference', 'reasoning',
            'multimodal', 'vision-language', 'embedding', 'attention',
            'neural network', 'deep learning', 'supervised learning',
            'zero-shot', 'few-shot', 'transfer learning', 'generalization',
            'instruction tuning', 'foundation model', 'language model',

            # Academic quality signals (prioritize papers with strong results)
            'state-of-the-art', 'sota', 'outperforms', 'surpasses', 'achieves',
            'novel', 'we propose', 'we introduce', 'contributions',
            'ablation', 'experiments', 'evaluation', 'empirical',

            # Trending research areas
            'scaling law', 'emergent', 'capability', 'safety', 'interpretability',
            'mechanistic', 'world model', 'planning', 'agentic', 'self-improvement',
            'constitutional ai', 'preference learning', 'reward model',
            'mixture of experts', 'moe', 'retrieval augmented', 'rag',
            'long context', 'context window', 'instruction following',
            'code generation', 'mathematical reasoning', 'tool learning',

            # AI agent marketplace & crypto terms
            'marketplace', 'crypto', 'blockchain', 'token', 'tokenomics',
            'decentralized', 'web3', 'defi', 'smart contract', 'dao',
            'agent marketplace', 'agent economy', 'on-chain',
        }

        # Academic impact keywords (extra boost for papers with strong results)
        self.impact_keywords = {
            'state-of-the-art', 'sota', 'outperforms', 'surpasses',
            'novel contribution', 'first to', 'breakthrough', 'significantly'
        }

    def score(self, item: Dict) -> float:
        """
        Calculate relevance score for item.

        Args:
            item: Research item

        Returns:
            Relevance score (0.0 - 1.0+)
        """
        score = 0.0

        # 1. Base relevance from keywords
        score += self._keyword_score(item) * 0.20

        # 2. Source tier weight (prioritize strategic sources)
        score += self._source_score(item) * 0.35

        # 3. Engagement metrics
        score += self._engagement_score(item) * 0.15

        # 4. Recency bonus
        score += self._recency_score(item) * 0.10

        # 5. Novelty bonus
        score += self._novelty_score(item) * 0.10

        # 6. Quality score (penalize slop)
        score += self._quality_score(item) * 0.10

        # Apply author/institution boost (multiplicative)
        author_boost = get_author_boost(item)
        if author_boost > 1.0:
            score *= author_boost

        # Check for priority author in metadata (already computed by arxiv source)
        metadata = item.get('source_metadata', {})
        if metadata.get('priority_author'):
            # Critical priority authors get maximum boost
            score = max(score, 0.95)  # Ensure they're near the top

        return score

    def _quality_score(self, item: Dict) -> float:
        """
        Score based on writing quality (inverse of slop score).

        Papers with AI-generated slop get penalized.
        """
        metadata = item.get('source_metadata', {})

        # Check if slop score was already computed (by arxiv source)
        if 'slop_score' in metadata:
            slop = metadata['slop_score']
            return 1.0 - slop  # Invert: low slop = high quality

        # Compute slop score for non-arxiv sources
        quality = score_paper_quality(item)
        return 1.0 - quality['slop_score']

    def _keyword_score(self, item: Dict) -> float:
        """Score based on keyword matching."""
        text = (item.get('title', '') + ' ' + (item.get('snippet') or '')).lower()

        matches = sum(1 for keyword in self.high_value_keywords if keyword in text)

        # Extra boost for academic impact keywords
        impact_matches = sum(1 for keyword in self.impact_keywords if keyword in text)

        # Base score from keyword matches (normalized to 0-1)
        base_score = min(matches / 3.0, 1.0)

        # Add impact bonus (up to 0.2 extra for papers with strong results language)
        impact_bonus = min(impact_matches * 0.1, 0.2)

        return min(base_score + impact_bonus, 1.0)

    def _source_score(self, item: Dict) -> float:
        """Score based on source tier."""
        metadata = item.get('source_metadata', {})
        source = item.get('source', '').lower()

        # PRIORITY FIX: Academic sources get maximum tier score
        # Academic papers are research foundation and should be prioritized
        if 'arxiv' in source or 'semantic_scholar' in source or 'openreview' in source:
            return 1.0

        # Check for explicit tier metadata first (new tiered system)
        if 'tier' in metadata:
            tier = metadata['tier']
            # Tier 2: Synthesis sources (strategic thinkers) = HIGHEST VALUE
            # Tier 1: Primary sources (research labs, arXiv) = very high weight
            # Tier 3: News aggregators = medium weight
            # Tier 5: Implementation blogs = medium weight
            tier_weights = {
                2: 1.0,   # Synthesis sources (HIGHEST - strategic analysis)
                1: 0.9,   # Primary sources (research labs, arXiv)
                3: 0.6,   # News aggregators
                5: 0.7,   # Implementation blogs
            }
            return tier_weights.get(tier, 0.5)

        # Fall back to old source string matching
        source = item.get('source', '').lower()
        for tier_source, tier_score in self.source_tiers.items():
            if tier_source in source:
                return tier_score

        return 0.5  # Default for unknown sources

    def _engagement_score(self, item: Dict) -> float:
        """Score based on engagement metrics (citations, points, upvotes)."""
        metadata = item.get('source_metadata', {})

        # Different metrics based on source
        if 'citation_count' in metadata:
            # Semantic Scholar citation count (preferred - most reliable)
            citations = metadata['citation_count']
            # Boost for influential citations (highly weighted by S2)
            influential = metadata.get('influential_citations', 0)
            base_score = min(math.log(citations + 1) / math.log(100), 1.0)
            # Add bonus for influential citations (up to 0.2 extra)
            influential_bonus = min(influential * 0.05, 0.2)
            return min(base_score + influential_bonus, 1.0)

        elif 'citations' in metadata:
            # arXiv citations (legacy)
            citations = metadata['citations']
            return min(math.log(citations + 1) / math.log(100), 1.0)

        elif 'points' in metadata:
            # Hacker News points
            points = metadata['points']
            return min(math.log(points + 1) / math.log(500), 1.0)

        elif 'score' in metadata:
            # Generic score
            score = metadata['score']
            return min(score / 100.0, 1.0)

        return 0.5  # No engagement data

    def _recency_score(self, item: Dict) -> float:
        """Score based on recency."""
        published_date = item.get('published_date')

        if not published_date:
            # MISSING DATE FIX: Try to extract date from title
            # Many blog posts include date in title (e.g., "ArticleDec 19, 2024")
            title = item.get('title', '')
            extracted_date = self._extract_date_from_title(title)
            if extracted_date:
                published_date = extracted_date
            else:
                # No date available - return low score to avoid including old content
                return 0.1

        # Parse date if string
        if isinstance(published_date, str):
            try:
                published_date = datetime.fromisoformat(published_date)
            except Exception:
                return 0.5

        # Remove timezone info for comparison
        if hasattr(published_date, 'tzinfo') and published_date.tzinfo is not None:
            published_date = published_date.replace(tzinfo=None)

        # Calculate age in hours
        age_hours = (datetime.now() - published_date).total_seconds() / 3600

        # ARXIV FIX: Academic papers have slower recency decay
        # arXiv papers remain relevant longer than breaking news/blog posts
        source = item.get('source', '').lower()
        if 'arxiv' in source:
            # Slower decay: 1.0 for new, 0.5 at 72h (3 days), 0.25 at 144h (6 days)
            # This prevents 3-4 day old papers from being completely devalued
            return math.exp(-age_hours / 72.0)
        else:
            # Standard decay: 1.0 for new, 0.5 at 24h, 0.25 at 48h
            return math.exp(-age_hours / 24.0)

    def _novelty_score(self, item: Dict) -> float:
        """Score based on novelty (dissimilarity to historical items)."""
        # Check FTS similarity to recent items
        similar = self.state._find_similar_titles(item['title'], threshold=0.7)

        if not similar:
            return 1.0  # Very novel

        # Penalize if very similar to existing items
        max_similarity = max(s['score'] for s in similar)
        return 1.0 - max_similarity

    def _extract_date_from_title(self, title: str) -> str:
        """
        Extract date from title for blog posts that embed dates.

        Example: "Building Effective AgentsDec 19, 2024" -> "2024-12-19"
        """
        import re
        from dateutil import parser as date_parser

        # Common patterns in Anthropic blog titles
        # Pattern: "MonthName DD, YYYY" (e.g., "Dec 19, 2024")
        month_day_year = re.search(r'([A-Z][a-z]{2,8})\s+(\d{1,2}),?\s+(\d{4})', title)
        if month_day_year:
            try:
                date_str = f"{month_day_year.group(1)} {month_day_year.group(2)}, {month_day_year.group(3)}"
                parsed = date_parser.parse(date_str)
                return parsed.strftime('%Y-%m-%d')
            except:
                pass

        # Fallback: try dateutil's fuzzy parsing
        try:
            parsed = date_parser.parse(title, fuzzy=True)
            # Only return if year is reasonable (2020-2030)
            if 2020 <= parsed.year <= 2030:
                return parsed.strftime('%Y-%m-%d')
        except:
            pass

        return None
