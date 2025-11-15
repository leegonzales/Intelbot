# Issue #3: Validate API Keys

**Priority**: 🔴 Critical (P1)
**Status**: ✅ Closed
**Assignee**: Claude
**Estimate**: 1 hour
**Actual**: 0.5 hours
**Created**: 2024-11-15
**Updated**: 2024-11-15
**Closed**: 2024-11-15

---

## Summary

No validation of `ANTHROPIC_API_KEY` before attempting synthesis, causing cryptic errors when key is missing.

## Resolution

✅ **FIXED** - Added API key validation at CLI startup

### Implementation Details

**Files Modified**:
- `research_agent/cli/main.py` - Added API key check in `run()` command

### Features Implemented
- ✅ Check for `ANTHROPIC_API_KEY` environment variable on startup
- ✅ Fail fast with clear error message
- ✅ Provide helpful setup instructions
- ✅ Exit with code 1 if missing

### Commits
- `68ae1d3` - API key validation implementation

---

## Acceptance Criteria

- [x] Check for `ANTHROPIC_API_KEY` before running
- [x] Clear error message with setup instructions
- [x] Fail fast (before any processing)
- [x] Exit with non-zero code

## Implementation Code

```python
# research_agent/cli/main.py (in run command)

@click.command()
@click.option('--dry-run', is_flag=True, help='Run without writing digest')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--config', type=click.Path(exists=True), help='Config file path')
def run(dry_run, verbose, config):
    """Run a research cycle."""

    # Validate API key first
    import os
    if not os.getenv('ANTHROPIC_API_KEY'):
        click.secho(
            "Error: ANTHROPIC_API_KEY environment variable not found.",
            fg='red',
            err=True
        )
        click.echo("Please add your API key to ~/.research-agent/.env:")
        click.echo("  ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)

    # Rest of run logic...
```

## Error Message Example

```
Error: ANTHROPIC_API_KEY environment variable not found.
Please add your API key to ~/.research-agent/.env:
  ANTHROPIC_API_KEY=your-key-here
```

## Test Requirements

**Unit Tests** (deferred to Sprint 002):
- [ ] Test with valid API key (should succeed)
- [ ] Test with missing API key (should exit with code 1)
- [ ] Test error message content
- [ ] Test with empty API key

**Integration Tests**:
- [ ] Verify early failure before network calls
- [ ] Verify no wasted processing time

## References

- [BUG_REPORT.md](../../../../BUG_REPORT.md) #3
- [TASK_LIST.md](../../../../TASK_LIST.md) Task 1.3
- [Sprint 001](../../sprints/SPRINT_001.md)
