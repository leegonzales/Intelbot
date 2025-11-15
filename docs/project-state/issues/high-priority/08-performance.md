# Issue #8: Optimize filter_new() Performance

**Priority**: 🟡 High (P2)
**Status**: Open
**Assignee**: Unassigned
**Estimate**: 2 hours
**Created**: 2024-11-15
**Updated**: 2024-11-15

---

## Summary

`StateManager.filter_new()` opens a new database connection for each item, causing O(n) connections and poor performance with 100+ items.

## Details

See [Issue Template](../../../../.github/ISSUE_TEMPLATE/08-optimize-filter-new-performance.md) for full details.

## Acceptance Criteria

- [ ] Single database connection for batch check
- [ ] O(1) database connections regardless of item count
- [ ] Handles 100+ items in <1 second
- [ ] Maintains same deduplication accuracy
- [ ] Works with URL and content hash deduplication

## Test Requirements

**Performance Tests**:
- [ ] `tests/performance/test_filter_new_scalability.py`
  - [ ] Benchmark with 10 items
  - [ ] Benchmark with 100 items
  - [ ] Benchmark with 1000 items
  - [ ] Verify O(1) DB connections
  - [ ] Compare before/after performance

**Unit Tests**:
- [ ] `tests/unit/test_state.py::test_batch_duplicate_check`
  - [ ] Test batch URL checking
  - [ ] Test batch hash checking
  - [ ] Test correctness maintained
  - [ ] Test empty list
  - [ ] Test all duplicates
  - [ ] Test mixed new/duplicate

## Implementation Notes

Use SQL IN clause for batch checking:

```python
# Batch URL check
urls = [item['url'] for item in items]
placeholders = ','.join('?' * len(urls))
cursor = conn.execute(
    f"SELECT url FROM seen_items WHERE url IN ({placeholders})",
    urls
)
existing_urls = {row['url'] for row in cursor}
```

## Performance Targets

| Items | Current | Target | Improvement |
|-------|---------|--------|-------------|
| 10 | ~100ms | <50ms | 2x |
| 100 | ~1000ms | <100ms | 10x |
| 1000 | ~10s | <500ms | 20x |

## Dependencies

None

## Blocks

Production deployment (performance bottleneck)

## References

- [BUG_REPORT.md](../../../../BUG_REPORT.md) #8
- [TASK_LIST.md](../../../../TASK_LIST.md) Task 2.3
- [Test Plan](../../tests/TESTING.md#8---filter_new-performance)
