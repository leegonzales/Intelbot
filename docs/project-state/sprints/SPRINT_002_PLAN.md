# Sprint 002: Comprehensive Testing Implementation

**Sprint Goal**: Add comprehensive test coverage for all critical fixes and core functionality
**Status**: 🟡 Planning
**Estimated Duration**: 12-16 hours
**Target Coverage**: >80%

---

## Overview

This sprint focuses on implementing comprehensive tests for:
1. ✅ Critical fixes from Sprint 001 (Issues #1-5)
2. 🔧 Core infrastructure (logging, retry, state management)
3. 🔗 Integration tests for full system
4. 📊 Test coverage reporting and CI setup

---

## Linked Issue Sets

### Issue Set A: Infrastructure Tests (6 hours)
**Goal**: Test core utilities and infrastructure

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **#54** | Logging system tests | P3 | 3h | None |
| **#55** | Retry logic tests | P3 | 2h | None |
| **New** | Test infrastructure setup | P2 | 1h | None |

**Deliverables**:
- `tests/unit/test_logger.py` - 15+ test cases
- `tests/unit/test_retry.py` - 12+ test cases
- `pytest.ini` configuration
- Coverage reporting setup
- GitHub Actions CI workflow

**Acceptance Criteria**:
- ✅ Logging: >90% coverage
- ✅ Retry: >95% coverage
- ✅ All tests pass
- ✅ CI runs on push

---

### Issue Set B: State Management Tests (4 hours)
**Goal**: Expand existing state manager tests

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **New** | Database constraint tests | P2 | 1h | Issue #5 |
| **New** | FTS5 functionality tests | P2 | 1h | Issue #4 |
| **New** | Item deduplication tests | P2 | 1h | Issue #5 |
| **New** | Run tracking tests | P2 | 1h | Issue #5 |

**Deliverables**:
- Expand `tests/unit/test_state.py`
- Add 20+ new test cases
- Test all database operations
- Test constraint handling
- Test FTS5 queries

**Acceptance Criteria**:
- ✅ StateManager: >85% coverage
- ✅ All CRUD operations tested
- ✅ Edge cases covered
- ✅ Transaction handling verified

---

### Issue Set C: Source Collector Tests (3 hours)
**Goal**: Test all source collectors with mocking

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **New** | ArXiv source tests | P2 | 1h | Issue #2 |
| **New** | HackerNews source tests | P2 | 0.5h | Issue #2 |
| **New** | RSS source tests | P2 | 1h | Issue #2 |
| **New** | Blog scraper tests | P2 | 0.5h | Issue #2 |

**Deliverables**:
- `tests/unit/sources/test_arxiv.py`
- `tests/unit/sources/test_hackernews.py`
- `tests/unit/sources/test_rss.py`
- `tests/unit/sources/test_blog_scraper.py`
- Mock HTTP responses
- Test retry behavior

**Acceptance Criteria**:
- ✅ Each source: >80% coverage
- ✅ Network calls mocked
- ✅ Retry decorator tested in context
- ✅ Error handling verified

---

### Issue Set D: Agent Tests (2 hours)
**Goal**: Test orchestration and synthesis agents

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **New** | SourceAgent tests | P2 | 0.5h | Set C |
| **New** | SynthesisAgent tests | P2 | 1h | Issue #3 |
| **New** | ResearchOrchestrator tests | P2 | 0.5h | All above |

**Deliverables**:
- `tests/unit/agents/test_source_agent.py`
- `tests/unit/agents/test_synthesis_agent.py`
- `tests/unit/test_orchestrator.py`
- Mock Anthropic API calls
- Test parallel collection

**Acceptance Criteria**:
- ✅ Agents: >75% coverage
- ✅ API calls mocked
- ✅ Error paths tested
- ✅ Parallel execution verified

---

### Issue Set E: CLI and Config Tests (2 hours)
**Goal**: Test CLI commands and configuration

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **New** | CLI command tests | P2 | 1h | Issue #3 |
| **New** | Config loading tests | P2 | 0.5h | None |
| **New** | DotDict tests | P2 | 0.5h | Issue #7 |

**Deliverables**:
- `tests/unit/test_cli.py`
- `tests/unit/test_config.py`
- Test API key validation
- Test command parsing
- Test config merging

**Acceptance Criteria**:
- ✅ CLI: >70% coverage
- ✅ All commands tested
- ✅ Error messages verified
- ✅ Config validation works

---

### Issue Set F: Integration Tests (3 hours)
**Goal**: Test full system end-to-end

| Issue | Component | Priority | Estimate | Dependencies |
|-------|-----------|----------|----------|--------------|
| **#24** | Full research cycle test | P3 | 2h | All above |
| **New** | Error condition tests | P2 | 0.5h | All above |
| **New** | Data flow tests | P2 | 0.5h | All above |

**Deliverables**:
- `tests/integration/test_full_cycle.py`
- `tests/integration/test_error_handling.py`
- Test complete workflow
- Test failure recovery
- Test data persistence

**Acceptance Criteria**:
- ✅ Full cycle completes successfully
- ✅ Error recovery tested
- ✅ Database persistence verified
- ✅ Digest generation works

---

## Test Infrastructure Requirements

### Tools and Dependencies
```toml
# Add to pyproject.toml [tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.1"
responses = "^0.23.0"  # Mock HTTP
freezegun = "^1.2.2"   # Mock datetime
faker = "^19.0.0"      # Test data generation
```

### Configuration Files
1. **pytest.ini** - Test configuration
2. **.coveragerc** - Coverage settings
3. **.github/workflows/test.yml** - CI/CD
4. **tests/conftest.py** - Shared fixtures

### Directory Structure
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_logger.py       # Issue #54
│   ├── test_retry.py        # Issue #55
│   ├── test_state.py        # Expand existing
│   ├── test_config.py
│   ├── test_cli.py
│   ├── agents/
│   │   ├── test_source_agent.py
│   │   └── test_synthesis_agent.py
│   ├── sources/
│   │   ├── test_arxiv.py
│   │   ├── test_hackernews.py
│   │   ├── test_rss.py
│   │   └── test_blog_scraper.py
│   └── core/
│       └── test_orchestrator.py
└── integration/
    ├── test_full_cycle.py   # Issue #24
    ├── test_error_handling.py
    └── test_data_flow.py
```

---

## Implementation Phases

### Phase 1: Setup (1 hour)
**Tasks**:
- [ ] Add test dependencies to pyproject.toml
- [ ] Create pytest.ini configuration
- [ ] Set up .coveragerc
- [ ] Create tests directory structure
- [ ] Create conftest.py with shared fixtures
- [ ] Set up GitHub Actions CI

**Blockers**: None

---

### Phase 2: Infrastructure Tests (5 hours)
**Tasks**:
- [ ] Implement test_logger.py (Issue #54)
- [ ] Implement test_retry.py (Issue #55)
- [ ] Achieve >90% coverage on utils
- [ ] Verify CI passes

**Blockers**: Phase 1

---

### Phase 3: Core Component Tests (6 hours)
**Tasks**:
- [ ] Expand test_state.py (database tests)
- [ ] Implement source collector tests
- [ ] Implement agent tests
- [ ] Implement CLI tests

**Blockers**: Phase 2

---

### Phase 4: Integration Tests (3 hours)
**Tasks**:
- [ ] Implement full cycle test (Issue #24)
- [ ] Implement error handling tests
- [ ] Implement data flow tests
- [ ] Verify end-to-end functionality

**Blockers**: Phase 3

---

### Phase 5: Validation (1 hour)
**Tasks**:
- [ ] Run full test suite
- [ ] Generate coverage report
- [ ] Review coverage gaps
- [ ] Document test results
- [ ] Update project state

**Blockers**: Phase 4

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Overall Coverage** | >80% | pytest-cov |
| **Utils Coverage** | >90% | logger.py, retry.py |
| **State Coverage** | >85% | state.py |
| **Sources Coverage** | >80% | All sources |
| **Test Count** | >100 | pytest count |
| **CI Pass Rate** | 100% | GitHub Actions |
| **Test Execution Time** | <30s | pytest --durations |

---

## Risk Assessment

### High Risk
- ❌ **Mocking Anthropic API** - Complex API, need careful mocking
  - Mitigation: Use responses library, create fixtures

### Medium Risk
- ⚠️ **FTS5 Testing** - SQLite FTS5 may not be available in CI
  - Mitigation: Use in-memory DB, skip if FTS5 missing

- ⚠️ **Parallel Execution** - ThreadPoolExecutor testing complex
  - Mitigation: Use small pool sizes, deterministic ordering

### Low Risk
- ✅ **File I/O** - Temp directories needed
  - Mitigation: Use pytest tmp_path fixture

---

## Dependencies Between Issue Sets

```
Setup (Phase 1)
    ↓
Infrastructure Tests (Set A)
    ↓
State Tests (Set B) ←→ Source Tests (Set C)
    ↓                        ↓
Agent Tests (Set D) ←→ CLI Tests (Set E)
    ↓
Integration Tests (Set F)
    ↓
Validation
```

---

## Test Fixtures (Shared)

### Common Fixtures (tests/conftest.py)
```python
@pytest.fixture
def temp_config():
    """Temporary config for testing."""
    ...

@pytest.fixture
def temp_db():
    """In-memory SQLite database."""
    ...

@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock ANTHROPIC_API_KEY."""
    ...

@pytest.fixture
def sample_research_items():
    """Sample research items for testing."""
    ...

@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response."""
    ...
```

---

## Coverage Exclusions

Files to exclude from coverage:
- `__init__.py` files
- `install.sh`
- `schedule.sh`
- Development utilities

---

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Timeline

| Week | Phase | Hours | Deliverables |
|------|-------|-------|--------------|
| 1 | Setup + Infrastructure | 6h | Test framework + utils tests |
| 1-2 | Core Components | 6h | State, sources, agents, CLI tests |
| 2 | Integration | 3h | Full cycle tests |
| 2 | Validation | 1h | Coverage reports, docs |

**Total**: 16 hours over 2 weeks

---

## Post-Sprint Actions

After achieving >80% coverage:
1. Enable required CI checks on PRs
2. Set up coverage badges
3. Document testing guidelines
4. Create test writing guide for contributors
5. Schedule regression test runs

---

## References

- [Issue #54](../issues/NEW_ISSUES.md#issue-54) - Logging tests
- [Issue #55](../issues/NEW_ISSUES.md#issue-55) - Retry tests
- [Issue #24](../issues/INDEX.md) - Integration tests
- [Sprint 001](SPRINT_001.md) - Critical fixes that need testing
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Guide](https://pytest-cov.readthedocs.io/)

---

**Plan Status**: ✅ Ready for review and implementation
**Next Step**: Review plan → Set up infrastructure → Begin Phase 1
