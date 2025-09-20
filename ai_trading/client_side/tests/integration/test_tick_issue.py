"""
test_tick_issue.py - Tick Data Issue Investigation Tests

🎯 PURPOSE:
Business: Tick data processing issue diagnosis and validation
Technical: Tick data flow issue identification and resolution testing
Domain: Testing/Tick Data/Issue Diagnosis

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.823Z
Session: client-side-ai-brain-full-compliance
Confidence: 85%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_TICK_DIAGNOSIS: Tick data issue diagnosis and resolution

📦 DEPENDENCIES:
Internal: mt5_handler, bridge_app
External: pytest, MetaTrader5

💡 AI DECISION REASONING:
Tick issue testing helps identify and resolve data flow problems in trading systems.

🚀 USAGE:
pytest tests/integration/test_tick_issue.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""
import asyncio
import MetaTrader5 as mt5
from datetime import datetime
import sys

async def test_tick_data():
    """Test MT5 tick data retrieval"""
    print("=== MT5 Tick Data Test ===")
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        print("Error:", mt5.last_error())
        return
    
    print("✅ MT5 initialized")
    
    # Get terminal info
    terminal_info = mt5.terminal_info()
    if terminal_info:
        print(f"📊 MT5 Terminal:")
        print(f"   Connected: {terminal_info.connected}")
        print(f"   Trade Allowed: {terminal_info.trade_allowed}")
        print(f"   Company: {terminal_info.company}")
    
    # Test symbols
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    
    for symbol in symbols:
        print(f"\n📈 Testing {symbol}:")
        
        # Check symbol info
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"   ❌ Symbol not found")
            continue
            
        print(f"   Visible: {symbol_info.visible}")
        print(f"   Selected: {symbol_info.select}")
        
        # Select symbol if not selected
        if not symbol_info.select:
            selected = mt5.symbol_select(symbol, True)
            print(f"   Selection attempt: {'✅' if selected else '❌'}")
            
            # Re-check after selection
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                print(f"   Selected after attempt: {symbol_info.select}")
        
        # Get tick data
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            print(f"   ✅ Tick data:")
            print(f"      Time: {datetime.fromtimestamp(tick.time)}")
            print(f"      Bid: {tick.bid}")
            print(f"      Ask: {tick.ask}")
            print(f"      Volume: {tick.volume}")
        else:
            print(f"   ❌ No tick data available")
            error = mt5.last_error()
            print(f"   Error: {error}")
    
    # Test market status
    print("\n🏪 Market Status:")
    for symbol in symbols:
        if mt5.market_book_add(symbol):
            print(f"   {symbol}: Market book added ✅")
            mt5.market_book_release(symbol)
        else:
            print(f"   {symbol}: Market book failed ❌")
    
    mt5.shutdown()
    print("\n✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_tick_data())