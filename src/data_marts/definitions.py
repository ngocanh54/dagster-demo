"""
Data Marts - Definitions

This code location creates analytics-ready data marts.
These assets depend on raw data from the ingestion_pipelines code location.

This demonstrates:
1. Cross-code-location dependencies using SourceAssets (YAML-based)
2. Factory pattern for data mart transformations
3. Consistent YAML approach across all code locations
"""

from dagster import Definitions
import os

# Import shared factory
from shared.factories import build_from_yaml

# Get the directory where this file lives
current_dir = os.path.dirname(__file__)

# Load data marts from YAML (includes sources + transformations)
marts = build_from_yaml(
    os.path.join(current_dir, "config", "marts.yaml")
)

# Define all assets for this code location
defs = Definitions(
    assets=marts['assets'],  # Includes both source assets and mart assets
    schedules=marts['schedules'],
    jobs=marts['jobs'],
)
