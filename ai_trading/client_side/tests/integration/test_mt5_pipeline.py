"""
test_mt5_pipeline.py - MT5 Pipeline Integration Tests

🎯 PURPOSE:
Business: End-to-end testing of MT5 data pipeline and trading operations
Technical: Complete MT5 workflow testing with real market data simulation
Domain: Testing/MT5 Integration/Trading Pipeline

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.131Z
Session: client-side-ai-brain-full-compliance
Confidence: 92%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_MT5_TESTING: Complete MT5 integration testing

📦 DEPENDENCIES:
Internal: mt5_handler, bridge_app, data_source_monitor
External: pytest, MetaTrader5, asyncio

💡 AI DECISION REASONING:
MT5 pipeline testing ensures trading operations work correctly with real market conditions and data flows.

🚀 USAGE:
pytest tests/integration/test_mt5_pipeline.py --mt5-demo

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""
import asyncio
import sys
import os
from datetime import datetime
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_bridge import HybridMT5Bridge

async def monitor_tick_pipeline():
    """Monitor the tick data pipeline"""
    print("=== MT5 Tick Pipeline Monitor ===\n")
    
    # Create bridge instance
    bridge = HybridMT5Bridge()
    
    try:
        # Start the bridge
        print("Starting Hybrid MT5 Bridge...")
        start_task = asyncio.create_task(bridge.start())
        
        # Wait a bit for initialization
        await asyncio.sleep(5)
        
        # Monitor for 30 seconds
        print("\nMonitoring tick data for 30 seconds...\n")
        
        start_time = time.time()
        last_report = start_time
        
        while time.time() - start_time < 30:
            # Check tick times
            if bridge.last_tick_times:
                print(f"\n📊 Tick Status at {datetime.now().strftime('%H:%M:%S')}:")
                for symbol, last_time in bridge.last_tick_times.items():
                    age = (datetime.now() - last_time).total_seconds()
                    print(f"   {symbol}: Last tick {age:.1f}s ago")
            else:
                print(f"⚠️  No ticks received yet at {datetime.now().strftime('%H:%M:%S')}")
            
            # Check connections
            if time.time() - last_report > 10:
                print(f"\n🔗 Connection Status:")
                print(f"   MT5: {'✅' if bridge.mt5_handler and await bridge.mt5_handler.is_connected() else '❌'}")
                print(f"   WebSocket: {'✅' if bridge.ws_client and bridge.ws_client.is_connected else '❌'}")
                print(f"   Redpanda: {'✅' if bridge.redpanda_manager and bridge.redpanda_manager.is_healthy() else '❌'}")
                last_report = time.time()
            
            await asyncio.sleep(2)
        
        print("\n📊 Final Summary:")
        if bridge.last_tick_times:
            print(f"   Total symbols with ticks: {len(bridge.last_tick_times)}")
            for symbol, last_time in bridge.last_tick_times.items():
                print(f"   {symbol}: Last tick at {last_time.strftime('%H:%M:%S')}")
        else:
            print("   ❌ No tick data was received during monitoring period")
        
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Stop the bridge
        print("\nStopping bridge...")
        await bridge.stop()
        
        # Cancel start task if still running
        if not start_task.done():
            start_task.cancel()
            try:
                await start_task
            except asyncio.CancelledError:
                pass

if __name__ == "__main__":
    asyncio.run(monitor_tick_pipeline())