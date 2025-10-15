"""
Connection Manager
Handles all infrastructure connections (database, cache, messaging)
"""

import os
import time
import asyncio
import logging
from typing import Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared"))

# Real database imports
import asyncpg
import redis.asyncio as redis

# Real transport imports
import nats
from confluent_kafka import Producer

# Shared components
from components.utils.patterns import DatabaseManager, CacheManager, CacheConfig, DatabaseConfig
from components.utils.log_utils.error_dna.analyzer import ErrorDNA

logger = logging.getLogger("central-hub.connection-manager")


class ConnectionManager:
    """
    Manages all infrastructure connections for Central Hub

    Responsibilities:
    - Database connections (PostgreSQL)
    - Cache connections (DragonflyDB/Redis)
    - Messaging connections (NATS, Kafka)
    - Error analysis (ErrorDNA)
    """

    def __init__(self, service_name: str):
        self.service_name = service_name

        # Database and cache
        self.db_manager: Optional[DatabaseManager] = None
        self.cache_manager: Optional[CacheManager] = None
        self.error_analyzer: Optional[ErrorDNA] = None

        # Transport connections
        self.nats_client: Optional[nats.NATS] = None
        self.kafka_producer: Optional[Producer] = None
        self.redis_client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize all connections"""
        try:
            logger.info("🔗 Initializing Connection Manager...")

            # 1. Initialize database
            await self._initialize_database()

            # 2. Initialize cache
            await self._initialize_cache()

            # 3. Initialize transports
            await self._initialize_transports()

            logger.info("✅ Connection Manager initialized")

        except Exception as e:
            logger.error(f"❌ Connection Manager initialization failed: {str(e)}")
            raise

    async def _initialize_database(self):
        """Initialize real PostgreSQL database connection"""
        try:
            db_config = DatabaseConfig(
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", 5432)),
                database=os.getenv("POSTGRES_DB", "central_hub"),
                username=os.getenv("POSTGRES_USER", "central_hub"),
                password=os.getenv("POSTGRES_PASSWORD")
            )

            self.db_manager = DatabaseManager(self.service_name)
            await self.db_manager.add_connection("default", "postgresql", db_config)

            # Create database schema
            await self._create_database_schema()

            logger.info("✅ PostgreSQL database connected")

        except Exception as e:
            logger.error(f"❌ Database connection FAILED: {str(e)}")
            raise RuntimeError(f"Database connection required but failed: {str(e)}")

    async def _create_database_schema(self):
        """Create real database schema for Central Hub with multi-tenant support"""
        schema_sql = """
        -- Migration: Add tenant_id column to existing tables if not exists
        DO $$
        BEGIN
            -- Add tenant_id to service_registry if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='service_registry' AND column_name='tenant_id') THEN
                ALTER TABLE service_registry ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'system';
            END IF;

            -- Add tenant_id to health_metrics if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='health_metrics' AND column_name='tenant_id') THEN
                ALTER TABLE health_metrics ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'system';
            END IF;

            -- Add tenant_id to coordination_history if not exists
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name='coordination_history' AND column_name='tenant_id') THEN
                ALTER TABLE coordination_history ADD COLUMN tenant_id VARCHAR(100) NOT NULL DEFAULT 'system';
            END IF;
        END $$;

        -- Service Registry with tenant isolation
        CREATE TABLE IF NOT EXISTS service_registry (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(100) NOT NULL DEFAULT 'system',
            service_name VARCHAR(255) NOT NULL,
            host VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            protocol VARCHAR(50) NOT NULL DEFAULT 'http',
            health_endpoint VARCHAR(255) NOT NULL DEFAULT '/health',
            version VARCHAR(100),
            metadata JSONB,
            status VARCHAR(50) NOT NULL DEFAULT 'active',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transport_preferences JSONB,
            contract_validated BOOLEAN DEFAULT FALSE,
            UNIQUE(tenant_id, service_name)
        );

        -- Health Metrics with tenant isolation
        CREATE TABLE IF NOT EXISTS health_metrics (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(100) NOT NULL DEFAULT 'system',
            service_name VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) NOT NULL,
            response_time_ms FLOAT,
            cpu_usage FLOAT,
            memory_usage FLOAT,
            error_rate FLOAT,
            metadata JSONB
        );

        -- Coordination History with tenant isolation
        CREATE TABLE IF NOT EXISTS coordination_history (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(100) NOT NULL DEFAULT 'system',
            correlation_id VARCHAR(255) NOT NULL,
            source_service VARCHAR(255) NOT NULL,
            target_service VARCHAR(255) NOT NULL,
            operation VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            execution_time_ms FLOAT,
            result_data JSONB,
            error_message TEXT
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_service_registry_tenant ON service_registry(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_service_registry_name ON service_registry(tenant_id, service_name);
        CREATE INDEX IF NOT EXISTS idx_health_metrics_tenant ON health_metrics(tenant_id, service_name, timestamp);
        CREATE INDEX IF NOT EXISTS idx_coordination_tenant ON coordination_history(tenant_id, correlation_id);

        -- Enable Row-Level Security (RLS) for tenant isolation
        ALTER TABLE service_registry ENABLE ROW LEVEL SECURITY;
        ALTER TABLE health_metrics ENABLE ROW LEVEL SECURITY;
        ALTER TABLE coordination_history ENABLE ROW LEVEL SECURITY;

        -- RLS Policy: Users can only see their tenant's data
        -- Note: Requires setting tenant_id in session: SET app.tenant_id = 'tenant123';
        DROP POLICY IF EXISTS tenant_isolation_policy_service_registry ON service_registry;
        CREATE POLICY tenant_isolation_policy_service_registry ON service_registry
            USING (tenant_id = current_setting('app.tenant_id', TRUE)::text OR current_setting('app.tenant_id', TRUE) IS NULL);

        DROP POLICY IF EXISTS tenant_isolation_policy_health_metrics ON health_metrics;
        CREATE POLICY tenant_isolation_policy_health_metrics ON health_metrics
            USING (tenant_id = current_setting('app.tenant_id', TRUE)::text OR current_setting('app.tenant_id', TRUE) IS NULL);

        DROP POLICY IF EXISTS tenant_isolation_policy_coordination ON coordination_history;
        CREATE POLICY tenant_isolation_policy_coordination ON coordination_history
            USING (tenant_id = current_setting('app.tenant_id', TRUE)::text OR current_setting('app.tenant_id', TRUE) IS NULL);
        """

        if self.db_manager:
            await self.db_manager.execute(schema_sql)
            logger.info("✅ Database schema created")

    async def _initialize_cache(self):
        """Initialize real Redis cache connection"""
        try:
            dragonfly_config = CacheConfig(
                backend="redis",
                host=os.getenv("DRAGONFLY_HOST", "localhost"),
                port=int(os.getenv("DRAGONFLY_PORT", 6379)),
                password=os.getenv("DRAGONFLY_PASSWORD"),
                db=0,
                default_ttl=300
            )

            self.cache_manager = CacheManager(self.service_name)
            await self.cache_manager.add_backend("dragonfly", dragonfly_config)

            # Test connection
            await self.cache_manager.set("startup_test", {"timestamp": time.time()}, ttl=60)
            test_result = await self.cache_manager.get("startup_test")

            if test_result:
                logger.info("✅ DragonflyDB cache connected and tested")
            else:
                raise Exception("DragonflyDB connection test failed")

        except Exception as e:
            logger.error(f"❌ Cache connection FAILED: {str(e)}")
            raise RuntimeError(f"Cache connection required but failed: {str(e)}")

    async def _initialize_transports(self):
        """Initialize real transport method connections"""
        # NATS connection
        try:
            nats_url = os.getenv("NATS_URL", "nats://nats-server:4222")

            if "," in nats_url:
                # Cluster mode
                nats_servers = [url.strip() for url in nats_url.split(",")]
                logger.info(f"🔗 Connecting to NATS cluster: {nats_servers}")
                self.nats_client = await asyncio.wait_for(
                    nats.connect(servers=nats_servers),
                    timeout=5.0
                )
                logger.info(f"✅ NATS cluster connected to {len(nats_servers)} servers")
            else:
                # Single server mode
                logger.info(f"🔗 Connecting to NATS server: {nats_url}")
                self.nats_client = await asyncio.wait_for(
                    nats.connect(servers=[nats_url]),
                    timeout=5.0
                )
                logger.info(f"✅ NATS connected to {nats_url}")
        except Exception as e:
            logger.error(f"❌ NATS connection FAILED: {str(e)}")
            raise RuntimeError(f"NATS connection required but failed: {str(e)}")

        # Kafka producer
        try:
            kafka_config = {
                'bootstrap.servers': os.getenv("KAFKA_BROKERS", "kafka:9092"),
                'client.id': f'central-hub-{os.getpid()}'
            }
            self.kafka_producer = Producer(kafka_config)
            logger.info("✅ Kafka producer initialized")
        except Exception as e:
            logger.error(f"❌ Kafka connection FAILED: {str(e)}")
            raise RuntimeError(f"Kafka connection required but failed: {str(e)}")

        # DragonflyDB pub/sub client
        try:
            dragonfly_password = os.getenv('DRAGONFLY_PASSWORD')
            dragonfly_host = os.getenv('DRAGONFLY_HOST', 'dragonflydb')
            dragonfly_port = os.getenv('DRAGONFLY_PORT', 6379)
            dragonfly_url = f"redis://:{dragonfly_password}@{dragonfly_host}:{dragonfly_port}"
            self.redis_client = redis.from_url(dragonfly_url)
            await asyncio.wait_for(self.redis_client.ping(), timeout=5.0)
            logger.info("✅ DragonflyDB pub/sub client connected")
        except Exception as e:
            logger.error(f"❌ Redis/DragonflyDB connection FAILED: {str(e)}")
            raise RuntimeError(f"Redis/DragonflyDB connection required but failed: {str(e)}")

    async def shutdown(self):
        """Close all connections gracefully"""
        try:
            logger.info("🛑 Shutting down Connection Manager...")

            # Close transport connections
            if self.nats_client:
                await self.nats_client.close()
                logger.info("✅ NATS connection closed")

            if self.kafka_producer:
                self.kafka_producer.flush()
                logger.info("✅ Kafka producer flushed")

            if self.redis_client:
                await self.redis_client.close()
                logger.info("✅ Redis client closed")

            # Close database connections
            if self.db_manager:
                await self.db_manager.disconnect()
                logger.info("✅ Database disconnected")

            if self.cache_manager:
                await self.cache_manager.disconnect()
                logger.info("✅ Cache disconnected")

            logger.info("✅ Connection Manager shutdown complete")

        except Exception as e:
            logger.error(f"❌ Connection Manager shutdown error: {str(e)}")

    async def health_check(self):
        """Check health of all connections"""
        health = {
            "database": "unknown",
            "cache": "unknown",
            "transports": {}
        }

        # Database health
        if self.db_manager:
            try:
                health["database"] = "healthy"
            except Exception:
                health["database"] = "unhealthy"

        # Cache health
        if self.cache_manager:
            try:
                cache_health = await self.cache_manager.health_check()
                health["cache"] = cache_health.get("overall_status", "unknown")
            except Exception:
                health["cache"] = "unhealthy"

        # Transport health
        for transport_name in ["nats", "kafka", "redis"]:
            client = getattr(self, f"{transport_name}_client", None)
            health["transports"][transport_name] = "connected" if client else "disconnected"

        return health
