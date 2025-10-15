"""
ArangoDB Connection Manager
Multi-model database (graph, document, key-value)
"""
from arango import ArangoClient
from arango.database import StandardDatabase
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from .base import BaseConnectionManager, DatabaseStatus

logger = logging.getLogger(__name__)


class ArangoDBManager(BaseConnectionManager):
    """
    Connection manager for ArangoDB

    Features:
    - Graph database operations
    - Document collections
    - AQL query execution
    - Graph traversal
    - Schema-less flexibility
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client: Optional[ArangoClient] = None
        self.db: Optional[StandardDatabase] = None
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8529)
        self.database = config.get('database', '_system')
        self.username = config.get('username', 'root')
        self.password = config.get('password', '')

    async def connect(self) -> bool:
        """Establish connection to ArangoDB"""
        try:
            logger.info(f"🔌 Connecting to ArangoDB at {self.host}:{self.port}/{self.database}")

            # ArangoDB client is synchronous, but fast enough for our use
            self.client = ArangoClient(hosts=f"http://{self.host}:{self.port}")

            # Connect to system database first
            sys_db = self.client.db('_system', username=self.username, password=self.password)

            # Check if target database exists, create if not
            if not sys_db.has_database(self.database):
                sys_db.create_database(self.database)
                logger.info(f"✅ Created database: {self.database}")

            # Connect to target database
            self.db = self.client.db(self.database, username=self.username, password=self.password)

            # Get version info
            version_info = self.db.version()

            logger.info(f"✅ ArangoDB connected | Version: {version_info}")
            self._is_connected = True
            return True

        except Exception as e:
            logger.error(f"❌ ArangoDB connection failed: {e}")
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close ArangoDB connection"""
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            self._is_connected = False
            logger.info("✅ ArangoDB connection closed")

    async def health_check(self) -> Dict[str, Any]:
        """Check ArangoDB health"""
        if not self._is_connected or not self.db:
            return {
                "status": DatabaseStatus.UNHEALTHY.value,
                "connected": False,
                "error": "Not connected"
            }

        try:
            # Get database properties
            props = self.db.properties()

            # Get collection count
            collections = self.db.collections()
            coll_count = len([c for c in collections if not c['name'].startswith('_')])

            return {
                "status": DatabaseStatus.HEALTHY.value,
                "connected": True,
                "collections": coll_count,
                "database": props.get('name'),
                "is_system": props.get('is_system', False)
            }

        except Exception as e:
            logger.error(f"❌ ArangoDB health check failed: {e}")
            return {
                "status": DatabaseStatus.DEGRADED.value,
                "connected": True,
                "error": str(e)
            }

    async def initialize_schema(self, schema_path: str) -> bool:
        """
        Initialize collections and graphs from schema file

        Schema file should be JSON with format:
        {
            "collections": ["collection1", "collection2"],
            "graphs": [{"name": "graph1", "edge_definitions": [...]}]
        }
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

            # Create collections
            for coll_name in schema.get('collections', []):
                if not self.db.has_collection(coll_name):
                    self.db.create_collection(coll_name)
                    logger.info(f"✅ Created collection: {coll_name}")

            # Create graphs
            for graph_def in schema.get('graphs', []):
                graph_name = graph_def['name']
                if not self.db.has_graph(graph_name):
                    self.db.create_graph(
                        graph_name,
                        edge_definitions=graph_def.get('edge_definitions', [])
                    )
                    logger.info(f"✅ Created graph: {graph_name}")

            logger.info(f"✅ Schema initialized from {schema_file.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False

    async def execute_query(self, query: str, bind_vars: Optional[Dict] = None, **kwargs) -> Any:
        """
        Execute AQL query

        Args:
            query: AQL query string
            bind_vars: Query bind variables

        Returns:
            Query cursor/results
        """
        if not self._is_connected:
            raise ConnectionError("Not connected to ArangoDB")

        try:
            cursor = self.db.aql.execute(
                query,
                bind_vars=bind_vars,
                count=kwargs.get('count', False),
                batch_size=kwargs.get('batch_size', 1000)
            )

            if kwargs.get('fetch_all', True):
                return list(cursor)
            else:
                return cursor

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    # Convenience methods

    def get_collection(self, name: str):
        """Get or create collection"""
        if not self.db.has_collection(name):
            return self.db.create_collection(name)
        return self.db.collection(name)

    def get_graph(self, name: str):
        """Get graph"""
        if self.db.has_graph(name):
            return self.db.graph(name)
        return None
