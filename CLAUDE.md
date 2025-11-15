# Claude Context: Research Agent System

**Last Updated**: 2024-11-15
**Project**: Research Agent System v1.0
**Repository**: leegonzales/Intelbot
**Branch**: `claude/build-research-agent-system-01CK5aqiGiVCX2f1xAmivmVm`

---

## Quick Project Summary

This is an **autonomous AI research tracking agent** that:
- Collects research items from multiple sources (arXiv, Hacker News, RSS, blogs)
- Deduplicates using SQLite FTS5
- Scores and ranks items by relevance
- Synthesizes daily digests using Claude AI
- Outputs markdown to Obsidian vault
- Runs on schedule via macOS launchd

**Current Status**: 🟢 Critical fixes complete, entering testing phase

---

## Project Context

### What This Project Does
The Research Agent System is a personal research assistant that:
1. **Collects** - Fetches papers, articles, and discussions from configured sources
2. **Filters** - Removes duplicates and low-quality content
3. **Ranks** - Scores items by relevance using configurable criteria
4. **Synthesizes** - Uses Claude to create coherent daily digests
5. **Delivers** - Writes markdown files to your Obsidian vault

### Why It Exists
Built to solve the problem of staying current with AI research without drowning in noise. Instead of checking multiple sources daily, you get one curated digest.

### Who It's For
- AI researchers tracking latest developments
- Engineers following ML/LLM trends
- Anyone wanting automated research aggregation

---

## Architecture Overview

### Tech Stack
- **Language**: Python 3.10+
- **Package Manager**: Poetry
- **Database**: SQLite with FTS5 (full-text search)
- **AI**: Anthropic Claude API (claude-sonnet-4-20250514)
- **CLI**: Click framework
- **Scheduler**: macOS launchd
- **Output**: Markdown (Obsidian-compatible)

### Directory Structure
```
research_agent/
├── agents/          # SourceAgent, SynthesisAgent
├── cli/             # Click CLI commands
├── core/            # ResearchOrchestrator, Config, PromptManager
├── sources/         # ArxivSource, HackerNewsSource, RSSSource, BlogScraperSource
├── storage/         # StateManager (SQLite operations)
└── utils/           # Logger, Retry decorator, Text utils

tests/
├── unit/            # Unit tests for all components
├── integration/     # End-to-end tests
└── conftest.py      # Shared fixtures

docs/
└── project-state/   # Issue tracking, sprints, test plans
    ├── issues/      # Individual issue tracking
    ├── sprints/     # Sprint documentation
    └── tests/       # Test plans and results
```

### Key Components

**ResearchOrchestrator** (`research_agent/core/orchestrator.py`)
- Coordinates entire research cycle
- Manages data flow between components
- Entry point for CLI

**StateManager** (`research_agent/storage/state.py`)
- SQLite database operations
- FTS5 deduplication
- Run tracking and history

**SourceAgent** (`research_agent/agents/source_agent.py`)
- Parallel source collection
- Aggregates results from all sources

**SynthesisAgent** (`research_agent/agents/synthesis_agent.py`)
- Claude API integration
- Digest generation
- Fallback synthesis

**Source Collectors** (`research_agent/sources/`)
- ArxivSource: Academic papers via arXiv API
- HackerNewsSource: Top stories via HN API
- RSSSource: RSS/Atom feeds
- BlogScraperSource: Generic blog scraping

---

## Development History

### Sprint 001 (Completed)
**Goal**: Fix all critical (P1) bugs blocking production

**Completed**:
- ✅ Issue #1: Implemented centralized logging system
- ✅ Issue #2: Added retry logic with exponential backoff
- ✅ Issue #3: Added API key validation
- ✅ Issue #4: Added SQLite FTS5 support check
- ✅ Issue #5: Fixed database constraint violations
- ✅ Bonus: Cleaned up all print() statements

**Time**: 5.5 hours (vs 8-10h estimated)

**Key Commits**:
- `68ae1d3` - Critical bug fixes for production readiness
- `93ccaf2` - Replace print statements with proper logging
- `8fdc1a1` - Update project state after completing critical fixes
- `2a9bea0` - Close critical issues and document new discoveries

### Sprint 002 (Current - Planning)
**Goal**: Add comprehensive test coverage (>80%)

**Status**: 🟡 Planning complete, ready to implement

**Plan**: See `docs/project-state/sprints/SPRINT_002_PLAN.md`

---

## Current State

### What Works
- ✅ All core functionality implemented
- ✅ Database schema with FTS5
- ✅ All source collectors
- ✅ Claude synthesis
- ✅ CLI commands
- ✅ Logging system
- ✅ Retry logic
- ✅ Error handling

### What's Missing
- ❌ Comprehensive tests (<10% coverage currently)
- ❌ High priority bug fixes (Issues #6-10)
- ❌ Performance optimization
- ❌ Production deployment

### Known Issues

**Critical (P1)**: 0 remaining ✅

**High Priority (P2)**: 5 issues
- #6: Standardize path expansion (1h)
- #7: Improve DotDict robustness (1-2h)
- #8: Optimize filter_new() performance (2h)
- #9: Fix item-to-run linking (partially done in #5)
- #10: Fix BM25 normalization (2-3h)

**See**: `docs/project-state/issues/INDEX.md` for full list

---

## Key Files to Understand

### Configuration
**File**: `~/.research-agent/config.yaml`
```yaml
paths:
  db_path: ~/.research-agent/state.db
  logs_dir: ~/.research-agent/logs
  obsidian_vault: ~/Notes/Research

sources:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.LG]
  hackernews:
    enabled: true
    min_score: 100
  # ... etc
```

### Database Schema
**File**: `research_agent/storage/schema.sql`
- `seen_items` - All collected items with URL dedup
- `seen_items_fts` - FTS5 virtual table for content search
- `runs` - Research cycle executions
- `item_runs` - Many-to-many linking

### Prompts
**Files**: `~/.research-agent/prompts/*.md`
- `system.md` - Claude system prompt
- `synthesis.md` - Digest synthesis template

---

## Common Workflows

### Running a Research Cycle
```bash
# Full run
research-agent run

# Dry run (no digest written)
research-agent run --dry-run

# Verbose logging
research-agent run --verbose
```

### Checking System Status
```bash
# View stats
research-agent stats

# View recent runs
research-agent stats --runs

# Initialize system
research-agent init
```

### Development
```bash
# Install dependencies
poetry install

# Run tests (when implemented)
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Format code
poetry run black research_agent/
```

---

## Testing Strategy

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_logger.py
│   ├── test_retry.py
│   ├── test_state.py
│   ├── agents/
│   ├── sources/
│   └── core/
└── integration/       # Slower, end-to-end tests
    ├── test_full_cycle.py
    └── test_error_handling.py
```

### Key Testing Principles
1. **Mock external APIs** (arXiv, HN, Anthropic)
2. **Use in-memory SQLite** for speed
3. **Temp directories** for file I/O
4. **Fixtures** for shared test data
5. **Coverage target**: >80%

**See**: `docs/project-state/sprints/SPRINT_002_PLAN.md` for full test plan

---

## Important Patterns

### Logging
```python
from research_agent.utils.logger import get_logger

logger = get_logger("component.name")

logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug message", exc_info=True)  # With traceback
```

### Retry Decorator
```python
from research_agent.utils.retry import retry

@retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
def network_call():
    # Will retry with delays: 2s, 4s, 8s
    response = requests.get(url)
    return response.json()
```

### State Management
```python
from research_agent.storage.state import StateManager

state = StateManager(config)

# Add item (idempotent - returns existing ID if duplicate)
item_id = state.add_item(item_dict)

# Check if seen
is_new = state.is_new(item_dict)

# Record run
run_id = state.record_run(
    items_collected=all_items,
    items_new=new_items,
    items_included=digest_items,
    digest_path=output_path
)
```

### Configuration Access
```python
# DotDict allows nested access
config.sources.arxiv.enabled  # True/False
config.paths.db_path         # Path object
```

---

## Git Workflow

### Branch Strategy
- Main branch: Not specified (likely `main` or `master`)
- Feature branch: `claude/build-research-agent-system-01CK5aqiGiVCX2f1xAmivmVm`

### Commit Message Format
```
type: Brief description

Detailed explanation of changes

- Bullet points for specifics
- Reference issues: #1, #2
- Note breaking changes

Files changed:
- path/to/file.py (description)
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Important Notes
- **Always push to**: `claude/build-research-agent-system-01CK5aqiGiVCX2f1xAmivmVm`
- **Retry logic**: If push fails, retry up to 4 times with exponential backoff
- **No destructive operations**: No force push, hard reset without explicit permission

---

## Project State Tracking

### Issue Tracking
**Location**: `docs/project-state/issues/`

- `INDEX.md` - Complete issue list
- `critical/` - P1 issues (all closed ✅)
- `high-priority/` - P2 issues
- `NEW_ISSUES.md` - Issues discovered during Sprint 001

### Sprint Tracking
**Location**: `docs/project-state/sprints/`

- `SPRINT_001.md` - Critical bug fixes (complete)
- `SPRINT_002_PLAN.md` - Test implementation (current)

### Documentation
- `README.md` - User-facing documentation
- `BUG_REPORT.md` - Original validation findings (51 bugs)
- `TASK_LIST.md` - Prioritized fix tasks
- `VALIDATION_SUMMARY.md` - Executive summary
- `CLAUDE.md` - This file (project context)

---

## Environment Setup

### Required Environment Variables
```bash
# ~/.research-agent/.env
ANTHROPIC_API_KEY=your-key-here

# Optional
ANTHROPIC_MODEL=claude-sonnet-4-20250514
DEBUG=false
```

### Required Directories
```
~/.research-agent/
├── config.yaml
├── .env
├── state.db
├── logs/
│   └── 2024-11-15.log
└── prompts/
    ├── system.md
    └── synthesis.md
```

### System Requirements
- Python 3.10+
- SQLite with FTS5 support
- macOS (for launchd scheduling)
- Internet connection for sources

---

## Critical Dependencies

### Python Packages (pyproject.toml)
```toml
[tool.poetry.dependencies]
python = "^3.10"
anthropic = "^0.3.0"
click = "^8.1.0"
feedparser = "^6.0.0"
beautifulsoup4 = "^4.12.0"
requests = "^2.31.0"
python-dateutil = "^2.8.0"
pyyaml = "^6.0.0"
python-dotenv = "^1.0.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.1"
responses = "^0.23.0"
freezegun = "^1.2.2"
faker = "^19.0.0"
```

---

## Debugging Tips

### Common Issues

**Issue**: "ANTHROPIC_API_KEY not found"
- **Fix**: Add key to `~/.research-agent/.env`

**Issue**: "SQLite does not have FTS5 support"
- **Fix**: `brew install sqlite3` (macOS)

**Issue**: UNIQUE constraint violation
- **Fixed**: Issue #5 - uses INSERT OR IGNORE now

**Issue**: Network failures
- **Fixed**: Issue #2 - retry decorator handles this

### Viewing Logs
```bash
# Today's log
tail -f ~/.research-agent/logs/$(date +%Y-%m-%d).log

# All errors
grep ERROR ~/.research-agent/logs/*.log

# Verbose mode
research-agent run --verbose
```

### Database Inspection
```bash
sqlite3 ~/.research-agent/state.db

# Useful queries
SELECT COUNT(*) FROM seen_items;
SELECT * FROM runs ORDER BY completed_at DESC LIMIT 5;
SELECT url, title FROM seen_items ORDER BY collected_at DESC LIMIT 10;
```

---

## Next Steps (Priority Order)

### Immediate (Current Sprint)
1. ✅ Review Sprint 002 test plan
2. 🔄 Set up test infrastructure
3. 🔄 Implement logging tests (Issue #54)
4. 🔄 Implement retry tests (Issue #55)
5. 🔄 Implement integration tests (Issue #24)

### Short Term (Next Sprint)
1. Fix high priority bugs (#6-10)
2. Add quick wins from new issues (#53, #57, #56, #58)
3. Performance optimization (#8, #45)

### Medium Term
1. Address medium priority issues
2. Cross-platform support (Linux, Windows)
3. Additional source collectors
4. Web interface for digest viewing

---

## Performance Characteristics

### Typical Run Metrics
- **Collection**: 5-15 seconds (parallel)
- **Deduplication**: 1-2 seconds (FTS5 queries)
- **Synthesis**: 10-30 seconds (Claude API)
- **Total**: ~20-60 seconds per run

### Resource Usage
- **Memory**: ~100MB typical
- **Disk**: ~10MB/month (logs + DB)
- **Network**: ~1-5MB/run (API calls)

### Scalability Limits
- **Items/day**: Designed for ~100-200
- **Sources**: No hard limit, but 4-6 recommended
- **History**: Unlimited (SQLite handles GBs)

---

## API Rate Limits

### Anthropic Claude
- **Limit**: Varies by plan
- **Handling**: Not implemented yet (TODO: Issue #13)
- **Cost**: ~$0.01-0.05 per digest

### Source APIs
- **arXiv**: No official limit, be respectful
- **Hacker News**: No limit on API
- **RSS**: Depends on feed provider

---

## Security Considerations

### Current Security Measures
- ✅ API key in .env (not committed)
- ✅ Parameterized SQL queries (no injection)
- ✅ File permissions on .env (600)

### Known Vulnerabilities
- ⚠️ Shell command in schedule.sh (Issue #14)
- ⚠️ No input sanitization on blog scraper (Issue #38)
- ⚠️ User-agent string reveals bot (Issue #39)

**See**: Issues #14, #38, #39 for details

---

## Useful Commands Reference

```bash
# Installation
poetry install
research-agent init

# Daily usage
research-agent run
research-agent stats

# Development
poetry run pytest                    # Run tests
poetry run pytest --cov             # With coverage
poetry run pytest -v                # Verbose
poetry run pytest tests/unit/       # Unit tests only
poetry run pytest -k test_logger    # Specific test

# Database
research-agent stats --runs         # View run history
sqlite3 ~/.research-agent/state.db  # Direct DB access

# Logs
tail -f ~/.research-agent/logs/$(date +%Y-%m-%d).log

# Scheduling (macOS)
./schedule.sh --daily              # Set up daily run
launchctl list | grep research     # Check if running
```

---

## External Resources

### Documentation
- [Anthropic API Docs](https://docs.anthropic.com/)
- [arXiv API](https://arxiv.org/help/api)
- [Hacker News API](https://github.com/HackerNews/API)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [Click CLI Framework](https://click.palletsprojects.com/)

### Related Projects
- Similar tools: Pocket, Instapaper, Feedly
- Research assistants: Semantic Scholar, Connected Papers
- Note-taking: Obsidian, Roam Research

---

## Contact & Contribution

**Project Owner**: Lee Gonzales
**Repository**: leegonzales/Intelbot

### For Future Claude Sessions
This file provides context about:
- What the project does and why
- Current state and progress
- Code patterns and conventions
- Testing strategy
- Known issues and next steps

**Always check**:
1. `docs/project-state/README.md` - Current status
2. `docs/project-state/issues/INDEX.md` - Open issues
3. Latest sprint plan in `docs/project-state/sprints/`

---

**Last Updated**: 2024-11-15 after Sprint 001 completion
**Next Update**: After Sprint 002 (test implementation)
