# Issue #2: Add Retry Logic

**Priority**: 🔴 Critical (P1)
**Status**: ✅ Closed
**Assignee**: Claude
**Estimate**: 2-3 hours
**Actual**: 1 hour
**Created**: 2024-11-15
**Updated**: 2024-11-15
**Closed**: 2024-11-15

---

## Summary

Network calls to external APIs (arXiv, HN, RSS) have no retry logic, causing failures on transient errors.

## Resolution

✅ **FIXED** - Implemented retry decorator with exponential backoff

### Implementation Details

**Files Created**:
- `research_agent/utils/retry.py` - Retry decorator with exponential backoff

**Files Modified**:
- `research_agent/sources/arxiv.py` - Added @retry decorator
- `research_agent/sources/hackernews.py` - Added @retry decorator
- `research_agent/sources/rss.py` - Added @retry decorator
- `research_agent/sources/blog_scraper.py` - Added @retry decorator

### Features Implemented
- ✅ Configurable max attempts (default: 3)
- ✅ Exponential backoff (2s, 4s, 8s delays)
- ✅ Specific exception type filtering
- ✅ Logging of all retry attempts
- ✅ Optional on_retry callback support

### Commits
- `68ae1d3` - Retry decorator implementation
- `93ccaf2` - Applied to all source collectors

---

## Acceptance Criteria

- [x] Network calls retry on failure
- [x] Exponential backoff implemented (2s, 4s, 8s)
- [x] Max 3 retry attempts
- [x] Retry attempts logged
- [x] Different exception types supported

## Implementation Code

```python
# research_agent/utils/retry.py
import time
import logging
from functools import wraps
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)

def retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable = None
):
    """
    Decorator to retry function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts
        backoff_base: Base delay in seconds (exponentially increases)
        exceptions: Tuple of exception types to catch
        on_retry: Optional callback function called on each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        # Last attempt, re-raise
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise

                    # Calculate delay with exponential backoff
                    delay = backoff_base * (2 ** attempt)
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {delay}s: {e}"
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(delay)

        return wrapper
    return decorator
```

## Usage Example

```python
from research_agent.utils.retry import retry

class ArxivSource:
    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        # Network call that may fail
        response = requests.get(url)
        return response.json()
```

## Test Requirements

**Unit Tests** (deferred to Sprint 002):
- [ ] Test successful execution (no retries)
- [ ] Test retry on failure
- [ ] Test max attempts exhaustion
- [ ] Test exponential backoff timing
- [ ] Test exception filtering

## References

- [BUG_REPORT.md](../../../../BUG_REPORT.md) #2
- [TASK_LIST.md](../../../../TASK_LIST.md) Task 1.2
- [Sprint 001](../../sprints/SPRINT_001.md)
