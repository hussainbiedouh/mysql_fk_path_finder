"""Type definitions for FK Path Finder."""

from typing import Dict, List, Set, Tuple, Optional, Any, TypedDict
from dataclasses import dataclass


class ForeignKeyDict(TypedDict):
    """Dictionary representation of a foreign key."""
    CONSTRAINT_NAME: str
    TABLE_NAME: str
    COLUMN_NAME: str
    REFERENCED_TABLE_NAME: str
    REFERENCED_COLUMN_NAME: str


class ConnectionParams(TypedDict, total=False):
    """MySQL connection parameters."""
    host: str
    port: int
    user: str
    password: str
    database: Optional[str]


@dataclass
class PathResult:
    """Result of a path finding operation."""
    paths: List[List[str]]
    total_found: int
    limit_reached: bool
    start_nodes: List[str]
    end_nodes: List[str]
    
    def __post_init__(self) -> None:
        """Sort paths by length after initialization."""
        self.paths.sort(key=len)


@dataclass
class Config:
    """Application configuration."""
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: Optional[str] = None
    max_path_length: int = 6
    max_paths: int = 1000
    display_limit: int = 20
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        return cls(
            host=data.get("host", "localhost"),
            port=data.get("port", 3306),
            user=data.get("user", ""),
            password=data.get("password", ""),
            database=data.get("database"),
            max_path_length=data.get("max_path_length", 6),
            max_paths=data.get("max_paths", 1000),
            display_limit=data.get("display_limit", 20),
        )
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create Config from environment variables."""
        import os
        
        return cls(
            host=os.getenv("FK_MYSQL_HOST", "localhost"),
            port=int(os.getenv("FK_MYSQL_PORT", "3306")),
            user=os.getenv("FK_MYSQL_USER", ""),
            password=os.getenv("FK_MYSQL_PASSWORD", ""),
            database=os.getenv("FK_MYSQL_DATABASE") or None,
            max_path_length=int(os.getenv("FK_MAX_PATH_LENGTH", "6")),
            max_paths=int(os.getenv("FK_MAX_PATHS", "1000")),
            display_limit=int(os.getenv("FK_DISPLAY_LIMIT", "20")),
        )
    
    def to_connection_params(self) -> Dict[str, Any]:
        """Convert to MySQL connection parameters."""
        params: Dict[str, Any] = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
        }
        if self.database:
            params["database"] = self.database
        return params


# Type aliases
Graph = Dict[str, Set[str]]
ReferenceType = Tuple[str, List[str]]  # ('column'|'table', [nodes])
