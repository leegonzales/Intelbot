# Research Agent

Autonomous AI research tracking with preference learning.

**Version**: 1.0.0
**Status**: 🟡 Testing Phase (Critical fixes complete)

> **For Developers**: See [CLAUDE.md](CLAUDE.md) for complete project context, architecture, and development history.
>
> **Project State**: [docs/project-state/README.md](docs/project-state/README.md) | **Issues**: [docs/project-state/issues/INDEX.md](docs/project-state/issues/INDEX.md)

## Overview

Research Agent is an automated daily digest system for AI research developments. It surfaces high-signal content from academic papers, practitioner blogs, and technical discourse, outputting markdown reports searchable by Claude Code and stored in your Obsidian vault.

### Key Features

- **Automated Daily Digests**: Scheduled execution via macOS launchd
- **Multi-Source Collection**: arXiv papers, Hacker News, RSS feeds, blogs
- **Intelligent Deduplication**: URL, content hash, and FTS5-based similarity
- **Relevance Scoring**: Multi-signal ranking (keywords, source tier, engagement, recency, novelty)
- **Claude-Powered Synthesis**: AI-generated digest with thematic grouping
- **Obsidian Integration**: Markdown output with proper frontmatter and tags
- **State Tracking**: SQLite database with full-text search (FTS5)
- **Preference Learning**: Track engagement to improve relevance over time (Phase 2)

## Installation

### Requirements

- Python 3.10+
- macOS (for launchd scheduling)
- Anthropic API key

### Quick Start

```bash
# Clone the repository
git clone https://github.com/leegonzales/research-agent.git
cd research-agent

# Run installation script
bash scripts/install.sh

# Add your API key
echo "ANTHROPIC_API_KEY=your-key-here" > ~/.research-agent/.env

# Test the system
research-agent run --dry-run

# Enable daily scheduling
research-agent schedule install
```

### Manual Installation

```bash
# Install package
pip install -e .

# Create config directory
mkdir -p ~/.research-agent/{prompts,logs}

# Copy configuration examples
cp .env.example .env
cp config.yaml.example config.yaml

# Edit configuration files with your settings
# 1. Add your Anthropic API key to .env
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# 2. Update config.yaml with your paths (Obsidian vault location, etc.)
nano config.yaml  # or use your preferred editor

# Copy and customize prompts
cp prompts/system.example.md ~/.research-agent/prompts/system.md
cp prompts/synthesis.example.md ~/.research-agent/prompts/synthesis.md
cp prompts/sources.example.md ~/.research-agent/prompts/sources.md

# Edit prompts to customize for your use case
# Replace placeholders like {{USER_NAME}}, {{USER_COMPANY}}, etc.
nano ~/.research-agent/prompts/system.md
nano ~/.research-agent/prompts/synthesis.md

# Note: The schedule.sh script will automatically generate the
# launchd plist from the template when you run './schedule.sh install'
```

### Customizing Prompts

The prompt templates contain placeholders that you should replace:

**In `~/.research-agent/prompts/system.md`**:
- `{{USER_NAME}}` - Your name
- `{{USER_TITLE}}` - Your job title
- `{{USER_COMPANY}}` - Your company/organization
- `{{USER_EXPERIENCE}}` - Your professional background
- `{{USER_PROGRAMS}}` - Programs or initiatives you run
- `{{USER_FRAMEWORKS}}` - Frameworks or methodologies you use
- `{{USER_VALUES}}` - Your professional values

**In `~/.research-agent/prompts/synthesis.md`**:
- `{{USER_NAME}}` - Your name
- `{{USER_COMPANY}}` - Your company/organization
- `{{USER_PROGRAMS}}` - Your programs
- `{{USER_THESIS}}` - Your key thesis or framework
- `{{USER_WORK_CONTEXT_*}}` - Specific work contexts to connect research to

This customization ensures the digest is relevant to your specific work and interests.

## Configuration

### Main Config File

Edit `~/.research-agent/config.yaml` to customize:

- **Paths**: Data directory, output location, prompt templates
- **Sources**: Enable/disable sources, configure search parameters
- **Research**: Target items, deduplication thresholds
- **Output**: File naming, directory structure, metadata
- **Model**: Claude model, temperature, max tokens
- **Schedule**: Run time, retry logic

See `config.yaml.example` for full configuration options.

### Prompt Templates

Customize the AI's behavior by editing:

- `~/.research-agent/prompts/system.md` - Research analyst persona and selection criteria
- `~/.research-agent/prompts/sources.md` - Source configuration and filtering strategy
- `~/.research-agent/prompts/synthesis.md` - Output format template

Edit prompts with:
```bash
research-agent config edit system
research-agent config edit sources
research-agent config edit synthesis
```

## Usage

### Manual Execution

```bash
# Run research cycle
research-agent run

# Dry run (don't write outputs)
research-agent run --dry-run

# Verbose output
research-agent run --verbose

# Custom config file
research-agent run --config /path/to/config.yaml
```

### Scheduled Execution

```bash
# Install daily schedule (7:00 AM default)
research-agent schedule install

# Check schedule status
research-agent schedule status

# Uninstall schedule
research-agent schedule uninstall
```

### History & Search

```bash
# View recent runs
research-agent history runs --last 10

# Search historical items
research-agent history search "multi-agent systems"
```

### Configuration Management

```bash
# Show current config
research-agent config show

# Get config file path
research-agent config path
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ launchd (macOS scheduler)                               │
│ Triggers: Daily 7:00 AM                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ ResearchOrchestrator                                    │
│ - Load config & prompts                                 │
│ - Execute research cycle                                │
│ - Handle failures & retries                             │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
┌────────────┐ ┌──────────┐ ┌────────────┐
│SourceAgent │ │StateManager│ │DigestWriter│
│ - arXiv    │ │ - SQLite   │ │ - Markdown │
│ - HN       │ │ - FTS5     │ │ - Obsidian │
│ - RSS      │ │ - Dedup    │ │ - Metadata │
│ - Blogs    │ │ - History  │ │            │
└────────────┘ └──────────┘ └────────────┘
```

### Components

**ResearchOrchestrator**: Main workflow coordinator

**SourceAgent**: Parallel collection from multiple sources

**StateManager**: SQLite database with FTS5 for deduplication and search

**SynthesisAgent**: Claude-powered digest generation

**DigestWriter**: Markdown formatting and file output

**RelevanceScorer**: Multi-signal item ranking

## Directory Structure

```
~/.research-agent/
├── config.yaml              # Main configuration
├── state.db                 # SQLite database
├── prompts/
│   ├── system.md           # Research analyst persona
│   ├── sources.md          # Source configuration
│   └── synthesis.md        # Output format template
├── logs/
│   ├── YYYY-MM-DD.log      # Daily run logs
│   └── launchd.*.log       # Scheduler logs
└── .env                    # API keys

~/Documents/Obsidian/Research/Digests/  # Output location
└── YYYY/
    └── MM/
        └── YYYY-MM-DD-research-digest.md
```

## Database Schema

### Core Tables

- **seen_items**: All collected items with FTS5 indexing
- **research_runs**: Audit trail of all runs
- **run_items**: Many-to-many linking runs and items

### Phase 2 (Preference Learning)

- **item_engagement**: Track user engagement (opened, rated, etc.)
- **source_performance**: Source quality metrics
- **learned_topics**: Auto-extracted topic preferences

## Development

### Current Development Status

**Sprint 001**: ✅ Complete - All critical bugs fixed ([details](docs/project-state/sprints/SPRINT_001.md))
**Sprint 002**: 🔄 In Progress - Comprehensive testing ([plan](docs/project-state/sprints/SPRINT_002_PLAN.md))

### Running Tests

```bash
# Install dev dependencies
poetry install

# Run tests (Sprint 002 in progress)
poetry run pytest

# Run with coverage
poetry run pytest --cov=research_agent --cov-report=html

# Run specific test suites
poetry run pytest tests/unit/              # Unit tests only
poetry run pytest tests/integration/       # Integration tests only
poetry run pytest -v                       # Verbose output
```

**Current Coverage**: ~10% (target: >80% by end of Sprint 002)

**Test Plan**: See [Sprint 002 Plan](docs/project-state/sprints/SPRINT_002_PLAN.md) for comprehensive testing strategy

### Code Quality

```bash
# Format code
black research_agent

# Lint
ruff research_agent
```

### Adding New Sources

1. Create source class in `research_agent/sources/`
2. Inherit from `ResearchSource`
3. Implement `fetch()` method
4. Add to `SourceAgent._init_sources()`
5. Add config section to `config.yaml`

Example:

```python
from research_agent.sources.base import ResearchSource

class MySource(ResearchSource):
    def fetch(self) -> List[Dict]:
        items = []
        # Fetch logic here
        return items
```

## Troubleshooting

### No items collected

- Check API keys in `~/.research-agent/.env`
- Verify source configurations in `config.yaml`
- Check network connectivity
- Review logs in `~/.research-agent/logs/`

### Digest not generated

- Ensure minimum items threshold is met (default: 3)
- Check Claude API key and quota
- Review synthesis errors in logs
- Try `--dry-run --verbose` for debugging

### Schedule not running

- Check launchd status: `research-agent schedule status`
- Review scheduler logs: `~/.research-agent/logs/launchd.*.log`
- Verify executable path: `which research-agent`
- Reload schedule: `research-agent schedule uninstall && research-agent schedule install`

### Database issues

```bash
# Rebuild FTS index
sqlite3 ~/.research-agent/state.db "DELETE FROM items_fts"
sqlite3 ~/.research-agent/state.db "INSERT INTO items_fts(items_fts) VALUES('rebuild')"

# Vacuum database
sqlite3 ~/.research-agent/state.db "VACUUM"
```

## Roadmap

### Phase 1: Core Functionality (Current)
- [x] Multi-source collection
- [x] Deduplication
- [x] Relevance scoring
- [x] Claude synthesis
- [x] Obsidian output
- [x] Scheduling

### Phase 2: Preference Learning
- [ ] Engagement tracking
- [ ] Adaptive scoring
- [ ] Source performance metrics
- [ ] Topic preference learning

### Phase 3: Advanced Features
- [ ] Embedding-based semantic search
- [ ] Weekly rollup digests
- [ ] Slack/email notifications
- [ ] Zotero integration
- [ ] Graph visualization

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code quality (black, ruff)
5. Submit a pull request

## License

MIT License

## Author

Lee Gonzales
Director of AI Transformation, BetterUp
Founder, Catalyst AI Services

## Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI synthesis
- [arXiv API](https://arxiv.org/) - Research papers
- [Hacker News API](https://github.com/HackerNews/API) - Community discourse
- [SQLite FTS5](https://www.sqlite.org/fts5.html) - Full-text search
- [Click](https://click.palletsprojects.com/) - CLI framework

---

**Questions?** Open an issue or contact lee@catalystai.services
