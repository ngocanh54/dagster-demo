"""
Sample data pipeline assets demonstrating common patterns.

This example shows:
- API data ingestion (like PythonOperator in Airflow)
- Data transformation (like transform tasks in Airflow)
- Asset dependencies (like task dependencies in Airflow)
- Data passing between assets (like XCom in Airflow, but type-safe)
- CSV output for easy inspection
- Metadata for data preview in UI
"""

import os
import pandas as pd
import requests
from dagster import asset, AssetExecutionContext, MetadataValue, Output
from typing import Dict, List

# Output directory for CSV files
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


@asset(
    description="Fetch user data from JSONPlaceholder API (simulates API ingestion)"
)
def raw_users(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """
    Fetch raw user data from a public API.

    In Airflow, this would be a PythonOperator or HttpSensor + PythonOperator.
    In Dagster, it's just a function that returns data.
    """
    context.log.info("Fetching users from API...")

    response = requests.get("https://jsonplaceholder.typicode.com/users")
    response.raise_for_status()

    users_data = response.json()
    df = pd.DataFrame(users_data)

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "raw_users.csv")
    df.to_csv(csv_path, index=False)

    context.log.info(f"Fetched {len(df)} users")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"Sample data:\n{df.head(3)[['id', 'name', 'email']].to_string()}")

    # Return with metadata for UI preview
    return Output(
        value=df,
        metadata={
            "num_records": len(df),
            "csv_path": csv_path,
            "preview": MetadataValue.md(df.head(5).to_markdown()),
            "columns": MetadataValue.json(df.columns.tolist()),
        }
    )


@asset(
    description="Fetch posts data from JSONPlaceholder API"
)
def raw_posts(context: AssetExecutionContext) -> Output[pd.DataFrame]:
    """
    Fetch raw posts data from API.
    This runs in parallel with raw_users (no dependency).
    """
    context.log.info("Fetching posts from API...")

    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    response.raise_for_status()

    posts_data = response.json()
    df = pd.DataFrame(posts_data)

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "raw_posts.csv")
    df.to_csv(csv_path, index=False)

    context.log.info(f"Fetched {len(df)} posts")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"Sample data:\n{df.head(3)[['id', 'userId', 'title']].to_string()}")

    return Output(
        value=df,
        metadata={
            "num_records": len(df),
            "csv_path": csv_path,
            "preview": MetadataValue.md(df.head(5).to_markdown()),
        }
    )


@asset(
    description="Clean and transform user data",
    deps=[raw_users]  # This asset depends on raw_users (like task dependencies in Airflow)
)
def cleaned_users(context: AssetExecutionContext, raw_users: pd.DataFrame) -> Output[pd.DataFrame]:
    """
    Transform raw user data into cleaned format.

    Key difference from Airflow:
    - In Airflow: You'd use XCom to pass data (untyped, stored in metadata DB)
    - In Dagster: Direct parameter passing (type-safe, efficient)
    """
    context.log.info("Cleaning user data...")

    df = raw_users.copy()

    # Extract relevant fields
    df['full_name'] = df['name']
    df['username'] = df['username']
    df['email'] = df['email']
    df['company_name'] = df['company'].apply(lambda x: x['name'])
    df['city'] = df['address'].apply(lambda x: x['city'])

    # Select only needed columns
    cleaned = df[['id', 'full_name', 'username', 'email', 'company_name', 'city']]

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "cleaned_users.csv")
    cleaned.to_csv(csv_path, index=False)

    context.log.info(f"Cleaned {len(cleaned)} user records")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"Sample data:\n{cleaned.head(3).to_string()}")

    return Output(
        value=cleaned,
        metadata={
            "num_records": len(cleaned),
            "csv_path": csv_path,
            "preview": MetadataValue.md(cleaned.head(5).to_markdown()),
        }
    )


@asset(
    description="Transform posts data with user information",
    deps=[raw_posts, cleaned_users]  # Depends on BOTH posts and users
)
def enriched_posts(
    context: AssetExecutionContext,
    raw_posts: pd.DataFrame,
    cleaned_users: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Join posts with user data to create enriched dataset.

    This demonstrates multi-asset dependencies - something that would
    require multiple XCom pulls in Airflow.
    """
    context.log.info("Enriching posts with user data...")

    # Join posts with user information
    enriched = raw_posts.merge(
        cleaned_users[['id', 'full_name', 'username', 'company_name']],
        left_on='userId',
        right_on='id',
        how='left',
        suffixes=('_post', '_user')
    )

    # Rename columns for clarity
    enriched = enriched.rename(columns={
        'id_post': 'post_id',
        'id_user': 'user_id'
    })

    # Add some computed fields
    enriched['title_length'] = enriched['title'].str.len()
    enriched['body_length'] = enriched['body'].str.len()

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "enriched_posts.csv")
    enriched.to_csv(csv_path, index=False)

    context.log.info(f"Created {len(enriched)} enriched post records")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"Sample data:\n{enriched.head(3)[['post_id', 'username', 'title']].to_string()}")

    return Output(
        value=enriched,
        metadata={
            "num_records": len(enriched),
            "csv_path": csv_path,
            "preview": MetadataValue.md(enriched.head(5)[['post_id', 'username', 'title', 'title_length']].to_markdown()),
        }
    )


@asset(
    description="Generate analytics on posts by user and company"
)
def posts_analytics(
    context: AssetExecutionContext,
    enriched_posts: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Create aggregated analytics from enriched posts.

    This is the final output asset - like a final task in an Airflow DAG
    that writes to a dashboard or data warehouse.
    """
    context.log.info("Generating post analytics...")

    analytics = enriched_posts.groupby(['user_id', 'username', 'company_name']).agg({
        'post_id': 'count',
        'title_length': 'mean',
        'body_length': 'mean'
    }).reset_index()

    analytics.columns = [
        'user_id',
        'username',
        'company_name',
        'total_posts',
        'avg_title_length',
        'avg_body_length'
    ]

    # Sort by most active users
    analytics = analytics.sort_values('total_posts', ascending=False)

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "posts_analytics.csv")
    analytics.to_csv(csv_path, index=False)

    context.log.info(f"Generated analytics for {len(analytics)} users")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"Top poster: {analytics.iloc[0]['username']} with {analytics.iloc[0]['total_posts']} posts")
    context.log.info(f"\nTop 5 users:\n{analytics.head(5).to_string()}")

    return Output(
        value=analytics,
        metadata={
            "num_records": len(analytics),
            "csv_path": csv_path,
            "top_poster": analytics.iloc[0]['username'],
            "top_posts_count": int(analytics.iloc[0]['total_posts']),
            "preview": MetadataValue.md(analytics.head(10).to_markdown()),
        }
    )


@asset(
    description="Company-level aggregated statistics"
)
def company_analytics(
    context: AssetExecutionContext,
    enriched_posts: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Aggregate statistics at company level.
    """
    context.log.info("Generating company analytics...")

    company_stats = enriched_posts.groupby('company_name').agg({
        'post_id': 'count',
        'userId': 'nunique',
        'title_length': 'mean',
        'body_length': 'mean'
    }).reset_index()

    company_stats.columns = [
        'company_name',
        'total_posts',
        'unique_users',
        'avg_title_length',
        'avg_body_length'
    ]

    company_stats = company_stats.sort_values('total_posts', ascending=False)

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "company_analytics.csv")
    company_stats.to_csv(csv_path, index=False)

    context.log.info(f"Generated analytics for {len(company_stats)} companies")
    context.log.info(f"Saved to: {csv_path}")
    context.log.info(f"\nTop companies:\n{company_stats.head(5).to_string()}")

    return Output(
        value=company_stats,
        metadata={
            "num_records": len(company_stats),
            "csv_path": csv_path,
            "preview": MetadataValue.md(company_stats.to_markdown()),
        }
    )
