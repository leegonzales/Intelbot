# arXiv Paper Inclusion Analysis

**Date**: 2025-11-16
**Issue**: 61-80 arXiv papers collected, but 0 included in digests

---

## Current Constraints on arXiv Papers

### 1. Collection Filters (arxiv.py)

**Time window**: Last 7 days only
```python
if (datetime.now() - published_naive).days > 7:
    continue
```

**Max results**: 20 papers per category
```python
max_results = self.config.get('max_results', 20)
```

**Categories**: Limited to 4 categories
- cs.AI (Artificial Intelligence)
- cs.LG (Machine Learning)
- cs.CL (Computation and Language)
- cs.HC (Human-Computer Interaction)

**Content**: Abstract only (~1.3KB average)
```python
content=result.summary  # Just the abstract, not full paper
```

### 2. Scoring Disadvantages

**Scoring formula**:
```python
score = (
    keyword_score * 0.25 +      # Keyword matching
    source_score * 0.40 +       # Tier weight
    engagement_score * 0.15 +   # Citations/points
    recency_score * 0.10 +      # How recent
    novelty_score * 0.10        # Uniqueness
)
```

**arXiv paper typical scores**:

| Component | arXiv Papers | Blog Posts (Tier 2) | Difference |
|-----------|--------------|---------------------|------------|
| **Keyword (25%)** | ~0.10 (low) | ~0.20 (high) | -50% |
| **Tier (40%)** | 0.36 (Tier 1 = 0.9) | 0.40 (Tier 2 = 1.0) | -10% |
| **Engagement (15%)** | 0.075 (no citations) | 0.10+ (with engagement) | -25% |
| **Recency (10%)** | 0.08-0.10 (recent) | 0.05-0.08 (older) | +25% |
| **Novelty (10%)** | 0.08-0.10 (new) | 0.05-0.08 (varies) | +25% |
| **TOTAL** | **~0.71** | **~0.88** | **-19%** |

### 3. Why arXiv Scores Lower

#### A. Keyword Mismatch

**High-value keywords** (from scoring.py):
```python
'multi-agent', 'agent', 'rlhf', 'alignment', 'prompt engineering',
'tool use', 'autonomous', 'framework', 'production', 'benchmark',
'claude', 'gpt', 'llm', 'transformer', 'in-context', 'chain-of-thought'
```

**Academic papers use formal language**:
- "optimization" not "prompt engineering"
- "inference" not "in-context"
- "reinforcement learning from human feedback" not "rlhf"
- Mathematical notation and formal terminology

**Example from database**:
```
Title: "Alignment Debt: The Hidden Work of Making AI Usable"
Abstract: 1728 bytes of formal academic language
Keywords matched: Maybe "alignment", "AI" (1-2 keywords)
Score: ~0.10 keyword score (need 3 for 1.0)
```

#### B. No Engagement Signals

**arXiv source doesn't collect citations**:
```python
# arxiv.py line 59-65
source_metadata={
    'arxiv_id': result.entry_id.split('/')[-1],
    'categories': [...],
    'pdf_url': result.pdf_url,
    'tier': self.tier,
    'priority': self.priority,
    # NO 'citations' field!
}
```

**Engagement scoring defaults to 0.5**:
```python
# scoring.py line 127
return 0.5  # No engagement data
```

Blog posts with comments, upvotes, or HN points score higher (0.6-1.0).

#### C. Limited Content for Matching

**Content comparison**:
- arXiv: 1.3KB average (abstract only)
- Anthropic Engineering: 14.5KB average (full article)
- Interconnects: 42KB average (full article)
- Latent Space: 66KB average (full transcript)

More content = more keyword matches = higher scores.

#### D. Tier Weight Disadvantage

After our improvements:
- **Tier 2** (strategic synthesis): 1.0 weight (HIGHEST)
- **Tier 1** (primary sources including arXiv): 0.9 weight
- Tier weight is 40% of total score

This means Tier 2 blog posts get a built-in 4% advantage:
- Tier 2: 1.0 × 0.40 = 0.40
- Tier 1: 0.9 × 0.40 = 0.36
- Difference: 0.04 (4% of total score)

---

## Database Evidence

**Last 7 days collection**:
```
arxiv: 61 papers (MOST collected!)
  Average content: 1,303 bytes
  Average age: 3-4 days
  Included in digests: 0
```

**Example recent papers** (from Nov 12):
1. "When Thinking Pays Off: Incentive Alignment for Human-AI Collaboration"
2. "Alignment Debt: The Hidden Work of Making AI Usable"
3. "How AI Responses Shape User Beliefs"
4. "Why Open Small AI Models Matter for Interactive Art"

These look highly relevant but scored too low vs blog posts!

---

## Root Causes

### Primary Issue: Keyword-Centric Scoring

The scoring algorithm is optimized for **practitioner blog posts** with informal language, not academic papers.

Academic abstracts:
- Use formal terminology
- Avoid brand names ("Claude", "GPT")
- Use full terms ("reinforcement learning from human feedback" vs "RLHF")
- Focus on methods and results, not implications
- Mathematical and technical precision

### Secondary Issue: Tier 2 Prioritization

Our recent fix to prioritize Tier 2 (strategic synthesis) over Tier 1 (primary sources) was intended to favor Mollick/Willison over Anthropic Engineering.

**Unintended consequence**: Also deprioritized arXiv papers (also Tier 1).

### Tertiary Issue: No Citation Data

arXiv API doesn't provide citation counts for new papers. Would need to:
- Integrate with Semantic Scholar API
- Add citation lookup step
- Cache citation counts

---

## Recommended Fixes

### Priority 1: arXiv-Specific Scoring Boost (EASY)

**Add arXiv bonus in scoring.py**:

```python
def _source_score(self, item: Dict) -> float:
    """Score based on source tier."""
    metadata = item.get('source_metadata', {})
    source = item.get('source', '').lower()

    # Special boost for arXiv papers (research foundation)
    if 'arxiv' in source:
        return 1.0  # Max tier score to ensure inclusion

    # Check for explicit tier metadata first (new tiered system)
    if 'tier' in metadata:
        # ... rest of code
```

**Impact**: arXiv papers get same tier score as Tier 2 (1.0 instead of 0.9)
**Result**: +4% total score → competitive with blog posts

### Priority 2: Expand Keyword Dictionary for Academic Papers (MEDIUM)

**Add academic equivalents**:

```python
self.high_value_keywords = {
    # Existing practitioner terms
    'multi-agent', 'agent', 'rlhf', 'alignment', 'prompt engineering',
    'tool use', 'autonomous', 'framework', 'production', 'benchmark',
    'claude', 'gpt', 'llm', 'transformer', 'in-context', 'chain-of-thought',

    # Academic equivalents
    'reinforcement learning from human feedback', 'optimization',
    'fine-tuning', 'pre-training', 'inference', 'reasoning',
    'multimodal', 'vision-language', 'embedding', 'attention',
    'neural network', 'deep learning', 'supervised learning',
    'zero-shot', 'few-shot', 'transfer learning', 'generalization'
}
```

**Impact**: Better keyword matching for academic abstracts
**Result**: +5-10% keyword score

### Priority 3: Fetch Full Paper Text (HARD, OPTIONAL)

**Use PDF extraction**:
```python
# In arxiv.py, fetch PDF and extract text
import PyPDF2
full_text = self._extract_pdf_text(result.pdf_url)
content = result.summary + "\n\n" + full_text[:5000]  # Summary + intro
```

**Impact**: More content for keyword matching (1.3KB → 6-8KB)
**Result**: Significantly better keyword scores

**Downside**: Slower collection, more API calls, PDF parsing complexity

### Priority 4: Separate arXiv Papers in Diversity Constraints (EASY)

Already done! We have:
```python
MIN_ARXIV = 2   # At least 2 arXiv papers
```

But this only works if arXiv papers make it into the ranked list first.

### Priority 5: Add Citation Lookup (HARD, OPTIONAL)

**Integrate Semantic Scholar API**:
```python
# Look up citation count
s2_data = self._lookup_semantic_scholar(arxiv_id)
metadata['citations'] = s2_data.get('citationCount', 0)
```

**Impact**: Engagement score for papers (0.5 → 0.6-0.8 depending on citations)
**Result**: +1-5% total score

**Downside**: Extra API calls, rate limits, complexity

---

## Quick Win: arXiv Scoring Boost

**Implement Priority 1** (5 minutes):

1. Edit `research_agent/utils/scoring.py`
2. Add arXiv check at top of `_source_score()`
3. Return 1.0 for arXiv papers
4. Test with dry run

**Expected result**: 2-3 arXiv papers in every digest

---

## Long-Term Solution: Separate Scoring Profiles

Consider different scoring weights for different source types:

**Academic papers** (arXiv):
- Keyword: 15% (lower, formal language)
- Tier: 50% (higher, trust the source)
- Engagement: 5% (lower, no citations for new papers)
- Recency: 20% (higher, want newest research)
- Novelty: 10%

**Practitioner blogs** (Tier 2):
- Keyword: 25% (current)
- Tier: 40% (current)
- Engagement: 15% (current)
- Recency: 10% (current)
- Novelty: 10% (current)

**Lab announcements** (Tier 1 blogs):
- Keyword: 20%
- Tier: 35%
- Engagement: 20% (high value)
- Recency: 15%
- Novelty: 10%

---

## Testing Plan

1. **Implement arXiv boost** (Priority 1)
2. **Run dry run** with recent database
3. **Verify** 2+ arXiv papers in top 15
4. **Check** they make sense contextually
5. **If successful**, expand keywords (Priority 2)
6. **Re-test** and measure improvement

---

## Success Metrics

**Current state**:
- arXiv papers collected: 61-80 per run
- arXiv papers included: 0 (0%)

**Target state**:
- arXiv papers included: 2-3 (2-4%)
- Quality: Relevant to AI transformation/agents focus
- Balance: Mix of academic + practitioner perspectives

**Ideal distribution** (from DIGEST_ASSESSMENT.md):
```
Tier 1 (Primary): 5-6 items (33-40%)
  ├─ arXiv: 2-3 papers ✅ TARGET
  ├─ Anthropic: 1-2 items
  ├─ DeepMind: 1 item
  └─ OpenAI: 1 item
```

---

## Conclusion

**Root cause**: Scoring algorithm optimized for practitioner blogs, not academic papers.

**Quick fix**: Boost arXiv tier score to 1.0 (same as Tier 2).

**Better fix**: Expand keyword dictionary with academic equivalents.

**Best fix**: Separate scoring profiles per source type.

**Recommendation**: Implement Priority 1 now (5 min), then Priority 2 (30 min) if needed.

---

**Analysis Date**: 2025-11-16
**Next Step**: Implement arXiv scoring boost
