"""
Central Hub - Configuration Manager Coordinator
Handles configuration distribution and management
"""

import time
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging


class ConfigManager:
    """Manages configuration distribution for all services"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.config-manager")
        self.configurations = self._load_default_configurations()
        self.service_configs: Dict[str, Dict[str, Any]] = {}

    def _load_default_configurations(self) -> Dict[str, Any]:
        """Load configurations from shared/static directory"""
        config = {}

        # Load database configurations
        config["database"] = self._load_database_configs()

        # Load messaging configurations
        config["messaging"] = self._load_messaging_configs()

        # Legacy configurations that aren't moved to shared/static yet
        config.update(self._load_legacy_configurations())

        return config

    def _load_database_configs(self) -> Dict[str, Any]:
        """Load database configurations from shared/static/database/"""
        db_configs = {}
        shared_path = Path(__file__).parent.parent.parent / "shared" / "static" / "database"

        try:
            for config_file in shared_path.glob("*.json"):
                db_name = config_file.stem  # filename without .json
                with open(config_file, 'r') as f:
                    db_config = json.load(f)
                    # Replace environment variables in config
                    db_config = self._substitute_env_vars(db_config)
                    db_configs[db_name] = db_config

            self.logger.info(f"Loaded {len(db_configs)} database configurations")
            return db_configs

        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to load database configs from shared/static/database/: {e}")
            raise RuntimeError(f"Database configuration loading failed: {e}. Check shared/static/database/ directory and file permissions.")

    def _load_messaging_configs(self) -> Dict[str, Any]:
        """Load messaging configurations from shared/static/messaging/"""
        msg_configs = {}
        shared_path = Path(__file__).parent.parent.parent / "shared" / "static" / "messaging"

        try:
            for config_file in shared_path.glob("*.json"):
                msg_name = config_file.stem  # filename without .json
                with open(config_file, 'r') as f:
                    msg_config = json.load(f)
                    # Replace environment variables in config
                    msg_config = self._substitute_env_vars(msg_config)
                    msg_configs[msg_name] = msg_config

            self.logger.info(f"Loaded {len(msg_configs)} messaging configurations")
            return msg_configs

        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to load messaging configs from shared/static/messaging/: {e}")
            raise RuntimeError(f"Messaging configuration loading failed: {e}. Check shared/static/messaging/ directory and file permissions.")

    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute environment variables in config"""
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            env_var = config[2:-1]  # Remove ${ and }
            env_value = os.getenv(env_var)
            if env_value is None:
                raise RuntimeError(f"Required environment variable '{env_var}' is not set. Please configure all required environment variables.")
            return env_value
        else:
            return config

    def get_database_config(self, db_name: str) -> Dict[str, Any]:
        """Get specific database configuration"""
        config = self.configurations.get("database", {}).get(db_name)
        if config is None:
            raise RuntimeError(f"Database configuration for '{db_name}' not found. Available databases: {list(self.configurations.get('database', {}).keys())}")
        return config

    def get_messaging_config(self, msg_name: str) -> Dict[str, Any]:
        """Get specific messaging configuration"""
        config = self.configurations.get("messaging", {}).get(msg_name)
        if config is None:
            raise RuntimeError(f"Messaging configuration for '{msg_name}' not found. Available messaging systems: {list(self.configurations.get('messaging', {}).keys())}")
        return config

    def get_all_database_configs(self) -> Dict[str, Any]:
        """Get all database configurations"""
        return self.configurations.get("database", {})

    def get_all_messaging_configs(self) -> Dict[str, Any]:
        """Get all messaging configurations"""
        return self.configurations.get("messaging", {})

    def get_nats_subjects(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get NATS subject patterns for specific domain

        Args:
            domain: market_data, signals, indicators, system (optional)

        Returns:
            Subject patterns dict

        Example:
            >>> config_manager.get_nats_subjects("market_data")
            {
                "patterns": {
                    "tick": "market.{symbol}.tick",
                    "candle": "market.{symbol}.{timeframe}"
                },
                "examples": ["market.EURUSD.tick", "market.EURUSD.5m"]
            }
        """
        nats_config = self.get_messaging_config("nats")
        subjects = nats_config.get("subjects", {})

        if domain:
            domain_subjects = subjects.get(domain, {})
            if not domain_subjects:
                available_domains = list(subjects.keys())
                raise ValueError(f"Domain '{domain}' not found. Available domains: {available_domains}")
            return domain_subjects

        return subjects

    def get_kafka_topics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Kafka topic configurations for specific domain

        Args:
            domain: user_domain, system_domain (optional)

        Returns:
            Topic configurations dict

        Example:
            >>> config_manager.get_kafka_topics("user_domain")
            {
                "auth": {
                    "name": "user.auth",
                    "partitions": 3,
                    "retention_ms": 7776000000
                }
            }
        """
        kafka_config = self.get_messaging_config("kafka")
        topics = kafka_config.get("topics", {})

        if domain:
            domain_topics = topics.get(domain, {})
            if not domain_topics:
                available_domains = list(topics.keys())
                raise ValueError(f"Domain '{domain}' not found. Available domains: {available_domains}")
            return domain_topics

        return topics

    def get_kafka_consumer_groups(self) -> Dict[str, Any]:
        """
        Get pre-defined Kafka consumer group configurations

        Returns:
            Consumer group configs for all services

        Example:
            >>> config_manager.get_kafka_consumer_groups()
            {
                "trading_engine": {
                    "group_id": "trading-engine",
                    "topics": ["user.commands"]
                }
            }
        """
        kafka_config = self.get_messaging_config("kafka")
        return kafka_config.get("consumer_groups", {})

    def _load_legacy_configurations(self) -> Dict[str, Any]:
        """Load legacy configurations that aren't in shared/static yet"""
        return {
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