"""
Central Hub - Configuration Manager Coordinator
Handles configuration distribution and management
"""

import time
from typing import Dict, List, Optional, Any
import logging


class ConfigManager:
    """Manages configuration distribution for all services"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.config-manager")
        self.configurations = self._load_default_configurations()
        self.service_configs: Dict[str, Dict[str, Any]] = {}

    def _load_default_configurations(self) -> Dict[str, Any]:
        """Load default system configurations"""
        return {
            "database": {
                "postgresql": "postgresql://suho_admin:suho_secure_password_2024@postgresql:5432/suho_trading",
                "clickhouse": "http://clickhouse:8123",
                "dragonflydb": "redis://:dragonfly_secure_2024@dragonflydb:6379",
                "arangodb": "http://root:arango_secure_password_2024@arangodb:8529"
            },
            "messaging": {
                "nats": "nats://nats-server:4222",
                "kafka": "kafka:9092"
            },
            "ai": {
                "weaviate": "http://weaviate:8080"
            },
            "shared_components": {
                "error_dna": {
                    "enabled": True,
                    "classification_threshold": 0.8,
                    "max_retry_attempts": 3
                },
                "circuit_breaker": {
                    "enabled": True,
                    "failure_threshold": 5,
                    "timeout_seconds": 60
                },
                "transfer_manager": {
                    "auto_select_transport": True,
                    "fallback_method": "http",
                    "timeout_seconds": 30
                }
            },
            "transport_routing": {
                "service_registration": {
                    "primary_method": "grpc",
                    "fallback_method": "http",
                    "timeout_ms": 5000
                },
                "configuration_request": {
                    "primary_method": "http",
                    "fallback_method": "grpc",
                    "timeout_ms": 10000
                },
                "health_monitoring": {
                    "primary_method": "nats-kafka",
                    "fallback_method": "http",
                    "timeout_ms": 2000
                }
            }
        }

    async def get_config(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get configuration for a service"""
        service_name = request_data.get("service_name")
        config_keys = request_data.get("config_keys", [])
        environment = request_data.get("environment", "production")

        if not service_name:
            raise ValueError("Service name is required for configuration request")

        # Get base configuration
        config_response = {}

        if not config_keys:
            # Return all configurations
            config_response = self.configurations.copy()
        else:
            # Return specific configuration keys
            for key in config_keys:
                if key in self.configurations:
                    config_response[key] = self.configurations[key]

        # Add service-specific overrides if available
        if service_name in self.service_configs:
            service_overrides = self.service_configs[service_name]
            config_response.update(service_overrides)

        # Environment-specific adjustments
        if environment == "development":
            config_response = self._apply_development_overrides(config_response)
        elif environment == "testing":
            config_response = self._apply_testing_overrides(config_response)

        return {
            "direct_response": {
                "type": "configuration_response",
                "data": {
                    "service_name": service_name,
                    "environment": environment,
                    "configuration": config_response,
                    "version": "1.0.0",
                    "timestamp": int(time.time() * 1000)
                }
            }
        }

    async def update_config(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update system configuration"""
        config_key = update_data.get("config_key")
        config_value = update_data.get("config_value")
        target_services = update_data.get("target_services", "all")

        if not config_key or config_value is None:
            raise ValueError("Config key and value are required")

        # Update configuration
        self._set_nested_config(self.configurations, config_key, config_value)

        self.logger.info(f"✅ Configuration updated: {config_key}")

        # Prepare broadcast update
        broadcast_data = {
            "type": "configuration_update",
            "data": {
                "config_key": config_key,
                "config_value": config_value,
                "version": "1.0.0",
                "updated_at": int(time.time() * 1000),
                "effective_immediately": True
            }
        }

        if target_services == "all":
            # Broadcast to all registered services
            return {
                "broadcast_updates": [broadcast_data]
            }
        else:
            # Send to specific services
            return {
                "coordination_messages": [
                    {
                        "type": "configuration_update",
                        "target_service": service,
                        "data": broadcast_data["data"]
                    }
                    for service in target_services if isinstance(target_services, list)
                ]
            }

    def _set_nested_config(self, config_dict: Dict, key_path: str, value: Any):
        """Set nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = config_dict

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _apply_development_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply development environment overrides"""
        dev_config = config.copy()

        # Development-specific database URLs (if using local instances)
        if "database" in dev_config:
            dev_config["database"].update({
                "postgresql": "postgresql://dev_user:dev_pass@localhost:5432/suho_trading_dev",
                "dragonflydb": "redis://localhost:6379"
            })

        # Enable debug logging
        if "shared_components" not in dev_config:
            dev_config["shared_components"] = {}
        dev_config["shared_components"]["debug_logging"] = True

        return dev_config

    def _apply_testing_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply testing environment overrides"""
        test_config = config.copy()

        # Testing-specific configurations
        if "database" in test_config:
            test_config["database"].update({
                "postgresql": "postgresql://test_user:test_pass@localhost:5433/suho_trading_test"
            })

        # Reduce timeouts for faster tests
        if "transport_routing" in test_config:
            for route_config in test_config["transport_routing"].values():
                if "timeout_ms" in route_config:
                    route_config["timeout_ms"] = min(route_config["timeout_ms"], 3000)

        return test_config

    async def register_service_config(self, service_name: str, service_config: Dict[str, Any]):
        """Register service-specific configuration overrides"""
        self.service_configs[service_name] = service_config
        self.logger.info(f"✅ Service-specific config registered for {service_name}")

    async def health_check(self) -> Dict[str, Any]:
        """Health check for configuration coordinator"""
        return {
            "status": "operational",
            "total_configurations": len(self.configurations),
            "service_specific_configs": len(self.service_configs),
            "last_update": int(time.time() * 1000)
        }