"""
Database Schema Definitions
Python-based schema definitions for all databases
"""

from .timescale_schema import get_timescale_schemas
from .clickhouse_schema import get_clickhouse_schemas
from .dragonfly_schema import get_dragonfly_schemas
from .arangodb_schema import get_arangodb_schemas
from .weaviate_schema import get_weaviate_schemas

__all__ = [
    "get_timescale_schemas",
    "get_clickhouse_schemas",
    "get_dragonfly_schemas",
    "get_arangodb_schemas",
    "get_weaviate_schemas",
]
