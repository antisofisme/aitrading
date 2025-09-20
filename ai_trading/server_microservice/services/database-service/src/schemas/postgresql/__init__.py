"""
PostgreSQL Database Schemas
User authentication, system configuration, and metadata management
"""

from .user_auth_schemas import PostgresqlUserAuthSchemas
from .ml_metadata_schemas import PostgresqlMlMetadataSchemas

# Create unified PostgreSQL schemas class
class PostgreSQLSchemas:
    """Unified PostgreSQL schemas access"""
    UserAuth = PostgresqlUserAuthSchemas
    MlMetadata = PostgresqlMlMetadataSchemas

__all__ = [
    "PostgresqlUserAuthSchemas",
    "PostgresqlMlMetadataSchemas", 
    "PostgreSQLSchemas"
]