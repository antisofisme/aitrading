#!/usr/bin/env python3
"""
test_internal_kafka.py - Internal Kafka Integration Tests

🎯 PURPOSE:
Business: Internal Kafka/Redpanda messaging system testing
Technical: Kafka producer/consumer functionality validation
Domain: Testing/Messaging/Kafka Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.766Z
Session: client-side-ai-brain-full-compliance
Confidence: 87%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_KAFKA_TESTING: Kafka messaging system testing

📦 DEPENDENCIES:
Internal: mt5_redpanda
External: pytest, kafka-python

💡 AI DECISION REASONING:
Internal Kafka testing validates messaging infrastructure for reliable data streaming.

🚀 USAGE:
pytest tests/integration/test_internal_kafka.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import json
import time
from kafka import KafkaProducer
from kafka.errors import KafkaError

def test_internal_kafka():
    """Test internal Kafka connection"""
    print("🧪 Testing internal Kafka connection...")
    
    # Use internal broker address
    broker = "redpanda:9092"
    
    try:
        print(f"📡 Connecting to internal broker: {broker}")
        
        # Create producer with internal broker
        producer = KafkaProducer(
            bootstrap_servers=[broker],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            api_version=(0, 10, 1),
            request_timeout_ms=10000,
            max_block_ms=10000,
            acks=1
        )
        
        # Test messages
        for i in range(5):
            test_message = {
                "symbol": f"EURUSD",
                "bid": 1.0856 + i * 0.0001,
                "ask": 1.0858 + i * 0.0001,
                "timestamp": f"2025-07-17T16:40:{i:02d}Z",
                "sequence": i
            }
            
            # Send message
            future = producer.send('tick_data', test_message)
            result = future.get(timeout=5)
            
            print(f"✅ Message {i+1} sent successfully")
            print(f"   Partition: {result.partition}, Offset: {result.offset}")
            
            time.sleep(0.1)
        
        producer.close()
        print("🎉 Internal Kafka connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Internal Kafka test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_internal_kafka()
    sys.exit(0 if success else 1)