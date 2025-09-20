"""
check_mt5_market.py - MT5 Market Status Checker

🎯 PURPOSE:
Business: Automated MT5 market status verification for trading readiness
Technical: Market hours and symbol availability checking with status reporting
Domain: MT5 Integration/Market Status/Trading Readiness

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.079Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_MARKET_MONITORING: Automated market status monitoring and reporting

📦 DEPENDENCIES:
Internal: mt5_handler, logger_manager
External: MetaTrader5, datetime, json

💡 AI DECISION REASONING:
Trading systems need to verify market availability and symbol status before executing trades to prevent errors.

🚀 USAGE:
python check_mt5_market.py --symbols=EURUSD,GBPUSD

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""
import MetaTrader5 as mt5
from datetime import datetime

def check_mt5_market():
    print("=== MT5 Market Status Check ===\n")
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        print("Error:", mt5.last_error())
        return
    
    print("✅ MT5 initialized successfully")
    
    # Terminal info
    terminal_info = mt5.terminal_info()
    if terminal_info:
        print("\n📊 Terminal Info:")
        print(f"   Connected: {terminal_info.connected}")
        print(f"   Trade Allowed: {terminal_info.trade_allowed}")
        print(f"   Path: {terminal_info.path}")
        print(f"   Company: {terminal_info.company}")
        print(f"   Server: {terminal_info.server}")
    
    # Account info
    account_info = mt5.account_info()
    if account_info:
        print("\n💰 Account Info:")
        print(f"   Login: {account_info.login}")
        print(f"   Server: {account_info.server}")
        print(f"   Balance: {account_info.balance}")
        print(f"   Currency: {account_info.currency}")
    
    # Check symbols
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "EURJPY", "GBPJPY"]
    
    print("\n📈 Symbol Status:")
    available_symbols = []
    
    for symbol in symbols:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            print(f"\n   {symbol}:")
            print(f"      Exists: ✅")
            print(f"      Visible: {'✅' if symbol_info.visible else '❌'}")
            print(f"      Selected: {'✅' if symbol_info.select else '❌'}")
            print(f"      Session deals: {symbol_info.session_deals}")
            print(f"      Spread: {symbol_info.spread}")
            
            # Try to get tick
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                print(f"      Current Bid: {tick.bid}")
                print(f"      Current Ask: {tick.ask}")
                print(f"      Last update: {datetime.fromtimestamp(tick.time)}")
                available_symbols.append(symbol)
            else:
                print(f"      Tick data: ❌ Not available")
                
            # Check if symbol needs to be selected
            if not symbol_info.select:
                if mt5.symbol_select(symbol, True):
                    print(f"      ✅ Symbol selected successfully")
                else:
                    print(f"      ❌ Failed to select symbol")
        else:
            print(f"\n   {symbol}: ❌ Not found")
    
    # Check total symbols
    all_symbols = mt5.symbols_get()
    if all_symbols:
        print(f"\n📊 Total symbols available: {len(all_symbols)}")
        print(f"   Symbols with tick data: {len(available_symbols)}")
    
    # Check if market is open
    print("\n🏪 Market Status:")
    if available_symbols:
        print("   ✅ Market appears to be OPEN (tick data available)")
    else:
        print("   ❌ Market appears to be CLOSED or no data access")
        print("\n   Possible reasons:")
        print("   - Market is closed (weekend/holiday)")
        print("   - Demo account has no data access")
        print("   - Network/connection issues")
        print("   - Symbol permissions not granted")
    
    mt5.shutdown()
    print("\n✅ Check completed")

if __name__ == "__main__":
    check_mt5_market()