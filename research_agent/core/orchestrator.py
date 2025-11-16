"""Research orchestrator - main workflow coordinator."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from research_agent.core.config import Config
from research_agent.core.prompts import PromptManager
from research_agent.storage.state import StateManager
from research_agent.agents.source_agent import SourceAgent
from research_agent.agents.synthesis_agent import SynthesisAgent
from research_agent.output.digest_writer import DigestWriter
from research_agent.utils.scoring import RelevanceScorer
from research_agent.utils.logger import get_logger


@dataclass
class ResearchResult:
    """Result of a research cycle."""

    timestamp: datetime
    status: str  # 'success', 'partial', 'failed'
    items_found: int
    items_new: int
    items_included: int
    output_path: Optional[Path]
    runtime_seconds: float
    error_log: Optional[str] = None


class ResearchOrchestrator:
    """
    Main orchestrator for research cycle.

    Responsibilities:
    - Load config and prompts
    - Initialize agents and state manager
    - Execute research workflow
    - Handle errors and retries
    - Write outputs and logs
    """

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("orchestrator")

        # Expand paths
        data_dir = Path(config.paths.data_dir).expanduser()
        prompts_dir = Path(config.paths.prompts_dir).expanduser()

        # Initialize components
        self.prompts = PromptManager(prompts_dir)
        self.state = StateManager(data_dir / "state.db")
        self.source_agent = SourceAgent(config, self.state)
        self.synthesis_agent = SynthesisAgent(config, self.prompts)
        self.digest_writer = DigestWriter(config)

    def run(self, dry_run: bool = False) -> ResearchResult:
        """
        Execute a complete research cycle.

        Args:
            dry_run: If True, don't write outputs or update state

        Returns:
            ResearchResult with metadata about the run
        """
        start_time = datetime.now()

        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting research cycle...")
            self.logger.info("=" * 60)

            # 1. Collect items from all sources
            self.logger.info("[1/6] Collecting items from sources...")
            items = self.source_agent.collect_all()

            if not items:
                self.logger.warning("No items collected from any source")
                return ResearchResult(
                    timestamp=start_time,
                    status='partial',
                    items_found=0,
                    items_new=0,
                    items_included=0,
                    output_path=None,
                    runtime_seconds=(datetime.now() - start_time).total_seconds(),
                    error_log="No items collected from sources"
                )

            # 2. Deduplicate against state
            self.logger.info(f"[2/6] Deduplicating {len(items)} items...")
            new_items = self.state.filter_new(items)
            self.logger.info(f"Found {len(new_items)} new items")

            # Always generate digest for monitoring purposes
            # If few new items, supplement with recent items from database
            min_items_target = self.config.research.get('min_items', 5)
            items_to_rank = new_items

            if len(new_items) < min_items_target:
                self.logger.warning(f"Only {len(new_items)} new items (target: {min_items_target})")
                self.logger.info("Supplementing with recent items from last 7 days...")

                # Get recent items from database to supplement
                # Use larger limit (100) to ensure diversity across sources, especially arXiv papers
                recent_items = self.state.get_recent_items(days=7, limit=100)
                self.logger.info(f"Found {len(recent_items)} recent items from database")

                # Combine new items with recent items (new items first)
                items_to_rank = new_items + recent_items
                self.logger.info(f"Total items to rank: {len(items_to_rank)} ({len(new_items)} new + {len(recent_items)} recent)")

            # 3. Score and rank
            self.logger.info(f"[3/6] Scoring and ranking items...")
            ranked_items = self._score_and_rank(items_to_rank)

            # 4. Select items with diversity constraints
            target_items = self.config.research.get('target_items', 10)
            max_items = self.config.research.get('max_items', 15)
            target_count = min(target_items, max_items)
            self.logger.info(f"[4/6] Selecting {target_count} items with diversity constraints...")
            selected = self._select_with_diversity(ranked_items, target_count)
            self.logger.info(f"Selected {len(selected)} items for digest")

            # 5. Synthesize digest using Claude
            self.logger.info(f"[5/6] Synthesizing digest...")
            digest_content = self.synthesis_agent.synthesize(
                selected,
                all_items=items,
                new_items_count=len(new_items)
            )

            # 6. Write output
            output_path = None
            if not dry_run:
                self.logger.info(f"[6/6] Writing digest...")
                output_path = self.digest_writer.write(digest_content)

                self.logger.info(f"Recording run in database...")
                runtime = (datetime.now() - start_time).total_seconds()
                self.state.record_run(
                    items,
                    new_items,
                    selected,
                    output_path,
                    runtime
                )
            else:
                self.logger.info("[DRY RUN] Skipping file write and database update")

            # 7. Return result
            runtime = (datetime.now() - start_time).total_seconds()

            self.logger.info("=" * 60)
            self.logger.info("Research cycle completed successfully!")
            self.logger.info("=" * 60)

            return ResearchResult(
                timestamp=start_time,
                status='success',
                items_found=len(items),
                items_new=len(new_items),
                items_included=len(selected),
                output_path=output_path,
                runtime_seconds=runtime
            )

        except Exception as e:
            runtime = (datetime.now() - start_time).total_seconds()

            self.logger.error(f"Error during research cycle: {e}")
            self.logger.debug("Full traceback:", exc_info=True)

            return ResearchResult(
                timestamp=start_time,
                status='failed',
                items_found=0,
                items_new=0,
                items_included=0,
                output_path=None,
                runtime_seconds=runtime,
                error_log=str(e)
            )

    def _score_and_rank(self, items: List[Dict]) -> List[Dict]:
        """Score items by relevance and rank."""
        scorer = RelevanceScorer(self.config, self.state)

        scored = [
            {**item, 'score': scorer.score(item)}
            for item in items
        ]

        # Sort by score (descending)
        return sorted(scored, key=lambda x: x['score'], reverse=True)

    def _select_with_diversity(self, ranked_items: List[Dict], target_count: int = 15) -> List[Dict]:
        """
        Select items with diversity constraints to ensure balanced digest.

        Constraints:
        - Minimum per tier (Tier 1: 3, Tier 2: 5, Tier 5: 1)
        - Maximum per source (3 items max from any single source)
        - Minimum arXiv papers (2-3)

        Args:
            ranked_items: Items sorted by relevance score (descending)
            target_count: Target number of items (default: 15)

        Returns:
            List of selected items meeting diversity constraints
        """
        from collections import defaultdict

        selected = []
        source_counts = defaultdict(int)
        tier_counts = defaultdict(int)
        arxiv_count = 0

        # Diversity constraints
        MIN_TIER_1 = 3  # At least 3 Tier 1 (primary sources)
        MIN_TIER_2 = 5  # At least 5 Tier 2 (strategic thinkers - HIGHEST VALUE)
        MIN_TIER_5 = 1  # At least 1 Tier 5 (implementation)
        MIN_ARXIV = 2   # At least 2 arXiv papers
        MAX_PER_SOURCE = 3  # No more than 3 from any single source

        # First pass: Ensure minimums are met
        # Priority order: Tier 2 (strategic), arXiv, Tier 1, Tier 5

        # 1. Get top Tier 2 items (strategic thinkers - HIGHEST PRIORITY)
        tier_2_items = [item for item in ranked_items if item.get('source_metadata', {}).get('tier') == 2]
        for item in tier_2_items[:MIN_TIER_2]:
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[2] += 1

        # 2. Get arXiv papers
        arxiv_items = [item for item in ranked_items if 'arxiv' in item.get('source', '').lower()]
        for item in arxiv_items[:MIN_ARXIV]:
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE and item not in selected:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[1] += 1
                arxiv_count += 1

        # 3. Get Tier 1 items (but exclude arXiv we already added)
        tier_1_items = [
            item for item in ranked_items
            if item.get('source_metadata', {}).get('tier') == 1
            and 'arxiv' not in item.get('source', '').lower()
        ]
        for item in tier_1_items:
            if tier_counts[1] >= MIN_TIER_1:
                break
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE and item not in selected:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[1] += 1

        # 4. Get Tier 5 items (implementation)
        tier_5_items = [item for item in ranked_items if item.get('source_metadata', {}).get('tier') == 5]
        for item in tier_5_items:
            if tier_counts[5] >= MIN_TIER_5:
                break
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE and item not in selected:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[5] += 1

        # Second pass: Fill remaining slots with highest-scored items
        for item in ranked_items:
            if len(selected) >= target_count:
                break

            if item in selected:
                continue

            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE:
                selected.append(item)
                source_counts[source] += 1
                tier = item.get('source_metadata', {}).get('tier', 0)
                tier_counts[tier] += 1

        # Log diversity stats
        self.logger.info(f"Diversity stats:")
        self.logger.info(f"  Tier 1 (Primary): {tier_counts[1]} items")
        self.logger.info(f"  Tier 2 (Strategic): {tier_counts[2]} items")
        self.logger.info(f"  Tier 3 (News): {tier_counts[3]} items")
        self.logger.info(f"  Tier 5 (Implementation): {tier_counts[5]} items")
        self.logger.info(f"  arXiv papers: {arxiv_count} items")
        self.logger.info(f"  Unique sources: {len(source_counts)} sources")

        # Warn if diversity constraints not met
        if tier_counts[2] < MIN_TIER_2:
            self.logger.warning(f"⚠️  Only {tier_counts[2]} Tier 2 items (target: {MIN_TIER_2})")
        if arxiv_count < MIN_ARXIV:
            self.logger.warning(f"⚠️  Only {arxiv_count} arXiv papers (target: {MIN_ARXIV})")
        if tier_counts[1] < MIN_TIER_1:
            self.logger.warning(f"⚠️  Only {tier_counts[1]} Tier 1 items (target: {MIN_TIER_1})")

        # Re-sort by score before returning
        return sorted(selected, key=lambda x: x['score'], reverse=True)

    def _get_source_name(self, item: Dict) -> str:
        """Extract source name from item for diversity tracking."""
        metadata = item.get('source_metadata', {})
        source_name = metadata.get('feed_name') or metadata.get('blog_name') or item.get('source', 'Unknown')
        # Clean up source name
        source_name = source_name.replace('rss:', '').replace('blog:', '').strip()
        return source_name
