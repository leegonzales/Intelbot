---
title: "[CRITICAL] Fix database UNIQUE constraint violations in record_run()"
labels: bug, critical, priority-1, database
---

## Problem

`StateManager.record_run()` attempts to insert items that may already exist in the database, causing UNIQUE constraint violations on the `url` field.

## Current Behavior

- `record_run()` loops through `items_new` and calls `add_item()`
- If an item was already deduped but URL exists from previous run
- Crashes with:
  ```
  sqlite3.IntegrityError: UNIQUE constraint failed: seen_items.url
  ```
- Research run fails, no digest written, data lost

## Expected Behavior

- Handle duplicate URLs gracefully
- Return existing item ID if URL already in database
- Successfully link items to runs
- No constraint violations

## Files Affected

- `research_agent/storage/state.py:149-177` - `add_item()` method
- `research_agent/storage/state.py:238-248` - `record_run()` item insertion loop

## Root Causes

**Issue 1**: `add_item()` uses INSERT which fails on duplicate URLs

**Issue 2**: Item comparison in line 243 uses object reference instead of URL:
```python
if item in items_included:  # This compares dict objects by reference!
```

## Proposed Solution

**Fix 1: Use INSERT OR IGNORE**
```python
def add_item(self, item: Dict) -> int:
    """Add new item or return existing ID."""
    with self._get_conn() as conn:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO seen_items (
                url, content_hash, title, ...
            ) VALUES (?, ?, ?, ...)
        """, (...))

        # Get ID (either newly inserted or existing)
        cursor = conn.execute("SELECT id FROM seen_items WHERE url = ?", (item['url'],))
        return cursor.fetchone()[0]
```

**Fix 2: Compare items by URL**
```python
# Build URL set for O(1) lookup
included_urls = {item['url'] for item in items_included}

for item in items_new:
    item_id = self.add_item(item)

    # Link to run if included in digest
    if item['url'] in included_urls:
        rank = items_included.index(item)  # Or use enumerate
        conn.execute(...)
```

**Better Fix 2: Build mapping upfront**
```python
# Build mapping of URLs to ranks
url_to_rank = {
    item['url']: idx
    for idx, item in enumerate(items_included)
}

for item in items_new:
    item_id = self.add_item(item)

    if item['url'] in url_to_rank:
        rank = url_to_rank[item['url']]
        conn.execute(
            "INSERT INTO run_items (run_id, item_id, rank) VALUES (?, ?, ?)",
            (run_id, item_id, rank)
        )
```

## Acceptance Criteria

- [ ] No UNIQUE constraint violations
- [ ] `add_item()` returns ID for existing or new items
- [ ] Items correctly linked to runs in `run_items` table
- [ ] Can query items by run_id successfully
- [ ] Works with items that appear in multiple runs
- [ ] History commands show correct item-run relationships

## Priority

**CRITICAL** - Research runs crash, data lost.

## Effort Estimate

1 hour

## Related Issues

#9 Fix Item-to-Run Linking

## References

- BUG_REPORT.md #5 and #9
- TASK_LIST.md Task 1.5 and 2.4
