"""
DragonflyDB Schema Definitions
Redis-compatible cache - key-value patterns and TTL configurations
"""
from typing import Dict, List, Any


def get_dragonfly_schemas() -> List[Dict[str, Any]]:
    """Get all DragonflyDB cache patterns"""
    return [
        TICK_CACHE_PATTERN,
        CANDLE_CACHE_PATTERN,
        ANALYTICS_CACHE_PATTERN,
        SESSION_CACHE_PATTERN,
    ]


# ============================================================================
# TICK CACHE (Latest tick data)
# ============================================================================

TICK_CACHE_PATTERN = {
    "pattern": "tick:latest:{symbol}",
    "description": "Latest tick for each symbol",
    "ttl": 60,  # 1 minute
    "type": "hash",
    "fields": {
        "symbol": "string",
        "timestamp": "int",
        "bid": "float",
        "ask": "float",
        "mid": "float",
        "spread": "float",
        "source": "string",
    },
    "example": {
        "key": "tick:latest:EURUSD",
        "value": {
            "symbol": "EUR/USD",
            "timestamp": 1697123456789,
            "bid": 1.0850,
            "ask": 1.0852,
            "mid": 1.0851,
            "spread": 0.0002,
            "source": "dukascopy"
        }
    }
}


# ============================================================================
# CANDLE CACHE (Recent candles)
# ============================================================================

CANDLE_CACHE_PATTERN = {
    "pattern": "candle:latest:{symbol}:{timeframe}",
    "description": "Latest N candles for symbol+timeframe",
    "ttl": 300,  # 5 minutes
    "type": "list",
    "max_length": 100,
    "fields": {
        "timestamp": "int",
        "open": "float",
        "high": "float",
        "low": "float",
        "close": "float",
        "volume": "int",
    },
    "example": {
        "key": "candle:latest:EURUSD:5m",
        "value": [
            {"timestamp": 1697123400, "open": 1.0850, "high": 1.0855, "low": 1.0848, "close": 1.0852, "volume": 1234},
            {"timestamp": 1697123700, "open": 1.0852, "high": 1.0858, "low": 1.0850, "close": 1.0856, "volume": 1567},
        ]
    }
}


# ============================================================================
# ANALYTICS CACHE (Aggregated metrics)
# ============================================================================

ANALYTICS_CACHE_PATTERN = {
    "pattern": "analytics:{metric_type}:{symbol}:{period}",
    "description": "Cached analytics results",
    "ttl": 3600,  # 1 hour
    "type": "string",  # JSON string
    "fields": {
        "metric_type": "string",  # avg_volume, volatility, etc.
        "value": "float",
        "calculated_at": "int",
    },
    "example": {
        "key": "analytics:volatility:EURUSD:1d",
        "value": '{"metric_type": "volatility", "value": 0.0125, "calculated_at": 1697123456}'
    }
}


# ============================================================================
# SESSION CACHE (User/system sessions)
# ============================================================================

SESSION_CACHE_PATTERN = {
    "pattern": "session:{session_id}",
    "description": "User/system session data",
    "ttl": 1800,  # 30 minutes
    "type": "hash",
    "fields": {
        "user_id": "string",
        "service_name": "string",
        "created_at": "int",
        "last_activity": "int",
        "metadata": "string",  # JSON
    },
    "example": {
        "key": "session:abc123",
        "value": {
            "user_id": "user-001",
            "service_name": "tick-aggregator",
            "created_at": 1697120000,
            "last_activity": 1697123456,
            "metadata": '{"version": "1.0"}'
        }
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_cache_documentation() -> str:
    """Generate documentation for cache patterns"""
    schemas = get_dragonfly_schemas()

    doc_parts = ["""
# ===========================================================================
# DragonflyDB Cache Patterns - Auto-generated Documentation
# Generated: 2025-10-14
# Version: 2.0
# ===========================================================================

"""]

    for schema in schemas:
        doc_parts.append(f"""
## {schema['description']}

**Pattern:** `{schema['pattern']}`
**Type:** {schema['type']}
**TTL:** {schema['ttl']} seconds

**Fields:**
""")
        for field, ftype in schema['fields'].items():
            doc_parts.append(f"- `{field}`: {ftype}")

        doc_parts.append(f"\n**Example:**\n```json")
        doc_parts.append(f"Key: {schema['example']['key']}")
        doc_parts.append(f"Value: {schema['example']['value']}")
        doc_parts.append("```\n")

    return "\n".join(doc_parts)


def get_cache_pattern(pattern_name: str) -> Dict[str, Any]:
    """Get specific cache pattern by name"""
    schemas = get_dragonfly_schemas()
    for schema in schemas:
        if pattern_name.lower() in schema['pattern'].lower():
            return schema
    return {}


def get_all_cache_patterns() -> Dict[str, Dict[str, Any]]:
    """Get all cache patterns as dictionary"""
    schemas = get_dragonfly_schemas()
    return {schema['pattern']: schema for schema in schemas}
