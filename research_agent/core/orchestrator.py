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
            print("=" * 60)
            print("Starting research cycle...")
            print("=" * 60)

            # 1. Collect items from all sources
            print("\n[1/6] Collecting items from sources...")
            items = self.source_agent.collect_all()

            if not items:
                print("Warning: No items collected from any source")
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
            print(f"\n[2/6] Deduplicating {len(items)} items...")
            new_items = self.state.filter_new(items)
            print(f"Found {len(new_items)} new items")

            if len(new_items) < self.config.research.get('min_items', 3):
                print(f"Warning: Only {len(new_items)} new items (minimum: {self.config.research.get('min_items', 3)})")
                print("Skipping digest generation")
                return ResearchResult(
                    timestamp=start_time,
                    status='partial',
                    items_found=len(items),
                    items_new=len(new_items),
                    items_included=0,
                    output_path=None,
                    runtime_seconds=(datetime.now() - start_time).total_seconds(),
                    error_log="Insufficient new items for digest"
                )

            # 3. Score and rank
            print(f"\n[3/6] Scoring and ranking items...")
            ranked_items = self._score_and_rank(new_items)

            # 4. Select top N for digest
            target_items = self.config.research.get('target_items', 10)
            max_items = self.config.research.get('max_items', 15)
            selected = ranked_items[:min(target_items, max_items)]
            print(f"Selected {len(selected)} items for digest")

            # 5. Synthesize digest using Claude
            print(f"\n[4/6] Synthesizing digest...")
            digest_content = self.synthesis_agent.synthesize(selected)

            # 6. Write output
            output_path = None
            if not dry_run:
                print(f"\n[5/6] Writing digest...")
                output_path = self.digest_writer.write(digest_content)

                print(f"\n[6/6] Recording run in database...")
                runtime = (datetime.now() - start_time).total_seconds()
                self.state.record_run(
                    items,
                    new_items,
                    selected,
                    output_path,
                    runtime
                )
            else:
                print("\n[DRY RUN] Skipping file write and database update")

            # 7. Return result
            runtime = (datetime.now() - start_time).total_seconds()

            print("\n" + "=" * 60)
            print("Research cycle completed successfully!")
            print("=" * 60)

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

            print(f"\nError during research cycle: {e}")

            import traceback
            traceback.print_exc()

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
