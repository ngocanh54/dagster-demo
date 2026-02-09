"""
Ingestion Pipelines - Definitions

This code location contains RAW DATA INGESTION only.
These assets are used downstream by the data_marts code location.

Demonstrates the factory pattern for YAML-defined ingestion pipelines with schedules.
"""

from dagster import Definitions
import os

# Import shared factory (supports both assets and schedules)
from shared.factories import build_from_yaml, build_assets_from_yaml

# Get the directory where this file lives
current_dir = os.path.dirname(__file__)

# Load sample pipeline WITH schedule (demonstrates full YAML pattern)
sample_pipeline = build_from_yaml(
    os.path.join(current_dir, "config", "sample_pipeline.yaml")
)

# Load albums pipeline WITHOUT schedule (just assets)
albums_pipeline_assets = build_assets_from_yaml(
    os.path.join(current_dir, "config", "albums_pipeline.yaml")
)

# Combine everything
defs = Definitions(
    assets=[
        # From sample_pipeline.yaml (with schedule)
        *sample_pipeline['assets'],
        # From albums_pipeline.yaml (no schedule)
        *albums_pipeline_assets,
    ],
    schedules=sample_pipeline['schedules'],  # Schedules from YAML
    jobs=sample_pipeline['jobs'],  # Jobs created for schedules
)
