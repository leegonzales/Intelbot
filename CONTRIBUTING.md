# Contributing to Research Agent

Thanks for your interest in contributing!

## Development Setup

```bash
# Clone and install
git clone https://github.com/leegonzales/Intelbot.git
cd Intelbot
poetry install

# Run tests
poetry run pytest

# Format code
poetry run black research_agent/
poetry run ruff research_agent/
```

## Project Structure

```
research_agent/
├── agents/          # SourceAgent, SynthesisAgent
├── cli/             # Click CLI commands
├── core/            # ResearchOrchestrator, Config, PromptManager
├── sources/         # ArxivSource, HackerNewsSource, RSSSource, BlogScraperSource
├── storage/         # StateManager (SQLite operations)
└── utils/           # Logger, Retry decorator, Text utils

tests/
├── unit/            # Fast, isolated tests
└── integration/     # End-to-end tests
```

## Code Patterns

### Logging
```python
from research_agent.utils.logger import get_logger
logger = get_logger("component.name")
logger.info("Message")
```

### Retry Decorator
```python
from research_agent.utils.retry import retry

@retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
def network_call():
    # Will retry with exponential backoff
    pass
```

## Adding New Sources

1. Create source class in `research_agent/sources/`
2. Inherit from `ResearchSource`
3. Implement `fetch()` method
4. Add to `SourceAgent._init_sources()`
5. Add config section to `config.yaml`

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure code passes `black` and `ruff`
5. Submit a pull request

## Questions?

Open an issue or contact lee@catalystai.services
