"""
Central Hub Configuration Management API
Enhanced with contract validation and transport routing
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time

import sys
from pathlib import Path

# Add shared directory to Python path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from components.utils.contract_bridge import ContractProcessorIntegration

config_router = APIRouter()
contract_processor = ContractProcessorIntegration()


class ConfigUpdate(BaseModel):
    """Configuration update model"""
    service: Optional[str] = None  # Specific service or global
    config: Dict[str, Any]
    version: Optional[str] = None


@config_router.get("/")
async def get_global_config(request: Request) -> Dict[str, Any]:
    """Get global configuration - Enhanced with contract-based formatting"""

    # Prepare configuration request data for contract processing
    request_data = {
        "service_name": "global",
        "config_keys": [],  # Empty means all configs
        "environment": "production",
        "timestamp": int(time.time() * 1000)
    }

    # Process through contract validation
    try:
        contract_result = await contract_processor.process_inbound_message('configuration_request', request_data)
        transport_info = contract_result.get('transport_info', {})
    except Exception as e:
        # Continue with default if contract processing fails
        transport_info = {"primary": "http", "fallback": "grpc"}

    # Get configuration data
    config_data = {
        "config": {
            "rate_limits": {
                "free_tier": 50,
                "pro_tier": 200,
                "enterprise_tier": 1000
            },
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 60
            },
            "health_check": {
                "interval_seconds": 30,
                "timeout_seconds": 5
            },
            "transport_routing": {
                "default_method": transport_info.get("primary", "http"),
                "fallback_method": transport_info.get("fallback", "grpc")
            }
        },
        "version": "1.0.0",
        "last_updated": int(time.time() * 1000),
        "transport_method": transport_info.get("primary", "http")
    }

    return config_data


@config_router.get("/{service_name}")
async def get_service_config(service_name: str, request: Request) -> Dict[str, Any]:
    """
    Get configuration for specific service from PostgreSQL

    Returns:
        - 200: Config found
        - 404: Service not found
        - 500: Database error
    """
    try:
        # Get database manager from app state
        import sys
        from pathlib import Path
        # Add base directory to path
        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from app import central_hub_service

        if not central_hub_service.connection_manager or not central_hub_service.connection_manager.db_manager:
            raise HTTPException(status_code=503, detail="Database connection not available")

        db_manager = central_hub_service.connection_manager.db_manager

        # Fetch config from PostgreSQL using DatabaseManager API
        row = await db_manager.fetch_one(
            """
            SELECT
                config_json,
                version,
                updated_at,
                description,
                tags,
                active
            FROM service_configs
            WHERE service_name = $1 AND active = true
            """,
            [service_name]
        )

        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration not found for service: {service_name}"
            )

        return {
            "service_name": service_name,
            "config": row['config_json'],
            "version": row['version'],
            "updated_at": int(row['updated_at'].timestamp() * 1000),
            "description": row['description'],
            "tags": row['tags'],
            "active": row['active']
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.post("/{service_name}")
async def update_service_config(
    service_name: str,
    config_update: Dict[str, Any],
    request: Request,
    version: Optional[str] = None,
    updated_by: str = "api-user"
) -> Dict[str, Any]:
    """
    Update service configuration and store in PostgreSQL

    Also broadcasts update notification via NATS (optional)

    Args:
        service_name: Service identifier
        config_update: New configuration (full or partial)
        version: Config version (auto-incremented if not provided)
        updated_by: Who made the change (for audit)

    Returns:
        - 200: Config updated successfully
        - 404: Service not found
        - 500: Database error
    """
    try:
        import sys
        from pathlib import Path
        # Add base directory to path
        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from app import central_hub_service

        if not central_hub_service.connection_manager or not central_hub_service.connection_manager.db_manager:
            raise HTTPException(status_code=503, detail="Database connection not available")

        db_manager = central_hub_service.connection_manager.db_manager

        # Store in PostgreSQL with UPSERT using DatabaseManager API
        # Convert config_update to JSON string for JSONB column
        import json
        config_json_str = json.dumps(config_update)

        await db_manager.execute(
            """
            INSERT INTO service_configs (
                service_name,
                config_json,
                version,
                updated_by
            ) VALUES ($1, $2::jsonb, $3, $4)
            ON CONFLICT (service_name) DO UPDATE SET
                config_json = EXCLUDED.config_json,
                version = EXCLUDED.version,
                updated_by = EXCLUDED.updated_by,
                updated_at = NOW()
            """,
            [service_name, config_json_str, version or "1.0.0", updated_by]
        )

        # Fetch updated config for response
        row = await db_manager.fetch_one(
            """
            SELECT config_json, version, updated_at
            FROM service_configs
            WHERE service_name = $1
            """,
            [service_name]
        )

        # Broadcast update via NATS (optional, best-effort)
        try:
            if central_hub_service.connection_manager.nats_client:
                import json
                update_message = {
                    "service_name": service_name,
                    "config": config_update,
                    "version": row['version'],
                    "updated_at": int(row['updated_at'].timestamp() * 1000),
                    "updated_by": updated_by
                }

                await central_hub_service.connection_manager.nats_client.publish(
                    f"config.update.{service_name}",
                    json.dumps(update_message).encode()
                )

                central_hub_service.logger.info(
                    f"✅ Config updated and broadcasted for {service_name} (version: {row['version']})"
                )
        except Exception as nats_error:
            central_hub_service.logger.warning(f"NATS broadcast failed (non-critical): {nats_error}")

        return {
            "status": "updated",
            "service_name": service_name,
            "config": row['config_json'],
            "version": row['version'],
            "updated_at": int(row['updated_at'].timestamp() * 1000),
            "updated_by": updated_by,
            "broadcast": "sent" if central_hub_service.connection_manager.nats_client else "unavailable"
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to update config for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/history/{service_name}")
async def get_config_history(
    service_name: str,
    request: Request,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get configuration change history for service from audit log

    Args:
        service_name: Service identifier
        limit: Maximum number of history entries (default: 10, max: 100)

    Returns:
        - 200: History retrieved
        - 404: Service not found
        - 500: Database error
    """
    try:
        import sys
        from pathlib import Path
        # Add base directory to path
        base_dir = Path(__file__).parent.parent
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))

        from app import central_hub_service

        if not central_hub_service.connection_manager or not central_hub_service.connection_manager.db_manager:
            raise HTTPException(status_code=503, detail="Database connection not available")

        db_manager = central_hub_service.connection_manager.db_manager

        # Limit max history entries
        limit = min(limit, 100)

        # Fetch history from audit log using DatabaseManager API
        rows = await db_manager.fetch_many(
            """
            SELECT
                version,
                action,
                changed_by,
                changed_at,
                change_reason,
                config_json
            FROM config_audit_log
            WHERE service_name = $1
            ORDER BY changed_at DESC
            LIMIT $2
            """,
            [service_name, limit]
        )

        # Get total count
        # Use get_connection to access the pool for fetchval (not in DatabaseManager API)
        connection = db_manager.get_connection("default")
        async with connection.pool.acquire() as conn:
            total = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM config_audit_log
                WHERE service_name = $1
                """,
                service_name
            )

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No history found for service: {service_name}"
            )

        history = [
            {
                "version": row['version'],
                "action": row['action'],
                "changed_by": row['changed_by'],
                "changed_at": int(row['changed_at'].timestamp() * 1000),
                "change_reason": row['change_reason'],
                "config": row['config_json']
            }
            for row in rows
        ]

        return {
            "service_name": service_name,
            "history": history,
            "total": total,
            "limit": limit
        }

    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get history for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/database/{db_name}")
async def get_database_config(db_name: str, request: Request) -> Dict[str, Any]:
    """Get database configuration by name

    Available databases:
    - postgresql
    - clickhouse
    - dragonflydb
    - arangodb
    - weaviate
    """
    try:
        # Get config_manager from app state
        config_manager = request.app.state.config_manager

        config = config_manager.get_database_config(db_name)

        return {
            "database": db_name,
            "config": config,
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000)
        }

    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get database config for {db_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/messaging/{msg_name}")
async def get_messaging_config(msg_name: str, request: Request) -> Dict[str, Any]:
    """Get messaging configuration by name

    Available messaging systems:
    - nats
    - kafka
    - zookeeper
    """
    try:
        # Get config_manager from app state
        config_manager = request.app.state.config_manager

        config = config_manager.get_messaging_config(msg_name)

        return {
            "messaging": msg_name,
            "config": config,
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000)
        }

    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get messaging config for {msg_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/databases/all")
async def get_all_database_configs(request: Request) -> Dict[str, Any]:
    """Get all database configurations in format expected by services

    Returns:
        {
            "timescale": {...},
            "dragonfly": {...},
            "clickhouse": {...},
            ...
        }
    """
    try:
        config_manager = request.app.state.config_manager

        # Map database names to their config keys expected by services
        db_mapping = {
            "timescale": "postgresql",  # Services use "timescale" key for PostgreSQL/TimescaleDB
            "dragonfly": "dragonflydb",
            "clickhouse": "clickhouse",
            "arango": "arangodb",
            "weaviate": "weaviate"
        }

        all_configs = {}

        for service_key, config_key in db_mapping.items():
            try:
                config = config_manager.get_database_config(config_key)
                all_configs[service_key] = config
            except RuntimeError:
                # Skip databases that don't have configs
                continue

        return all_configs

    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get all database configs: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/messaging/nats/subjects")
async def get_nats_subjects(request: Request, domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Get NATS subject patterns

    Query params:
        domain: market_data, signals, indicators, system (optional)

    Returns:
        Subject patterns for specified domain or all domains

    Examples:
        GET /api/config/messaging/nats/subjects
        GET /api/config/messaging/nats/subjects?domain=market_data
    """
    try:
        config_manager = request.app.state.config_manager
        subjects = config_manager.get_nats_subjects(domain)

        return {
            "status": "success",
            "domain": domain or "all",
            "subjects": subjects,
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get NATS subjects: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/messaging/kafka/topics")
async def get_kafka_topics(request: Request, domain: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Kafka topic configurations

    Query params:
        domain: user_domain, system_domain (optional)

    Returns:
        Topic configs for specified domain or all domains

    Examples:
        GET /api/config/messaging/kafka/topics
        GET /api/config/messaging/kafka/topics?domain=user_domain
    """
    try:
        config_manager = request.app.state.config_manager
        topics = config_manager.get_kafka_topics(domain)

        return {
            "status": "success",
            "domain": domain or "all",
            "topics": topics,
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get Kafka topics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@config_router.get("/messaging/kafka/consumer-groups")
async def get_kafka_consumer_groups(request: Request) -> Dict[str, Any]:
    """
    Get pre-defined Kafka consumer group configurations

    Returns:
        Consumer group configs for all services

    Example:
        GET /api/config/messaging/kafka/consumer-groups
    """
    try:
        config_manager = request.app.state.config_manager
        consumer_groups = config_manager.get_kafka_consumer_groups()

        return {
            "status": "success",
            "consumer_groups": consumer_groups,
            "version": "1.0.0",
            "last_updated": int(time.time() * 1000)
        }

    except Exception as e:
        import logging
        logger = logging.getLogger("central-hub.api.config")
        logger.error(f"Failed to get Kafka consumer groups: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")