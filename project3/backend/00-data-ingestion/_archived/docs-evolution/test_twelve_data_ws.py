"""
Test Twelve Data WebSocket - Check Symbol Limits
"""
import asyncio
import json
from twelvedata import TDClient

API_KEY = "6b8c86ca6dd04b53b559bdaf6cb61783"

print("=" * 70)
print("TWELVE DATA WEBSOCKET TEST")
print("=" * 70)

async def test_websocket():
    """Test WebSocket connection and symbol subscription"""

    # Initialize client
    td = TDClient(apikey=API_KEY)

    # Test symbols (start with 8, then try more)
    test_symbols = [
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD",
        "USD/CAD",
        "NZD/USD",
        "USD/CHF",
        "XAU/USD",
        "EUR/GBP",  # 9th symbol
        "GBP/JPY",  # 10th symbol
    ]

    print(f"\n[TEST 1] Attempting to subscribe to {len(test_symbols)} symbols...")
    print("Symbols:", ", ".join(test_symbols))

    # Event counter
    event_count = {}

    def on_event(event):
        """Handle WebSocket events"""
        try:
            symbol = event.get('symbol', 'unknown')

            if symbol not in event_count:
                event_count[symbol] = 0
                print(f"\n  ✅ Symbol connected: {symbol}")

            event_count[symbol] += 1

            # Print first event for each symbol
            if event_count[symbol] == 1:
                print(f"     First data: {event}")

        except Exception as e:
            print(f"  ❌ Error in event handler: {e}")

    try:
        # Create WebSocket connection
        print("\n[TEST 2] Creating WebSocket connection...")
        ws = td.websocket(
            symbols=test_symbols,
            on_event=on_event
        )

        print("  ✅ WebSocket object created")

        # Connect
        print("\n[TEST 3] Connecting to WebSocket server...")
        ws.connect()
        print("  ✅ Connected")

        # Keep alive for 30 seconds to receive data
        print("\n[TEST 4] Listening for 30 seconds...")
        print("  (Press Ctrl+C to stop early)")

        await asyncio.sleep(30)

        # Disconnect
        print("\n[TEST 5] Disconnecting...")
        ws.disconnect()
        print("  ✅ Disconnected")

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)

        print(f"\nTotal symbols attempted: {len(test_symbols)}")
        print(f"Total symbols received data: {len(event_count)}")

        print("\nData received per symbol:")
        for symbol, count in event_count.items():
            print(f"  - {symbol}: {count} events")

        if len(event_count) < len(test_symbols):
            print(f"\n⚠️ WARNING: Only {len(event_count)}/{len(test_symbols)} symbols received data")
            print("   This might indicate a symbol limit!")

            missing = set(test_symbols) - set(event_count.keys())
            print(f"\n   Missing symbols: {', '.join(missing)}")
        else:
            print(f"\n✅ All {len(test_symbols)} symbols received data successfully!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"\nError details:")
        print(f"  Type: {type(e).__name__}")
        print(f"  Message: {str(e)}")

        # Check if it's a plan limitation error
        if "plan" in str(e).lower() or "upgrade" in str(e).lower():
            print("\n⚠️ This appears to be a PLAN LIMITATION error")
            print("   WebSocket might not be available on FREE tier")
            print("   Or limited to fewer symbols")

# Run test
if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with exception: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
