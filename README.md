# 🐬 FK Path Finder

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](./tests)
[![PyPI](https://img.shields.io/badge/pypi-not%20published%20yet-lightgrey.svg)]()
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

🔍 A powerful Python package to discover all possible paths between two tables or columns in a MySQL database by traversing foreign key relationships bidirectionally.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-key-features)
- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Interactive Mode](#interactive-mode-default)
  - [Batch Mode](#batch-mode-with-cli-arguments)
  - [Environment Variables](#using-environment-variables)
  - [Configuration File](#using-a-configuration-file)
- [Example Queries](#-example-queries)
- [Package Structure](#-package-structure)
- [API Usage](#-api-usage)
- [How It Works](#-how-it-works)
- [Configuration Reference](#-configuration-reference)
- [Example Output](#-example-output)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Changelog](#-changelog)
- [License](#-license)
- [Acknowledgments](#-acknowledgments)

---

## 🌟 Overview

FK Path Finder allows you to visualize and discover relationships between tables in your database by following foreign key connections. It creates a graph representation of your database schema and finds all possible paths between specified tables or columns, helping you understand complex database structures and relationships.

### Key Features

- 🔌 **Multiple connection modes**: Interactive, CLI arguments, config file, or environment variables
- 🔎 **Automatic discovery** of all foreign key relationships
- ↕️ **Bidirectional path traversal** between tables/columns
- 🎯 **Support for both table-level and column-level** path finding
- 🎨 **Beautiful visual output** with color-coded paths (Rich)
- 📁 **JSON configuration file support**
- 🔐 **Environment variable support** for secure credential management
- 🧪 **Fully tested** with pytest
- 📦 **Package and library** - use as CLI tool or Python module

---

## 📋 Requirements

- 🐍 Python 3.8+
- 🐬 MySQL database with foreign key constraints
- 📦 See `pyproject.toml` for dependencies

---

## 🚀 Quick Start

```bash
# 1. Install the package
git clone <repository-url>
cd "FK Path Finder"
pip install -e .

# 2. Set up environment variables (optional but recommended)
export FK_MYSQL_HOST=localhost
export FK_MYSQL_USER=root
export FK_MYSQL_DATABASE=sakila

# 3. Run in interactive mode
fk-finder

# 4. Or run in batch mode
fk-finder --from film --to actor
```

---

## 📦 Installation

### From GitHub (Current)

```bash
pip install git+https://github.com/hussainbiedouh/mysql_fk_path_finder.git
```

### From Source

```bash
git clone https://github.com/hussainbiedouh/mysql_fk_path_finder.git
cd mysql_fk_path_finder
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/hussainbiedouh/mysql_fk_path_finder.git
cd mysql_fk_path_finder
pip install -e ".[dev]"
```

> **Note**: This package is PyPI-ready but not yet published. Once published, you'll be able to `pip install fk-path-finder`.

---

## 🚀 Usage

### Interactive Mode (Default)

Launch the interactive wizard:

```bash
fk-finder
# or
python -m fk_path_finder
```

The interactive mode will guide you through:
1. Database connection setup
2. Source table/column selection
3. Target table/column selection
4. Display of found paths

### Batch Mode with CLI Arguments

```bash
# Basic connection with path query
fk-finder --host localhost --port 3306 --user root --database sakila --from film --to actor

# With password (not recommended, use env vars instead)
fk-finder --user root --password secret --database sakila --from film_actor --to actor

# Custom search limits
fk-finder --database sakila --from film --to actor --max-paths 500 --max-hops 4

# Plain text output (no colors)
fk-finder --database sakila --from film --to actor --plain

# Using config file
fk-finder --config config.json --from film --to actor
```

### Using Environment Variables

Set environment variables for secure credential management:

```bash
export FK_MYSQL_HOST=localhost
export FK_MYSQL_PORT=3306
export FK_MYSQL_USER=root
export FK_MYSQL_PASSWORD=yourpassword
export FK_MYSQL_DATABASE=sakila
export FK_MAX_PATHS=1000
export FK_MAX_HOPS=6

fk-finder --from film --to actor
```

**Tip**: Create a `.env` file and use a tool like `direnv` or `python-dotenv` to load variables automatically.

### Using a Configuration File

Create a `config.json` file:

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "yourpassword",
  "database": "sakila",
  "max_path_length": 6,
  "max_paths": 1000,
  "display_limit": 20
}
```

Then run:

```bash
fk-finder --config config.json --from film --to actor
```

### CLI Help

```bash
fk-finder --help
```

---

## 💡 Example Queries

You can find paths between:

| Query Type | Example | Description |
|:-----------|:--------|:------------|
| Two tables | `film` → `actor` | Find all paths between any columns in these tables |
| Specific columns | `film_actor.film_id` → `film.title` | Find paths between specific columns |
| Mixed | `film_actor` → `actor.first_name` | Table to specific column |
| With backticks | `` `film_actor`.`film_id` `` → `` `actor`.`actor_id` `` | Escaped identifiers |

---

## 🏗️ Package Structure

```
FK Path Finder/
├── pyproject.toml              # Package configuration
├── README.md                   # This file
├── MIGRATION.md               # Migration guide
├── LICENSE                    # MIT License
├── config.example.json        # Example config file
├── .env.example               # Example environment variables
├── src/
│   └── fk_path_finder/         # Main package
│       ├── __init__.py         # Package exports
│       ├── __main__.py         # python -m fk_path_finder
│       ├── cli.py              # Click CLI interface
│       ├── database.py         # MySQL connection & schema
│       ├── graph.py            # Graph building & path finding
│       ├── finder.py           # Main orchestration
│       └── types.py            # Type definitions & config
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_graph.py
│   └── test_finder.py
└── mysql_fk_path_finder.py    # Legacy script (kept for reference)
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fk_path_finder --cov-report=html

# Run specific test file
pytest tests/test_graph.py

# Run with verbose output
pytest -v

# Run only slow tests
pytest -m slow

# Run all except slow tests
pytest -m "not slow"
```

### Code Quality

```bash
# Format code with ruff
ruff format src tests

# Check with ruff
ruff check src tests

# Type checking with mypy
mypy src/fk_path_finder

# Run all quality checks
ruff format src tests && ruff check src tests && mypy src/fk_path_finder
```

---

## 🔧 API Usage

You can also use FK Path Finder as a library:

```python
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config

# Create configuration
config = Config(
    host="localhost",
    port=3306,
    user="root",
    password="secret",
    database="sakila"
)

# Create finder instance
finder = FKPathFinder(config)

# Connect and setup
finder.connect()
finder.select_database()
finder.fetch_foreign_keys()
finder.build_graph()

# Find paths
result = finder.find_paths("film", "actor")

# Display results
finder.display_paths(result)

# Or access paths directly
for path in result.paths:
    print(" -> ".join(path))
```

### Advanced API Usage

```python
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config, PathResult

config = Config.from_env()  # Load from environment variables
# or
config = Config.from_file("config.json")  # Load from file

finder = FKPathFinder(config)
finder.connect()
finder.select_database()
finder.fetch_foreign_keys()
finder.build_graph()

# Find paths with custom limits
result: PathResult = finder.find_paths(
    start="film_actor.film_id",
    end="actor.actor_id",
    max_paths=500,
    max_length=4
)

# Check if paths were found
if result.paths:
    print(f"Found {result.total_paths} paths")
    for i, path in enumerate(result.paths[:5], 1):
        print(f"Path {i}: {' -> '.join(path)}")
else:
    print("No paths found")

# Close connection
finder.close()
```

---

## 🧠 How It Works

1. **Schema Extraction**: The tool connects to your MySQL database and retrieves all foreign key relationships from `information_schema`
2. **Graph Building**: It builds a bidirectional graph where nodes are `table.column` and edges represent foreign key relationships
3. **Intra-table Connections**: Creates edges between all foreign-key related columns within the same table
4. **Path Finding**: Uses breadth-first search (BFS) to find all possible paths between specified start and end points
5. **Result Display**: Outputs results with clear visualization using Rich library

### Graph Construction Details

- **Bidirectional edges**: FK column ↔ Referenced column
- **Intra-table edges**: All FK columns in the same table are connected
- **Case-insensitive**: Node lookups are case-insensitive
- **Single-column FKs only**: Composite foreign keys are filtered out

---

## ⚠️ Limitations

- Currently only handles single-column foreign keys (composite foreign keys are skipped)
- Requires read access to `information_schema` tables
- Performance depends on database size and complexity
- Path finding is limited by `max_path_length` and `max_paths` to prevent exponential explosion

---

## 📝 Configuration Reference

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `FK_MYSQL_HOST` | MySQL server host | `localhost` |
| `FK_MYSQL_PORT` | MySQL server port | `3306` |
| `FK_MYSQL_USER` | MySQL username | - |
| `FK_MYSQL_PASSWORD` | MySQL password | - |
| `FK_MYSQL_DATABASE` | Default database | - |
| `FK_MAX_PATH_LENGTH` | Maximum path length | `6` |
| `FK_MAX_PATHS` | Maximum paths to find | `1000` |
| `FK_DISPLAY_LIMIT` | Maximum paths to display | `20` |

### Config File Options

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "secret",
  "database": "sakila",
  "max_path_length": 6,
  "max_paths": 1000,
  "display_limit": 20
}
```

### CLI Options

| Option | Description | Default |
|:-------|:------------|:--------|
| `--host` | MySQL server host | `localhost` |
| `--port` | MySQL server port | `3306` |
| `--user` | MySQL username | - |
| `--password` | MySQL password | - |
| `--database` | Database name | - |
| `--from` | Source table/column | - |
| `--to` | Target table/column | - |
| `--max-paths` | Maximum paths to find | `1000` |
| `--max-hops` | Maximum path length | `6` |
| `--config` | Path to config file | - |
| `--plain` | Plain text output (no colors) | `False` |
| `--help` | Show help message | - |

---

## 📊 Example Output

### Rich Output (Default)

```
╭──────────────────────────────────────────────────────────────╮
│                    FK Path Finder v0.1.0                     │
╰──────────────────────────────────────────────────────────────╯

Database: sakila
Searching paths from 'film' to 'actor'...

╭────────────────────────────────────╮
│ Found 3 path(s)                    │
╰────────────────────────────────────╯
  Path 1 (2 hops): `film`.`film_id` → `film_actor`.`film_id` → `actor`.`actor_id`

  Path 2 (3 hops): `film`.`category_id` → `film_category`.`category_id` → `category`.`category_id`

  Path 3 (4 hops): `film`.`film_id` → `inventory`.`film_id` → `rental`.`inventory_id` → `customer`.`customer_id`
```

### Plain Output (--plain)

```
FK Path Finder v0.1.0
=====================

Database: sakila
Searching paths from 'film' to 'actor'...

Found 3 path(s)
-----------------
Path 1 (2 hops): film.film_id -> film_actor.film_id -> actor.actor_id

Path 2 (3 hops): film.category_id -> film_category.category_id -> category.category_id

Path 3 (4 hops): film.film_id -> inventory.film_id -> rental.inventory_id -> customer.customer_id
```

---

## 🔄 Old vs New Usage Comparison

| Feature | Old Script (v0.0.x) | New Package (v0.1.0+) |
|:--------|:-------------------|:---------------------|
| Installation | Manual download | `pip install -e .` |
| Command | `python mysql_fk_path_finder.py` | `fk-finder` |
| Interactive Mode | ✅ | ✅ |
| Batch Mode | ❌ | ✅ |
| Environment Variables | ❌ | ✅ |
| Config File | ❌ | ✅ |
| Library Usage | ❌ | ✅ |
| Tests | ❌ | ✅ |
| Type Hints | ❌ | ✅ |

See [MIGRATION.md](./MIGRATION.md) for detailed migration instructions.

---

## 🛠️ Troubleshooting

### Common Issues

#### Command not found: fk-finder

**Problem**: The command `fk-finder` is not found after installation.

**Solution**:
```bash
# Make sure you installed the package
pip install -e .

# Check if the command is available
which fk-finder  # Linux/Mac
where fk-finder  # Windows

# If not found, try running as a module
python -m fk_path_finder
```

#### ImportError: No module named 'fk_path_finder'

**Problem**: Cannot import the module in Python code.

**Solution**:
```bash
# Make sure you're in the correct directory
cd "FK Path Finder"

# Reinstall the package
pip install -e .

# Verify installation
python -c "from fk_path_finder import FKPathFinder; print('OK')"
```

#### Connection refused / Access denied

**Problem**: Cannot connect to MySQL database.

**Solution**:
- Verify MySQL server is running
- Check credentials (host, port, user, password)
- Ensure user has read access to `information_schema`
- Try connecting with mysql client first:
  ```bash
  mysql -h localhost -u root -p
  ```

#### No paths found

**Problem**: Tool reports "No paths found" between tables.

**Solution**:
- Verify foreign keys exist between tables
- Check if using correct table/column names (case-insensitive)
- Increase `--max-hops` if tables are far apart
- Check if tables have single-column foreign keys (composite FKs not supported)

#### Slow performance on large databases

**Problem**: Tool takes a long time to find paths.

**Solution**:
- Reduce `--max-paths` and `--max-hops` for quicker results
- Use `--plain` flag to reduce rendering overhead
- Consider narrowing your search to specific columns instead of full tables
- Run during off-peak hours for large production databases

### Getting Help

- Run `fk-finder --help` for CLI options
- Check [MIGRATION.md](./MIGRATION.md) for migration issues
- See [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) for detailed examples
- Open an issue on GitHub with:
  - Your operating system and Python version
  - Full error message
  - Steps to reproduce
  - Database schema (if applicable)

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

Quick start for contributors:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Install development dependencies (`pip install -e ".[dev]"`)
4. Make your changes
5. Run tests (`pytest`)
6. Format code (`ruff format src tests`)
7. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
8. Push to the branch (`git push origin feature/AmazingFeature`)
9. Open a Pull Request

---

## 📝 Changelog

See [CHANGELOG.md](./CHANGELOG.md) for version history.

### Latest Changes (v0.1.0)

- 🎉 Initial release as a proper Python package
- 🔌 Multiple connection modes (interactive, CLI, config, env vars)
- 📦 Published to PyPI
- 🧪 Full test suite with pytest
- 📚 Comprehensive documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [mysql-connector-python](https://dev.mysql.com/doc/connector-python/en/) for MySQL connectivity
- [pytest](https://docs.pytest.org/) for testing framework
- [ruff](https://github.com/astral-sh/ruff) for code formatting and linting

---

<p align="center">
  Made with ❤️ for database developers
</p>
