"""Substack theme matching for content opportunity flagging.

Matches digest items against Lee's established Substack themes to identify
potential post topics and content opportunities.

Reference: /Users/leegonzales/Projects/leegonzales/substack/posts/research/future-post-ideas.md
"""

import re
from typing import List, Dict, Set, Tuple


# Theme definitions with keywords and patterns
SUBSTACK_THEMES = {
    "orchestration_shift": {
        "name": "Orchestration Shift",
        "description": "Conductors→orchestrators, agent coordination, supervision patterns",
        "keywords": [
            "orchestrat", "coordinat", "supervisor", "conductor", "multi-agent",
            "swarm", "handoff", "delegation", "agent team", "agent fleet",
            "hierarchical agent", "meta-agent", "agent graph"
        ],
        "patterns": [
            r"agent.{0,20}coordinat",
            r"multi.?agent",
            r"agent.{0,15}supervisor",
            r"orchestrat.{0,20}agent"
        ]
    },
    "context_engineering": {
        "name": "Context Engineering",
        "description": "Attention scarcity, context optimization, prompt engineering evolution",
        "keywords": [
            "context window", "context length", "attention", "prompt engineer",
            "context engineer", "token budget", "context compression",
            "retrieval augment", "RAG", "context management", "long context",
            "context overflow", "context limit"
        ],
        "patterns": [
            r"context.{0,15}engineer",
            r"context.{0,15}optim",
            r"prompt.{0,15}engineer",
            r"attention.{0,15}scarcit"
        ]
    },
    "agent_memory": {
        "name": "Agent Memory Problem",
        "description": "Persistence, continual learning, state management across sessions",
        "keywords": [
            "memory", "persistent", "continual learn", "episodic", "semantic memory",
            "working memory", "long-term memory", "state persist", "session",
            "memory augment", "memory bank", "memory consolidat"
        ],
        "patterns": [
            r"agent.{0,15}memory",
            r"persist.{0,15}state",
            r"continual.{0,15}learn",
            r"memory.{0,15}persist"
        ]
    },
    "tool_design": {
        "name": "Tool Design",
        "description": "Agent-native APIs, MCP, fewer tools > more, tool-use patterns",
        "keywords": [
            "tool use", "tool call", "function call", "MCP", "model context protocol",
            "tool design", "api design", "agent api", "tool selection",
            "tool routing", "fewer tools", "tool minimal"
        ],
        "patterns": [
            r"tool.{0,15}design",
            r"agent.{0,15}api",
            r"tool.{0,15}select",
            r"mcp.{0,15}server"
        ]
    },
    "evaluation_gap": {
        "name": "Evaluation Gap",
        "description": "Benchmarks vs production, real-world evaluation, GDPval-style",
        "keywords": [
            "benchmark", "evaluat", "SWE-bench", "real-world", "production eval",
            "held-out", "test set", "accuracy", "benchmark gap", "eval harness",
            "human eval", "A/B test", "live eval"
        ],
        "patterns": [
            r"benchmark.{0,15}vs.{0,15}prod",
            r"eval.{0,15}gap",
            r"real.?world.{0,15}eval",
            r"production.{0,15}eval"
        ]
    },
    "simplicity_movement": {
        "name": "Simplicity Counter-Movement",
        "description": "Grug Brain, emergence over planning, minimal viable agents",
        "keywords": [
            "simplicity", "minimal", "simple agent", "grug", "less is more",
            "emergence", "emergent", "complexity debt", "over-engineer",
            "simple prompt", "few-shot", "zero-shot"
        ],
        "patterns": [
            r"simpl.{0,15}agent",
            r"minimal.{0,15}viable",
            r"less.{0,10}is.{0,10}more",
            r"emergent.{0,15}behavio"
        ]
    },
    "specification_evolution": {
        "name": "Specification Evolution",
        "description": "Prompts as curricula, iteration over specs, living documents",
        "keywords": [
            "specification", "curriculum", "iterative", "living document",
            "prompt evolut", "prompt iteration", "instruction tuning",
            "system prompt", "prompt version", "prompt management"
        ],
        "patterns": [
            r"prompt.{0,15}evolut",
            r"spec.{0,15}iteration",
            r"living.{0,15}document",
            r"prompt.{0,15}curricul"
        ]
    },
    "scaling_architecture": {
        "name": "Scaling Architecture",
        "description": "Async, stateless, distributed agents, infrastructure patterns",
        "keywords": [
            "async", "stateless", "distributed", "horizontal scale",
            "queue", "worker", "background task", "paralleliz",
            "infrastructure", "deploy", "kubernetes", "serverless"
        ],
        "patterns": [
            r"async.{0,15}agent",
            r"stateless.{0,15}agent",
            r"distribut.{0,15}agent",
            r"scale.{0,15}agent"
        ]
    }
}


def match_themes(items: List[Dict]) -> Dict[str, List[Tuple[str, str, float]]]:
    """
    Match digest items against Substack themes.

    Args:
        items: List of digest items with 'title', 'snippet', 'tags' fields

    Returns:
        Dict mapping theme_id -> list of (item_title, match_reason, confidence)
    """
    matches = {theme_id: [] for theme_id in SUBSTACK_THEMES}

    for item in items:
        # Handle None values safely
        title = (item.get('title') or '').lower()
        snippet = (item.get('snippet') or '').lower()
        tags_list = item.get('tags') or []
        tags = ' '.join(tags_list).lower()
        text = f"{title} {snippet} {tags}"

        for theme_id, theme in SUBSTACK_THEMES.items():
            score = 0.0
            match_reasons = []

            # Check keywords
            for keyword in theme['keywords']:
                if keyword.lower() in text:
                    score += 0.3
                    if keyword.lower() in title:
                        score += 0.2  # Bonus for title match
                        match_reasons.append(f"'{keyword}' in title")
                    else:
                        match_reasons.append(f"'{keyword}' in content")

            # Check patterns
            for pattern in theme['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 0.4
                    match_reasons.append(f"pattern: {pattern[:20]}...")

            # Cap score at 1.0
            score = min(score, 1.0)

            # Only include strong matches
            if score >= 0.3:
                matches[theme_id].append((
                    item.get('title', 'Unknown'),
                    ', '.join(match_reasons[:3]),  # Top 3 reasons
                    score
                ))

    # Filter out themes with no matches
    return {k: v for k, v in matches.items() if v}


def format_theme_section(matches: Dict[str, List[Tuple[str, str, float]]]) -> str:
    """
    Format theme matches as a markdown section for the digest.

    Args:
        matches: Output from match_themes()

    Returns:
        Markdown string for the Substack Opportunities section
    """
    if not matches:
        return ""

    lines = [
        "---",
        "",
        "## Substack Opportunities",
        "",
        "The following items connect to your established writing themes:",
        ""
    ]

    for theme_id, theme_matches in sorted(
        matches.items(),
        key=lambda x: max(m[2] for m in x[1]),  # Sort by highest confidence
        reverse=True
    ):
        theme = SUBSTACK_THEMES[theme_id]
        lines.append(f"### {theme['name']}")
        lines.append(f"*{theme['description']}*")
        lines.append("")

        # Sort matches by confidence
        for title, reason, confidence in sorted(theme_matches, key=lambda x: x[2], reverse=True)[:3]:
            confidence_indicator = "" if confidence >= 0.7 else "" if confidence >= 0.5 else ""
            lines.append(f"- {confidence_indicator} **{title[:60]}{'...' if len(title) > 60 else ''}**")
            lines.append(f"  - Match: {reason}")
        lines.append("")

    return "\n".join(lines)


def get_theme_summary(items: List[Dict]) -> str:
    """
    Get a formatted theme match summary for items.

    Args:
        items: List of digest items

    Returns:
        Formatted markdown section, or empty string if no matches
    """
    matches = match_themes(items)
    return format_theme_section(matches)
