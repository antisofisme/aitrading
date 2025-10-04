"""
API Gateway Configuration - Suho AI Trading Platform
===================================================

Centralized configuration for API Gateway service.
This config supports hot reload for business logic while keeping
infrastructure configs static for stability.
"""

CONFIG_API_GATEWAY = {
    # Service Metadata
    "service_info": {
        "name": "api-gateway",
        "version": "2.0.0",
        "description": "Main API Gateway with hot reload support and Suho Binary Protocol",
        "maintainer": "suho-platform-team@suho.ai",
        "environment": "development"
    },

    # HOT RELOAD: Business Rules & Logic
    "business_rules": {
        "rate_limiting": {
            "requests_per_minute": 1000,
            "burst_limit": 100,
            "enabled": True,
            "whitelist_ips": [],
            "blacklist_ips": []
        },
        "timeouts": {
            "request_timeout_ms": 30000,
            "connection_timeout_ms": 5000,
            "keep_alive_timeout_ms": 65000,
            "circuit_breaker_timeout_ms": 60000
        },
        "retry_policy": {
            "max_attempts": 3,
            "backoff_multiplier": 2,
            "base_delay_ms": 100,
            "max_delay_ms": 5000
        },
        "validation_rules": {
            "strict_mode": False,
            "allow_unknown_fields": True,
            "max_request_size_mb": 10,
            "require_authentication": True
        },
        "routing": {
            "load_balancing_strategy": "round_robin",  # round_robin, least_connections, weighted
            "health_check_interval_ms": 30000,
            "failed_requests_threshold": 5
        }
    },

    # HOT RELOAD: Feature Toggles
    "features": {
        "enable_debug_logging": False,
        "enable_performance_metrics": True,
        "enable_request_tracing": False,
        "enable_circuit_breaker": True,
        "enable_health_checks": True,
        "enable_cors": True,
        "enable_compression": True,
        "enable_websocket": True,
        "enable_suho_binary_protocol": True,
        "enable_client_mt5_integration": True,
        "enable_hot_reload": True,
        "maintenance_mode": False,
        "enable_new_routing_algorithm": True
    },

    # HOT RELOAD: API Gateway Specific Settings
    "api_gateway": {
        "ports": {
            "http": 8000,
            "https": 8001,
            "websocket": 8002
        },
        "cors": {
            "allowed_origins": ["*"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["*"],
            "max_age_seconds": 86400
        },
        "websocket": {
            "max_connections": 1000,
            "message_size_limit": 65536,
            "ping_interval_ms": 30000,
            "pong_timeout_ms": 5000
        },
        "suho_binary_protocol": {
            "enabled": True,
            "compression": True,
            "encryption": False,  # Enable in production
            "version": "1.0.0"
        }
    },

    # HOT RELOAD: Trading Integration
    "trading": {
        "max_concurrent_orders": 100,
        "position_size_limits": {
            "forex": 1000000,
            "crypto": 50000,
            "stocks": 500000,
            "commodities": 200000
        },
        "market_data": {
            "update_frequency_ms": 100,
            "depth_levels": 10,
            "history_retention_hours": 24
        },
        "client_mt5": {
            "max_connections": 50,
            "heartbeat_interval_ms": 30000,
            "order_timeout_ms": 10000
        }
    },

    # HOT RELOAD: Performance Tuning
    "performance": {
        "thread_pool_size": 10,
        "connection_pool_size": 20,
        "cache_ttl_seconds": 300,
        "batch_size": 100,
        "memory_limit_mb": 512,
        "cpu_limit_percent": 80,
        "request_queue_size": 1000
    },

    # HOT RELOAD: Monitoring & Alerting
    "monitoring": {
        "metrics_enabled": True,
        "alert_thresholds": {
            "error_rate_percent": 5.0,
            "response_time_p95_ms": 1000,
            "response_time_p99_ms": 2000,
            "memory_usage_percent": 80.0,
            "cpu_usage_percent": 70.0,
            "active_connections": 800,
            "queue_depth": 500
        },
        "log_levels": {
            "root": "INFO",
            "business": "DEBUG",
            "performance": "WARN",
            "trading": "INFO",
            "websocket": "WARN",
            "suho_binary": "INFO"
        },
        "metrics_export": {
            "prometheus_enabled": True,
            "prometheus_port": 9090,
            "export_interval_seconds": 30
        }
    },

    # HOT RELOAD: Security Settings
    "security": {
        "jwt": {
            "token_expiry_minutes": 60,
            "refresh_token_expiry_hours": 24,
            "algorithm": "HS256"
        },
        "api_keys": {
            "rotation_interval_days": 30,
            "max_requests_per_key": 10000
        },
        "ssl_tls": {
            "min_version": "TLS1.2",
            "cipher_suites": ["ECDHE-RSA-AES128-GCM-SHA256"],
            "hsts_enabled": True
        }
    },

    # STATIC REFERENCES: Infrastructure (Environment Variables)
    "static_references": {
        "database_url": "ENV:DATABASE_URL",
        "cache_url": "ENV:CACHE_URL",
        "nats_url": "ENV:NATS_URL",
        "kafka_brokers": "ENV:KAFKA_BROKERS",
        "central_hub_url": "ENV:CENTRAL_HUB_URL",
        "jwt_secret": "ENV:JWT_SECRET",
        "api_keys": "ENV:API_KEYS",
        "ssl_cert_path": "ENV:SSL_CERT_PATH",
        "ssl_key_path": "ENV:SSL_KEY_PATH",
        "database_service_url": "ENV:DATABASE_SERVICE_URL"
    },

    # INFRASTRUCTURE: Database Service Integration
    "infrastructure": {
        "database": {
            # Primary database connection via Database Service
            "primary": {
                "service_name": "database-service",
                "host": "ENV:POSTGRES_HOST",
                "port": "ENV:POSTGRES_PORT",
                "name": "ENV:POSTGRES_DB",
                "user": "ENV:POSTGRES_USER",
                "password": "ENV:POSTGRES_PASSWORD",
                "schema": "public",
                "ssl_mode": "prefer",
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "connection_string": "ENV:DATABASE_URL"
            },

            # Read-only connection for analytics queries
            "read_only": {
                "enabled": False,
                "host": "ENV:POSTGRES_READ_HOST",
                "port": "ENV:POSTGRES_READ_PORT",
                "name": "ENV:POSTGRES_DB",
                "user": "ENV:POSTGRES_READ_USER",
                "password": "ENV:POSTGRES_READ_PASSWORD",
                "pool_size": 5,
                "max_overflow": 10
            },

            # Connection health monitoring
            "health_check": {
                "enabled": True,
                "interval": 30,  # seconds
                "timeout": 5,    # seconds
                "retry_count": 3,
                "circuit_breaker": True,
                "health_endpoint": "/health/database"
            }
        },

        # Message Queue Integration
        "messaging": {
            "nats": {
                "servers": ["ENV:NATS_URL"],
                "cluster_id": "suho-cluster",
                "client_id": "api-gateway",
                "subjects": {
                    "database_health": "suho.database.health",
                    "api_requests": "suho.api.requests",
                    "trading_orders": "suho.trading.orders"
                }
            },
            "kafka": {
                "brokers": "ENV:KAFKA_BROKERS",
                "topics": {
                    "market_data": "suho.market.data",
                    "trade_events": "suho.trade.events",
                    "user_activities": "suho.user.activities"
                }
            }
        },

        # Service Discovery
        "service_discovery": {
            "enabled": True,
            "registry_url": "ENV:CENTRAL_HUB_URL",
            "health_check_interval": 30,
            "service_timeout": 5000,
            "retry_attempts": 3
        }
    },

    # Configuration Metadata
    "config_meta": {
        "version": "2.0.0",
        "last_updated": "2025-09-29T18:45:00Z",
        "updated_by": "platform-team",
        "hot_reload_enabled": True,
        "validation_schema": "api_gateway_config_v2",
        "dependencies": ["central-hub", "nats", "kafka"]
    }
}

# API Gateway Specific Validation Rules
VALIDATION_RULES_API_GATEWAY = {
    "required_fields": [
        "service_info.name",
        "service_info.version",
        "api_gateway.ports.http",
        "business_rules.rate_limiting.requests_per_minute",
        "features.enable_health_checks",
        "trading.max_concurrent_orders"
    ],
    "numeric_ranges": {
        "api_gateway.ports.http": (8000, 8999),
        "api_gateway.ports.websocket": (8000, 8999),
        "business_rules.rate_limiting.requests_per_minute": (1, 100000),
        "business_rules.timeouts.request_timeout_ms": (1000, 300000),
        "trading.max_concurrent_orders": (1, 1000),
        "performance.thread_pool_size": (1, 100),
        "performance.memory_limit_mb": (128, 8192)
    },
    "allowed_values": {
        "service_info.environment": ["development", "staging", "production"],
        "business_rules.routing.load_balancing_strategy": ["round_robin", "least_connections", "weighted"],
        "security.jwt.algorithm": ["HS256", "HS384", "HS512", "RS256"],
        "monitoring.log_levels.root": ["DEBUG", "INFO", "WARN", "ERROR"]
    }
}

def validate_api_gateway_config(config):
    """
    Validate API Gateway specific configuration
    Returns: (is_valid: bool, errors: list)
    """
    from templates.service_config_template import _get_nested_value

    errors = []

    # Check required fields
    for field_path in VALIDATION_RULES_API_GATEWAY["required_fields"]:
        if not _get_nested_value(config, field_path):
            errors.append(f"Required field missing: {field_path}")

    # Check numeric ranges
    for field_path, (min_val, max_val) in VALIDATION_RULES_API_GATEWAY["numeric_ranges"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and not (min_val <= value <= max_val):
            errors.append(f"Value out of range for {field_path}: {value} (should be {min_val}-{max_val})")

    # Check allowed values
    for field_path, allowed in VALIDATION_RULES_API_GATEWAY["allowed_values"].items():
        value = _get_nested_value(config, field_path)
        if value is not None and value not in allowed:
            errors.append(f"Invalid value for {field_path}: {value} (allowed: {allowed})")

    # Custom validation for API Gateway
    http_port = _get_nested_value(config, "api_gateway.ports.http")
    ws_port = _get_nested_value(config, "api_gateway.ports.websocket")
    if http_port and ws_port and http_port == ws_port:
        errors.append("HTTP and WebSocket ports cannot be the same")

    return len(errors) == 0, errors

# Export for hot reload system
__all__ = ['CONFIG_API_GATEWAY', 'VALIDATION_RULES_API_GATEWAY', 'validate_api_gateway_config']