"""Tests for Brave Search web search source."""

import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
import requests

from research_agent.sources.web_search import WebSearchSource


@pytest.fixture
def web_search_config():
    """Provide web search source config."""
    return {
        'enabled': True,
        'tier': 3,
        'priority': 'medium',
        'freshness': 'pw',
        'max_queries_per_run': 2,
        'results_per_query': 5,
        'use_news_api': True,
        'request_delay': 0,  # No delay in tests
        'queries': [
            'AI agent marketplace platform',
            'AI agents crypto blockchain',
        ],
    }


@pytest.fixture
def mock_brave_api_key(monkeypatch):
    """Mock BRAVE_SEARCH_API_KEY environment variable."""
    monkeypatch.setenv('BRAVE_SEARCH_API_KEY', 'BSA-test-key-12345')
    return 'BSA-test-key-12345'


@pytest.fixture
def source(web_search_config, mock_brave_api_key):
    """Create WebSearchSource instance with mocked API key."""
    return WebSearchSource(web_search_config)


@pytest.fixture
def mock_brave_response():
    """Mock Brave Search News API response."""
    return {
        'results': [
            {
                'url': 'https://example.com/ai-marketplace-launch',
                'title': 'New AI Agent Marketplace Launches',
                'description': 'A decentralized marketplace for autonomous AI agents.',
                'age': '2 hours ago',
                'meta_url': {
                    'hostname': 'example.com',
                },
            },
            {
                'url': 'https://crypto-news.com/agents-blockchain',
                'title': 'AI Agents Now Trading on <b>Blockchain</b>',
                'description': 'Crypto tokens power new agent economy platform.',
                'page_age': '2026-02-18T10:00:00Z',
                'meta_url': {
                    'hostname': 'crypto-news.com',
                },
            },
            {
                'url': 'https://tech.io/dao-agents',
                'title': 'DAO Governance by Autonomous AI Agents',
                'description': 'Smart contracts enable decentralized agent coordination.',
                'age': '3 days ago',
                'meta_url': {
                    'hostname': 'tech.io',
                },
            },
        ],
    }


class TestWebSearchSourceInit:
    """Test WebSearchSource initialization."""

    def test_init_with_config(self, source, web_search_config):
        assert source.tier == 3
        assert source.freshness == 'pw'
        assert source.results_per_query == 5
        assert source.max_queries_per_run == 2
        assert len(source.queries) == 2

    def test_init_defaults(self, mock_brave_api_key):
        config = {'enabled': True}
        source = WebSearchSource(config)
        assert source.tier == 3
        assert source.freshness == 'pw'
        assert source.results_per_query == 10
        assert source.max_queries_per_run == 5
        assert source.queries == WebSearchSource.DEFAULT_QUERIES

    def test_init_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            config = {'enabled': True}
            source = WebSearchSource(config)
            assert source.api_key == ''


class TestWebSearchSourceFetch:
    """Test fetch method."""

    def test_fetch_returns_items(self, source, mock_brave_response):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_brave_response
        mock_resp.raise_for_status = MagicMock()

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp):
            items = source.fetch()

        assert len(items) > 0
        for item in items:
            assert 'url' in item
            assert 'title' in item
            assert item['source'] == 'web_search:brave'

    def test_fetch_deduplicates_by_url(self, source):
        """Items with the same URL across queries should be deduplicated."""
        duplicate_response = {
            'results': [
                {
                    'url': 'https://example.com/same-article',
                    'title': 'Duplicate Article',
                    'description': 'Same article from different queries.',
                    'age': '1 hour ago',
                    'meta_url': {'hostname': 'example.com'},
                },
            ],
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = duplicate_response
        mock_resp.raise_for_status = MagicMock()

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp):
            items = source.fetch()

        # Should have only 1 item even though 2 queries ran
        urls = [item['url'] for item in items]
        assert len(urls) == len(set(urls))

    def test_fetch_skips_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            config = {'enabled': True, 'request_delay': 0}
            source = WebSearchSource(config)
            items = source.fetch()
            assert items == []

    def test_fetch_handles_api_error(self, source):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp):
            items = source.fetch()

        assert items == []


class TestResultToItem:
    """Test _result_to_item conversion."""

    def test_basic_conversion(self, source):
        result = {
            'url': 'https://example.com/article',
            'title': 'AI Marketplace Article',
            'description': 'Description of the article.',
            'age': '5 hours ago',
            'meta_url': {'hostname': 'example.com'},
        }

        item = source._result_to_item(result, 'AI marketplace')

        assert item['url'] == 'https://example.com/article'
        assert item['title'] == 'AI Marketplace Article'
        assert item['source'] == 'web_search:brave'
        assert item['source_metadata']['query'] == 'AI marketplace'
        assert item['source_metadata']['tier'] == 3
        assert item['category'] == 'ai-agents'

    def test_html_cleaned_from_title(self, source):
        result = {
            'url': 'https://example.com/article',
            'title': 'AI <b>Marketplace</b> Article',
            'description': 'A <em>great</em> article.',
            'meta_url': {'hostname': 'example.com'},
        }

        item = source._result_to_item(result, 'test query')
        assert '<b>' not in item['title']
        assert '<em>' not in item['snippet']

    def test_returns_none_for_missing_url(self, source):
        result = {'title': 'No URL'}
        assert source._result_to_item(result, 'query') is None

    def test_returns_none_for_missing_title(self, source):
        result = {'url': 'https://example.com'}
        assert source._result_to_item(result, 'query') is None


class TestParseDate:
    """Test date parsing."""

    def test_iso_format(self, source):
        result = {'page_age': '2026-02-18T10:00:00Z'}
        dt = source._parse_date(result)
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 18

    def test_relative_hours(self, source):
        result = {'age': '3 hours ago'}
        dt = source._parse_date(result)
        assert dt is not None
        # Should be roughly 3 hours ago
        age = datetime.now() - dt
        assert 2.9 * 3600 <= age.total_seconds() <= 3.1 * 3600

    def test_relative_days(self, source):
        result = {'age': '2 days ago'}
        dt = source._parse_date(result)
        assert dt is not None
        age = datetime.now() - dt
        assert 1.9 * 86400 <= age.total_seconds() <= 2.1 * 86400

    def test_relative_weeks(self, source):
        result = {'age': '1 week ago'}
        dt = source._parse_date(result)
        assert dt is not None
        age = datetime.now() - dt
        assert 6.9 * 86400 <= age.total_seconds() <= 7.1 * 86400

    def test_no_date_returns_none(self, source):
        result = {}
        assert source._parse_date(result) is None


class TestExtractTags:
    """Test tag extraction."""

    def test_marketplace_tag(self, source):
        tags = source._extract_tags('AI Marketplace Launch', 'New platform', 'query')
        assert 'marketplace' in tags

    def test_crypto_tags(self, source):
        tags = source._extract_tags(
            'Blockchain Agent Trading',
            'Crypto token decentralized exchange',
            'query',
        )
        assert 'blockchain' in tags
        assert 'crypto' in tags
        assert 'decentralized' in tags

    def test_always_includes_base_tags(self, source):
        tags = source._extract_tags('Generic Title', 'Generic description', 'query')
        assert 'web-search' in tags
        assert 'ai-agents' in tags

    def test_dao_tag(self, source):
        tags = source._extract_tags('DAO Governance', 'Smart contract coordination', 'query')
        assert 'dao' in tags
        assert 'smart-contract' in tags


class TestSearch:
    """Test _search method."""

    def test_search_sends_correct_headers(self, source):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': []}
        mock_resp.raise_for_status = MagicMock()

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp) as mock_get:
            source._search('test query')

            call_kwargs = mock_get.call_args
            headers = call_kwargs.kwargs.get('headers', call_kwargs[1].get('headers', {}))
            assert headers['X-Subscription-Token'] == 'BSA-test-key-12345'
            assert headers['Accept'] == 'application/json'

    def test_search_sends_correct_params(self, source):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'results': []}
        mock_resp.raise_for_status = MagicMock()

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp) as mock_get:
            source._search('AI marketplace')

            call_kwargs = mock_get.call_args
            params = call_kwargs.kwargs.get('params', call_kwargs[1].get('params', {}))
            assert params['q'] == 'AI marketplace'
            assert params['count'] == 5
            assert params['freshness'] == 'pw'

    def test_search_rate_limit_raises(self, source):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {'Retry-After': '1'}

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp):
            with patch('research_agent.sources.web_search.time.sleep'):
                with pytest.raises(requests.RequestException):
                    source._search('test')


class TestFetchFullArticle:
    """Test full article content fetching."""

    def test_extracts_article_content(self, source):
        html = """
        <html><body>
        <nav>Navigation</nav>
        <article>
            <h1>Article Title Goes Here For Testing</h1>
            <p>This is a paragraph with enough text to pass the length filter easily.</p>
            <p>Another paragraph with substantial content for extraction testing.</p>
        </article>
        <footer>Footer content</footer>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()

        with patch('research_agent.sources.web_search.requests.get', return_value=mock_resp):
            content = source._fetch_full_article('https://example.com/article', 'Test')

        assert 'Article Title Goes Here' in content
        assert 'enough text to pass' in content
        assert 'Navigation' not in content
        assert 'Footer' not in content

    def test_returns_empty_on_failure(self, source):
        with patch('research_agent.sources.web_search.requests.get', side_effect=requests.ConnectionError):
            content = source._fetch_full_article('https://bad-url.example.com', 'Test')

        assert content == ''

    def test_fetch_used_in_result_to_item(self, source):
        """Full article content should be used when longer than description."""
        result = {
            'url': 'https://example.com/article',
            'title': 'Test Article',
            'description': 'Short desc.',
            'meta_url': {'hostname': 'example.com'},
        }

        long_article = 'A' * 200  # Much longer than description

        with patch.object(source, '_fetch_full_article', return_value=long_article):
            item = source._result_to_item(result, 'test query')

        assert item['content'] == long_article
