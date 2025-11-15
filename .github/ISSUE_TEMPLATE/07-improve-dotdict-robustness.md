---
title: "[HIGH] Make DotDict config access more robust"
labels: bug, priority-2, configuration
---

## Problem

DotDict raises AttributeError when accessing nested config keys if intermediate keys are missing. For example, `config.sources.arxiv.enabled` crashes if `sources` key is missing from config.

## Current Behavior

```python
config = Config.load()
enabled = config.sources.arxiv.enabled
# AttributeError: No attribute 'sources'
```

- Crashes on malformed configs
- No graceful degradation
- Hard to provide defaults
- Poor error messages

## Expected Behavior

- Graceful handling of missing keys
- Support for default values in nested access
- Clear error for truly required fields
- Option to use `get()` with defaults for optional fields

## Files Affected

- `research_agent/core/config.py:11-30` - DotDict class
- `research_agent/agents/source_agent.py:27-41` - Config access

## Proposed Solutions

**Option 1: Add nested get() method**
```python
class DotDict(dict):
    def nested_get(self, path, default=None):
        """Get nested value with dotted path: 'sources.arxiv.enabled'"""
        keys = path.split('.')
        value = self
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
```

**Option 2: Make __getattr__ return DotDict for missing keys**
```python
class DotDict(dict):
    def __getattr__(self, key):
        try:
            value = self[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError:
            # Return empty DotDict for chaining
            return DotDict()
```

**Option 3: Use Pydantic or dataclasses** (recommended long-term)

## Acceptance Criteria

- [ ] Missing intermediate keys don't crash
- [ ] Can access nested config safely
- [ ] Clear errors for required fields
- [ ] Supports default values
- [ ] Backward compatible with existing code

## Priority

**HIGH** - Causes crashes with invalid configs.

## Effort Estimate

1-2 hours

## Related Issues

#11 Add Configuration Validation

## References

- BUG_REPORT.md #7
- TASK_LIST.md Task 2.2
