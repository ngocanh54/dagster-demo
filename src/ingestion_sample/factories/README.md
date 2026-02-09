# Asset Factories

This folder contains factory patterns for dynamically creating Dagster assets, similar to Airflow's `plugins/dagbuilder.py` pattern.

## Purpose

In Airflow, you might use `plugins/` folder with a `dagbuilder.py` to create DAGs from YAML config:

```python
# Airflow pattern
from plugins.dagbuilder import DagBuilder

dag = DagBuilder("config.yaml").build()
```

In Dagster, this `factories/` folder serves the same purpose:

```python
# Dagster equivalent
from ingestion_sample.factories import build_assets_from_yaml

assets = build_assets_from_yaml("config/pipeline.yaml")
```

## Usage

### 1. Create a YAML configuration file

```yaml
# config/my_pipeline.yaml
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
```

### 2. Load it in your definitions

```python
# In src/ingestion_sample/definitions.py
from dagster import Definitions
from ingestion_sample.factories import build_assets_from_yaml

# Build assets from YAML config
config_assets = build_assets_from_yaml("config/my_pipeline.yaml")

defs = Definitions(
    assets=config_assets,
)
```

## Airflow vs Dagster Comparison

| Airflow | Dagster |
|---------|---------|
| `plugins/dagbuilder.py` | `factories/asset_builder.py` |
| `config/dag_config.yaml` | `config/pipeline_config.yaml` |
| `DagBuilder(config).build()` | `build_assets_from_yaml(config)` |
| Creates DAG with tasks | Creates assets with dependencies |
| Uses `>>` for dependencies in code | Uses `depends_on` in YAML |

## Supported Asset Types

### `api_fetch`
Fetches data from an API endpoint.

```yaml
asset_name:
  type: api_fetch
  url: https://api.example.com/endpoint
  description: Optional description
```

### `transform`
Transforms data, optionally using SQL file.

```yaml
asset_name:
  type: transform
  sql_file: queries/transform.sql  # Optional
  depends_on:
    - upstream_asset_1
    - upstream_asset_2
  description: Optional description
```

## Extending

To add new asset types:

1. Add a new `_create_<type>_asset` method in `AssetBuilder`
2. Handle it in the `build_assets()` method
3. Document it in this README

Example:

```python
def _create_database_query_asset(self, asset_name: str, asset_config: Dict[str, Any]):
    """Create an asset that queries a database."""
    query = asset_config['query']

    @asset(name=asset_name, description=asset_config.get('description', ''))
    def database_query_asset(context: AssetExecutionContext) -> Output[pd.DataFrame]:
        # Execute query
        df = execute_query(query)
        return Output(value=df, metadata={...})

    return database_query_asset
```

## Folder Structure

```
src/ingestion_sample/
├── factories/              # Similar to Airflow's plugins/
│   ├── __init__.py
│   ├── asset_builder.py   # Similar to dagbuilder.py
│   └── README.md          # This file
├── defs/
│   ├── assets.py          # Hand-written assets (if any)
│   └── schedules.py
└── definitions.py          # Load both config-based and hand-written assets
```

## Benefits

- **Centralized configuration**: Define entire pipelines in YAML
- **Non-technical users**: Analysts can modify YAML without touching Python
- **Consistency**: Enforce patterns across similar pipelines
- **Rapid development**: Add new assets by editing YAML

## When to Use

✅ **Use factories/YAML when:**
- You have many similar pipelines
- Non-developers need to create/modify pipelines
- You want enforced patterns

❌ **Use regular Python assets when:**
- Complex custom logic needed
- One-off unique pipelines
- Type safety and IDE autocomplete are priorities
