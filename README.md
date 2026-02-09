# Dagster Demo Project

A demo project showing Dagster's factory pattern (YAML-defined pipelines) for users coming from Apache Airflow.

## 🚀 Quick Start

```bash
# Install dependencies
make install

# Start Dagster with both code locations
make dev

# Access UI at http://localhost:3000
```

## 📋 Prerequisites

- Python 3.8+
- pip

## 🏗️ Project Structure

```
dagster_demo/
├── src/
│   ├── ingestion_pipelines/         # Code Location 1: Raw data ingestion (YAML)
│   │   ├── definitions.py          # Loads YAML pipelines
│   │   └── config/                 # YAML pipeline configs (with schedules)
│   │       ├── sample_pipeline.yaml
│   │       └── albums_pipeline.yaml
│   │
│   ├── data_marts/                 # Code Location 2: Analytics marts (Python)
│   │   ├── definitions.py          # Loads Python assets
│   │   └── assets.py               # Mart transformations
│   │
│   └── shared/                     # Shared utilities
│       └── factories/              # Factory pattern (like Airflow's plugins/)
│           ├── __init__.py
│           └── asset_builder.py   # YAML → Assets + Schedules
│
├── workspace.yaml                  # Defines both code locations
├── Makefile                        # Common commands
├── pyproject.toml                  # Dependencies
├── README.md                       # This file
└── AIRFLOW_COMPARISON.md           # Detailed Airflow vs Dagster comparison
```

## 🎯 What This Demo Shows

### 1. Factory Pattern (YAML-Defined Pipelines)

Similar to Airflow's `plugins/dagbuilder.py` pattern where entire pipelines are defined in YAML.

**Airflow approach:**
```yaml
# config/dag.yaml
dag_id: my_pipeline
schedule: "0 2 * * *"
tasks:
  fetch_data:
    operator: HttpOperator
```

**Dagster approach (this project):**
```yaml
# config/pipeline.yaml
assets:
  fetch_data:
    type: api_fetch
    url: https://api.example.com/data

schedules:
  - name: daily_refresh
    cron: "0 2 * * *"
    asset_selection: "*"
```

### 2. Multiple Code Locations

Like having separate DAG folders in Airflow:
- **`ingestion_pipelines`**: Raw data ingestion (YAML-defined)
- **`data_marts`**: Analytics transformations (Python)

### 3. Cross-Code-Location Dependencies

Data marts depend on ingestion pipelines:

```
ingestion_pipelines          data_marts
┌─────────────┐            ┌────────────────┐
│ raw_todos   │───────────>│ user_activity_ │
│ raw_comments│            │ mart           │
└─────────────┘            └────────────────┘
```

## 🔧 Available Commands

| Command | Description |
|---------|-------------|
| `make install` | Install dependencies in virtual environment |
| `make dev` | Start Dagster webserver with both code locations |
| `make test` | Run test suite |
| `make clean` | Remove build artifacts |
| `make help` | Show all available commands |

## 📖 Understanding the Factory Pattern

### Creating a YAML Pipeline

**Step 1:** Create a YAML config file

```yaml
# src/ingestion_pipelines/config/my_pipeline.yaml
assets:
  raw_data:
    type: api_fetch
    url: https://api.example.com/data
    description: Fetch data from API

  processed_data:
    type: transform
    description: Process the raw data
    depends_on:
      - raw_data

schedules:
  - name: daily_pipeline
    cron: "0 2 * * *"
    asset_selection: "*"
```

**Step 2:** Load it in definitions.py

```python
# src/ingestion_pipelines/definitions.py
from shared.factories import build_from_yaml
import os

pipeline = build_from_yaml("config/my_pipeline.yaml")

defs = Definitions(
    assets=pipeline['assets'],
    schedules=pipeline['schedules'],
    jobs=pipeline['jobs'],
)
```

**Step 3:** Run it

```bash
make dev
# Go to http://localhost:3000
# Click "Materialize all"
```

### Supported Asset Types

#### `api_fetch`
Fetches data from HTTP endpoint, saves as CSV.

```yaml
asset_name:
  type: api_fetch
  url: https://api.example.com/endpoint
  description: What this fetches
```

#### `transform`
Transforms or combines upstream data.

```yaml
asset_name:
  type: transform
  description: What this does
  depends_on:
    - upstream_asset_1
    - upstream_asset_2
```

### Schedules in YAML

Define schedules just like Airflow's `schedule_interval`:

```yaml
schedules:
  - name: daily_refresh
    cron: "0 2 * * *"          # Cron expression
    asset_selection: "*"       # "*" = all assets, or list specific ones
```

## 🔗 Data Flow in This Demo

```
┌──────────────────────────────────────────────────────────────┐
│ ingestion_pipelines (YAML-defined)                           │
│                                                              │
│  raw_todos ──┐                                               │
│              ├──> merged_data ──> final_analytics            │
│  raw_comments┘                                               │
│                                                              │
│  raw_albums ──┐                                              │
│               ├──> enriched_albums ──> album_stats           │
│  raw_photos ──┘                                              │
└───────────────────────────────┬──────────────────────────────┘
                                │ (dependencies)
                                ▼
┌──────────────────────────────────────────────────────────────┐
│ data_marts (Python)                                          │
│                                                              │
│  user_activity_mart (uses raw_todos, raw_comments)           │
│  album_engagement_mart (uses raw_albums, raw_photos)         │
└──────────────────────────────────────────────────────────────┘
```

## 📊 Output Files

All assets save data to `output/`:

```
output/
├── raw_todos.csv
├── raw_comments.csv
├── user_activity_mart.csv
└── ... (more CSV files)
```

## 🆚 Dagster vs Airflow

For detailed comparison, see **[AIRFLOW_COMPARISON.md](AIRFLOW_COMPARISON.md)**.

### Quick Comparison

| Airflow | Dagster (this project) |
|---------|------------------------|
| `dags/pipeline1/` | `ingestion_pipelines/` code location |
| `dags/pipeline2/` | `data_marts/` code location |
| `plugins/dagbuilder.py` | `shared/factories/asset_builder.py` |
| DAG config YAML | Pipeline config YAML |
| `schedule_interval: "0 2 * * *"` | `schedules: [{cron: "0 2 * * *"}]` |
| XCom for data passing | Direct function parameters |
| Task-centric | Asset-centric (data products) |

### Key Differences

**1. Data Passing**
- **Airflow**: XCom (push/pull, untyped)
- **Dagster**: Function parameters (type-safe)

**2. Dependencies**
- **Airflow**: `>>` operator + XCom
- **Dagster**: Function parameters define both

**3. Testing**
- **Airflow**: Complex mocking (XCom, context)
- **Dagster**: Test like regular Python functions

**4. Local Development**
- **Airflow**: Requires Docker
- **Dagster**: Just `make dev`

## 🎓 When to Use Each Pattern

### Use YAML (Factory Pattern) When:
✅ Standard ingestion patterns (API → CSV)
✅ Many similar pipelines
✅ Non-developers need to create pipelines
✅ Consistency is important

### Use Python (Hand-Written) When:
✅ Complex transformations (like `data_marts`)
✅ Custom business logic
✅ Type safety is priority
✅ IDE autocomplete needed

### Use Multiple Code Locations When:
✅ Different teams own different pipelines
✅ Different deployment schedules
✅ Logical separation (ingestion vs analytics)

## 🐛 Troubleshooting

**Port already in use?**
```bash
lsof -ti:3000 | xargs kill -9
```

**Module not found?**
```bash
make clean
make install
```

**Code location failed to load?**
- Check for Python syntax errors in definitions.py
- Ensure YAML files are valid
- Check logs in terminal

## 🔗 Useful Resources

- [Dagster Docs](https://docs.dagster.io)
- [Dagster University](https://dagster.io/university) - Free courses
- [Airflow to Dagster Migration Guide](https://docs.dagster.io/integrations/airflow)
- [AIRFLOW_COMPARISON.md](AIRFLOW_COMPARISON.md) - Detailed comparison

## 📝 Next Steps

1. ✅ Run `make dev` and explore the UI
2. ✅ View the asset graph to see dependencies across code locations
3. ✅ Materialize all assets to see the data flow
4. ✅ Check the Schedules tab for YAML-defined schedules
5. ✅ Create your own YAML pipeline in `config/`
6. ✅ Add custom transformations in `data_marts/defs/`

---

**Happy Orchestrating! 🎉**
