"""Synthesis agent using Claude."""

from typing import List, Dict
import anthropic


class SynthesisAgent:
    """
    Uses Claude to synthesize digest from items.
    """

    def __init__(self, config, prompt_manager):
        self.config = config
        self.prompts = prompt_manager

        # Initialize Anthropic client
        self.client = anthropic.Anthropic()

    def synthesize(self, items: List[Dict]) -> str:
        """
        Generate digest markdown from items.

        Args:
            items: Selected and ranked items for digest

        Returns:
            Formatted markdown digest
        """
        # Load prompts
        system_prompt = self.prompts.get_system_prompt()
        synthesis_template = self.prompts.get_synthesis_template()

        # Build context from items
        items_context = self._format_items_context(items)

        # Construct synthesis prompt
        synthesis_prompt = f"""
{system_prompt}

---

## Your Task

Generate today's research digest using the following items and the synthesis template.

## Items to Synthesize

{items_context}

## Synthesis Template

{synthesis_template}

## Instructions

1. Group items by theme (agent architectures, prompt engineering, etc.)
2. Write concise, precise descriptions (max 3 sentences per item)
3. Include "why this matters" for each item
4. Generate TL;DR summarizing key developments
5. Note any signals/trends
6. Follow template structure exactly

Begin synthesis now.
"""

        # Run Claude synthesis
        print("Synthesizing digest with Claude...")

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
            print(f"Error synthesizing with Claude: {e}")
            # Fallback to simple template
            return self._fallback_synthesis(items)

    def _format_items_context(self, items: List[Dict]) -> str:
        """Format items for Claude context."""
        formatted = []

        for i, item in enumerate(items, 1):
            formatted.append(f"""
### Item {i}: {item['title']}

- **URL**: {item['url']}
- **Source**: {item['source']}
- **Date**: {item.get('published_date', 'Unknown')}
- **Author**: {item.get('author', 'Unknown')}
- **Score**: {item.get('score', 0):.3f}

**Snippet**:
{item.get('snippet', 'No snippet available')}

**Tags**: {', '.join(item.get('tags', []))}

---
""")

        return "\n".join(formatted)

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
            lines.append(item.get('snippet', ''))
            lines.append("")

        return "\n".join(lines)
