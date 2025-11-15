# Research Agent System - Prioritized Fix Task List

## Phase 1: Critical Fixes (Must Fix Before Testing)

### Task 1.1: Implement Logging System
**Priority**: CRITICAL
**Effort**: Medium (3-4 hours)
**Files to modify**:
- Create `research_agent/utils/logger.py`
- Update all 30 `.py` files to use logging

**Steps**:
1. Create centralized logging configuration
2. Add log levels: DEBUG, INFO, WARNING, ERROR
3. Configure file logging to `~/.research-agent/logs/`
4. Replace all `print()` statements with `logger.info()`, `logger.error()`, etc.
5. Add log rotation

**Acceptance Criteria**:
- All output goes through logging system
- Logs written to dated files
- Console output configurable via `--verbose` flag
- No more bare `print()` statements

---

### Task 1.2: Add Retry Logic with Exponential Backoff
**Priority**: CRITICAL
**Effort**: Medium (2-3 hours)
**Files to modify**:
- Create `research_agent/utils/retry.py`
- `research_agent/sources/arxiv.py`
- `research_agent/sources/hackernews.py`
- `research_agent/sources/rss.py`
- `research_agent/agents/synthesis_agent.py`

**Steps**:
1. Create `@retry` decorator with exponential backoff
2. Make retry attempts configurable
3. Apply to all network calls and Claude API
4. Add proper exception handling
5. Log retry attempts

**Acceptance Criteria**:
- Network failures retry 3 times with 2s, 4s, 8s delays
- Claude API failures retry per config
- All retries logged
- Final failure raises clear exception

---

### Task 1.3: Validate API Keys on Startup
**Priority**: CRITICAL
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/agents/synthesis_agent.py`
- `research_agent/cli/main.py`

**Steps**:
1. Check ANTHROPIC_API_KEY exists before creating client
2. Optionally validate key format
3. Provide clear error message if missing
4. Add check to CLI `run` command

**Acceptance Criteria**:
- Clear error if API key not set
- Error shown before any processing
- Suggests adding key to `.env`

---

### Task 1.4: Check SQLite FTS5 Support
**Priority**: CRITICAL
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/storage/state.py`

**Steps**:
1. Add FTS5 capability check in `_init_db()`
2. Query `PRAGMA compile_options` for FTS5
3. Provide clear error if not available
4. Suggest installing sqlite3 with FTS5

**Acceptance Criteria**:
- Fails fast with clear error if no FTS5
- Error message includes installation instructions
- Doesn't corrupt database

---

### Task 1.5: Fix Database Constraint Violations
**Priority**: CRITICAL
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/storage/state.py:240`

**Steps**:
1. Change `add_item()` to use `INSERT OR IGNORE`
2. Or check for existing URL before insert
3. Return existing item ID if duplicate
4. Fix `record_run()` item comparison logic

**Acceptance Criteria**:
- No UNIQUE constraint violations
- Items properly linked to runs
- Deduplication works correctly

---

## Phase 2: High Priority Bugs (Fix Before Production)

### Task 2.1: Standardize Path Expansion
**Priority**: HIGH
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/core/config.py`
- All files using paths from config

**Steps**:
1. Expand all paths in config loader
2. Store expanded paths
3. Remove scattered `.expanduser()` calls
4. Validate paths exist where required

**Acceptance Criteria**:
- All `~` in config paths expanded
- No runtime path errors
- Works across different home directories

---

### Task 2.2: Improve DotDict Robustness
**Priority**: HIGH
**Effort**: Small (1-2 hours)
**Files to modify**:
- `research_agent/core/config.py:11-30`

**Steps**:
1. Add nested `get()` support with defaults
2. Handle missing intermediate keys gracefully
3. Add `__contains__` for `in` operator
4. Consider replacing with proper dataclass or pydantic

**Acceptance Criteria**:
- `config.sources.arxiv.enabled` doesn't crash if `sources` missing
- Returns sensible defaults
- Clear errors for truly required fields

---

### Task 2.3: Optimize filter_new() Performance
**Priority**: HIGH
**Effort**: Medium (2 hours)
**Files to modify**:
- `research_agent/storage/state.py:179-201`

**Steps**:
1. Create batch duplicate checking method
2. Use single query: `SELECT url FROM seen_items WHERE url IN (?)`
3. Check content hashes in batch
4. Reduce DB connections from N to 1-2

**Acceptance Criteria**:
- Handles 100+ items efficiently
- Single-digit DB connections per filter_new() call
- Maintains same deduplication accuracy

---

### Task 2.4: Fix Item-to-Run Linking
**Priority**: HIGH
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/storage/state.py:243`

**Steps**:
1. Compare items by URL instead of object reference
2. Or build item_id mapping during add_item()
3. Ensure correct items linked to runs
4. Add test to verify linking

**Acceptance Criteria**:
- Items correctly appear in run_items table
- Can query items by run_id
- History commands show correct items

---

### Task 2.5: Fix BM25 Score Normalization
**Priority**: HIGH
**Effort**: Medium (2-3 hours)
**Files to modify**:
- `research_agent/storage/state.py:137`

**Steps**:
1. Research actual BM25 score ranges
2. Test with real data
3. Adjust normalization formula
4. Make threshold configurable
5. Document expected score ranges

**Acceptance Criteria**:
- Title similarity detection works
- Threshold of 0.85 triggers on similar titles
- Documented score interpretation

---

## Phase 3: Config & Validation (Production Hardening)

### Task 3.1: Add Configuration Validation
**Priority**: MEDIUM
**Effort**: Medium (3 hours)
**Files to modify**:
- Create `research_agent/core/validation.py`
- `research_agent/core/config.py`

**Steps**:
1. Define required vs optional config fields
2. Add type checking
3. Validate paths exist
4. Check numeric ranges
5. Provide clear validation errors

**Acceptance Criteria**:
- Invalid configs rejected at load time
- Clear error messages
- Suggests fixes for common issues

---

### Task 3.2: Make Thresholds Configurable
**Priority**: MEDIUM
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/storage/state.py:77`
- `config.yaml.example`

**Steps**:
1. Add `research.dedup.title_similarity` to config
2. Pass from config to `is_duplicate()`
3. Document threshold tuning
4. Add sensible defaults

---

### Task 3.3: Add Rate Limiting
**Priority**: MEDIUM
**Effort**: Medium (2-3 hours)
**Files to modify**:
- Create `research_agent/utils/rate_limiter.py`
- All source collectors

**Steps**:
1. Implement rate limiter class
2. Add delays between requests
3. Make delays configurable per source
4. Log rate limit events

**Acceptance Criteria**:
- Respects arXiv rate limits (1 req/3s)
- Configurable delays
- Doesn't slow down unnecessarily

---

### Task 3.4: Secure Shell Command Execution
**Priority**: MEDIUM
**Effort**: Small (30 min)
**Files to modify**:
- `research_agent/cli/main.py:86`

**Steps**:
1. Replace `os.system()` with `subprocess.run()`
2. Use list-based arguments
3. Validate editor path

**Acceptance Criteria**:
- No shell injection risk
- Works with editors containing spaces
- Proper error handling

---

## Phase 4: Error Handling & Robustness

### Task 4.1: Improve Prompt Error Handling
**Priority**: MEDIUM
**Effort**: Small (1 hour)
**Files to modify**:
- `research_agent/core/prompts.py`

**Steps**:
1. Raise error if critical prompts missing
2. Add fallback system prompt
3. Validate prompt content (not empty)
4. Log prompt loading

---

### Task 4.2: Configure Network Timeouts
**Priority**: MEDIUM
**Effort**: Small (1 hour)
**Files to modify**:
- All source collectors
- Add to config

**Steps**:
1. Add timeout config per source
2. Use reasonable defaults (30s)
3. Make configurable
4. Document timeout tuning

---

### Task 4.3: Add ThreadPool Timeout
**Priority**: MEDIUM
**Effort**: Small (30 min)
**Files to modify**:
- `research_agent/agents/source_agent.py:47`

**Steps**:
1. Add timeout to `as_completed()`
2. Handle TimeoutError
3. Log which sources timed out
4. Continue with completed sources

---

### Task 4.4: Enhance Blog Scraper
**Priority**: LOW
**Effort**: Large (6+ hours)
**Files to modify**:
- `research_agent/sources/blog_scraper.py`

**Steps**:
1. Add blog-specific parsers
2. Or recommend using RSS instead
3. Add better error recovery
4. Document limitations

**Recommendation**: Disable blog scraper and use RSS feeds instead

---

## Phase 5: Testing & Quality

### Task 5.1: Add Integration Tests
**Priority**: HIGH (before production)
**Effort**: Large (8+ hours)
**Files to create**:
- `tests/test_integration.py`
- `tests/test_sources.py`
- `tests/test_orchestrator.py`
- `tests/test_cli.py`

**Steps**:
1. Test full workflow end-to-end
2. Test each source collector
3. Mock external APIs
4. Test error conditions
5. Test config variations

---

### Task 5.2: Add Type Hints
**Priority**: LOW
**Effort**: Medium (4 hours)
**Files to modify**: All Python files

**Steps**:
1. Add complete type hints
2. Configure mypy
3. Fix type errors
4. Add to CI/CD

---

### Task 5.3: Verify Installation
**Priority**: HIGH
**Effort**: Small (2 hours)
**Steps**:
1. Test installation on clean macOS
2. Test installation on Linux
3. Document platform-specific issues
4. Update install script

---

## Phase 6: Enhancements

### Task 6.1: Add Progress Indicators
**Priority**: LOW
**Effort**: Medium (2-3 hours)
**Steps**:
1. Add progress bars for long operations
2. Show source collection progress
3. Show synthesis progress
4. Use rich or tqdm library

---

### Task 6.2: Database Performance
**Priority**: LOW
**Effort**: Medium (2-3 hours)
**Steps**:
1. Add SQLite busy handler
2. Add connection pooling
3. Optimize FTS queries
4. Add database VACUUM schedule

---

### Task 6.3: Add Caching
**Priority**: LOW
**Effort**: Medium (3-4 hours)
**Steps**:
1. Cache API responses
2. Add TTL configuration
3. Cache invalidation strategy
4. Make optional

---

### Task 6.4: Cross-Platform Scheduling
**Priority**: MEDIUM
**Effort**: Large (6+ hours)
**Steps**:
1. Add cron support (Linux)
2. Add Task Scheduler support (Windows)
3. Abstract scheduler interface
4. Test on each platform

---

## Phase 7: Documentation

### Task 7.1: Add Comprehensive Docstrings
**Priority**: LOW
**Effort**: Medium (3-4 hours)
**Steps**:
1. Add Google-style docstrings
2. Document all parameters
3. Document return values
4. Add examples

---

### Task 7.2: Improve README
**Priority**: MEDIUM
**Effort**: Small (1-2 hours)
**Steps**:
1. Add common error codes
2. Expand troubleshooting
3. Add FAQ section
4. Add screenshots

---

## Summary

### Must Fix (Critical Path):
1. Logging system
2. Retry logic
3. API key validation
4. FTS5 check
5. Database constraints
6. Path expansion
7. DotDict robustness
8. filter_new() performance
9. Item linking
10. BM25 normalization

### Recommended Before Production:
11. Config validation
12. Rate limiting
13. Integration tests
14. Installation verification

### Nice to Have:
15. Progress indicators
16. Cross-platform scheduling
17. Type hints
18. Comprehensive docs

## Estimated Total Effort

- **Phase 1 (Critical)**: 10-12 hours
- **Phase 2 (High Priority)**: 6-8 hours
- **Phase 3 (Validation)**: 6-8 hours
- **Phase 4 (Error Handling)**: 4-6 hours
- **Phase 5 (Testing)**: 12-16 hours
- **Phase 6 (Enhancements)**: 15-20 hours
- **Phase 7 (Documentation)**: 4-6 hours

**Total**: 57-76 hours (1.5-2 weeks full-time)

**Minimum Viable**: 16-20 hours (Phase 1 + Phase 2)
