"""
Deduplication logic for complementary NATS+Kafka pattern
"""
import logging
from typing import Set, Dict
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Deduplicator:
    """
    Deduplicate messages received from both NATS and Kafka

    Strategy:
    1. L1 Cache: In-memory LRU cache (10k entries, 1 hour TTL)
    2. Prevents duplicate processing from NATS + Kafka complementary pattern

    Message ID Format: "{symbol}:{timestamp_ms}:{event_type}"
    Example: "EURUSD:1727996400000:tick"
    """

    def __init__(self, config: Dict):
        self.enabled = config.get('enabled', True)
        self.cache_size = config.get('cache_size', 10000)
        self.cache_ttl_seconds = config.get('cache_ttl_seconds', 3600)

        # LRU cache using OrderedDict
        self._cache: OrderedDict[str, datetime] = OrderedDict()

        # Statistics
        self.total_checked = 0
        self.total_duplicates = 0
        self.cache_hits = 0

        logger.info(f"Deduplicator initialized: enabled={self.enabled}, cache_size={self.cache_size}")

    def generate_message_id(self, data: dict) -> str:
        """
        Generate unique message ID from data

        Format: "{symbol}:{timestamp_ms}:{event_type}"
        """
        symbol = data.get('symbol', '').replace('/', '')  # EUR/USD → EURUSD
        timestamp_ms = data.get('timestamp_ms', 0)
        event_type = data.get('event_type', 'unknown')

        return f"{symbol}:{timestamp_ms}:{event_type}"

    def is_duplicate(self, message_id: str, source: str = "unknown") -> bool:
        """
        Check if message has already been processed

        Args:
            message_id: Unique message identifier
            source: "nats" or "kafka"

        Returns:
            True if duplicate, False if new message
        """
        if not self.enabled:
            return False

        self.total_checked += 1

        # Check L1 cache (in-memory)
        if message_id in self._cache:
            self.cache_hits += 1
            self.total_duplicates += 1

            # Update access time (move to end for LRU)
            self._cache.move_to_end(message_id)

            logger.debug(f"Duplicate message from {source}: {message_id}")
            return True

        # New message - add to cache
        self._cache[message_id] = datetime.utcnow()

        # Evict old entries (LRU)
        if len(self._cache) > self.cache_size:
            # Remove oldest
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        # Clean expired entries periodically
        if self.total_checked % 1000 == 0:
            self._clean_expired()

        return False

    def _clean_expired(self):
        """Remove expired entries from cache"""
        cutoff = datetime.utcnow() - timedelta(seconds=self.cache_ttl_seconds)

        expired_keys = [
            key for key, timestamp in self._cache.items()
            if timestamp < cutoff
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")

    def mark_processed(self, data: dict, source: str):
        """
        Mark message as processed (add to cache)

        Args:
            data: Message data
            source: "nats" or "kafka"
        """
        message_id = self.generate_message_id(data)
        self._cache[message_id] = datetime.utcnow()

        # Enforce cache size limit
        if len(self._cache) > self.cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

    def get_stats(self) -> dict:
        """Get deduplication statistics"""
        duplicate_rate = self.total_duplicates / self.total_checked if self.total_checked > 0 else 0
        cache_hit_rate = self.cache_hits / self.total_checked if self.total_checked > 0 else 0

        return {
            'enabled': self.enabled,
            'total_checked': self.total_checked,
            'total_duplicates': self.total_duplicates,
            'duplicate_rate': round(duplicate_rate, 4),
            'cache_size': len(self._cache),
            'cache_hit_rate': round(cache_hit_rate, 4)
        }
