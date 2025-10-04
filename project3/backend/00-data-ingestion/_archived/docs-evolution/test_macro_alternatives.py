"""
Test Alternative Macro Symbols and ETFs
"""
import requests

API_KEY = "6b8c86ca6dd04b53b559bdaf6cb61783"
BASE_URL = "https://api.twelvedata.com"

# Alternative symbols - Try ETFs and different formats
SYMBOLS_TO_TEST = [
    # Dollar Index alternatives
    ("UUP", "US Dollar Index ETF"),
    ("USDU", "US Dollar ETF alternative"),

    # S&P 500 alternatives
    ("SPY", "S&P 500 ETF (most liquid)"),
    ("VOO", "Vanguard S&P 500 ETF"),

    # Volatility alternatives
    ("VIXY", "VIX Short-Term Futures ETF"),
    ("VXX", "VIX ETF alternative"),

    # Treasury Yield proxies
    ("TLT", "20+ Year Treasury Bond ETF"),
    ("IEF", "7-10 Year Treasury ETF"),

    # Commodities ETFs
    ("GLD", "Gold ETF (tracks XAU/USD)"),
    ("SLV", "Silver ETF (tracks XAG/USD)"),
    ("USO", "US Oil Fund ETF"),
    ("UNG", "Natural Gas ETF"),
    ("COPX", "Copper Miners ETF"),

    # Already confirmed working
    ("BTC/USD", "Bitcoin (confirmed working)"),
    ("XAU/USD", "Gold (confirmed working)"),
    ("WTI/USD", "Oil WTI (confirmed working)"),
]

print("Testing alternative macro symbols (ETFs)...")
print("=" * 70)

available = []
not_available = []

for symbol, description in SYMBOLS_TO_TEST:
    try:
        url = f"{BASE_URL}/quote"
        params = {"symbol": symbol, "apikey": API_KEY}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if "name" in data and "close" in data:
            print(f"✅ {symbol:<15} → {data['name']}")
            print(f"   Price: ${data.get('close')}")
            available.append((symbol, description, data['name']))
        else:
            reason = data.get('message', 'Unknown error')
            if 'Grow' in reason or 'pricing' in reason:
                print(f"💰 {symbol:<15} → PAID PLAN REQUIRED")
            else:
                print(f"❌ {symbol:<15} → {reason[:50]}")
            not_available.append((symbol, reason))

    except Exception as e:
        print(f"❌ {symbol:<15} → Error: {str(e)[:40]}")
        not_available.append((symbol, str(e)))

print("\n" + "=" * 70)
print(f"AVAILABLE ON FREE TIER ({len(available)}):")
print("=" * 70)

for symbol, desc, name in available:
    print(f"  {symbol:<15} - {name}")

print("\n" + "=" * 70)
print("RECOMMENDED CONFIG:")
print("=" * 70)
print("```yaml")
print("macro_instruments:")

# Group recommendations
etfs = [x for x in available if len(x[0]) <= 4 and '/' not in x[0]]
crypto = [x for x in available if 'BTC' in x[0] or 'ETH' in x[0]]
commodities = [x for x in available if '/' in x[0]]

if etfs:
    print("  # Stock Market / Bonds ETFs (FREE tier)")
    for symbol, desc, name in etfs[:5]:
        print(f"  - \"{symbol}\"  # {desc}")

if crypto:
    print("\n  # Cryptocurrency (FREE tier)")
    for symbol, desc, name in crypto[:2]:
        print(f"  - \"{symbol}\"  # {desc}")

if commodities:
    print("\n  # Commodities (FREE tier)")
    for symbol, desc, name in commodities[:5]:
        print(f"  - \"{symbol}\"  # {desc}")

print("```")
print("\n" + "=" * 70)
