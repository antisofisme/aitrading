"""
Manual Test for Dukascopy Tick Routing
Publishes test tick with source='dukascopy_historical' to NATS
Verifies it arrives in ClickHouse ticks table
"""
import asyncio
import json
from datetime import datetime, timezone
from nats.aio.client import Client as NATS


async def test_dukascopy_routing():
    """
    Test that Dukascopy ticks are routed to ClickHouse

    Steps:
    1. Connect to NATS cluster
    2. Publish test tick with source='dukascopy_historical'
    3. Wait for data bridge to process
    4. Query ClickHouse to verify tick was saved
    """

    # Connect to NATS
    nc = NATS()
    await nc.connect(servers=[
        "nats://localhost:4222",
        "nats://localhost:4223",
        "nats://localhost:4224"
    ])

    print("✅ Connected to NATS cluster")

    # Create test tick (Dukascopy format)
    test_tick = {
        "source": "dukascopy_historical",  # CRITICAL: This triggers ClickHouse routing
        "symbol": "EUR/USD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bid": 1.08450,
        "ask": 1.08452,
        "mid": 1.08451,
        "spread": 0.00002,
        "volume": 1000,
        "flags": 0
    }

    # Publish to NATS (subject: market.ticks.{symbol})
    subject = "market.ticks.EUR/USD"
    message = json.dumps(test_tick).encode()

    await nc.publish(subject, message)
    print(f"✅ Published test tick to {subject}")
    print(f"📋 Tick data: {json.dumps(test_tick, indent=2)}")

    # Wait for data bridge to process
    print("\n⏳ Waiting 15 seconds for data bridge to process...")
    await asyncio.sleep(15)

    await nc.close()
    print("✅ NATS connection closed")

    print("\n" + "="*80)
    print("VERIFICATION STEPS:")
    print("="*80)
    print("\n1. Check ClickHouse for Dukascopy tick:")
    print("   docker exec suho-clickhouse clickhouse-client --user suho_analytics \\")
    print("     --password clickhouse_secure_2024 \\")
    print("     --query \"SELECT * FROM suho_analytics.ticks WHERE symbol = 'EUR/USD' ORDER BY timestamp DESC LIMIT 5\"")

    print("\n2. Check TimescaleDB (should NOT have this tick):")
    print("   docker exec suho-postgresql psql -U suho_admin -d suho_trading \\")
    print("     -c \"SELECT symbol, timestamp, source FROM market_ticks WHERE symbol = 'EUR/USD' ORDER BY timestamp DESC LIMIT 5;\"")

    print("\n3. Check data bridge logs:")
    print("   docker logs backend-data-bridge-1 --tail 100 | grep -E '(dukascopy|ClickHouse|_save_tick)'")

    print("\n" + "="*80)
    print("Expected Result:")
    print("  ✅ Tick appears in ClickHouse ticks table")
    print("  ✅ Tick does NOT appear in TimescaleDB market_ticks table")
    print("  ✅ Data bridge logs show: 'Saved X ticks to ClickHouse'")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_dukascopy_routing())
