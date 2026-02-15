"""Main path finding orchestration module."""

from typing import List, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from fk_path_finder.types import Config, PathResult, ForeignKeyDict
from fk_path_finder.database import DatabaseConnector, DatabaseError
from fk_path_finder.graph import GraphBuilder, format_path


class FKPathFinderError(Exception):
    """Custom exception for FK Path Finder errors."""
    pass


class FKPathFinder:
    """Main class for finding foreign key paths in MySQL databases."""
    
    def __init__(
        self,
        config: Optional[Config] = None,
        console: Optional[Console] = None
    ) -> None:
        """Initialize the path finder.
        
        Args:
            config: Application configuration.
            console: Optional Rich console instance.
        """
        self.config = config or Config()
        self.console = console or Console()
        self.connector = DatabaseConnector(self.console)
        self.graph_builder = GraphBuilder()
        self._database: Optional[str] = None
        self._foreign_keys: List[ForeignKeyDict] = []
    
    @property
    def database(self) -> Optional[str]:
        """Get the currently selected database."""
        return self._database
    
    @property
    def foreign_keys(self) -> List[ForeignKeyDict]:
        """Get the retrieved foreign keys."""
        return self._foreign_keys
    
    def connect(self) -> bool:
        """Connect to the MySQL database.
        
        Returns:
            True if connected successfully.
            
        Raises:
            FKPathFinderError: If connection fails.
        """
        params = self.config.to_connection_params()
        
        if not params.get("user"):
            raise FKPathFinderError("Database user is required")
        
        try:
            return self.connector.connect(params)
        except DatabaseError as e:
            raise FKPathFinderError(str(e))
    
    def disconnect(self) -> None:
        """Disconnect from the database."""
        self.connector.disconnect()
    
    def select_database(self, database: Optional[str] = None) -> str:
        """Select a database to use.
        
        Args:
            database: Database name. If None, uses config.database or prompts user.
            
        Returns:
            Selected database name.
            
        Raises:
            FKPathFinderError: If database selection fails.
        """
        if database:
            self._database = database
            try:
                self.connector.select_database(database)
                return database
            except DatabaseError as e:
                raise FKPathFinderError(str(e))
        
        if self.config.database:
            self._database = self.config.database
            try:
                self.connector.select_database(self.config.database)
                return self.config.database
            except DatabaseError as e:
                raise FKPathFinderError(str(e))
        
        raise FKPathFinderError("No database specified")
    
    def list_databases(self) -> List[str]:
        """List available databases.
        
        Returns:
            List of database names.
            
        Raises:
            FKPathFinderError: If not connected.
        """
        try:
            return self.connector.list_databases()
        except DatabaseError as e:
            raise FKPathFinderError(str(e))
    
    def fetch_foreign_keys(self) -> List[ForeignKeyDict]:
        """Fetch foreign keys from the current database.
        
        Returns:
            List of foreign key dictionaries.
            
        Raises:
            FKPathFinderError: If not connected or no database selected.
        """
        if not self._database:
            raise FKPathFinderError("No database selected")
        
        try:
            self._foreign_keys = self.connector.get_foreign_keys(self._database)
            return self._foreign_keys
        except DatabaseError as e:
            raise FKPathFinderError(str(e))
    
    def build_graph(self) -> Dict[str, set]:
        """Build the graph from foreign keys.
        
        Returns:
            The built graph dictionary.
            
        Raises:
            FKPathFinderError: If no foreign keys loaded.
        """
        if not self._foreign_keys:
            raise FKPathFinderError("No foreign keys loaded. Call fetch_foreign_keys() first.")
        
        return self.graph_builder.build(self._foreign_keys)
    
    def display_foreign_keys(self) -> None:
        """Display all foreign keys in a table format."""
        if not self._foreign_keys:
            self.console.print("\n[bold red]✗ No foreign keys found in this database.[/bold red]")
            return
        
        table = Table(
            title=f"Foreign Keys ({len(self._foreign_keys)} found)",
            show_header=True,
            header_style="bold blue"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Source (`Table`.`Column`)", style="green")
        table.add_column("Target (`Table`.`Column`)", style="cyan")
        
        for i, fk in enumerate(self._foreign_keys, 1):
            source = f"`[bold]{fk['TABLE_NAME']}[/bold]`.`{fk['COLUMN_NAME']}`"
            target = f"`[bold]{fk['REFERENCED_TABLE_NAME']}[/bold]`.`{fk['REFERENCED_COLUMN_NAME']}`"
            table.add_row(str(i), source, target)
            
        self.console.print(table)
    
    def find_paths(
        self,
        start_ref: str,
        end_ref: str
    ) -> PathResult:
        """Find paths between two references.
        
        Args:
            start_ref: Starting reference (table or table.column).
            end_ref: Ending reference (table or table.column).
            
        Returns:
            PathResult with found paths.
            
        Raises:
            FKPathFinderError: If references are invalid or graph not built.
        """
        # Parse references
        start_type, start_nodes = self.graph_builder.parse_reference(start_ref)
        end_type, end_nodes = self.graph_builder.parse_reference(end_ref)
        
        if start_type == "unknown":
            available = list(self.graph_builder.get_tables())[:10]
            raise FKPathFinderError(
                f"Start reference '{start_ref}' not found. "
                f"Available tables: {', '.join(sorted(available))}"
            )
        
        if end_type == "unknown":
            raise FKPathFinderError(f"End reference '{end_ref}' not found")
        
        # Find paths
        result = self.graph_builder.find_all_paths(
            start_nodes=start_nodes,
            end_nodes=end_nodes,
            max_path_length=self.config.max_path_length,
            max_paths=self.config.max_paths,
            console=self.console
        )
        
        return result
    
    def display_paths(self, result: PathResult, display_limit: Optional[int] = None) -> None:
        """Display the found paths.
        
        Args:
            result: PathResult containing paths.
            display_limit: Maximum number of paths to display.
        """
        if not result.paths:
            self.console.print("\n[bold red]✗ No paths found.[/bold red]")
            return
        
        limit = display_limit or self.config.display_limit
        
        # Show summary
        if result.limit_reached:
            self.console.print(Panel(
                f"Found [bold yellow]{result.total_found}[/bold yellow] paths "
                f"[dim](search limit reached)[/dim]",
                border_style="yellow"
            ))
        else:
            self.console.print(Panel(
                f"Found [bold green]{result.total_found}[/bold green] path(s)",
                border_style="green"
            ))
        
        # Display paths
        for i, path in enumerate(result.paths[:limit], 1):
            self.console.print(
                f"  [bold]Path {i}[/bold] [dim]({len(path)} hops)[/dim]: {format_path(path)}\n"
            )
        
        if result.total_found > limit:
            self.console.print(
                f"\n[dim]... and {result.total_found - limit} more paths[/dim]"
            )
    
    def interactive_find_paths(self) -> None:
        """Run interactive path finding session."""
        from fk_path_finder.database import prompt_database_selection
        
        # Show header
        self.console.print(Panel(
            Text.assemble(
                ("MySQL ", "bold blue"), 
                ("FK Path Finder", "bold cyan")
            ),
            subtitle="[dim]Bidirectional Foreign Key Traversal[/dim]",
            expand=False
        ))
        
        # Connect
        if not self.connector.is_connected():
            if not self.connect():
                return
        
        try:
            # Select database if not already selected
            if not self._database:
                try:
                    self.select_database()
                except FKPathFinderError:
                    # Prompt for database selection
                    self.console.print("\n[bold yellow]Please select a database:[/bold yellow]")
                    db = prompt_database_selection(self.connector, self.console)
                    if not db:
                        return
                    self._database = db
            
            # Fetch foreign keys
            with self.console.status("[bold green]Fetching foreign keys..."):
                self.fetch_foreign_keys()
            
            self.display_foreign_keys()
            
            if not self._foreign_keys:
                return
            
            # Build graph
            self.build_graph()
            
            # Main loop for finding paths
            while True:
                self.console.print(Panel.fit(
                    "[bold blue]Path Finder[/bold blue]",
                    border_style="cyan"
                ))
                self.console.print(
                    "Enter [bold cyan]table names[/bold cyan] (e.g., 'films') or "
                    "specific [bold cyan]`table`.`column`[/bold cyan]"
                )
                
                # Get user input
                from_input = self.console.input("\n[bold yellow]From:[/bold yellow] ").strip()
                start_type, start_nodes = self.graph_builder.parse_reference(from_input)
                
                if start_type == "unknown":
                    self.console.print(
                        "[bold red]✗ Not found.[/bold red] Enter a table name or `table`.`column`"
                    )
                    tables = sorted(list(self.graph_builder.get_tables()))[:10]
                    self.console.print(f"[bold]Available tables:[/bold] {', '.join(tables)}")
                    continue
                
                if start_type == "table":
                    table_name = from_input.strip("`")
                    self.console.print(
                        f"[dim]Found {len(start_nodes)} FK-related column(s) in table "
                        f"'{table_name}'[/dim]"
                    )
                
                to_input = self.console.input("[bold yellow]To:[/bold yellow] ").strip()
                end_type, end_nodes = self.graph_builder.parse_reference(to_input)
                
                if end_type == "unknown":
                    self.console.print(
                        "[bold red]✗ Not found.[/bold red] Enter a table name or `table`.`column`"
                    )
                    continue
                
                if end_type == "table":
                    table_name = to_input.strip("`")
                    self.console.print(
                        f"[dim]Found {len(end_nodes)} FK-related column(s) in table "
                        f"'{table_name}'[/dim]"
                    )
                
                # Ask for limits
                self.console.print(
                    f"\n[dim]Search will be limited to max {self.config.max_path_length} hops "
                    f"and {self.config.max_paths} paths by default[/dim]"
                )
                custom_limit = self.console.input(
                    "[yellow]Custom max paths (press Enter for default):[/yellow] "
                ).strip()
                
                max_paths = self.config.max_paths
                if custom_limit.isdigit():
                    max_paths = int(custom_limit)
                    max_paths = min(max_paths, 10000)  # Hard cap at 10k
                
                self.console.print(
                    f"\n[bold blue]Searching[/bold blue] for paths "
                    f"(max {max_paths} paths, max {self.config.max_path_length} hops)..."
                )
                
                # Find paths
                result = self.graph_builder.find_all_paths(
                    start_nodes=start_nodes,
                    end_nodes=end_nodes,
                    max_path_length=self.config.max_path_length,
                    max_paths=max_paths,
                    console=self.console
                )
                
                # Display results
                self.display_paths(result)
                
                # Ask to continue
                again = self.console.input(
                    "\nFind another path? [bold yellow](y/n)[/bold yellow]: "
                ).strip().lower()
                if again != "y":
                    break
            
            self.console.print("\n[bold blue]Goodbye![/bold blue]")
            
        finally:
            self.disconnect()
    
    def run_batch(
        self,
        start_ref: str,
        end_ref: str,
        output_format: str = "rich"
    ) -> PathResult:
        """Run batch path finding (non-interactive).
        
        Args:
            start_ref: Starting reference.
            end_ref: Ending reference.
            output_format: Output format ('rich' or 'plain').
            
        Returns:
            PathResult with found paths.
            
        Raises:
            FKPathFinderError: If any step fails.
        """
        # Connect
        if not self.connect():
            raise FKPathFinderError("Failed to connect to database")
        
        try:
            # Select database
            self.select_database()
            
            # Fetch foreign keys
            with self.console.status("[bold green]Fetching foreign keys..."):
                self.fetch_foreign_keys()
            
            if not self._foreign_keys:
                raise FKPathFinderError("No foreign keys found in database")
            
            # Build graph
            self.build_graph()
            
            # Find paths
            result = self.find_paths(start_ref, end_ref)
            
            # Display results
            if output_format == "plain":
                self._display_paths_plain(result)
            else:
                self.display_paths(result)
            
            return result
            
        finally:
            self.disconnect()
    
    def _display_paths_plain(self, result: PathResult) -> None:
        """Display paths in plain text format.
        
        Args:
            result: PathResult containing paths.
        """
        from fk_path_finder.graph import format_path_plain
        
        if not result.paths:
            print("No paths found.")
            return
        
        print(f"Found {result.total_found} path(s)")
        if result.limit_reached:
            print("(search limit reached)")
        
        for i, path in enumerate(result.paths[:self.config.display_limit], 1):
            print(f"Path {i} ({len(path)} hops): {format_path_plain(path)}")
        
        if result.total_found > self.config.display_limit:
            print(f"... and {result.total_found - self.config.display_limit} more paths")
