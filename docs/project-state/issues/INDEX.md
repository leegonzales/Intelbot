# Issue Tracker - Complete Index

**Total Issues**: 61 (51 original + 10 new)
**Open**: 56
**Closed**: 5

Last Updated: 2024-11-15

---

## Critical Issues (P1) - 5 issues ✅ ALL FIXED

| # | Title | Status | Assignee | Actual | Labels |
|---|-------|--------|----------|--------|--------|
| [1](critical/01-logging.md) | Implement logging system | ✅ Closed | Claude | 2h | critical, infrastructure |
| [2](critical/02-retry.md) | Add retry logic | ✅ Closed | Claude | 1h | critical, networking |
| [3](critical/03-api-keys.md) | Validate API keys | ✅ Closed | Claude | 0.5h | critical, config |
| [4](critical/04-fts5.md) | Check SQLite FTS5 | ✅ Closed | Claude | 0.5h | critical, database |
| [5](critical/05-constraints.md) | Fix DB constraints | ✅ Closed | Claude | 1.5h | critical, database |

**Total Actual Time**: 5.5 hours (vs 8-10h estimated)

---

## High Priority Issues (P2) - 5 issues

| # | Title | Status | Assignee | Est | Labels |
|---|-------|--------|----------|-----|--------|
| [6](high-priority/06-paths.md) | Standardize path expansion | 🟡 Open | - | 1h | high, config |
| [7](high-priority/07-dotdict.md) | Improve DotDict | 🟡 Open | - | 1-2h | high, config |
| [8](high-priority/08-performance.md) | Optimize filter_new() | 🟡 Open | - | 2h | high, performance |
| [9](high-priority/09-linking.md) | Fix item linking | 🟡 Open | - | 1h | high, database |
| [10](high-priority/10-bm25.md) | Fix BM25 normalization | 🟡 Open | - | 2-3h | high, search |

**Total Estimate**: 7-9 hours

---

## Medium Priority Issues (P3) - 15 issues

### Configuration & Validation
| # | Title | Status | Est |
|---|-------|--------|-----|
| 11 | Add config validation | 🟠 Open | 3h |
| 12 | Make thresholds configurable | 🟠 Open | 1h |

### Error Handling
| # | Title | Status | Est |
|---|-------|--------|-----|
| 13 | Add rate limiting | 🟠 Open | 2-3h |
| 14 | Secure shell commands | 🟠 Open | 30m |
| 15 | Improve prompt error handling | 🟠 Open | 1h |
| 16 | Configure network timeouts | 🟠 Open | 1h |
| 17 | Add thread pool timeout | 🟠 Open | 30m |

### Code Quality
| # | Title | Status | Est |
|---|-------|--------|-----|
| 18 | Enhance blog scraper | 🟠 Open | 6h |
| 19 | Handle DateTime parsing | 🟠 Open | 1h |
| 20 | Verify dateutil import | 🟠 Open | 15m |
| 21 | Add type hints | 🟠 Open | 4h |
| 22 | Replace print with logging | 🟠 Open | 2h |
| 23 | Use logging for errors | 🟠 Open | 1h |

### Testing
| # | Title | Status | Est |
|---|-------|--------|-----|
| 24 | Add integration tests | 🟠 Open | 8h |
| 25 | Improve install script | 🟠 Open | 1h |

**Total Estimate**: 30-35 hours

---

## Low Priority Issues (P4) - 26 issues

### Enhancements
| # | Title | Status | Category |
|---|-------|--------|----------|
| 26 | Improve fallback synthesis | 🔵 Open | Enhancement |
| 27 | Add database locking handling | 🔵 Open | Database |
| 28 | Implement migration rollback | 🔵 Open | Database |
| 29 | Validate schema file path | 🔵 Open | Database |
| 30 | Validate Obsidian vault | 🔵 Open | Output |
| 31 | Make scoring weights configurable | 🔵 Open | Config |
| 32 | Add progress indicators | 🔵 Open | UX |
| 33 | Make ArxivSource date filter configurable | 🔵 Open | Config |
| 34 | Improve RSS error handling | 🔵 Open | Error Handling |
| 35 | Validate digest content | 🔵 Open | Output |

### Platform Support
| # | Title | Status | Category |
|---|-------|--------|----------|
| 36 | Add cron/Task Scheduler support | 🔵 Open | Platform |
| 37 | Fix launchd path assumptions | 🔵 Open | Platform |

### Security
| # | Title | Status | Category |
|---|-------|--------|----------|
| 38 | Add input sanitization | 🔵 Open | Security |
| 39 | Improve user-agent string | 🔵 Open | Security |

### Testing & Documentation
| # | Title | Status | Category |
|---|-------|--------|----------|
| 40-41 | Add comprehensive tests | 🔵 Open | Testing |
| 42 | Add missing docstrings | 🔵 Open | Documentation |
| 43 | Test README installation | 🔵 Open | Documentation |
| 44 | Expand troubleshooting | 🔵 Open | Documentation |

### Performance
| # | Title | Status | Category |
|---|-------|--------|----------|
| 45 | Optimize FTS queries | 🔵 Open | Performance |
| 46 | Add caching layer | 🔵 Open | Performance |
| 47 | Add prompt cache invalidation | 🔵 Open | Performance |

**Total Estimate**: 40-50 hours

---

## New Issues Discovered (Sprint 001) - 10 issues

Issues discovered during critical bug fixes that should be addressed:

### Code Quality (P3)
| # | Title | Status | Est | Category |
|---|-------|--------|-----|----------|
| 52 | Add type hints to logger.py and retry.py | 🟠 Open | 1h | Code Quality |
| 53 | Create __init__.py for utils package | 🟠 Open | 15m | Code Quality |
| 54 | Add comprehensive tests for logging | 🟠 Open | 3h | Testing |
| 55 | Add comprehensive tests for retry | 🟠 Open | 2h | Testing |

### Error Handling (P3)
| # | Title | Status | Est | Category |
|---|-------|--------|-----|----------|
| 56 | Validate log directory permissions | 🟠 Open | 30m | Error Handling |
| 57 | Log retry success not just failures | 🟠 Open | 15m | Enhancement |

### UX & Config (P3-P4)
| # | Title | Status | Est | Category |
|---|-------|--------|-----|----------|
| 58 | Auto-create .env file in install script | 🟠 Open | 30m | UX |
| 59 | Add example config with all options | 🟠 Open | 1h | Documentation |
| 60 | Add CLI command to test configuration | 🟠 Open | 2h | CLI |
| 61 | Add health check CLI command | 🟠 Open | 2h | CLI |

**Total Estimate**: 12.5 hours

---

## Summary by Category

| Category | Count | Priority Breakdown |
|----------|-------|-------------------|
| Database | 7 | P1: 2, P2: 2, P3: 1, P4: 2 |
| Configuration | 7 | P1: 1, P2: 2, P3: 2, P4: 2 |
| Error Handling | 6 | P1: 1, P3: 4, P4: 1 |
| Testing | 5 | P3: 1, P4: 4 |
| Performance | 5 | P2: 1, P3: 0, P4: 4 |
| Documentation | 4 | P4: 4 |
| Networking | 3 | P1: 1, P3: 2 |
| Security | 2 | P4: 2 |
| Platform | 2 | P4: 2 |
| Other | 10 | Mixed |

---

## Issue Lifecycle

```
🔴 Open (Critical)    → 🟡 In Progress → ✅ Closed
🟡 Open (High)        → 🟡 In Progress → ✅ Closed
🟠 Open (Medium)      → 🟡 In Progress → ✅ Closed
🔵 Open (Low)         → 🟡 In Progress → ✅ Closed
                      → 🚫 Blocked     → 🟡 In Progress
```

---

## Quick Links

### By Priority
- [Critical Issues](critical/)
- [High Priority Issues](high-priority/)
- [Medium Priority Issues](medium-priority/)
- [Low Priority Issues](low-priority/)

### By Category
- Database: #4, #5, #9, #10, #27, #28, #29
- Configuration: #3, #6, #7, #11, #12, #31, #33
- Testing: #24, #40, #41, #42, #43
- Performance: #8, #45, #46, #47
- Error Handling: #2, #13, #15, #16, #17, #34

### Documentation
- [Full Bug Report](../../../BUG_REPORT.md) - Detailed analysis
- [Task List](../../../TASK_LIST.md) - Prioritized fixes
- [Validation Summary](../../../VALIDATION_SUMMARY.md) - Executive summary
- [Test Plan](../tests/TESTING.md) - Testing strategy

---

## How to Use This Tracker

1. **Pick an issue** from the priority list
2. **Create a branch**: `git checkout -b fix/issue-{number}`
3. **Update issue status** in the tracking file
4. **Write tests** per test plan
5. **Implement fix** following issue guidelines
6. **Run tests**: `pytest`
7. **Update issue**: Mark ✅ Closed
8. **Commit & PR**: Reference issue number

---

## Labels

- `critical` - Blocks production (P1)
- `high` - Must fix before deploy (P2)
- `medium` - Should fix soon (P3)
- `low` - Nice to have (P4)
- `bug` - Something is broken
- `enhancement` - New feature/improvement
- `database` - Database-related
- `config` - Configuration-related
- `testing` - Test-related
- `documentation` - Docs-related
- `performance` - Performance issue
- `security` - Security issue

---

**Need help?** See [TASK_LIST.md](../../../TASK_LIST.md) for detailed implementation guidance.
