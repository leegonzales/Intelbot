# Issue #1: Implement Logging System

**Priority**: 🔴 Critical (P1)
**Status**: Open
**Assignee**: Unassigned
**Estimate**: 3-4 hours
**Created**: 2024-11-15
**Updated**: 2024-11-15

---

## Summary

All components use `print()` statements instead of proper Python logging, making debugging impossible.

## Details

See [Issue Template](../../../../.github/ISSUE_TEMPLATE/01-implement-logging-system.md) for full details.

## Acceptance Criteria

- [ ] No `print()` statements remain in codebase
- [ ] All logs written to `~/.research-agent/logs/YYYY-MM-DD.log`
- [ ] Console output respects `--verbose` flag
- [ ] Log rotation implemented
- [ ] Error messages include stack traces

## Test Requirements

**Unit Tests**:
- [ ] `tests/unit/test_logger.py` - Test log configuration
- [ ] Test log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Test file logging
- [ ] Test console logging
- [ ] Test log rotation

**Integration Tests**:
- [ ] Verify all components use logger
- [ ] Test verbose flag in CLI
- [ ] Verify log files created

## Implementation Notes

```python
# research_agent/utils/logger.py
import logging
from pathlib import Path

def setup_logger(name, log_dir, verbose=False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # File handler
    log_file = Path(log_dir) / f"{datetime.now():%Y-%m-%d}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

## Dependencies

None

## Blocks

- All other issues (need logging to debug)

## References

- [BUG_REPORT.md](../../../../BUG_REPORT.md) #1
- [TASK_LIST.md](../../../../TASK_LIST.md) Task 1.1
- [GitHub Issue Template](../../../../.github/ISSUE_TEMPLATE/01-implement-logging-system.md)
