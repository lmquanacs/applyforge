import click
from codelens import __version__
from codelens.config.parser import load_config
from codelens.agents.coordinator_agent import CoordinatorAgent


@click.group()
@click.version_option(__version__)
def cli():
    """CodeLens CLI - Intelligent project scanner and report generator."""
    pass


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("-c", "--config", "config_path", default=None, help="Path to codelens.config.yaml")
@click.option("-o", "--output", default=None, help="Output markdown file path")
@click.option("--hint", default=None, help="Framework hint (e.g. spring-boot, django, react)")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Stream agent logs")
@click.option("--dry-run", is_flag=True, default=False, help="Estimate token usage without calling APIs")
def scan(path, config_path, output, hint, verbose, dry_run):
    """Scan a project directory and generate a Markdown summary report."""
    config = load_config(config_path, overrides={"output_file": output, "project_hint": hint})

    if verbose:
        click.echo(f"Scanning: {path}")
        click.echo(f"Hint: {config.get('project_hint', 'auto')}")
        click.echo(f"Model: {config['agents']['coordinator']['model']}")

    coordinator = CoordinatorAgent(config=config, verbose=verbose, dry_run=dry_run)
    coordinator.run(path)


def main():
    cli()
