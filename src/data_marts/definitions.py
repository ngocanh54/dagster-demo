"""
Data Marts - Definitions

This code location creates analytics-ready data marts.
These assets depend on raw data from the ingestion_pipelines code location.

This demonstrates:
1. Cross-code-location dependencies (data_marts depends on ingestion_pipelines)
2. SourceAssets for external dependencies
3. Hand-written transformation assets (Python)
"""

from dagster import Definitions

# Import source assets (from ingestion_pipelines) and data mart assets
from .assets import (
    # Source assets from ingestion_pipelines code location
    raw_todos_source,
    raw_comments_source,
    raw_albums_source,
    raw_photos_source,
    # Data mart transformation assets
    user_activity_mart,
    album_engagement_mart,
)

# Define all assets for this code location
defs = Definitions(
    assets=[
        # Source assets (produced by ingestion_pipelines)
        raw_todos_source,
        raw_comments_source,
        raw_albums_source,
        raw_photos_source,
        # Data marts (depend on source assets)
        user_activity_mart,
        album_engagement_mart,
    ],
)
