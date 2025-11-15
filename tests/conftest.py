"""
Shared pytest fixtures for research agent tests.

This module provides common fixtures used across all test suites.
"""

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pytest
from faker import Faker

# Initialize Faker for test data generation
fake = Faker()


@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock ANTHROPIC_API_KEY environment variable."""
    test_key = "sk-ant-test-key-12345"
    monkeypatch.setenv("ANTHROPIC_API_KEY", test_key)
    return test_key


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    test_dir = tmp_path / "research_agent_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def temp_config_dir(temp_dir):
    """Create temporary config directory structure."""
    config_dir = temp_dir / "config"
    config_dir.mkdir(exist_ok=True)

    # Create subdirectories
    (config_dir / "prompts").mkdir(exist_ok=True)
    (config_dir / "logs").mkdir(exist_ok=True)

    return config_dir


@pytest.fixture
def temp_db_path(temp_dir):
    """Provide path to temporary SQLite database."""
    return temp_dir / "test_state.db"


@pytest.fixture
def in_memory_db():
    """Provide an in-memory SQLite database connection."""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def sample_config_dict(temp_config_dir, temp_db_path):
    """Provide sample configuration dictionary for testing."""
    return {
        "paths": {
            "db_path": str(temp_db_path),
            "logs_dir": str(temp_config_dir / "logs"),
            "prompts_dir": str(temp_config_dir / "prompts"),
            "obsidian_vault": str(temp_config_dir / "vault"),
        },
        "sources": {
            "arxiv": {
                "enabled": True,
                "categories": ["cs.AI", "cs.LG"],
                "max_results": 10,
            },
            "hackernews": {
                "enabled": True,
                "endpoints": ["topstories"],
                "max_items": 10,
                "min_score": 50,
            },
            "rss": {
                "enabled": False,
                "feeds": [],
            },
            "blogs": {
                "enabled": False,
                "urls": [],
            },
        },
        "research": {
            "target_items": 10,
            "dedup_threshold": 0.8,
        },
        "model": {
            "name": "claude-sonnet-4-20250514",
            "max_tokens": 16000,
            "temperature": 0.3,
        },
    }


@pytest.fixture
def sample_research_item():
    """Provide a single sample research item."""
    return {
        "url": fake.url(),
        "title": fake.sentence(nb_words=8),
        "source": "arxiv",
        "content_hash": fake.sha256(),
        "snippet": fake.text(max_nb_chars=200),
        "content": fake.text(max_nb_chars=1000),
        "source_metadata": {
            "arxiv_id": "2401.12345",
            "categories": ["cs.AI"],
        },
        "collected_at": datetime.now().isoformat(),
        "published_date": datetime.now().isoformat(),
        "author": fake.name(),
        "tags": ["ai", "machine-learning"],
        "score": 0.85,
    }


@pytest.fixture
def sample_research_items():
    """Provide multiple sample research items."""
    items = []
    for i in range(10):
        items.append({
            "url": fake.url(),
            "title": fake.sentence(nb_words=8),
            "source": fake.random_element(["arxiv", "hackernews", "rss"]),
            "content_hash": fake.sha256(),
            "snippet": fake.text(max_nb_chars=200),
            "content": fake.text(max_nb_chars=1000),
            "source_metadata": {
                "id": f"item_{i}",
            },
            "collected_at": datetime.now().isoformat(),
            "published_date": datetime.now().isoformat(),
            "author": fake.name(),
            "tags": fake.words(nb=3),
            "score": fake.pyfloat(min_value=0.0, max_value=1.0),
        })
    return items


@pytest.fixture
def mock_anthropic_response():
    """Mock Anthropic API response for digest synthesis."""
    return {
        "id": "msg_test123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": """# AI Research Digest - Test

## Top Items

### 1. Sample Research Paper
**Source**: arXiv
**Why this matters**: Significant advancement in the field

This paper presents novel findings in AI research.

## TL;DR

- Key development 1
- Key development 2
- Key development 3
""",
            }
        ],
        "model": "claude-sonnet-4-20250514",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
        },
    }


@pytest.fixture
def mock_arxiv_response():
    """Mock arXiv API XML response."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>ArXiv Query: cat:cs.AI</title>
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <title>Sample AI Research Paper</title>
    <summary>This is a sample abstract about AI research.</summary>
    <author><name>John Doe</name></author>
    <published>2024-01-15T00:00:00Z</published>
    <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>"""


@pytest.fixture
def mock_hackernews_response():
    """Mock Hacker News API response."""
    return {
        "by": "testuser",
        "descendants": 42,
        "id": 12345678,
        "kids": [12345679, 12345680],
        "score": 150,
        "time": 1705276800,
        "title": "Sample HN Article About AI",
        "type": "story",
        "url": "https://example.com/article",
    }


@pytest.fixture
def mock_rss_feed():
    """Mock RSS feed data."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Research Blog</title>
    <link>https://example.com</link>
    <description>Latest AI research</description>
    <item>
      <title>New Developments in LLMs</title>
      <link>https://example.com/article1</link>
      <description>This article discusses new LLM developments.</description>
      <pubDate>Mon, 15 Jan 2024 12:00:00 GMT</pubDate>
      <author>Jane Researcher</author>
    </item>
  </channel>
</rss>"""


@pytest.fixture(autouse=True)
def reset_loggers():
    """Reset logging configuration between tests."""
    import logging

    # Clear all handlers from research_agent logger
    logger = logging.getLogger("research_agent")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)

    yield

    # Clean up after test
    logger.handlers.clear()


@pytest.fixture
def capture_logs(caplog):
    """Fixture to easily capture log messages."""
    import logging

    caplog.set_level(logging.DEBUG)
    return caplog


# Markers for test categorization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
