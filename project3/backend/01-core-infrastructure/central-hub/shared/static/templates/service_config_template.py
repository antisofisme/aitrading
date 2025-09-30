"""
Service Configuration Template - Suho AI Trading Platform
=======================================================

This template provides the standard structure for service-specific configurations.
All services should follow this pattern for consistent configuration management.

Configuration Strategy:
- STATIC: Infrastructure configs (databases, message queues, security)
- HOT RELOAD: Business logic configs (rules, features, parameters)
"""

SERVICE_CONFIG_TEMPLATE = {
    # Service Metadata
    "service_info": {
        "name": "service-name",
        "version": "1.0.0",
        "description": "Service description",
        "maintainer": "team@suho.ai",
        "environment": "development"  # development, staging, production
    },

    # HOT RELOAD: Business Rules & Logic
    "business_rules": {
        "rate_limiting": {
            "requests_per_minute": 1000,
            "burst_limit": 100,
            "enabled": True
        },
        "timeouts": {
            "request_timeout_ms": 30000,
            "connection_timeout_ms": 5000,
            "circuit_breaker_timeout_ms": 60000
        },
        "retry_policy": {
            "max_attempts": 3,
            "backoff_multiplier": 2,
            "base_delay_ms": 100
        },
        "validation_rules": {
            "strict_mode": False,
            "allow_unknown_fields": True
        }
    },

    # HOT RELOAD: Feature Toggles
    "features": {
        "enable_debug_logging": False,
        "enable_performance_metrics": True,
        "enable_request_tracing": False,
        "enable_circuit_breaker": True,
        "enable_health_checks": True,
        "maintenance_mode": False
    },

    # HOT RELOAD: Performance Tuning
    "performance": {
        "thread_pool_size": 10,
        "connection_pool_size": 20,
        "cache_ttl_seconds": 300,
        "batch_size": 100,
        "memory_limit_mb": 512
    },

    # HOT RELOAD: Monitoring & Alerting
    "monitoring": {
        "metrics_enabled": True,
        "alert_thresholds": {
            "error_rate_percent": 5.0,
            "response_time_ms": 1000,
            "memory_usage_percent": 80.0,
            "cpu_usage_percent": 70.0
        },
        "log_levels": {
            "root": "INFO",
            "business": "DEBUG",
            "performance": "WARN"
        }
    },

    # STATIC REFERENCES: Infrastructure (Environment Variables)
    "static_references": {
        "database_url": "ENV:DATABASE_URL",
        "cache_url": "ENV:CACHE_URL",
        "nats_url": "ENV:NATS_URL",
        "kafka_brokers": "ENV:KAFKA_BROKERS",
        "api_keys": "ENV:API_KEYS",
        "secrets": "ENV:SERVICE_SECRETS"
    },

    # Configuration Metadata
    "config_meta": {
        "version": "1.0.0",
        "last_updated": "2025-09-29T18:45:00Z",
        "updated_by": "system",
        "hot_reload_enabled": True,
        "validation_schema": "service_config_v1"
    }
}

# Validation Rules for Configuration
VALIDATION_RULES = {
    "required_fields": [
        "service_info.name",
        "service_info.version",
        "business_rules.rate_limiting.requests_per_minute",
        "features.enable_health_checks"
    ],
    "numeric_ranges": {
        "business_rules.timeouts.request_timeout_ms": (1000, 300000),
        "business_rules.rate_limiting.requests_per_minute": (1, 100000),
        "performance.thread_pool_size": (1, 100)
    },
    "allowed_values": {
        "service_info.environment": ["development", "staging", "production"],
        "monitoring.log_levels.root": ["DEBUG", "INFO", "WARN", "ERROR"]
    }
}

def validate_config(config):
    """
    Validate service configuration against rules
    Returns: (is_valid: bool, errors: list)
    """
    errors = []

    # Check required fields
    for field_path in VALIDATION_RULES["required_fields"]:
        if not _get_nested_value(config, field_path):
            errors.append(f"Required field missing: {field_path}")

    # Check numeric ranges
    for field_path, (min_val, max_val) in VALIDATION_RULES["numeric_ranges"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and not (min_val <= value <= max_val):
            errors.append(f"Value out of range for {field_path}: {value} (should be {min_val}-{max_val})")

    # Check allowed values
    for field_path, allowed in VALIDATION_RULES["allowed_values"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and value not in allowed:
            errors.append(f"Invalid value for {field_path}: {value} (allowed: {allowed})")

    return len(errors) == 0, errors

def _get_nested_value(config, field_path):
    """Get nested value from config using dot notation"""
    keys = field_path.split('.')
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

# Export template for service-specific configs
__all__ = ['SERVICE_CONFIG_TEMPLATE', 'VALIDATION_RULES', 'validate_config']