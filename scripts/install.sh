#!/bin/bash
# Installation script for Research Agent

set -e

echo "=========================================="
echo "Installing Research Agent..."
echo "=========================================="
echo

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d ' ' -f 2)
required_version="3.10"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "Error: Python 3.10+ required (found $python_version)"
    exit 1
fi

echo "✓ Python $python_version detected"
echo

# Install package
echo "Installing package..."
pip install -e . || {
    echo "Error: Failed to install package"
    exit 1
}

echo "✓ Package installed"
echo

# Create config directory
echo "Setting up configuration directory..."
mkdir -p ~/.research-agent/{prompts,logs}

echo "✓ Created ~/.research-agent/"
echo

# Copy default prompts
echo "Installing default prompts..."
cp prompts/*.md ~/.research-agent/prompts/

echo "✓ Prompts installed"
echo

# Create default config
echo "Creating default configuration..."
cat > ~/.research-agent/config.yaml <<'EOF'
# Research Agent Configuration
version: "1.0"

paths:
  data_dir: "~/.research-agent"
  output_dir: "~/Documents/Obsidian/Research/Digests"
  prompts_dir: "~/.research-agent/prompts"
  logs_dir: "~/.research-agent/logs"

schedule:
  interval: "0 7 * * *"
  timezone: "America/Denver"

model:
  name: "claude-sonnet-4-20250514"
  max_tokens: 16000
  temperature: 0.3

research:
  target_items: 10
  min_items: 3
  max_items: 15

output:
  filename_pattern: "{year}-{month:02d}-{day:02d}-research-digest.md"
  dir_structure: "year/month"

sources:
  arxiv:
    enabled: true
    categories: ["cs.AI", "cs.LG", "cs.CL", "cs.HC"]
    max_results: 20

  hackernews:
    enabled: true
    endpoints: ["topstories", "beststories"]
    max_items: 30
    filter_keywords:
      - "AI"
      - "LLM"
      - "agent"
      - "GPT"
      - "Claude"
      - "machine learning"

  rss:
    enabled: true
    feeds:
      - url: "https://www.anthropic.com/news/rss"
        name: "Anthropic News"

  blogs:
    enabled: false
    urls: []
EOF

echo "✓ Configuration created"
echo

# Create .env template
echo "Creating .env template..."
cat > ~/.research-agent/.env.example <<'EOF'
# Anthropic API Key (required)
ANTHROPIC_API_KEY=your-api-key-here
EOF

# Check if .env already exists
if [ ! -f ~/.research-agent/.env ]; then
    cp ~/.research-agent/.env.example ~/.research-agent/.env
    echo "✓ Created .env file (please add your API key)"
else
    echo "✓ .env file already exists"
fi

echo

# Create output directory
echo "Creating output directory..."
mkdir -p ~/Documents/Obsidian/Research/Digests

echo "✓ Output directory created"
echo

# Summary
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Add your Anthropic API key to ~/.research-agent/.env"
echo "2. Configure Obsidian vault path in ~/.research-agent/config.yaml"
echo "3. Test with: research-agent run --dry-run"
echo "4. Enable scheduling: research-agent schedule install"
echo
echo "For help: research-agent --help"
echo
