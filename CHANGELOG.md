# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Future features and improvements

---

## [0.1.0] - 2024-02-14

### 🎉 Initial Release

First official release of FK Path Finder as a proper Python package.

### Added

#### Core Features
- 🔍 **Foreign Key Path Discovery**: Find all possible paths between tables/columns via foreign key relationships
- ↕️ **Bidirectional Traversal**: Search paths in both directions through FK relationships
- 🎯 **Table and Column Level Support**: Search between full tables or specific columns
- 🎨 **Rich Terminal Output**: Beautiful color-coded output with the Rich library
- 📝 **Plain Text Mode**: Option for plain text output without colors

#### Connection Modes
- 🖥️ **Interactive Mode**: Guided wizard for database connection and path queries
- ⚡ **Batch Mode**: Command-line arguments for automated/scripted usage
- 🔐 **Environment Variables**: Secure credential management via env vars
- 📁 **Configuration Files**: JSON config file support for reusable settings

#### Package & Distribution
- 📦 **Python Package Structure**: Proper package layout with `src/` directory
- 🚀 **CLI Entry Point**: `fk-finder` command after installation
- 📥 **PyPI Ready**: Configured for publication to Python Package Index
- 🔧 **Module Support**: Can be used as `python -m fk_path_finder`

#### API & Library Usage
- 🐍 **Public API**: Use as a Python library with `from fk_path_finder import FKPathFinder`
- 📘 **Type Hints**: Full type annotation support
- ⚙️ **Configuration Classes**: Typed configuration with validation
- 🔌 **Extensible Design**: Modular architecture for easy extension

#### Testing & Quality
- 🧪 **Test Suite**: Comprehensive tests with pytest
- 📊 **Coverage Reporting**: Code coverage with pytest-cov
- 🔍 **Type Checking**: mypy configuration for static analysis
- 🎨 **Code Formatting**: ruff for linting and formatting
- 📋 **Pre-commit Ready**: Configured for code quality tools

#### Documentation
- 📚 **README.md**: Comprehensive usage documentation
- 🔄 **MIGRATION.md**: Guide for migrating from old script version
- 📝 **CHANGELOG.md**: This file - version history
- 👥 **CONTRIBUTING.md**: Guidelines for contributors
- 💡 **USAGE_EXAMPLES.md**: Real-world usage scenarios
- 🐛 **Issue Templates**: Bug report and feature request templates
- 🔄 **PR Template**: Pull request template

#### Configuration Options
- Environment variables support (`FK_MYSQL_*`, `FK_MAX_*`)
- JSON configuration file support
- CLI argument overrides
- Sensible defaults for all options

### Technical Details

#### Dependencies
- `mysql-connector-python>=8.0.0` - MySQL database connectivity
- `rich>=13.0.0` - Terminal formatting and output
- `click>=8.0.0` - Command-line interface framework

#### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `pytest-mock>=3.10.0` - Mocking utilities
- `mypy>=1.0.0` - Static type checking
- `ruff>=0.1.0` - Linting and formatting

#### Package Structure
```
src/fk_path_finder/
├── __init__.py      # Package exports and version
├── __main__.py      # Module entry point
├── cli.py           # Click CLI implementation
├── database.py      # MySQL connection and schema extraction
├── graph.py         # Graph construction and path finding
├── finder.py        # Main orchestration class
└── types.py         # Type definitions and configuration
```

### Migration from Old Script

This release replaces the original single-file script (`mysql_fk_path_finder.py`) with a proper Python package. The old script is kept for backward compatibility but new development should use the package.

See [MIGRATION.md](./MIGRATION.md) for detailed migration instructions.

---

## Pre-0.1.0 (Legacy Script)

### Original Script Version
- Single file: `mysql_fk_path_finder.py`
- Only interactive mode supported
- No package structure
- No tests
- Dependencies: mysql-connector-python, rich

---

[Unreleased]: https://github.com/yourusername/fk-path-finder/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/fk-path-finder/releases/tag/v0.1.0
