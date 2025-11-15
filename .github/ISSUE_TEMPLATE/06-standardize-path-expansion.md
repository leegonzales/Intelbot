---
title: "[HIGH] Standardize path expansion across all config paths"
labels: bug, priority-2, configuration
---

## Problem

Path expansion using `.expanduser()` is inconsistent - some places expand paths, others don't. This causes "file not found" errors on some systems.

## Current Behavior

- Some files expand paths: `orchestrator.py:37-38`, `digest_writer.py:23`, `cli.py:85`
- Others use paths directly from config
- Config loader doesn't expand paths
- Inconsistent behavior depending on code path

## Expected Behavior

- All paths with `~` expanded consistently
- Expansion happens once in config loader
- All code uses pre-expanded paths
- No scattered `.expanduser()` calls

## Files Affected

- `research_agent/core/config.py` - Config loader
- `research_agent/core/orchestrator.py:37-38`
- `research_agent/output/digest_writer.py:23`
- `research_agent/cli/main.py:85`

## Proposed Solution

Expand all paths in the config loader:

```python
@classmethod
def load(cls, config_path: Path = None) -> 'Config':
    # ... load config_data ...

    # Expand all paths
    paths = config_data.get('paths', {})
    for key in paths:
        if isinstance(paths[key], str):
            paths[key] = str(Path(paths[key]).expanduser())

    return cls(
        paths=DotDict(paths),
        # ...
    )
```

Remove all `.expanduser()` calls from other files since paths are already expanded.

## Acceptance Criteria

- [ ] All paths in config expanded during load
- [ ] No `.expanduser()` calls in business logic
- [ ] Works with `~` in all config path fields
- [ ] Works across different user home directories
- [ ] No "file not found" errors from unexpanded paths

## Priority

**HIGH** - Causes failures on some systems.

## Effort Estimate

1 hour

## Related Issues

#11 Add Configuration Validation

## References

- BUG_REPORT.md #6
- TASK_LIST.md Task 2.1
