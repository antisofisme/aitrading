"""
Redpanda Streaming Platform Schemas
Kafka-compatible streaming platform for real-time data processing
"""

from .streaming_schemas import RedpandaStreamingSchemas

# Create unified redpanda schemas class
class RedpandaSchemas:
    """Unified redpanda schemas access"""
    RedpandaStreaming = RedpandaStreamingSchemas

__all__ = [
    "RedpandaSchemas",
   
    "RedpandaStreamingSchemas"
]