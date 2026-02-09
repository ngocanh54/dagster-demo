# Factory Pattern: Airflow DAGBuilder vs Dagster AssetBuilder

A side-by-side comparison of building pipelines from YAML configuration.

## Overview

Both Airflow and Dagster support dynamically creating pipelines from YAML configuration files. This pattern is useful when you have many similar pipelines or want non-developers to define pipelines.

## Folder Structure Comparison

**Airflow:**
```
your_airflow_project/
├── dags/
│   └── generated_dag.py          # Loads config and creates DAG
├── plugins/
│   └── dagbuilder.py             # DagBuilder factory class
└── config/
    └── my_pipeline.yaml          # YAML configuration
```

**Dagster:**
```
your_dagster_project/
├── src/ingestion_sample/
│   ├── definitions.py            # Loads config and creates assets
│   └── factories/                # Similar to plugins/
│       ├── __init__.py
│       └── asset_builder.py      # AssetBuilder factory class
└── config/
    └── my_pipeline.yaml          # YAML configuration
```

## Code Comparison

### 1. YAML Configuration

Both use similar YAML structure:

**Airflow (config/my_pipeline.yaml):**
```yaml
dag_id: user_posts_pipeline
schedule: "0 2 * * *"

tasks:
  fetch_users:
    operator: HttpOperator
    endpoint: /users
    method: GET

  fetch_posts:
    operator: HttpOperator
    endpoint: /posts
    method: GET

  process_data:
    operator: PythonOperator
    python_callable: process_data_func
    upstream:              # Dependencies defined here
      - fetch_users
      - fetch_posts

  analytics:
    operator: PythonOperator
    python_callable: create_analytics
    upstream:
      - process_data
```

**Dagster (config/my_pipeline.yaml):**
```yaml
assets:
  fetch_users:
    type: api_fetch
    url: https://api.example.com/users
    description: Fetch user data

  fetch_posts:
    type: api_fetch
    url: https://api.example.com/posts
    description: Fetch posts data

  process_data:
    type: transform
    description: Process combined data
    depends_on:           # Dependencies defined here
      - fetch_users
      - fetch_posts

  analytics:
    type: transform
    description: Create analytics
    depends_on:
      - process_data
```

### 2. Factory/Builder Class

**Airflow (plugins/dagbuilder.py):**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.http_simple import SimpleHttpOperator
import yaml

class DagBuilder:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def build(self):
        """Build DAG from config"""
        dag_config = self.config

        with DAG(
            dag_id=dag_config['dag_id'],
            schedule_interval=dag_config.get('schedule'),
            catchup=False,
        ) as dag:
            tasks = {}

            # Create tasks
            for task_name, task_config in dag_config['tasks'].items():
                if task_config['operator'] == 'HttpOperator':
                    task = SimpleHttpOperator(
                        task_id=task_name,
                        endpoint=task_config['endpoint'],
                        method=task_config['method'],
                    )
                elif task_config['operator'] == 'PythonOperator':
                    task = PythonOperator(
                        task_id=task_name,
                        python_callable=task_config['python_callable'],
                    )

                tasks[task_name] = task

            # Set dependencies
            for task_name, task_config in dag_config['tasks'].items():
                if 'upstream' in task_config:
                    for upstream_name in task_config['upstream']:
                        tasks[upstream_name] >> tasks[task_name]

        return dag
```

**Dagster (factories/asset_builder.py):**
```python
from dagster import asset, AssetExecutionContext, Output
import yaml
import pandas as pd
import requests

class AssetBuilder:
    def __init__(self, config_path, output_dir="output"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.output_dir = output_dir

    def _create_api_fetch_asset(self, asset_name, asset_config):
        """Create API fetch asset"""
        url = asset_config['url']

        @asset(name=asset_name, description=asset_config.get('description', ''))
        def api_fetch_asset(context: AssetExecutionContext) -> Output[pd.DataFrame]:
            response = requests.get(url)
            df = pd.DataFrame(response.json())
            return Output(value=df, metadata={"num_records": len(df)})

        return api_fetch_asset

    def _create_transform_asset(self, asset_name, asset_config, dependencies):
        """Create transform asset with dependencies"""
        description = asset_config.get('description', '')

        @asset(name=asset_name, description=description)
        def transform_asset(context: AssetExecutionContext, **kwargs) -> Output[pd.DataFrame]:
            # Access upstream data via kwargs
            upstream_dfs = kwargs.values()
            df = pd.concat(upstream_dfs, ignore_index=True)
            return Output(value=df, metadata={"num_records": len(df)})

        return transform_asset

    def build_assets(self):
        """Build assets from config"""
        assets_config = self.config.get('assets', {})
        built_assets = {}
        asset_list = []

        for asset_name, asset_config in assets_config.items():
            asset_type = asset_config.get('type', 'transform')

            if asset_type == 'api_fetch':
                asset_def = self._create_api_fetch_asset(asset_name, asset_config)
            elif asset_type == 'transform':
                depends_on = asset_config.get('depends_on', [])
                dependencies = [built_assets[dep] for dep in depends_on if dep in built_assets]
                asset_def = self._create_transform_asset(asset_name, asset_config, dependencies)

            built_assets[asset_name] = asset_def
            asset_list.append(asset_def)

        return asset_list

# Convenience function
def build_assets_from_yaml(yaml_path, output_dir="output"):
    builder = AssetBuilder(yaml_path, output_dir)
    return builder.build_assets()
```

### 3. Loading the Pipeline

**Airflow (dags/generated_dag.py):**
```python
from plugins.dagbuilder import DagBuilder

# Load and create DAG from YAML
dag = DagBuilder('config/my_pipeline.yaml').build()

# That's it! Airflow will pick up this DAG
```

**Dagster (definitions.py):**
```python
from dagster import Definitions
from ingestion_sample.factories import build_assets_from_yaml

# Load and create assets from YAML
config_assets = build_assets_from_yaml('config/my_pipeline.yaml')

defs = Definitions(
    assets=config_assets,
)
```

## Key Differences

| Aspect | Airflow | Dagster |
|--------|---------|---------|
| **Location** | `plugins/dagbuilder.py` | `factories/asset_builder.py` |
| **What it creates** | DAG with tasks | List of assets |
| **Dependencies** | Set with `>>` operator after creation | Set via `depends_on` in YAML + function params |
| **Configuration** | DAG-level config (schedule, owner, etc.) | Asset-level config (description, type, etc.) |
| **Returns** | Single DAG object | List of asset definitions |
| **Operator mapping** | Maps YAML to Airflow operators | Maps YAML to asset types |

## Usage Patterns

### Airflow Pattern

```python
# Step 1: Define YAML config
# config/pipeline.yaml

# Step 2: Create DagBuilder in plugins/
# plugins/dagbuilder.py

# Step 3: Create DAG file that uses builder
# dags/my_dag.py
from plugins.dagbuilder import DagBuilder
dag = DagBuilder('config/pipeline.yaml').build()
```

### Dagster Pattern

```python
# Step 1: Define YAML config
# config/pipeline.yaml

# Step 2: Create AssetBuilder in factories/
# src/ingestion_sample/factories/asset_builder.py

# Step 3: Load in definitions.py
# src/ingestion_sample/definitions.py
from ingestion_sample.factories import build_assets_from_yaml
assets = build_assets_from_yaml('config/pipeline.yaml')
defs = Definitions(assets=assets)
```

## Example: Real Usage

**Create your YAML config:**
```yaml
# config/example_pipeline.yaml
assets:
  api_users:
    type: api_fetch
    url: https://jsonplaceholder.typicode.com/users

  api_posts:
    type: api_fetch
    url: https://jsonplaceholder.typicode.com/posts

  combined:
    type: transform
    depends_on:
      - api_users
      - api_posts
```

**Load it in your definitions:**
```python
# src/ingestion_sample/definitions.py
from dagster import Definitions
from ingestion_sample.factories import build_assets_from_yaml
from ingestion_sample.defs.assets import *  # Your hand-written assets

# Combine config-based assets with hand-written ones
config_assets = build_assets_from_yaml("config/example_pipeline.yaml")

defs = Definitions(
    assets=[
        # Config-based assets
        *config_assets,
        # Hand-written assets (from defs/assets.py)
        raw_users,
        raw_posts,
        # ... etc
    ],
)
```

## Benefits of This Pattern

✅ **Centralized configuration**: Entire pipeline in one YAML file
✅ **Non-technical users**: Analysts can create pipelines without Python
✅ **Rapid development**: Add new pipelines quickly
✅ **Consistency**: Enforced patterns across pipelines
✅ **Version control**: Track pipeline changes in YAML

## When to Use

**Use this pattern when:**
- You have many similar pipelines (e.g., 50+ ingestion pipelines)
- Non-developers need to create/modify pipelines
- You want to enforce standard patterns
- Configuration changes shouldn't require Python knowledge

**Use regular Python code when:**
- Complex custom logic is needed
- You have unique, one-off pipelines
- Type safety and IDE autocomplete are priorities
- The pipeline requires dynamic runtime decisions

## Summary

Both Airflow and Dagster support the factory/builder pattern for YAML-based pipeline configuration:

- **Airflow**: `plugins/dagbuilder.py` + `config.yaml` → DAG
- **Dagster**: `factories/asset_builder.py` + `config.yaml` → Assets

The core concepts are the same, just adapted to each tool's architecture (tasks vs assets).
