"""arXiv source collector with quality filtering."""

import re
import arxiv
from typing import List, Dict, Set
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger
from research_agent.utils.slop_detector import score_paper_quality
from research_agent.utils.priority_authors import (
    check_priority_author,
    check_levin_adjacent,
    PRIORITY_AUTHORS,
)


def normalize_arxiv_url(url: str) -> str:
    """
    Normalize arXiv URL to consistent format: https://arxiv.org/abs/YYMM.NNNNN

    Handles:
    - HTTP to HTTPS conversion
    - Version suffix removal (v1, v2, etc.)
    - abs/pdf path consistency
    """
    if not url:
        return url

    # Force HTTPS
    url = url.replace('http://', 'https://')

    # Remove version suffix (e.g., 2511.23476v1 -> 2511.23476)
    url = re.sub(r'v\d+$', '', url)

    # Ensure /abs/ not /pdf/ for main URL
    url = url.replace('/pdf/', '/abs/')

    return url


# Core AI/ML keywords for relevance filtering
# Papers must contain at least one of these to be included
RELEVANCE_KEYWORDS: Set[str] = {
    # Core LLM/transformer
    'language model', 'llm', 'large language', 'transformer', 'attention mechanism',
    'gpt', 'bert', 'llama', 'claude', 'gemini',

    # Agents and autonomy
    'agent', 'agentic', 'autonomous', 'multi-agent', 'tool use', 'tool learning',
    'react', 'chain-of-thought', 'reasoning',

    # Training and alignment
    'rlhf', 'reinforcement learning from human', 'alignment', 'fine-tuning',
    'instruction tuning', 'preference learning', 'reward model',

    # Retrieval and RAG
    'retrieval augmented', 'rag', 'retrieval-augmented', 'vector database',
    'embedding', 'semantic search',

    # Prompting
    'prompt', 'prompting', 'in-context learning', 'few-shot', 'zero-shot',

    # Safety and interpretability
    'interpretability', 'mechanistic', 'safety', 'jailbreak', 'red team',
    'hallucination', 'factuality',

    # Scaling and efficiency
    'scaling law', 'mixture of experts', 'moe', 'quantization', 'distillation',
    'efficient inference',

    # Multimodal
    'multimodal', 'vision-language', 'image-text', 'video understanding',

    # Benchmarks
    'benchmark', 'evaluation', 'mmlu', 'humaneval', 'gsm8k',

    # Code and math
    'code generation', 'mathematical reasoning', 'theorem proving',

    # Michael Levin adjacent (always include)
    'bioelectricity', 'bioelectric', 'morphogenesis', 'collective intelligence',
    'xenobot', 'self-organization', 'emergence', 'swarm',
}


class ArxivSource(ResearchSource):
    """Collect papers from arXiv with quality filtering."""

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.arxiv")
        self.tier = config.get('tier', 1)  # arXiv is tier 1 by default
        self.priority = config.get('priority', 'high')

        # Quality filtering settings
        self.filter_keywords = config.get('filter_keywords', True)
        self.max_slop_score = config.get('max_slop_score', 0.6)  # Reject heavy slop
        self.boost_priority_authors = config.get('boost_priority_authors', True)

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch recent papers from arXiv with quality filtering.

        Returns:
            List of paper items
        """
        items = []
        seen_ids = set()  # Deduplicate across categories

        # Get categories from config
        categories = self.config.get('categories', ['cs.AI', 'cs.LG', 'cs.CL'])
        max_results = self.config.get('max_results', 20)
        days_lookback = self.config.get('days_lookback', 14)

        # Track stats for logging
        stats = {
            'total_fetched': 0,
            'filtered_old': 0,
            'filtered_irrelevant': 0,
            'filtered_slop': 0,
            'priority_author_boost': 0,
            'duplicates': 0,
        }

        for category in categories:
            try:
                # Search for recent papers in category
                search = arxiv.Search(
                    query=f"cat:{category}",
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending
                )

                for result in search.results():
                    stats['total_fetched'] += 1

                    # Deduplicate (papers appear in multiple categories)
                    arxiv_id = result.entry_id.split('/')[-1]
                    arxiv_id = re.sub(r'v\d+$', '', arxiv_id)  # Remove version

                    if arxiv_id in seen_ids:
                        stats['duplicates'] += 1
                        continue
                    seen_ids.add(arxiv_id)

                    # Filter by publication date
                    published_naive = result.published.replace(tzinfo=None)
                    if (datetime.now() - published_naive).days > days_lookback:
                        stats['filtered_old'] += 1
                        continue

                    # Build text for analysis
                    text = f"{result.title} {result.summary}".lower()
                    author_str = ', '.join([a.name for a in result.authors[:5]])

                    # Check for priority authors FIRST (always include)
                    author_match = check_priority_author(author_str)
                    is_priority = bool(author_match)

                    if is_priority:
                        stats['priority_author_boost'] += 1
                        self.logger.info(
                            f"Priority author found: {author_match.get('matched_author')} "
                            f"in '{result.title[:50]}...'"
                        )

                    # Check for Levin-adjacent content (always include)
                    is_levin_adjacent = check_levin_adjacent(text)
                    if is_levin_adjacent and not is_priority:
                        self.logger.info(f"Levin-adjacent paper: '{result.title[:50]}...'")

                    # Keyword relevance filter (skip for priority/Levin-adjacent)
                    if self.filter_keywords and not is_priority and not is_levin_adjacent:
                        if not self._is_relevant(text):
                            stats['filtered_irrelevant'] += 1
                            continue

                    # Slop detection (skip for priority authors)
                    if not is_priority:
                        quality = score_paper_quality({
                            'title': result.title,
                            'content': result.summary,
                        })
                        slop_score = quality['slop_score']

                        if slop_score > self.max_slop_score:
                            stats['filtered_slop'] += 1
                            self.logger.debug(
                                f"Filtered slop ({slop_score:.2f}): {result.title[:50]}..."
                            )
                            continue
                    else:
                        slop_score = 0.0

                    # Normalize URLs for consistent format
                    normalized_url = normalize_arxiv_url(result.entry_id)

                    # Build metadata
                    metadata = {
                        'arxiv_id': arxiv_id,
                        'categories': [c.name if hasattr(c, 'name') else str(c) for c in result.categories],
                        'pdf_url': normalize_arxiv_url(result.pdf_url).replace('/abs/', '/pdf/'),
                        'tier': self.tier,
                        'priority': self.priority,
                        'slop_score': slop_score,
                    }

                    # Add priority author info if matched
                    if is_priority:
                        metadata['priority_author'] = author_match
                        metadata['priority'] = 'critical'

                    if is_levin_adjacent:
                        metadata['levin_adjacent'] = True

                    item = self._create_item(
                        url=normalized_url,
                        title=result.title,
                        source='arxiv',
                        snippet=extract_snippet(result.summary, 1500),
                        content=result.summary,
                        source_metadata=metadata,
                        published_date=result.published,
                        author=', '.join([a.name for a in result.authors[:3]]),
                        category=category,
                        tags=self._extract_tags(result, is_priority, is_levin_adjacent)
                    )

                    items.append(item)

            except Exception as e:
                self.logger.error(f"Error fetching arXiv category {category}: {e}")
                continue

        # Log filtering stats
        self.logger.info(
            f"arXiv fetch complete: {len(items)} papers retained from {stats['total_fetched']} fetched "
            f"(filtered: {stats['filtered_old']} old, {stats['filtered_irrelevant']} irrelevant, "
            f"{stats['filtered_slop']} slop, {stats['duplicates']} dupes; "
            f"{stats['priority_author_boost']} priority authors)"
        )

        return items

    def _is_relevant(self, text: str) -> bool:
        """
        Check if text contains relevant AI/ML keywords.

        Args:
            text: Lowercase text to check

        Returns:
            True if relevant
        """
        for keyword in RELEVANCE_KEYWORDS:
            if keyword in text:
                return True
        return False

    def _extract_tags(self, result, is_priority: bool, is_levin_adjacent: bool) -> List[str]:
        """Extract tags from arXiv result."""
        tags = ['research', 'paper']

        # Add primary category
        if result.primary_category:
            tags.append(result.primary_category.replace('.', '-'))

        # Extract keywords from title and summary
        keywords = ['agent', 'llm', 'transformer', 'rlhf', 'prompt', 'alignment',
                    'rag', 'multimodal', 'reasoning', 'benchmark', 'safety']
        text = (result.title + ' ' + result.summary).lower()

        for keyword in keywords:
            if keyword in text:
                tags.append(keyword)

        # Priority tags
        if is_priority:
            tags.append('priority-author')

        if is_levin_adjacent:
            tags.append('levin-adjacent')

        return list(set(tags))
