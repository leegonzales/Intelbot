"""Digest writer for markdown output."""

from pathlib import Path
from datetime import datetime
from typing import Optional


class DigestWriter:
    """
    Write research digest to markdown file.

    Handles:
    - Directory structure (year/month)
    - File naming
    - Metadata formatting
    """

    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.paths.output_dir).expanduser()

    def write(self, content: str, date: Optional[datetime] = None) -> Path:
        """
        Write digest content to file.

        Args:
            content: Markdown content
            date: Date for digest (default: today)

        Returns:
            Path to written file
        """
        if date is None:
            date = datetime.now()

        # Build output path based on dir_structure config
        output_path = self._build_output_path(date)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        output_path.write_text(content)

        print(f"Digest written to: {output_path}")

        return output_path

    def _build_output_path(self, date: datetime) -> Path:
        """Build output file path based on config."""
        # Get filename pattern from config
        filename_pattern = self.config.output.get(
            'filename_pattern',
            '{year}-{month:02d}-{day:02d}-research-digest.md'
        )

        # Format filename
        filename = filename_pattern.format(
            year=date.year,
            month=date.month,
            day=date.day
        )

        # Get directory structure
        dir_structure = self.config.output.get('dir_structure', 'year/month')

        # Build path
        if dir_structure == 'flat':
            output_path = self.output_dir / filename

        elif dir_structure == 'year':
            output_path = self.output_dir / str(date.year) / filename

        elif dir_structure == 'year/month':
            output_path = self.output_dir / str(date.year) / f"{date.month:02d}" / filename

        else:
            # Default to flat
            output_path = self.output_dir / filename

        return output_path
