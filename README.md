# 🐬 MySQL Foreign Key Path Finder

🔍 A powerful tool to discover all possible paths between two tables or columns in a MySQL database by traversing foreign key relationships bidirectionally.

## 🌟 Overview

The MySQL FK Path Finder allows you to visualize and discover relationships between tables in your database by following foreign key connections. It creates a graph representation of your database schema and finds all possible paths between specified tables or columns, helping you understand complex database structures and relationships.

## ✨ Features

- 🔌 Interactive connection setup for MySQL databases
- 🔎 Automatic discovery of all foreign key relationships
- ↕️ Bidirectional path traversal between tables/columns
- 🎯 Support for both table-level and column-level path finding
- 🎨 Visual representation of paths with color-coded output
- 🔗 Detection of multiple connection paths between entities
- 🔄 Intra-table connections between foreign-key related columns

## ⚙️ Requirements

- 🐍 Python 3.6+
- 🐬 MySQL database with foreign key constraints
- 📦 Required Python packages (see Installation)

## 📥 Installation

1. Clone this repository or download the script
2. Install the required Python packages:

```bash
pip install mysql-connector-python rich
```

## ▶️ Usage

Run the script directly:

```bash
python mysql_fk_path_finder.py
```

The tool will guide you through:
1. Providing MySQL connection details (host, port, username, password)
2. Selecting a database from the available options
3. Viewing the foreign key relationships in your database
4. Specifying start and end points (tables or `table`.`column`) to find paths between them

### 💡 Example Queries

You can find paths between:
- Two tables: `films` → `actors`
- Specific columns: `film_actor.film_id` → `film.title`
- Mixed: `film_actor` → `actor.first_name`

## 🧠 How It Works

1. The tool connects to your MySQL database and retrieves all foreign key relationships from `information_schema`
2. It builds a bidirectional graph where nodes are `table.column` and edges represent foreign key relationships
3. Additionally, it creates intra-table edges between all foreign-key related columns within the same table
4. Using breadth-first search, it finds all possible paths between the specified start and end points
5. Results are displayed with clear visualization of the relationships

## 📊 Example Output

```
Path 1 (2 hops): `film`.`film_id` → `film_actor`.`film_id` → `actor`.`actor_id`
Path 2 (3 hops): `film`.`category_id` → `film_category`.`category_id` → `category`.`category_id`
```

## ⚠️ Limitations

- Currently only handles single-column foreign keys (composite foreign keys are skipped)
- Requires read access to `information_schema` tables
- Performance may vary depending on database size and complexity

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.