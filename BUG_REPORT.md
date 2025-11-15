# Research Agent System - Bug Report & Validation Task List

## Critical Issues

### 1. **Missing Logging System**
- **Location**: Entire codebase
- **Issue**: All components use `print()` instead of proper logging
- **Impact**: No log levels, no file logging, no structured logging
- **Files affected**: All `.py` files
- **Task**: Implement Python `logging` module throughout

### 2. **No Retry Logic**
- **Location**: Sources, SynthesisAgent, API calls
- **Issue**: Specification requires retry logic but none implemented
- **Impact**: Network failures will cause complete run failures
- **Files affected**:
  - `research_agent/sources/arxiv.py`
  - `research_agent/sources/hackernews.py`
  - `research_agent/sources/rss.py`
  - `research_agent/agents/synthesis_agent.py`
- **Task**: Add retry decorator with exponential backoff

### 3. **API Key Validation Missing**
- **Location**: `research_agent/agents/synthesis_agent.py:17`
- **Issue**: Creates Anthropic client without checking if ANTHROPIC_API_KEY is set
- **Impact**: Will fail at runtime with cryptic error
- **Task**: Add validation in `__init__()` or CLI run command

### 4. **SQLite FTS5 Availability Not Checked**
- **Location**: `research_agent/storage/state.py:40`
- **Issue**: Assumes SQLite compiled with FTS5 support
- **Impact**: Will crash on systems without FTS5
- **Task**: Add FTS5 capability check in `_init_db()`

### 5. **Database Constraint Violation**
- **Location**: `research_agent/storage/state.py:240`
- **Issue**: `add_item()` called for items that may already exist (duplicate URLs)
- **Impact**: Will raise UNIQUE constraint violation
- **Task**: Use INSERT OR IGNORE or check before insert

## High Priority Bugs

### 6. **Path Expansion Inconsistent**
- **Location**: Multiple files
- **Issue**: Some paths use `.expanduser()`, others don't
- **Files affected**:
  - `research_agent/core/orchestrator.py:37-38`
  - `research_agent/output/digest_writer.py:23`
  - `research_agent/cli/main.py:85`
- **Task**: Ensure all config paths are expanded consistently

### 7. **DotDict Nested Access Fragile**
- **Location**: `research_agent/core/config.py:14-21`
- **Issue**: Accessing `config.sources.arxiv.enabled` will fail if `sources` key missing
- **Impact**: AttributeError on malformed configs
- **Task**: Add proper nested defaulting or validation

### 8. **Filter_new() O(n*m) Complexity**
- **Location**: `research_agent/storage/state.py:179-201`
- **Issue**: Opens new DB connection for each item check
- **Impact**: Very slow for large item lists (100+ items)
- **Task**: Batch duplicate checking with single query

### 9. **record_run() Item Comparison Bug**
- **Location**: `research_agent/storage/state.py:243`
- **Issue**: Uses `item in items_included` which compares dict objects by reference
- **Impact**: Items won't be linked to runs properly
- **Task**: Compare by URL or use item IDs

### 10. **BM25 Score Normalization Incorrect**
- **Location**: `research_agent/storage/state.py:137`
- **Issue**: Normalization `1 / (1 + abs(score))` doesn't map BM25 properly to 0-1
- **Impact**: Similarity threshold of 0.85 may never trigger
- **Task**: Research proper BM25 score ranges and normalize correctly

## Medium Priority Issues

### 11. **No Config Validation**
- **Location**: `research_agent/core/config.py:77-87`
- **Issue**: No validation of required fields or types
- **Impact**: Runtime errors with bad configs
- **Task**: Add pydantic or manual validation

### 12. **Hardcoded Similarity Threshold**
- **Location**: `research_agent/storage/state.py:77`
- **Issue**: Threshold hardcoded to 0.85, should use config
- **Impact**: Can't tune deduplication sensitivity
- **Task**: Pass threshold from config

### 13. **Missing Rate Limiting**
- **Location**: All source collectors
- **Issue**: No rate limiting for API calls
- **Impact**: May get blocked by arXiv, HN, etc.
- **Task**: Implement rate limiter or delays

### 14. **Unsafe Shell Command**
- **Location**: `research_agent/cli/main.py:86`
- **Issue**: Uses `os.system()` for editor
- **Impact**: Shell injection risk
- **Task**: Use `subprocess.run()` with proper escaping

### 15. **Empty Prompts Not Handled**
- **Location**: `research_agent/core/prompts.py:55`
- **Issue**: Returns empty string if prompt file missing
- **Impact**: Will synthesize with empty system prompt
- **Task**: Raise error or use hardcoded fallback

### 16. **Network Timeout Too Short**
- **Location**: `research_agent/sources/hackernews.py:46`
- **Issue**: 10 second timeout may be too short
- **Impact**: Frequent timeouts on slow connections
- **Task**: Make configurable or increase to 30s

### 17. **Thread Pool No Timeout**
- **Location**: `research_agent/agents/source_agent.py:47`
- **Issue**: `as_completed()` has no timeout
- **Impact**: Can hang indefinitely
- **Task**: Add timeout parameter

### 18. **Blog Scraper Too Generic**
- **Location**: `research_agent/sources/blog_scraper.py:48-107`
- **Issue**: Generic selectors won't work on most blogs
- **Impact**: Will return empty results for most blogs
- **Task**: Add blog-specific parsers or use RSS

### 19. **DateTime Parsing Unchecked**
- **Location**: `research_agent/sources/blog_scraper.py:125`
- **Issue**: Uses `dateutil.parser` without try/except
- **Impact**: Will fail on malformed dates
- **Task**: Already has try/except but returns None - should log warning

### 20. **Missing Dependency**
- **Location**: `research_agent/sources/blog_scraper.py:125`
- **Issue**: Imports `from dateutil import parser` but package is `python-dateutil`
- **Impact**: Import error if not installed
- **Status**: Actually added to pyproject.toml:20
- **Task**: Verify import works

## Low Priority / Enhancements

### 21. **No Type Hints Consistency**
- **Location**: Various
- **Issue**: Some functions have type hints, others don't
- **Task**: Add complete type hints and run mypy

### 22. **Print Statements in Libraries**
- **Location**: All source collectors, agents
- **Issue**: Library code should not print to stdout
- **Task**: Replace with logging after #1 is fixed

### 23. **Error Messages to Stdout**
- **Location**: `research_agent/agents/source_agent.py:61`
- **Issue**: Errors printed instead of logged
- **Task**: Use proper logging

### 24. **No Integration Tests**
- **Location**: `tests/`
- **Issue**: Only unit tests for StateManager
- **Task**: Add integration tests for full workflow

### 25. **Install Script Assumptions**
- **Location**: `scripts/install.sh:11`
- **Issue**: Assumes `python3` and `pip` exist
- **Task**: Add checks for Python/pip

### 26. **Fallback Synthesis Poor Quality**
- **Location**: `research_agent/agents/synthesis_agent.py:103-132`
- **Issue**: Fallback doesn't follow template
- **Task**: Improve fallback or fail fast

### 27. **No Database Locking Handling**
- **Location**: `research_agent/storage/state.py`
- **Issue**: No handling of SQLite BUSY/LOCKED states
- **Task**: Add timeout and busy handler

### 28. **Migration System No Rollback**
- **Location**: `research_agent/storage/migrations/__init__.py`
- **Issue**: Only implements `up()`, no `down()` functionality
- **Task**: Implement rollback capability

### 29. **Schema File Relative Path**
- **Location**: `research_agent/storage/migrations/001_initial.py:11`
- **Issue**: Uses `Path(__file__).parent.parent / "schema.sql"`
- **Impact**: May fail if run from different working directory
- **Task**: Test or use absolute path construction

### 30. **No Obsidian Vault Validation**
- **Location**: `research_agent/output/digest_writer.py:33`
- **Issue**: Doesn't check if output directory is writable
- **Task**: Add validation before write

### 31. **Scoring Weights Hardcoded**
- **Location**: `research_agent/utils/scoring.py:31-49`
- **Issue**: All scoring weights and keywords hardcoded
- **Task**: Move to configuration

### 32. **No Progress Indicators**
- **Location**: CLI
- **Issue**: Long-running operations have no progress feedback
- **Task**: Add progress bars or status updates

### 33. **ArxivSource Date Filter**
- **Location**: `research_agent/sources/arxiv.py:57`
- **Issue**: Hardcoded 7-day lookback
- **Task**: Use config `lookback_hours`

### 34. **RSS Feed Error Handling**
- **Location**: `research_agent/sources/rss.py:39`
- **Issue**: Broad exception catching with just print
- **Task**: Specific exception handling and logging

### 35. **Digest Writer Doesn't Validate Content**
- **Location**: `research_agent/output/digest_writer.py:26`
- **Issue**: Writes any string, doesn't check if valid markdown
- **Task**: Add basic validation

## Platform-Specific Issues

### 36. **macOS-Only Scheduler**
- **Location**: `research_agent/scheduler/launchd.py`
- **Issue**: Only works on macOS
- **Impact**: Won't work on Linux/Windows
- **Task**: Add cron (Linux) and Task Scheduler (Windows) support

### 37. **Launchd Path Assumptions**
- **Location**: `research_agent/scheduler/launchd.py:71`
- **Issue**: Assumes `~/Library/LaunchAgents` exists
- **Task**: Create directory if missing

## Security Issues

### 38. **No Input Sanitization**
- **Location**: `research_agent/storage/state.py` (SQL queries)
- **Issue**: While using parameterized queries (good), no validation of input data
- **Impact**: Large inputs could cause issues
- **Task**: Add input validation and size limits

### 39. **User-Agent String**
- **Location**: `research_agent/sources/blog_scraper.py:30`
- **Issue**: Custom user-agent but no contact info
- **Task**: Add valid email to user-agent per RFC

## Testing Gaps

### 40. **No Tests for:**
- Source collectors (arXiv, HN, RSS, blogs)
- SynthesisAgent
- ResearchOrchestrator
- CLI commands
- Configuration loading
- Digest writing
- Scheduler integration
- **Task**: Add comprehensive test coverage

### 41. **Test Database Cleanup**
- **Location**: `tests/test_state.py`
- **Issue**: Uses `tmp_path` but doesn't explicitly clean up
- **Impact**: Relies on pytest cleanup
- **Task**: Add explicit cleanup or verify pytest handles it

## Documentation Issues

### 42. **Missing Docstrings**
- **Location**: Various utility functions
- **Issue**: Not all functions have docstrings
- **Task**: Add complete docstrings

### 43. **README Installation Steps Untested**
- **Location**: `README.md`
- **Issue**: Installation instructions not verified
- **Task**: Test installation on clean system

### 44. **No Troubleshooting for Common Errors**
- **Location**: `README.md`
- **Issue**: Generic troubleshooting, no specific error codes
- **Task**: Add common error messages and solutions

## Performance Issues

### 45. **FTS Query Inefficient**
- **Location**: `research_agent/storage/state.py:119-130`
- **Issue**: Creates FTS query with OR for all terms
- **Impact**: Slow with long titles
- **Task**: Use more efficient FTS query syntax

### 46. **No Caching**
- **Location**: Source collectors
- **Issue**: No caching of API responses
- **Impact**: Repeated runs fetch same data
- **Task**: Add optional caching layer

### 47. **Prompt Cache Never Invalidates**
- **Location**: `research_agent/core/prompts.py:31`
- **Issue**: Prompts cached forever, no reload
- **Impact**: Need to restart to pick up prompt changes
- **Task**: Add cache invalidation or TTL

## Summary Statistics

- **Critical Issues**: 5
- **High Priority Bugs**: 5
- **Medium Priority Issues**: 15
- **Low Priority/Enhancements**: 14
- **Platform-Specific**: 2
- **Security Issues**: 2
- **Testing Gaps**: 2
- **Documentation Issues**: 3
- **Performance Issues**: 3

**Total Issues**: 51

## Recommended Fix Priority

1. Fix Critical Issues #1-5 first (logging, retries, API validation, FTS5 check, DB constraints)
2. Fix High Priority Bugs #6-10 (paths, config access, performance, item linking, BM25)
3. Add comprehensive error handling and logging
4. Implement config validation
5. Add integration tests
6. Address security issues
7. Performance optimizations
8. Platform-specific enhancements

## Testing Checklist Before Production

- [ ] Test with empty database
- [ ] Test with missing config file
- [ ] Test with invalid API key
- [ ] Test with no internet connection
- [ ] Test with malformed RSS feeds
- [ ] Test with blog scraper on real blogs
- [ ] Test FTS5 availability check
- [ ] Test on system without FTS5
- [ ] Test launchd installation/uninstallation
- [ ] Test with output directory not writable
- [ ] Test with > 100 items
- [ ] Test duplicate detection accuracy
- [ ] Test Claude API rate limiting
- [ ] Test concurrent runs (database locking)
- [ ] Test migration system
- [ ] Verify all dependencies install correctly
