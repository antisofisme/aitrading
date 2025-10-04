"""
Test Macro Instrument Symbol Availability on Twelve Data
"""
import requests
import time

API_KEY = "6b8c86ca6dd04b53b559bdaf6cb61783"
BASE_URL = "https://api.twelvedata.com"

# Symbols to test
MACRO_SYMBOLS = {
    # Treasury Yields
    "US10Y": "US 10-Year Treasury Yield",
    "^TNX": "US 10-Year Treasury Yield (alternative)",
    "TNX": "US 10-Year Treasury Yield (no caret)",
    "US02Y": "US 2-Year Treasury Yield",

    # Dollar Index
    "DXY": "US Dollar Index",
    "DX-Y.NYB": "US Dollar Index (alternative)",
    "USDX": "US Dollar Index (alternative 2)",

    # Stock Indices
    "SPX": "S&P 500 Index",
    "^GSPC": "S&P 500 Index (alternative)",
    "SPY": "S&P 500 ETF",

    # Volatility
    "VIX": "CBOE Volatility Index",
    "^VIX": "CBOE Volatility Index (alternative)",

    # Commodities
    "COPPER": "Copper",
    "HG": "Copper (alternative)",
    "XAG/USD": "Silver",
    "BTC/USD": "Bitcoin",
    "NG": "Natural Gas",
}

print("=" * 80)
print("TESTING MACRO SYMBOL AVAILABILITY ON TWELVE DATA")
print("=" * 80)

results = {
    "available": [],
    "not_found": [],
    "errors": []
}

for symbol, description in MACRO_SYMBOLS.items():
    print(f"\nTesting: {symbol} ({description})")

    try:
        # Test quote endpoint
        url = f"{BASE_URL}/quote"
        params = {
            "symbol": symbol,
            "apikey": API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code == 200 and "name" in data:
            print(f"  ✅ AVAILABLE")
            print(f"     Name: {data.get('name')}")
            print(f"     Price: {data.get('close', 'N/A')}")
            print(f"     Exchange: {data.get('exchange', 'N/A')}")

            results["available"].append({
                "symbol": symbol,
                "name": data.get("name"),
                "description": description,
                "price": data.get("close"),
                "exchange": data.get("exchange")
            })

        elif "code" in data and data["code"] == 404:
            print(f"  ❌ NOT FOUND")
            print(f"     Error: {data.get('message', 'Unknown')}")
            results["not_found"].append(symbol)

        else:
            print(f"  ⚠️ ERROR")
            print(f"     Response: {data}")
            results["errors"].append({
                "symbol": symbol,
                "error": data
            })

        # Rate limit: 8 per minute
        time.sleep(8)  # Wait 8 seconds between requests

    except Exception as e:
        print(f"  ❌ EXCEPTION: {e}")
        results["errors"].append({
            "symbol": symbol,
            "error": str(e)
        })

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\n✅ AVAILABLE SYMBOLS ({len(results['available'])}):")
for item in results["available"]:
    print(f"  - {item['symbol']:<15} → {item['name']}")

print(f"\n❌ NOT FOUND ({len(results['not_found'])}):")
for symbol in results["not_found"]:
    print(f"  - {symbol}")

print(f"\n⚠️ ERRORS ({len(results['errors'])}):")
for item in results["errors"]:
    print(f"  - {item['symbol']}: {item.get('error', 'Unknown')}")

# Recommendations
print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

if results["available"]:
    print("\n✅ Use these symbols in config.yaml:")
    print("```yaml")
    print("macro_instruments:")

    # Group by category
    yields = [x for x in results["available"] if "yield" in x["description"].lower() or "treasury" in x["description"].lower()]
    indices = [x for x in results["available"] if "index" in x["description"].lower() or "s&p" in x["description"].lower()]
    commodities = [x for x in results["available"] if "copper" in x["description"].lower() or "silver" in x["description"].lower() or "bitcoin" in x["description"].lower()]

    if yields:
        print("  # Treasury Yields")
        for item in yields[:2]:  # Max 2
            print(f"  - \"{item['symbol']}\"  # {item['description']}")

    if indices:
        print("\n  # Stock Indices")
        for item in indices[:2]:  # Max 2
            print(f"  - \"{item['symbol']}\"  # {item['description']}")

    if commodities:
        print("\n  # Commodities")
        for item in commodities[:3]:  # Max 3
            print(f"  - \"{item['symbol']}\"  # {item['description']}")

    print("```")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
