"""
Schedules for running assets periodically.

In Airflow, you'd use schedule_interval in the DAG definition.
In Dagster, you create Schedule objects and attach them to jobs.
"""

from dagster import (
    AssetSelection,
    ScheduleDefinition,
    define_asset_job,
)

# Define a job that materializes all assets
# This is like defining a DAG in Airflow
all_assets_job = define_asset_job(
    name="daily_pipeline_job",
    selection=AssetSelection.all(),
    description="Run the complete data pipeline"
)

# Define a schedule to run daily at 2 AM
# In Airflow: schedule_interval="0 2 * * *"
# In Dagster: cron_schedule="0 2 * * *"
daily_schedule = ScheduleDefinition(
    name="daily_pipeline_schedule",
    job=all_assets_job,
    cron_schedule="0 2 * * *",  # Every day at 2 AM
    description="Run the pipeline daily at 2 AM UTC"
)

# You can also create schedules for specific asset groups
analytics_job = define_asset_job(
    name="analytics_only_job",
    selection=AssetSelection.assets("posts_analytics", "company_analytics"),
    description="Run only analytics assets"
)

hourly_analytics_schedule = ScheduleDefinition(
    name="hourly_analytics_schedule",
    job=analytics_job,
    cron_schedule="0 * * * *",  # Every hour
    description="Update analytics every hour"
)
