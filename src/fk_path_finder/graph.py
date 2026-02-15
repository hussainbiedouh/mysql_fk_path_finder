"""Graph building and path finding logic."""

import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

from fk_path_finder.types import ForeignKeyDict, Graph, PathResult


class GraphBuilder:
    """Builds and manages the bidirectional graph from foreign keys."""
    
    def __init__(self) -> None:
        """Initialize the graph builder."""
        self._graph: Graph = defaultdict(set)
    
    @property
    def graph(self) -> Graph:
        """Get the built graph.
        
        Returns:
            The graph dictionary.
        """
        return dict(self._graph)
    
    def build(self, foreign_keys: List[ForeignKeyDict]) -> Graph:
        """Build a bidirectional graph from foreign keys.
        
        Nodes are 'table.column', edges connect FK column <-> referenced column.
        Also adds intra-table edges between FK columns and primary keys within the same table.
        
        Args:
            foreign_keys: List of foreign key dictionaries.
            
        Returns:
            The built graph.
        """
        self._graph = defaultdict(set)
        
        # Track all columns by table
        table_columns: Dict[str, Set[str]] = defaultdict(set)
        
        for fk in foreign_keys:
            source = f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}"
            target = f"{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}"
            
            # Bidirectional edges between FK relationships
            self._graph[source].add(target)
            self._graph[target].add(source)
            
            # Track columns by table
            table_columns[fk["TABLE_NAME"]].add(source)
            table_columns[fk["REFERENCED_TABLE_NAME"]].add(target)
        
        # Add intra-table edges: all FK-related columns within the same table are connected
        # This allows traversing from one column to another in the same table
        for table, columns in table_columns.items():
            columns_list = list(columns)
            for i in range(len(columns_list)):
                for j in range(i + 1, len(columns_list)):
                    self._graph[columns_list[i]].add(columns_list[j])
                    self._graph[columns_list[j]].add(columns_list[i])
        
        return self.graph
    
    def get_tables(self) -> Set[str]:
        """Get all tables in the graph.
        
        Returns:
            Set of table names.
        """
        tables: Set[str] = set()
        for node in self._graph.keys():
            table = node.split(".")[0]
            tables.add(table)
        return tables
    
    def get_columns_for_table(self, table_name: str) -> List[str]:
        """Get all columns for a specific table.
        
        Args:
            table_name: Name of the table.
            
        Returns:
            List of column identifiers (table.column).
        """
        table_lower = table_name.lower()
        return [
            node for node in self._graph.keys()
            if node.lower().startswith(f"{table_lower}.")
        ]
    
    def parse_reference(self, ref: str) -> Tuple[str, List[str]]:
        """Parse a reference string.
        
        Can be either:
        - A table name: returns ('table', [list of all FK-related columns in that table])
        - A table.column: returns ('column', ['table.column'])
        
        Args:
            ref: Reference string (table or table.column).
            
        Returns:
            Tuple of (type, nodes) where type is 'column', 'table', or 'unknown'.
        """
        ref = ref.strip()
        
        # Helper for case-insensitive lookup
        def find_node_ci(target: str) -> Optional[str]:
            target_lower = target.lower()
            for node in self._graph.keys():
                if node.lower() == target_lower:
                    return node
            return None
        
        # Try to parse as `table`.`column` format
        backtick_pattern = r"^`([^`]+)`\.`([^`]+)`$"
        match = re.match(backtick_pattern, ref)
        if match:
            col_ref = f"{match.group(1)}.{match.group(2)}"
            found = find_node_ci(col_ref)
            if found:
                return ("column", [found])
        
        # Try to parse as table.column format (split at LAST dot to support dots in table names)
        if "." in ref:
            parts = ref.rsplit(".", 1)
            table_part = parts[0].strip("`")
            col_part = parts[1].strip("`")
            col_ref = f"{table_part}.{col_part}"
            found = find_node_ci(col_ref)
            if found:
                return ("column", [found])
        
        # Try to parse as table name (with or without backticks)
        table_name = ref.strip("`").lower()
        
        # Find all columns in this table that are in the graph (case-insensitive)
        table_columns = [
            node for node in self._graph.keys()
            if node.lower().startswith(f"{table_name}.")
        ]
        
        if table_columns:
            return ("table", table_columns)
        
        return ("unknown", [])
    
    def find_all_paths(
        self,
        start_nodes: List[str],
        end_nodes: List[str],
        max_path_length: int = 6,
        max_paths: int = 1000,
        console: Optional[Console] = None
    ) -> PathResult:
        """Find all unique paths between any start node and any end node.
        
        Uses BFS to find paths with length and count limits to prevent exponential explosion.
        
        Args:
            start_nodes: List of starting node identifiers.
            end_nodes: List of ending node identifiers.
            max_path_length: Maximum number of hops allowed.
            max_paths: Maximum number of paths to find.
            console: Optional Rich console for progress display.
            
        Returns:
            PathResult containing found paths and metadata.
        """
        all_paths: List[List[str]] = []
        seen_paths: Set[Tuple[str, ...]] = set()  # To avoid duplicate paths
        
        total_searches = len(start_nodes) * len(end_nodes)
        current_search = 0
        hit_limit = False
        
        progress_console = console or Console()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=progress_console,
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Searching paths...", total=total_searches)
            
            for start in start_nodes:
                if hit_limit:
                    break
                    
                for end in end_nodes:
                    current_search += 1
                    progress.update(
                        task,
                        advance=1,
                        description=f"[cyan]Searching {current_search}/{total_searches} pairs... "
                                   f"({len(all_paths)} paths found)"
                    )
                    
                    # Early termination if we've found enough paths
                    if len(all_paths) >= max_paths:
                        hit_limit = True
                        progress.update(task, completed=total_searches)
                        break
                    
                    if start == end:
                        # Same column - direct path
                        path_tuple: Tuple[str, ...] = tuple([start])
                        if path_tuple not in seen_paths:
                            all_paths.append([start])
                            seen_paths.add(path_tuple)
                            if len(all_paths) >= max_paths:
                                hit_limit = True
                                progress.update(task, completed=total_searches)
                                break
                        continue
                    
                    # BFS to find paths with length limit
                    queue: deque[Tuple[str, List[str]]] = deque([(start, [start])])
                    
                    while queue:
                        # Check limit more frequently
                        if len(all_paths) >= max_paths:
                            hit_limit = True
                            break
                            
                        current, path = queue.popleft()
                        
                        # Skip if path is too long
                        if len(path) >= max_path_length:
                            continue
                        
                        for neighbor in self._graph.get(current, set()):
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
        
        return PathResult(
            paths=all_paths,
            total_found=len(all_paths),
            limit_reached=hit_limit,
            start_nodes=start_nodes,
            end_nodes=end_nodes
        )
    
    def find_paths_simple(
        self,
        start: str,
        end: str
    ) -> List[List[str]]:
        """Simple BFS path finding without limits (for small graphs).
        
        Args:
            start: Starting node.
            end: Ending node.
            
        Returns:
            List of paths found.
        """
        if start not in self._graph or end not in self._graph:
            return []
        
        if start == end:
            return [[start]]
        
        all_paths: List[List[str]] = []
        queue: deque[Tuple[str, List[str]]] = deque([(start, [start])])
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self._graph[current]:
                if neighbor in path:
                    continue
                
                new_path = path + [neighbor]
                
                if neighbor == end:
                    all_paths.append(new_path)
                else:
                    queue.append((neighbor, new_path))
        
        return all_paths


def format_path(path: List[str]) -> str:
    """Format a path for display.
    
    Args:
        path: List of node identifiers.
        
    Returns:
        Formatted string with Rich markup.
    """
    formatted = []
    for node in path:
        table, column = node.split(".", 1)
        formatted.append(f"[bold green]`{table}`[/bold green].[cyan]`{column}`[/cyan]")
    return " [bold yellow]→[/bold yellow] ".join(formatted)


def format_path_plain(path: List[str]) -> str:
    """Format a path for plain text output (no Rich markup).
    
    Args:
        path: List of node identifiers.
        
    Returns:
        Plain text formatted string.
    """
    formatted = []
    for node in path:
        table, column = node.split(".", 1)
        formatted.append(f"`{table}`.`{column}`")
    return " -> ".join(formatted)
