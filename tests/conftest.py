"""Shared fixtures and utilities for all tests."""

from typing import List, Dict, Any, Generator
from unittest.mock import Mock, MagicMock, patch
import pytest

from fk_path_finder.types import Config, ForeignKeyDict, PathResult
from fk_path_finder.database import DatabaseConnector, DatabaseError
from fk_path_finder.graph import GraphBuilder
from fk_path_finder.finder import FKPathFinder


# =============================================================================
# Mock MySQL Connection Fixtures
# =============================================================================

@pytest.fixture
def mock_mysql_connector() -> Generator[Mock, None, None]:
    """Mock the mysql.connector module."""
    with patch("fk_path_finder.database.mysql.connector") as mock:
        yield mock


@pytest.fixture
def mock_mysql_connection() -> Mock:
    """Create a mock MySQL connection."""
    conn = Mock()
    conn.is_connected.return_value = True
    conn.get_server_info.return_value = "8.0.33"
    conn.database = None
    conn.close = Mock()
    return conn


@pytest.fixture
def mock_mysql_cursor() -> Mock:
    """Create a mock MySQL cursor."""
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    cursor.execute = Mock()
    cursor.close = Mock()
    return cursor


@pytest.fixture
def mock_connected_connector(
    mock_mysql_connector: Mock,
    mock_mysql_connection: Mock,
    mock_mysql_cursor: Mock
) -> DatabaseConnector:
    """Create a DatabaseConnector with mocked connection."""
    mock_mysql_connector.connect.return_value = mock_mysql_connection
    mock_mysql_connection.cursor.return_value = mock_mysql_cursor
    
    connector = DatabaseConnector()
    connector.connect({
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "secret"
    })
    return connector


# =============================================================================
# Sample Data Fixtures
# =============================================================================

@pytest.fixture
def sample_foreign_keys() -> List[ForeignKeyDict]:
    """Create sample foreign keys for testing."""
    return [
        {
            "CONSTRAINT_NAME": "fk_film_actor_film",
            "TABLE_NAME": "film_actor",
            "COLUMN_NAME": "film_id",
            "REFERENCED_TABLE_NAME": "film",
            "REFERENCED_COLUMN_NAME": "film_id"
        },
        {
            "CONSTRAINT_NAME": "fk_film_actor_actor",
            "TABLE_NAME": "film_actor",
            "COLUMN_NAME": "actor_id",
            "REFERENCED_TABLE_NAME": "actor",
            "REFERENCED_COLUMN_NAME": "actor_id"
        },
        {
            "CONSTRAINT_NAME": "fk_film_category_film",
            "TABLE_NAME": "film_category",
            "COLUMN_NAME": "film_id",
            "REFERENCED_TABLE_NAME": "film",
            "REFERENCED_COLUMN_NAME": "film_id"
        },
        {
            "CONSTRAINT_NAME": "fk_film_category_category",
            "TABLE_NAME": "film_category",
            "COLUMN_NAME": "category_id",
            "REFERENCED_TABLE_NAME": "category",
            "REFERENCED_COLUMN_NAME": "category_id"
        },
        {
            "CONSTRAINT_NAME": "fk_film_language",
            "TABLE_NAME": "film",
            "COLUMN_NAME": "language_id",
            "REFERENCED_TABLE_NAME": "language",
            "REFERENCED_COLUMN_NAME": "language_id"
        },
    ]


@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration."""
    return Config(
        host="localhost",
        port=3306,
        user="root",
        password="secret",
        database="sakila",
        max_path_length=6,
        max_paths=1000,
        display_limit=20
    )


@pytest.fixture
def sample_path_result() -> PathResult:
    """Create a sample PathResult for testing."""
    return PathResult(
        paths=[
            ["film.film_id", "film_actor.film_id"],
            ["film.film_id", "film_category.film_id"],
        ],
        total_found=2,
        limit_reached=False,
        start_nodes=["film.film_id"],
        end_nodes=["film_actor.film_id", "film_category.film_id"]
    )


@pytest.fixture
def empty_path_result() -> PathResult:
    """Create an empty PathResult for testing."""
    return PathResult(
        paths=[],
        total_found=0,
        limit_reached=False,
        start_nodes=["table1.id"],
        end_nodes=["table2.id"]
    )


@pytest.fixture
def large_path_result() -> PathResult:
    """Create a PathResult with limit reached for testing."""
    return PathResult(
        paths=[[f"node_{i}", f"node_{i+1}"] for i in range(100)],
        total_found=100,
        limit_reached=True,
        start_nodes=["start"],
        end_nodes=["end"]
    )


# =============================================================================
# Graph Fixtures
# =============================================================================

@pytest.fixture
def sample_graph_builder(sample_foreign_keys: List[ForeignKeyDict]) -> GraphBuilder:
    """Create a GraphBuilder with sample data."""
    builder = GraphBuilder()
    builder.build(sample_foreign_keys)
    return builder


@pytest.fixture
def empty_graph_builder() -> GraphBuilder:
    """Create an empty GraphBuilder."""
    return GraphBuilder()


@pytest.fixture
def circular_graph_builder() -> GraphBuilder:
    """Create a GraphBuilder with circular references."""
    builder = GraphBuilder()
    # Create A -> B -> C -> A circular reference
    foreign_keys = [
        {
            "CONSTRAINT_NAME": "fk_a_b",
            "TABLE_NAME": "table_a",
            "COLUMN_NAME": "b_id",
            "REFERENCED_TABLE_NAME": "table_b",
            "REFERENCED_COLUMN_NAME": "id"
        },
        {
            "CONSTRAINT_NAME": "fk_b_c",
            "TABLE_NAME": "table_b",
            "COLUMN_NAME": "c_id",
            "REFERENCED_TABLE_NAME": "table_c",
            "REFERENCED_COLUMN_NAME": "id"
        },
        {
            "CONSTRAINT_NAME": "fk_c_a",
            "TABLE_NAME": "table_c",
            "COLUMN_NAME": "a_id",
            "REFERENCED_TABLE_NAME": "table_a",
            "REFERENCED_COLUMN_NAME": "id"
        }
    ]
    builder.build(foreign_keys)
    return builder


@pytest.fixture
def long_chain_graph_builder() -> GraphBuilder:
    """Create a GraphBuilder with a long chain."""
    builder = GraphBuilder()
    # Create A -> B -> C -> D -> E -> F -> G chain
    foreign_keys = []
    for i in range(6):
        foreign_keys.append({
            "CONSTRAINT_NAME": f"fk_{i}",
            "TABLE_NAME": f"table_{chr(66 + i)}",  # B, C, D, E, F, G
            "COLUMN_NAME": f"parent_id",
            "REFERENCED_TABLE_NAME": f"table_{chr(65 + i)}",  # A, B, C, D, E, F
            "REFERENCED_COLUMN_NAME": "id"
        })
    builder.build(foreign_keys)
    return builder


# =============================================================================
# Finder Fixtures
# =============================================================================

@pytest.fixture
def mock_finder(sample_config: Config, mocker) -> FKPathFinder:
    """Create a FKPathFinder with mocked dependencies."""
    finder = FKPathFinder(sample_config)
    finder.connector = mocker.Mock()
    finder.graph_builder = mocker.Mock()
    finder.console = mocker.Mock()
    return finder


# =============================================================================
# CLI Fixtures
# =============================================================================

@pytest.fixture
def mock_click_context(mocker) -> Mock:
    """Create a mock Click context."""
    ctx = mocker.Mock()
    ctx.invoked_subcommand = None
    ctx.params = {}
    return ctx


@pytest.fixture
def mock_console(mocker) -> Mock:
    """Create a mock Rich console."""
    console = mocker.Mock()
    console.print = mocker.Mock()
    console.input = mocker.Mock(return_value="")
    
    # Create a proper context manager mock for status
    status_cm = mocker.MagicMock()
    status_cm.__enter__ = mocker.Mock(return_value=status_cm)
    status_cm.__exit__ = mocker.Mock(return_value=None)
    console.status = mocker.Mock(return_value=status_cm)
    return console


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def sample_database_list() -> List[str]:
    """Sample list of databases."""
    return ["sakila", "mydb", "testdb", "production"]


@pytest.fixture
def sample_fk_query_result() -> List[Dict[str, Any]]:
    """Sample result from foreign key query."""
    return [
        {
            "CONSTRAINT_NAME": "fk_test",
            "TABLE_NAME": "orders",
            "COLUMN_NAME": "customer_id",
            "REFERENCED_TABLE_NAME": "customers",
            "REFERENCED_COLUMN_NAME": "id"
        }
    ]


@pytest.fixture
def composite_fk_query_result() -> List[Dict[str, Any]]:
    """Sample result with composite foreign keys."""
    return [
        {
            "CONSTRAINT_NAME": "fk_composite",
            "TABLE_NAME": "order_items",
            "COLUMN_NAME": "order_id",
            "REFERENCED_TABLE_NAME": "orders",
            "REFERENCED_COLUMN_NAME": "id"
        },
        {
            "CONSTRAINT_NAME": "fk_composite",
            "TABLE_NAME": "order_items",
            "COLUMN_NAME": "product_id",
            "REFERENCED_TABLE_NAME": "products",
            "REFERENCED_COLUMN_NAME": "id"
        },
        {
            "CONSTRAINT_NAME": "fk_single",
            "TABLE_NAME": "orders",
            "COLUMN_NAME": "customer_id",
            "REFERENCED_TABLE_NAME": "customers",
            "REFERENCED_COLUMN_NAME": "id"
        }
    ]


# =============================================================================
# Edge Case Fixtures
# =============================================================================

@pytest.fixture
def empty_foreign_keys() -> List[ForeignKeyDict]:
    """Empty list of foreign keys."""
    return []


@pytest.fixture
def single_foreign_key() -> List[ForeignKeyDict]:
    """Single foreign key for testing."""
    return [
        {
            "CONSTRAINT_NAME": "fk_single",
            "TABLE_NAME": "orders",
            "COLUMN_NAME": "customer_id",
            "REFERENCED_TABLE_NAME": "customers",
            "REFERENCED_COLUMN_NAME": "id"
        }
    ]


@pytest.fixture
def self_referencing_fk() -> List[ForeignKeyDict]:
    """Self-referencing foreign key."""
    return [
        {
            "CONSTRAINT_NAME": "fk_self",
            "TABLE_NAME": "employees",
            "COLUMN_NAME": "manager_id",
            "REFERENCED_TABLE_NAME": "employees",
            "REFERENCED_COLUMN_NAME": "id"
        }
    ]
