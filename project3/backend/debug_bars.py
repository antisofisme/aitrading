#!/usr/bin/env python3
"""
Debug script to check if bars are reaching ClickHouse
"""
from clickhouse_driver import Client
from datetime import datetime, date

# Connect to ClickHouse
client = Client(
    host='localhost',  # Using localhost (WSL should map to Docker)
    port=9000,
    database='suho_analytics',
    user='suho_analytics',
    password='clickhouse_secure_2024'
)

print("=" * 80)
print("CHECKING BARS IN CLICKHOUSE")
print("=" * 80)

# Check 1: Total bars for XAU/USD 5m
print("\n1. Total bars for XAU/USD 5m:")
query1 = """
SELECT COUNT(*) as total
FROM live_aggregates
WHERE symbol = 'XAU/USD'
  AND timeframe = '5m'
"""
result = client.execute(query1)
print(f"   Total: {result[0][0]} bars")

# Check 2: Date range
print("\n2. Date range for XAU/USD 5m:")
query2 = """
SELECT
    MIN(toDate(time)) as earliest_date,
    MAX(toDate(time)) as latest_date
FROM live_aggregates
WHERE symbol = 'XAU/USD'
  AND timeframe = '5m'
"""
result = client.execute(query2)
if result and result[0][0]:
    print(f"   Earliest: {result[0][0]}")
    print(f"   Latest: {result[0][1]}")
else:
    print("   No data found")

# Check 3: Check for 2015-01-01 specifically
print("\n3. Bars for 2015-01-01:")
query3 = """
SELECT COUNT(*) as cnt
FROM live_aggregates
WHERE symbol = 'XAU/USD'
  AND timeframe = '5m'
  AND toDate(time) = '2015-01-01'
"""
result = client.execute(query3)
print(f"   Count: {result[0][0]} bars")

# Check 4: Recent insertions
print("\n4. Recent insertions (last 10 minutes):")
query4 = """
SELECT
    symbol,
    timeframe,
    toDate(time) as date,
    COUNT(*) as bars,
    MAX(created_at) as latest_insert
FROM live_aggregates
WHERE created_at >= now() - INTERVAL 10 MINUTE
GROUP BY symbol, timeframe, date
ORDER BY latest_insert DESC
LIMIT 10
"""
result = client.execute(query4)
if result:
    for row in result:
        print(f"   {row[0]} {row[1]} {row[2]}: {row[3]} bars @ {row[4]}")
else:
    print("   No recent insertions")

# Check 5: All unique symbols
print("\n5. All unique symbols in live_aggregates:")
query5 = """
SELECT DISTINCT symbol
FROM live_aggregates
ORDER BY symbol
"""
result = client.execute(query5)
if result:
    for row in result:
        print(f"   - {row[0]}")
else:
    print("   No symbols found")

print("\n" + "=" * 80)
