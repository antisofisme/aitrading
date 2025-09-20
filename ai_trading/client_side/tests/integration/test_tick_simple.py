"""
test_tick_simple.py - Simple Tick Data Tests

🎯 PURPOSE:
Business: Basic tick data functionality testing
Technical: Simple tick data retrieval and processing validation
Domain: Testing/Tick Data/Basic Functionality

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.861Z
Session: client-side-ai-brain-full-compliance
Confidence: 89%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_SIMPLE_TICK_TESTING: Basic tick data testing

📦 DEPENDENCIES:
Internal: mt5_handler
External: pytest, MetaTrader5

💡 AI DECISION REASONING:
Simple tick testing provides basic validation for tick data functionality.

🚀 USAGE:
pytest tests/integration/test_tick_simple.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""
import asyncio
import MetaTrader5 as mt5
from datetime import datetime
import json
import websockets

async def test_tick_flow():
    """Test the complete tick data flow"""
    print("=== Testing Tick Data Flow ===\n")
    
    # 1. Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return
    
    print("✅ MT5 initialized")
    
    # 2. Check symbol
    symbol = "EURUSD"
    symbol_info = mt5.symbol_info(symbol)
    
    if not symbol_info:
        print(f"❌ Symbol {symbol} not found")
        mt5.shutdown()
        return
    
    print(f"📊 Symbol {symbol}:")
    print(f"   Visible: {symbol_info.visible}")
    print(f"   Selected: {symbol_info.select}")
    
    # 3. Select symbol if needed
    if not symbol_info.select:
        if mt5.symbol_select(symbol, True):
            print(f"   ✅ Symbol selected")
        else:
            print(f"   ❌ Failed to select symbol")
            mt5.shutdown()
            return
    
    # 4. Get tick data
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        print(f"❌ No tick data available")
        mt5.shutdown()
        return
    
    print(f"\n📈 Tick data received:")
    print(f"   Time: {datetime.fromtimestamp(tick.time)}")
    print(f"   Bid: {tick.bid}")
    print(f"   Ask: {tick.ask}")
    print(f"   Volume: {tick.volume}")
    
    # 5. Format tick data like the bridge does
    tick_data = {
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "last": tick.last,
        "volume": tick.volume,
        "spread": tick.ask - tick.bid,
        "time": datetime.fromtimestamp(tick.time).isoformat()
    }
    
    print(f"\n📦 Formatted tick data:")
    print(json.dumps(tick_data, indent=2))
    
    # 6. Test WebSocket sending
    print(f"\n🌐 Testing WebSocket connection...")
    
    try:
        ws_url = "ws://localhost:8000/api/v1/ws/mt5"
        async with websockets.connect(ws_url) as websocket:
            print(f"✅ Connected to {ws_url}")
            
            # Send tick data message
            message = {
                "type": "tick_data",
                "symbol": tick_data["symbol"],
                "bid": tick_data["bid"],
                "ask": tick_data["ask"],
                "last": tick_data["last"],
                "volume": tick_data["volume"],
                "spread": tick_data["spread"],
                "timestamp": datetime.now().isoformat(),
                "source": "test_script"
            }
            
            await websocket.send(json.dumps(message, default=str))
            print(f"📤 Sent tick data message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            print(f"📥 Server response: {response_data}")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    
    mt5.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_tick_flow())