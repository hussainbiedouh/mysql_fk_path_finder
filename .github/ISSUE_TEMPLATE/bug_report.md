---
name: Bug report
about: Create a report to help us improve FK Path Finder
title: '[BUG] '
labels: bug
assignees: ''

---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:

1. Go to '...'
2. Run command '...'
3. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## 🖥️ Environment

Please complete the following information:

- **OS**: [e.g., Windows 10, macOS 13, Ubuntu 22.04]
- **Python Version**: [e.g., 3.9.7] (run `python --version`)
- **Package Version**: [e.g., 0.1.0] (run `pip show fk-path-finder`)
- **MySQL Version**: [e.g., 8.0.32] (run `SELECT VERSION();` in MySQL)
- **Installation Method**: [e.g., pip, from source]

## 📋 Error Details

```
Paste the full error message or traceback here
```

## 💾 Configuration

If applicable, provide your configuration (remove sensitive data):

**Config file** (config.json):
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "database": "sakila"
}
```

**Environment variables** (run `env | grep FK_`):
```
FK_MYSQL_HOST=localhost
FK_MYSQL_DATABASE=sakila
```

**Command used**:
```bash
fk-finder --database sakila --from film --to actor
```

## 🗄️ Database Schema

If relevant, describe your database structure or provide a minimal schema that reproduces the issue:

```sql
-- Example schema
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 📸 Screenshots

If applicable, add screenshots to help explain your problem.

## 🔍 Additional Context

Add any other context about the problem here:
- Does this happen consistently or intermittently?
- Have you tried any workarounds?
- Does this happen with other databases?

## ✅ Checklist

- [ ] I've searched existing issues to ensure this isn't a duplicate
- [ ] I've provided all the information requested above
- [ ] I've tested with the latest version of FK Path Finder
- [ ] I've checked that my MySQL user has proper permissions
