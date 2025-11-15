---
title: "[CRITICAL] Check SQLite FTS5 support on initialization"
labels: bug, critical, priority-1, database
---

## Problem

System assumes SQLite compiled with FTS5 support. Will crash on systems where SQLite lacks FTS5 (many Linux distros, older macOS).

## Current Behavior

- Creates FTS5 virtual table without checking support
- Crashes with cryptic error:
  ```
  sqlite3.OperationalError: no such module: fts5
  ```
- May corrupt database if schema partially created

## Expected Behavior

- Check FTS5 support during database initialization
- Fail fast with clear error and installation instructions
- Don't create any tables if FTS5 unavailable

## Files Affected

- `research_agent/storage/state.py:40` - `_init_db()` method
- `research_agent/storage/schema.sql:44` - FTS5 table creation

## Proposed Solution

Add FTS5 capability check in `StateManager._init_db()`:

```python
def _init_db(self):
    """Initialize database schema."""
    # Check FTS5 support first
    with self._get_conn() as conn:
        cursor = conn.execute("PRAGMA compile_options")
        options = [row[0] for row in cursor.fetchall()]

        has_fts5 = any('FTS5' in opt for opt in options)

        if not has_fts5:
            raise RuntimeError(
                "SQLite does not have FTS5 support.\n\n"
                "On macOS: brew install sqlite\n"
                "On Ubuntu: sudo apt-get install sqlite3\n"
                "On Fedora: sudo dnf install sqlite\n\n"
                "Then reinstall Python to use system SQLite:\n"
                "pyenv install --force 3.10.x"
            )

    # Continue with migration
    from research_agent.storage.migrations import run_migrations
    run_migrations(self.db_path)
```

## Acceptance Criteria

- [ ] FTS5 support checked on first database access
- [ ] Clear error message if FTS5 missing
- [ ] Platform-specific installation instructions
- [ ] No database corruption if check fails
- [ ] Error shown before any table creation

## Priority

**CRITICAL** - Will crash on many systems. Silent corruption risk.

## Effort Estimate

1 hour

## Related Issues

None

## References

- BUG_REPORT.md #4
- TASK_LIST.md Task 1.4
- SQLite FTS5 docs: https://www.sqlite.org/fts5.html
