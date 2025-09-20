"""
DragonflyDB Cache Schemas
High-performance in-memory data store for caching and real-time processing
"""

from .cache_schemas import DragonflyDbCacheSchemas

# Create unified dragonflydb schemas class
class DragonflyDBSchemas:
    """Unified dragonflydb schemas access"""
    DragonflyDbCache = DragonflyDbCacheSchemas

__all__ = [
    "DragonflyDBSchemas",
    "DragonflyDbCacheSchemas"
]