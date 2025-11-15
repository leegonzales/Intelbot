"""Tests for StateManager."""

import pytest
from pathlib import Path
from research_agent.storage.state import StateManager


def test_exact_url_dedup(tmp_path):
    """Test exact URL deduplication."""
    state = StateManager(tmp_path / "test.db")

    item = {
        'url': 'https://example.com/article',
        'title': 'Test Article',
        'content': 'Test content',
        'source': 'test',
    }

    # First time: not duplicate
    is_dup, reason = state.is_duplicate(item['url'], item['title'], item['content'])
    assert not is_dup

    # Add to state
    state.add_item(item)

    # Second time: is duplicate
    is_dup, reason = state.is_duplicate(item['url'], item['title'], item['content'])
    assert is_dup
    assert reason == "exact_url"


def test_content_hash_dedup(tmp_path):
    """Test content hash deduplication (different URLs, same content)."""
    state = StateManager(tmp_path / "test.db")

    item1 = {
        'url': 'https://example.com/article1',
        'title': 'Article 1',
        'content': 'Identical content here',
        'source': 'test',
    }

    item2 = {
        'url': 'https://different.com/article2',
        'title': 'Article 2',
        'content': 'Identical content here',
        'source': 'test',
    }

    state.add_item(item1)

    is_dup, reason = state.is_duplicate(item2['url'], item2['title'], item2['content'])
    assert is_dup
    assert reason == "content_hash"


def test_filter_new(tmp_path):
    """Test filtering new items."""
    state = StateManager(tmp_path / "test.db")

    items = [
        {
            'url': 'https://example.com/1',
            'title': 'Article 1',
            'content': 'Content 1',
            'source': 'test',
        },
        {
            'url': 'https://example.com/2',
            'title': 'Article 2',
            'content': 'Content 2',
            'source': 'test',
        },
    ]

    # First time: all new
    new_items = state.filter_new(items)
    assert len(new_items) == 2

    # Add first item
    state.add_item(items[0])

    # Second time: only one new
    new_items = state.filter_new(items)
    assert len(new_items) == 1
    assert new_items[0]['url'] == 'https://example.com/2'


def test_search_history(tmp_path):
    """Test FTS5 search."""
    state = StateManager(tmp_path / "test.db")

    items = [
        {
            'url': 'https://example.com/1',
            'title': 'Multi-Agent Systems',
            'content': 'Research on multi-agent coordination',
            'source': 'test',
        },
        {
            'url': 'https://example.com/2',
            'title': 'Prompt Engineering',
            'content': 'Techniques for prompt optimization',
            'source': 'test',
        },
    ]

    for item in items:
        state.add_item(item)

    # Search for "agent"
    results = state.search_history("agent", limit=10)
    assert len(results) >= 1
    assert any('agent' in r['title'].lower() for r in results)

    # Search for "prompt"
    results = state.search_history("prompt", limit=10)
    assert len(results) >= 1
    assert any('prompt' in r['title'].lower() for r in results)
