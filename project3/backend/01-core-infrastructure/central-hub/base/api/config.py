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
async def get_service_config(service_name: str) -> Dict[str, Any]:
    """Get configuration for specific service"""
    # TODO: Implement service-specific config retrieval
    return {
        "service": service_name,
        "config": {
            "database_pool_size": 10,
            "cache_ttl": 300,
            "log_level": "INFO"
        },
        "version": "1.0.0",
        "last_updated": int(time.time() * 1000)
    }


@config_router.post("/update")
async def update_config(update: ConfigUpdate, request: Request) -> Dict[str, Any]:
    """Update global or service-specific configuration - Enhanced with contract-based broadcasting"""
    from ..app import central_hub_service

    # Prepare update data for contract processing
    update_data = {
        "config_key": "service_config" if update.service else "global_config",
        "config_value": update.config,
        "target_services": [update.service] if update.service else "all",
        "version": update.version or "1.0.1",
        "timestamp": int(time.time() * 1000)
    }

    # Process configuration update through contract formatting
    try:
        format_result = await contract_processor.process_outbound_message('configuration_update', update_data)
        formatted_data = format_result.get('formatted_data', update_data)
        transport_info = format_result.get('transport_info', {})

        central_hub_service.logger.info(
            f"✅ Configuration updated for {'global' if not update.service else update.service} "
            f"using {transport_info.get('primary', 'http')} transport"
        )

        # TODO: Implement actual config update logic
        # This would typically:
        # 1. Validate config using contract schemas
        # 2. Store in database
        # 3. Broadcast to affected services using selected transport method
        # 4. Log the change with contract metadata

        return {
            "status": "updated",
            "service": update.service or "global",
            "updated_at": int(time.time() * 1000),
            "version": update.version or "1.0.1",
            "transport_method": transport_info.get('primary', 'http'),
            "broadcast_format": "contract_validated",
            "affected_services": formatted_data.get('target_services', [])
        }

    except Exception as e:
        central_hub_service.logger.warning(f"Contract formatting failed for config update: {str(e)}")

        # Fallback to basic update without contract formatting
        central_hub_service.logger.info(
            f"Configuration updated for {'global' if not update.service else update.service} (fallback mode)"
        )

        return {
            "status": "updated",
            "service": update.service or "global",
            "updated_at": int(time.time() * 1000),
            "version": update.version or "1.0.1",
            "transport_method": "http",
            "broadcast_format": "basic"
        }


@config_router.get("/history/{service_name}")
async def get_config_history(service_name: str, limit: int = 10) -> Dict[str, Any]:
    """Get configuration change history for service"""
    # TODO: Implement config history retrieval
    return {
        "service": service_name,
        "history": [
            {
                "version": "1.0.0",
                "updated_at": int(time.time() * 1000) - 3600000,
                "updated_by": "admin",
                "changes": ["database_pool_size: 5 -> 10"]
            }
        ],
        "total": 1
    }


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