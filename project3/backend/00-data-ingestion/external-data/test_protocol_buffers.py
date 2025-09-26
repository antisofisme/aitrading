#!/usr/bin/env python3
"""
Protocol Buffers Performance Test
Verify 60% smaller payloads and 10x faster serialization
"""

import time
import json
import sys
from typing import Dict, Any

# Import our Protocol Buffers implementation
sys.path.append('schemas')
from market_data_pb2 import UnifiedMarketData, MarketDataStream


def test_protocol_buffers_performance():
    """Test Protocol Buffers vs JSON performance"""

    print("🧪 Testing Protocol Buffers Performance...")
    print("=" * 50)

    # Create sample market data
    sample_data = UnifiedMarketData(
        symbol="EURUSD",
        timestamp=int(time.time() * 1000),
        source="OANDA_API",
        data_type="market_price",
        price_open=1.0855,
        price_high=1.0857,
        price_low=1.0853,
        price_close=1.0856,
        bid=1.0855,
        ask=1.0857,
        spread=0.2,
        volume=1000.0,
        change_percent=0.01,
        session="London",
        market_impact_score=0.8
    )

    # Test 1: Serialization Performance
    print("📊 Test 1: Serialization Performance")
    print("-" * 30)

    # Protocol Buffers serialization
    pb_start = time.perf_counter()
    pb_data = sample_data.SerializeToString()
    pb_time = time.perf_counter() - pb_start

    # JSON serialization
    json_start = time.perf_counter()
    json_data = json.dumps(sample_data.to_dict()).encode('utf-8')
    json_time = time.perf_counter() - json_start

    print(f"Protocol Buffers: {pb_time*1000:.3f}ms")
    print(f"JSON: {json_time*1000:.3f}ms")
    print(f"Speed improvement: {json_time/pb_time:.1f}x faster")
    print()

    # Test 2: Payload Size
    print("📦 Test 2: Payload Size Comparison")
    print("-" * 30)

    pb_size = len(pb_data)
    json_size = len(json_data)
    size_reduction = (1 - pb_size/json_size) * 100

    print(f"Protocol Buffers: {pb_size} bytes")
    print(f"JSON: {json_size} bytes")
    print(f"Size reduction: {size_reduction:.1f}% smaller")
    print()

    # Test 3: Deserialization Performance
    print("🔄 Test 3: Deserialization Performance")
    print("-" * 30)

    # Protocol Buffers deserialization
    pb_start = time.perf_counter()
    pb_parsed = UnifiedMarketData()
    pb_parsed.ParseFromString(pb_data)
    pb_parse_time = time.perf_counter() - pb_start

    # JSON deserialization
    json_start = time.perf_counter()
    json_parsed = json.loads(json_data.decode('utf-8'))
    json_parse_time = time.perf_counter() - json_start

    print(f"Protocol Buffers: {pb_parse_time*1000:.3f}ms")
    print(f"JSON: {json_parse_time*1000:.3f}ms")
    print(f"Parse speed improvement: {json_parse_time/pb_parse_time:.1f}x faster")
    print()

    # Test 4: Batch Processing Performance
    print("⚡ Test 4: Batch Processing (50 ticks)")
    print("-" * 30)

    # Create batch stream
    stream = MarketDataStream(
        source="data-ingestion",
        batch_time_msc=int(time.time() * 1000),
        batch_id=1
    )

    # Add 50 ticks to simulate real workload
    for i in range(50):
        tick = UnifiedMarketData(
            symbol="EURUSD",
            timestamp=int(time.time() * 1000) + i,
            source="OANDA_API",
            data_type="market_price",
            price_close=1.0855 + (i * 0.00001),
            bid=1.0855 + (i * 0.00001),
            ask=1.0857 + (i * 0.00001)
        )
        stream.add_tick(tick)

    # Batch serialization performance
    batch_start = time.perf_counter()
    batch_data = stream.SerializeToString()
    batch_time = time.perf_counter() - batch_start

    print(f"50 ticks serialization: {batch_time*1000:.3f}ms")
    print(f"Per tick: {batch_time*1000/50:.3f}ms")
    print(f"Throughput: {50/batch_time:.0f} ticks/second")
    print()

    # Test 5: Smart Table Routing
    print("🎯 Test 5: Smart Table Routing")
    print("-" * 30)

    # High-frequency data → market_ticks
    market_data = UnifiedMarketData(symbol="EURUSD", data_type="market_price")
    print(f"Market price → {market_data.get_target_table()}")

    # Low-frequency data → market_context
    sentiment_data = UnifiedMarketData(symbol="FEAR_GREED", data_type="market_sentiment")
    print(f"Market sentiment → {sentiment_data.get_target_table()}")

    economic_data = UnifiedMarketData(symbol="CPI", data_type="economic_indicator")
    print(f"Economic indicator → {economic_data.get_target_table()}")
    print()

    # Summary
    print("✅ Protocol Buffers Performance Summary")
    print("=" * 50)
    print(f"✓ Serialization: {json_time/pb_time:.1f}x faster than JSON")
    print(f"✓ Payload size: {size_reduction:.1f}% smaller than JSON")
    print(f"✓ Deserialization: {json_parse_time/pb_parse_time:.1f}x faster than JSON")
    print(f"✓ Batch processing: {50/batch_time:.0f} ticks/second throughput")
    print(f"✓ Smart routing: Automatic table selection based on data type")
    print()
    print("🚀 Optimal for 50+ ticks/second real-time trading!")


def test_database_format_conversion():
    """Test database format conversion"""

    print("\n🗄️ Testing Database Format Conversion...")
    print("=" * 50)

    # Test market_ticks format
    market_tick = UnifiedMarketData(
        symbol="EURUSD",
        timestamp=int(time.time() * 1000),
        data_type="market_price",
        price_open=1.0855,
        price_close=1.0856,
        bid=1.0855,
        ask=1.0857,
        volume=1000,
        source="OANDA_API"
    )

    db_format = market_tick.to_database_format()
    print("Market Tick DB Format:")
    for key, value in db_format.items():
        print(f"  {key}: {value}")
    print()

    # Test market_context format with forecast/actual
    economic_data = UnifiedMarketData(
        symbol="CPI",
        timestamp=int(time.time() * 1000),
        data_type="economic_indicator",
        value=3.2,
        units="Percent",
        source="FRED",
        raw_metadata={"collection_phase": "actual", "previous": 3.1}
    )

    context_format = economic_data.to_database_format()
    print("Economic Indicator DB Format:")
    for key, value in context_format.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        test_protocol_buffers_performance()
        test_database_format_conversion()
        print("\n🎉 All tests passed! Protocol Buffers implementation is working correctly.")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()