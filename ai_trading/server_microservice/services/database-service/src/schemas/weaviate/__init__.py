"""
Weaviate Vector Database Schemas
AI-native vector database for semantic search and ML embeddings
"""

from .vector_schemas import WeaviateVectorSchemas

# Create unified weaviate schemas class
class WeaviateSchemas:
    """Unified weaviate schemas access"""
    WeaviateVector = WeaviateVectorSchemas

__all__ = [
    "WeaviateSchemas",
   
    "WeaviateVectorSchemas"
]