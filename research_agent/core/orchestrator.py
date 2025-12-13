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

    def run(self, dry_run: bool = False, target_date: Optional[datetime] = None) -> ResearchResult:
        """
        Execute a complete research cycle.

        Args:
            dry_run: If True, don't write outputs or update state
            target_date: Optional date for the report (for backfilling)

        Returns:
            ResearchResult with metadata about the run
        """
        start_time = datetime.now()
        self.target_date = target_date  # Store for use in digest writing

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

            # 4.5. Validate selected items (QC check)
            self.logger.info(f"[4.5/6] Validating digest quality...")
            validation = self._validate_digest_quality(selected, all_items=items)

            # Log validation results
            if validation['errors']:
                for error in validation['errors']:
                    self.logger.error(f"VALIDATION ERROR: {error}")
            if validation['warnings']:
                for warning in validation['warnings']:
                    self.logger.warning(f"VALIDATION WARNING: {warning}")

            # Fail if critical errors found
            if validation['errors']:
                raise ValueError(f"Digest validation failed: {validation['errors']}")

            # 5. Synthesize digest using Claude
            self.logger.info(f"[5/6] Synthesizing digest...")

            # Get database statistics for digest header
            db_stats = self.state.get_database_stats()

            digest_content = self.synthesis_agent.synthesize(
                selected,
                all_items=items,
                new_items_count=len(new_items),
                validation_report=validation,
                db_stats=db_stats,
                target_date=self.target_date
            )

            # 6. Write output
            output_path = None
            if not dry_run:
                self.logger.info(f"[6/6] Writing digest...")
                output_path = self.digest_writer.write(digest_content, date=self.target_date)

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

        # Diversity constraints (tuned for balanced strategic + academic coverage)
        MIN_TIER_1 = 3  # At least 3 Tier 1 (primary sources - lab announcements)
        MIN_TIER_2 = 5  # At least 5 Tier 2 (strategic thinkers) - INCREASED for better synthesis coverage
        MIN_TIER_3 = 1  # At least 1 Tier 3 (news/community - HackerNews)
        MIN_TIER_5 = 1  # At least 1 Tier 5 (implementation)
        MIN_ARXIV = 4   # At least 4 arXiv papers for academic coverage
        MAX_PER_SOURCE = 3  # No more than 3 from any single source

        # First pass: Ensure minimums are met
        # Priority order: Tier 2 (strategic), arXiv, Tier 1, Tier 5
        # T2 gets highest priority because QC showed it's consistently underweight

        # 1. Get top Tier 2 items (strategic thinkers - HIGHEST PRIORITY)
        # Take more than minimum initially to ensure we hit the target after source filtering
        tier_2_items = [item for item in ranked_items if item.get('source_metadata', {}).get('tier') == 2]
        for item in tier_2_items[:MIN_TIER_2 + 2]:  # Try a few extra in case of source conflicts
            if tier_counts[2] >= MIN_TIER_2:
                break
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[2] += 1

        # 2. Get academic papers (arXiv + Semantic Scholar + OpenReview)
        # Try more items than minimum to account for source conflicts
        academic_sources = ['arxiv', 'semantic_scholar', 'openreview']
        arxiv_items = [
            item for item in ranked_items
            if any(src in item.get('source', '').lower() for src in academic_sources)
        ]
        for item in arxiv_items[:MIN_ARXIV + 3]:  # Try extra items in case of conflicts
            if arxiv_count >= MIN_ARXIV:
                break
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

        # 5. Get Tier 3 items (news/community - e.g. HackerNews)
        tier_3_items = [item for item in ranked_items if item.get('source_metadata', {}).get('tier') == 3]
        for item in tier_3_items:
            if tier_counts[3] >= MIN_TIER_3:
                break
            source = self._get_source_name(item)
            if source_counts[source] < MAX_PER_SOURCE and item not in selected:
                selected.append(item)
                source_counts[source] += 1
                tier_counts[3] += 1

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

    def _validate_digest_quality(self, selected: List[Dict], all_items: List[Dict] = None) -> Dict:
        """
        Validate digest quality before synthesis.

        Checks for:
        - Date freshness (no items > 30 days old)
        - arXiv representation (>= 2 papers)
        - Source diversity (>= 6 unique sources)
        - Anthropic over-representation (< 40%)
        - Missing critical metadata

        Returns:
            Dict with 'status', 'errors', 'warnings', and 'metrics'
        """
        from collections import Counter
        from datetime import datetime, timedelta

        errors = []
        warnings = []
        metrics = {}

        # Calculate metrics
        total_items = len(selected)

        # 1. Check date freshness
        max_age_days = 30
        stale_items = []
        ages = []
        missing_dates = []

        for item in selected:
            pub_date = item.get('published_date')
            if not pub_date:
                missing_dates.append(item['title'][:50])
                continue

            try:
                if isinstance(pub_date, str):
                    pub_dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                else:
                    pub_dt = pub_date

                if hasattr(pub_dt, 'tzinfo') and pub_dt.tzinfo:
                    pub_dt = pub_dt.replace(tzinfo=None)

                age_days = (datetime.now() - pub_dt).days
                ages.append(age_days)

                if age_days > max_age_days:
                    stale_items.append({
                        'title': item['title'][:50],
                        'age_days': age_days,
                        'published': pub_date
                    })
            except Exception as e:
                self.logger.debug(f"Date parsing error for {item['title'][:30]}: {e}")

        # Warning if stale content found (not blocking - still generate digest)
        if stale_items:
            for stale in stale_items:
                warnings.append(f"Stale content ({stale['age_days']}d old): {stale['title']}")

        # Warning if many missing dates
        if len(missing_dates) > 3:
            warnings.append(f"{len(missing_dates)} items missing published_date")

        # Calculate age metrics
        if ages:
            metrics['oldest_item_days'] = max(ages)
            metrics['avg_item_age_days'] = sum(ages) / len(ages)
            metrics['newest_item_days'] = min(ages)
        else:
            metrics['oldest_item_days'] = None
            metrics['avg_item_age_days'] = None

        # 2. Check academic paper representation (arXiv + Semantic Scholar + OpenReview)
        academic_sources = ['arxiv', 'semantic_scholar', 'openreview']
        arxiv_count = sum(
            1 for item in selected
            if any(src in item.get('source', '').lower() for src in academic_sources)
        )
        metrics['arxiv_count'] = arxiv_count

        if arxiv_count < 4:
            warnings.append(f"Low academic paper representation: {arxiv_count} papers (target: 4+)")

        # 3. Check source diversity
        sources = [self._get_source_name(item) for item in selected]
        unique_sources = len(set(sources))
        metrics['unique_sources'] = unique_sources

        if unique_sources < 6:
            warnings.append(f"Low source diversity: {unique_sources} sources (target: 6+)")

        # 4. Check Anthropic over-representation
        anthropic_count = sum(1 for s in sources if 'anthropic' in s.lower())
        anthropic_pct = (anthropic_count / total_items * 100) if total_items > 0 else 0
        metrics['anthropic_count'] = anthropic_count
        metrics['anthropic_pct'] = anthropic_pct

        if anthropic_pct > 40:
            warnings.append(f"Anthropic over-represented: {anthropic_count}/{total_items} items ({anthropic_pct:.0f}%)")

        # 5. Tier distribution
        tier_counts = Counter(item.get('source_metadata', {}).get('tier', 0) for item in selected)
        metrics['tier1_count'] = tier_counts.get(1, 0)
        metrics['tier2_count'] = tier_counts.get(2, 0)
        metrics['tier3_count'] = tier_counts.get(3, 0)
        metrics['tier5_count'] = tier_counts.get(5, 0)

        if tier_counts.get(2, 0) < 5:
            warnings.append(f"Low Tier 2 (strategic): {tier_counts.get(2, 0)} items (target: 5)")

        # 6. Overall collection stats (if all_items provided)
        if all_items:
            metrics['total_collected'] = len(all_items)
            metrics['selection_rate'] = (total_items / len(all_items) * 100) if len(all_items) > 0 else 0

        # Determine overall status
        if errors:
            status = 'FAILED'
        elif warnings:
            status = 'WARNING'
        else:
            status = 'PASS'

        return {
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'metrics': metrics
        }
