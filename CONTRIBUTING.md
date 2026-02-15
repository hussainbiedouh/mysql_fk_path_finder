# Contributing to FK Path Finder

First off, thank you for considering contributing to FK Path Finder! It's people like you that make this tool better for everyone.

## 🎯 Ways to Contribute

You can contribute in many ways:

- 🐛 **Report bugs** - Found an issue? Let us know!
- 💡 **Suggest features** - Have an idea? We'd love to hear it!
- 📝 **Improve documentation** - Help us make docs clearer
- 🔧 **Submit fixes** - Fix bugs or implement features
- 🧪 **Add tests** - Help us improve coverage
- 📢 **Spread the word** - Share the project with others

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Pull Requests](#pull-requests)
- [Development Guidelines](#development-guidelines)
  - [Coding Standards](#coding-standards)
  - [Testing](#testing)
  - [Documentation](#documentation)
- [Release Process](#release-process)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our commitment to:

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards others

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- MySQL (for testing)

### Fork the Repository

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fk-path-finder.git
   cd fk-path-finder
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/fk-path-finder.git
   ```

## 🛠️ Development Setup

### 1. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- The package in editable mode
- All runtime dependencies
- Development tools (pytest, mypy, ruff)

### 3. Verify Installation

```bash
# Test CLI
fk-finder --help

# Run tests
pytest

# Check code quality
ruff check src tests
mypy src/fk_path_finder
```

### 4. Set Up Pre-commit (Optional but Recommended)

```bash
pip install pre-commit
pre-commit install
```

## 🤝 How to Contribute

### Reporting Bugs

Before creating a bug report, please:

1. **Check existing issues** - Someone may have already reported it
2. **Update to the latest version** - The bug may already be fixed
3. **Isolate the problem** - Create a minimal reproducible example

When reporting bugs, use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:

- **OS and version**: e.g., Windows 10, macOS 13, Ubuntu 22.04
- **Python version**: Run `python --version`
- **Package version**: Run `pip show fk-path-finder`
- **MySQL version**: Run `SELECT VERSION();` in MySQL
- **Steps to reproduce**: Detailed steps to recreate the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Error messages**: Full traceback or error output
- **Screenshots**: If applicable
- **Database schema**: If relevant to the issue (anonymized)

### Suggesting Features

Feature requests are welcome! Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:

- **Use case**: What problem are you trying to solve?
- **Proposed solution**: Your idea for how to solve it
- **Alternatives**: Other solutions you've considered
- **Additional context**: Screenshots, examples, etc.

### Pull Requests

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/bug-description
   ```

2. **Make your changes** following our [guidelines](#development-guidelines)

3. **Test your changes**:
   ```bash
   pytest
   pytest --cov=fk_path_finder
   ```

4. **Format and lint**:
   ```bash
   ruff format src tests
   ruff check src tests
   mypy src/fk_path_finder
   ```

5. **Update documentation** if needed (README, docstrings, etc.)

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```
   Follow [conventional commits](https://www.conventionalcommits.org/) format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test changes
   - `refactor:` Code refactoring
   - `style:` Code style changes (formatting)
   - `chore:` Maintenance tasks

7. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

8. **Open a Pull Request** on GitHub using our [PR template](.github/PULL_REQUEST_TEMPLATE.md)

#### PR Checklist

- [ ] Code follows our style guidelines
- [ ] Tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Code coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages follow conventional format
- [ ] PR description is clear and complete

## 📐 Development Guidelines

### Coding Standards

#### Python Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Format code
ruff format src tests

# Check for issues
ruff check src tests

# Fix auto-fixable issues
ruff check src tests --fix
```

Configuration is in `pyproject.toml`:
- Line length: 100 characters
- Target Python: 3.8+
- Enabled rules: E, W, F, I, N, D, UP, B, C4, SIM

#### Type Hints

All code should have type hints:

```python
from typing import List, Optional, Dict

def find_paths(
    start: str,
    end: str,
    max_paths: int = 1000
) -> List[List[str]]:
    """Find paths between two nodes.
    
    Args:
        start: Starting node identifier
        end: Ending node identifier
        max_paths: Maximum number of paths to find
        
    Returns:
        List of paths, where each path is a list of node identifiers
    """
    ...
```

Run type checking:
```bash
mypy src/fk_path_finder
```

#### Documentation Strings

Use Google-style docstrings:

```python
def connect(self, config: Config) -> None:
    """Connect to the MySQL database.
    
    Establishes a connection to the MySQL server using the provided
    configuration. The connection is stored internally and can be
    closed with the `close()` method.
    
    Args:
        config: Database configuration containing host, port, user,
            password, and database name.
            
    Raises:
        ConnectionError: If the connection cannot be established.
        AuthenticationError: If the credentials are invalid.
        
    Example:
        >>> config = Config(host="localhost", user="root", database="test")
        >>> finder.connect(config)
    """
```

### Testing

#### Writing Tests

We use pytest. Tests should be in `tests/` directory:

```python
# tests/test_graph.py
import pytest
from fk_path_finder.graph import Graph

class TestGraph:
    """Tests for Graph class."""
    
    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = Graph()
        graph.add_node("table.column")
        assert "table.column" in graph.nodes
    
    def test_add_edge_bidirectional(self):
        """Test adding bidirectional edges."""
        graph = Graph()
        graph.add_edge("a.id", "b.id")
        assert "b.id" in graph.neighbors("a.id")
        assert "a.id" in graph.neighbors("b.id")
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fk_path_finder --cov-report=html

# Run specific test file
pytest tests/test_graph.py

# Run specific test
pytest tests/test_graph.py::TestGraph::test_add_node

# Run with verbose output
pytest -v

# Run only slow tests
pytest -m slow

# Run excluding slow tests
pytest -m "not slow"
```

#### Test Coverage

Aim for high test coverage, especially for critical paths:

```bash
pytest --cov=fk_path_finder --cov-report=term-missing
```

### Documentation

#### Code Documentation

- All public functions/methods must have docstrings
- Complex logic should have inline comments
- Type hints should be used everywhere

#### README Updates

When adding features:
- Update the feature list
- Add usage examples
- Update configuration tables
- Add troubleshooting entries if relevant

#### Changelog

Update `CHANGELOG.md` for user-facing changes:

```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description
```

## 📝 Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, semicolons, etc.)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or correcting tests
- **chore**: Build process or auxiliary tool changes

Examples:
```
feat(cli): add --plain flag for plain text output

fix(graph): handle self-referencing foreign keys correctly

docs(readme): add troubleshooting section for connection errors

test(database): add tests for connection retry logic
```

## 🚀 Release Process

Maintainers only:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release date
3. Create a git tag:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   ```
4. Push tag:
   ```bash
   git push origin v0.1.0
   ```
5. Create GitHub release with notes
6. Build and publish to PyPI (if applicable):
   ```bash
   python -m build
   twine upload dist/*
   ```

## ❓ Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar questions

## 🙏 Thank You!

Every contribution, no matter how small, helps make FK Path Finder better. We appreciate your time and effort!

---

<p align="center">
  Happy Contributing! 🎉
</p>
