#!/usr/bin/env python3
"""
run.py - Development Run Script

🎯 PURPOSE:
Business: Development-focused entry point with debugging and monitoring features
Technical: Development runtime with enhanced logging and monitoring
Domain: Development/Debugging/Runtime

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.922Z
Session: client-side-ai-brain-full-compliance
Confidence: 88%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_DEV_RUNTIME: Development runtime with enhanced monitoring
- DEBUG_INSTRUMENTATION: Enhanced debugging and monitoring capabilities

📦 DEPENDENCIES:
Internal: central_hub, hybrid_bridge, websocket_monitor
External: sys, os, logging

💡 AI DECISION REASONING:
Development runtime provides enhanced debugging capabilities and monitoring for development and testing phases.

🚀 USAGE:
python run.py --debug --monitor

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import asyncio
from pathlib import Path
import time

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import centralized import system
try:
    from src.infrastructure.imports.import_manager import get_function, get_class, get_module
except ImportError:
    print("⚠️ Centralized import system not available, using direct imports")

async def main():
    """Run the hybrid bridge with integrated WebSocket monitoring"""
    print("🚀 Starting MT5 Hybrid Bridge with WebSocket Monitoring...")
    print("💡 For more options, use: python main.py")
    print("-" * 50)
    
    try:
        # Use centralized import system where possible
        try:
            # Try centralized imports first
            hybrid_main = get_function('hybrid_bridge', 'main')
            print("✅ Using centralized import for hybrid bridge")
        except:
            # Fallback to direct import
            from src.presentation.cli.hybrid_bridge import main as hybrid_main, get_heartbeat_logger
            print("⚠️ Using direct import for hybrid bridge (centralized not available)")
        
        # Import WebSocket monitoring (no centralized mapping yet)
        from src.monitoring.websocket_monitor import WebSocketMonitor, ServicePriority
        
        # Initialize WebSocket Monitor
        print("🔍 Initializing WebSocket Monitor...")
        monitor = WebSocketMonitor()
        
        # Add status callback to display monitoring info
        def status_callback(status_data):
            endpoint = status_data.get('endpoint')
            message_type = status_data.get('message_type', 'unknown')
            print(f"📡 {endpoint.name}: {message_type}")
        
        monitor.add_status_callback(status_callback)
        
        # Start monitoring CRITICAL services first (Trading, Data-Bridge, API Gateway)
        print("🎯 Starting CRITICAL services monitoring...")
        monitor_task = asyncio.create_task(
            monitor.start_monitoring(priority_filter=ServicePriority.CRITICAL)
        )
        
        # Wait a moment for initial connections
        await asyncio.sleep(2)
        
        print("\n🌐 WebSocket Monitoring Active - Running Hybrid Bridge...")
        print("-" * 60)
        
        # Start hybrid bridge first to initialize the heartbeat logger
        bridge_task = asyncio.create_task(hybrid_main())
        
        # Wait a moment for bridge to initialize
        await asyncio.sleep(3)
        
        # Integrate WebSocket Monitor with existing dashboard
        try:
            # Get the heartbeat logger from hybrid bridge
            heartbeat_logger = await get_heartbeat_logger()
            if heartbeat_logger:
                # Connect WebSocket Monitor to the dashboard
                heartbeat_logger.set_websocket_monitor(monitor)
                print("✅ WebSocket Monitor integrated with dashboard")
            else:
                print("⚠️ Heartbeat logger not available yet")
        except Exception as e:
            print(f"⚠️ Could not integrate with dashboard: {e}")
        
        # Hybrid bridge already started above
        
        # Run both tasks concurrently
        await asyncio.gather(bridge_task, monitor_task, return_exceptions=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping WebSocket Monitor and Bridge...")
        if 'monitor' in locals():
            await monitor.stop_monitoring()
        print("👋 Bridge stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try: python main.py for more options")
        if 'monitor' in locals():
            await monitor.stop_monitoring()

def main_sync():
    """Synchronous wrapper for main function"""
    asyncio.run(main())

if __name__ == "__main__":
    main_sync()