"""
Asset Builder - Dagster equivalent of Airflow's DAGBuilder pattern.

This module provides a factory for dynamically creating Dagster assets from YAML configuration,
similar to how Airflow's plugins/dagbuilder.py creates DAGs from config files.

Example YAML structure:
    assets:
      raw_data:
        type: api_fetch
        url: https://api.example.com/data
        description: Fetch raw data from API

      processed_data:
        type: transform
        sql_file: queries/transform.sql
        depends_on:
          - raw_data
        description: Transform raw data
"""

import os
import yaml
import pandas as pd
import requests
from typing import Any, Dict, List, Optional
from pathlib import Path

from dagster import (
    asset,
    AssetExecutionContext,
    Output,
    MetadataValue,
)


class AssetBuilder:
    """
    Factory class for building Dagster assets from configuration.

    Similar to Airflow's DagBuilder pattern where you define entire pipelines in YAML.
    """

    def __init__(self, config_path: str, output_dir: str = "output"):
        """
        Initialize the AssetBuilder.

        Args:
            config_path: Path to YAML configuration file
            output_dir: Directory for output files (default: output/)
        """
        self.config_path = config_path
        self.output_dir = output_dir

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _create_api_fetch_asset(self, asset_name: str, asset_config: Dict[str, Any]):
        """Create an asset that fetches data from an API."""
        url = asset_config['url']
        description = asset_config.get('description', f'Fetch data from {url}')

        @asset(name=asset_name, description=description)
        def api_fetch_asset(context: AssetExecutionContext) -> Output[pd.DataFrame]:
            context.log.info(f"Fetching data from {url}")
            response = requests.get(url)
            response.raise_for_status()

            data = response.json()
            df = pd.DataFrame(data)

            # Save to CSV
            csv_path = os.path.join(self.output_dir, f"{asset_name}.csv")
            df.to_csv(csv_path, index=False)

            return Output(
                value=df,
                metadata={
                    "num_records": len(df),
                    "num_columns": len(df.columns),
                    "csv_path": csv_path,
                    "preview": MetadataValue.md(df.head(5).to_markdown()),
                }
            )

        return api_fetch_asset

    def _create_sql_transform_asset(
        self,
        asset_name: str,
        asset_config: Dict[str, Any],
        dependencies: List[Any]
    ):
        """Create an asset that transforms data using SQL or Python."""
        description = asset_config.get('description', f'Transform data for {asset_name}')
        sql_file = asset_config.get('sql_file')

        # Build function signature dynamically based on dependencies
        def make_transform_asset():
            if dependencies:
                # Asset has dependencies - add them as parameters
                dep_names = [dep.key.path[0] for dep in dependencies]

                @asset(name=asset_name, description=description)
                def transform_asset(context: AssetExecutionContext, **kwargs) -> Output[pd.DataFrame]:
                    context.log.info(f"Transforming data for {asset_name}")

                    # Get upstream data
                    upstream_dfs = {name: kwargs[name] for name in dep_names}

                    # If SQL file provided, execute it (simplified - just demonstrate pattern)
                    if sql_file:
                        context.log.info(f"Would execute SQL from {sql_file}")
                        # In real implementation, you'd execute the SQL here
                        # For demo, just merge upstream data
                        df = pd.concat(upstream_dfs.values(), ignore_index=True)
                    else:
                        # Simple merge of upstream dataframes
                        df = pd.concat(upstream_dfs.values(), ignore_index=True)

                    # Save to CSV
                    csv_path = os.path.join(self.output_dir, f"{asset_name}.csv")
                    df.to_csv(csv_path, index=False)

                    return Output(
                        value=df,
                        metadata={
                            "num_records": len(df),
                            "csv_path": csv_path,
                            "preview": MetadataValue.md(df.head(5).to_markdown()),
                        }
                    )

                # Manually set dependencies by modifying the asset's input definitions
                # This is a simplified version - in production you'd use deps parameter
                return transform_asset
            else:
                # No dependencies
                @asset(name=asset_name, description=description)
                def transform_asset(context: AssetExecutionContext) -> Output[pd.DataFrame]:
                    context.log.info(f"Transforming data for {asset_name}")

                    # Create empty dataframe
                    df = pd.DataFrame()

                    csv_path = os.path.join(self.output_dir, f"{asset_name}.csv")
                    df.to_csv(csv_path, index=False)

                    return Output(
                        value=df,
                        metadata={
                            "num_records": len(df),
                            "csv_path": csv_path,
                        }
                    )

                return transform_asset

        return make_transform_asset()

    def build_assets(self) -> List[Any]:
        """
        Build all assets defined in the YAML configuration.

        Returns:
            List of asset definitions
        """
        assets_config = self.config.get('assets', {})
        built_assets = {}
        asset_list = []

        # First pass: Create all assets
        for asset_name, asset_config in assets_config.items():
            asset_type = asset_config.get('type', 'transform')

            if asset_type == 'api_fetch':
                asset_def = self._create_api_fetch_asset(asset_name, asset_config)
                built_assets[asset_name] = asset_def
                asset_list.append(asset_def)

            elif asset_type == 'transform':
                # Get dependencies
                depends_on = asset_config.get('depends_on', [])
                dependencies = [built_assets[dep] for dep in depends_on if dep in built_assets]

                asset_def = self._create_sql_transform_asset(
                    asset_name,
                    asset_config,
                    dependencies
                )
                built_assets[asset_name] = asset_def
                asset_list.append(asset_def)

        return asset_list


def build_assets_from_yaml(yaml_path: str, output_dir: str = "output") -> List[Any]:
    """
    Convenience function to build assets from a YAML file.

    Usage:
        # In your definitions.py
        from ingestion_sample.factories import build_assets_from_yaml

        config_assets = build_assets_from_yaml("config/pipeline.yaml")

        defs = Definitions(
            assets=config_assets,
        )

    Args:
        yaml_path: Path to YAML configuration file
        output_dir: Directory for output files

    Returns:
        List of asset definitions
    """
    builder = AssetBuilder(yaml_path, output_dir)
    return builder.build_assets()
