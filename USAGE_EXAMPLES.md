# Usage Examples

This document provides real-world usage scenarios and examples for FK Path Finder.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Common Scenarios](#common-scenarios)
- [Advanced Queries](#advanced-queries)
- [Working with Large Databases](#working-with-large-databases)
- [Automation & Scripting](#automation--scripting)
- [Integration Examples](#integration-examples)

---

## Basic Usage

### Example 1: Finding Paths Between Two Tables

**Scenario**: You want to understand how the `film` table relates to the `actor` table in a movie database.

```bash
fk-finder --database sakila --from film --to actor
```

**Expected Output**:
```
╭──────────────────────────────────────────────────────────────╮
│                    FK Path Finder v0.1.0                     │
╰──────────────────────────────────────────────────────────────╯

Database: sakila
Searching paths from 'film' to 'actor'...

╭────────────────────────────────────╮
│ Found 1 path(s)                    │
╰────────────────────────────────────╯
  Path 1 (2 hops): `film`.`film_id` → `film_actor`.`film_id` → `film_actor`.`actor_id` → `actor`.`actor_id`
```

**Explanation**: The path shows that you can go from `film` to `actor` through the `film_actor` junction table.

---

### Example 2: Column-Specific Path Finding

**Scenario**: You need to find how `film_actor.film_id` specifically connects to `actor.actor_id`.

```bash
fk-finder --database sakila --from film_actor.film_id --to actor.actor_id
```

**Expected Output**:
```
Found 1 path(s):
  Path 1 (2 hops): `film_actor`.`film_id` → `film_actor`.`actor_id` → `actor`.`actor_id`
```

**Note**: This is more specific than table-level search and may yield different results.

---

### Example 3: Using Environment Variables

**Scenario**: You frequently work with the same database and want to avoid typing credentials repeatedly.

```bash
# Set up once in your .bashrc or .zshrc
export FK_MYSQL_HOST=localhost
export FK_MYSQL_PORT=3306
export FK_MYSQL_USER=dbadmin
export FK_MYSQL_PASSWORD=secretpassword
export FK_MYSQL_DATABASE=sakila

# Now run queries without credentials
fk-finder --from customer --to film
```

---

## Common Scenarios

### Scenario 1: Database Schema Exploration

**Use Case**: You're new to a database and want to understand table relationships.

**Approach**: Start with table-level searches to map out the schema.

```bash
# Find all major entity connections
fk-finder --from customer --to film
fk-finder --from customer --to staff
fk-finder --from rental --to payment
```

**Tips**:
- Use `--max-hops 3` to find direct relationships
- Redirect output to a file for documentation: `fk-finder --from customer --to film > schema-docs.txt`

---

### Scenario 2: Data Lineage Investigation

**Use Case**: You need to trace how data flows from one table to another for compliance/auditing.

```bash
# Find all paths from a source table to target
fk-finder --database production --from user_profiles --to audit_logs --max-paths 2000 --max-hops 8
```

**Output Analysis**:
- Multiple paths indicate redundant data flows
- Long paths may indicate inefficient data architecture
- Direct paths (1-2 hops) are usually preferred

---

### Scenario 3: Finding Orphaned Data Routes

**Use Case**: Identify if there are any unexpected paths that could lead to orphaned records.

```bash
# Check if there are multiple ways to reach a table
fk-finder --from orders --to customers --max-hops 5
```

**Interpretation**:
- If you find multiple paths, verify which one is the "correct" relationship
- Unexpected paths might indicate schema design issues

---

### Scenario 4: Query Optimization

**Use Case**: Understand join paths to write better SQL queries.

```bash
fk-finder --from film --to category
```

**Result Application**:
```sql
-- If FK Path Finder shows: film -> film_category -> category
-- Your query should be:
SELECT f.title, c.name
FROM film f
JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c ON fc.category_id = c.category_id;
```

---

## Advanced Queries

### Example: Complex Multi-Hop Search

**Scenario**: Find all ways to connect `inventory` to `country` (which might be far apart).

```bash
fk-finder --database sakila \
  --from inventory \
  --to country \
  --max-hops 6 \
  --max-paths 500
```

**Sample Output**:
```
Found 4 path(s)
  Path 1 (3 hops): `inventory`.`film_id` → `film`.`film_id` → `film_actor`.`film_id` → `actor`...
  Path 2 (4 hops): `inventory`.`store_id` → `store`.`store_id` → `address`.`address_id` → `city`...
  Path 3 (5 hops): `inventory`.`film_id` → `film`.`film_id` → `film_category`.`film_id` → ...
  Path 4 (6 hops): `inventory`.`store_id` → `store`.`manager_staff_id` → `staff`.`staff_id` → ...
```

---

### Example: Specific Column Path with Limits

```bash
fk-finder --config production.json \
  --from orders.customer_id \
  --to customers.id \
  --max-paths 100 \
  --plain
```

**Use `--plain` for**:
- Parsing output in scripts
- Saving to log files
- Environments without color support

---

### Example: Finding All Paths Between Multiple Tables

Use a shell script to batch queries:

```bash
#!/bin/bash
# find_all_paths.sh

TABLES=("film" "actor" "customer" "staff" "store")
DATABASE="sakila"

for from_table in "${TABLES[@]}"; do
  for to_table in "${TABLES[@]}"; do
    if [ "$from_table" != "$to_table" ]; then
      echo "=== Paths from $from_table to $to_table ==="
      fk-finder --database "$DATABASE" \
        --from "$from_table" \
        --to "$to_table" \
        --max-hops 4 \
        --plain
      echo ""
    fi
  done
done
```

---

## Working with Large Databases

### Challenge: Performance on Large Schemas

Large databases with many tables and foreign keys can be slow to analyze.

### Solutions:

#### 1. Limit Search Scope

```bash
# Reduce max paths to get quicker results
fk-finder --from users --to orders --max-paths 100 --max-hops 4
```

#### 2. Use Column-Level Search

```bash
# More specific = faster
fk-finder --from users.id --to orders.user_id --max-hops 3
```

#### 3. Plain Text Output

```bash
# Rich formatting can be slow on large outputs
fk-finder --from large_table --to another_table --plain
```

#### 4. Batch Processing with Config Files

Create `production-config.json`:
```json
{
  "host": "prod-db.company.com",
  "port": 3306,
  "user": "readonly_user",
  "password": "***",
  "database": "production",
  "max_path_length": 4,
  "max_paths": 500,
  "display_limit": 10
}
```

Run queries:
```bash
fk-finder --config production-config.json --from users --to transactions
```

#### 5. Off-Peak Analysis

For very large production databases:

```bash
# Schedule during low-traffic hours
0 2 * * * /usr/local/bin/fk-finder --config /etc/fk-finder/nightly.json --from users --to events > /var/log/fk-finder/nightly.log 2>&1
```

---

## Automation & Scripting

### Python Script Example

```python
#!/usr/bin/env python3
"""Batch path finder for multiple table pairs."""

import json
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config

def find_paths_batch(config_file: str, pairs_file: str, output_file: str):
    """Find paths for multiple table pairs.
    
    Args:
        config_file: Path to JSON config file
        pairs_file: JSON file with list of [from, to] pairs
        output_file: Where to save results
    """
    # Load config
    config = Config.from_file(config_file)
    
    # Initialize finder
    finder = FKPathFinder(config)
    finder.connect()
    finder.select_database()
    finder.fetch_foreign_keys()
    finder.build_graph()
    
    # Load table pairs
    with open(pairs_file) as f:
        pairs = json.load(f)
    
    # Find paths for each pair
    results = []
    for from_table, to_table in pairs:
        print(f"Finding paths: {from_table} -> {to_table}")
        result = finder.find_paths(from_table, to_table)
        results.append({
            "from": from_table,
            "to": to_table,
            "path_count": result.total_paths,
            "paths": result.paths[:10]  # Limit stored paths
        })
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    finder.close()
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    find_paths_batch("config.json", "pairs.json", "results.json")
```

**Input pairs.json**:
```json
[
  ["film", "actor"],
  ["customer", "film"],
  ["staff", "store"]
]
```

---

### Bash Script Example

```bash
#!/bin/bash
# check_schema_integrity.sh

# Check if critical paths exist in database
DATABASE="sakila"
REQUIRED_PATHS=(
  "film:actor"
  "customer:rental"
  "staff:store"
)

EXIT_CODE=0

for path in "${REQUIRED_PATHS[@]}"; do
  IFS=':' read -r from to <<< "$path"
  echo "Checking path: $from -> $to"
  
  # Run FK Path Finder and capture output
  output=$(fk-finder --database "$DATABASE" --from "$from" --to "$to" --plain --max-hops 3)
  
  if echo "$output" | grep -q "Found 0 path"; then
    echo "  ❌ FAIL: No path found from $from to $to"
    EXIT_CODE=1
  else
    path_count=$(echo "$output" | grep -oP 'Found \K\d+')
    echo "  ✅ PASS: Found $path_count path(s)"
  fi
done

exit $EXIT_CODE
```

---

## Integration Examples

### Integration with Data Catalog

Use FK Path Finder to populate a data catalog:

```python
# catalog_integration.py
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config
import requests

def update_catalog_with_relationships():
    config = Config.from_env()
    finder = FKPathFinder(config)
    finder.connect()
    finder.select_database()
    finder.fetch_foreign_keys()
    finder.build_graph()
    
    # Get all foreign key relationships
    relationships = []
    for edge in finder.graph.edges:
        relationships.append({
            "source": edge[0],
            "target": edge[1],
            "type": "foreign_key"
        })
    
    # Send to catalog API
    requests.post(
        "https://catalog.company.com/api/relationships",
        json={"relationships": relationships},
        headers={"Authorization": "Bearer TOKEN"}
    )
    
    finder.close()
```

---

### Integration with SQL Generators

```python
# sql_generator.py
from fk_path_finder import FKPathFinder
from fk_path_finder.types import Config

def generate_join_sql(from_table: str, to_table: str) -> str:
    """Generate JOIN SQL based on FK Path Finder results."""
    config = Config.from_env()
    finder = FKPathFinder(config)
    finder.connect()
    finder.select_database()
    finder.fetch_foreign_keys()
    finder.build_graph()
    
    result = finder.find_paths(from_table, to_table, max_paths=1)
    finder.close()
    
    if not result.paths:
        raise ValueError(f"No path found from {from_table} to {to_table}")
    
    path = result.paths[0]
    
    # Generate SQL
    sql_parts = [f"SELECT * FROM {from_table}"]
    
    for i in range(len(path) - 1):
        left = path[i].replace('.', '.')
        right = path[i + 1].replace('.', '.')
        
        # Parse table.column
        left_table, left_col = left.rsplit('.', 1)
        right_table, right_col = right.rsplit('.', 1)
        
        join_type = "JOIN" if i == 0 else "JOIN"
        sql_parts.append(
            f"{join_type} {right_table} ON {left} = {right}"
        )
    
    return "\n".join(sql_parts)

# Usage
sql = generate_join_sql("film", "actor")
print(sql)
# Output:
# SELECT * FROM film
# JOIN film_actor ON film.film_id = film_actor.film_id
# JOIN actor ON film_actor.actor_id = actor.actor_id
```

---

## Tips and Best Practices

### 1. Start Broad, Then Narrow

1. First, find table-level paths to understand relationships
2. Then use column-level searches for specific queries

### 2. Document Common Paths

Save frequently used configurations:

```bash
# Save to alias
alias fk-prod='fk-finder --config ~/.config/fk-finder/production.json'

# Or use wrapper scripts
# /usr/local/bin/fk-sakila
#!/bin/bash
fk-finder --config /etc/fk-finder/sakila.json "$@"
```

### 3. Validate Schema Changes

Before and after schema migrations:

```bash
# Before migration
fk-finder --from orders --to customers --plain > before_migration.txt

# After migration
fk-finder --from orders --to customers --plain > after_migration.txt

# Compare
diff before_migration.txt after_migration.txt
```

### 4. Performance Monitoring

Time your queries:

```bash
time fk-finder --from large_table --to another_table --max-hops 5
```

### 5. Use in CI/CD

Add schema validation to your pipeline:

```yaml
# .github/workflows/schema-check.yml
name: Schema Validation

on: [pull_request]

jobs:
  check-paths:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check critical paths
        run: |
          pip install fk-path-finder
          ./scripts/validate_schema.sh
```

---

<p align="center">
  For more examples, see the <a href="../tests/">tests directory</a>
</p>
