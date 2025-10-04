"""
Quick Test - Critical Macro Symbols Only
"""
import requests

API_KEY = "6b8c86ca6dd04b53b559bdaf6cb61783"
BASE_URL = "https://api.twelvedata.com"

# Test only critical symbols
SYMBOLS_TO_TEST = [
    "DXY",      # Dollar Index
    "SPX",      # S&P 500
    "VIX",      # Volatility
    "XAG/USD",  # Silver (should work, similar to XAU/USD)
    "BTC/USD",  # Bitcoin
]

print("Testing critical macro symbols...")
print("=" * 60)

for symbol in SYMBOLS_TO_TEST:
    try:
        url = f"{BASE_URL}/quote"
        params = {"symbol": symbol, "apikey": API_KEY}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "name" in data:
            print(f"✅ {symbol:<10} → {data['name']}")
            print(f"   Price: {data.get('close', 'N/A')}")
        else:
            print(f"❌ {symbol:<10} → Not found or error")
            if "message" in data:
                print(f"   {data['message']}")

    except Exception as e:
        print(f"❌ {symbol:<10} → Error: {e}")

    print()

print("=" * 60)
print("Test completed")
