"""
Configuration Validation System for Centralized Config Management
Part of SPARC Trading Platform - Central Hub Service
"""

import os
import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    level: ValidationLevel
    field: str
    message: str
    current_value: Any = None
    expected_type: str = None

class ConfigValidator:
    """Centralized configuration validation system"""

    def __init__(self):
        self.validation_results: List[ValidationResult] = []

    def validate_config(self, config: Dict[str, Any], service_name: str) -> List[ValidationResult]:
        """
        Validate configuration for a specific service

        Args:
            config: Configuration dictionary to validate
            service_name: Name of the service (api-gateway, component-manager, etc.)

        Returns:
            List of validation results
        """
        self.validation_results = []

        # Common validation for all services
        self._validate_service_info(config.get('service_info', {}))
        self._validate_infrastructure(config.get('infrastructure', {}))

        # Service-specific validation
        if service_name == 'api-gateway':
            self._validate_api_gateway_specific(config)
        elif service_name == 'component-manager':
            self._validate_component_manager_specific(config)
        elif service_name == 'trading-engine':
            self._validate_trading_engine_specific(config)
        elif service_name == 'market-analyzer':
            self._validate_market_analyzer_specific(config)

        return self.validation_results

    def _validate_service_info(self, service_info: Dict[str, Any]):
        """Validate common service info fields"""
        required_fields = ['name', 'version', 'description', 'port']

        for field in required_fields:
            if field not in service_info:
                self.validation_results.append(
                    ValidationResult(
                        ValidationLevel.ERROR,
                        f"service_info.{field}",
                        f"Required field '{field}' is missing"
                    )
                )

        # Validate port range
        if 'port' in service_info:
            port = service_info['port']
            if not isinstance(port, int) or port < 1000 or port > 65535:
                self.validation_results.append(
                    ValidationResult(
                        ValidationLevel.ERROR,
                        "service_info.port",
                        "Port must be an integer between 1000 and 65535",
                        port,
                        "int (1000-65535)"
                    )
                )

    def _validate_infrastructure(self, infrastructure: Dict[str, Any]):
        """Validate infrastructure configuration"""
        if 'database' in infrastructure:
            db_config = infrastructure['database']

            # Check for required database fields
            required_db_fields = ['host', 'port', 'name', 'user']
            for field in required_db_fields:
                if field not in db_config:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.ERROR,
                            f"infrastructure.database.{field}",
                            f"Required database field '{field}' is missing"
                        )
                    )

        if 'messaging' in infrastructure:
            messaging_config = infrastructure['messaging']

            # Validate NATS configuration
            if 'nats' in messaging_config:
                nats_config = messaging_config['nats']
                if 'servers' not in nats_config or not nats_config['servers']:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.ERROR,
                            "infrastructure.messaging.nats.servers",
                            "NATS servers configuration is required"
                        )
                    )

    def _validate_api_gateway_specific(self, config: Dict[str, Any]):
        """Validate API Gateway specific configuration"""
        # Validate routing configuration
        if 'business_rules' in config and 'routing' in config['business_rules']:
            routing = config['business_rules']['routing']

            if 'load_balancing_strategy' in routing:
                valid_strategies = ['round_robin', 'least_connections', 'ip_hash']
                strategy = routing['load_balancing_strategy']
                if strategy not in valid_strategies:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.ERROR,
                            "business_rules.routing.load_balancing_strategy",
                            f"Invalid load balancing strategy. Must be one of: {valid_strategies}",
                            strategy,
                            f"str ({', '.join(valid_strategies)})"
                        )
                    )

        # Validate rate limiting
        if 'features' in config and 'rate_limiting' in config['features']:
            rate_limit = config['features']['rate_limiting']
            if rate_limit.get('enabled', False):
                if 'requests_per_minute' not in rate_limit:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.WARNING,
                            "features.rate_limiting.requests_per_minute",
                            "Rate limiting enabled but requests_per_minute not specified"
                        )
                    )

    def _validate_component_manager_specific(self, config: Dict[str, Any]):
        """Validate Component Manager specific configuration"""
        if 'business_rules' in config and 'file_watching' in config['business_rules']:
            file_watching = config['business_rules']['file_watching']

            # Validate watch patterns
            if 'patterns' in file_watching:
                patterns = file_watching['patterns']
                if not isinstance(patterns, list) or not patterns:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.ERROR,
                            "business_rules.file_watching.patterns",
                            "Watch patterns must be a non-empty list",
                            patterns,
                            "list[str]"
                        )
                    )

            # Validate polling settings
            if 'use_polling' in file_watching and file_watching['use_polling']:
                if 'polling_interval' not in file_watching:
                    self.validation_results.append(
                        ValidationResult(
                            ValidationLevel.WARNING,
                            "business_rules.file_watching.polling_interval",
                            "Polling enabled but polling_interval not specified, using default"
                        )
                    )

    def _validate_trading_engine_specific(self, config: Dict[str, Any]):
        """Validate Trading Engine specific configuration (placeholder)"""
        # Future implementation for trading engine validation
        self.validation_results.append(
            ValidationResult(
                ValidationLevel.INFO,
                "trading_engine",
                "Trading Engine validation not yet implemented"
            )
        )

    def _validate_market_analyzer_specific(self, config: Dict[str, Any]):
        """Validate Market Analyzer specific configuration (placeholder)"""
        # Future implementation for market analyzer validation
        self.validation_results.append(
            ValidationResult(
                ValidationLevel.INFO,
                "market_analyzer",
                "Market Analyzer validation not yet implemented"
            )
        )

    def has_errors(self) -> bool:
        """Check if validation found any errors"""
        return any(result.level == ValidationLevel.ERROR for result in self.validation_results)

    def has_warnings(self) -> bool:
        """Check if validation found any warnings"""
        return any(result.level == ValidationLevel.WARNING for result in self.validation_results)

    def get_error_summary(self) -> str:
        """Get summary of validation errors"""
        errors = [r for r in self.validation_results if r.level == ValidationLevel.ERROR]
        warnings = [r for r in self.validation_results if r.level == ValidationLevel.WARNING]

        summary = []
        if errors:
            summary.append(f"❌ {len(errors)} error(s) found:")
            for error in errors:
                summary.append(f"  • {error.field}: {error.message}")

        if warnings:
            summary.append(f"⚠️  {len(warnings)} warning(s) found:")
            for warning in warnings:
                summary.append(f"  • {warning.field}: {warning.message}")

        if not errors and not warnings:
            summary.append("✅ Configuration validation passed")

        return "\n".join(summary)

def validate_service_config(service_name: str, config: Dict[str, Any]) -> List[ValidationResult]:
    """
    Convenience function to validate a service configuration

    Args:
        service_name: Name of the service
        config: Configuration dictionary

    Returns:
        List of validation results
    """
    validator = ConfigValidator()
    return validator.validate_config(config, service_name)

# Example usage and testing
if __name__ == "__main__":
    # Test validation with sample config
    sample_config = {
        "service_info": {
            "name": "api-gateway",
            "version": "1.0.0",
            "description": "API Gateway Service",
            "port": 3000
        },
        "infrastructure": {
            "database": {
                "host": "suho-postgresql",
                "port": 5432,
                "name": "suho_trading",
                "user": "suho_admin"
            },
            "messaging": {
                "nats": {
                    "servers": ["nats://suho-nats-server:4222"]
                }
            }
        }
    }

    validator = ConfigValidator()
    results = validator.validate_config(sample_config, "api-gateway")
    print(validator.get_error_summary())