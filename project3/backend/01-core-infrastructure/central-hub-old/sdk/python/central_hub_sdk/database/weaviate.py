"""
Weaviate Connection Manager
Vector database for ML embeddings and semantic search
"""
import weaviate
from weaviate.client import Client
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from .base import BaseConnectionManager, DatabaseStatus

logger = logging.getLogger(__name__)


class WeaviateManager(BaseConnectionManager):
    """
    Connection manager for Weaviate vector database

    Features:
    - Vector similarity search
    - Semantic search
    - ML model integration
    - Schema management
    - Batch operations
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client: Optional[Client] = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.grpc_port = config.get('grpc_port', 50051)
        self.use_grpc = config.get('use_grpc', True)

    async def connect(self) -> bool:
        """Establish connection to Weaviate"""
        try:
            logger.info(f"🔌 Connecting to Weaviate at {self.host}:{self.port}")

            # Weaviate client setup
            if self.use_grpc:
                self.client = weaviate.Client(
                    url=f"http://{self.host}:{self.port}",
                    additional_config=weaviate.Config(grpc_port_experimental=self.grpc_port)
                )
            else:
                self.client = weaviate.Client(url=f"http://{self.host}:{self.port}")

            # Test connection
            if not self.client.is_ready():
                raise ConnectionError("Weaviate is not ready")

            # Get metadata
            meta = self.client.get_meta()

            logger.info(f"✅ Weaviate connected | Version: {meta.get('version', 'unknown')}")
            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ Weaviate connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close Weaviate connection"""
        if self.client:
            # Weaviate client doesn't have explicit close method
            self.client = None
            self._is_connected = False
            logger.info("✅ Weaviate connection closed")

    async def health_check(self) -> Dict[str, Any]:
        """Check Weaviate health"""
        if not self._is_connected or not self.client:
            return {
                "status": DatabaseStatus.UNHEALTHY.value,
                "connected": False,
                "error": "Not connected"
            }

        try:
            # Check if ready
            is_ready = self.client.is_ready()

            # Get schema
            schema = self.client.schema.get()
            class_count = len(schema.get('classes', []))

            # Get meta
            meta = self.client.get_meta()

            return {
                "status": DatabaseStatus.HEALTHY.value if is_ready else DatabaseStatus.DEGRADED.value,
                "connected": True,
                "ready": is_ready,
                "classes": class_count,
                "version": meta.get('version', 'unknown')
            }

        except Exception as e:
            logger.error(f"❌ Weaviate health check failed: {e}")
            return {
                "status": DatabaseStatus.DEGRADED.value,
                "connected": True,
                "error": str(e)
            }

    async def initialize_schema(self, schema_path: str) -> bool:
        """
        Initialize Weaviate schema from JSON file

        Schema file should contain class definitions with:
        - class name
        - properties
        - vectorizer config
        """
        if not self._is_connected:
            logger.error("Cannot initialize schema: Not connected")
            return False

        try:
            import json

            schema_file = Path(schema_path)
            if not schema_file.exists():
                logger.error(f"Schema file not found: {schema_path}")
                return False

            schema = json.loads(schema_file.read_text())

            # Create classes
            for class_def in schema.get('classes', []):
                class_name = class_def['class']

                # Check if class exists
                if self.client.schema.exists(class_name):
                    logger.debug(f"Class already exists: {class_name}")
                    continue

                # Create class
                self.client.schema.create_class(class_def)
                logger.info(f"✅ Created class: {class_name}")

            logger.info(f"✅ Schema initialized from {schema_file.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False

    async def execute_query(
        self,
        query: str,
        class_name: Optional[str] = None,
        properties: Optional[List[str]] = None,
        **kwargs
    ) -> Any:
        """
        Execute Weaviate query

        This is a simplified interface. For complex queries,
        use the client directly via self.client

        Args:
            query: Search query or GraphQL query
            class_name: Target class name
            properties: Properties to return

        Returns:
            Query results
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to Weaviate")

        try:
            if class_name:
                # Semantic search
                result = (
                    self.client.query
                    .get(class_name, properties or ["*"])
                    .with_near_text({"concepts": [query]})
                    .with_limit(kwargs.get('limit', 10))
                    .do()
                )
                return result
            else:
                # Raw GraphQL query
                result = self.client.query.raw(query)
                return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    # Convenience methods

    def batch_insert(self, class_name: str, objects: List[Dict[str, Any]]) -> int:
        """Batch insert objects"""
        if not self._is_connected:
            raise ConnectionError("Not connected to Weaviate")

        try:
            with self.client.batch as batch:
                for obj in objects:
                    batch.add_data_object(
                        data_object=obj,
                        class_name=class_name
                    )

            logger.info(f"✅ Batch inserted {len(objects)} objects into {class_name}")
            return len(objects)

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise

    def semantic_search(
        self,
        class_name: str,
        query: str,
        properties: List[str],
        limit: int = 10
    ) -> List[Dict]:
        """Semantic search using vector similarity"""
        if not self._is_connected:
            raise ConnectionError("Not connected to Weaviate")

        try:
            result = (
                self.client.query
                .get(class_name, properties)
                .with_near_text({"concepts": [query]})
                .with_limit(limit)
                .with_additional(["certainty", "distance"])
                .do()
            )

            return result.get("data", {}).get("Get", {}).get(class_name, [])

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
