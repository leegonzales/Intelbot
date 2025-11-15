# New Issues Discovered During Sprint 001

**Discovered**: 2024-11-15 during critical bug fixes
**Total**: 10 issues
**Priority**: Medium (P3) and Low (P4)
**Total Estimate**: 12.5 hours

---

## Issue #52: Add Type Hints to logger.py and retry.py

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 1 hour
**Category**: Code Quality

### Description
The newly created `logger.py` and `retry.py` utility files lack comprehensive type hints, reducing IDE support and type safety.

### Acceptance Criteria
- [ ] All function parameters have type hints
- [ ] All return types specified
- [ ] Import `from typing import ...` as needed
- [ ] No mypy errors

### Example
```python
# Before
def setup_logger(name="research_agent", log_dir=None, verbose=False):
    ...

# After
def setup_logger(
    name: str = "research_agent",
    log_dir: Optional[Path] = None,
    verbose: bool = False,
    log_to_file: bool = True
) -> logging.Logger:
    ...
```

---

## Issue #53: Create __init__.py for utils Package

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 15 minutes
**Category**: Code Quality

### Description
The `research_agent/utils/` directory lacks an `__init__.py` file, making it not a proper Python package. This could cause import issues.

### Acceptance Criteria
- [ ] Create `research_agent/utils/__init__.py`
- [ ] Export main utilities: `setup_logger`, `get_logger`, `retry`
- [ ] Add docstring describing the utils package
- [ ] Verify imports work: `from research_agent.utils import retry`

### Implementation
```python
# research_agent/utils/__init__.py
"""
Utility functions for the Research Agent system.

This package provides:
- Logging configuration (logger.py)
- Retry logic with exponential backoff (retry.py)
- Text processing utilities (text.py)
"""

from research_agent.utils.logger import setup_logger, get_logger
from research_agent.utils.retry import retry

__all__ = ['setup_logger', 'get_logger', 'retry']
```

---

## Issue #54: Add Comprehensive Tests for Logging

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 3 hours
**Category**: Testing

### Description
No tests exist for the logging system, which is critical infrastructure.

### Acceptance Criteria
- [ ] Test logger setup with various configurations
- [ ] Test log levels (DEBUG, INFO, WARNING, ERROR)
- [ ] Test file logging
- [ ] Test console logging
- [ ] Test log rotation
- [ ] Test verbose flag behavior
- [ ] Test duplicate handler prevention
- [ ] Coverage >90%

### Test Cases
```python
# tests/unit/test_logger.py

def test_setup_logger_creates_file_handler():
    """Test that file handler is created when log_dir provided."""
    ...

def test_setup_logger_respects_verbose_flag():
    """Test that verbose=True sets DEBUG level."""
    ...

def test_get_logger_returns_child_logger():
    """Test that get_logger creates child loggers."""
    ...

def test_log_rotation_at_10mb():
    """Test that logs rotate at 10MB limit."""
    ...

def test_prevent_duplicate_handlers():
    """Test that calling setup_logger twice doesn't duplicate handlers."""
    ...
```

---

## Issue #55: Add Comprehensive Tests for Retry Logic

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 2 hours
**Category**: Testing

### Description
The retry decorator has no tests to verify exponential backoff, max attempts, and exception handling.

### Acceptance Criteria
- [ ] Test successful execution (no retries needed)
- [ ] Test retry on failure
- [ ] Test max attempts exhaustion
- [ ] Test exponential backoff timing
- [ ] Test exception filtering
- [ ] Test on_retry callback
- [ ] Coverage >95%

### Test Cases
```python
# tests/unit/test_retry.py

def test_retry_succeeds_first_attempt():
    """Test that successful calls don't retry."""
    ...

def test_retry_with_failures():
    """Test retry after transient failures."""
    ...

def test_exponential_backoff():
    """Test backoff delays: 2s, 4s, 8s."""
    ...

def test_max_attempts_exhaustion():
    """Test that exception is raised after max attempts."""
    ...

def test_exception_filtering():
    """Test that only specified exceptions trigger retry."""
    ...

def test_on_retry_callback():
    """Test that on_retry callback is called."""
    ...
```

---

## Issue #56: Validate Log Directory Permissions

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 30 minutes
**Category**: Error Handling

### Description
The logger doesn't check if the log directory is writable before attempting to create log files, potentially failing silently or with cryptic errors.

### Acceptance Criteria
- [ ] Check if log directory is writable on setup
- [ ] Raise clear error if not writable
- [ ] Provide helpful error message with chmod command
- [ ] Test with read-only directory

### Implementation
```python
# research_agent/utils/logger.py

def setup_logger(...):
    if log_to_file and log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

        # Check write permissions
        if not os.access(log_dir, os.W_OK):
            raise PermissionError(
                f"Log directory is not writable: {log_dir}\n"
                f"Please fix permissions: chmod 755 {log_dir}"
            )

        # Create log file...
```

---

## Issue #57: Log Retry Success, Not Just Failures

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 15 minutes
**Category**: Enhancement

### Description
The retry decorator only logs failures and retry attempts, but doesn't log when a retry succeeds. This makes it hard to track recovery.

### Acceptance Criteria
- [ ] Log when retry succeeds after previous failures
- [ ] Include number of attempts in success message
- [ ] Use INFO level for success after retry
- [ ] Don't log if first attempt succeeds (no noise)

### Implementation
```python
# research_agent/utils/retry.py

def retry(...):
    def wrapper(*args, **kwargs):
        for attempt in range(max_attempts):
            try:
                result = func(*args, **kwargs)

                # Log success after retry
                if attempt > 0:
                    logger.info(
                        f"{func.__name__} succeeded after {attempt + 1} attempts"
                    )

                return result
            except exceptions as e:
                # existing retry logic...
```

---

## Issue #58: Auto-Create .env File in Install Script

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 30 minutes
**Category**: UX

### Description
The install script doesn't create the `.env` file, requiring users to manually create it. This adds friction to onboarding.

### Acceptance Criteria
- [ ] Install script creates `~/.research-agent/.env` if missing
- [ ] Prompts user for ANTHROPIC_API_KEY during setup
- [ ] Adds template with all env variables
- [ ] Sets proper permissions (600)
- [ ] Doesn't overwrite existing .env

### Implementation
```bash
# install.sh

# Create .env file
ENV_FILE="$HOME/.research-agent/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env file..."

    read -p "Enter your Anthropic API key: " API_KEY

    cat > "$ENV_FILE" <<EOF
# Anthropic API Configuration
ANTHROPIC_API_KEY=$API_KEY

# Optional: Override default model
# ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Optional: Debug mode
# DEBUG=false
EOF

    chmod 600 "$ENV_FILE"
    echo "✓ Created $ENV_FILE"
fi
```

---

## Issue #59: Add Example Config with All Options

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 1 hour
**Category**: Documentation

### Description
There's no example configuration file showing all available options and their defaults, making it hard for users to customize the system.

### Acceptance Criteria
- [ ] Create `config.example.yaml` with all options
- [ ] Add comments explaining each option
- [ ] Include sensible defaults
- [ ] Document in README
- [ ] Link from error messages

### Implementation
```yaml
# config.example.yaml
# Research Agent Configuration Example
# Copy to ~/.research-agent/config.yaml and customize

# Paths
paths:
  db_path: ~/.research-agent/state.db
  logs_dir: ~/.research-agent/logs
  prompts_dir: ~/.research-agent/prompts
  obsidian_vault: ~/Notes/Research

# Sources - Enable/disable and configure each source
sources:
  arxiv:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL]
    max_results: 50
    days_back: 7

  hackernews:
    enabled: true
    endpoints: [topstories, beststories]
    max_items: 30
    min_score: 100
    filter_keywords: [AI, LLM, agent, Claude]

  # ... full example ...
```

---

## Issue #60: Add CLI Command to Test Configuration

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 2 hours
**Category**: CLI

### Description
No way to validate configuration without running a full research cycle. A `research-agent test-config` command would help users verify their setup.

### Acceptance Criteria
- [ ] Add `test-config` CLI command
- [ ] Validate all config paths exist and are writable
- [ ] Test API key is valid
- [ ] Check SQLite FTS5 support
- [ ] Verify Obsidian vault exists
- [ ] Report all issues clearly
- [ ] Exit with code 0 if all OK, 1 if any issues

### Implementation
```python
# research_agent/cli/main.py

@cli.command()
def test_config():
    """Test configuration and verify system readiness."""

    click.echo("Testing Research Agent configuration...\n")

    all_ok = True

    # Test API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        click.secho("✗ ANTHROPIC_API_KEY not found", fg='red')
        all_ok = False
    else:
        click.secho("✓ ANTHROPIC_API_KEY found", fg='green')

    # Test SQLite FTS5
    try:
        conn = sqlite3.connect(':memory:')
        conn.execute("CREATE VIRTUAL TABLE test USING fts5(content)")
        click.secho("✓ SQLite FTS5 support available", fg='green')
    except:
        click.secho("✗ SQLite FTS5 not available", fg='red')
        all_ok = False

    # Test paths...
    # Test write permissions...
    # Test Obsidian vault...

    if all_ok:
        click.secho("\n✓ All tests passed!", fg='green', bold=True)
        sys.exit(0)
    else:
        click.secho("\n✗ Some tests failed", fg='red', bold=True)
        sys.exit(1)
```

---

## Issue #61: Add Health Check CLI Command

**Priority**: 🟠 Medium (P3)
**Status**: 🟠 Open
**Estimate**: 2 hours
**Category**: CLI

### Description
No way to verify system is healthy and all components are accessible. A `research-agent health` command would help diagnose issues.

### Acceptance Criteria
- [ ] Add `health` CLI command
- [ ] Check database connectivity
- [ ] Verify recent runs (if any)
- [ ] Test network connectivity to sources
- [ ] Check disk space for logs
- [ ] Report system metrics
- [ ] Output JSON format for scripting

### Implementation
```python
# research_agent/cli/main.py

@cli.command()
@click.option('--json', is_flag=True, help='Output as JSON')
def health(json_output):
    """Check system health and connectivity."""

    health_status = {
        'overall': 'healthy',
        'checks': {}
    }

    # Database check
    try:
        state = StateManager(config)
        stats = state.get_stats()
        health_status['checks']['database'] = {
            'status': 'ok',
            'items': stats['total_items'],
            'runs': stats['total_runs']
        }
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }
        health_status['overall'] = 'unhealthy'

    # Network checks...
    # Disk space...
    # Log directory...

    if json_output:
        click.echo(json.dumps(health_status, indent=2))
    else:
        # Pretty print...
        click.echo(f"Overall: {health_status['overall']}")
        for check, result in health_status['checks'].items():
            status = '✓' if result['status'] == 'ok' else '✗'
            click.echo(f"{status} {check}: {result['status']}")
```

---

## Priority Summary

| Priority | Count | Total Estimate |
|----------|-------|----------------|
| P3 (Medium) | 10 | 12.5 hours |

All issues are marked as Medium priority as they are improvements/enhancements discovered during critical bug fixes, not blockers.

---

## Recommended Next Steps

1. **Sprint 002**: Address high priority bugs (#6-10)
2. **Sprint 003**: Add comprehensive tests (#54, #55, and deferred tests from Sprint 001)
3. **Sprint 004**: Address these new issues (#52-61)

---

## References

- [Sprint 001](../sprints/SPRINT_001.md) - Where these issues were discovered
- [Issue Index](INDEX.md) - Full issue tracker
- [BUG_REPORT.md](../../../BUG_REPORT.md) - Original bug report
