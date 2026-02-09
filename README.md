# Dagster Demo Project

A sample Dagster project for learning and experimentation, created for users transitioning from Apache Airflow.

## 🚀 Quick Start

```bash
# Install dependencies
make install

# Start Dagster webserver (runs on http://localhost:3000)
make dev
```

## 📋 Prerequisites

- Python 3.8+
- pip

## 🏗️ Project Structure

```
.
├── Makefile              # Common commands (install, dev, test)
├── README.md             # This file
├── pyproject.toml        # Python project config and dependencies
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── definitions.py    # Main Dagster definitions (like DAGs in Airflow)
│       └── defs/            # Directory for organizing assets, jobs, etc.
│           └── __init__.py
└── tests/
    └── __init__.py
```

## 🔧 Available Commands

| Command | Description |
|---------|-------------|
| `make install` | Install project and dependencies |
| `make dev` | Start Dagster webserver + daemon |
| `make test` | Run test suite |
| `make clean` | Remove build artifacts |
| `make help` | Show all available commands |

## 📚 Dagster vs Airflow - Key Concepts

If you're coming from Airflow, here are the main concept mappings:

| Airflow | Dagster | Notes |
|---------|---------|-------|
| **DAG** | **Job** | A set of tasks/ops to execute |
| **Task** | **Op** (Operation) | Individual unit of computation |
| **Sensor** | **Sensor** | Similar! Polls for conditions |
| **Schedule** | **Schedule** | Similar! Time-based triggers |
| **XCom** | **IO Manager** | Data passing between ops (more powerful) |
| **Operator** | **Op** | Task execution unit |
| **TaskFlow API** | **Asset-based** | Dagster's modern approach focuses on data assets |
| N/A | **Asset** | **NEW!** Data-centric abstraction (recommended) |

### Key Differences

**1. Assets vs Tasks**
- **Airflow**: Task-centric (focus on what to run)
- **Dagster**: Asset-centric (focus on what to produce)
- Assets represent data products (tables, files, ML models)

**2. Development & Testing**
- **Airflow**: Requires running webserver to test DAGs
- **Dagster**: Full local testing without infrastructure

**3. Data Lineage**
- **Airflow**: Manual tracking
- **Dagster**: Built-in automatic lineage tracking

**4. Type System**
- **Airflow**: Minimal typing
- **Dagster**: Strong type system with validation

## 📖 Understanding the Sample Code

### `definitions.py` - The Entry Point

```python
from dagster import Definitions, asset

@asset
def sample_asset():
    """
    Assets represent data products (like tables, files, models).
    This is similar to a task, but focuses on WHAT you're creating.
    """
    return "Hello, Dagster!"

defs = Definitions(
    assets=[sample_asset],
)
```

**Airflow equivalent:**
```python
# In Airflow, this would be a PythonOperator in a DAG
@task
def sample_task():
    return "Hello, Airflow!"

with DAG('sample_dag', ...):
    sample_task()
```

## 🎯 Next Steps

1. **Add more assets**: Create new `@asset` decorated functions
2. **Add dependencies**: Assets can depend on other assets
3. **Add schedules**: Schedule your jobs to run periodically
4. **Add sensors**: Trigger jobs based on external events
5. **Add resources**: Configure connections (databases, APIs, etc.)

### Example: Adding a New Asset

```python
# In src/my_project/definitions.py

@asset
def raw_data():
    """Fetch raw data from API"""
    return fetch_from_api()

@asset
def processed_data(raw_data):  # Depends on raw_data
    """Process the raw data"""
    return transform(raw_data)
```

## 🔗 Useful Resources

- [Dagster Docs](https://docs.dagster.io)
- [Dagster University](https://dagster.io/university) - Free courses
- [Airflow to Dagster Migration Guide](https://docs.dagster.io/integrations/airflow)
- [Example Projects](https://github.com/dagster-io/dagster/tree/master/examples)

## 🐛 Troubleshooting

**Port already in use?**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Module not found?**
```bash
# Reinstall in editable mode
make clean
make install
```

## 📝 Notes for Airflow Users

- **No Executors to Configure**: Dagster handles execution differently
- **No dag_id**: Use descriptive asset/job names
- **No start_date/catchup**: Dagster uses different backfill mechanisms
- **Testing is Easier**: You can unit test assets like regular Python functions
- **No Jinja Templating**: Use Python directly for dynamic behavior

---

**Happy Orchestrating! 🎉**
