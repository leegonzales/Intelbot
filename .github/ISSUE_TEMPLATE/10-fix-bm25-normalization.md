---
title: "[HIGH] Fix BM25 score normalization for title similarity"
labels: bug, priority-2, database, search
---

## Problem

BM25 score normalization formula is incorrect, likely preventing title similarity detection from working. The threshold of 0.85 may never trigger.

## Current Behavior

```python
# BM25 scores are negative (lower is better)
# Normalize to 0-1 range (higher is better)
normalized_score = 1 / (1 + abs(row['score']))
```

- BM25 scores from SQLite FTS5 are negative
- Range is typically -10 to 0 (lower = better match)
- Current formula: `1 / (1 + abs(score))`
- For score = -1: `1 / (1 + 1) = 0.5`
- For score = -10: `1 / (1 + 10) = 0.09`
- Threshold of 0.85 is likely never reached
- Title similarity detection doesn't work

## Expected Behavior

- BM25 scores properly normalized to 0-1 range
- Better matches have higher normalized scores
- Threshold of 0.85 triggers for similar titles
- Deduplication catches near-duplicate titles

## Files Affected

- `research_agent/storage/state.py:137` - Score normalization
- `research_agent/storage/state.py:77` - Similarity threshold (hardcoded)

## Research Needed

1. Test actual BM25 score ranges from SQLite FTS5
2. Determine proper normalization formula
3. Calibrate threshold based on real data

## Proposed Solution

**Step 1: Research actual scores**
```python
# Add logging to see actual BM25 scores
cursor = conn.execute("""
    SELECT title, bm25(items_fts) as score
    FROM items_fts
    JOIN seen_items ON items_fts.rowid = seen_items.id
    WHERE items_fts MATCH ?
    ORDER BY score
    LIMIT 10
""", (fts_query,))

for row in cursor:
    print(f"Title: {row['title']}, BM25: {row['score']}")
```

**Step 2: Choose normalization**

Option A - Min-Max normalization:
```python
# Assume BM25 range is [-20, 0]
MIN_SCORE = -20
MAX_SCORE = 0
normalized = (row['score'] - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)
```

Option B - Sigmoid normalization:
```python
import math
normalized = 1 / (1 + math.exp(row['score']))  # Sigmoid
```

Option C - Inverse negative score:
```python
# If scores range [-10, 0], invert and normalize
normalized = min(abs(row['score']) / 10, 1.0)
```

**Step 3: Make threshold configurable**
```python
# In config.yaml
research:
  dedup:
    title_similarity: 0.85  # Already in spec

# In state.py
threshold = config.research.dedup.get('title_similarity', 0.85)
```

## Acceptance Criteria

- [ ] Research actual BM25 score ranges from FTS5
- [ ] Implement correct normalization formula
- [ ] Document expected score ranges
- [ ] Title similarity detection works
- [ ] Threshold configurable in config.yaml
- [ ] Test with real duplicate titles
- [ ] Document how to tune threshold

## Testing

Create test cases:
```python
# Add similar titles
state.add_item({'url': 'http://a.com', 'title': 'Claude Agent SDK for Production'})
state.add_item({'url': 'http://b.com', 'title': 'Production Agent SDK with Claude'})

# Should detect as similar
is_dup, reason = state.is_duplicate(
    'http://c.com',
    'Claude Agent SDK in Production Systems',
    None
)
assert is_dup and 'similar_title' in reason
```

## Priority

**HIGH** - Core deduplication feature doesn't work.

## Effort Estimate

2-3 hours (includes research and testing)

## Related Issues

#8 Optimize filter_new Performance (FTS usage)
#12 Make Thresholds Configurable

## References

- BUG_REPORT.md #10
- TASK_LIST.md Task 2.5
- SQLite FTS5 BM25: https://www.sqlite.org/fts5.html#the_bm25_function
