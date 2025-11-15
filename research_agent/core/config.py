"""Configuration management."""

import yaml
from pathlib import Path
from typing import Any, Dict
from dataclasses import dataclass, field
from dotenv import load_dotenv
import os


class DotDict(dict):
    """Dict with dot notation access."""

    def __getattr__(self, key):
        try:
            value = self[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        except KeyError:
            raise AttributeError(f"No attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


@dataclass
class Config:
    """Research agent configuration."""

    paths: DotDict
    schedule: DotDict
    model: DotDict
    research: DotDict
    output: DotDict
    sources: DotDict
    learning: DotDict
    notifications: DotDict
    dev: DotDict

    @classmethod
    def load(cls, config_path: Path = None) -> 'Config':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file (default: ~/.research-agent/config.yaml)

        Returns:
            Config object
        """
        if config_path is None:
            config_path = Path.home() / '.research-agent' / 'config.yaml'
        else:
            config_path = Path(config_path)

        # Load environment variables
        env_path = config_path.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)

        # Load YAML config
        if config_path.exists():
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
        else:
            # Use default config
            config_data = cls._get_default_config()

        # Convert to DotDict for easy access
        return cls(
            paths=DotDict(config_data.get('paths', {})),
            schedule=DotDict(config_data.get('schedule', {})),
            model=DotDict(config_data.get('model', {})),
            research=DotDict(config_data.get('research', {})),
            output=DotDict(config_data.get('output', {})),
            sources=DotDict(config_data.get('sources', {})),
            learning=DotDict(config_data.get('learning', {})),
            notifications=DotDict(config_data.get('notifications', {})),
            dev=DotDict(config_data.get('dev', {}))
        )

    @classmethod
    def load_default(cls) -> 'Config':
        """Load default configuration."""
        return cls.load()

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'version': '1.0',
            'paths': {
                'data_dir': '~/.research-agent',
                'output_dir': '~/Documents/Obsidian/Research/Digests',
                'prompts_dir': '~/.research-agent/prompts',
                'logs_dir': '~/.research-agent/logs',
            },
            'schedule': {
                'interval': '0 7 * * *',
                'timezone': 'America/Denver',
                'retry': {
                    'enabled': True,
                    'max_attempts': 3,
                    'backoff_minutes': [5, 15, 30],
                },
            },
            'model': {
                'name': 'claude-sonnet-4-20250514',
                'fallback': 'claude-sonnet-4-20250514',
                'max_tokens': 16000,
                'temperature': 0.3,
                'api': {
                    'timeout_seconds': 300,
                    'max_retries': 3,
                },
            },
            'research': {
                'target_items': 10,
                'min_items': 3,
                'max_items': 15,
                'lookback_hours': 24,
                'dedup': {
                    'exact_url': True,
                    'title_similarity': 0.85,
                    'content_hash': True,
                    'fts_enabled': True,
                    'fts_min_score': 0.7,
                },
            },
            'output': {
                'filename_pattern': '{year}-{month:02d}-{day:02d}-research-digest.md',
                'dir_structure': 'year/month',
                'metadata': {
                    'frontmatter': True,
                    'tags': ['research', 'ai', 'daily-digest'],
                    'source_attribution': True,
                    'runtime_stats': True,
                },
                'obsidian': {
                    'use_wikilinks': True,
                    'tag_format': '#ai/research',
                },
            },
            'sources': {
                'arxiv': {
                    'enabled': True,
                    'categories': ['cs.AI', 'cs.LG', 'cs.CL', 'cs.HC'],
                    'max_results': 20,
                },
                'hackernews': {
                    'enabled': True,
                    'endpoints': ['topstories', 'beststories'],
                    'max_items': 30,
                    'filter_keywords': [
                        'AI', 'LLM', 'agent', 'GPT', 'Claude', 'machine learning'
                    ],
                },
                'rss': {
                    'enabled': True,
                    'feeds': [
                        {
                            'url': 'https://www.anthropic.com/news/rss',
                            'name': 'Anthropic News',
                        },
                    ],
                },
                'blogs': {
                    'enabled': False,
                    'urls': [],
                },
            },
            'learning': {
                'enabled': False,
                'tracking': {
                    'file_access': True,
                    'obsidian_api': False,
                },
                'adaptation': {
                    'min_samples': 20,
                    'learning_rate': 0.1,
                    'rerank_sources': True,
                },
            },
            'notifications': {
                'enabled': False,
                'on_success': {
                    'enabled': False,
                    'method': 'none',
                },
                'on_failure': {
                    'enabled': True,
                    'method': 'log',
                },
            },
            'dev': {
                'dry_run': False,
                'verbose': False,
                'debug': False,
            },
        }

    def to_yaml(self) -> str:
        """Convert config to YAML string."""
        config_dict = {
            'paths': dict(self.paths),
            'schedule': dict(self.schedule),
            'model': dict(self.model),
            'research': dict(self.research),
            'output': dict(self.output),
            'sources': dict(self.sources),
            'learning': dict(self.learning),
            'notifications': dict(self.notifications),
            'dev': dict(self.dev),
        }
        return yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
