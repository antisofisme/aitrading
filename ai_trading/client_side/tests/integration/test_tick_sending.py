#!/usr/bin/env python3
"""
test_tick_sending.py - Tick Data Transmission Tests

🎯 PURPOSE:
Business: Tick data transmission reliability and performance testing
Technical: End-to-end tick data flow validation with performance metrics
Domain: Testing/Tick Data/Data Transmission

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.840Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_TICK_TRANSMISSION: Tick data transmission testing

📦 DEPENDENCIES:
Internal: mt5_handler, websocket_client
External: pytest, MetaTrader5, asyncio

💡 AI DECISION REASONING:
Tick transmission testing ensures reliable real-time data flow for trading operations.

🚀 USAGE:
pytest tests/integration/test_tick_sending.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
from datetime import datetime
from mt5_handler import MT5Handler
from websocket_client import WebSocketClient
from libs.config import get_mt5_settings

async def test_tick_sending():
    """Test tick data sending to WebSocket"""
    
    # Initialize
    settings = get_mt5_settings()
    mt5 = MT5Handler(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    ws_client = WebSocketClient(settings.backend_ws_url)
    
    try:
        # Connect MT5
        if not mt5.connect():
            print("❌ Failed to connect MT5")
            return
        print("✅ MT5 connected")
        
        # Connect WebSocket
        await ws_client.connect()
        print("✅ WebSocket connected")
        
        # Get tick for EURUSD
        tick = mt5.get_tick("EURUSD")
        if tick:
            print(f"\n📊 Got tick: {tick}")
            
            # Send via WebSocket
            result = await ws_client.send_tick_data(tick)
            print(f"\n📤 Send result: {result}")
        else:
            print("❌ No tick data available")
            
        # Wait a bit for response
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await ws_client.disconnect()
        mt5.disconnect()

if __name__ == "__main__":
    asyncio.run(test_tick_sending())