"""
ArangoDB Database Schemas
Multi-model database schemas for relationships and configuration
"""

from .trading_strategies_schemas import ArangodbTradingStrategiesSchemas

# Create unified arangodb schemas class
class ArangoDBSchemas:
    """Unified arangodb schemas access"""
    ArangodbTradingStrategies = ArangodbTradingStrategiesSchemas

__all__ = [
    "ArangoDBSchemas",
   
    "ArangoDBTradingStrategiesSchemas"
]