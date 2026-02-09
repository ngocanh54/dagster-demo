from dagster import Definitions, asset

from .defs import *


@asset
def sample_asset():
    """
    A sample asset that returns a simple value.
    """
    return "Hello, Dagster!"


defs = Definitions(
    assets=[sample_asset],
)
