# Research Agent - Testing Plan

**Version**: 1.0.0
**Last Updated**: 2024-11-15
**Current Coverage**: ~5%
**Target Coverage**: >80%

---

## Test Strategy

### Testing Pyramid

```
        /\
       /E2E\         End-to-End Tests (5%)
      /______\       - Full research cycles
     /        \      - CLI workflows
    /Integration\    Integration Tests (15%)
   /____________\    - Component integration
  /              \   - Database operations
 /  Unit Tests   \  Unit Tests (80%)
/__________________\ - Individual functions
```

---

## Test Requirements by Issue

### Critical Issues

#### #1 - Logging System
**Unit Tests** (Required):
- `tests/unit/test_logger.py`
  - [ ] Test logger creation
  - [ ] Test log levels (DEBUG, INFO, WARNING, ERROR)
  - [ ] Test file handler writes to correct location
  - [ ] Test console handler respects verbose flag
  - [ ] Test log rotation
  - [ ] Test log formatting

**Integration Tests**:
- [ ] Verify all components use logger
- [ ] Test `--verbose` flag affects all modules
- [ ] Verify log files created on first run

#### #2 - Retry Logic
**Unit Tests** (Required):
- `tests/unit/test_retry.py`
  - [ ] Test retry decorator
  - [ ] Test exponential backoff (2s, 4s, 8s)
  - [ ] Test max attempts honored
  - [ ] Test specific exceptions caught
  - [ ] Test final exception raised
  - [ ] Test success on retry

**Integration Tests**:
- [ ] Test arXiv API retry on network error
- [ ] Test Hacker News API retry
- [ ] Test Claude API retry
- [ ] Test partial success (some sources fail, others succeed)

#### #3 - API Key Validation
**Unit Tests** (Required):
- `tests/unit/test_config.py`
  - [ ] Test API key validation in config
  - [ ] Test clear error message if missing
  - [ ] Test valid key accepted

**Integration Tests**:
- [ ] Test CLI fails fast with clear message if no API key
- [ ] Test dry-run mode doesn't require API key

#### #4 - SQLite FTS5 Check
**Unit Tests** (Required):
- `tests/unit/test_state.py`
  - [ ] Test FTS5 capability check
  - [ ] Test clear error if FTS5 missing
  - [ ] Test database creation succeeds with FTS5

**Integration Tests**:
- [ ] Test StateManager initialization with FTS5
- [ ] Test full-text search works

#### #5 - Database Constraints
**Unit Tests** (Required):
- `tests/unit/test_state.py`
  - [ ] Test `add_item()` with duplicate URL
  - [ ] Test `add_item()` returns existing ID
  - [ ] Test `record_run()` links items correctly
  - [ ] Test item comparison by URL not reference

**Integration Tests**:
- [ ] Test full research cycle with duplicates
- [ ] Test items properly linked in run_items table
- [ ] Test history queries return correct items

### High Priority Issues

#### #6 - Path Expansion
**Unit Tests**: `tests/unit/test_config.py`
- [ ] Test all paths expanded in config
- [ ] Test `~` handled correctly
- [ ] Test relative paths converted to absolute

#### #7 - DotDict Robustness
**Unit Tests**: `tests/unit/test_config.py`
- [ ] Test nested access with missing keys
- [ ] Test graceful defaults
- [ ] Test clear error for required fields

#### #8 - filter_new() Performance
**Unit Tests**: `tests/unit/test_state.py`
- [ ] Test batch duplicate checking
- [ ] Test performance with 100+ items
- [ ] Test correctness maintained

**Performance Tests**:
- [ ] Benchmark with 10, 100, 1000 items
- [ ] Verify O(1) database connections

#### #9 - Item Linking
**Unit Tests**: `tests/unit/test_state.py`
- [ ] Test URL comparison instead of reference
- [ ] Test URL-to-rank mapping
- [ ] Test items linked correctly

#### #10 - BM25 Normalization
**Unit Tests**: `tests/unit/test_state.py`
- [ ] Test BM25 score normalization
- [ ] Test similarity threshold triggers
- [ ] Test with real similar titles

**Research Tests**:
- [ ] Collect real BM25 score ranges
- [ ] Validate normalization formula
- [ ] Tune threshold

---

## Unit Test Plan

### Core Components

#### `tests/unit/test_state.py` ✅ (Partial)
**Coverage**: ~30% of StateManager
**Status**: Needs expansion

Existing:
- [x] test_exact_url_dedup
- [x] test_content_hash_dedup
- [x] test_filter_new
- [x] test_search_history

Needed:
- [ ] test_is_duplicate_with_fts_similarity
- [ ] test_add_item_with_duplicate_url
- [ ] test_record_run_links_items
- [ ] test_get_recent_runs
- [ ] test_batch_duplicate_check (performance)

#### `tests/unit/test_config.py` ❌ (Missing)
**Coverage**: 0%
**Priority**: High

- [ ] test_load_default_config
- [ ] test_load_custom_config
- [ ] test_path_expansion
- [ ] test_dotdict_nested_access
- [ ] test_dotdict_missing_keys
- [ ] test_config_validation
- [ ] test_api_key_validation

#### `tests/unit/test_sources.py` ❌ (Missing)
**Coverage**: 0%
**Priority**: Medium

- [ ] test_arxiv_source_fetch
- [ ] test_hackernews_source_fetch
- [ ] test_rss_source_fetch
- [ ] test_blog_scraper_source_fetch
- [ ] test_source_error_handling
- [ ] test_source_timeout

#### `tests/unit/test_scoring.py` ❌ (Missing)
**Coverage**: 0%
**Priority**: Medium

- [ ] test_keyword_score
- [ ] test_source_score
- [ ] test_engagement_score
- [ ] test_recency_score
- [ ] test_novelty_score
- [ ] test_overall_score

#### `tests/unit/test_text_utils.py` ❌ (Missing)
**Coverage**: 0%
**Priority**: Low

- [ ] test_normalize_text
- [ ] test_extract_snippet
- [ ] test_extract_keywords
- [ ] test_clean_html
- [ ] test_truncate_text

---

## Integration Test Plan

### `tests/integration/test_full_workflow.py` ❌ (Missing)
**Priority**: Critical

- [ ] test_full_research_cycle_success
- [ ] test_research_cycle_no_items
- [ ] test_research_cycle_below_minimum
- [ ] test_research_cycle_with_duplicates
- [ ] test_dry_run_mode
- [ ] test_output_file_created
- [ ] test_database_updated

### `tests/integration/test_cli.py` ❌ (Missing)
**Priority**: High

- [ ] test_cli_run_command
- [ ] test_cli_dry_run
- [ ] test_cli_verbose
- [ ] test_cli_config_show
- [ ] test_cli_config_edit
- [ ] test_cli_history_runs
- [ ] test_cli_history_search
- [ ] test_cli_schedule_install
- [ ] test_cli_without_api_key

### `tests/integration/test_orchestrator.py` ❌ (Missing)
**Priority**: High

- [ ] test_orchestrator_initialization
- [ ] test_collect_from_sources
- [ ] test_deduplication
- [ ] test_scoring_and_ranking
- [ ] test_synthesis
- [ ] test_digest_writing
- [ ] test_state_recording
- [ ] test_error_handling

### `tests/integration/test_sources_live.py` ⚠️ (Optional)
**Priority**: Low (requires network)

- [ ] test_arxiv_live_api
- [ ] test_hackernews_live_api
- [ ] test_rss_live_feeds
- [ ] test_rate_limiting
- [ ] test_timeout_handling

---

## End-to-End Test Plan

### `tests/e2e/test_daily_digest.py` ❌ (Missing)
**Priority**: Medium

- [ ] test_complete_daily_digest_generation
- [ ] test_scheduled_execution
- [ ] test_multiple_consecutive_runs
- [ ] test_no_duplicates_across_days
- [ ] test_obsidian_vault_integration

---

## Performance Test Plan

### `tests/performance/test_scalability.py` ❌ (Missing)

- [ ] test_performance_10_items
- [ ] test_performance_100_items
- [ ] test_performance_1000_items
- [ ] test_database_query_performance
- [ ] test_fts_search_performance
- [ ] test_memory_usage

---

## Test Data & Fixtures

### Required Fixtures

#### `tests/fixtures/config_fixtures.py`
```python
@pytest.fixture
def default_config():
    """Default config for testing"""
    return Config._get_default_config()

@pytest.fixture
def test_config(tmp_path):
    """Config with temp paths"""
    # ...
```

#### `tests/fixtures/item_fixtures.py`
```python
@pytest.fixture
def sample_items():
    """Sample research items for testing"""
    return [
        {
            'url': 'https://arxiv.org/abs/2401.00001',
            'title': 'Multi-Agent Systems',
            'source': 'arxiv',
            # ...
        },
        # ...
    ]
```

#### `tests/fixtures/database_fixtures.py`
```python
@pytest.fixture
def test_db(tmp_path):
    """Temporary test database"""
    db_path = tmp_path / "test.db"
    state = StateManager(db_path)
    yield state
    # Cleanup handled by tmp_path
```

---

## Test Execution

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=research_agent --cov-report=html

# Specific test file
pytest tests/unit/test_state.py

# Specific test
pytest tests/unit/test_state.py::test_exact_url_dedup

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Coverage Goals

| Component | Target | Current | Gap |
|-----------|--------|---------|-----|
| StateManager | 90% | 30% | 60% |
| Config | 80% | 0% | 80% |
| Sources | 70% | 0% | 70% |
| Orchestrator | 85% | 0% | 85% |
| CLI | 75% | 0% | 75% |
| Utils | 80% | 0% | 80% |
| **Overall** | **80%** | **~5%** | **~75%** |

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=research_agent --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Test Results Tracking

All test runs should be documented in:
- `docs/project-state/tests/results/YYYY-MM-DD_run-{n}.md`

Template:
```markdown
# Test Run - 2024-11-15 (Run #1)

**Branch**: main
**Commit**: abc123
**Tester**: Lee Gonzales

## Summary
- Total Tests: 50
- Passed: 45
- Failed: 5
- Skipped: 0
- Coverage: 65%

## Failed Tests
1. test_bm25_normalization - AssertionError
2. ...

## Notes
- Need to fix BM25 normalization
```

---

## Issue-Test Mapping

| Issue | Required Tests | Status |
|-------|---------------|--------|
| #1 | test_logger.py | ❌ Missing |
| #2 | test_retry.py | ❌ Missing |
| #3 | test_config.py (API key) | ❌ Missing |
| #4 | test_state.py (FTS5) | ❌ Missing |
| #5 | test_state.py (constraints) | ⚠️ Partial |
| #6 | test_config.py (paths) | ❌ Missing |
| #7 | test_config.py (DotDict) | ❌ Missing |
| #8 | test_state.py (performance) | ❌ Missing |
| #9 | test_state.py (linking) | ❌ Missing |
| #10 | test_state.py (BM25) | ❌ Missing |

---

## Next Steps

1. **Immediate**: Create test fixtures and utilities
2. **Phase 1**: Write tests for critical issues #1-5
3. **Phase 2**: Write tests for high priority issues #6-10
4. **Phase 3**: Achieve 80% coverage
5. **Phase 4**: Add CI/CD pipeline

---

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Issue Tracker](../issues/)
