"""CLI main entry point."""

import click
from pathlib import Path
import sys

from research_agent.core.config import Config
from research_agent.core.orchestrator import ResearchOrchestrator
from research_agent.storage.state import StateManager
from research_agent.utils.logger import setup_logger


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Research Agent - Automated AI research tracking."""
    pass


@cli.command()
@click.option('--dry-run', is_flag=True, help='Run without writing outputs')
@click.option('--verbose', is_flag=True, help='Verbose logging')
@click.option('--config', type=click.Path(), help='Custom config file')
def run(dry_run, verbose, config):
    """Execute research cycle."""
    try:
        # Load config
        if config:
            config_obj = Config.load(Path(config))
        else:
            config_obj = Config.load_default()

        # Validate API key (Issue #3 - Critical Fix)
        import os
        if not os.getenv('ANTHROPIC_API_KEY'):
            click.secho("Error: ANTHROPIC_API_KEY not found in environment", fg='red', err=True)
            click.echo("Please add your API key to ~/.research-agent/.env")
            click.echo("Example: ANTHROPIC_API_KEY=sk-ant-your-key-here")
            sys.exit(1)

        # Override dev settings
        if verbose:
            config_obj.dev['verbose'] = True

        if dry_run:
            config_obj.dev['dry_run'] = True
            click.echo("Running in DRY RUN mode (no outputs will be written)")

        # Initialize logging
        log_dir = Path(config_obj.paths.logs_dir).expanduser()
        setup_logger(
            name="research_agent",
            log_dir=log_dir,
            verbose=verbose
        )

        # Run orchestrator
        orchestrator = ResearchOrchestrator(config_obj)
        result = orchestrator.run(dry_run=dry_run)

        # Print result
        click.echo()
        click.echo("=" * 60)
        click.secho(f"Research run completed: {result.status}",
                    fg='green' if result.status == 'success' else 'yellow')
        click.echo("=" * 60)
        click.echo(f"  Items found:    {result.items_found}")
        click.echo(f"  New items:      {result.items_new}")
        click.echo(f"  Included:       {result.items_included}")
        click.echo(f"  Runtime:        {result.runtime_seconds:.2f}s")

        if result.output_path:
            click.echo(f"  Output:         {result.output_path}")

        if result.error_log:
            click.secho(f"  Errors:         {result.error_log}", fg='red', err=True)

        # Exit with appropriate code
        sys.exit(0 if result.status == 'success' else 1)

    except Exception as e:
        click.secho(f"Fatal error: {e}", fg='red', err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.group()
def config():
    """Manage configuration and prompts."""
    pass


@config.command()
@click.argument('component', type=click.Choice(['system', 'sources', 'synthesis']))
def edit(component):
    """Edit prompt templates."""
    import os

    config_obj = Config.load_default()
    prompt_path = Path(config_obj.paths.prompts_dir).expanduser() / f"{component}.md"

    if not prompt_path.exists():
        click.secho(f"Prompt file not found: {prompt_path}", fg='red', err=True)
        click.echo(f"Create it first with: mkdir -p {prompt_path.parent}")
        sys.exit(1)

    # Open in $EDITOR
    editor = os.environ.get('EDITOR', 'vim')
    os.system(f"{editor} {prompt_path}")


@config.command()
def show():
    """Show current configuration."""
    config_obj = Config.load_default()
    click.echo(config_obj.to_yaml())


@config.command()
def path():
    """Show config file path."""
    config_path = Path.home() / '.research-agent' / 'config.yaml'
    click.echo(str(config_path))


@cli.group()
def schedule():
    """Manage scheduled execution."""
    pass


@schedule.command()
def install():
    """Install launchd job."""
    try:
        from research_agent.scheduler.launchd import install_launchd
        install_launchd()
        click.secho("✓ Scheduled job installed", fg='green')
    except Exception as e:
        click.secho(f"Error installing schedule: {e}", fg='red', err=True)
        sys.exit(1)


@schedule.command()
def uninstall():
    """Uninstall launchd job."""
    try:
        from research_agent.scheduler.launchd import uninstall_launchd
        uninstall_launchd()
        click.secho("✓ Scheduled job removed", fg='green')
    except Exception as e:
        click.secho(f"Error uninstalling schedule: {e}", fg='red', err=True)
        sys.exit(1)


@schedule.command()
def status():
    """Check schedule status."""
    try:
        from research_agent.scheduler.launchd import check_status
        status_str = check_status()
        if status_str == "loaded":
            click.secho(f"Status: {status_str}", fg='green')
        else:
            click.secho(f"Status: {status_str}", fg='yellow')
    except Exception as e:
        click.secho(f"Error checking status: {e}", fg='red', err=True)
        sys.exit(1)


@cli.group()
def history():
    """View research history."""
    pass


@history.command()
@click.option('--last', type=int, default=10, help='Last N runs')
def runs(last):
    """Show recent research runs."""
    try:
        config_obj = Config.load_default()
        data_dir = Path(config_obj.paths.data_dir).expanduser()
        state = StateManager(data_dir / "state.db")

        recent = state.get_recent_runs(limit=last)

        if not recent:
            click.echo("No runs found")
            return

        click.echo()
        click.echo("Recent research runs:")
        click.echo("=" * 80)

        for run in recent:
            status_color = 'green' if run['status'] == 'success' else 'red'
            click.secho(f"{run['timestamp']} - {run['status']}", fg=status_color)
            click.echo(f"  Items: {run['items_included']}/{run['items_new']}/{run['items_found']} (included/new/found)")
            if run['output_path']:
                click.echo(f"  Output: {run['output_path']}")
            click.echo()

    except Exception as e:
        click.secho(f"Error fetching history: {e}", fg='red', err=True)
        sys.exit(1)


@history.command()
@click.argument('query')
@click.option('--limit', type=int, default=20, help='Max results')
def search(query, limit):
    """Search historical items."""
    try:
        config_obj = Config.load_default()
        data_dir = Path(config_obj.paths.data_dir).expanduser()
        state = StateManager(data_dir / "state.db")

        results = state.search_history(query, limit=limit)

        if not results:
            click.echo(f"No results found for: {query}")
            return

        click.echo()
        click.echo(f"Search results for: {query}")
        click.echo("=" * 80)

        for item in results:
            click.secho(f"\n{item['title']}", fg='blue', bold=True)
            click.echo(f"  URL: {item['url']}")
            click.echo(f"  Source: {item['source']}")
            click.echo(f"  Date: {item['first_seen']}")
            if item.get('snippet_html'):
                # Strip HTML tags for terminal display
                from research_agent.utils.text import clean_html
                snippet = clean_html(item['snippet_html'])
                click.echo(f"  {snippet}")

    except Exception as e:
        click.secho(f"Error searching: {e}", fg='red', err=True)
        sys.exit(1)


@cli.group()
def authors():
    """Manage author tracking and performance."""
    pass


@authors.command()
def seed():
    """Seed author performance from existing database items."""
    try:
        config_obj = Config.load_default()
        data_dir = Path(config_obj.paths.data_dir).expanduser()

        # Initialize logging
        log_dir = Path(config_obj.paths.logs_dir).expanduser()
        setup_logger(
            name="research_agent",
            log_dir=log_dir,
            verbose=True
        )

        state = StateManager(data_dir / "state.db")

        click.echo("Seeding author performance from existing database...")
        state.seed_authors_from_existing_items()
        click.secho("✓ Author seeding complete", fg='green')

    except Exception as e:
        click.secho(f"Error seeding authors: {e}", fg='red', err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@authors.command()
@click.option('--limit', type=int, default=20, help='Number of authors to show')
@click.option('--min-rate', type=float, default=0.0, help='Minimum inclusion rate (0.0-1.0)')
def top(limit, min_rate):
    """Show top-performing authors."""
    try:
        config_obj = Config.load_default()
        data_dir = Path(config_obj.paths.data_dir).expanduser()
        state = StateManager(data_dir / "state.db")

        top_authors = state.get_top_authors(
            limit=limit,
            min_inclusion_rate=min_rate,
            min_papers=1
        )

        if not top_authors:
            click.echo("No authors found")
            return

        click.echo()
        click.echo(f"Top {len(top_authors)} authors:")
        click.echo("=" * 80)

        for author_name in top_authors:
            stats = state.get_author_stats(author_name)
            if stats:
                inclusion_pct = stats['inclusion_rate'] * 100
                click.secho(f"\n{author_name}", fg='blue', bold=True)
                click.echo(f"  Papers: {stats['total_papers']} total, {stats['included_papers']} included ({inclusion_pct:.1f}%)")
                click.echo(f"  Recency score: {stats['recency_score']:.3f}")
                click.echo(f"  Velocity: {stats['recent_velocity']:.2f} papers/month")
                if stats['last_included']:
                    click.echo(f"  Last included: {stats['last_included']}")

        click.echo()

    except Exception as e:
        click.secho(f"Error fetching top authors: {e}", fg='red', err=True)
        sys.exit(1)


@authors.command()
@click.argument('author_name')
def stats(author_name):
    """Show detailed stats for a specific author."""
    try:
        config_obj = Config.load_default()
        data_dir = Path(config_obj.paths.data_dir).expanduser()
        state = StateManager(data_dir / "state.db")

        author_stats = state.get_author_stats(author_name)

        if not author_stats:
            click.secho(f"No data found for author: {author_name}", fg='yellow')
            return

        click.echo()
        click.secho(f"Author: {author_stats['author_name']}", fg='blue', bold=True)
        click.echo("=" * 80)
        click.echo(f"  Total papers:      {author_stats['total_papers']}")
        click.echo(f"  Included papers:   {author_stats['included_papers']}")
        click.echo(f"  Inclusion rate:    {author_stats['inclusion_rate'] * 100:.1f}%")
        click.echo(f"  Recency score:     {author_stats['recency_score']:.3f}")
        click.echo(f"  Velocity:          {author_stats['recent_velocity']:.2f} papers/month")
        click.echo(f"  First seen:        {author_stats['first_seen']}")
        click.echo(f"  Last seen:         {author_stats['last_seen']}")
        if author_stats['last_included']:
            click.echo(f"  Last included:     {author_stats['last_included']}")
        click.echo()

    except Exception as e:
        click.secho(f"Error fetching author stats: {e}", fg='red', err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
