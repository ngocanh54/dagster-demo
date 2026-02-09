# Dagster vs Airflow - Side-by-Side Comparison

This document compares the sample pipeline in this repository with how you'd implement the same logic in Airflow.

## Pipeline Overview

The pipeline:
1. Fetches user data from an API (parallel)
2. Fetches posts data from an API (parallel)
3. Cleans user data
4. Enriches posts with user information
5. Creates two analytics outputs: user stats and company stats

## Side-by-Side Code Comparison

### 1. DAG/Pipeline Definition

**Airflow:**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'user_posts_pipeline',
    default_args=default_args,
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
)
```

**Dagster:**
```python
# In schedules.py
from dagster import ScheduleDefinition, define_asset_job

all_assets_job = define_asset_job(
    name="daily_pipeline_job",
    selection=AssetSelection.all(),
)

daily_schedule = ScheduleDefinition(
    name="daily_pipeline_schedule",
    job=all_assets_job,
    cron_schedule="0 2 * * *",
)
```

### 2. Data Fetching Tasks

**Airflow:**
```python
def fetch_users(**context):
    import requests
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    users = response.json()
    # Push to XCom (untyped, stored in metadata DB)
    context['task_instance'].xcom_push(key='users', value=users)

fetch_users_task = PythonOperator(
    task_id='fetch_users',
    python_callable=fetch_users,
    dag=dag,
)
```

**Dagster:**
```python
@asset(description="Fetch user data from JSONPlaceholder API")
def raw_users(context: AssetExecutionContext) -> pd.DataFrame:
    """Type-safe, efficient data passing"""
    response = requests.get("https://jsonplaceholder.typicode.com/users")
    users_data = response.json()
    return pd.DataFrame(users_data)  # Returns directly (type-safe)
```

**Key Differences:**
- Dagster: Type hints, direct returns, no XCom needed
- Airflow: XCom push/pull, untyped, stored in metadata DB

### 3. Task Dependencies & Data Passing

**Key difference between the two approaches:**

In Airflow, these are **two separate concepts**:
1. **Task dependencies** (execution order): Use `>>`
2. **Data passing** (sharing data): Use XCom

In Dagster, **they're unified**: Function parameters define both!

#### Airflow Approach (Two Separate Systems):

```python
# Part 1: Define the tasks
def fetch_users(**context):
    users = get_users_from_api()
    # Push to XCom to share data
    context['task_instance'].xcom_push(key='users', value=users)

def clean_users(**context):
    # Pull from XCom to get data
    ti = context['task_instance']
    users = ti.xcom_pull(task_ids='fetch_users', key='users')

    cleaned = transform_users(users)
    # Push for next task
    ti.xcom_push(key='cleaned_users', value=cleaned)

fetch_task = PythonOperator(task_id='fetch_users', python_callable=fetch_users, dag=dag)
clean_task = PythonOperator(task_id='clean_users', python_callable=clean_users, dag=dag)

# Part 2: Separately define execution order with >>
# This ONLY controls execution order, NOT data flow!
fetch_task >> clean_task
```

**Airflow approach characteristics:**
- Two separate systems to maintain (>> for order, XCom for data)
- XCom keys are strings - typos cause runtime errors
- Need to know task_ids of upstream tasks
- No type safety - data type is unknown until runtime
- XCom data stored in metadata DB (performance issues with large data)
- Dependency and data flow are disconnected - hard to trace

#### Dagster Approach (Unified):

```python
@asset
def raw_users(context: AssetExecutionContext) -> pd.DataFrame:
    """Just return the data"""
    users = get_users_from_api()
    return users  # That's it!

@asset
def cleaned_users(
    context: AssetExecutionContext,
    raw_users: pd.DataFrame  # ← This does BOTH:
                             #   1. Creates dependency (runs after raw_users)
                             #   2. Receives the data from raw_users
) -> pd.DataFrame:
    """Dependencies and data flow defined in one place"""
    cleaned = transform_users(raw_users)
    return cleaned  # Pass to next asset
```

**How it works:**
- The parameter `raw_users: pd.DataFrame` tells Dagster:
  1. "This asset depends on `raw_users`" (execution order)
  2. "Pass me the data from `raw_users`" (data flow)
- **Both concepts unified in one declaration!**

**Dagster approach characteristics:**
- One system for both dependencies and data flow
- Type-safe: `pd.DataFrame` catches errors early
- Works like normal Python functions
- Automatic data lineage tracking
- Refactoring is safe - rename the asset, parameter updates automatically
- Easy to test - just call the function!

**Example - What happens when you materialize `cleaned_users`:**
1. Dagster sees it needs `raw_users` parameter
2. Automatically runs `raw_users` first
3. Takes the return value (DataFrame)
4. Passes it to `cleaned_users` as the `raw_users` parameter
5. Runs `cleaned_users` with that data

**In Airflow, you'd have to:**
1. Remember to use `>>` to set execution order
2. Remember to `xcom_push` in fetch_users
3. Remember to `xcom_pull` with correct task_id and key in clean_users
4. Hope you didn't make any typos!

### 4. Multiple Dependencies

**When a task needs data from multiple upstream tasks, the difference becomes even more clear.**

**Airflow:**
```python
def enrich_posts(**context):
    ti = context['task_instance']

    # Manually pull from each upstream task's XCom
    # Need to know exact task_ids and keys
    posts = ti.xcom_pull(task_ids='fetch_posts', key='posts')
    users = ti.xcom_pull(task_ids='clean_users', key='cleaned_users')

    # If someone renames a task or changes a key, this breaks!
    enriched = posts.merge(users, ...)
    ti.xcom_push(key='enriched_posts', value=enriched)

enrich_task = PythonOperator(
    task_id='enrich_posts',
    python_callable=enrich_posts,
    dag=dag,
)

# Separately define that both tasks must run first
# This ONLY controls order, not data flow!
[fetch_posts_task, clean_users_task] >> enrich_task
```

**Dagster:**
```python
@asset
def enriched_posts(
    raw_posts: pd.DataFrame,      # ← Depends on raw_posts, gets its data
    cleaned_users: pd.DataFrame   # ← Depends on cleaned_users, gets its data
) -> pd.DataFrame:
    """
    Two parameters = two dependencies!
    Dagster automatically:
    1. Runs raw_posts first
    2. Runs cleaned_users first (can run in parallel with raw_posts!)
    3. Waits for both to complete
    4. Passes their return values to this function
    """
    return raw_posts.merge(cleaned_users, ...)
```

**Key Differences:**
- Dagster: Just list what data you need as parameters - that's it!
- Dependencies and data flow are the same thing
- No manual XCom management
- Type-safe: IDE autocomplete works, type errors caught early
- Refactor-friendly: rename `raw_posts` → automatically updates everywhere
- Airflow: Multiple XCom pulls, verbose, error-prone, hard to track

**The Power of This Approach:**
When you write `enriched_posts(raw_posts, cleaned_users)`, you're telling Dagster:
- "I need the data from raw_posts and cleaned_users"
- Dagster figures out: "I need to run those assets first and pass their results"
- **The data flow IS the dependency graph!**

### 5. Parallel Execution

**Airflow:**
```python
# Tasks with no dependencies run in parallel automatically
fetch_users_task = PythonOperator(task_id='fetch_users', ...)
fetch_posts_task = PythonOperator(task_id='fetch_posts', ...)

# Both run in parallel (no >> between them)
```

**Dagster:**
```python
# Assets with no dependencies run in parallel automatically
@asset
def raw_users() -> pd.DataFrame: ...

@asset
def raw_posts() -> pd.DataFrame: ...

# Both run in parallel automatically
```

**Key Differences:**
- Both handle parallel execution similarly
- Dagster shows parallelism visually in the lineage graph

### 6. Testing

**Airflow:**
```python
# Testing is complex - need to mock context, XCom, etc.
def test_clean_users():
    from airflow.models import TaskInstance

    # Complex setup
    mock_context = {
        'task_instance': Mock(TaskInstance),
        'ti': Mock(),
    }
    mock_context['ti'].xcom_pull.return_value = sample_users

    clean_users(**mock_context)

    # Assert on XCom push
    mock_context['ti'].xcom_push.assert_called_with(...)
```

**Dagster:**
```python
# Testing is just regular Python testing
def test_cleaned_users():
    # Create sample data
    sample_users = pd.DataFrame([...])

    # Call the asset directly (it's just a function!)
    result = cleaned_users(mock_context, sample_users)

    # Assert on return value
    assert len(result) == expected_length
    assert 'full_name' in result.columns
```

**Key Differences:**
- Dagster: Test like regular Python functions
- Airflow: Complex mocking, XCom, context, TaskInstance

## Summary Table

| Feature | Airflow | Dagster |
|---------|---------|---------|
| **Data Passing** | XCom (untyped, DB-stored) | Function parameters (type-safe) |
| **Dependencies** | `>>` operator + XCom pulls | Function parameters |
| **Type Safety** | No | Yes |
| **Testing** | Complex (mocking) | Simple (pure functions) |
| **Local Dev** | Needs Docker/DB | Just Python |
| **Lineage** | Manual | Automatic |
| **Code Style** | Imperative (how to do it) | Declarative (what to produce) |
| **Learning Curve** | Higher | Lower (for Python devs) |
| **Data-Centric** | Task-centric | Asset-centric |

## File Structure Comparison

**Airflow:**
```
dags/
├── user_posts_pipeline/     # DAG folder
│   ├── dag.py              # Main DAG definition
│   ├── config.yaml         # Configuration (if using DAG factory)
│   └── sql/
│       └── queries.sql
├── another_pipeline/
│   ├── dag.py
│   └── config.yaml
└── common/                  # Shared utilities
    ├── operators/
    └── utils/
```

**Dagster:**
```
.
├── Makefile
├── pyproject.toml
├── src/
│   └── ingestion_sample/
│       ├── __init__.py
│       ├── definitions.py      # Entry point
│       └── defs/
│           ├── __init__.py
│           ├── assets.py       # Asset definitions
│           └── schedules.py    # Schedule definitions
├── output/                     # Data output directory
│   ├── raw_users.csv
│   ├── posts_analytics.csv
│   └── ...
└── tests/
    └── __init__.py
```

## Running the Pipeline

**Airflow:**
```bash
# Start services
docker-compose up -d

# Access UI
open http://localhost:8080

# Trigger DAG
airflow dags trigger user_posts_pipeline
```

**Dagster:**
```bash
# Start everything (no Docker needed)
make dev

# Access UI
open http://localhost:3000

# Click "Materialize all" in the UI
```

**Dagster Option 1 - YAML (same pattern):**
```yaml
assets:
  revenue:
    type: bigquery_query
    sql: revenue.sql
  revenue__ratio_change:
    type: bigquery_alert
    args:
      alert_type: ratio_change
      threshold: 0.05
    depends_on:
      - revenue
```

**Dagster Option 2 - Python (recommended):**
```python
@asset
def revenue(context):
    return run_sql_file("revenue.sql")

@asset
def revenue__ratio_change(context, revenue):  # Lineage automatic!
    return check_ratio_change(revenue, threshold=0.05)
```

**Both work! Choose based on your team's preference.**

## Key Differences Summary

1. **Mental Model**:
   - Airflow: Task-centric (focus on execution steps)
   - Dagster: Asset-centric (focus on data products)

2. **Data Passing**:
   - Airflow: XCom (push/pull pattern, stored in metadata DB)
   - Dagster: Function parameters (direct passing, type-safe)

3. **Dependencies**:
   - Airflow: Two systems - `>>` for order, XCom for data
   - Dagster: Unified - function parameters define both

4. **Testing**:
   - Airflow: Requires mocking context, XCom, TaskInstance
   - Dagster: Test assets like regular Python functions

5. **Local Development**:
   - Airflow: Typically requires Docker for full setup
   - Dagster: Runs with just Python (`make dev`)

6. **Lineage**:
   - Airflow: Implicit from `>>` operators, manual for data flow
   - Dagster: Automatic from function parameters or explicit in YAML

7. **YAML Configuration**:
   - Airflow: Common pattern for defining entire DAG structure
   - Dagster: Possible with custom factory, but Python is standard

8. **Type Safety**:
   - Airflow: Untyped (runtime discovery)
   - Dagster: Typed (compile-time checking when using Python)

## Choosing an Approach

Both frameworks are capable orchestration tools. Consider:

**Airflow may fit better if:**
- You have existing Airflow infrastructure
- Your team is familiar with Airflow patterns
- You prefer YAML-defined pipeline structures
- You need specific Airflow operators or integrations

**Dagster may fit better if:**
- You're starting a new project
- Type safety and IDE support are priorities
- You prefer Python over YAML for pipeline definitions
- Asset-centric thinking aligns with your use case

**For exploration:** Try both with a sample pipeline to see which mental model fits your team better.
