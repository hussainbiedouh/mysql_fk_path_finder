"""Comprehensive tests for graph module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Set, Dict

from fk_path_finder.graph import GraphBuilder, format_path, format_path_plain
from fk_path_finder.types import ForeignKeyDict, PathResult


# =============================================================================
# Test GraphBuilder Initialization
# =============================================================================

class TestGraphBuilderInit:
    """Test cases for GraphBuilder initialization."""
    
    def test_init(self):
        """Test initialization."""
        builder = GraphBuilder()
        assert builder._graph is not None
        assert len(builder._graph) == 0
    
    def test_graph_property_empty(self):
        """Test graph property when empty."""
        builder = GraphBuilder()
        graph = builder.graph
        assert graph == {}
        assert isinstance(graph, dict)


# =============================================================================
# Test Graph Building
# =============================================================================

class TestGraphBuilderBuild:
    """Test cases for graph building."""
    
    def test_build_empty_list(self):
        """Test building graph with empty foreign key list."""
        builder = GraphBuilder()
        graph = builder.build([])
        
        assert len(graph) == 0
    
    def test_build_single_fk(self):
        """Test building graph with single foreign key."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "orders",
                "COLUMN_NAME": "customer_id",
                "REFERENCED_TABLE_NAME": "customers",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        
        graph = builder.build(foreign_keys)
        
        # Should have bidirectional edge
        assert "orders.customer_id" in graph
        assert "customers.id" in graph
        assert "customers.id" in graph["orders.customer_id"]
        assert "orders.customer_id" in graph["customers.id"]
    
    def test_build_bidirectional_edges(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test that graph creates bidirectional edges."""
        builder = GraphBuilder()
        graph = builder.build(sample_foreign_keys)
        
        # Check bidirectional edges for first FK
        assert "film_actor.film_id" in graph
        assert "film.film_id" in graph
        assert "film.film_id" in graph["film_actor.film_id"]
        assert "film_actor.film_id" in graph["film.film_id"]
    
    def test_build_intra_table_edges(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test that graph creates intra-table edges."""
        builder = GraphBuilder()
        graph = builder.build(sample_foreign_keys)
        
        # film_actor has two FK columns that should be connected
        assert "film_actor.film_id" in graph
        assert "film_actor.actor_id" in graph
        assert "film_actor.film_id" in graph["film_actor.actor_id"]
        assert "film_actor.actor_id" in graph["film_actor.film_id"]
    
    def test_build_multiple_tables(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test graph with multiple tables."""
        builder = GraphBuilder()
        graph = builder.build(sample_foreign_keys)
        
        # Should have nodes from all tables
        tables = set()
        for node in graph.keys():
            table = node.split(".")[0]
            tables.add(table)
        
        assert "film_actor" in tables
        assert "film" in tables
        assert "actor" in tables
        assert "film_category" in tables
        assert "category" in tables
        assert "language" in tables
    
    def test_build_self_referencing(self):
        """Test graph with self-referencing foreign key."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk_self",
                "TABLE_NAME": "employees",
                "COLUMN_NAME": "manager_id",
                "REFERENCED_TABLE_NAME": "employees",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        
        graph = builder.build(foreign_keys)
        
        # Should handle self-reference correctly
        assert "employees.manager_id" in graph
        assert "employees.id" in graph
        assert "employees.id" in graph["employees.manager_id"]
        assert "employees.manager_id" in graph["employees.id"]
    
    def test_build_rebuild(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test rebuilding graph with new data."""
        builder = GraphBuilder()
        
        # First build
        graph1 = builder.build(sample_foreign_keys)
        
        # Second build with different data
        new_keys = [
            {
                "CONSTRAINT_NAME": "fk_new",
                "TABLE_NAME": "new_table",
                "COLUMN_NAME": "ref_id",
                "REFERENCED_TABLE_NAME": "other_table",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        graph2 = builder.build(new_keys)
        
        # Graph should be replaced, not merged
        assert "new_table.ref_id" in graph2
        assert "film_actor.film_id" not in graph2


# =============================================================================
# Test Get Tables and Columns
# =============================================================================

class TestGraphBuilderGetTables:
    """Test cases for getting tables."""
    
    def test_get_tables_empty(self):
        """Test getting tables from empty graph."""
        builder = GraphBuilder()
        builder.build([])
        
        tables = builder.get_tables()
        
        assert len(tables) == 0
    
    def test_get_tables(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test getting all tables."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        tables = builder.get_tables()
        
        assert "film_actor" in tables
        assert "film" in tables
        assert "actor" in tables
        assert "film_category" in tables
        assert "category" in tables
        assert "language" in tables
    
    def test_get_tables_returns_set(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test that get_tables returns a set."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        tables = builder.get_tables()
        
        assert isinstance(tables, set)


class TestGraphBuilderGetColumns:
    """Test cases for getting columns."""
    
    def test_get_columns_for_table(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test getting columns for specific table."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        columns = builder.get_columns_for_table("film_actor")
        
        assert "film_actor.film_id" in columns
        assert "film_actor.actor_id" in columns
        assert len(columns) == 2
    
    def test_get_columns_for_table_case_insensitive(
        self, sample_foreign_keys: List[ForeignKeyDict]
    ):
        """Test case-insensitive table lookup."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        columns_lower = builder.get_columns_for_table("film_actor")
        columns_upper = builder.get_columns_for_table("FILM_ACTOR")
        columns_mixed = builder.get_columns_for_table("Film_Actor")
        
        assert columns_lower == columns_upper == columns_mixed
    
    def test_get_columns_for_table_empty(self):
        """Test getting columns for non-existent table."""
        builder = GraphBuilder()
        builder.build([])
        
        columns = builder.get_columns_for_table("nonexistent")
        
        assert len(columns) == 0
    
    def test_get_columns_for_table_not_in_graph(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test getting columns for table not in graph."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        columns = builder.get_columns_for_table("nonexistent")
        
        assert len(columns) == 0


# =============================================================================
# Test Parse Reference
# =============================================================================

class TestGraphBuilderParseReference:
    """Test cases for parse_reference method."""
    
    def test_parse_column_reference(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing table.column reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("film_actor.film_id")
        
        assert ref_type == "column"
        assert len(nodes) == 1
        assert nodes[0] == "film_actor.film_id"
    
    def test_parse_column_with_backticks(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing `table`.`column` reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("`film_actor`.`film_id`")
        
        assert ref_type == "column"
        assert len(nodes) == 1
        assert nodes[0] == "film_actor.film_id"
    
    def test_parse_column_partial_backticks(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing `table`.column reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("`film_actor`.film_id")
        
        assert ref_type == "column"
        assert len(nodes) == 1
    
    def test_parse_table_reference(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing just table name."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("film_actor")
        
        assert ref_type == "table"
        assert len(nodes) == 2  # film_actor has two FK columns
    
    def test_parse_table_with_backticks(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing `table` reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("`film_actor`")
        
        assert ref_type == "table"
        assert len(nodes) == 2
    
    def test_parse_unknown_reference(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing unknown reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("nonexistent")
        
        assert ref_type == "unknown"
        assert len(nodes) == 0
    
    def test_parse_unknown_column(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing unknown column reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("film_actor.nonexistent")
        
        assert ref_type == "unknown"
        assert len(nodes) == 0
    
    def test_parse_case_insensitive_column(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test case-insensitive column reference parsing."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type1, nodes1 = builder.parse_reference("FILM_ACTOR.film_id")
        ref_type2, nodes2 = builder.parse_reference("film_actor.FILM_ID")
        ref_type3, nodes3 = builder.parse_reference("Film_Actor.Film_Id")
        
        assert ref_type1 == ref_type2 == ref_type3 == "column"
        assert nodes1 == nodes2 == nodes3
    
    def test_parse_case_insensitive_table(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test case-insensitive table reference parsing."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type1, nodes1 = builder.parse_reference("FILM_ACTOR")
        ref_type2, nodes2 = builder.parse_reference("film_actor")
        
        assert ref_type1 == ref_type2 == "table"
        assert nodes1 == nodes2
    
    def test_parse_whitespace_stripping(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test that whitespace is stripped from reference."""
        builder = GraphBuilder()
        builder.build(sample_foreign_keys)
        
        ref_type, nodes = builder.parse_reference("  film_actor.film_id  ")
        
        assert ref_type == "column"
        assert len(nodes) == 1
    
    def test_parse_table_with_dots_in_name(self, sample_foreign_keys: List[ForeignKeyDict]):
        """Test parsing table name with dots (edge case with rsplit)."""
        # This is an edge case - table names with dots are unusual
        # but we should handle the last dot as separator
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk_test",
                "TABLE_NAME": "my.schema.table",
                "COLUMN_NAME": "col",
                "REFERENCED_TABLE_NAME": "other",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        # The rsplit should use the last dot
        ref_type, nodes = builder.parse_reference("my.schema.table.col")
        
        assert ref_type == "column"
        assert nodes[0] == "my.schema.table.col"


# =============================================================================
# Test Find All Paths
# =============================================================================

class TestGraphBuilderFindAllPaths:
    """Test cases for find_all_paths method."""
    
    def test_find_direct_path_same_node(self):
        """Test finding path from node to itself."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["table_a.id"],
            end_nodes=["table_a.id"],
            max_path_length=6,
            max_paths=100
        )
        
        assert result.total_found == 1
        assert result.paths[0] == ["table_a.id"]
    
    def test_find_direct_connection(self):
        """Test finding direct path between connected nodes."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["table_a.b_id"],
            end_nodes=["table_b.id"],
            max_path_length=6,
            max_paths=100
        )
        
        assert result.total_found == 1
        assert result.paths[0] == ["table_a.b_id", "table_b.id"]
    
    def test_find_path_through_chain(self):
        """Test finding path through chain of FKs."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "table_a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "table_c",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["table_a.id"],
            end_nodes=["table_c.b_id"],
            max_path_length=6,
            max_paths=100
        )
        
        assert result.total_found >= 1
        # Should find path: table_a.id -> table_b.a_id -> table_b.id -> table_c.b_id
        # (intra-table edge in table_b connects a_id and id)
    
    def test_no_path_found(self):
        """Test when no path exists."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "table_c",
                "COLUMN_NAME": "d_id",
                "REFERENCED_TABLE_NAME": "table_d",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["table_a.b_id"],
            end_nodes=["table_c.d_id"],
            max_path_length=6,
            max_paths=100
        )
        
        assert result.total_found == 0
        assert len(result.paths) == 0
    
    def test_respect_max_paths_limit(self):
        """Test that max_paths limit is respected."""
        # Create a graph with multiple paths
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk3",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["a.id"],
            end_nodes=["c.a_id", "c.b_id"],
            max_path_length=6,
            max_paths=1
        )
        
        assert result.total_found == 1
        assert result.limit_reached is True
    
    def test_respect_max_path_length(self):
        """Test that max_path_length limit is respected."""
        # Create a long chain: A -> B -> C -> D -> E
        builder = GraphBuilder()
        foreign_keys = []
        for i in range(4):
            foreign_keys.append({
                "CONSTRAINT_NAME": f"fk_{i}",
                "TABLE_NAME": f"table_{chr(66 + i)}",
                "COLUMN_NAME": "parent_id",
                "REFERENCED_TABLE_NAME": f"table_{chr(65 + i)}",
                "REFERENCED_COLUMN_NAME": "id"
            })
        builder.build(foreign_keys)
        
        # With max_path_length=3, can't reach from A to E
        result = builder.find_all_paths(
            start_nodes=["table_a.id"],
            end_nodes=["table_e.parent_id"],
            max_path_length=3,
            max_paths=100
        )
        
        # Path would be: table_a.id -> table_b.parent_id -> table_b.id -> ...
        # This is longer than 3 nodes, so no path found
        assert result.total_found == 0
    
    def test_avoid_duplicate_paths(self):
        """Test that duplicate paths are not returned."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        # Search same start and end nodes multiple times shouldn't duplicate
        result = builder.find_all_paths(
            start_nodes=["a.id", "a.id"],
            end_nodes=["c.b_id", "c.b_id"],
            max_path_length=6,
            max_paths=100
        )
        
        # Should not have duplicate paths
        unique_paths = set(tuple(p) for p in result.paths)
        assert len(unique_paths) == len(result.paths)
    
    def test_multiple_start_nodes(self):
        """Test with multiple start nodes."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        result = builder.find_all_paths(
            start_nodes=["a.id"],
            end_nodes=["b.a_id", "c.a_id"],
            max_path_length=6,
            max_paths=100
        )
        
        assert result.total_found >= 2
    
    def test_circular_reference_avoid_infinite_loop(self, circular_graph_builder: GraphBuilder):
        """Test that circular references don't cause infinite loops."""
        result = circular_graph_builder.find_all_paths(
            start_nodes=["table_a.id"],
            end_nodes=["table_c.id"],
            max_path_length=6,
            max_paths=100
        )
        
        # Should find paths without infinite looping
        assert result.total_found >= 1
    
    def test_find_all_paths_with_console(self):
        """Test find_all_paths with console for progress display."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        # Create mock console with proper Progress support
        from unittest.mock import MagicMock
        mock_console = MagicMock()
        
        result = builder.find_all_paths(
            start_nodes=["table_a.b_id"],
            end_nodes=["table_b.id"],
            max_path_length=6,
            max_paths=100,
            console=mock_console
        )
        
        assert result.total_found == 1


# =============================================================================
# Test Find Paths Simple
# =============================================================================

class TestGraphBuilderFindPathsSimple:
    """Test cases for find_paths_simple method."""
    
    def test_find_paths_simple_same_node(self):
        """Test finding path from node to itself."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        paths = builder.find_paths_simple("table_a.b_id", "table_a.b_id")
        
        assert len(paths) == 1
        assert paths[0] == ["table_a.b_id"]
    
    def test_find_paths_simple_direct(self):
        """Test finding direct path."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        paths = builder.find_paths_simple("table_a.b_id", "table_b.id")
        
        assert len(paths) == 1
        assert paths[0] == ["table_a.b_id", "table_b.id"]
    
    def test_find_paths_simple_not_in_graph(self):
        """Test finding path when node not in graph."""
        builder = GraphBuilder()
        builder.build([])
        
        paths = builder.find_paths_simple("table_a.id", "table_b.id")
        
        assert len(paths) == 0
    
    def test_find_paths_simple_multiple(self):
        """Test finding multiple paths."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "b",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk3",
                "TABLE_NAME": "c",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "a",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        # c can reach a directly and through b
        paths = builder.find_paths_simple("c.a_id", "a.id")
        
        assert len(paths) >= 1
    
    def test_find_paths_simple_avoids_cycles(self):
        """Test that simple path finding avoids cycles."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk1",
                "TABLE_NAME": "table_b",
                "COLUMN_NAME": "a_id",
                "REFERENCED_TABLE_NAME": "table_a",
                "REFERENCED_COLUMN_NAME": "id"
            },
            {
                "CONSTRAINT_NAME": "fk2",
                "TABLE_NAME": "table_a",
                "COLUMN_NAME": "b_id",
                "REFERENCED_TABLE_NAME": "table_b",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        builder.build(foreign_keys)
        
        # This creates a cycle: a <-> b
        paths = builder.find_paths_simple("table_a.id", "table_b.id")
        
        # Should find paths without infinite looping
        assert len(paths) >= 1


# =============================================================================
# Test Path Formatting
# =============================================================================

class TestPathFormatting:
    """Test cases for path formatting functions."""
    
    def test_format_path_single_node(self):
        """Test formatting path with single node."""
        path = ["film.film_id"]
        formatted = format_path(path)
        
        assert "film" in formatted
        assert "film_id" in formatted
        assert "[bold green]" in formatted
        assert "[cyan]" in formatted
    
    def test_format_path_multiple_nodes(self):
        """Test formatting path with multiple nodes."""
        path = ["film.film_id", "film_actor.film_id", "film_actor.actor_id"]
        formatted = format_path(path)
        
        assert "film" in formatted
        assert "film_actor" in formatted
        assert "→" in formatted  # Arrow character
        assert "[bold yellow]→[/bold yellow]" in formatted
    
    def test_format_path_with_dots_in_column(self):
        """Test formatting path with dots in column name (edge case)."""
        path = ["table.col.with.dots"]
        formatted = format_path(path)
        
        # Should split only on first dot
        assert "table" in formatted
    
    def test_format_path_plain_single(self):
        """Test plain formatting with single node."""
        path = ["film.film_id"]
        formatted = format_path_plain(path)
        
        assert "film" in formatted
        assert "film_id" in formatted
        assert "->" in formatted or "→" not in formatted
        assert "[bold" not in formatted  # No Rich markup
    
    def test_format_path_plain_multiple(self):
        """Test plain formatting with multiple nodes."""
        path = ["a.id", "b.a_id", "b.id", "c.b_id"]
        formatted = format_path_plain(path)
        
        assert "a" in formatted
        assert "b" in formatted
        assert "c" in formatted
        assert " -> " in formatted  # Plain arrow with spaces
        assert "[bold" not in formatted
        assert "[green" not in formatted
    
    def test_format_path_plain_with_backticks(self):
        """Test plain formatting includes backticks."""
        path = ["film.film_id"]
        formatted = format_path_plain(path)
        
        assert "`film`" in formatted
        assert "`film_id`" in formatted
    
    def test_format_path_empty(self):
        """Test formatting empty path."""
        path = []
        formatted = format_path(path)
        
        assert formatted == ""
    
    def test_format_path_plain_empty(self):
        """Test plain formatting empty path."""
        path = []
        formatted = format_path_plain(path)
        
        assert formatted == ""


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestGraphEdgeCases:
    """Test edge cases for graph operations."""
    
    def test_empty_graph_operations(self):
        """Test operations on empty graph."""
        builder = GraphBuilder()
        builder.build([])
        
        # These should not raise errors
        assert builder.get_tables() == set()
        assert builder.get_columns_for_table("any") == []
        ref_type, nodes = builder.parse_reference("test.table")
        assert ref_type == "unknown"
        assert nodes == []
    
    def test_very_long_column_names(self):
        """Test with very long column names."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk_test",
                "TABLE_NAME": "a" * 50,
                "COLUMN_NAME": "b" * 50,
                "REFERENCED_TABLE_NAME": "c" * 50,
                "REFERENCED_COLUMN_NAME": "d" * 50
            }
        ]
        graph = builder.build(foreign_keys)
        
        long_node = f"{'a' * 50}.{'b' * 50}"
        assert long_node in graph
    
    def test_special_characters_in_names(self):
        """Test with special characters in table/column names."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk_test",
                "TABLE_NAME": "table-name",
                "COLUMN_NAME": "column_name",
                "REFERENCED_TABLE_NAME": "other_table",
                "REFERENCED_COLUMN_NAME": "id"
            }
        ]
        graph = builder.build(foreign_keys)
        
        assert "table-name.column_name" in graph
    
    def test_unicode_in_names(self):
        """Test with unicode characters in names."""
        builder = GraphBuilder()
        foreign_keys = [
            {
                "CONSTRAINT_NAME": "fk_test",
                "TABLE_NAME": "表名",
                "COLUMN_NAME": "列名",
                "REFERENCED_TABLE_NAME": "其他表",
                "REFERENCED_COLUMN_NAME": "编号"
            }
        ]
        graph = builder.build(foreign_keys)
        
        assert "表名.列名" in graph
        assert "其他表.编号" in graph
