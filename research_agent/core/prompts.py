"""Prompt template management."""

from pathlib import Path
from typing import Dict


class PromptManager:
    """
    Manage prompt templates.

    Loads markdown prompt files and provides access to them.
    """

    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir).expanduser()
        self._prompts_cache: Dict[str, str] = {}

    def get_system_prompt(self) -> str:
        """Get system prompt."""
        return self._load_prompt('system.md')

    def get_sources_prompt(self) -> str:
        """Get sources strategy prompt."""
        return self._load_prompt('sources.md')

    def get_synthesis_template(self) -> str:
        """Get synthesis template."""
        return self._load_prompt('synthesis.md')

    def _load_prompt(self, filename: str) -> str:
        """
        Load prompt from file.

        Args:
            filename: Prompt filename

        Returns:
            Prompt content
        """
        # Check cache first
        if filename in self._prompts_cache:
            return self._prompts_cache[filename]

        # Load from file
        prompt_path = self.prompts_dir / filename

        if not prompt_path.exists():
            print(f"Warning: Prompt file not found: {prompt_path}")
            return ""

        content = prompt_path.read_text()

        # Cache it
        self._prompts_cache[filename] = content

        return content

    def reload(self):
        """Reload all prompts from disk."""
        self._prompts_cache.clear()
