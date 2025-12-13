"""AI slop detection for filtering low-quality AI-generated content."""

import re
from typing import Dict, Tuple, List


# Common AI slop phrases and patterns
# These are phrases that appear disproportionately in AI-generated academic text
SLOP_PHRASES = [
    # Hedging and filler
    "it is important to note that",
    "it is worth noting that",
    "it should be noted that",
    "in this paper, we",
    "in this work, we",
    "in recent years",
    "has gained significant attention",
    "has attracted considerable attention",
    "has received increasing attention",
    "plays a crucial role",
    "plays a vital role",
    "plays an important role",
    "of paramount importance",
    "pave the way",
    "paves the way",
    "shed light on",
    "sheds light on",
    "leverage the power of",
    "harness the power of",
    "unlock the potential",
    "unlocking the potential",
    "delve into",
    "delve deeper",
    "delves into",

    # Overused AI paper phrases
    "comprehensive evaluation",
    "extensive experiments",
    "extensive evaluations",
    "rigorous evaluation",
    "thorough evaluation",
    "comprehensive analysis",
    "comprehensive study",
    "comprehensive framework",
    "novel framework",
    "novel approach",
    "innovative approach",
    "pioneering approach",
    "cutting-edge",
    "state-of-the-art results",
    "achieves state-of-the-art",
    "surpasses existing methods",
    "outperforms existing",
    "demonstrates superior",
    "exhibits remarkable",
    "showcases the effectiveness",
    "underscores the importance",

    # Empty superlatives
    "remarkable performance",
    "impressive results",
    "significant improvements",
    "substantial improvements",
    "notable improvements",
    "promising results",
    "encouraging results",

    # Vague technical claims
    "seamlessly integrates",
    "effectively captures",
    "efficiently handles",
    "elegantly addresses",
    "robustly handles",

    # AI assistant tells
    "as an ai",
    "as a language model",
    "i don't have personal",
    "i cannot provide",
]

# Regex patterns for structural slop
SLOP_PATTERNS = [
    r"(?:first|second|third|fourth|fifth)(?:ly)?,?\s+we",  # Enumerated claims
    r"to\s+(?:the\s+)?best\s+of\s+our\s+knowledge",  # Hedge phrase
    r"(?:large|extensive|comprehensive)\s+(?:set\s+of\s+)?experiments",  # Vague claims
    r"(?:significantly|substantially|considerably)\s+(?:outperforms?|improves?|enhances?)",  # Inflated claims
    r"a\s+(?:novel|new|innovative)\s+(?:method|approach|framework|technique|paradigm)",  # Novelty claims
]

# High-quality signal phrases (reduce slop score)
QUALITY_SIGNALS = [
    # Specific technical details
    "ablation study",
    "ablation experiments",
    "statistical significance",
    "p-value",
    "confidence interval",
    "hyperparameter",
    "learning rate",
    "batch size",
    "training steps",
    "compute budget",
    "flops",
    "gpu hours",

    # Reproducibility signals
    "code available",
    "open source",
    "github",
    "reproducible",
    "implementation details",

    # Honest limitations
    "limitation",
    "limitations",
    "fails to",
    "does not handle",
    "future work",
    "room for improvement",

    # Specific benchmarks (not just "benchmark")
    "imagenet",
    "glue",
    "superglue",
    "mmlu",
    "hellaswag",
    "arc challenge",
    "winogrande",
    "gsm8k",
    "math benchmark",
    "humaneval",
    "mbpp",
]


def detect_slop(text: str) -> Tuple[float, List[str]]:
    """
    Detect AI slop in text and return a score.

    Args:
        text: Text to analyze (title + abstract)

    Returns:
        Tuple of (slop_score, list of detected slop phrases)
        Score ranges from 0.0 (no slop) to 1.0 (heavy slop)
        Papers with score > 0.5 are likely AI-generated or low quality
    """
    if not text:
        return 0.0, []

    text_lower = text.lower()
    detected = []

    # Count slop phrase matches
    slop_count = 0
    for phrase in SLOP_PHRASES:
        if phrase in text_lower:
            slop_count += 1
            detected.append(phrase)

    # Count slop pattern matches
    for pattern in SLOP_PATTERNS:
        matches = re.findall(pattern, text_lower)
        slop_count += len(matches)
        detected.extend(matches)

    # Count quality signals (reduce score)
    quality_count = 0
    for signal in QUALITY_SIGNALS:
        if signal in text_lower:
            quality_count += 1

    # Calculate base score (normalized by text length)
    # Longer texts naturally have more phrases, so normalize
    words = len(text.split())
    normalized_slop = slop_count / max(words / 100, 1)  # Per 100 words

    # Base score from slop density
    # 0-2 slop phrases per 100 words = 0.0-0.3
    # 3-5 slop phrases per 100 words = 0.3-0.6
    # 6+ slop phrases per 100 words = 0.6-1.0
    base_score = min(normalized_slop * 0.15, 1.0)

    # Quality signals reduce score
    quality_reduction = min(quality_count * 0.05, 0.3)

    final_score = max(0.0, base_score - quality_reduction)

    return round(final_score, 3), detected[:10]  # Return top 10 detected phrases


def get_slop_assessment(score: float) -> str:
    """
    Get human-readable assessment of slop score.

    Args:
        score: Slop score from detect_slop()

    Returns:
        Assessment string
    """
    if score < 0.1:
        return "clean"
    elif score < 0.25:
        return "minor_slop"
    elif score < 0.5:
        return "moderate_slop"
    elif score < 0.75:
        return "heavy_slop"
    else:
        return "likely_ai_generated"


def score_paper_quality(item: Dict) -> Dict:
    """
    Score a paper item for quality, including slop detection.

    Args:
        item: Research item dict with title, snippet, content

    Returns:
        Dict with quality metrics
    """
    # Combine title and content for analysis (handle None values)
    title = item.get('title') or ''
    content = item.get('content') or item.get('snippet') or ''
    text = f"{title} {content}"

    slop_score, detected_phrases = detect_slop(text)
    assessment = get_slop_assessment(slop_score)

    return {
        'slop_score': slop_score,
        'slop_assessment': assessment,
        'slop_phrases_detected': detected_phrases,
        'is_likely_slop': slop_score >= 0.5,
    }
