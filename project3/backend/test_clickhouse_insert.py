#!/usr/bin/env python3
"""
Test ClickHouse aggregates insertion with new schema
"""
from clickhouse_driver import Client
from datetime import datetime

# Connect to ClickHouse
client = Client(
    host='localhost',
    port=9000,
    user='suho_analytics',
    password='clickhouse_secure_2024',
    database='suho_analytics'
)

# Test data matching the schema
test_data = [
    (
        'EUR/USD',                              # symbol
        '1m',                                   # timeframe
        datetime(2024, 1, 26, 13, 30, 0),      # timestamp
        1706275800000,                          # timestamp_ms
        1.0845,                                 # open
        1.0855,                                 # high
        1.0840,                                 # low
        1.0850,                                 # close
        12345,                                  # volume
        1.0847,                                 # vwap
        15.0,                                   # range_pips
        5.0,                                    # body_pips
        datetime(2024, 1, 26, 13, 30, 0),      # start_time
        datetime(2024, 1, 26, 13, 31, 0),      # end_time
        'polygon_historical',                   # source
        'ohlcv'                                 # event_type
    ),
    (
        'XAU/USD',
        '1m',
        datetime(2024, 1, 26, 13, 31, 0),
        1706275860000,
        2045.50,
        2046.80,
        2045.10,
        2046.30,
        8523,
        2046.00,
        17.0,
        8.0,
        datetime(2024, 1, 26, 13, 31, 0),
        datetime(2024, 1, 26, 13, 32, 0),
        'polygon_historical',
        'ohlcv'
    )
]

# Insert test data
print("📤 Inserting test data...")
insert_sql = """
    INSERT INTO aggregates
    (symbol, timeframe, timestamp, timestamp_ms, open, high, low, close,
     volume, vwap, range_pips, body_pips, start_time, end_time, source, event_type)
    VALUES
"""

try:
    client.execute(insert_sql, test_data)
    print(f"✅ Inserted {len(test_data)} test records")
except Exception as e:
    print(f"❌ Insert failed: {e}")
    raise

# Verify inserted data
print("\n📊 Querying inserted data...")
result = client.execute("""
    SELECT
        symbol,
        timeframe,
        timestamp,
        open,
        high,
        low,
        close,
        volume,
        range_pips,
        body_pips,
        source
    FROM aggregates
    ORDER BY timestamp DESC
    LIMIT 10
""")

print(f"\n✅ Found {len(result)} records:")
for row in result:
    print(f"   {row[0]} | {row[1]} | {row[2]} | O:{row[3]} H:{row[4]} L:{row[5]} C:{row[6]} | V:{row[7]} | R:{row[8]} B:{row[9]} | {row[10]}")

# Check table stats
stats = client.execute("""
    SELECT
        count() as total_rows,
        uniq(symbol) as unique_symbols,
        min(timestamp) as earliest,
        max(timestamp) as latest
    FROM aggregates
""")

print(f"\n📈 Table Statistics:")
print(f"   Total Rows: {stats[0][0]}")
print(f"   Unique Symbols: {stats[0][1]}")
print(f"   Earliest: {stats[0][2]}")
print(f"   Latest: {stats[0][3]}")

print("\n✅ Schema verification complete!")
