---
title: "[CRITICAL] Implement proper logging system"
labels: bug, critical, priority-1
---

## Problem

All components use `print()` statements instead of proper Python logging. This makes debugging impossible and violates best practices.

## Current Behavior

- All output goes to stdout via `print()`
- No log files generated
- No log levels (DEBUG, INFO, WARNING, ERROR)
- No structured logging
- Cannot control verbosity
- No audit trail

## Expected Behavior

- Centralized logging configuration
- Log files written to `~/.research-agent/logs/YYYY-MM-DD.log`
- Proper log levels throughout codebase
- Console output configurable via `--verbose` flag
- Log rotation for old files
- Structured logging with timestamps

## Files Affected

All 30+ `.py` files contain `print()` statements:
- `research_agent/agents/source_agent.py:61`
- `research_agent/agents/synthesis_agent.py:67`
- `research_agent/core/orchestrator.py:87-137`
- And many more...

## Proposed Solution

1. Create `research_agent/utils/logger.py` with centralized config
2. Replace all `print()` with `logger.info()`, `logger.error()`, etc.
3. Configure file handler for `~/.research-agent/logs/`
4. Add console handler respecting `--verbose` flag
5. Implement log rotation (daily or size-based)

## Acceptance Criteria

- [ ] No `print()` statements remain in codebase (except CLI output)
- [ ] All logs written to dated files in logs directory
- [ ] Console output respects `--verbose` flag
- [ ] Log rotation implemented
- [ ] Error messages include stack traces
- [ ] Info messages for major workflow steps

## Priority

**CRITICAL** - Blocks production deployment. Cannot debug issues without proper logging.

## Effort Estimate

3-4 hours

## Related Issues

None

## References

- BUG_REPORT.md #1
- TASK_LIST.md Task 1.1
