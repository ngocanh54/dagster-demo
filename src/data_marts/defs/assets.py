"""
Data Mart Assets

These assets transform raw ingested data into analytics-ready data marts.
They depend on assets from the ingestion_pipelines code location.

NOTE: Cross-code-location dependencies require declaring source assets.
"""

import os
import pandas as pd
from dagster import (
    asset,
    AssetExecutionContext,
    AssetIn,
    Output,
    MetadataValue,
    SourceAsset,
)

# Output directory
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Declare external assets from ingestion_pipelines code location
# These are produced by ingestion_pipelines and consumed here
raw_todos_source = SourceAsset(key="raw_todos")
raw_comments_source = SourceAsset(key="raw_comments")
raw_albums_source = SourceAsset(key="raw_albums")
raw_photos_source = SourceAsset(key="raw_photos")


@asset(
    description="User analytics mart - aggregates user and post data",
    # Depends on raw_todos and raw_comments from ingestion_pipelines
    ins={
        "raw_todos": AssetIn(key="raw_todos"),
        "raw_comments": AssetIn(key="raw_comments"),
    }
)
def user_activity_mart(
    context: AssetExecutionContext,
    raw_todos: pd.DataFrame,
    raw_comments: pd.DataFrame,
) -> Output[pd.DataFrame]:
    """
    Creates a user activity mart by combining todos and comments.

    This demonstrates cross-code-location dependencies:
    - raw_todos comes from ingestion_pipelines/sample_pipeline.yaml
    - raw_comments comes from ingestion_pipelines/sample_pipeline.yaml
    - This mart lives in data_marts code location
    """
    context.log.info(f"Building user activity mart from {len(raw_todos)} todos and {len(raw_comments)} comments")

    # Aggregate todos by user
    todos_by_user = raw_todos.groupby('userId').agg({
        'id': 'count',
        'completed': 'sum'
    }).rename(columns={'id': 'total_todos', 'completed': 'completed_todos'})

    # Aggregate comments by post (using postId as a proxy for user activity)
    comments_by_post = raw_comments.groupby('postId').agg({
        'id': 'count',
        'email': 'nunique'
    }).rename(columns={'id': 'total_comments', 'email': 'unique_commenters'})

    # For demo: just combine the first few rows
    # In reality, you'd join on proper user IDs
    user_activity = pd.DataFrame({
        'user_id': range(1, min(len(todos_by_user), len(comments_by_post)) + 1),
        'total_todos': todos_by_user['total_todos'].values[:min(len(todos_by_user), len(comments_by_post))],
        'completed_todos': todos_by_user['completed_todos'].values[:min(len(todos_by_user), len(comments_by_post))],
        'engagement_score': (
            todos_by_user['completed_todos'].values[:min(len(todos_by_user), len(comments_by_post))] /
            todos_by_user['total_todos'].values[:min(len(todos_by_user), len(comments_by_post))] * 100
        ).round(2)
    })

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "user_activity_mart.csv")
    user_activity.to_csv(csv_path, index=False)
    context.log.info(f"Saved mart to {csv_path}")

    return Output(
        value=user_activity,
        metadata={
            "num_users": len(user_activity),
            "avg_engagement": user_activity['engagement_score'].mean(),
            "csv_path": csv_path,
            "preview": MetadataValue.md(user_activity.head(10).to_markdown(index=False)),
        }
    )


@asset(
    description="Album engagement mart - analyzes album and photo data",
    ins={
        "raw_albums": AssetIn(key="raw_albums"),
        "raw_photos": AssetIn(key="raw_photos"),
    }
)
def album_engagement_mart(
    context: AssetExecutionContext,
    raw_albums: pd.DataFrame,
    raw_photos: pd.DataFrame,
) -> Output[pd.DataFrame]:
    """
    Creates an album engagement mart.

    Depends on:
    - raw_albums from ingestion_pipelines/albums_pipeline.yaml
    - raw_photos from ingestion_pipelines/albums_pipeline.yaml
    """
    context.log.info(f"Building album engagement mart from {len(raw_albums)} albums and {len(raw_photos)} photos")

    # Count photos per album
    photos_per_album = raw_photos.groupby('albumId').size().reset_index(name='photo_count')

    # Join with albums
    album_engagement = raw_albums.merge(photos_per_album, left_on='id', right_on='albumId', how='left')
    album_engagement['photo_count'] = album_engagement['photo_count'].fillna(0).astype(int)

    # Create engagement metrics
    album_stats = album_engagement.groupby('userId').agg({
        'id': 'count',
        'photo_count': ['sum', 'mean']
    }).reset_index()

    album_stats.columns = ['user_id', 'total_albums', 'total_photos', 'avg_photos_per_album']
    album_stats['avg_photos_per_album'] = album_stats['avg_photos_per_album'].round(2)

    # Save to CSV
    csv_path = os.path.join(OUTPUT_DIR, "album_engagement_mart.csv")
    album_stats.to_csv(csv_path, index=False)
    context.log.info(f"Saved mart to {csv_path}")

    return Output(
        value=album_stats,
        metadata={
            "num_users": len(album_stats),
            "total_photos": int(album_stats['total_photos'].sum()),
            "avg_photos_per_user": album_stats['total_photos'].mean(),
            "csv_path": csv_path,
            "preview": MetadataValue.md(album_stats.head(10).to_markdown(index=False)),
        }
    )
