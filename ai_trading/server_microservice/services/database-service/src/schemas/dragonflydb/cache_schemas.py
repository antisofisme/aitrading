"""
DragonflyDB Cache Schemas - Simplified Version
High-performance caching strategies for trading data
"""

from typing import Dict, List
from enum import Enum


class CacheType(Enum):
    """Cache types for different data categories"""
    TICK_DATA = "tick_data"
    INDICATOR_DATA = "indicator_data"
    ML_RESULTS = "ml_results"
    USER_SESSION = "user_session"
    API_RESPONSE = "api_response"
    SYSTEM_CONFIG = "system_config"


class DragonflyDbCacheSchemas:
    """
    DragonflyDB caching schemas for high-performance data access
    Redis-compatible protocol with enhanced performance
    """

    @staticmethod
    def get_all_cache_patterns() -> Dict[str, Dict]:
        """Get all cache patterns and their configurations"""
        return {
            "tick_data_cache": DragonflyDbCacheSchemas.tick_data_cache(),
            "indicator_cache": DragonflyDbCacheSchemas.indicator_cache(),
            "ml_predictions_cache": DragonflyDbCacheSchemas.ml_predictions_cache(),
            "user_session_cache": DragonflyDbCacheSchemas.user_session_cache(),
            "api_response_cache": DragonflyDbCacheSchemas.api_response_cache(),
            "system_config_cache": DragonflyDbCacheSchemas.system_config_cache()
        }
    
    @staticmethod
    def get_cache_strategies() -> Dict[str, Dict]:
        """Get cache strategies for different data types"""
        return {
            "tick_data": {
                "strategy": "LRU",
                "ttl": 300,  # 5 minutes
                "max_size": "1GB",
                "eviction_policy": "allkeys-lru"
            },
            "indicator_data": {
                "strategy": "LRU", 
                "ttl": 900,  # 15 minutes
                "max_size": "500MB",
                "eviction_policy": "volatile-lru"
            },
            "ml_predictions": {
                "strategy": "TTL",
                "ttl": 1800,  # 30 minutes
                "max_size": "2GB",
                "eviction_policy": "volatile-ttl"
            },
            "user_sessions": {
                "strategy": "TTL",
                "ttl": 86400,  # 24 hours
                "max_size": "100MB",
                "eviction_policy": "volatile-ttl"
            },
            "api_responses": {
                "strategy": "LRU",
                "ttl": 60,  # 1 minute
                "max_size": "200MB",
                "eviction_policy": "allkeys-lru"
            }
        }

    @staticmethod
    def tick_data_cache() -> Dict:
        """Cache configuration for tick data"""
        return {
            "key_pattern": "tick:${symbol}:${timestamp}",
            "ttl": 300,
            "data_structure": "hash",
            "fields": ["bid", "ask", "volume", "spread", "timestamp"],
            "compression": "gzip",
            "priority": "high"
        }

    @staticmethod
    def indicator_cache() -> Dict:
        """Cache configuration for indicator data"""
        return {
            "key_pattern": "indicator:${symbol}:${indicator}:${timeframe}",
            "ttl": 900,
            "data_structure": "string", 
            "compression": "lz4",
            "priority": "medium"
        }

    @staticmethod
    def ml_predictions_cache() -> Dict:
        """Cache configuration for ML predictions"""
        return {
            "key_pattern": "ml:${model}:${symbol}:${prediction_id}",
            "ttl": 1800,
            "data_structure": "json",
            "compression": "gzip",
            "priority": "high"
        }

    @staticmethod
    def user_session_cache() -> Dict:
        """Cache configuration for user sessions"""
        return {
            "key_pattern": "session:${user_id}:${session_id}",
            "ttl": 86400,
            "data_structure": "hash",
            "fields": ["user_id", "broker", "account_type", "login_time"],
            "priority": "low"
        }

    @staticmethod
    def api_response_cache() -> Dict:
        """Cache configuration for API responses"""
        return {
            "key_pattern": "api:${endpoint}:${params_hash}",
            "ttl": 60,
            "data_structure": "string",
            "compression": "gzip",
            "priority": "medium"
        }

    @staticmethod
    def system_config_cache() -> Dict:
        """Cache configuration for system config"""
        return {
            "key_pattern": "config:${service}:${config_key}",
            "ttl": 3600,
            "data_structure": "string",
            "priority": "high"
        }