"""Comprehensive tests for finder module."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from typing import List, Optional

from fk_path_finder.finder import FKPathFinder, FKPathFinderError
from fk_path_finder.database import DatabaseError, DatabaseConnector
from fk_path_finder.types import Config, PathResult, ForeignKeyDict


# =============================================================================
# Test FKPathFinder Initialization
# =============================================================================

class TestFKPathFinderInit:
    """Test cases for FKPathFinder initialization."""
    
    def test_init_default(self):
        """Test initialization with default config."""
        finder = FKPathFinder()
        
        assert finder.config is not None
        assert finder.config.host == "localhost"
        assert finder.connector is not None
        assert finder.graph_builder is not None
        assert finder._database is None
        assert finder._foreign_keys == []
    
    def test_init_with_config(self, sample_config: Config):
        """Test initialization with custom config."""
        finder = FKPathFinder(sample_config)
        
        assert finder.config == sample_config
        assert finder.config.host == "localhost"
        assert finder.config.user == "root"
    
    def test_init_with_custom_console(self, sample_config: Config):
        """Test initialization with custom console."""
        custom_console = Mock()
        finder = FKPathFinder(sample_config, console=custom_console)
        
        assert finder.console == custom_console
    
    def test_database_property(self, sample_config: Config):
        """Test database property."""
        finder = FKPathFinder(sample_config)
        
        assert finder.database is None
        
        finder._database = "testdb"
        assert finder.database == "testdb"
    
    def test_foreign_keys_property(self, sample_config: Config):
        """Test foreign_keys property."""
        finder = FKPathFinder(sample_config)
        
        assert finder.foreign_keys == []
        
        fk_list = [{"CONSTRAINT_NAME": "fk1"}]
        finder._foreign_keys = fk_list
        assert finder.foreign_keys == fk_list


# =============================================================================
# Test Connection Operations
# =============================================================================

class TestFKPathFinderConnection:
    """Test cases for connection operations."""
    
    @patch("fk_path_finder.finder.DatabaseConnector")
    def test_connect_success(self, mock_connector_class: Mock, sample_config: Config):
        """Test successful connection."""
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        mock_connector.connect.return_value = True
        
        finder = FKPathFinder(sample_config)
        result = finder.connect()
        
        assert result is True
        mock_connector.connect.assert_called_once()
        # Verify connection params were passed
        call_args = mock_connector.connect.call_args[0][0]
        assert call_args["host"] == "localhost"
        assert call_args["user"] == "root"
    
    @patch("fk_path_finder.finder.DatabaseConnector")
    def test_connect_failure(self, mock_connector_class: Mock, sample_config: Config):
        """Test connection failure."""
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        mock_connector.connect.side_effect = DatabaseError("Connection refused")
        
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="Connection refused"):
            finder.connect()
    
    @patch("fk_path_finder.finder.DatabaseConnector")
    def test_connect_no_user(self, mock_connector_class: Mock, sample_config: Config):
        """Test connection without user raises error."""
        sample_config.user = ""
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="user is required"):
            finder.connect()
    
    @patch("fk_path_finder.finder.DatabaseConnector")
    def test_connect_no_password(self, mock_connector_class: Mock, sample_config: Config):
        """Test connection without password (should still work)."""
        mock_connector = Mock()
        mock_connector_class.return_value = mock_connector
        mock_connector.connect.return_value = True
        
        sample_config.password = ""
        finder = FKPathFinder(sample_config)
        result = finder.connect()
        
        assert result is True
    
    def test_disconnect(self, sample_config: Config):
        """Test disconnect."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        
        finder.disconnect()
        
        finder.connector.disconnect.assert_called_once()


# =============================================================================
# Test Database Selection
# =============================================================================

class TestFKPathFinderDatabaseSelection:
    """Test cases for database selection."""
    
    def test_select_database_with_param(self, sample_config: Config):
        """Test selecting database with explicit parameter."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.select_database.return_value = True
        
        result = finder.select_database("mydb")
        
        assert result == "mydb"
        assert finder.database == "mydb"
        finder.connector.select_database.assert_called_once_with("mydb")
    
    def test_select_database_from_config(self, sample_config: Config):
        """Test selecting database from config."""
        sample_config.database = "configdb"
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.select_database.return_value = True
        
        result = finder.select_database()
        
        assert result == "configdb"
        assert finder.database == "configdb"
    
    def test_select_database_failure(self, sample_config: Config):
        """Test selecting database that fails."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.select_database.side_effect = DatabaseError("Database not found")
        
        with pytest.raises(FKPathFinderError, match="Database not found"):
            finder.select_database("nonexistent")
    
    def test_select_database_none(self, sample_config: Config):
        """Test selecting database when none specified."""
        sample_config.database = None
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="No database specified"):
            finder.select_database()


# =============================================================================
# Test List Databases
# =============================================================================

class TestFKPathFinderListDatabases:
    """Test cases for listing databases."""
    
    def test_list_databases_success(self, sample_config: Config):
        """Test listing databases successfully."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.list_databases.return_value = ["db1", "db2", "db3"]
        
        result = finder.list_databases()
        
        assert result == ["db1", "db2", "db3"]
    
    def test_list_databases_error(self, sample_config: Config):
        """Test listing databases when error occurs."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.list_databases.side_effect = DatabaseError("Not connected")
        
        with pytest.raises(FKPathFinderError, match="Not connected"):
            finder.list_databases()


# =============================================================================
# Test Foreign Key Operations
# =============================================================================

class TestFKPathFinderForeignKeys:
    """Test cases for foreign key operations."""
    
    def test_fetch_foreign_keys_success(self, sample_config: Config):
        """Test fetching foreign keys successfully."""
        sample_fks = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "customer_id",
                "REFERENCED_TABLE_NAME": "customers",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        
        finder = FKPathFinder(sample_config)
        finder._database = "testdb"
        finder.connector = Mock()
        finder.connector.get_foreign_keys.return_value = sample_fks
        
        result = finder.fetch_foreign_keys()
        
        assert result == sample_fks
        assert finder.foreign_keys == sample_fks
        finder.connector.get_foreign_keys.assert_called_once_with("testdb")
    
    def test_fetch_foreign_keys_no_database(self, sample_config: Config):
        """Test fetching foreign keys without database selected."""
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="No database selected"):
            finder.fetch_foreign_keys()
    
    def test_fetch_foreign_keys_error(self, sample_config: Config):
        """Test fetching foreign keys when error occurs."""
        finder = FKPathFinder(sample_config)
        finder._database = "testdb"
        finder.connector = Mock()
        finder.connector.get_foreign_keys.side_effect = DatabaseError("Query failed")
        
        with pytest.raises(FKPathFinderError, match="Query failed"):
            finder.fetch_foreign_keys()
    
    def test_fetch_foreign_keys_empty(self, sample_config: Config):
        """Test fetching foreign keys when none exist."""
        finder = FKPathFinder(sample_config)
        finder._database = "testdb"
        finder.connector = Mock()
        finder.connector.get_foreign_keys.return_value = []
        
        result = finder.fetch_foreign_keys()
        
        assert result == []
        assert finder.foreign_keys == []


# =============================================================================
# Test Graph Building
# =============================================================================

class TestFKPathFinderGraphBuilding:
    """Test cases for graph building."""
    
    def test_build_graph_success(self, sample_config: Config):
        """Test building graph successfully."""
        sample_fks = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "customer_id",
                "REFERENCED_TABLE_NAME": "customers",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = sample_fks
        finder.graph_builder = Mock()
        finder.graph_builder.build.return_value = {"orders.customer_id": {"customers.id"}}
        
        result = finder.build_graph()
        
        assert result is not None
        finder.graph_builder.build.assert_called_once_with(sample_fks)
    
    def test_build_graph_no_foreign_keys(self, sample_config: Config):
        """Test building graph without foreign keys."""
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="No foreign keys loaded"):
            finder.build_graph()
    
    def test_build_graph_empty_foreign_keys(self, sample_config: Config):
        """Test building graph with empty foreign keys."""
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = []
        
        with pytest.raises(FKPathFinderError, match="No foreign keys loaded"):
            finder.build_graph()


# =============================================================================
# Test Display Foreign Keys
# =============================================================================

class TestFKPathFinderDisplayForeignKeys:
    """Test cases for displaying foreign keys."""
    
    def test_display_foreign_keys_with_data(self, sample_config: Config):
        """Test displaying foreign keys when data exists."""
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "customer_id",
                "REFERENCED_TABLE_NAME": "customers",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        finder.console = Mock()
        
        finder.display_foreign_keys()
        
        # Should have been called (with a Table object)
        finder.console.print.assert_called()
        # The print was called with a Rich Table object, just verify it was called
        assert finder.console.print.call_count >= 1
    
    def test_display_foreign_keys_empty(self, sample_config: Config):
        """Test displaying foreign keys when empty."""
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = []
        finder.console = Mock()
        
        finder.display_foreign_keys()
        
        finder.console.print.assert_any_call(
            "\n[bold red]✗ No foreign keys found in this database.[/bold red]"
        )
    
    def test_display_foreign_keys_none(self, sample_config: Config):
        """Test displaying foreign keys when None."""
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = None
        finder.console = Mock()
        
        finder.display_foreign_keys()
        
        finder.console.print.assert_any_call(
            "\n[bold red]✗ No foreign keys found in this database.[/bold red]"
        )


# =============================================================================
# Test Find Paths
# =============================================================================

class TestFKPathFinderFindPaths:
    """Test cases for finding paths."""
    
    def test_find_paths_success(self, sample_config: Config):
        """Test finding paths successfully."""
        finder = FKPathFinder(sample_config)
        finder.graph_builder = Mock()
        finder.graph_builder.parse_reference.side_effect = [
            ("column", ["table_a.id"]),
            ("column", ["table_b.id"])
        ]
        
        mock_result = Mock(spec=PathResult)
        mock_result.paths = [["table_a.id", "table_b.id"]]
        mock_result.total_found = 1
        mock_result.limit_reached = False
        
        finder.graph_builder.find_all_paths.return_value = mock_result
        
        result = finder.find_paths("table_a.id", "table_b.id")
        
        assert result == mock_result
        finder.graph_builder.find_all_paths.assert_called_once()
    
    def test_find_paths_invalid_start(self, sample_config: Config):
        """Test finding paths with invalid start reference."""
        finder = FKPathFinder(sample_config)
        finder.graph_builder = Mock()
        finder.graph_builder.parse_reference.return_value = ("unknown", [])
        finder.graph_builder.get_tables.return_value = {"table1", "table2"}
        
        with pytest.raises(FKPathFinderError, match="Start reference"):
            finder.find_paths("invalid", "table2")
    
    def test_find_paths_invalid_end(self, sample_config: Config):
        """Test finding paths with invalid end reference."""
        finder = FKPathFinder(sample_config)
        finder.graph_builder = Mock()
        finder.graph_builder.parse_reference.side_effect = [
            ("column", ["table_a.id"]),
            ("unknown", [])
        ]
        
        with pytest.raises(FKPathFinderError, match="End reference"):
            finder.find_paths("table_a.id", "invalid")
    
    def test_find_paths_table_reference(self, sample_config: Config):
        """Test finding paths with table reference."""
        finder = FKPathFinder(sample_config)
        finder.graph_builder = Mock()
        finder.graph_builder.parse_reference.side_effect = [
            ("table", ["table_a.col1", "table_a.col2"]),
            ("column", ["table_b.id"])
        ]
        
        mock_result = Mock(spec=PathResult)
        mock_result.paths = [["table_a.col1", "table_b.id"]]
        mock_result.total_found = 1
        
        finder.graph_builder.find_all_paths.return_value = mock_result
        
        result = finder.find_paths("table_a", "table_b.id")
        
        assert result.total_found == 1


# =============================================================================
# Test Display Paths
# =============================================================================

class TestFKPathFinderDisplayPaths:
    """Test cases for displaying paths."""
    
    def test_display_paths_empty(self, sample_config: Config):
        """Test displaying empty results."""
        finder = FKPathFinder(sample_config)
        finder.console = Mock()
        
        result = PathResult(
            paths=[],
            total_found=0,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        finder.display_paths(result)
        
        finder.console.print.assert_any_call(
            "\n[bold red]✗ No paths found.[/bold red]"
        )
    
    def test_display_paths_with_data(self, sample_config: Config):
        """Test displaying paths with data."""
        finder = FKPathFinder(sample_config)
        finder.console = Mock()
        
        # Use properly formatted node names (table.column format)
        result = PathResult(
            paths=[["table_a.id", "table_b.id"], ["table_a.id", "table_c.id", "table_b.id"]],
            total_found=2,
            limit_reached=False,
            start_nodes=["table_a.id"],
            end_nodes=["table_b.id"]
        )
        
        finder.display_paths(result)
        
        # Should show success message - verify print was called
        finder.console.print.assert_called()
        calls = [str(call) for call in finder.console.print.call_args_list]
        assert any("Found" in call or "path" in call.lower() for call in calls)
    
    def test_display_paths_with_limit_reached(self, sample_config: Config):
        """Test displaying results with limit reached."""
        finder = FKPathFinder(sample_config)
        finder.console = Mock()
        
        # Use properly formatted node names (table.column format)
        result = PathResult(
            paths=[["table_a.id", "table_b.id"], ["table_a.id", "table_c.id", "table_b.id"]],
            total_found=2,
            limit_reached=True,
            start_nodes=["table_a.id"],
            end_nodes=["table_b.id"]
        )
        
        finder.display_paths(result)
        
        # Should indicate limit was reached - verify print was called
        finder.console.print.assert_called()
        calls = [str(call) for call in finder.console.print.call_args_list]
        assert any("limit" in call.lower() for call in calls)
    
    def test_display_paths_with_display_limit(self, sample_config: Config):
        """Test displaying paths with display limit."""
        finder = FKPathFinder(sample_config)
        finder.console = Mock()
        
        # Use properly formatted node names (table.column format)
        result = PathResult(
            paths=[[f"table_{i}.id", f"table_{i+1}.id"] for i in range(50)],
            total_found=50,
            limit_reached=False,
            start_nodes=["table_0.id"],
            end_nodes=["table_50.id"]
        )
        
        finder.display_paths(result, display_limit=5)
        
        # Should indicate more paths exist - verify print was called
        finder.console.print.assert_called()
        calls = [str(call) for call in finder.console.print.call_args_list]
        assert any("more" in call.lower() for call in calls)


# =============================================================================
# Test Batch Mode
# =============================================================================

class TestFKPathFinderRunBatch:
    """Test cases for batch mode."""
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "select_database")
    @patch.object(FKPathFinder, "fetch_foreign_keys")
    @patch.object(FKPathFinder, "build_graph")
    @patch.object(FKPathFinder, "find_paths")
    @patch.object(FKPathFinder, "display_paths")
    @patch.object(FKPathFinder, "disconnect")
    def test_run_batch_success(
        self,
        mock_disconnect: Mock,
        mock_display: Mock,
        mock_find: Mock,
        mock_build: Mock,
        mock_fetch: Mock,
        mock_select: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test batch mode success."""
        mock_connect.return_value = True
        mock_fetch.return_value = [{"CONSTRAINT_NAME": "fk1"}]
        mock_build.return_value = {"table.col": {"other.col"}}
        
        mock_result = Mock(spec=PathResult)
        mock_result.paths = [["table_a.id", "table_b.id"]]
        mock_find.return_value = mock_result
        
        finder = FKPathFinder(sample_config)
        # Set up the foreign keys to pass the empty check
        finder._foreign_keys = [{"CONSTRAINT_NAME": "fk1"}]
        result = finder.run_batch("table_a", "table_b")
        
        assert result == mock_result
        mock_connect.assert_called_once()
        mock_select.assert_called_once()
        mock_fetch.assert_called_once()
        mock_build.assert_called_once()
        mock_find.assert_called_once_with("table_a", "table_b")
        mock_display.assert_called_once()
        mock_disconnect.assert_called_once()
    
    @patch.object(FKPathFinder, "connect")
    def test_run_batch_connect_failure(self, mock_connect: Mock, sample_config: Config):
        """Test batch mode when connection fails."""
        mock_connect.return_value = False
        
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="Failed to connect"):
            finder.run_batch("table_a", "table_b")
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "select_database")
    @patch.object(FKPathFinder, "fetch_foreign_keys")
    @patch.object(FKPathFinder, "build_graph")
    @patch.object(FKPathFinder, "find_paths")
    @patch.object(FKPathFinder, "display_paths")
    @patch.object(FKPathFinder, "disconnect")
    def test_run_batch_plain_output(
        self,
        mock_disconnect: Mock,
        mock_display: Mock,
        mock_find: Mock,
        mock_build: Mock,
        mock_fetch: Mock,
        mock_select: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test batch mode with plain output."""
        mock_connect.return_value = True
        mock_fetch.return_value = [{"CONSTRAINT_NAME": "fk1"}]
        mock_build.return_value = {"table.col": {"other.col"}}
        
        mock_result = Mock(spec=PathResult)
        mock_result.paths = [["table_a.id", "table_b.id"]]
        mock_find.return_value = mock_result
        
        finder = FKPathFinder(sample_config)
        finder._foreign_keys = [{"CONSTRAINT_NAME": "fk1"}]
        finder._display_paths_plain = Mock()
        
        result = finder.run_batch("table_a", "table_b", output_format="plain")
        
        finder._display_paths_plain.assert_called_once_with(mock_result)
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "select_database")
    @patch.object(FKPathFinder, "fetch_foreign_keys")
    @patch.object(FKPathFinder, "build_graph")
    @patch.object(FKPathFinder, "find_paths")
    @patch.object(FKPathFinder, "display_paths")
    @patch.object(FKPathFinder, "disconnect")
    def test_run_batch_always_disconnects(
        self,
        mock_disconnect: Mock,
        mock_display: Mock,
        mock_find: Mock,
        mock_build: Mock,
        mock_fetch: Mock,
        mock_select: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test that disconnect is always called even on error."""
        mock_connect.return_value = True
        mock_find.side_effect = FKPathFinderError("Path finding failed")
        
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError):
            finder.run_batch("table_a", "table_b")
        
        mock_disconnect.assert_called_once()
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "select_database")
    @patch.object(FKPathFinder, "fetch_foreign_keys")
    @patch.object(FKPathFinder, "disconnect")
    def test_run_batch_no_foreign_keys(
        self,
        mock_disconnect: Mock,
        mock_fetch: Mock,
        mock_select: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test batch mode when no foreign keys found."""
        mock_connect.return_value = True
        mock_fetch.return_value = []
        
        finder = FKPathFinder(sample_config)
        
        with pytest.raises(FKPathFinderError, match="No foreign keys found"):
            finder.run_batch("table_a", "table_b")


# =============================================================================
# Test Plain Display
# =============================================================================

class TestFKPathFinderPlainDisplay:
    """Test cases for plain text display."""
    
    def test_display_paths_plain_empty(self, sample_config: Config):
        """Test plain display with empty results."""
        finder = FKPathFinder(sample_config)
        
        result = PathResult(
            paths=[],
            total_found=0,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        # Capture print output
        with patch("builtins.print") as mock_print:
            finder._display_paths_plain(result)
            mock_print.assert_any_call("No paths found.")
    
    def test_display_paths_plain_with_data(self, sample_config: Config):
        """Test plain display with paths."""
        finder = FKPathFinder(sample_config)
        finder.config.display_limit = 10
        
        result = PathResult(
            paths=[["table_a.id", "table_b.id"]],
            total_found=1,
            limit_reached=False,
            start_nodes=["table_a.id"],
            end_nodes=["table_b.id"]
        )
        
        with patch("builtins.print") as mock_print:
            finder._display_paths_plain(result)
            
            # Should print summary
            mock_print.assert_any_call("Found 1 path(s)")
    
    def test_display_paths_plain_with_limit(self, sample_config: Config):
        """Test plain display with limit reached."""
        finder = FKPathFinder(sample_config)
        finder.config.display_limit = 10
        
        # Use properly formatted node names (table.column format)
        result = PathResult(
            paths=[["table_a.id", "table_b.id"]],
            total_found=1,
            limit_reached=True,
            start_nodes=["table_a.id"],
            end_nodes=["table_b.id"]
        )
        
        with patch("builtins.print") as mock_print:
            finder._display_paths_plain(result)
            
            mock_print.assert_any_call("Found 1 path(s)")
            mock_print.assert_any_call("(search limit reached)")


# =============================================================================
# Test Interactive Mode
# =============================================================================

class TestFKPathFinderInteractive:
    """Test cases for interactive mode."""
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "select_database")
    @patch.object(FKPathFinder, "fetch_foreign_keys")
    @patch.object(FKPathFinder, "build_graph")
    @patch.object(FKPathFinder, "display_foreign_keys")
    @patch.object(FKPathFinder, "disconnect")
    def test_interactive_no_foreign_keys(
        self,
        mock_disconnect: Mock,
        mock_display: Mock,
        mock_build: Mock,
        mock_fetch: Mock,
        mock_select: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test interactive mode when no foreign keys."""
        mock_connect.return_value = True
        mock_fetch.return_value = []
        
        finder = FKPathFinder(sample_config)
        # Create mock console with status context manager support
        from unittest.mock import MagicMock
        mock_console = MagicMock()
        status_cm = MagicMock()
        status_cm.__enter__ = MagicMock(return_value=status_cm)
        status_cm.__exit__ = MagicMock(return_value=None)
        mock_console.status = MagicMock(return_value=status_cm)
        finder.console = mock_console
        finder._database = "testdb"  # Pre-set database to avoid prompt
        
        finder.interactive_find_paths()
        
        mock_display.assert_called_once()
        mock_disconnect.assert_called_once()
    
    @patch.object(FKPathFinder, "connect")
    @patch.object(FKPathFinder, "disconnect")
    def test_interactive_connect_failure(
        self,
        mock_disconnect: Mock,
        mock_connect: Mock,
        sample_config: Config
    ):
        """Test interactive mode when connection fails."""
        mock_connect.return_value = False
        
        finder = FKPathFinder(sample_config)
        finder.interactive_find_paths()
        
        mock_disconnect.assert_not_called()  # Not connected, so no disconnect


# =============================================================================
# Test Error Handling
# =============================================================================

class TestFKPathFinderErrors:
    """Test cases for error handling."""
    
    def test_error_message_propagation(self):
        """Test that error messages are properly propagated."""
        error = FKPathFinderError("Custom error message")
        assert str(error) == "Custom error message"
    
    def test_database_error_wrapped(self, sample_config: Config):
        """Test that DatabaseError is wrapped in FKPathFinderError."""
        finder = FKPathFinder(sample_config)
        finder.connector = Mock()
        finder.connector.list_databases.side_effect = DatabaseError("DB Error")
        
        with pytest.raises(FKPathFinderError, match="DB Error"):
            finder.list_databases()


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
class TestFKPathFinderIntegration:
    """Integration tests for FKPathFinder (requires real MySQL connection)."""
    
    def test_full_workflow(self):
        """Test the complete workflow end-to-end."""
        # This test requires a real MySQL connection
        # Should be run with: pytest -m integration
        pass
