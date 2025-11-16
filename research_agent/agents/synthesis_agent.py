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

    def synthesize(self, items: List[Dict], all_items: List[Dict] = None) -> str:
        """
        Generate digest markdown from items.

        Args:
            items: Selected and ranked items for digest
            all_items: All collected items (for comprehensive source stats)

        Returns:
            Formatted markdown digest
        """
        # Load prompts
        system_prompt = self.prompts.get_system_prompt()
        synthesis_template = self.prompts.get_synthesis_template()

        # Get current date for digest header
        now = datetime.now()
        date_iso = now.strftime("%Y-%m-%d")
        date_full = now.strftime("%A, %B %d, %Y")

        # Build context from items
        items_context = self._format_items_context(items)
        # Use all_items for comprehensive source stats if available
        source_stats, source_count = self._calculate_source_stats(all_items if all_items else items, len(items))

        # Construct synthesis prompt
        synthesis_prompt = f"""
{system_prompt}

---

## Current Date

Today is {date_full} ({date_iso})

Use this date in the digest header. Do NOT use any other date.

---

## Source Information

Total unique sources: {source_count}
Total items analyzed: {len(all_items) if all_items else len(items)}
Items selected for digest: {len(items)}

Use these numbers in the frontmatter and footer.

---

## Your Task

Generate today's research digest using the following items and the synthesis template.

## Items to Synthesize

{items_context}

## Source Statistics

{source_stats}

## Synthesis Template

{synthesis_template}

## Instructions

1. Group items by theme (agent architectures, prompt engineering, etc.)
2. Write concise, precise descriptions (max 3 sentences per item)
3. Include "why this matters" for each item
4. Generate TL;DR summarizing key developments
5. Note any signals/trends
6. Follow template structure exactly
7. **IMPORTANT**: Use the Source Statistics above to populate the "📡 Sources Polled" footer section

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

        lines = [
            "---",
            f"date: {datetime.now().strftime('%Y-%m-%d')}",
            "type: research-digest",
            "tags: [research, ai, daily-digest]",
            "---",
            "",
            f"# AI Research Digest - {datetime.now().strftime('%A, %B %d, %Y')}",
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
