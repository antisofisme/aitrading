"""
Component Manager Configuration - Suho AI Trading Platform
=========================================================

Centralized configuration for Component Manager service.
This service handles hot reload of shared components via NATS.
"""

CONFIG_COMPONENT_MANAGER = {
    # Service Metadata
    "service_info": {
        "name": "component-manager",
        "version": "1.0.0",
        "description": "Standalone service for hot reload shared components distribution",
        "maintainer": "suho-platform-team@suho.ai",
        "environment": "development"
    },

    # HOT RELOAD: Business Rules & Logic
    "business_rules": {
        "file_watcher": {
            "enabled": True,
            "debounce_ms": 500,
            "polling_interval_ms": 1000,
            "use_polling": True,  # Better for Docker volumes
            "watch_patterns": [
                "**/*.js",
                "**/*.py",
                "**/*.json"
            ],
            "ignore_patterns": [
                "**/node_modules/**",
                "**/.git/**",
                "**/test-*.js",
                "**/__pycache__/**",
                "**/*.pyc"
            ]
        },
        "component_processing": {
            "enable_compression": True,
            "compression_threshold_bytes": 1024,
            "max_component_size_mb": 10,
            "hash_algorithm": "sha256",
            "version_format": "timestamp.hash"
        },
        "publishing": {
            "publish_timeout_ms": 5000,
            "retry_attempts": 3,
            "retry_delay_ms": 1000,
            "batch_publishing": False,
            "topic_prefix": "suho.components.update"
        }
    },

    # HOT RELOAD: Feature Toggles
    "features": {
        "enable_debug_logging": True,
        "enable_performance_metrics": True,
        "enable_file_watcher": True,
        "enable_nats_publishing": True,
        "enable_component_caching": True,
        "enable_version_tracking": True,
        "enable_health_checks": True,
        "maintenance_mode": False
    },

    # HOT RELOAD: Component Manager Specific Settings
    "component_manager": {
        "shared_root": "/app/shared",
        "cache_directory": "/app/.component_cache",
        "versions_file": "/app/data/component_versions.json",
        "supported_extensions": [".js", ".py", ".json", ".md"],
        "max_cached_versions": 10,
        "cleanup_interval_hours": 24
    },

    # HOT RELOAD: NATS Configuration (Non-sensitive settings)
    "messaging": {
        "topics": {
            "component_updates": "suho.components.update",
            "component_requests": "suho.components.request",
            "component_deletions": "suho.components.delete"
        },
        "message_settings": {
            "max_payload_bytes": 1048576,  # 1MB
            "message_ttl_seconds": 300,
            "delivery_policy": "all",
            "ack_wait_seconds": 30
        },
        "connection_settings": {
            "reconnect_time_wait_ms": 2000,
            "max_reconnect_attempts": 10,
            "ping_interval_seconds": 30
        }
    },

    # HOT RELOAD: Performance Tuning
    "performance": {
        "thread_pool_size": 5,
        "file_scan_batch_size": 50,
        "memory_limit_mb": 256,
        "cpu_limit_percent": 50,
        "io_timeout_ms": 5000,
        "concurrent_processing": 3
    },

    # HOT RELOAD: Monitoring & Alerting
    "monitoring": {
        "metrics_enabled": True,
        "alert_thresholds": {
            "file_scan_time_ms": 5000,
            "publish_failure_rate_percent": 5.0,
            "memory_usage_percent": 80.0,
            "cpu_usage_percent": 70.0,
            "queue_depth": 100,
            "failed_publishes_count": 10
        },
        "log_levels": {
            "root": "INFO",
            "file_watcher": "DEBUG",
            "component_processor": "INFO",
            "nats_publisher": "INFO",
            "performance": "WARN"
        },
        "health_checks": {
            "nats_connection": True,
            "file_system_access": True,
            "memory_usage": True,
            "component_cache": True
        }
    },

    # HOT RELOAD: Component Validation
    "validation": {
        "syntax_validation": {
            "javascript": True,
            "python": True,
            "json": True
        },
        "security_scanning": {
            "enabled": False,  # Enable in production
            "scan_for_secrets": True,
            "allowed_imports": ["lodash", "axios", "moment"],
            "blocked_patterns": ["eval(", "Function(", "setTimeout("]
        },
        "size_limits": {
            "max_file_size_mb": 5,
            "max_line_count": 10000,
            "max_function_length": 500
        }
    },

    # STATIC REFERENCES: Infrastructure (Environment Variables)
    "static_references": {
        "nats_url": "ENV:NATS_URL",
        "shared_root": "ENV:SHARED_ROOT",
        "log_level": "ENV:LOG_LEVEL",
        "watch_enabled": "ENV:WATCH_ENABLED",
        "debounce_ms": "ENV:DEBOUNCE_MS"
    },

    # Configuration Metadata
    "config_meta": {
        "version": "1.0.0",
        "last_updated": "2025-09-29T18:45:00Z",
        "updated_by": "platform-team",
        "hot_reload_enabled": True,
        "validation_schema": "component_manager_config_v1",
        "dependencies": ["nats", "file-system"]
    }
}

# Component Manager Specific Validation Rules
VALIDATION_RULES_COMPONENT_MANAGER = {
    "required_fields": [
        "service_info.name",
        "service_info.version",
        "component_manager.shared_root",
        "business_rules.file_watcher.debounce_ms",
        "messaging.topics.component_updates"
    ],
    "numeric_ranges": {
        "business_rules.file_watcher.debounce_ms": (100, 5000),
        "business_rules.file_watcher.polling_interval_ms": (500, 10000),
        "business_rules.component_processing.max_component_size_mb": (1, 50),
        "performance.thread_pool_size": (1, 20),
        "performance.memory_limit_mb": (128, 1024),
        "validation.size_limits.max_file_size_mb": (1, 20)
    },
    "allowed_values": {
        "service_info.environment": ["development", "staging", "production"],
        "business_rules.component_processing.hash_algorithm": ["sha256", "sha1", "md5"],
        "messaging.message_settings.delivery_policy": ["all", "last", "new"]
    }
}

def validate_component_manager_config(config):
    """
    Validate Component Manager specific configuration
    Returns: (is_valid: bool, errors: list)
    """
    from templates.service_config_template import _get_nested_value

    errors = []

    # Check required fields
    for field_path in VALIDATION_RULES_COMPONENT_MANAGER["required_fields"]:
        if not _get_nested_value(config, field_path):
            errors.append(f"Required field missing: {field_path}")

    # Check numeric ranges
    for field_path, (min_val, max_val) in VALIDATION_RULES_COMPONENT_MANAGER["numeric_ranges"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and not (min_val <= value <= max_val):
            errors.append(f"Value out of range for {field_path}: {value} (should be {min_val}-{max_val})")

    # Check allowed values
    for field_path, allowed in VALIDATION_RULES_COMPONENT_MANAGER["allowed_values"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and value not in allowed:
            errors.append(f"Invalid value for {field_path}: {value} (allowed: {allowed})")

    # Custom validation for Component Manager
    watch_patterns = _get_nested_value(config, "business_rules.file_watcher.watch_patterns")
    if watch_patterns and len(watch_patterns) == 0:
        errors.append("At least one watch pattern must be specified")

    return len(errors) == 0, errors

# Export for hot reload system
__all__ = ['CONFIG_COMPONENT_MANAGER', 'VALIDATION_RULES_COMPONENT_MANAGER', 'validate_component_manager_config']