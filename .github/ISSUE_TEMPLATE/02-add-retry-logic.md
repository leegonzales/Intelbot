---
title: "[CRITICAL] Add retry logic with exponential backoff"
labels: bug, critical, priority-1, networking
---

## Problem

Despite specification requiring retry logic, all network calls fail immediately on errors. Any network hiccup causes complete research cycle failure.

## Current Behavior

- arXiv API calls fail immediately on network errors
- Hacker News API calls fail immediately
- RSS feed fetches fail immediately
- Claude API calls fail immediately
- No exponential backoff
- Entire run aborts on first failure

## Expected Behavior

- Network failures retry 3 times with exponential backoff (2s, 4s, 8s)
- Claude API failures retry per config `model.api.max_retries`
- Individual source failures don't abort entire run
- Retry attempts logged
- Clear error after max retries exceeded

## Files Affected

- `research_agent/sources/arxiv.py` - arXiv API calls
- `research_agent/sources/hackernews.py` - HN API calls
- `research_agent/sources/rss.py` - RSS feed parsing
- `research_agent/sources/blog_scraper.py` - HTTP requests
- `research_agent/agents/synthesis_agent.py:70` - Claude API

## Proposed Solution

1. Create `research_agent/utils/retry.py` with `@retry` decorator
2. Make retry attempts configurable per source
3. Implement exponential backoff: `delay = base_delay * (2 ** attempt)`
4. Apply decorator to all network calls
5. Log each retry attempt with reason
6. Raise clear exception after max retries

```python
@retry(max_attempts=3, backoff_base=2.0, exceptions=(RequestException,))
def fetch_arxiv_papers():
    # API call here
```

## Acceptance Criteria

- [ ] Retry decorator created and tested
- [ ] Applied to all network operations
- [ ] Configurable retry attempts
- [ ] Exponential backoff implemented (2s, 4s, 8s default)
- [ ] All retry attempts logged
- [ ] Source failures don't abort entire run
- [ ] Clear error message after max retries

## Priority

**CRITICAL** - System will fail frequently in production without retry logic.

## Effort Estimate

2-3 hours

## Related Issues

#13 Add Rate Limiting

## References

- BUG_REPORT.md #2
- TASK_LIST.md Task 1.2
- Specification: "Retry on failure" in schedule.retry config
