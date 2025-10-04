"""
Test Twelve Data API - Cek Limit dan Capabilities
"""
import requests
import json
import time

API_KEY = "6b8c86ca6dd04b53b559bdaf6cb61783"
BASE_URL = "https://api.twelvedata.com"

print("=" * 70)
print("TWELVE DATA API TEST")
print("=" * 70)

# Test 1: Get API Usage/Plan Info
print("\n[TEST 1] Checking API Plan & Usage...")
try:
    response = requests.get(
        f"{BASE_URL}/api_usage",
        params={"apikey": API_KEY},
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Plan Info:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Get Single Quote (REST API)
print("\n[TEST 2] Getting Single Quote (EUR/USD)...")
try:
    response = requests.get(
        f"{BASE_URL}/quote",
        params={
            "symbol": "EUR/USD",
            "apikey": API_KEY
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Quote Data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Get Multiple Quotes (Test Rate Limit)
print("\n[TEST 3] Getting Multiple Quotes (Testing Rate Limit)...")
symbols = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD", "USD/CHF", "XAU/USD", "EUR/GBP"]

for i, symbol in enumerate(symbols, 1):
    try:
        print(f"\n  Request {i}/9: {symbol}...", end=" ")
        response = requests.get(
            f"{BASE_URL}/quote",
            params={
                "symbol": symbol,
                "apikey": API_KEY
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data.get('close', 'N/A')}")
        elif response.status_code == 429:
            print(f"⚠️ RATE LIMIT! (After {i} requests)")
            print(f"   Response: {response.text}")
            break
        else:
            print(f"❌ {response.status_code}: {response.text}")

        # Small delay to avoid hitting rate limit too fast
        time.sleep(1)

    except Exception as e:
        print(f"❌ Exception: {e}")

# Test 4: Test WebSocket Info
print("\n[TEST 4] Checking WebSocket Availability...")
try:
    # Try to get WebSocket token or info
    response = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": "EUR/USD",
            "interval": "1min",
            "outputsize": 1,
            "apikey": API_KEY
        },
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Time Series available")
        # Check for WebSocket info in response
        if 'meta' in data:
            print(f"Meta info: {json.dumps(data['meta'], indent=2)}")
    else:
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 5: Check Available Markets
print("\n[TEST 5] Checking Available Forex Pairs...")
try:
    response = requests.get(
        f"{BASE_URL}/forex_pairs",
        params={"apikey": API_KEY},
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if 'data' in data:
            total = len(data['data'])
            print(f"✅ Total Forex Pairs Available: {total}")
            print(f"First 10 pairs:")
            for pair in data['data'][:10]:
                print(f"  - {pair.get('symbol')}: {pair.get('currency_base')}/{pair.get('currency_quote')}")
        else:
            print(f"Data: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 6: Check Earliest Timestamp (Historical Data)
print("\n[TEST 6] Checking Historical Data Availability...")
try:
    response = requests.get(
        f"{BASE_URL}/earliest_timestamp",
        params={
            "symbol": "EUR/USD",
            "interval": "1day",
            "apikey": API_KEY
        },
        timeout=10
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Earliest Data:")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)

print("\n📋 SUMMARY:")
print("1. Check API plan info above to see your limits")
print("2. Rate limit test shows how many requests before hitting limit")
print("3. WebSocket availability will show if you can use real-time streaming")
print("4. If rate limit hits after ~8 requests, that's your 8 req/min limit")
print("5. For WebSocket symbols limit, need to test actual WebSocket connection")
