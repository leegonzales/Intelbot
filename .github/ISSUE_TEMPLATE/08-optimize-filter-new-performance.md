---
title: "[HIGH] Optimize filter_new() database performance"
labels: bug, priority-2, performance, database
---

## Problem

`StateManager.filter_new()` opens a new database connection for each item check. With 100+ items, this creates 100+ database connections, making the operation very slow.

## Current Behavior

```python
def filter_new(self, items: List[Dict]) -> List[Dict]:
    new_items = []
    for item in items:
        is_dup, reason = self.is_duplicate(...)  # Opens DB connection
        if not is_dup:
            new_items.append(item)
    return new_items
```

- O(n) database connections for n items
- Each `is_duplicate()` call opens connection
- Very slow with 100+ items (5-10 seconds)
- Inefficient resource usage

## Expected Behavior

- Batch duplicate checking
- 1-2 database connections total
- Fast even with 1000+ items (<1 second)
- Efficient resource usage

## Files Affected

- `research_agent/storage/state.py:179-201` - `filter_new()` method
- `research_agent/storage/state.py:45-81` - `is_duplicate()` method

## Proposed Solution

Create batch duplicate checking:

```python
def filter_new(self, items: List[Dict]) -> List[Dict]:
    """Filter items to only new ones (batch optimized)."""
    if not items:
        return []

    new_items = []

    with self._get_conn() as conn:
        # Batch URL check
        urls = [item['url'] for item in items]
        placeholders = ','.join('?' * len(urls))
        cursor = conn.execute(
            f"SELECT url FROM seen_items WHERE url IN ({placeholders})",
            urls
        )
        existing_urls = {row['url'] for row in cursor}

        # Batch content hash check (for items with content)
        items_with_content = [
            (self._hash_content(item.get('content', '')), item)
            for item in items
            if item.get('content')
        ]

        if items_with_content:
            hashes = [h for h, _ in items_with_content]
            placeholders = ','.join('?' * len(hashes))
            cursor = conn.execute(
                f"SELECT content_hash FROM seen_items WHERE content_hash IN ({placeholders})",
                hashes
            )
            existing_hashes = {row['content_hash'] for row in cursor}
        else:
            existing_hashes = set()

        # Filter new items
        for item in items:
            # Check URL
            if item['url'] in existing_urls:
                continue

            # Check content hash
            if item.get('content'):
                content_hash = self._hash_content(item['content'])
                if content_hash in existing_hashes:
                    continue

            # TODO: FTS similarity check (still needs per-item query)
            # For now, skip FTS in batch mode or make it optional

            new_items.append(item)

    return new_items
```

## Acceptance Criteria

- [ ] Single database connection for batch check
- [ ] O(1) database connections regardless of item count
- [ ] Handles 100+ items in <1 second
- [ ] Maintains same deduplication accuracy
- [ ] Works with URL, content hash deduplication
- [ ] FTS similarity check optional or optimized separately

## Priority

**HIGH** - Major performance bottleneck with large item counts.

## Effort Estimate

2 hours

## Related Issues

#10 Fix BM25 Score Normalization (FTS similarity)

## References

- BUG_REPORT.md #8
- TASK_LIST.md Task 2.3
