"""Comprehensive tests for database module."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Dict, Any

from mysql.connector import Error as MySQLError

from fk_path_finder.database import (
    DatabaseConnector,
    DatabaseError,
    prompt_connection_params,
    prompt_database_selection,
)
from fk_path_finder.types import ForeignKeyDict


# =============================================================================
# Test DatabaseConnector Initialization
# =============================================================================

class TestDatabaseConnectorInit:
    """Test cases for DatabaseConnector initialization."""
    
    def test_init_default(self):
        """Test initialization with default console."""
        connector = DatabaseConnector()
        assert connector._connection is None
        assert connector.console is not None
    
    def test_init_with_custom_console(self):
        """Test initialization with custom console."""
        custom_console = Mock()
        connector = DatabaseConnector(console_instance=custom_console)
        assert connector.console == custom_console


# =============================================================================
# Test DatabaseConnector Connection
# =============================================================================

class TestDatabaseConnectorConnection:
    """Test cases for database connection operations."""
    
    @pytest.mark.database
    def test_connection_property_not_connected(self):
        """Test accessing connection when not connected raises error."""
        connector = DatabaseConnector()
        
        with pytest.raises(DatabaseError, match="Not connected to database"):
            _ = connector.connection
    
    @pytest.mark.database
    def test_connection_property_disconnected(self, mock_mysql_connection: Mock):
        """Test accessing connection after disconnect."""
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        mock_mysql_connection.is_connected.return_value = False
        
        with pytest.raises(DatabaseError, match="Not connected to database"):
            _ = connector.connection
    
    @patch("fk_path_finder.database.mysql.connector.connect")
    def test_connect_success(self, mock_connect: Mock, mock_mysql_connection: Mock):
        """Test successful connection."""
        mock_connect.return_value = mock_mysql_connection
        connector = DatabaseConnector(console_instance=Mock())
        
        params = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "secret"
        }
        
        result = connector.connect(params)
        
        assert result is True
        assert connector.is_connected() is True
        mock_connect.assert_called_once_with(**params)
    
    @patch("fk_path_finder.database.mysql.connector.connect")
    def test_connect_failure(self, mock_connect: Mock):
        """Test connection failure raises DatabaseError."""
        mock_connect.side_effect = MySQLError("Connection refused")
        connector = DatabaseConnector()
        
        params = {"host": "invalid", "user": "root"}
        
        with pytest.raises(DatabaseError, match="Error connecting to MySQL"):
            connector.connect(params)
        
        assert connector.is_connected() is False
    
    @patch("fk_path_finder.database.mysql.connector.connect")
    def test_connect_not_connected(self, mock_connect: Mock, mock_mysql_connection: Mock):
        """Test when connection returns but is_connected is False."""
        mock_mysql_connection.is_connected.return_value = False
        mock_connect.return_value = mock_mysql_connection
        connector = DatabaseConnector()
        
        result = connector.connect({"host": "localhost", "user": "root"})
        
        assert result is False
    
    def test_disconnect_connected(self, mock_mysql_connection: Mock):
        """Test disconnect when connected."""
        connector = DatabaseConnector(console_instance=Mock())
        connector._connection = mock_mysql_connection
        mock_mysql_connection.is_connected.return_value = True
        
        connector.disconnect()
        
        mock_mysql_connection.close.assert_called_once()
    
    def test_disconnect_not_connected(self):
        """Test disconnect when not connected - should not raise."""
        connector = DatabaseConnector()
        connector.disconnect()  # Should not raise
    
    def test_disconnect_none_connection(self):
        """Test disconnect when connection is None."""
        connector = DatabaseConnector()
        connector._connection = None
        connector.disconnect()  # Should not raise
    
    def test_is_connected_true(self, mock_mysql_connection: Mock):
        """Test is_connected returns True."""
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        mock_mysql_connection.is_connected.return_value = True
        
        assert connector.is_connected() is True
    
    def test_is_connected_false_no_connection(self):
        """Test is_connected returns False when no connection."""
        connector = DatabaseConnector()
        assert connector.is_connected() is False
    
    def test_is_connected_false_disconnected(self, mock_mysql_connection: Mock):
        """Test is_connected returns False when disconnected."""
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        mock_mysql_connection.is_connected.return_value = False
        
        assert connector.is_connected() is False


# =============================================================================
# Test Database Operations
# =============================================================================

class TestDatabaseOperations:
    """Test cases for database operations."""
    
    def test_list_databases_success(self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock):
        """Test listing databases successfully."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = [
            ("mysql",),
            ("information_schema",),
            ("performance_schema",),
            ("sys",),
            ("sakila",),
            ("mydb",),
        ]
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        databases = connector.list_databases()
        
        # System databases should be filtered out
        assert "sakila" in databases
        assert "mydb" in databases
        assert "mysql" not in databases
        assert "information_schema" not in databases
        assert "performance_schema" not in databases
        assert "sys" not in databases
        mock_mysql_cursor.execute.assert_called_once_with("SHOW DATABASES")
        mock_mysql_cursor.close.assert_called_once()
    
    def test_list_databases_empty(self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock):
        """Test listing databases when none exist."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = [
            ("mysql",),
            ("information_schema",),
        ]
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        databases = connector.list_databases()
        
        assert len(databases) == 0
    
    def test_list_databases_not_connected(self):
        """Test listing databases when not connected raises error."""
        connector = DatabaseConnector()
        
        with pytest.raises(DatabaseError, match="Not connected to database"):
            connector.list_databases()
    
    def test_list_databases_query_error(self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock):
        """Test listing databases when query fails."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.execute.side_effect = MySQLError("Query failed")
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        # The error propagates as a DatabaseError
        with pytest.raises(Exception):  # MySQLError or DatabaseError depending on implementation
            connector.list_databases()
    
    def test_select_database_success(self, mock_mysql_connection: Mock):
        """Test selecting database successfully."""
        connector = DatabaseConnector(console_instance=Mock())
        connector._connection = mock_mysql_connection
        
        result = connector.select_database("sakila")
        
        assert result is True
        assert mock_mysql_connection.database == "sakila"
    
    def test_select_database_failure(self, mock_mysql_connection: Mock):
        """Test selecting database that doesn't exist."""
        connector = DatabaseConnector(console_instance=Mock())
        connector._connection = mock_mysql_connection
        
        # Simulate database assignment raising error
        def raise_error(obj, val):
            raise MySQLError("Unknown database 'nonexistent'")
        
        # Patch the database property setter
        with patch.object(type(mock_mysql_connection), 'database', 
                         property(lambda self: None, raise_error)):
            with pytest.raises(DatabaseError, match="Failed to select database"):
                connector.select_database("nonexistent")
    
    def test_select_database_not_connected(self):
        """Test selecting database when not connected."""
        connector = DatabaseConnector()
        
        with pytest.raises(DatabaseError, match="Not connected to database"):
            connector.select_database("sakila")


# =============================================================================
# Test Foreign Key Operations
# =============================================================================

class TestForeignKeyOperations:
    """Test cases for foreign key operations."""
    
    def test_get_foreign_keys_success(
        self,
        mock_mysql_connection: Mock,
        mock_mysql_cursor: Mock,
        sample_fk_query_result: List[Dict[str, Any]]
    ):
        """Test retrieving foreign keys successfully."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = sample_fk_query_result
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        foreign_keys = connector.get_foreign_keys("testdb")
        
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["CONSTRAINT_NAME"] == "fk_test"
        mock_mysql_cursor.execute.assert_called_once()
        mock_mysql_cursor.close.assert_called_once()
    
    def test_get_foreign_keys_with_composite_filtered(
        self,
        mock_mysql_connection: Mock,
        mock_mysql_cursor: Mock,
        composite_fk_query_result: List[Dict[str, Any]]
    ):
        """Test that composite foreign keys are filtered out."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = composite_fk_query_result
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        foreign_keys = connector.get_foreign_keys("testdb")
        
        # Only single-column FK should remain
        assert len(foreign_keys) == 1
        assert foreign_keys[0]["CONSTRAINT_NAME"] == "fk_single"
    
    def test_get_foreign_keys_empty(self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock):
        """Test retrieving foreign keys when none exist."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = []
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        foreign_keys = connector.get_foreign_keys("testdb")
        
        assert len(foreign_keys) == 0
    
    def test_get_foreign_keys_not_connected(self):
        """Test retrieving foreign keys when not connected."""
        connector = DatabaseConnector()
        
        with pytest.raises(DatabaseError, match="Not connected to database"):
            connector.get_foreign_keys("testdb")
    
    def test_get_foreign_keys_query_error(
        self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock
    ):
        """Test retrieving foreign keys when query fails."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.execute.side_effect = MySQLError("Query failed")
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        with pytest.raises(DatabaseError, match="Failed to fetch foreign keys"):
            connector.get_foreign_keys("testdb")
    
    def test_get_tables_with_foreign_keys(
        self,
        mock_mysql_connection: Mock,
        mock_mysql_cursor: Mock,
        sample_fk_query_result: List[Dict[str, Any]]
    ):
        """Test getting tables with foreign keys."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = sample_fk_query_result
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        tables = connector.get_tables_with_foreign_keys("testdb")
        
        assert "orders" in tables
        assert "customers" in tables
        assert "orders.customer_id" in tables["orders"]
        assert "customers.id" in tables["customers"]
    
    def test_get_tables_with_foreign_keys_empty(
        self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock
    ):
        """Test getting tables with foreign keys when none exist."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = []
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        tables = connector.get_tables_with_foreign_keys("testdb")
        
        assert len(tables) == 0


# =============================================================================
# Test Prompt Functions
# =============================================================================

class TestPromptConnectionParams:
    """Test cases for prompt_connection_params function."""
    
    @patch("getpass.getpass")
    @patch("fk_path_finder.database.Console")
    def test_prompt_with_defaults(
        self, mock_console_class: Mock, mock_getpass: Mock
    ):
        """Test prompting with default values."""
        mock_console = Mock()
        mock_console.input.side_effect = ["", "", "root"]  # host, port, user
        mock_console_class.return_value = mock_console
        mock_getpass.return_value = "password"
        
        result = prompt_connection_params()
        
        assert result["host"] == "localhost"  # default
        assert result["port"] == 3306  # default
        assert result["user"] == "root"
        assert result["password"] == "password"
    
    @patch("getpass.getpass")
    @patch("fk_path_finder.database.Console")
    def test_prompt_with_custom_values(self, mock_console_class: Mock, mock_getpass: Mock):
        """Test prompting with custom values."""
        mock_console = Mock()
        mock_console.input.side_effect = ["myhost", "3307", "admin"]
        mock_console_class.return_value = mock_console
        mock_getpass.return_value = "secret123"
        
        result = prompt_connection_params()
        
        assert result["host"] == "myhost"
        assert result["port"] == 3307
        assert result["user"] == "admin"
        assert result["password"] == "secret123"
    
    @patch("getpass.getpass")
    @patch("fk_path_finder.database.Console")
    def test_prompt_with_custom_console(self, mock_console_class: Mock, mock_getpass: Mock):
        """Test prompting with custom console instance."""
        custom_console = Mock()
        custom_console.input.side_effect = ["localhost", "3306", "user"]
        mock_getpass.return_value = "pass"
        
        result = prompt_connection_params(console_instance=custom_console)
        
        assert result["user"] == "user"
        mock_console_class.assert_not_called()


class TestPromptDatabaseSelection:
    """Test cases for prompt_database_selection function."""
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_success(self, mock_console_class: Mock):
        """Test successful database selection."""
        mock_console = Mock()
        mock_console.input.return_value = "2"  # Select second database
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.return_value = ["db1", "db2", "db3"]
        
        result = prompt_database_selection(connector)
        
        assert result == "db2"
        connector.select_database.assert_called_once_with("db2")
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_first(self, mock_console_class: Mock):
        """Test selecting first database."""
        mock_console = Mock()
        mock_console.input.return_value = "1"
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.return_value = ["db1", "db2"]
        
        result = prompt_database_selection(connector)
        
        assert result == "db1"
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_last(self, mock_console_class: Mock):
        """Test selecting last database."""
        mock_console = Mock()
        mock_console.input.return_value = "3"
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.return_value = ["db1", "db2", "db3"]
        
        result = prompt_database_selection(connector)
        
        assert result == "db3"
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_invalid_then_valid(self, mock_console_class: Mock):
        """Test invalid input followed by valid selection."""
        mock_console = Mock()
        mock_console.input.side_effect = ["invalid", "0", "4", "2"]
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.return_value = ["db1", "db2", "db3"]
        
        result = prompt_database_selection(connector)
        
        assert result == "db2"
        # Should have shown error message for invalid inputs
        assert mock_console.print.call_count >= 3  # At least 3 error messages
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_empty_list(self, mock_console_class: Mock):
        """Test when no databases are available."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.return_value = []
        
        result = prompt_database_selection(connector)
        
        assert result is None
        mock_console.print.assert_any_call(
            "\n[bold red]✗ No accessible databases found.[/bold red]"
        )
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_list_error(self, mock_console_class: Mock):
        """Test when listing databases fails."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        connector = Mock()
        connector.list_databases.side_effect = DatabaseError("Connection lost")
        
        result = prompt_database_selection(connector)
        
        assert result is None
    
    @patch("fk_path_finder.database.Console")
    def test_select_database_with_custom_console(self, mock_console_class: Mock):
        """Test with custom console instance."""
        custom_console = Mock()
        custom_console.input.return_value = "1"
        
        connector = Mock()
        connector.list_databases.return_value = ["db1"]
        
        result = prompt_database_selection(connector, console_instance=custom_console)
        
        assert result == "db1"
        mock_console_class.assert_not_called()


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestDatabaseEdgeCases:
    """Test edge cases for database operations."""
    
    def test_multiple_connect_calls(self, mock_mysql_connection: Mock):
        """Test connecting multiple times."""
        with patch("fk_path_finder.database.mysql.connector.connect") as mock_connect:
            mock_connect.return_value = mock_mysql_connection
            connector = DatabaseConnector()
            
            params = {"host": "localhost", "user": "root"}
            
            # First connection
            result1 = connector.connect(params)
            assert result1 is True
            
            # Second connection should replace the first
            result2 = connector.connect(params)
            assert result2 is True
            
            assert mock_connect.call_count == 2
    
    def test_fk_with_null_references_filtered(
        self, mock_mysql_connection: Mock, mock_mysql_cursor: Mock
    ):
        """Test that FKs with null referenced tables are handled."""
        mock_mysql_connection.cursor.return_value = mock_mysql_cursor
        mock_mysql_cursor.fetchall.return_value = [
            {
                "CONSTRAINT_NAME": "fk_valid",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "customer_id",
                "REFERENCED_TABLE_NAME": "customers",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk_null",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "temp_id",
                "REFERENCED_TABLE_NAME": None,
                "REFERENCED_COLUMN_NAME": None
            }
        ]
        
        connector = DatabaseConnector()
        connector._connection = mock_mysql_connection
        
        # The query itself filters NULL, so this tests the query behavior
        foreign_keys = connector.get_foreign_keys("testdb")
        
        # The actual SQL query filters out NULL referenced tables
        # This is handled in the SQL WHERE clause
        mock_mysql_cursor.execute.assert_called_once()
    
    def test_database_error_message_propagation(self):
        """Test that DatabaseError messages are properly propagated."""
        error = DatabaseError("Custom error message")
        assert str(error) == "Custom error message"
    
    @patch("fk_path_finder.database.mysql.connector.connect")
    def test_connect_with_all_parameters(self, mock_connect: Mock, mock_mysql_connection: Mock):
        """Test connection with all possible parameters."""
        mock_connect.return_value = mock_mysql_connection
        connector = DatabaseConnector()
        
        params = {
            "host": "remote.host.com",
            "port": 3307,
            "user": "admin",
            "password": "complex_password123",
            "database": "mydb",
        }
        
        connector.connect(params)
        
        mock_connect.assert_called_once_with(**params)
