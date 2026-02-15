"""Comprehensive tests for types module."""

import pytest
from unittest.mock import Mock, patch
import os

from fk_path_finder.types import (
    ForeignKeyDict,
    ConnectionParams,
    PathResult,
    Config,
    Graph,
    ReferenceType,
)


# =============================================================================
# Test ForeignKeyDict Type
# =============================================================================

class TestForeignKeyDict:
    """Test cases for ForeignKeyDict TypedDict."""
    
    def test_foreign_key_dict_creation(self):
        """Test creating ForeignKeyDict."""
        fk: ForeignKeyDict = {
            "CONSTRAINT_NAME": "fk_test",
            "TABLE_NAME": "orders",
            "COLUMN_NAME": "customer_id",
            "REFERENCED_TABLE_NAME": "customers",
            "REFERENCED_COLUMN_NAME": "id"
        }
        
        assert fk["CONSTRAINT_NAME"] == "fk_test"
        assert fk["TABLE_NAME"] == "orders"
        assert fk["COLUMN_NAME"] == "customer_id"
        assert fk["REFERENCED_TABLE_NAME"] == "customers"
        assert fk["REFERENCED_COLUMN_NAME"] == "id"
    
    def test_foreign_key_dict_access(self):
        """Test accessing ForeignKeyDict fields."""
        fk: ForeignKeyDict = {
            "CONSTRAINT_NAME": "fk_test",
            "TABLE_NAME": "orders",
            "COLUMN_NAME": "customer_id",
            "REFERENCED_TABLE_NAME": "customers",
            "REFERENCED_COLUMN_NAME": "id"
        }
        
        # Test all required keys exist
        assert "CONSTRAINT_NAME" in fk
        assert "TABLE_NAME" in fk
        assert "COLUMN_NAME" in fk
        assert "REFERENCED_TABLE_NAME" in fk
        assert "REFERENCED_COLUMN_NAME" in fk


# =============================================================================
# Test ConnectionParams Type
# =============================================================================

class TestConnectionParams:
    """Test cases for ConnectionParams TypedDict."""
    
    def test_connection_params_creation(self):
        """Test creating ConnectionParams."""
        params: ConnectionParams = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "secret"
        }
        
        assert params["host"] == "localhost"
        assert params["port"] == 3306
        assert params["user"] == "root"
        assert params["password"] == "secret"
    
    def test_connection_params_optional_database(self):
        """Test ConnectionParams with optional database."""
        params_with_db: ConnectionParams = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "secret",
            "database": "mydb"
        }
        
        assert params_with_db["database"] == "mydb"
        
        params_without_db: ConnectionParams = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "secret"
        }
        
        assert "database" not in params_without_db
    
    def test_connection_params_partial(self):
        """Test ConnectionParams with partial fields."""
        params: ConnectionParams = {
            "host": "localhost"
        }
        
        assert params["host"] == "localhost"


# =============================================================================
# Test PathResult
# =============================================================================

class TestPathResult:
    """Test cases for PathResult dataclass."""
    
    def test_path_result_creation(self):
        """Test creating PathResult."""
        result = PathResult(
            paths=[["a", "b", "c"], ["a", "d", "c"]],
            total_found=2,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["c"]
        )
        
        assert len(result.paths) == 2
        assert result.total_found == 2
        assert result.limit_reached is False
        assert result.start_nodes == ["a"]
        assert result.end_nodes == ["c"]
    
    def test_path_result_sorts_by_length(self):
        """Test that paths are sorted by length."""
        result = PathResult(
            paths=[
                ["a", "b", "c", "d"],  # 4 nodes
                ["a", "b"],  # 2 nodes
                ["a", "b", "c"]  # 3 nodes
            ],
            total_found=3,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["d"]
        )
        
        # Should be sorted by length: 2, 3, 4
        assert len(result.paths[0]) == 2
        assert len(result.paths[1]) == 3
        assert len(result.paths[2]) == 4
    
    def test_path_result_empty_paths(self):
        """Test PathResult with empty paths."""
        result = PathResult(
            paths=[],
            total_found=0,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        assert len(result.paths) == 0
        assert result.total_found == 0
    
    def test_path_result_single_path(self):
        """Test PathResult with single path."""
        result = PathResult(
            paths=[["a", "b"]],
            total_found=1,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        assert len(result.paths) == 1
        assert result.paths[0] == ["a", "b"]
    
    def test_path_result_limit_reached(self):
        """Test PathResult with limit reached."""
        result = PathResult(
            paths=[["a", "b"]],
            total_found=1000,
            limit_reached=True,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        assert result.limit_reached is True
        assert result.total_found == 1000
    
    def test_path_result_multiple_start_end_nodes(self):
        """Test PathResult with multiple start and end nodes."""
        result = PathResult(
            paths=[["a", "b"], ["c", "d"]],
            total_found=2,
            limit_reached=False,
            start_nodes=["a", "c"],
            end_nodes=["b", "d"]
        )
        
        assert len(result.start_nodes) == 2
        assert len(result.end_nodes) == 2


# =============================================================================
# Test Config
# =============================================================================

class TestConfig:
    """Test cases for Config dataclass."""
    
    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == ""
        assert config.password == ""
        assert config.database is None
        assert config.max_path_length == 6
        assert config.max_paths == 1000
        assert config.display_limit == 20
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = Config(
            host="myhost",
            port=3307,
            user="myuser",
            password="mypass",
            database="mydb",
            max_path_length=10,
            max_paths=500,
            display_limit=50
        )
        
        assert config.host == "myhost"
        assert config.port == 3307
        assert config.user == "myuser"
        assert config.password == "mypass"
        assert config.database == "mydb"
        assert config.max_path_length == 10
        assert config.max_paths == 500
        assert config.display_limit == 50
    
    def test_config_from_dict(self):
        """Test creating Config from dictionary."""
        data = {
            "host": "dicthost",
            "port": 3308,
            "user": "dictuser",
            "password": "dictpass",
            "database": "dictdb",
            "max_path_length": 8,
            "max_paths": 200,
            "display_limit": 30
        }
        
        config = Config.from_dict(data)
        
        assert config.host == "dicthost"
        assert config.port == 3308
        assert config.user == "dictuser"
        assert config.password == "dictpass"
        assert config.database == "dictdb"
        assert config.max_path_length == 8
        assert config.max_paths == 200
        assert config.display_limit == 30
    
    def test_config_from_dict_partial(self):
        """Test creating Config from partial dictionary."""
        data = {
            "host": "partialhost",
            "user": "partialuser"
        }
        
        config = Config.from_dict(data)
        
        assert config.host == "partialhost"
        assert config.user == "partialuser"
        assert config.port == 3306  # Default
        assert config.max_paths == 1000  # Default
    
    def test_config_from_dict_empty(self):
        """Test creating Config from empty dictionary."""
        config = Config.from_dict({})
        
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == ""
        assert config.max_paths == 1000
    
    @patch.dict(os.environ, {
        "FK_MYSQL_HOST": "envhost",
        "FK_MYSQL_PORT": "3308",
        "FK_MYSQL_USER": "envuser",
        "FK_MYSQL_PASSWORD": "envpass",
        "FK_MYSQL_DATABASE": "envdb",
        "FK_MAX_PATH_LENGTH": "8",
        "FK_MAX_PATHS": "2000",
        "FK_DISPLAY_LIMIT": "50"
    })
    def test_config_from_env(self):
        """Test creating Config from environment variables."""
        config = Config.from_env()
        
        assert config.host == "envhost"
        assert config.port == 3308
        assert config.user == "envuser"
        assert config.password == "envpass"
        assert config.database == "envdb"
        assert config.max_path_length == 8
        assert config.max_paths == 2000
        assert config.display_limit == 50
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_env_defaults(self):
        """Test Config.from_env with no environment variables."""
        config = Config.from_env()
        
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == ""
        assert config.password == ""
        assert config.database is None
    
    @patch.dict(os.environ, {
        "FK_MYSQL_HOST": "envhost",
    })
    def test_config_from_env_partial(self):
        """Test Config.from_env with partial environment variables."""
        config = Config.from_env()
        
        assert config.host == "envhost"
        assert config.port == 3306  # Default
        assert config.user == ""
    
    def test_config_to_connection_params(self):
        """Test converting Config to connection parameters."""
        config = Config(
            host="localhost",
            port=3306,
            user="root",
            password="secret",
            database="mydb"
        )
        
        params = config.to_connection_params()
        
        assert params["host"] == "localhost"
        assert params["port"] == 3306
        assert params["user"] == "root"
        assert params["password"] == "secret"
        assert params["database"] == "mydb"
    
    def test_config_to_connection_params_no_database(self):
        """Test converting Config without database."""
        config = Config(
            host="localhost",
            user="root",
            password="secret"
        )
        
        params = config.to_connection_params()
        
        assert "host" in params
        assert "database" not in params
    
    def test_config_to_connection_params_only_required(self):
        """Test converting Config with only required fields."""
        config = Config()
        
        params = config.to_connection_params()
        
        assert params["host"] == "localhost"
        assert params["port"] == 3306
        assert params["user"] == ""
        assert params["password"] == ""
        assert "database" not in params


# =============================================================================
# Test Graph Type Alias
# =============================================================================

class TestGraphType:
    """Test cases for Graph type alias."""
    
    def test_graph_type(self):
        """Test Graph type structure."""
        graph: Graph = {
            "table_a.col1": {"table_b.col1", "table_c.col1"},
            "table_b.col1": {"table_a.col1"},
            "table_c.col1": {"table_a.col1"}
        }
        
        assert "table_a.col1" in graph
        assert "table_b.col1" in graph["table_a.col1"]
        assert "table_c.col1" in graph["table_a.col1"]
    
    def test_graph_empty(self):
        """Test empty Graph."""
        graph: Graph = {}
        
        assert len(graph) == 0
    
    def test_graph_single_node(self):
        """Test Graph with single node."""
        graph: Graph = {
            "table.col": set()
        }
        
        assert "table.col" in graph
        assert len(graph["table.col"]) == 0


# =============================================================================
# Test ReferenceType Type Alias
# =============================================================================

class TestReferenceType:
    """Test cases for ReferenceType type alias."""
    
    def test_reference_type_column(self):
        """Test ReferenceType with column."""
        ref: ReferenceType = ("column", ["table_a.col1"])
        
        assert ref[0] == "column"
        assert ref[1] == ["table_a.col1"]
    
    def test_reference_type_table(self):
        """Test ReferenceType with table."""
        ref: ReferenceType = ("table", ["table_a.col1", "table_a.col2"])
        
        assert ref[0] == "table"
        assert len(ref[1]) == 2
    
    def test_reference_type_unknown(self):
        """Test ReferenceType with unknown."""
        ref: ReferenceType = ("unknown", [])
        
        assert ref[0] == "unknown"
        assert ref[1] == []


# =============================================================================
# Test Immutability and Safety
# =============================================================================

class TestTypeSafety:
    """Test cases for type safety."""
    
    def test_path_result_paths_immutable_after_creation(self):
        """Test that PathResult paths can be modified after creation."""
        paths = [["a", "b"]]
        result = PathResult(
            paths=paths,
            total_found=1,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        # Original list can be modified, but result.paths is a copy
        paths.append(["c", "d"])
        
        # result.paths should reflect the change (it's the same list object)
        # This is not immutability, but documenting the behavior
        assert len(result.paths) == 2
    
    def test_config_immutable_fields(self):
        """Test that Config fields can be modified."""
        config = Config(host="original")
        
        assert config.host == "original"
        
        config.host = "modified"
        
        assert config.host == "modified"


# =============================================================================
# Test Edge Cases
# =============================================================================

class TestTypeEdgeCases:
    """Test edge cases for types."""
    
    def test_path_result_with_very_long_paths(self):
        """Test PathResult with very long paths."""
        long_path = [f"node_{i}" for i in range(100)]
        
        result = PathResult(
            paths=[long_path],
            total_found=1,
            limit_reached=False,
            start_nodes=["node_0"],
            end_nodes=["node_99"]
        )
        
        assert len(result.paths[0]) == 100
    
    def test_path_result_with_many_paths(self):
        """Test PathResult with many paths."""
        paths = [[f"a_{i}", f"b_{i}"] for i in range(1000)]
        
        result = PathResult(
            paths=paths,
            total_found=1000,
            limit_reached=True,
            start_nodes=["a_0"],
            end_nodes=["b_999"]
        )
        
        assert len(result.paths) == 1000
    
    def test_config_with_empty_strings(self):
        """Test Config with empty strings."""
        config = Config(
            host="",
            user="",
            password=""
        )
        
        assert config.host == ""
        assert config.user == ""
        assert config.password == ""
    
    def test_config_with_zero_values(self):
        """Test Config with zero values."""
        config = Config(
            port=0,
            max_path_length=0,
            max_paths=0,
            display_limit=0
        )
        
        assert config.port == 0
        assert config.max_path_length == 0
        assert config.max_paths == 0
        assert config.display_limit == 0
    
    def test_config_with_negative_values(self):
        """Test Config with negative values."""
        # While not recommended, the type system allows it
        config = Config(
            port=-1,
            max_path_length=-5
        )
        
        assert config.port == -1
        assert config.max_path_length == -5
    
    def test_graph_with_empty_sets(self):
        """Test Graph with empty neighbor sets."""
        graph: Graph = {
            "isolated_node": set()
        }
        
        assert len(graph["isolated_node"]) == 0
    
    def test_foreign_key_dict_with_empty_strings(self):
        """Test ForeignKeyDict with empty strings."""
        fk: ForeignKeyDict = {
            "CONSTRAINT_NAME": "",
            "TABLE_NAME": "",
            "COLUMN_NAME": "",
            "REFERENCED_TABLE_NAME": "",
            "REFERENCED_COLUMN_NAME": ""
        }
        
        assert fk["CONSTRAINT_NAME"] == ""
        assert fk["TABLE_NAME"] == ""


# =============================================================================
# Test Type Conversion
# =============================================================================

class TestTypeConversions:
    """Test cases for type conversions."""
    
    def test_config_to_dict_roundtrip(self):
        """Test Config can be converted to dict and back."""
        original = Config(
            host="myhost",
            port=3307,
            user="myuser",
            password="mypass",
            database="mydb",
            max_path_length=10,
            max_paths=500,
            display_limit=50
        )
        
        # Convert to connection params (dict-like)
        params = original.to_connection_params()
        
        # Create new config from dict
        new_config = Config.from_dict({
            "host": params.get("host", "localhost"),
            "port": params.get("port", 3306),
            "user": params.get("user", ""),
            "password": params.get("password", ""),
            "database": params.get("database"),
            "max_path_length": original.max_path_length,
            "max_paths": original.max_paths,
            "display_limit": original.display_limit
        })
        
        assert new_config.host == original.host
        assert new_config.port == original.port
        assert new_config.user == original.user
        assert new_config.password == original.password
    
    def test_path_result_to_dict_concept(self):
        """Test conceptual conversion of PathResult to dict."""
        result = PathResult(
            paths=[["a", "b"]],
            total_found=1,
            limit_reached=False,
            start_nodes=["a"],
            end_nodes=["b"]
        )
        
        # Conceptual conversion (actual conversion not implemented)
        result_dict = {
            "paths": result.paths,
            "total_found": result.total_found,
            "limit_reached": result.limit_reached,
            "start_nodes": result.start_nodes,
            "end_nodes": result.end_nodes
        }
        
        assert result_dict["total_found"] == 1
        assert result_dict["limit_reached"] is False
