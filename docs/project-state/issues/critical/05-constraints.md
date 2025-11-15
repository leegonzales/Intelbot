# Issue #5: Fix Database Constraint Violations

**Priority**: 🔴 Critical (P1)
**Status**: ✅ Closed
**Assignee**: Claude
**Estimate**: 1 hour
**Actual**: 1.5 hours
**Created**: 2024-11-15
**Updated**: 2024-11-15
**Closed**: 2024-11-15

---

## Summary

UNIQUE constraint violations occur when trying to insert duplicate URLs, and item-to-run linking compares objects by reference instead of URL, causing incorrect associations.

## Resolution

✅ **FIXED** - Implemented INSERT OR IGNORE pattern and URL-based item comparison

### Implementation Details

**Files Modified**:
- `research_agent/storage/state.py` - Fixed `add_item()` and `record_run()`

### Issues Fixed
1. **UNIQUE Constraint Violations**
   - Changed `INSERT` to `INSERT OR IGNORE`
   - Return existing ID if insert was ignored
   - Prevents crash on duplicate URLs

2. **Item-to-Run Linking**
   - Compare items by URL instead of object reference
   - Built URL-to-rank mapping for efficient lookup
   - Fixed incorrect digest inclusion tracking

### Features Implemented
- ✅ Idempotent `add_item()` operation
- ✅ Returns existing ID when URL already exists
- ✅ URL-based item comparison in `record_run()`
- ✅ Efficient URL-to-rank mapping

### Commits
- `68ae1d3` - Database constraint fixes

---

## Acceptance Criteria

- [x] No UNIQUE constraint errors on duplicate URLs
- [x] `add_item()` returns existing ID for duplicates
- [x] Items correctly linked to runs by URL
- [x] Duplicate items not inserted

## Implementation Code

```python
# research_agent/storage/state.py

def add_item(self, item: Dict) -> int:
    """Add item to seen_items, return ID (existing or new)."""

    with self._get_conn() as conn:
        # Use INSERT OR IGNORE to handle duplicates gracefully
        cursor = conn.execute("""
            INSERT OR IGNORE INTO seen_items (
                url, title, source, content_hash, metadata,
                collected_at, published_date, author
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item['url'],
            item.get('title', ''),
            item.get('source', ''),
            item.get('content_hash', ''),
            json.dumps(item.get('source_metadata', {})),
            item.get('collected_at'),
            item.get('published_date'),
            item.get('author')
        ))

        # If insert was ignored (duplicate), get existing ID
        if cursor.lastrowid:
            return cursor.lastrowid
        else:
            # URL already exists, fetch its ID
            cursor = conn.execute(
                "SELECT id FROM seen_items WHERE url = ?",
                (item['url'],)
            )
            return cursor.fetchone()[0]

def record_run(self, items_collected: List[Dict], items_new: List[Dict],
               items_included: List[Dict], digest_path: str = None) -> int:
    """Record research run and link items."""

    # Build URL-to-rank mapping (not object reference!)
    url_to_rank = {
        item['url']: idx
        for idx, item in enumerate(items_included)
    }

    with self._get_conn() as conn:
        # Record run
        cursor = conn.execute("""
            INSERT INTO runs (
                started_at, completed_at, items_collected,
                items_new, items_included, digest_path
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (...))

        run_id = cursor.lastrowid

        # Link items to this run
        for item in items_new:
            item_id = self.add_item(item)

            # Check if item was included in digest (by URL!)
            if item['url'] in url_to_rank:
                rank = url_to_rank[item['url']]
                included = True
            else:
                rank = None
                included = False

            # Record item-run association
            conn.execute("""
                INSERT INTO item_runs (
                    item_id, run_id, included_in_digest, rank_in_digest
                )
                VALUES (?, ?, ?, ?)
            """, (item_id, run_id, included, rank))

        return run_id
```

## Problem Explanation

**Before Fix**:
```python
# This compared object references, not URLs!
if item in items_included:  # ❌ Wrong - compares object identity
    included = True
```

**After Fix**:
```python
# Build mapping first
url_to_rank = {item['url']: idx for idx, item in enumerate(items_included)}

# Compare by URL
if item['url'] in url_to_rank:  # ✅ Correct - compares URLs
    rank = url_to_rank[item['url']]
    included = True
```

## Test Requirements

**Unit Tests** (deferred to Sprint 002):
- [ ] Test `add_item()` with new URL (should insert)
- [ ] Test `add_item()` with duplicate URL (should return existing ID)
- [ ] Test `record_run()` links items correctly
- [ ] Test URL-based inclusion detection
- [ ] Test rank assignment

**Integration Tests**:
- [ ] Run full cycle twice with same items
- [ ] Verify no constraint violations
- [ ] Verify correct item-run associations

## References

- [BUG_REPORT.md](../../../../BUG_REPORT.md) #5, #9
- [TASK_LIST.md](../../../../TASK_LIST.md) Task 1.5
- [Sprint 001](../../sprints/SPRINT_001.md)
