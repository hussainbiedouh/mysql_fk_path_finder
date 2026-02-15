"""Click-based command-line interface for FK Path Finder."""

import json
import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from fk_path_finder.types import Config
from fk_path_finder.finder import FKPathFinder, FKPathFinderError


@click.command()
@click.option(
    "--host",
    "-h",
    help="MySQL host (default: localhost or FK_MYSQL_HOST env var)"
)
@click.option(
    "--port",
    "-p",
    type=int,
    help="MySQL port (default: 3306 or FK_MYSQL_PORT env var)"
)
@click.option(
    "--user",
    "-u",
    help="MySQL user (default: FK_MYSQL_USER env var)"
)
@click.option(
    "--password",
    "-P",
    help="MySQL password (default: FK_MYSQL_PASSWORD env var)"
)
@click.option(
    "--database",
    "-d",
    help="MySQL database (default: FK_MYSQL_DATABASE env var)"
)
@click.option(
    "--config",
    "-c",
    "config_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to JSON configuration file"
)
@click.option(
    "--from",
    "from_ref",
    help="Starting reference (table or table.column) for batch mode"
)
@click.option(
    "--to",
    "to_ref",
    help="Ending reference (table or table.column) for batch mode"
)
@click.option(
    "--max-paths",
    type=int,
    default=1000,
    help="Maximum number of paths to find (default: 1000)"
)
@click.option(
    "--max-hops",
    type=int,
    default=6,
    help="Maximum path length in hops (default: 6)"
)
@click.option(
    "--plain",
    is_flag=True,
    help="Use plain text output instead of rich formatting"
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Force interactive mode"
)
@click.version_option(version="0.1.0", prog_name="fk-finder")
def main(
    host: Optional[str],
    port: Optional[int],
    user: Optional[str],
    password: Optional[str],
    database: Optional[str],
    config_file: Optional[str],
    from_ref: Optional[str],
    to_ref: Optional[str],
    max_paths: int,
    max_hops: int,
    plain: bool,
    interactive: bool
) -> None:
    """FK Path Finder - Discover paths between tables via foreign keys.
    
    Examples:
    
        \b
        # Interactive mode (default)
        fk-finder
    
        \b
        # With connection parameters
        fk-finder --host localhost --port 3306 --user root --database sakila
    
        \b
        # Batch mode with specific path query
        fk-finder --database sakila --from film --to actor
    
        \b
        # Using a config file
        fk-finder --config config.json --from film_actor --to actor
    
        \b
        # Using environment variables
        export FK_MYSQL_HOST=localhost
        export FK_MYSQL_USER=root
        export FK_MYSQL_DATABASE=sakila
        fk-finder --from film --to actor
    """
    console = Console(force_terminal=not plain)
    
    # Load configuration
    config = load_config(
        config_file=config_file,
        cli_host=host,
        cli_port=port,
        cli_user=user,
        cli_password=password,
        cli_database=database,
        cli_max_paths=max_paths,
        cli_max_hops=max_hops
    )
    
    # Determine mode
    is_batch = from_ref is not None and to_ref is not None
    
    if interactive or (not is_batch and not config.user):
        # Interactive mode
        run_interactive(config, console)
    elif is_batch:
        # Batch mode
        run_batch(config, console, from_ref, to_ref, plain)
    else:
        # Need references for batch mode
        console.print(
            "[bold red]Error:[/bold red] In non-interactive mode, "
            "both --from and --to are required."
        )
        console.print("\nUse --interactive for interactive mode, or provide --from and --to.")
        sys.exit(1)


def load_config(
    config_file: Optional[str] = None,
    cli_host: Optional[str] = None,
    cli_port: Optional[int] = None,
    cli_user: Optional[str] = None,
    cli_password: Optional[str] = None,
    cli_database: Optional[str] = None,
    cli_max_paths: int = 1000,
    cli_max_hops: int = 6
) -> Config:
    """Load configuration from file, environment, and CLI arguments.
    
    Priority: CLI args > Config file > Environment vars > Defaults
    
    Args:
        config_file: Path to JSON config file.
        cli_host: CLI host argument.
        cli_port: CLI port argument.
        cli_user: CLI user argument.
        cli_password: CLI password argument.
        cli_database: CLI database argument.
        cli_max_paths: CLI max_paths argument.
        cli_max_hops: CLI max_hops argument.
        
    Returns:
        Config object.
    """
    # Start with environment variables
    config = Config.from_env()
    
    # Override with config file if provided
    if config_file:
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
            config = Config.from_dict({
                "host": file_config.get("host", config.host),
                "port": file_config.get("port", config.port),
                "user": file_config.get("user", config.user),
                "password": file_config.get("password", config.password),
                "database": file_config.get("database", config.database),
                "max_path_length": file_config.get("max_path_length", config.max_path_length),
                "max_paths": file_config.get("max_paths", config.max_paths),
                "display_limit": file_config.get("display_limit", config.display_limit),
            })
        except (json.JSONDecodeError, KeyError, IOError) as e:
            click.echo(f"Error loading config file: {e}", err=True)
            sys.exit(1)
    
    # Override with CLI arguments
    if cli_host:
        config.host = cli_host
    if cli_port:
        config.port = cli_port
    if cli_user:
        config.user = cli_user
    if cli_password:
        config.password = cli_password
    if cli_database:
        config.database = cli_database
    if cli_max_paths:
        config.max_paths = cli_max_paths
    if cli_max_hops:
        config.max_path_length = cli_max_hops
    
    return config


def run_interactive(config: Config, console: Console) -> None:
    """Run in interactive mode.
    
    Args:
        config: Configuration object.
        console: Rich console instance.
    """
    from fk_path_finder.database import prompt_connection_params
    
    # Show header
    console.print(Panel(
        Text.assemble(
            ("MySQL ", "bold blue"),
            ("FK Path Finder", "bold cyan")
        ),
        subtitle="[dim]Bidirectional Foreign Key Traversal[/dim]",
        expand=False
    ))
    
    # If no user provided, prompt for connection params
    if not config.user:
        params = prompt_connection_params(console)
        config.host = params.get("host", config.host)
        config.port = params.get("port", config.port)
        config.user = params.get("user", config.user)
        config.password = params.get("password", config.password)
    
    # Create finder and run
    finder = FKPathFinder(config, console)
    finder.interactive_find_paths()


def run_batch(
    config: Config,
    console: Console,
    from_ref: str,
    to_ref: str,
    plain: bool
) -> None:
    """Run in batch mode.
    
    Args:
        config: Configuration object.
        console: Rich console instance.
        from_ref: Starting reference.
        to_ref: Ending reference.
        plain: Use plain output.
    """
    finder = FKPathFinder(config, console)
    
    try:
        result = finder.run_batch(from_ref, to_ref, output_format="plain" if plain else "rich")
        
        # Exit with error code if no paths found
        if not result.paths:
            sys.exit(1)
            
    except FKPathFinderError as e:
        if plain:
            click.echo(f"Error: {e}", err=True)
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
