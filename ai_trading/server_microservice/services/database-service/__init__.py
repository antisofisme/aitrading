"""
Database Service - Multi-database management
Unified interface for PostgreSQL, ClickHouse, ArangoDB, Redis, and Vector DBs
"""
__version__ = "2.0.0"
__service_type__ = "database-service"

from .src import api, business, infrastructure, schemas

__all__ = ['api', 'business', 'infrastructure', 'schemas']

__supported_databases__ = [
    'postgresql',
    'clickhouse', 
    'arangodb',
    'dragonflydb',
    'weaviate',
    'redpanda'
]