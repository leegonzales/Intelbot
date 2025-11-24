"""Synthesis agent using Claude."""

from typing import List, Dict
from datetime import datetime
import anthropic

from research_agent.utils.logger import get_logger


class SynthesisAgent:
    """
    Uses Claude to synthesize digest from items.
    """

    def __init__(self, config, prompt_manager):
        self.config = config
        self.prompts = prompt_manager
        self.logger = get_logger("agents.synthesis")

        # Initialize Anthropic client
        self.client = anthropic.Anthropic()

    def synthesize(self, items: List[Dict], all_items: List[Dict] = None, new_items_count: int = None, validation_report: Dict = None, db_stats: Dict = None) -> str:
        """
        Generate digest markdown from items.

        Args:
            items: Selected and ranked items for digest
            all_items: All collected items (for comprehensive source stats)
            new_items_count: Number of new items found today
            validation_report: Quality validation results
            db_stats: Database statistics

        Returns:
            Formatted markdown digest
        """
        # Load prompts
        system_prompt = self.prompts.get_system_prompt()
        synthesis_template = self.prompts.get_synthesis_template()

        # Get current date and timestamp for digest header
        now = datetime.now()
        date_iso = now.strftime("%Y-%m-%d")
        date_full = now.strftime("%A, %B %d, %Y")
        timestamp_full = now.strftime("%Y-%m-%d %H:%M:%S %Z")

        # Build context from items
        items_context = self._format_items_context(items)
        # Use all_items for comprehensive source stats if available
        source_stats, source_count = self._calculate_source_stats(all_items if all_items else items, len(items))

        # Determine if we're using supplemental content
        items_selected = len(items)
        new_count = new_items_count if new_items_count is not None else items_selected
        using_supplemental = new_count < items_selected

        # Format validation report for digest
        validation_block = self._format_validation_block(validation_report) if validation_report else ""

        # Format DB stats for digest
        db_stats_block = self._format_db_stats_block(db_stats) if db_stats else ""

        # Construct synthesis prompt
        synthesis_prompt = f"""
{system_prompt}

---

## Current Date and Timestamp

Today is {date_full} ({date_iso})
Full timestamp: {timestamp_full}

Use this date in the digest header. Do NOT use any other date.
Include the full timestamp in the frontmatter and footer.

---

## Source Information

Total unique sources: {source_count}
Total items analyzed: {len(all_items) if all_items else len(items)}
Items selected for digest: {len(items)}
New items found: {new_count}
{"Supplemental items from last 7 days: " + str(items_selected - new_count) if using_supplemental else ""}

Use these numbers in the frontmatter and footer.

{"**IMPORTANT**: Only " + str(new_count) + " new items were found today. The digest includes " + str(items_selected - new_count) + " recent items from the last 7 days to provide context. Add a note at the top of the TL;DR: 'Limited new content today (" + str(new_count) + " new items). Digest supplemented with recent highlights.'" if using_supplemental else ""}

---

## Your Task

Generate today's research digest using the following items and the synthesis template.

## Items to Synthesize

{items_context}

## Source Statistics

{source_stats}

## Synthesis Template

{synthesis_template}

## Database Statistics (INCLUDE AT VERY TOP)

{db_stats_block}

## Validation Report (INCLUDE AFTER DB STATS)

{validation_block}

**CRITICAL**: Include these blocks immediately after the frontmatter (YAML block), BEFORE the title and TL;DR.

The structure should be:
1. Frontmatter (---...---)
2. Database Statistics section
3. Quality Control block (validation)
4. Title (# AI Research Digest...)
5. TL;DR
6. Rest of digest

## Instructions

1. **FIRST**: Include the Database Statistics block right after frontmatter
2. **SECOND**: Include the Quality Control block after DB stats
3. **THIRD**: Add the title and TL;DR
4. Group items by theme (agent architectures, prompt engineering, etc.)
5. Write concise, precise descriptions (max 3 sentences per item)
6. Include "why this matters" for each item
7. Generate TL;DR summarizing key developments
8. Note any signals/trends
9. Follow template structure exactly
10. **IMPORTANT**: Use the Source Statistics above to populate the "📡 Sources Polled" footer section

## DATE ACCURACY REQUIREMENTS (CRITICAL)

**You MUST display publication dates EXACTLY as provided in the item metadata.**

- Today is {date_iso} (November 16, 2025)
- Each item above includes a "Date" field - USE THAT EXACT DATE
- If date shows "2025-11-13", display as "Nov 2025" (current year)
- If date shows "2024-12-19", display as "Dec 2024" (last year)
- If date shows "2025-10-15", display as "Oct 2025" (current year)
- DO NOT default dates to 2024 unless explicitly stated as 2024
- DO NOT invent or guess dates

**VALIDATE**: Before finalizing, verify every article date matches the metadata provided.

Begin synthesis now.
"""

        # Run Claude synthesis
        self.logger.info("Synthesizing digest with Claude...")

        try:
            message = self.client.messages.create(
                model=self.config.model.get('name', 'claude-sonnet-4-20250514'),
                max_tokens=self.config.model.get('max_tokens', 16000),
                temperature=self.config.model.get('temperature', 0.3),
                messages=[
                    {"role": "user", "content": synthesis_prompt}
                ]
            )

            digest_content = message.content[0].text

            return digest_content

        except Exception as e:
            self.logger.error(f"Error synthesizing with Claude: {e}")
            # Fallback to simple template
            return self._fallback_synthesis(items)

    def _format_items_context(self, items: List[Dict]) -> str:
        """Format items for Claude context."""
        formatted = []

        for i, item in enumerate(items, 1):
            # Extract tier info
            metadata = item.get('source_metadata', {})
            tier = metadata.get('tier', 'Unknown')
            priority = metadata.get('priority', 'medium')
            perspective = metadata.get('perspective', '')
            focus = metadata.get('focus', '')

            tier_label = f"Tier {tier}"
            if tier == 1:
                tier_label += " (Primary Source - Research Labs/arXiv)"
            elif tier == 2:
                tier_label += " (Synthesis Source - Strategic Analysis)"
            elif tier == 3:
                tier_label += " (News Aggregator)"
            elif tier == 5:
                tier_label += " (Implementation Blog)"

            formatted.append(f"""
### Item {i}: {item['title']}

- **URL**: {item['url']}
- **Source**: {item['source']}
- **Tier**: {tier_label}
- **Priority**: {priority}
- **Date**: {item.get('published_date', 'Unknown')}
- **Author**: {item.get('author', 'Unknown')}
- **Relevance Score**: {item.get('score', 0):.3f}
{f"- **Perspective**: {perspective}" if perspective else ""}
{f"- **Focus**: {focus}" if focus else ""}

**Snippet**:
{item.get('snippet', 'No snippet available')}

**Tags**: {', '.join(item.get('tags', []))}

---
""")

        return "\n".join(formatted)

    def _calculate_source_stats(self, items: List[Dict], selected_count: int = None):
        """
        Calculate source statistics for the footer.

        Returns:
            Tuple of (stats_string, unique_source_count)
        """
        from collections import defaultdict

        tier_sources = defaultdict(lambda: defaultdict(int))
        unique_sources = set()

        for item in items:
            metadata = item.get('source_metadata', {})
            tier = metadata.get('tier', 'Unknown')
            source_name = metadata.get('feed_name') or metadata.get('blog_name') or item.get('source', 'Unknown')

            # Clean up source name
            source_name = source_name.replace('rss:', '').replace('blog:', '').strip()

            tier_sources[tier][source_name] += 1
            unique_sources.add(source_name)

        # Format the statistics
        stats = []
        if selected_count and selected_count != len(items):
            stats.append(f"**Total Items Analyzed**: {len(items)}")
            stats.append(f"**Items Included in Digest**: {selected_count}")
        else:
            stats.append(f"**Total Items in Digest**: {len(items)}")
        stats.append("")

        # Tier 1
        if 1 in tier_sources:
            stats.append("**Tier 1 (Primary Sources - Research & Labs)**:")
            for source, count in sorted(tier_sources[1].items()):
                stats.append(f"- {source}: {count} items")
            stats.append("")

        # Tier 2
        if 2 in tier_sources:
            stats.append("**Tier 2 (Synthesis Sources - Strategic Analysis)**:")
            for source, count in sorted(tier_sources[2].items()):
                stats.append(f"- {source}: {count} items")
            stats.append("")

        # Tier 3
        if 3 in tier_sources:
            stats.append("**Tier 3 (News & Community)**:")
            for source, count in sorted(tier_sources[3].items()):
                stats.append(f"- {source}: {count} items")
            stats.append("")

        # Tier 5
        if 5 in tier_sources:
            stats.append("**Tier 5 (Implementation Blogs)**:")
            for source, count in sorted(tier_sources[5].items()):
                stats.append(f"- {source}: {count} items")
            stats.append("")

        return ("\n".join(stats), len(unique_sources))

    def _fallback_synthesis(self, items: List[Dict]) -> str:
        """
        Fallback synthesis if Claude API fails.

        Returns basic markdown list of items.
        """
        from datetime import datetime

        now = datetime.now()

        lines = [
            "---",
            f"date: {now.strftime('%Y-%m-%d')}",
            f"timestamp: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "type: research-digest",
            "tags: [research, ai, daily-digest]",
            "---",
            "",
            f"# AI Research Digest - {now.strftime('%A, %B %d, %Y')}",
            "",
            "## Items",
            ""
        ]

        for i, item in enumerate(items, 1):
            lines.append(f"### {i}. {item['title']}")
            lines.append(f"**Source**: [{item['source']}]({item['url']})")
            if item.get('author'):
                lines.append(f"**Author**: {item['author']}")
            if item.get('published_date'):
                lines.append(f"**Date**: {item['published_date']}")
            lines.append("")
            lines.append(item.get('snippet') or '')
            lines.append("")

        return "\n".join(lines)

    def _format_validation_block(self, validation: Dict) -> str:
        """
        Format validation report for inclusion in digest.

        Creates a compact, scannable block showing quality metrics.
        """
        if not validation:
            return ""

        status = validation.get('status', 'UNKNOWN')
        metrics = validation.get('metrics', {})
        warnings = validation.get('warnings', [])
        errors = validation.get('errors', [])

        # Status emoji
        status_emoji = {
            'PASS': '✅',
            'WARNING': '⚠️',
            'FAILED': '❌'
        }.get(status, '❓')

        lines = [
            "---",
            "",
            f"## 📋 Quality Control: {status_emoji} {status}",
            ""
        ]

        # Key metrics in compact format
        lines.append("**Digest Metrics:**")
        lines.append(f"- Content Age: {metrics.get('newest_item_days', 'N/A')}-{metrics.get('oldest_item_days', 'N/A')} days old (avg: {metrics.get('avg_item_age_days', 0):.1f}d)")
        lines.append(f"- Source Diversity: {metrics.get('unique_sources', 0)} unique sources")
        lines.append(f"- arXiv Papers: {metrics.get('arxiv_count', 0)}")
        lines.append(f"- Tier Distribution: T1={metrics.get('tier1_count', 0)} | T2={metrics.get('tier2_count', 0)} | T3={metrics.get('tier3_count', 0)} | T5={metrics.get('tier5_count', 0)}")

        # Anthropic representation (only show if > 20%)
        anthropic_pct = metrics.get('anthropic_pct', 0)
        if anthropic_pct > 20:
            lines.append(f"- Anthropic Content: {metrics.get('anthropic_count', 0)} items ({anthropic_pct:.0f}%)")

        lines.append("")

        # Errors (critical)
        if errors:
            lines.append("**❌ ERRORS:**")
            for error in errors:
                lines.append(f"- {error}")
            lines.append("")

        # Warnings (informational)
        if warnings:
            lines.append("**⚠️ WARNINGS:**")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")

        return "\n".join(lines)

    def _format_db_stats_block(self, db_stats: Dict) -> str:
        """
        Format database statistics for inclusion in digest.

        Creates a compact, informative block showing database state.
        """
        if not db_stats:
            return ""

        lines = [
            "---",
            "",
            "## 📊 Research Database Stats",
            ""
        ]

        # Total items and runs
        lines.append(f"**Database Overview:**")
        lines.append(f"- Total Items Tracked: {db_stats.get('total_items', 0):,}")
        lines.append(f"- Total Research Runs: {db_stats.get('total_runs', 0):,}")

        # Recent activity
        lines.append(f"- Items Added (Last 7 Days): {db_stats.get('items_last_7_days', 0):,}")
        lines.append(f"- Items Added (Last 30 Days): {db_stats.get('items_last_30_days', 0):,}")

        # Date range
        oldest = db_stats.get('oldest_item_date')
        newest = db_stats.get('newest_item_date')
        if oldest and newest:
            from datetime import datetime
            try:
                oldest_dt = datetime.fromisoformat(oldest.replace('Z', '+00:00'))
                newest_dt = datetime.fromisoformat(newest.replace('Z', '+00:00'))
                lines.append(f"- Content Date Range: {oldest_dt.strftime('%Y-%m-%d')} to {newest_dt.strftime('%Y-%m-%d')}")
            except:
                lines.append(f"- Content Date Range: {oldest} to {newest}")

        lines.append("")

        # Top sources
        top_sources = db_stats.get('top_sources', [])
        if top_sources:
            lines.append("**Top Sources (All Time):**")
            for src in top_sources:
                source_name = src['source'].replace('rss:', '').replace('blog:', '').replace('arxiv:', '').strip()
                lines.append(f"- {source_name}: {src['count']:,} items")
            lines.append("")

        return "\n".join(lines)
