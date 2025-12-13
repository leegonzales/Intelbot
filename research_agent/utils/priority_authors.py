"""Priority authors and labs for boosted paper selection."""

from typing import Dict, List, Set
import re


# Priority authors and research groups
# Papers from these authors/labs get automatic boost regardless of other signals
PRIORITY_AUTHORS: Dict[str, Dict] = {
    # === ALWAYS INCLUDE - Non-AI but critical to your interests ===
    "michael levin": {
        "affiliation": "Tufts University / Allen Discovery Center",
        "focus": "bioelectricity, morphogenesis, collective intelligence, xenobots",
        "priority": "critical",  # ALWAYS include
        "reason": "Foundational research on collective intelligence and emergent behavior",
    },

    # === AI Safety & Evaluation ===
    "beth barnes": {
        "affiliation": "METR",
        "focus": "AI evaluation, dangerous capabilities, autonomy",
        "priority": "critical",
        "reason": "Leading AI safety evaluations at METR",
    },

    # === AGI Research / ARC Prize ===
    "francois chollet": {
        "affiliation": "Ndea / ARC Prize Foundation",
        "focus": "AGI, program synthesis, abstraction, reasoning",
        "priority": "critical",
        "reason": "ARC benchmark creator, AGI research",
    },
    "françois chollet": {  # Handle accent variant
        "affiliation": "Ndea / ARC Prize Foundation",
        "focus": "AGI, program synthesis, abstraction, reasoning",
        "priority": "critical",
        "reason": "ARC benchmark creator, AGI research",
    },

    # === Major AI Labs - Key Researchers ===
    "dario amodei": {
        "affiliation": "Anthropic",
        "focus": "AI safety, scaling",
        "priority": "high",
    },
    "chris olah": {
        "affiliation": "Anthropic",
        "focus": "interpretability, mechanistic understanding",
        "priority": "high",
    },
    "jan leike": {
        "affiliation": "Anthropic (formerly OpenAI)",
        "focus": "alignment, superalignment",
        "priority": "high",
    },
    "ilya sutskever": {
        "affiliation": "SSI (formerly OpenAI)",
        "focus": "scaling, capabilities",
        "priority": "high",
    },
    "andrej karpathy": {
        "affiliation": "Independent (formerly Tesla/OpenAI)",
        "focus": "neural networks, education",
        "priority": "high",
    },
    "yann lecun": {
        "affiliation": "Meta AI",
        "focus": "self-supervised learning, world models",
        "priority": "high",
    },
    "demis hassabis": {
        "affiliation": "Google DeepMind",
        "focus": "AGI, neuroscience-inspired AI",
        "priority": "high",
    },
    "jeff dean": {
        "affiliation": "Google",
        "focus": "systems, scaling",
        "priority": "high",
    },

    # === Reasoning & Chain-of-Thought ===
    "jason wei": {
        "affiliation": "OpenAI (formerly Google)",
        "focus": "chain-of-thought, emergent abilities",
        "priority": "high",
    },

    # === Agents & Tool Use ===
    "shunyu yao": {
        "affiliation": "OpenAI (formerly Princeton)",
        "focus": "ReAct, agents, reasoning",
        "priority": "high",
    },

    # === Alignment & Safety ===
    "paul christiano": {
        "affiliation": "ARC",
        "focus": "alignment, RLHF foundations",
        "priority": "high",
    },
    "stuart russell": {
        "affiliation": "UC Berkeley",
        "focus": "AI safety, value alignment",
        "priority": "high",
    },

    # === Interpretability ===
    "neel nanda": {
        "affiliation": "Google DeepMind",
        "focus": "mechanistic interpretability",
        "priority": "medium",
    },

    # === Scaling Laws ===
    "jared kaplan": {
        "affiliation": "Anthropic",
        "focus": "scaling laws",
        "priority": "high",
    },
}

# Priority institutions/labs - papers with these affiliations get boosted
PRIORITY_INSTITUTIONS: Set[str] = {
    # AI Labs
    "anthropic",
    "openai",
    "deepmind",
    "google deepmind",
    "meta ai",
    "fair",  # Facebook AI Research

    # Safety Organizations
    "metr",
    "arc evals",
    "alignment research center",
    "center for ai safety",
    "cais",
    "miri",  # Machine Intelligence Research Institute
    "redwood research",

    # AGI Research
    "arc prize",
    "ndea",

    # Michael Levin's Labs
    "levin lab",
    "allen discovery center",
    "tufts",  # For bioelectricity papers

    # Academic - Top AI Programs
    "stanford ai",
    "berkeley ai",
    "cmu",
    "mit csail",
    "mila",
}

# Keywords that indicate relevance to Michael Levin's work
# (for cross-domain discovery)
LEVIN_ADJACENT_KEYWORDS: Set[str] = {
    "bioelectricity",
    "bioelectric",
    "morphogenesis",
    "collective intelligence",
    "xenobot",
    "planaria",
    "regeneration",
    "developmental biology",
    "cellular automata",
    "self-organization",
    "emergence",
    "swarm intelligence",
    "multi-agent collective",
}


def check_priority_author(author_string: str) -> Dict:
    """
    Check if any priority authors are in the author string.

    Args:
        author_string: Comma-separated author names

    Returns:
        Dict with match info or empty dict if no match
    """
    if not author_string:
        return {}

    author_lower = author_string.lower()

    for author, info in PRIORITY_AUTHORS.items():
        if author in author_lower:
            return {
                "matched_author": author,
                "priority": info.get("priority", "medium"),
                "affiliation": info.get("affiliation", ""),
                "focus": info.get("focus", ""),
                "reason": info.get("reason", "Priority author"),
            }

    return {}


def check_priority_institution(text: str) -> Dict:
    """
    Check if any priority institutions are mentioned in text.

    Args:
        text: Text to search (abstract, affiliations, etc.)

    Returns:
        Dict with match info or empty dict if no match
    """
    if not text:
        return {}

    text_lower = text.lower()

    for institution in PRIORITY_INSTITUTIONS:
        if institution in text_lower:
            return {
                "matched_institution": institution,
                "priority": "medium",
            }

    return {}


def check_levin_adjacent(text: str) -> bool:
    """
    Check if text contains keywords adjacent to Michael Levin's research.

    This helps discover relevant cross-domain papers that might not
    be in typical AI categories.

    Args:
        text: Title + abstract text

    Returns:
        True if contains Levin-adjacent keywords
    """
    if not text:
        return False

    text_lower = text.lower()

    for keyword in LEVIN_ADJACENT_KEYWORDS:
        if keyword in text_lower:
            return True

    return False


def get_author_boost(item: Dict) -> float:
    """
    Calculate author/institution boost for an item.

    Args:
        item: Research item dict

    Returns:
        Boost multiplier (1.0 = no boost, >1.0 = boosted)
    """
    boost = 1.0

    # Check author priority (handle None values)
    author = item.get('author') or ''
    author_match = check_priority_author(author)
    if author_match:
        priority = author_match.get('priority', 'medium')
        if priority == 'critical':
            boost *= 2.0  # Double score for critical authors
        elif priority == 'high':
            boost *= 1.5
        else:
            boost *= 1.25

    # Check content for institutions (handle None values)
    title = item.get('title') or ''
    content_text = item.get('content') or item.get('snippet') or ''
    content = f"{title} {content_text}"
    inst_match = check_priority_institution(content)
    if inst_match:
        boost *= 1.2

    # Check for Levin-adjacent research
    if check_levin_adjacent(content):
        boost *= 1.3

    return boost
