---
title: "[CRITICAL] Validate API keys on startup"
labels: bug, critical, priority-1, configuration
---

## Problem

System creates Anthropic client without checking if `ANTHROPIC_API_KEY` is set, leading to cryptic runtime errors after processing has begun.

## Current Behavior

- `SynthesisAgent.__init__()` creates client with no validation
- Runs through entire collection and processing
- Fails at synthesis step with unclear error:
  ```
  Error: anthropic.APIConnectionError: API key not found
  ```
- Wastes time and resources before failing

## Expected Behavior

- Check for API key before starting run
- Fail fast with clear error message:
  ```
  Error: ANTHROPIC_API_KEY not found in environment
  Please add your API key to ~/.research-agent/.env
  ```
- Optionally validate key format
- Check before any processing begins

## Files Affected

- `research_agent/agents/synthesis_agent.py:17` - Client creation
- `research_agent/cli/main.py:26` - CLI run command

## Proposed Solution

**Option 1: Validate in SynthesisAgent.__init__()**
```python
def __init__(self, config, prompt_manager):
    import os
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. "
            "Please add your API key to ~/.research-agent/.env"
        )
    self.client = anthropic.Anthropic()
```

**Option 2: Validate in CLI run command (before creating orchestrator)**
```python
@cli.command()
def run(dry_run, verbose, config):
    # Validate API key first
    if not os.getenv('ANTHROPIC_API_KEY'):
        click.secho("Error: ANTHROPIC_API_KEY not found", fg='red')
        click.echo("Please add your API key to ~/.research-agent/.env")
        sys.exit(1)

    # Continue with run...
```

Recommend **Option 2** for better UX.

## Acceptance Criteria

- [ ] API key checked before run starts
- [ ] Clear error message if missing
- [ ] Suggests adding to `.env` file
- [ ] No processing happens before validation
- [ ] Works with dry-run mode

## Priority

**CRITICAL** - Poor user experience and wasted resources.

## Effort Estimate

1 hour

## Related Issues

#11 Add Configuration Validation

## References

- BUG_REPORT.md #3
- TASK_LIST.md Task 1.3
