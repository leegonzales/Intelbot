---
title: "[HIGH] Fix item-to-run linking using URL comparison"
labels: bug, priority-2, database
---

## Problem

`StateManager.record_run()` compares dict objects by reference instead of URL when linking items to runs. This causes items to never be linked to runs in the `run_items` table.

## Current Behavior

```python
for item in items_new:
    item_id = self.add_item(item)

    # Link to run if included in digest
    if item in items_included:  # ← Compares dict objects by reference!
        rank = items_included.index(item)
        conn.execute("INSERT INTO run_items ...")
```

- Dict comparison uses object identity (`id(item)`)
- Items are different dict objects even if same URL
- `item in items_included` always returns False
- No items ever linked to runs
- `run_items` table always empty
- History commands don't work

## Expected Behavior

- Items compared by URL (unique identifier)
- Included items correctly linked to runs
- `run_items` table populated
- Can query items by run_id
- History shows which items were in which digests

## Files Affected

- `research_agent/storage/state.py:243-248` - Item comparison logic

## Proposed Solution

**Option 1: Compare by URL**
```python
# Build set of included URLs for O(1) lookup
included_urls = {item['url'] for item in items_included}

for item in items_new:
    item_id = self.add_item(item)

    if item['url'] in included_urls:
        # Find rank
        rank = next(
            i for i, inc_item in enumerate(items_included)
            if inc_item['url'] == item['url']
        )
        conn.execute(
            "INSERT INTO run_items (run_id, item_id, rank) VALUES (?, ?, ?)",
            (run_id, item_id, rank)
        )
```

**Option 2: Build URL-to-rank mapping (cleaner)**
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
            "INSERT INTO run_items (run_id, item_id, rank, theme) VALUES (?, ?, ?, ?)",
            (run_id, item_id, rank, None)  # theme could be extracted from synthesis
        )
```

**Option 3: Return item_id mapping from add_item loop**
```python
# Add all items and build URL -> ID mapping
url_to_id = {}
for item in items_new:
    item_id = self.add_item(item)
    url_to_id[item['url']] = item_id

# Link included items
for rank, item in enumerate(items_included):
    if item['url'] in url_to_id:
        item_id = url_to_id[item['url']]
        conn.execute(
            "INSERT INTO run_items (run_id, item_id, rank) VALUES (?, ?, ?)",
            (run_id, item_id, rank)
        )
```

Recommend **Option 2** for clarity.

## Acceptance Criteria

- [ ] Items correctly linked to runs
- [ ] `run_items` table populated
- [ ] Can query: `SELECT * FROM run_items WHERE run_id = ?`
- [ ] History commands show correct items per run
- [ ] Rank order preserved
- [ ] Works when item appears in multiple runs

## Testing

```python
# After fixing, verify:
run_id = state.record_run(items_found, items_new, items_included, output_path, runtime)

with state._get_conn() as conn:
    cursor = conn.execute("SELECT COUNT(*) FROM run_items WHERE run_id = ?", (run_id,))
    count = cursor.fetchone()[0]
    assert count == len(items_included), "All included items should be linked"
```

## Priority

**HIGH** - Breaks run history and item tracking.

## Effort Estimate

1 hour

## Related Issues

#5 Fix Database Constraint Violations

## References

- BUG_REPORT.md #9
- TASK_LIST.md Task 2.4
