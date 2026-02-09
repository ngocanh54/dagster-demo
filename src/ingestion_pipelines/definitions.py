"""
Ingestion Pipelines - Definitions

This code location contains RAW DATA INGESTION only.
These assets are used downstream by the data_marts code location.

Demonstrates the factory pattern for YAML-defined ingestion pipelines with schedules.
"""

from dagster import Definitions
import os

# Import shared factory (supports both assets and schedules)
from shared.factories import build_from_yaml

# Get the directory where this file lives
current_dir = os.path.dirname(__file__)

# Load all pipelines with schedules
sample_pipeline = build_from_yaml(
    os.path.join(current_dir, "config", "sample_pipeline.yaml")
)

albums_pipeline = build_from_yaml(
    os.path.join(current_dir, "config", "albums_pipeline.yaml")
)

# Combine everything from all pipelines
defs = Definitions(
    assets=[
        *sample_pipeline['assets'],
        *albums_pipeline['assets'],
    ],
    schedules=[
        *sample_pipeline['schedules'],
        *albums_pipeline['schedules'],
    ],
    jobs=[
        *sample_pipeline['jobs'],
        *albums_pipeline['jobs'],
    ],
)
