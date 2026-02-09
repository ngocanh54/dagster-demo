"""
Data Marts - Definitions

This code location creates analytics-ready data marts.
These assets depend on raw data from the ingestion_pipelines code location.

This demonstrates:
1. Cross-code-location dependencies (data_marts depends on ingestion_pipelines)
2. Hand-written transformation assets (Python)
"""

from dagster import Definitions

# Import data mart assets that depend on ingestion_pipelines
from .defs import (
    user_activity_mart,
    album_engagement_mart,
)

# Define all assets for this code location
defs = Definitions(
    assets=[
        # These marts depend on raw assets from ingestion_pipelines
        user_activity_mart,
        album_engagement_mart,
    ],
)
