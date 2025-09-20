#!/usr/bin/env python3
"""
debug_config.py - Debug Configuration Utilities

🎯 PURPOSE:
Business: Development and debugging configuration helpers
Technical: Debug settings, logging levels, and development features
Domain: Development/Debugging/Configuration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.045Z
Session: client-side-ai-brain-full-compliance
Confidence: 85%
Complexity: low

🧩 PATTERNS USED:
- AI_BRAIN_DEBUG_UTILITIES: Development and debugging configuration management

📦 DEPENDENCIES:
Internal: config_manager, logger_manager
External: logging, os, sys

💡 AI DECISION REASONING:
Debug configuration utilities enable enhanced debugging and development features while maintaining production safety.

🚀 USAGE:
debug_config.enable_verbose_logging()

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import os
import sys
from pathlib import Path

# Add the libs directory to the path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

def debug_env_vars():
    """Debug environment variables"""
    print("🔍 Environment Variables from .env.client:")
    
    # Read .env.client manually
    env_file = Path(".env.client")
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                print(f"  {key}: {value}")
                
                # Check if it's the problematic MAJOR_PAIRS
                if key == "MAJOR_PAIRS":
                    print(f"    Type: {type(value)}")
                    print(f"    Length: {len(value)}")
                    print(f"    Repr: {repr(value)}")
                    # Test split manually
                    try:
                        pairs = [pair.strip() for pair in value.split(',') if pair.strip()]
                        print(f"    Split result: {pairs}")
                    except Exception as e:
                        print(f"    Split error: {e}")
    else:
        print("❌ .env.client file not found")

def test_mt5_config_only():
    """Test MT5Config only"""
    print("\n🧪 Testing MT5Config in isolation...")
    
    try:
        from src.shared.config.client_settings import MT5Config
        
        # Try without env file first
        print("  Testing with defaults...")
        config = MT5Config(_env_file=None)
        print(f"  ✅ Default major_pairs: {config.major_pairs}")
        
        # Now test with env file
        print("  Testing with .env.client...")
        config = MT5Config(_env_file=".env.client")
        print(f"  ✅ Env major_pairs: {config.major_pairs}")
        
    except Exception as e:
        print(f"  ❌ MT5Config error: {e}")
        import traceback
        traceback.print_exc()

def test_major_pairs_validator():
    """Test the major_pairs validator directly"""
    print("\n🧪 Testing major_pairs validator...")
    
    try:
        from src.shared.config.client_settings import MT5Config
        
        # Test the validator method directly
        test_values = [
            "EURUSD,GBPUSD,USDJPY",
            ["EURUSD", "GBPUSD", "USDJPY"],
            "",
            None
        ]
        
        for test_val in test_values:
            try:
                result = MT5Config.validate_major_pairs(test_val)
                print(f"  ✅ Input: {repr(test_val)} -> Output: {result}")
            except Exception as e:
                print(f"  ❌ Input: {repr(test_val)} -> Error: {e}")
                
    except Exception as e:
        print(f"  ❌ Validator test error: {e}")

if __name__ == "__main__":
    print("🚀 Configuration Debug Script")
    print("=" * 50)
    
    debug_env_vars()
    test_major_pairs_validator()
    test_mt5_config_only()