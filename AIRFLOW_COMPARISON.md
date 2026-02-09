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
- ✅ Dagster: Type hints, direct returns, no XCom needed
- ❌ Airflow: XCom push/pull, untyped, stored in metadata DB

### 3. Task Dependencies & Data Passing

**Airflow:**
```python
def clean_users(**context):
    # Pull from XCom (need to know the key and task_id)
    ti = context['task_instance']
    users = ti.xcom_pull(task_ids='fetch_users', key='users')

    # Transform data
    cleaned = transform_users(users)

    # Push to XCom for next task
    ti.xcom_push(key='cleaned_users', value=cleaned)

clean_users_task = PythonOperator(
    task_id='clean_users',
    python_callable=clean_users,
    dag=dag,
)

# Define dependency
fetch_users_task >> clean_users_task
```

**Dagster:**
```python
@asset(deps=[raw_users])
def cleaned_users(
    context: AssetExecutionContext,
    raw_users: pd.DataFrame  # Direct parameter passing!
) -> pd.DataFrame:
    """Data is passed directly as function parameters"""
    df = raw_users.copy()
    # Transform data
    cleaned = transform_users(df)
    return cleaned  # Just return it
```

**Key Differences:**
- ✅ Dagster: Dependencies via parameters, type-safe, like regular Python
- ❌ Airflow: XCom push/pull, need task_ids and keys, error-prone

### 4. Multiple Dependencies

**Airflow:**
```python
def enrich_posts(**context):
    ti = context['task_instance']

    # Pull from multiple XComs
    posts = ti.xcom_pull(task_ids='fetch_posts', key='posts')
    users = ti.xcom_pull(task_ids='clean_users', key='cleaned_users')

    # Join data
    enriched = posts.merge(users, ...)
    ti.xcom_push(key='enriched_posts', value=enriched)

enrich_task = PythonOperator(
    task_id='enrich_posts',
    python_callable=enrich_posts,
    dag=dag,
)

# Dependencies
[fetch_posts_task, clean_users_task] >> enrich_task
```

**Dagster:**
```python
@asset(deps=[raw_posts, cleaned_users])
def enriched_posts(
    raw_posts: pd.DataFrame,
    cleaned_users: pd.DataFrame
) -> pd.DataFrame:
    """Multiple dependencies as parameters"""
    return raw_posts.merge(cleaned_users, ...)
```

**Key Differences:**
- ✅ Dagster: Natural function parameters, clean and readable
- ❌ Airflow: Multiple XCom pulls, verbose, hard to track

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
- ✅ Both handle parallel execution similarly
- ✅ Dagster shows parallelism visually in the lineage graph

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
- ✅ Dagster: Test like regular Python functions
- ❌ Airflow: Complex mocking, XCom, context, TaskInstance

## Summary Table

| Feature | Airflow | Dagster |
|---------|---------|---------|
| **Data Passing** | XCom (untyped, DB-stored) | Function parameters (type-safe) |
| **Dependencies** | `>>` operator + XCom pulls | Function parameters |
| **Type Safety** | ❌ No | ✅ Yes |
| **Testing** | ❌ Complex (mocking) | ✅ Simple (pure functions) |
| **Local Dev** | ❌ Needs Docker/DB | ✅ Just Python |
| **Lineage** | ❌ Manual | ✅ Automatic |
| **Code Style** | Imperative (how to do it) | Declarative (what to produce) |
| **Learning Curve** | Higher | Lower (for Python devs) |
| **Data-Centric** | ❌ Task-centric | ✅ Asset-centric |

## File Structure Comparison

**Airflow:**
```
dags/
├── user_posts_pipeline.py  # 200+ lines
├── sql/
│   └── queries.sql
└── config/
    └── connections.yaml
```

**Dagster:**
```
src/my_project/
├── definitions.py          # Entry point (30 lines)
├── defs/
│   ├── assets.py          # Asset definitions (150 lines)
│   └── schedules.py       # Schedules (30 lines)
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

## Key Takeaways for Airflow Users

1. **Think Data, Not Tasks**: Focus on what data you're creating, not the steps
2. **No XCom Needed**: Data passes naturally through function parameters
3. **Type Safety**: Catch errors at development time, not runtime
4. **Easy Testing**: Assets are just Python functions
5. **Better DX**: No Docker needed for local development
6. **Automatic Lineage**: Dagster tracks what creates what automatically

## When to Use Each

**Use Airflow when:**
- You have existing Airflow infrastructure
- Your team is heavily invested in Airflow
- You need very specific Airflow operators

**Use Dagster when:**
- Starting a new project
- You want better developer experience
- Type safety and testing are important
- You work with data assets (tables, models, reports)
- You want automatic lineage tracking
