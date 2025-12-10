"""Changelog source collector for AI CLI tools."""

import re
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from research_agent.sources.base import ResearchSource
from research_agent.utils.text import extract_snippet
from research_agent.utils.retry import retry
from research_agent.utils.logger import get_logger


class ChangelogSource(ResearchSource):
    """
    Collect changelog entries from AI CLI tools.

    Supports:
    - Claude Code (Anthropic)
    - Codex CLI (OpenAI)
    - Gemini CLI (Google)
    """

    # Default changelog sources configuration
    DEFAULT_SOURCES = [
        {
            'name': 'Claude Code',
            'vendor': 'Anthropic',
            'url': 'https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md',
            'repo_url': 'https://github.com/anthropics/claude-code',
            'type': 'markdown',
            'tier': 5,  # Implementation tier for tools/libraries
            'priority': 'high',
        },
        {
            'name': 'Codex CLI',
            'vendor': 'OpenAI',
            'url': 'https://api.github.com/repos/openai/codex/releases',
            'repo_url': 'https://github.com/openai/codex',
            'type': 'github_releases',
            'tier': 5,
            'priority': 'high',
        },
        {
            'name': 'Gemini CLI',
            'vendor': 'Google',
            'url': 'https://raw.githubusercontent.com/google-gemini/gemini-cli/main/docs/changelogs/index.md',
            'repo_url': 'https://github.com/google-gemini/gemini-cli',
            'type': 'markdown',
            'tier': 5,
            'priority': 'high',
        },
    ]

    def __init__(self, config):
        super().__init__(config)
        self.logger = get_logger("sources.changelog")
        self.days_lookback = config.get('days_lookback', 30)
        self.max_entries_per_tool = config.get('max_entries_per_tool', 3)

    @retry(max_attempts=3, backoff_base=2.0, exceptions=(Exception,))
    def fetch(self) -> List[Dict]:
        """
        Fetch changelog entries from configured CLI tools.

        Returns:
            List of changelog items
        """
        items = []

        # Get sources from config or use defaults
        sources = self.config.get('sources', self.DEFAULT_SOURCES)

        for source_config in sources:
            if not source_config.get('enabled', True):
                continue

            try:
                source_items = self._fetch_source(source_config)
                items.extend(source_items)
                self.logger.info(f"Fetched {len(source_items)} entries from {source_config['name']}")
            except Exception as e:
                self.logger.error(f"Error fetching changelog from {source_config['name']}: {e}")
                continue

        return items

    def _fetch_source(self, source_config: Dict) -> List[Dict]:
        """Fetch changelog entries from a single source."""
        source_type = source_config.get('type', 'markdown')

        if source_type == 'markdown':
            return self._fetch_markdown_changelog(source_config)
        elif source_type == 'github_releases':
            return self._fetch_github_releases(source_config)
        else:
            self.logger.warning(f"Unknown source type: {source_type}")
            return []

    def _fetch_markdown_changelog(self, source_config: Dict) -> List[Dict]:
        """Parse markdown-based changelog files."""
        items = []

        response = requests.get(
            source_config['url'],
            timeout=30,
            headers={'User-Agent': 'ResearchAgent/1.0'}
        )
        response.raise_for_status()

        content = response.text
        entries = self._parse_markdown_changelog(content, source_config)

        # Limit entries
        return entries[:self.max_entries_per_tool]

    def _parse_markdown_changelog(self, content: str, source_config: Dict) -> List[Dict]:
        """Parse a markdown changelog into individual version entries."""
        items = []
        tool_name = source_config['name']
        vendor = source_config.get('vendor', '')
        repo_url = source_config.get('repo_url', '')
        tier = source_config.get('tier', 5)
        priority = source_config.get('priority', 'medium')

        # Match version headers - handles formats like:
        # ## 2.0.64
        # ## v1.2.3
        # ## Announcements: v0.1.28 - 2025-06-24
        # ## [1.0.0] - 2025-01-15
        version_pattern = r'^##\s+(?:Announcements:\s+)?(?:\[)?v?(\d+\.\d+(?:\.\d+)?(?:-[\w.]+)?)(?:\])?\s*(?:-\s*(\d{4}-\d{2}-\d{2}))?'

        lines = content.split('\n')
        current_version = None
        current_date = None
        current_content = []

        for line in lines:
            version_match = re.match(version_pattern, line)

            if version_match:
                # Save previous entry if exists
                if current_version and current_content:
                    item = self._create_changelog_item(
                        tool_name=tool_name,
                        vendor=vendor,
                        version=current_version,
                        content='\n'.join(current_content),
                        published_date=current_date,
                        repo_url=repo_url,
                        tier=tier,
                        priority=priority
                    )
                    if item:
                        items.append(item)

                # Start new entry
                current_version = version_match.group(1)
                date_str = version_match.group(2)
                current_date = self._parse_date(date_str) if date_str else None
                current_content = []
            elif current_version:
                # Skip empty lines at the start of content
                if current_content or line.strip():
                    current_content.append(line)

        # Don't forget the last entry
        if current_version and current_content:
            item = self._create_changelog_item(
                tool_name=tool_name,
                vendor=vendor,
                version=current_version,
                content='\n'.join(current_content),
                published_date=current_date,
                repo_url=repo_url,
                tier=tier,
                priority=priority
            )
            if item:
                items.append(item)

        return items

    def _fetch_github_releases(self, source_config: Dict) -> List[Dict]:
        """Fetch changelog from GitHub releases API."""
        items = []
        tool_name = source_config['name']
        vendor = source_config.get('vendor', '')
        repo_url = source_config.get('repo_url', '')
        tier = source_config.get('tier', 5)
        priority = source_config.get('priority', 'medium')

        headers = {
            'User-Agent': 'ResearchAgent/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }

        # Add GitHub token if available
        github_token = self.config.get('github_token')
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        response = requests.get(
            source_config['url'],
            timeout=30,
            headers=headers
        )
        response.raise_for_status()

        releases = response.json()

        # Filter to non-prerelease versions (or include alpha/beta if configured)
        include_prereleases = self.config.get('include_prereleases', False)

        count = 0
        for release in releases:
            if count >= self.max_entries_per_tool:
                break

            # Skip prereleases unless configured
            if release.get('prerelease', False) and not include_prereleases:
                continue

            version = release.get('tag_name', '').lstrip('v').replace('rust-v', '')
            body = release.get('body', '')
            published_at = release.get('published_at', '')
            html_url = release.get('html_url', '')

            # Skip releases with empty body
            if not body or len(body.strip()) < 20:
                continue

            published_date = None
            if published_at:
                try:
                    published_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                except ValueError:
                    pass

            item = self._create_changelog_item(
                tool_name=tool_name,
                vendor=vendor,
                version=version,
                content=body,
                published_date=published_date,
                repo_url=repo_url,
                release_url=html_url,
                tier=tier,
                priority=priority
            )

            if item:
                items.append(item)
                count += 1

        return items

    def _create_changelog_item(
        self,
        tool_name: str,
        vendor: str,
        version: str,
        content: str,
        published_date: Optional[datetime],
        repo_url: str,
        release_url: str = None,
        tier: int = 5,
        priority: str = 'medium'
    ) -> Optional[Dict]:
        """Create a standardized changelog item."""

        # Filter by date if we have one
        if published_date:
            cutoff_date = datetime.now(published_date.tzinfo) if published_date.tzinfo else datetime.now()
            cutoff_date = cutoff_date - timedelta(days=self.days_lookback)
            if published_date < cutoff_date:
                return None

        # Clean and format content
        content_clean = content.strip()

        # Generate snippet (first 500 chars of meaningful content)
        snippet = self._generate_snippet(content_clean)

        # Build URL - prefer release URL, fall back to repo URL with version anchor
        url = release_url or f"{repo_url}/blob/main/CHANGELOG.md"

        # Create title
        title = f"{tool_name} v{version}"
        if vendor:
            title = f"{tool_name} v{version} ({vendor})"

        return self._create_item(
            url=url,
            title=title,
            source=f"changelog:{tool_name.lower().replace(' ', '-')}",
            snippet=snippet,
            content=content_clean,
            source_metadata={
                'tool_name': tool_name,
                'vendor': vendor,
                'version': version,
                'repo_url': repo_url,
                'tier': tier,
                'priority': priority,
                'type': 'cli_changelog',
            },
            published_date=published_date,
            author=vendor,
            category='ai-tools',
            tags=self._extract_tags(tool_name, vendor, content_clean)
        )

    def _generate_snippet(self, content: str) -> str:
        """Generate a meaningful snippet from changelog content."""
        # Remove markdown formatting for cleaner snippet
        cleaned = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)
        cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)

        # Get first meaningful lines
        lines = [l.strip() for l in cleaned.split('\n') if l.strip()]
        snippet_lines = []
        char_count = 0

        for line in lines:
            if char_count + len(line) > 500:
                break
            # Skip lines that are just bullet points without content
            if line in ['-', '*', '•']:
                continue
            snippet_lines.append(line)
            char_count += len(line) + 1

        return ' '.join(snippet_lines)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string from changelog."""
        if not date_str:
            return None

        formats = [
            '%Y-%m-%d',
            '%B %d, %Y',
            '%d %B %Y',
            '%Y/%m/%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None

    def _extract_tags(self, tool_name: str, vendor: str, content: str) -> List[str]:
        """Extract relevant tags from changelog entry."""
        tags = ['changelog', 'cli-tools', 'ai-tools']

        # Add tool-specific tags
        tool_tag = tool_name.lower().replace(' ', '-')
        tags.append(tool_tag)

        if vendor:
            tags.append(vendor.lower())

        # Extract feature keywords
        content_lower = content.lower()
        feature_keywords = {
            'mcp': 'mcp',
            'model context protocol': 'mcp',
            'hooks': 'hooks',
            'agent': 'agent',
            'terminal': 'terminal',
            'vscode': 'vscode',
            'ide': 'ide',
            'api': 'api',
            'streaming': 'streaming',
            'tool': 'tool-use',
            'context': 'context',
            'memory': 'memory',
            'session': 'session',
        }

        for keyword, tag in feature_keywords.items():
            if keyword in content_lower and tag not in tags:
                tags.append(tag)

        return list(set(tags))
