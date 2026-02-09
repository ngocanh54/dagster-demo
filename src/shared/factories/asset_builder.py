"""
Asset Builder - Dagster equivalent of Airflow's DAGBuilder pattern.

This module provides a factory for dynamically creating Dagster assets and schedules from YAML,
similar to how Airflow's plugins/dagbuilder.py creates DAGs from config files.

Example YAML structure:
    # Optional: Declare external assets from other code locations
    sources:
      - raw_data_from_other_location
      - another_external_asset

    # Define assets in this pipeline
    assets:
      raw_data:
        type: api_fetch
        url: https://api.example.com/data
        description: Fetch raw data from API

      processed_data:
        type: transform
        depends_on:
          - raw_data
        description: Transform raw data

    # Optional: Define schedules
    schedules:
      - name: daily_refresh
        cron: "0 2 * * *"
        asset_selection: "*"  # All assets, or list specific ones
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
    AssetIn,
    AssetSelection,
    Output,
    MetadataValue,
    ScheduleDefinition,
    SourceAsset,
    define_asset_job,
)


class AssetBuilder:
    """
    Factory class for building Dagster assets from configuration.

    Similar to Airflow's DagBuilder pattern where you define entire pipelines in YAML.
    """

    def __init__(self, config_path: str, output_dir: str = "output", group_name: Optional[str] = None):
        """
        Initialize the AssetBuilder.

        Args:
            config_path: Path to YAML configuration file
            output_dir: Directory for output files (default: output/)
            group_name: Optional group name for organizing assets (default: derived from filename)
        """
        self.config_path = config_path
        self.output_dir = output_dir

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Derive group name from config filename if not provided
        if group_name is None:
            filename = Path(config_path).stem  # e.g., "sample_pipeline" from "sample_pipeline.yaml"
            self.group_name = filename
        else:
            self.group_name = group_name

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def _create_api_fetch_asset(self, asset_name: str, asset_config: Dict[str, Any]):
        """Create an asset that fetches data from an API."""
        url = asset_config['url']
        description = asset_config.get('description', f'Fetch data from {url}')

        @asset(name=asset_name, description=description, group_name=self.group_name)
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

        if dependencies:
            # Asset has dependencies - explicitly declare them with ins parameter
            dep_names = [dep.key.path[0] for dep in dependencies]

            # Create ins mapping for explicit dependency declaration
            ins = {name: AssetIn(key=name) for name in dep_names}

            @asset(name=asset_name, description=description, ins=ins, group_name=self.group_name)
            def transform_asset(context: AssetExecutionContext, **kwargs) -> Output[pd.DataFrame]:
                context.log.info(f"Transforming data for {asset_name}")

                # Get upstream data from named parameters
                upstream_dfs = list(kwargs.values())

                # If SQL file provided, execute it (simplified - just demonstrate pattern)
                if sql_file:
                    context.log.info(f"Would execute SQL from {sql_file}")
                    # In real implementation, you'd execute the SQL here
                    # For demo, just merge upstream data
                    df = pd.concat(upstream_dfs, ignore_index=True)
                else:
                    # Simple merge of upstream dataframes
                    df = pd.concat(upstream_dfs, ignore_index=True)

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

            return transform_asset
        else:
            # No dependencies
            @asset(name=asset_name, description=description, group_name=self.group_name)
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

    def build_source_assets(self) -> List[SourceAsset]:
        """
        Build source assets from the 'sources' section in YAML.

        Sources are external assets from other code locations.

        Returns:
            List of SourceAsset definitions
        """
        sources_config = self.config.get('sources', [])
        source_assets = []

        for source_name in sources_config:
            source_asset = SourceAsset(key=source_name)
            source_assets.append(source_asset)

        return source_assets

    def build_assets(self) -> List[Any]:
        """
        Build all assets defined in the YAML configuration.

        Returns:
            List of asset definitions
        """
        assets_config = self.config.get('assets', {})
        built_assets = {}
        asset_list = []

        # Include source assets in the lookup so dependencies can reference them
        source_assets = self.build_source_assets()
        for source_asset in source_assets:
            # SourceAssets don't have a 'key' attribute directly accessible,
            # but we can get it from the asset key
            source_key = source_asset.key.path[0] if hasattr(source_asset.key, 'path') else str(source_asset.key)
            built_assets[source_key] = source_asset

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

    def build_schedules(self, assets: List[Any]) -> List[ScheduleDefinition]:
        """
        Build schedules from YAML configuration.

        Similar to how Airflow defines schedules in DAG config:
            schedule: "0 2 * * *"

        Args:
            assets: List of assets to schedule

        Returns:
            List of schedule definitions
        """
        schedules_config = self.config.get('schedules', [])
        schedules = []

        for schedule_config in schedules_config:
            schedule_name = schedule_config.get('name')
            cron_schedule = schedule_config.get('cron')
            asset_selection = schedule_config.get('asset_selection', '*')  # "*" means all assets

            # Create job for the assets
            if asset_selection == '*':
                selection = AssetSelection.all()
            else:
                # Select specific assets
                selection = AssetSelection.assets(*[a for a in assets if a.key.path[0] in asset_selection])

            job = define_asset_job(
                name=f"{schedule_name}_job",
                selection=selection,
            )

            schedule = ScheduleDefinition(
                name=schedule_name,
                job=job,
                cron_schedule=cron_schedule,
            )

            schedules.append(schedule)

        return schedules

    def build_all(self) -> Dict[str, Any]:
        """
        Build source assets, assets, and schedules from YAML.

        Returns:
            Dictionary with 'assets', 'schedules', and 'jobs' keys
        """
        source_assets = self.build_source_assets()
        assets = self.build_assets()

        # Combine source assets and regular assets
        all_assets = source_assets + assets

        # Build schedules (only for non-source assets)
        schedules = self.build_schedules(assets)

        # Extract jobs from schedules
        jobs = [schedule.job for schedule in schedules] if schedules else []

        return {
            'assets': all_assets,
            'schedules': schedules,
            'jobs': jobs,
        }


def build_assets_from_yaml(yaml_path: str, output_dir: str = "output") -> List[Any]:
    """
    Convenience function to build assets from a YAML file.

    Usage:
        # In your definitions.py
        from shared.factories import build_assets_from_yaml

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


def build_from_yaml(yaml_path: str, output_dir: str = "output") -> Dict[str, Any]:
    """
    Build both assets and schedules from a YAML file.

    Similar to Airflow's DagBuilder which creates DAG + schedule from config.

    Usage:
        # In your definitions.py
        from shared.factories import build_from_yaml

        pipeline = build_from_yaml("config/pipeline.yaml")

        defs = Definitions(
            assets=pipeline['assets'],
            schedules=pipeline['schedules'],
            jobs=pipeline['jobs'],
        )

    Args:
        yaml_path: Path to YAML configuration file
        output_dir: Directory for output files

    Returns:
        Dictionary with 'assets', 'schedules', and 'jobs'
    """
    builder = AssetBuilder(yaml_path, output_dir)
    return builder.build_all()
