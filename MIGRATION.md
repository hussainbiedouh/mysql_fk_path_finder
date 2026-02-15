# Migration Guide: FK Path Finder

> **Version**: 0.1.0  
> **Last Updated**: 2024-02-14

## 📋 Table of Contents

- [Overview](#overview)
- [What's Changed](#whats-changed)
- [Installation Changes](#installation-changes)
- [Usage Comparison](#usage-comparison)
  - [Before and After Examples](#before-and-after-examples)
- [Breaking Changes](#breaking-changes)
- [New Features](#new-features)
- [Migration Checklist](#migration-checklist)
- [File Structure Changes](#file-structure-changes)
- [API Usage Migration](#api-usage-migration)
- [Troubleshooting](#troubleshooting)
- [Backward Compatibility](#backward-compatibility)
- [Getting Help](#getting-help)

---

## Overview

The FK Path Finder has been refactored from a single script to a proper Python package. This guide helps you migrate from the old version (single script) to the new package version (0.1.0+).

### Why Migrate?

| Aspect | Old Script | New Package |
|:-------|:-----------|:------------|
| **Installation** | Manual download and run | `pip install -e .` |
| **Usage** | Interactive only | Interactive + Batch + API |
| **Configuration** | Hard-coded prompts | Config files, env vars, CLI args |
| **Testing** | None | Comprehensive test suite |
| **Maintainability** | Single large file | Modular, organized code |
| **Reusability** | Standalone script | Importable library |
| **Distribution** | Manual sharing | PyPI-ready package |

---

## What's Changed

### Before (Old Version: v0.0.x)

- **Single file**: `mysql_fk_path_finder.py`
- **Execution**: `python mysql_fk_path_finder.py`
- **Modes**: Interactive only
- **Dependencies**: `mysql-connector-python`, `rich`
- **Configuration**: Hard-coded interactive prompts
- **Testing**: No tests
- **Importing**: Not possible (not a package)

### After (New Package: v0.1.0+)

- **Package structure**: `src/fk_path_finder/` with modular files
- **Execution**: `fk-finder` or `python -m fk_path_finder`
- **Modes**: Interactive, batch, library/API
- **Dependencies**: `mysql-connector-python`, `rich`, `click`
- **Configuration**: Config files, environment variables, CLI arguments
- **Testing**: Full pytest test suite with coverage
- **Importing**: `from fk_path_finder import FKPathFinder`

---

## Installation Changes

### Old Installation

```bash
# Download the file somehow (email, USB, shared drive)
# Place it in your working directory
# No installation needed, just run
```

### New Installation

```bash
# Clone or download the repository
git clone <repository-url>
cd "FK Path Finder"

# Install the package
pip install -e .

# Verify installation
fk-finder --help
```

### Development Installation (Optional)

```bash
# For contributing or development
pip install -e ".[dev]"

# This installs additional tools:
# - pytest for testing
# - mypy for type checking
# - ruff for linting/formatting
```

---

## Usage Comparison

### Before: Single Script Execution

```bash
# The only way to run
python mysql_fk_path_finder.py

# Then answer interactive prompts:
# - Enter MySQL host: localhost
# - Enter MySQL port: 3306
# - Enter MySQL user: root
# - Enter MySQL password: *****
# - Enter database name: sakila
# - Enter FROM table: film
# - Enter TO table: actor
```

### After: Multiple Usage Modes

#### Option 1: Interactive Mode (Same Experience)

```bash
# Same interactive experience as before
fk-finder

# Or using module syntax
python -m fk_path_finder
```

#### Option 2: Batch Mode (New!)

```bash
# All parameters in one command
fk-finder --host localhost --port 3306 --user root --database sakila --from film --to actor

# With custom limits
fk-finder --database sakila --from film --to actor --max-paths 500 --max-hops 4

# Plain text output (no colors, good for logs)
fk-finder --database sakila --from film --to actor --plain
```

#### Option 3: Environment Variables (New!)

```bash
# Set once in your shell profile
export FK_MYSQL_HOST=localhost
export FK_MYSQL_PORT=3306
export FK_MYSQL_USER=root
export FK_MYSQL_PASSWORD=yourpassword
export FK_MYSQL_DATABASE=sakila

# Then run without credentials
fk-finder --from film --to actor
```

#### Option 4: Configuration File (New!)

```bash
# Create config.json once
cat > config.json << 'EOF'
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
EOF

# Use for all queries
fk-finder --config config.json --from film --to actor
```

---

## Before and After Examples

### Example 1: Simple Query

#### Before (Old Way)
```bash
$ python mysql_fk_path_finder.py
Enter MySQL host [localhost]: localhost
Enter MySQL port [3306]: 3306
Enter MySQL user: root
Enter MySQL password: ********
Enter database name: sakila
Enter FROM table or column: film
Enter TO table or column: actor
# ... results displayed ...
# Press Ctrl+C to exit or Enter to continue
```

#### After (New Way)
```bash
# Batch mode - single command
$ fk-finder --database sakila --from film --to actor

# Or with config file
$ fk-finder --config config.json --from film --to actor

# Or with env vars (already set)
$ fk-finder --from film --to actor
```

### Example 2: Multiple Queries

#### Before (Old Way)
```bash
# Had to restart the script for each query
$ python mysql_fk_path_finder.py
# ... answer all prompts for first query ...
# ... press Ctrl+C to exit ...

$ python mysql_fk_path_finder.py
# ... answer all prompts for second query ...
```

#### After (New Way)
```bash
# With env vars set
$ fk-finder --from film --to actor
$ fk-finder --from customer --to film
$ fk-finder --from rental --to payment

# Or use a script
for pair in "film:actor" "customer:film" "rental:payment"; do
  IFS=':' read -r from to <<< "$pair"
  fk-finder --from "$from" --to "$to"
done
```

### Example 3: Integration in Scripts

#### Before (Old Way)
```bash
#!/bin/bash
# NOT POSSIBLE - script is interactive only
echo "Cannot automate the old version"
```

#### After (New Way)
```bash
#!/bin/bash
# check_paths.sh - Automated schema validation

DATABASE="production"
CRITICAL_PATHS=("users:orders" "orders:payments" "users:profiles")

for path in "${CRITICAL_PATHS[@]}"; do
  IFS=':' read -r from to <<< "$path"
  echo "Checking: $from -> $to"
  
  result=$(fk-finder --database "$DATABASE" --from "$from" --to "$to" --plain)
  
  if echo "$result" | grep -q "Found 0 path"; then
    echo "ERROR: No path found!"
    exit 1
  fi
done

echo "All critical paths verified!"
```

### Example 4: Python API Usage

#### Before (Old Way)
```python
# NOT POSSIBLE - not importable
# You would have to copy-paste the code
```

#### After (New Way)
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

# Or process results programmatically
for path in result.paths:
    print(" -> ".join(path))

# Clean up
finder.close()
```

---

## Breaking Changes

### 1. Command Changed

| Before | After |
|:-------|:------|
| `python mysql_fk_path_finder.py` | `fk-finder` or `python -m fk_path_finder` |

**Migration**:
```bash
# Update your aliases
alias fk='fk-finder'

# Update your scripts
# OLD: python /path/to/mysql_fk_path_finder.py
# NEW: fk-finder
```

### 2. New Required Dependencies

- `click>=8.0.0` is now required for CLI functionality

**Migration**:
```bash
# Install will handle this automatically
pip install -e .
```

### 3. Import Path Changed

| Before | After |
|:-------|:------|
| Not importable | `from fk_path_finder import FKPathFinder` |

**Migration**: If you were copy-pasting code, switch to proper imports.

### 4. Interactive Flow Slightly Changed

The new interactive mode may have slightly different prompts or output formatting.

**Migration**: No action needed, just be aware of the new look.

---

## New Features

### 1. Batch Mode

Find paths without interactive prompts:

```bash
fk-finder --database sakila --from film --to actor
```

**Benefits**:
- Automatable
- Scriptable
- Faster for repeated queries
- Integrates with CI/CD pipelines

### 2. Plain Text Output

```bash
fk-finder --database sakila --from film --to actor --plain
```

**Benefits**:
- No ANSI color codes
- Perfect for log files
- Easier to parse programmatically

### 3. Custom Limits

```bash
fk-finder --max-paths 500 --max-hops 4 --from film --to actor
```

**Benefits**:
- Control search scope
- Improve performance on large databases
- Prevent runaway queries

### 4. Configuration File

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "secret",
  "database": "sakila"
}
```

```bash
fk-finder --config config.json --from film --to actor
```

**Benefits**:
- Reusable settings
- No credential exposure in shell history
- Share configurations with team

### 5. Environment Variables

```bash
export FK_MYSQL_HOST=localhost
export FK_MYSQL_USER=root
export FK_MYSQL_DATABASE=sakila
fk-finder --from film --to actor
```

**Benefits**:
- Secure credential management
- 12-factor app compliance
- Easy Docker/Kubernetes integration

### 6. Python API

```python
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config

config = Config.from_env()
finder = FKPathFinder(config)
# ... use programmatically
```

**Benefits**:
- Build custom tools
- Integrate with data pipelines
- Automated testing

### 7. Full Test Suite

```bash
pytest
pytest --cov=fk_path_finder
```

**Benefits**:
- Confidence in changes
- CI/CD integration
- Regression prevention

---

## Migration Checklist

Use this checklist to ensure a complete migration:

### Installation
- [ ] Backup any custom modifications to `mysql_fk_path_finder.py`
- [ ] Clone/download the new repository
- [ ] Run `pip install -e .` in the project directory
- [ ] Verify with `fk-finder --help`

### Configuration
- [ ] Choose your preferred configuration method:
  - [ ] Environment variables (recommended for production)
  - [ ] Config file (recommended for development)
  - [ ] CLI arguments (good for scripts)
- [ ] Create `.env` file or `config.json` with your settings
- [ ] Test connection with new configuration

### Testing
- [ ] Test interactive mode: `fk-finder`
- [ ] Test batch mode: `fk-finder --from table1 --to table2`
- [ ] Test with environment variables
- [ ] Test with config file
- [ ] Run existing queries to verify same results

### Scripts & Automation
- [ ] Identify all scripts using the old command
- [ ] Update scripts to use `fk-finder`
- [ ] Consider switching to batch mode for automation
- [ ] Test updated scripts

### Documentation
- [ ] Update internal documentation
- [ ] Share new usage patterns with team
- [ ] Update any wiki pages or runbooks

### Cleanup (Optional)
- [ ] Remove old `mysql_fk_path_finder.py` when ready
- [ ] Update `.gitignore` if needed
- [ ] Archive old documentation

---

## File Structure Changes

### Before (Old Structure)

```
FK Path Finder/
├── mysql_fk_path_finder.py      # Single script file
├── requirements.txt             # Dependencies
└── README.md                    # Documentation
```

### After (New Structure)

```
FK Path Finder/
├── mysql_fk_path_finder.py      # OLD - kept for reference
├── pyproject.toml               # NEW - package config
├── README.md                    # UPDATED
├── MIGRATION.md                 # NEW - this file
├── CHANGELOG.md                 # NEW - version history
├── CONTRIBUTING.md              # NEW - contribution guide
├── USAGE_EXAMPLES.md            # NEW - detailed examples
├── LICENSE                      # License file
├── config.example.json          # NEW - example config
├── .env.example                 # NEW - example env vars
├── src/
│   └── fk_path_finder/          # NEW - main package
│       ├── __init__.py          # Package exports
│       ├── __main__.py          # Module entry point
│       ├── cli.py               # Click CLI interface
│       ├── database.py          # MySQL connection & schema
│       ├── graph.py             # Graph building & path finding
│       ├── finder.py            # Main orchestration
│       └── types.py             # Type definitions & config
├── tests/                       # NEW - test suite
│   ├── __init__.py
│   ├── test_database.py
│   ├── test_graph.py
│   └── test_finder.py
└── .github/                     # NEW - GitHub templates
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## API Usage Migration

### Before: Not Possible

The old script could not be imported as a module.

### After: Full Library Support

#### Basic API Usage

```python
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config

# Method 1: Direct configuration
config = Config(
    host="localhost",
    user="root",
    password="secret",
    database="sakila"
)

# Method 2: From environment variables
config = Config.from_env()

# Method 3: From config file
config = Config.from_file("config.json")

# Create and use finder
finder = FKPathFinder(config)
finder.connect()
finder.select_database()
finder.fetch_foreign_keys()
finder.build_graph()

result = finder.find_paths("film", "actor")
finder.display_paths(result)
```

#### Advanced API Usage

```python
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config, PathResult
import json

# Configuration
config = Config.from_env()

# Initialize
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

# Process results programmatically
paths_data = {
    "source": "film_actor.film_id",
    "target": "actor.actor_id",
    "total_paths": result.total_paths,
    "displayed_paths": len(result.paths),
    "paths": [
        {"hops": len(path), "route": path}
        for path in result.paths
    ]
}

# Export to JSON
with open("paths_result.json", "w") as f:
    json.dump(paths_data, f, indent=2)

# Cleanup
finder.close()
```

---

## Troubleshooting

### Issue: Command not found: fk-finder

**Cause**: Package not installed or not in PATH

**Solution**:
```bash
# Reinstall
pip install -e .

# Check installation
which fk-finder        # Linux/Mac
where fk-finder        # Windows

# Use module syntax as fallback
python -m fk_path_finder
```

### Issue: Import errors

**Cause**: Package not installed in current environment

**Solution**:
```bash
# Ensure you're in the correct directory
cd "FK Path Finder"

# Reinstall
pip install -e .

# Verify
python -c "from fk_path_finder import FKPathFinder; print('OK')"
```

### Issue: Click not found

**Cause**: Missing dependencies

**Solution**:
```bash
# Install with all dependencies
pip install -e ".[dev]"

# Or just the runtime dependencies
pip install click>=8.0.0
```

### Issue: Different results than old script

**Cause**: Possible changes in graph traversal or output formatting

**Solution**:
1. Verify you're using the same database
2. Check that foreign keys haven't changed
3. Compare with `--plain` flag to rule out display differences
4. Open an issue if results are genuinely different

### Issue: Performance degradation

**Cause**: New features may have different performance characteristics

**Solution**:
```bash
# Limit search scope
fk-finder --max-paths 100 --max-hops 4 --from table1 --to table2

# Use plain output for large results
fk-finder --plain --from table1 --to table2
```

---

## Backward Compatibility

### The Old Script Still Works

The old script `mysql_fk_path_finder.py` is kept for backward compatibility. You can still run:

```bash
python mysql_fk_path_finder.py
```

### When to Use Old vs New

| Scenario | Recommendation |
|:---------|:---------------|
| Quick one-off query | Either (old is fine) |
| Daily usage | New package (better UX) |
| Automation/Scripting | New package (required) |
| Integration with other tools | New package (required) |
| Team collaboration | New package (standardized) |

### Migration Timeline Recommendation

**Week 1-2**: Parallel usage
- Install new package
- Test with your databases
- Keep old script as fallback

**Week 3-4**: Transition
- Update daily workflows to use new package
- Migrate critical scripts
- Update documentation

**Week 5+**: Full adoption
- Remove old script when comfortable
- Archive old documentation
- Train team on new features

---

## Getting Help

### Resources

- **CLI Help**: `fk-finder --help`
- **README**: [README.md](../README.md) - Full documentation
- **Usage Examples**: [USAGE_EXAMPLES.md](../USAGE_EXAMPLES.md) - Detailed scenarios
- **Contributing**: [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute

### Support Channels

- 🐛 **Bug Reports**: [Open an issue](../../issues/new?template=bug_report.md)
- 💡 **Feature Requests**: [Open an issue](../../issues/new?template=feature_request.md)
- ❓ **Questions**: [Open a discussion](../../discussions) (if available)

### Debug Information

When reporting issues, please include:

```bash
# System info
python --version
pip show fk-path-finder
fk-finder --help | head -5

# For import issues
python -c "import fk_path_finder; print(fk_path_finder.__file__)"
```

---

<p align="center">
  <strong>Happy Migrating!</strong> 🚀
</p>

<p align="center">
  If you encounter any issues not covered here, please <a href="../../issues/new?template=bug_report.md">open an issue</a>.
</p>
