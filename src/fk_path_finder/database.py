"""Database connection and schema extraction module."""

import re
from typing import Dict, List, Optional, Any
from collections import defaultdict

import mysql.connector
from mysql.connector import Error as MySQLError
from rich.console import Console

from fk_path_finder.types import ForeignKeyDict, ConnectionParams

console = Console()


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


class DatabaseConnector:
    """Handles MySQL database connections and schema extraction."""
    
    def __init__(self, console_instance: Optional[Console] = None) -> None:
        """Initialize the database connector.
        
        Args:
            console_instance: Optional Rich console instance.
        """
        self.console = console_instance or Console()
        self._connection: Optional[mysql.connector.MySQLConnection] = None
    
    @property
    def connection(self) -> mysql.connector.MySQLConnection:
        """Get the current connection.
        
        Returns:
            The MySQL connection.
            
        Raises:
            DatabaseError: If not connected.
        """
        if self._connection is None or not self._connection.is_connected():
            raise DatabaseError("Not connected to database")
        return self._connection
    
    def connect(self, params: Dict[str, Any]) -> bool:
        """Establish connection to MySQL server.
        
        Args:
            params: Connection parameters.
            
        Returns:
            True if connected successfully.
            
        Raises:
            DatabaseError: If connection fails.
        """
        try:
            self._connection = mysql.connector.connect(**params)
            if self._connection.is_connected():
                self.console.print(
                    f"[bold green]✓[/bold green] Connected to MySQL Server "
                    f"[dim](version: {self._connection.get_server_info()})[/dim]"
                )
                return True
        except MySQLError as e:
            raise DatabaseError(f"Error connecting to MySQL: {e}")
        
        return False
    
    def disconnect(self) -> None:
        """Close the database connection."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            self.console.print("[dim]MySQL connection closed.[/dim]")
    
    def is_connected(self) -> bool:
        """Check if connected to database.
        
        Returns:
            True if connected.
        """
        return self._connection is not None and self._connection.is_connected()
    
    def list_databases(self) -> List[str]:
        """Get list of accessible databases.
        
        Returns:
            List of database names.
            
        Raises:
            DatabaseError: If not connected.
        """
        cursor = self.connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        # Filter out system databases
        system_dbs = {"information_schema", "mysql", "performance_schema", "sys"}
        return [db for db in databases if db not in system_dbs]
    
    def select_database(self, database: str) -> bool:
        """Select a database to use.
        
        Args:
            database: Database name.
            
        Returns:
            True if successful.
            
        Raises:
            DatabaseError: If database doesn't exist or not connected.
        """
        try:
            self.connection.database = database
            self.console.print(
                f"[bold green]✓[/bold green] Selected database: [bold cyan]{database}[/bold cyan]"
            )
            return True
        except MySQLError as e:
            raise DatabaseError(f"Failed to select database: {e}")
    
    def get_foreign_keys(self, database: str) -> List[ForeignKeyDict]:
        """Retrieve all foreign keys from the database.
        
        Only single-column foreign keys are returned (composite FKs are skipped).
        
        Args:
            database: Database name.
            
        Returns:
            List of foreign key dictionaries.
            
        Raises:
            DatabaseError: If query fails.
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
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, (database,))
            rows = cursor.fetchall()
            cursor.close()
        except MySQLError as e:
            raise DatabaseError(f"Failed to fetch foreign keys: {e}")
        
        # Group by constraint to detect composite FKs
        constraints: Dict[str, List[ForeignKeyDict]] = defaultdict(list)
        for row in rows:
            constraints[row["CONSTRAINT_NAME"]].append(row)
        
        # Filter out composite FKs (keep only single-column FKs)
        foreign_keys: List[ForeignKeyDict] = []
        for constraint_name, columns in constraints.items():
            if len(columns) == 1:
                foreign_keys.append(columns[0])
        
        return foreign_keys
    
    def get_tables_with_foreign_keys(self, database: str) -> Dict[str, List[str]]:
        """Get mapping of tables to their FK-related columns.
        
        Args:
            database: Database name.
            
        Returns:
            Dictionary mapping table names to lists of column names.
        """
        foreign_keys = self.get_foreign_keys(database)
        
        tables: Dict[str, List[str]] = defaultdict(list)
        for fk in foreign_keys:
            source = f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']}"
            target = f"{fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}"
            
            if source not in tables[fk["TABLE_NAME"]]:
                tables[fk["TABLE_NAME"]].append(source)
            if target not in tables[fk["REFERENCED_TABLE_NAME"]]:
                tables[fk["REFERENCED_TABLE_NAME"]].append(target)
        
        return dict(tables)


def prompt_connection_params(console_instance: Optional[Console] = None) -> ConnectionParams:
    """Prompt user for MySQL connection parameters.
    
    Args:
        console_instance: Optional Rich console instance.
        
    Returns:
        Dictionary with connection parameters.
    """
    import getpass
    from rich.panel import Panel
    
    c = console_instance or Console()
    c.print(Panel.fit("[bold blue]MySQL Connection Setup[/bold blue]", border_style="cyan"))
    
    host = c.input("[yellow]MySQL Host[/yellow] [dim](localhost)[/dim]: ").strip() or "localhost"
    port_str = c.input("[yellow]MySQL Port[/yellow] [dim](3306)[/dim]: ").strip() or "3306"
    username = c.input("[yellow]Username[/yellow]: ").strip()
    password = getpass.getpass("Password: ")
    
    return {
        "host": host,
        "port": int(port_str),
        "user": username,
        "password": password,
    }


def prompt_database_selection(
    connector: DatabaseConnector,
    console_instance: Optional[Console] = None
) -> Optional[str]:
    """Prompt user to select a database.
    
    Args:
        connector: Database connector instance.
        console_instance: Optional Rich console instance.
        
    Returns:
        Selected database name or None.
    """
    from rich.table import Table
    
    c = console_instance or Console()
    
    try:
        databases = connector.list_databases()
    except DatabaseError as e:
        c.print(f"\n[bold red]✗ {e}[/bold red]")
        return None
    
    if not databases:
        c.print("\n[bold red]✗ No accessible databases found.[/bold red]")
        return None
    
    table = Table(title="Available Databases", show_header=True, header_style="bold magenta")
    table.add_column("Index", style="dim", width=6)
    table.add_column("Database Name", style="cyan")
    
    for i, db in enumerate(databases, 1):
        table.add_row(str(i), db)
    
    c.print(table)
    
    while True:
        choice = c.input(f"\nSelect database [bold yellow](1-{len(databases)})[/bold yellow]: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(databases):
                selected_db = databases[idx]
                connector.select_database(selected_db)
                return selected_db
        except ValueError:
            pass
        c.print("[bold red]Invalid selection. Please try again.[/bold red]")
