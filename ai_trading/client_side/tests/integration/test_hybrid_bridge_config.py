#!/usr/bin/env python3
"""
test_hybrid_bridge_config.py - Hybrid Bridge Configuration Tests

🎯 PURPOSE:
Business: Hybrid bridge configuration and initialization testing
Technical: Bridge configuration validation with component integration
Domain: Testing/Bridge Configuration/Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.727Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_BRIDGE_TESTING: Bridge configuration and integration testing

📦 DEPENDENCIES:
Internal: hybrid_bridge, bridge_app
External: pytest, asyncio

💡 AI DECISION REASONING:
Bridge configuration testing ensures proper integration between MT5 and WebSocket systems.

🚀 USAGE:
pytest tests/integration/test_hybrid_bridge_config.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_config_import():
    """Test that configuration imports work"""
    try:
        from libs.config import get_client_settings
        settings = get_client_settings()
        print("✅ Configuration import successful")
        print(f"   App name: {settings.app.app_name}")
        print(f"   MT5 path: {settings.mt5.installation_path}")
        print(f"   WebSocket URL: {settings.network.websocket_url}")
        return True
    except Exception as e:
        print(f"❌ Configuration import failed: {e}")
        return False

def test_hybrid_bridge_init():
    """Test that HybridMT5Bridge can be initialized (config only)"""
    try:
        # Mock the MT5 dependencies that aren't available on Linux
        import sys
        from unittest.mock import MagicMock
        
        # Mock MT5 modules
        mt5_mock = MagicMock()
        sys.modules['MetaTrader5'] = mt5_mock
        sys.modules['mt5_handler'] = MagicMock()
        sys.modules['websocket_client'] = MagicMock()
        sys.modules['libs.streaming'] = MagicMock()
        
        # Now try to import HybridMT5Bridge class
        from hybrid_bridge import HybridMT5Bridge
        
        # Test configuration loading in __init__
        bridge = HybridMT5Bridge()
        
        print("✅ HybridMT5Bridge initialization successful")
        print(f"   Settings loaded: {type(bridge.settings)}")
        print(f"   Log level: {bridge.settings.app.log_level}")
        print(f"   Trading enabled: {bridge.settings.app.trading_enabled}")
        return True
        
    except Exception as e:
        print(f"❌ HybridMT5Bridge initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Hybrid Bridge Configuration Loading")
    print("=" * 60)
    
    test1 = test_config_import()
    print()
    test2 = test_hybrid_bridge_init()
    
    print()
    print("=" * 60)
    if test1 and test2:
        print("🎉 All tests passed! Configuration migration successful")
        return 0
    else:
        print("❌ Some tests failed! Check configuration migration")
        return 1

if __name__ == "__main__":
    sys.exit(main())