#!/usr/bin/env python3
"""
MySQL FK Path Finder

A tool to discover all paths between two columns in a MySQL database
by traversing foreign key relationships bidirectionally.
"""

import mysql.connector
from mysql.connector import Error
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
import re
import getpass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

console = Console()


def get_connection_params() -> Dict[str, str]:
    """Prompt user for MySQL connection parameters."""
    console.print(Panel.fit("[bold blue]MySQL Connection Setup[/bold blue]", border_style="cyan"))
    
    host = console.input("[yellow]MySQL Host[/yellow] [dim](localhost)[/dim]: ").strip() or "localhost"
    port = console.input("[yellow]MySQL Port[/yellow] [dim](3306)[/dim]: ").strip() or "3306"
    username = console.input("[yellow]Username[/yellow]: ").strip()
    password = getpass.getpass("Password: ")
    
    return {
        "host": host,
        "port": int(port),
        "user": username,
        "password": password
    }


def connect_to_mysql(params: Dict) -> Optional[mysql.connector.MySQLConnection]:
    """Establish connection to MySQL server."""
    try:
        connection = mysql.connector.connect(**params)
        if connection.is_connected():
            console.print(f"\n[bold green]✓[/bold green] Connected to MySQL Server [dim](version: {connection.get_server_info()})[/dim]")
            return connection
    except Error as e:
        console.print(f"\n[bold red]✗ Error connecting to MySQL:[/bold red] {e}")
        return None


def list_databases(connection) -> List[str]:
    """Get list of accessible databases."""
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES")
    databases = [row[0] for row in cursor.fetchall()]
    cursor.close()
    # Filter out system databases
    system_dbs = {'information_schema', 'mysql', 'performance_schema', 'sys'}
    return [db for db in databases if db not in system_dbs]


def select_database(connection) -> Optional[str]:
    """Prompt user to select a database."""
    databases = list_databases(connection)
    
    if not databases:
        console.print("\n[bold red]✗ No accessible databases found.[/bold red]")
        return None
    
    table = Table(title="Available Databases", show_header=True, header_style="bold magenta")
    table.add_column("Index", style="dim", width=6)
    table.add_column("Database Name", style="cyan")
    
    for i, db in enumerate(databases, 1):
        table.add_row(str(i), db)
    
    console.print(table)
    
    while True:
        choice = console.input(f"\nSelect database [bold yellow](1-{len(databases)})[/bold yellow]: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(databases):
                selected_db = databases[idx]
                connection.database = selected_db
                console.print(f"\n[bold green]✓[/bold green] Selected database: [bold cyan]{selected_db}[/bold cyan]")
                return selected_db
        except ValueError:
            pass
        console.print("[bold red]Invalid selection. Please try again.[/bold red]")


def get_foreign_keys(connection, database: str) -> List[Dict]:
    """
    Retrieve all foreign keys from the database.
    Skips composite foreign keys (only single-column FKs).
    """
    query = """
    SELECT 
        kcu.CONSTRAINT_NAME,
        kcu.TABLE_NAME,
        kcu.COLUMN_NAME,
        kcu.REFERENCED_TABLE_NAME,
        kcu.REFERENCED_COLUMN_NAME
    FROM information_schema.KEY_COLUMN_USAGE kcu
    JOIN information_schema.TABLE_CONSTRAINTS tc
        ON kcu.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
        AND kcu.TABLE_SCHEMA = tc.TABLE_SCHEMA
    WHERE tc.CONSTRAINT_TYPE = 'FOREIGN KEY'
        AND kcu.TABLE_SCHEMA = %s
        AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
    ORDER BY kcu.CONSTRAINT_NAME, kcu.ORDINAL_POSITION
    """
    
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, (database,))
    rows = cursor.fetchall()
    cursor.close()
    
    # Group by constraint to detect composite FKs
    constraints = defaultdict(list)
    for row in rows:
        constraints[row['CONSTRAINT_NAME']].append(row)
    
    # Filter out composite FKs (keep only single-column FKs)
    foreign_keys = []
    for constraint_name, columns in constraints.items():
        if len(columns) == 1:
            foreign_keys.append(columns[0])
    
    return foreign_keys


def display_foreign_keys(foreign_keys: List[Dict]) -> None:
    """Display all foreign keys in the database."""
    if not foreign_keys:
        console.print("\n[bold red]✗ No foreign keys found in this database.[/bold red]")
        return
    
    table = Table(title=f"Foreign Keys ({len(foreign_keys)} found)", show_header=True, header_style="bold blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Source (`Table`.`Column`)", style="green")
    table.add_column("Target (`Table`.`Column`)", style="cyan")
    
    for i, fk in enumerate(foreign_keys, 1):
        source = f"`[bold]{fk['TABLE_NAME']}[/bold]`.`{fk['COLUMN_NAME']}`"
        target = f"`[bold]{fk['REFERENCED_TABLE_NAME']}[/bold]`.`{fk['REFERENCED_COLUMN_NAME']}`"
        table.add_row(str(i), source, target)
        
    console.print(table)


def build_graph(foreign_keys: List[Dict]) -> Dict[str, Set[str]]:
    """
    Build a bidirectional graph from foreign keys.
    Nodes are 'table.column', edges connect FK column <-> referenced column.
    Also adds intra-table edges between FK columns and primary keys within the same table.
    """
    graph = defaultdict(set)
    
    # Track all columns by table
    table_columns = defaultdict(set)
    
    for fk in foreign_keys:
        source = f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}"
        target = f"{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}"
        
        # Bidirectional edges between FK relationships
        graph[source].add(target)
        graph[target].add(source)
        
        # Track columns by table
        table_columns[fk['TABLE_NAME']].add(source)
        table_columns[fk['REFERENCED_TABLE_NAME']].add(target)
    
    # Add intra-table edges: all FK-related columns within the same table are connected
    # This allows traversing from one column to another in the same table
    for table, columns in table_columns.items():
        columns_list = list(columns)
        for i in range(len(columns_list)):
            for j in range(i + 1, len(columns_list)):
                graph[columns_list[i]].add(columns_list[j])
                graph[columns_list[j]].add(columns_list[i])
    
    return graph


def parse_reference(ref: str, graph: Dict[str, Set[str]]) -> Tuple[str, List[str]]:
    """
    Parse a reference that can be either:
    - A table name: returns ('table', [list of all FK-related columns in that table])
    - A table.column: returns ('column', ['table.column'])
    """
    ref = ref.strip()
    
    # Try to parse as `table`.`column` format
    backtick_pattern = r'^`([^`]+)`\.`([^`]+)`$'
    match = re.match(backtick_pattern, ref)
    if match:
        col_ref = f"{match.group(1)}.{match.group(2)}"
        if col_ref in graph:
            return ('column', [col_ref])
    
    # Try to parse as table.column format
    simple_pattern = r'^(\w+)\.(\w+)$'
    match = re.match(simple_pattern, ref)
    if match:
        col_ref = f"{match.group(1)}.{match.group(2)}"
        if col_ref in graph:
            return ('column', [col_ref])
    
    # Try to parse as table name (with or without backticks)
    table_name = ref.strip('`')
    
    # Find all columns in this table that are in the graph
    table_columns = [node for node in graph.keys() if node.startswith(f"{table_name}.")]
    
    if table_columns:
        return ('table', table_columns)
    
    return ('unknown', [])


def find_all_paths_between_nodes(graph: Dict[str, Set[str]], start_nodes: List[str], end_nodes: List[str], 
                                  max_path_length: int = 6, max_paths: int = 1000) -> List[List[str]]:
    """
    Find all unique paths between any start node and any end node.
    Returns list of paths, where each path is a list of node names.
    
    Args:
        max_path_length: Maximum number of hops allowed (prevents exponential explosion)
        max_paths: Maximum number of paths to find (prevents memory issues)
    """
    all_paths = []
    seen_paths = set()  # To avoid duplicate paths
    
    total_searches = len(start_nodes) * len(end_nodes)
    current_search = 0
    hit_limit = False
    
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(f"[cyan]Searching paths...", total=total_searches)
        
        for start in start_nodes:
            if hit_limit:
                break
                
            for end in end_nodes:
                current_search += 1
                progress.update(task, advance=1, description=f"[cyan]Searching {current_search}/{total_searches} pairs... ({len(all_paths)} paths found)")
                
                # Early termination if we've found enough paths
                if len(all_paths) >= max_paths:
                    hit_limit = True
                    # Complete the progress bar
                    progress.update(task, completed=total_searches)
                    break
                
                if start == end:
                    # Same column - direct path
                    path_tuple = tuple([start])
                    if path_tuple not in seen_paths:
                        all_paths.append([start])
                        seen_paths.add(path_tuple)
                        if len(all_paths) >= max_paths:
                            hit_limit = True
                            progress.update(task, completed=total_searches)
                            break
                    continue
                
                # BFS to find paths with length limit
                queue = deque([(start, [start])])
                
                while queue:
                    # Check limit more frequently
                    if len(all_paths) >= max_paths:
                        hit_limit = True
                        break
                        
                    current, path = queue.popleft()
                    
                    # Skip if path is too long
                    if len(path) >= max_path_length:
                        continue
                    
                    for neighbor in graph.get(current, set()):
                        if neighbor in path:
                            continue
                        
                        new_path = path + [neighbor]
                        
                        if neighbor == end:
                            # Found a path
                            path_tuple = tuple(new_path)
                            if path_tuple not in seen_paths:
                                all_paths.append(new_path)
                                seen_paths.add(path_tuple)
                                
                                # Check global limit immediately
                                if len(all_paths) >= max_paths:
                                    hit_limit = True
                                    break
                        else:
                            # Only continue if we haven't exceeded length
                            if len(new_path) < max_path_length:
                                queue.append((neighbor, new_path))
                    
                    if hit_limit:
                        break
                
                if hit_limit:
                    break
        
        # Ensure progress bar shows complete
        progress.update(task, completed=total_searches)
    
    if hit_limit:
        console.print(f"[yellow]⚠ Reached maximum path limit ({max_paths}). Stopped search early.[/yellow]")
    
    return all_paths


def find_all_paths(graph: Dict[str, Set[str]], start: str, end: str) -> List[List[str]]:
    """
    Find all paths between start and end nodes using BFS.
    Avoids cycles within a single path.
    """
    if start not in graph:
        console.print(f"\n[bold red]✗[/bold red] [cyan]'{start}'[/cyan] is not connected to any foreign key.")
        return []
    
    if end not in graph:
        console.print(f"\n[bold red]✗[/bold red] [cyan]'{end}'[/cyan] is not connected to any foreign key.")
        return []
    
    if start == end:
        return [[start]]
    
    all_paths = []
    queue = deque([(start, [start])])
    
    while queue:
        current, path = queue.popleft()
        
        for neighbor in graph[current]:
            if neighbor in path:
                # Skip to avoid cycles within this path
                continue
            
            new_path = path + [neighbor]
            
            if neighbor == end:
                all_paths.append(new_path)
            else:
                queue.append((neighbor, new_path))
    
    return all_paths


def format_path(path: List[str]) -> str:
    """Format a path for display."""
    formatted = []
    for node in path:
        table, column = node.split('.', 1)
        formatted.append(f"[bold green]`{table}`[/bold green].[cyan]`{column}`[/cyan]")
    return " [bold yellow]→[/bold yellow] ".join(formatted)


def get_user_endpoints(graph: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """Prompt user for start and end points (tables or table.column)."""
    console.print(Panel.fit("[bold blue]Path Finder[/bold blue]", border_style="cyan"))
    console.print("Enter [bold cyan]table names[/bold cyan] (e.g., 'films') or specific [bold cyan]`table`.`column`[/bold cyan]")
    
    while True:
        from_input = console.input("\n[bold yellow]From:[/bold yellow] ").strip()
        ref_type, from_nodes = parse_reference(from_input, graph)
        
        if ref_type == 'unknown':
            console.print("[bold red]✗ Not found.[/bold red] Enter a table name or `table`.`column`")
            # Show available tables
            tables = set(node.split('.')[0] for node in graph.keys())
            console.print(f"[bold]Available tables:[/bold] {', '.join(sorted(tables)[:10])}")
            continue
        
        if ref_type == 'table':
            table_name = from_input.strip('`')
            console.print(f"[dim]Found {len(from_nodes)} FK-related column(s) in table '{table_name}'[/dim]")
        
        break
    
    while True:
        to_input = console.input("[bold yellow]To:[/bold yellow] ").strip()
        ref_type, to_nodes = parse_reference(to_input, graph)
        
        if ref_type == 'unknown':
            console.print("[bold red]✗ Not found.[/bold red] Enter a table name or `table`.`column`")
            continue
        
        if ref_type == 'table':
            table_name = to_input.strip('`')
            console.print(f"[dim]Found {len(to_nodes)} FK-related column(s) in table '{table_name}'[/dim]")
        
        break
    
    return from_nodes, to_nodes


def main():
    console.print(Panel(
        Text.assemble(
            ("MySQL ", "bold blue"), 
            ("FK Path Finder", "bold cyan")
        ),
        subtitle="[dim]Bidirectional Foreign Key Traversal[/dim]",
        expand=False
    ))
    
    # Get connection parameters
    params = get_connection_params()
    
    # Connect to MySQL
    connection = connect_to_mysql(params)
    if not connection:
        return
    
    try:
        # Select database
        database = select_database(connection)
        if not database:
            return
        
        # Get foreign keys
        with console.status("[bold green]Fetching foreign keys...") as status:
            foreign_keys = get_foreign_keys(connection, database)
        
        display_foreign_keys(foreign_keys)
        
        if not foreign_keys:
            return
        
        # Build graph
        graph = build_graph(foreign_keys)
        
        # Main loop for finding paths
        while True:
            from_nodes, to_nodes = get_user_endpoints(graph)
            
            # Ask for limits
            console.print(f"\n[dim]Search will be limited to max 6 hops and 1000 paths by default[/dim]")
            custom_limit = console.input("[yellow]Custom max paths (press Enter for 1000):[/yellow] ").strip()
            
            max_paths = 1000
            if custom_limit.isdigit():
                max_paths = int(custom_limit)
                max_paths = min(max_paths, 10000)  # Hard cap at 10k
            
            console.print(f"\n[bold blue]Searching[/bold blue] for paths (max {max_paths} paths, max 6 hops)...")
            
            paths = find_all_paths_between_nodes(graph, from_nodes, to_nodes, max_path_length=6, max_paths=max_paths)
            
            if not paths:
                console.print("\n[bold red]✗ No paths found.[/bold red]")
            else:
                # Sort paths by length
                paths.sort(key=len)
                
                # Show summary
                if len(paths) >= max_paths:
                    console.print(Panel(
                        f"Found [bold yellow]{len(paths)}+[/bold yellow] paths [dim](search limit reached)[/dim]",
                        border_style="yellow"
                    ))
                else:
                    console.print(Panel(
                        f"Found [bold green]{len(paths)}[/bold green] path(s)",
                        border_style="green"
                    ))
                
                # Ask how many to display
                display_limit = min(20, len(paths))
                if len(paths) > 20:
                    show_all = console.input(f"\nShow all {len(paths)} paths? [yellow](y/n, default: first 20)[/yellow]: ").strip().lower()
                    if show_all == 'y':
                        display_limit = len(paths)
                
                for i, path in enumerate(paths[:display_limit], 1):
                    console.print(f"  [bold]Path {i}[/bold] [dim]({len(path)} hops)[/dim]: {format_path(path)}\n")
                
                if len(paths) > display_limit:
                    console.print(f"\n[dim]... and {len(paths) - display_limit} more paths[/dim]")
            
            # Ask to continue
            again = console.input("\nFind another path? [bold yellow](y/n)[/bold yellow]: ").strip().lower()
            if again != 'y':
                break
        
        console.print("\n[bold blue]Goodbye![/bold blue]")
        
    finally:
        if connection.is_connected():
            connection.close()
            console.print("[dim]MySQL connection closed.[/dim]")


if __name__ == "__main__":
    main()
