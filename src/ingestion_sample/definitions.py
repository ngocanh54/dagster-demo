"""
Main definitions file - this is the entry point for Dagster.

In Airflow, you'd have multiple DAG files in a dags/ folder.
In Dagster, you define everything in one Definitions object.
"""

from dagster import Definitions

from .defs import (
    # Assets
    raw_users,
    raw_posts,
    cleaned_users,
    enriched_posts,
    posts_analytics,
    company_analytics,
    # Schedules & Jobs
    daily_schedule,
    hourly_analytics_schedule,
    all_assets_job,
    analytics_job,
)

# This is similar to having a DAG in Airflow, but more declarative
# All your assets, jobs, schedules, sensors, and resources go here
defs = Definitions(
    assets=[
        raw_users,
        raw_posts,
        cleaned_users,
        enriched_posts,
        posts_analytics,
        company_analytics,
    ],
    jobs=[
        all_assets_job,
        analytics_job,
    ],
    schedules=[
        daily_schedule,
        hourly_analytics_schedule,
    ],
)
