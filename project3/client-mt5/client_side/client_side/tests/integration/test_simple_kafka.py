#!/usr/bin/env python3
"""
test_simple_kafka.py - Simple Kafka Integration Tests

🎯 PURPOSE:
Business: Basic Kafka functionality testing and validation
Technical: Simple Kafka producer/consumer workflow testing
Domain: Testing/Kafka/Basic Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.791Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SIMPLE_KAFKA_TESTING: Basic Kafka integration testing

📦 DEPENDENCIES:
Internal: mt5_redpanda
External: pytest, kafka-python

💡 AI DECISION REASONING:
Simple Kafka testing provides basic functionality validation for streaming infrastructure.

🚀 USAGE:
pytest tests/integration/test_simple_kafka.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

def test_kafka_connection():
    """Test basic Kafka connection"""
    print("🧪 Testing Kafka connection...")
    
    # Test different server configurations
    servers = [
        "127.0.0.1:19092",
        "localhost:19092",
        "127.0.0.1:9092",
        "localhost:9092"
    ]
    
    for server in servers:
        try:
            print(f"📡 Testing connection to {server}...")
            
            # Create producer with minimal configuration
            producer = KafkaProducer(
                bootstrap_servers=[server],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                api_version=(0, 10, 1),
                request_timeout_ms=5000,
                max_block_ms=5000
            )
            
            # Test message
            test_message = {
                "symbol": "EURUSD",
                "bid": 1.0856,
                "ask": 1.0858,
                "timestamp": "2025-07-17T16:30:00Z"
            }
            
            # Send message
            future = producer.send('tick_data', test_message)
            result = future.get(timeout=10)
            
            print(f"✅ Successfully sent to {server}")
            print(f"   Topic: {result.topic}")
            print(f"   Partition: {result.partition}")
            print(f"   Offset: {result.offset}")
            
            producer.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to {server}: {e}")
            continue
    
    print("❌ All connection attempts failed")
    return False

if __name__ == "__main__":
    success = test_kafka_connection()
    sys.exit(0 if success else 1)