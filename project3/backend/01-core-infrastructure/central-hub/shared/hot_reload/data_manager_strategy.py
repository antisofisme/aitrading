"""
Data Manager Hot-reload Strategy
Dynamic configuration for routing, caching, and performance tuning
Can be updated without service restart
"""

DATA_MANAGER_STRATEGY = {
    # =========================================================================
    # ROUTING RULES
    # =========================================================================
    "routing": {
        # Write operations
        "save_tick": ["timescale", "dragonfly_cache"],
        "save_candle": ["timescale", "dragonfly_cache"],
        "save_candles_bulk": ["timescale"],

        # Read operations - real-time
        "get_latest_tick": ["dragonfly_cache", "timescale"],
        "get_latest_candles": ["dragonfly_cache", "timescale"],

        # Read operations - historical (Phase 2: add ClickHouse)
        "get_historical_candles": ["timescale"],  # Will become: ["clickhouse", "timescale"]

        # Analytics operations (Phase 2: ClickHouse)
        "compute_aggregates": ["timescale"],  # Will become: ["clickhouse"]

        # AI/ML operations (Phase 3: Weaviate)
        "find_patterns": [],  # Will become: ["weaviate"]
        "similarity_search": [],  # Will become: ["weaviate"]

        # Correlation operations (Phase 3: ArangoDB)
        "get_correlations": [],  # Will become: ["arangodb"]
        "graph_analysis": []  # Will become: ["arangodb"]
    },

    # =========================================================================
    # CACHE TTL SETTINGS (seconds)
    # =========================================================================
    "cache": {
        # Tick data
        "tick_ttl_seconds": 3600,  # 1 hour (latest tick per symbol)

        # Candle data
        "candle_ttl_seconds": 3600,  # 1 hour (latest candles)

        # Historical data
        "historical_ttl_seconds": 0,  # No cache (always fresh)

        # Aggregates
        "aggregates_ttl_seconds": 300,  # 5 minutes

        # Patterns (AI/ML)
        "patterns_ttl_seconds": 0,  # No cache (always compute)

        # Correlations
        "correlations_ttl_seconds": 3600,  # 1 hour

        # L1 cache settings
        "l1_max_size": 1000,  # Max entries in memory
        "l1_ttl_seconds": 60,  # 1 minute in L1

        # L2 cache (DragonflyDB) default TTL
        "l2_ttl_seconds": 3600  # 1 hour in L2
    },

    # =========================================================================
    # CONNECTION POOL SETTINGS
    # =========================================================================
    "connection_pools": {
        "timescale": {
            "min_size": 5,
            "max_size": 20,
            "acquire_timeout_seconds": 30,
            "idle_timeout_seconds": 10,
            "max_queries": 50000,
            "max_inactive_connection_lifetime": 300
        },

        "clickhouse": {
            "max_connections": 10,
            "connection_timeout_seconds": 10,
            "receive_timeout_seconds": 300,
            "send_timeout_seconds": 300
        },

        "dragonfly": {
            "min_connections": 5,
            "max_connections": 50,
            "connection_timeout_seconds": 5,
            "command_timeout_seconds": 3,
            "retry_on_timeout": True
        },

        "weaviate": {
            "timeout_seconds": 30,
            "startup_period_seconds": 5
        },

        "arangodb": {
            "max_connections": 10,
            "timeout_seconds": 30
        }
    },

    # =========================================================================
    # PERFORMANCE TUNING
    # =========================================================================
    "performance": {
        # Batch operations
        "batch_size": 1000,  # Max records per batch insert
        "batch_flush_interval_seconds": 5,  # Auto-flush interval

        # Query optimization
        "query_timeout_seconds": 30,
        "enable_query_cache": True,
        "enable_prepared_statements": True,

        # Retry logic
        "retry_max_attempts": 3,
        "retry_backoff_multiplier": 2,  # 1s, 2s, 4s
        "retry_on_timeout": True,

        # Circuit breaker
        "circuit_breaker_enabled": True,
        "circuit_breaker_threshold": 5,  # Open after 5 consecutive failures
        "circuit_breaker_timeout_seconds": 60,  # Try again after 60s
        "circuit_breaker_half_open_max_calls": 1,  # Test with 1 call

        # Rate limiting (optional, per-operation)
        "rate_limit_enabled": False,
        "rate_limit_requests_per_second": 1000
    },

    # =========================================================================
    # OPTIMIZATION FLAGS
    # =========================================================================
    "optimization": {
        "enable_query_cache": True,
        "enable_prepared_statements": True,
        "enable_connection_pooling": True,
        "enable_batch_operations": True,
        "enable_multi_level_cache": True,
        "enable_async_operations": True
    },

    # =========================================================================
    # FEATURE FLAGS (for gradual rollout)
    # =========================================================================
    "features": {
        # Database features
        "timescale_enabled": True,
        "clickhouse_enabled": False,  # Phase 2
        "dragonfly_enabled": True,
        "weaviate_enabled": False,  # Phase 3
        "arangodb_enabled": False,  # Phase 3

        # Operational features
        "cache_enabled": True,
        "metrics_enabled": True,
        "debug_logging": False,
        "trace_queries": False,

        # Advanced features
        "auto_failover": True,
        "load_balancing": False,  # Future: multi-instance support
        "sharding": False  # Future: horizontal scaling
    },

    # =========================================================================
    # MONITORING & ALERTING
    # =========================================================================
    "monitoring": {
        "metrics_collection_interval_seconds": 60,
        "health_check_interval_seconds": 30,

        # Alert thresholds
        "alert_on_error_rate_percent": 5.0,
        "alert_on_latency_p95_ms": 1000,
        "alert_on_cache_hit_rate_below": 0.7,
        "alert_on_connection_pool_exhausted": True,

        # Metrics retention
        "metrics_retention_days": 7,
        "detailed_metrics_enabled": True
    },

    # =========================================================================
    # DATA VALIDATION
    # =========================================================================
    "validation": {
        "strict_mode": True,  # Fail on validation errors
        "allow_missing_fields": False,
        "auto_convert_types": True,
        "validate_timestamps": True,
        "validate_price_ranges": True,

        # Price validation ranges (for anomaly detection)
        "price_ranges": {
            "EUR/USD": {"min": 0.8, "max": 1.5},
            "GBP/USD": {"min": 1.0, "max": 2.0},
            "XAU/USD": {"min": 1000, "max": 3000}
        }
    }
}


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_routing_for_operation(operation: str) -> list:
    """Get database routing list for an operation"""
    return DATA_MANAGER_STRATEGY["routing"].get(operation, [])


def get_cache_ttl(data_type: str) -> int:
    """Get cache TTL for a data type"""
    key = f"{data_type}_ttl_seconds"
    return DATA_MANAGER_STRATEGY["cache"].get(key, 3600)


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled"""
    return DATA_MANAGER_STRATEGY["features"].get(feature, False)


def get_performance_config(key: str, default=None):
    """Get performance configuration value"""
    return DATA_MANAGER_STRATEGY["performance"].get(key, default)


# =========================================================================
# CONFIGURATION METADATA
# =========================================================================

STRATEGY_METADATA = {
    "version": "1.0.0",
    "last_updated": "2025-10-04",
    "phase": "Phase 1 - TimescaleDB + DragonflyDB",
    "next_phase": "Phase 2 - Add ClickHouse for analytics",
    "owner": "Backend Infrastructure Team",
    "hot_reload_enabled": True
}
