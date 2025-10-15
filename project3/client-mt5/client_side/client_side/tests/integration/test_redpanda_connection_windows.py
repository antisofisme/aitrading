#!/usr/bin/env python3
"""
test_redpanda_connection_windows.py - Windows Redpanda Connection Tests

🎯 PURPOSE:
Business: Windows-specific Redpanda connectivity testing
Technical: Platform-specific streaming connection validation
Domain: Testing/Windows Platform/Redpanda Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.776Z
Session: client-side-ai-brain-full-compliance
Confidence: 86%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_WINDOWS_STREAMING_TESTING: Windows-specific streaming testing

📦 DEPENDENCIES:
Internal: mt5_redpanda
External: pytest, kafka-python

💡 AI DECISION REASONING:
Windows-specific testing ensures streaming works correctly on MT5 production environments.

🚀 USAGE:
pytest tests/integration/test_redpanda_connection_windows.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import socket
import time
from datetime import datetime

def test_port_connection(host, port, timeout=5):
    """Test if a port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ Error testing {host}:{port} - {e}")
        return False

def test_redpanda_ports():
    """Test common Redpanda ports"""
    print("🧪 Testing Redpanda Server Connections")
    print("=" * 50)
    
    # Common Redpanda ports
    test_ports = [
        ("localhost", 19092, "Docker external port"),
        ("localhost", 9092, "Standard Kafka port"),
        ("127.0.0.1", 19092, "Explicit localhost external"),
        ("127.0.0.1", 9092, "Explicit localhost standard"),
        ("localhost", 18081, "Schema Registry"),
        ("localhost", 18082, "Pandaproxy"),
    ]
    
    available_servers = []
    
    for host, port, description in test_ports:
        print(f"🔍 Testing {host}:{port} ({description})...")
        
        if test_port_connection(host, port):
            print(f"✅ {host}:{port} is ACCESSIBLE")
            available_servers.append(f"{host}:{port}")
        else:
            print(f"❌ {host}:{port} is NOT ACCESSIBLE")
    
    print("\n" + "=" * 50)
    if available_servers:
        print(f"✅ Found {len(available_servers)} available Redpanda server(s):")
        for server in available_servers:
            print(f"   📡 {server}")
    else:
        print("❌ No Redpanda servers found!")
        print("💡 Make sure Docker containers are running:")
        print("   docker-compose up -d")
    
    return available_servers

def test_kafka_libraries():
    """Test if Kafka libraries are available"""
    print("\n🧪 Testing Kafka Libraries")
    print("=" * 50)
    
    # Test aiokafka
    try:
        import aiokafka
        print(f"✅ aiokafka {aiokafka.__version__} available")
    except ImportError as e:
        print(f"❌ aiokafka not available: {e}")
    
    # Test kafka-python
    try:
        import kafka
        print(f"✅ kafka-python {kafka.__version__} available")
    except ImportError as e:
        print(f"❌ kafka-python not available: {e}")

def test_kafka_connection():
    """Test actual Kafka connection"""
    print("\n🧪 Testing Kafka Connection")
    print("=" * 50)
    
    # Test servers
    servers = test_redpanda_ports()
    
    if not servers:
        print("❌ No servers available for testing")
        return
    
    # Test with kafka-python
    try:
        from kafka import KafkaProducer
        from kafka.errors import NoBrokersAvailable
        
        print(f"🔍 Testing connection with kafka-python...")
        
        producer = KafkaProducer(
            bootstrap_servers=servers,
            client_id="test_client",
            request_timeout_ms=10000,
            api_version=(0, 10, 1)
        )
        
        print("✅ kafka-python connection successful!")
        producer.close()
        
    except NoBrokersAvailable:
        print("❌ No brokers available - Redpanda server might not be running")
    except Exception as e:
        print(f"❌ kafka-python connection failed: {e}")

def main():
    """Main test function"""
    print(f"🕐 Redpanda Connection Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    test_kafka_libraries()
    test_kafka_connection()
    
    print("\n" + "=" * 70)
    print("🎉 Test completed!")
    print("💡 If no servers are available, start Docker containers:")
    print("   docker-compose up -d")

if __name__ == "__main__":
    main()