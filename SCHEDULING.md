# Research Agent Scheduling

The research agent is configured to run automatically every morning at **6:00 AM** using macOS launchd.

## Quick Commands

```bash
# Check if schedule is running
./schedule.sh status

# Test run now (without waiting for 6 AM)
./schedule.sh test

# Uninstall the schedule
./schedule.sh uninstall

# Reinstall the schedule
./schedule.sh install
```

## How It Works

### Schedule Details
- **Run Time**: Every day at 6:00 AM
- **Command**: `python3 -m research_agent.cli.main run`
- **Working Directory**: `/Users/leegonzales/Projects/leegonzales/Intelbot`
- **Logs**: `~/.research-agent/logs/launchd-*.log`

### Files
- **Plist File**: `~/Library/LaunchAgents/com.leegonzales.research-agent.plist`
- **Source Plist**: `./com.leegonzales.research-agent.plist`
- **Schedule Script**: `./schedule.sh`

## Output

Each morning at 6 AM, the system will:

1. **Collect** research items from all sources:
   - arXiv papers (cs.AI, cs.LG, cs.CL)
   - Anthropic Engineering & News blogs
   - DeepMind, Google AI, OpenAI blogs
   - RSS feeds from tier 1 & 2 sources
   - HackerNews top stories

2. **Deduplicate** against existing items in the database

3. **Generate** a comprehensive digest using Claude

4. **Write** the digest to:
   ```
   ~/Library/CloudStorage/Dropbox/Obisidian Vaults/PrimaryVault/Lee's Vault/Personal/YYYY/MM/YYYY-MM-DD-research-digest.md
   ```

5. **Record** the run in the database

## Logs

### Application Logs
Daily application logs are stored in:
```
~/.research-agent/logs/YYYY-MM-DD.log
```

### Launchd Logs
Schedule execution logs are stored in:
```
~/.research-agent/logs/launchd-stdout.log  # Normal output
~/.research-agent/logs/launchd-stderr.log  # Errors
```

### Check Recent Runs
```bash
# View last run
tail -100 ~/.research-agent/logs/$(date +%Y-%m-%d).log

# View launchd output
tail -100 ~/.research-agent/logs/launchd-stdout.log

# View launchd errors
tail -100 ~/.research-agent/logs/launchd-stderr.log
```

## Database

Run history is tracked in:
```
~/.research-agent/state.db
```

### Check Run History
```bash
sqlite3 ~/.research-agent/state.db "
SELECT
  id,
  status,
  items_found,
  items_new,
  items_included,
  datetime(timestamp, 'localtime') as run_time
FROM research_runs
ORDER BY timestamp DESC
LIMIT 10;
"
```

## Troubleshooting

### Schedule Not Running?

1. **Check Status**:
   ```bash
   ./schedule.sh status
   ```

2. **Check Launchd Registration**:
   ```bash
   launchctl list | grep research-agent
   ```

3. **Check Logs**:
   ```bash
   tail -50 ~/.research-agent/logs/launchd-stderr.log
   ```

4. **Reinstall**:
   ```bash
   ./schedule.sh uninstall
   ./schedule.sh install
   ```

### No Digest Generated?

If fewer than 5 new items are found, the system skips digest generation to avoid creating repetitive digests. This is normal behavior when running multiple times per day.

**Solution**: Wait for the next morning when new content will be available, or check the logs to see what was collected:
```bash
tail -100 ~/.research-agent/logs/$(date +%Y-%m-%d).log | grep "new items"
```

### Testing Without Waiting for 6 AM

Run immediately:
```bash
./schedule.sh test
```

Or run directly:
```bash
python3 -m research_agent.cli.main run
```

## Changing the Schedule

To run at a different time, edit `com.leegonzales.research-agent.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>6</integer>  <!-- Change this (0-23) -->
    <key>Minute</key>
    <integer>0</integer>  <!-- Change this (0-59) -->
</dict>
```

Then reinstall:
```bash
./schedule.sh uninstall
./schedule.sh install
```

## Disabling the Schedule

Temporarily:
```bash
launchctl unload ~/Library/LaunchAgents/com.leegonzales.research-agent.plist
```

Permanently:
```bash
./schedule.sh uninstall
```

## Re-enabling the Schedule

```bash
./schedule.sh install
```

---

**Installed**: 2025-11-15
**Next Run**: Every day at 6:00 AM
