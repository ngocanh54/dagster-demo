"""
Asset factories for dynamically creating Dagster assets and schedules from configuration.

Similar to Airflow's plugins/dagbuilder.py pattern.
"""

from .asset_builder import AssetBuilder, build_assets_from_yaml, build_from_yaml

__all__ = ["AssetBuilder", "build_assets_from_yaml", "build_from_yaml"]
