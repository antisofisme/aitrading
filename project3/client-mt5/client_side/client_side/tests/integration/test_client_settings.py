#!/usr/bin/env python3
"""
test_client_settings.py - Client Settings Integration Tests

🎯 PURPOSE:
Business: Client settings configuration validation and testing
Technical: Client settings functionality testing with environment validation
Domain: Testing/Configuration/Client Settings

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.709Z
Session: client-side-ai-brain-full-compliance
Confidence: 89%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CONFIG_TESTING: Configuration testing and validation

📦 DEPENDENCIES:
Internal: client_settings, config_manager
External: pytest, pathlib, os

💡 AI DECISION REASONING:
Client settings testing ensures configuration reliability across different environments.

🚀 USAGE:
pytest tests/integration/test_client_settings.py

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import sys
import os
from pathlib import Path

# Add the libs directory to the path
sys.path.insert(0, str(Path(__file__).parent / "libs"))

def test_client_settings():
    """Test client settings configuration"""
    print("🧪 Testing Client Settings Configuration...")
    
    try:
        # Import the new centralized settings
        from src.shared.config.client_settings import (
            get_client_settings, 
            ClientSettings, 
            ClientConstants,
            ClientEnvironment
        )
        
        print("✅ Import successful")
        
        # Initialize settings
        settings = get_client_settings()
        print("✅ Settings initialization successful")
        
        # Test constants
        constants = settings.constants
        print(f"✅ Constants accessible: {type(constants)}")
        print(f"   - FAST_TIMEOUT: {constants.FAST_TIMEOUT}")
        print(f"   - MT5_TIMEOUT: {constants.MT5_TIMEOUT}")
        print(f"   - MAX_RETRIES: {constants.MAX_RETRIES}")
        
        # Test connection URLs
        connection_urls = settings.get_connection_urls()
        print("✅ Connection URLs generated:")
        for conn_name, url in connection_urls.items():
            print(f"   - {conn_name}: {url}")
        
        # Test MT5 configuration
        mt5_config = settings.get_mt5_config()
        print("✅ MT5 Configuration accessible:")
        for key, value in mt5_config.items():
            if isinstance(value, list):
                print(f"   - {key}: {len(value)} items")
            else:
                print(f"   - {key}: {value}")
        
        # Test environment detection
        print(f"✅ Environment: {settings.app.environment}")
        print(f"✅ Is Production: {settings.is_production()}")
        print(f"✅ Is Development: {settings.is_development()}")
        
        # Test individual configurations
        print("✅ Configuration sections:")
        print(f"   - App config: {settings.app.app_name}")
        print(f"   - Network config: {settings.network.websocket_url}")
        print(f"   - MT5 config: {settings.mt5.installation_path}")
        print(f"   - Streaming config: {settings.streaming.bootstrap_servers}")
        
        # Test validation
        settings._validate_all()
        print("✅ All configuration validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment_variables():
    """Test environment variable loading"""
    print("\n🌍 Testing Environment Variable Loading...")
    
    try:
        # Set some test environment variables
        test_env_vars = {
            "SERVER_HOST": "test-server",
            "SERVER_PORT": "9000",
            "APP_NAME": "Test MT5 Bridge"
        }
        
        # Save original values
        original_values = {}
        for key in test_env_vars:
            original_values[key] = os.environ.get(key)
            os.environ[key] = test_env_vars[key]
        
        # Import and test with new env vars
        from src.shared.config.client_settings import reload_client_settings
        
        settings = reload_client_settings()
        
        # Verify environment variables were loaded
        assert settings.network.server_host == "test-server"
        assert settings.network.server_port == 9000
        assert settings.app.app_name == "Test MT5 Bridge"
        
        print("✅ Environment variables loaded correctly")
        
        # Restore original environment
        for key, original_value in original_values.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        
        # Reload to restore original settings
        reload_client_settings()
        
        return True
        
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False


def test_url_generation():
    """Test URL generation functionality"""
    print("\n🔗 Testing URL Generation...")
    
    try:
        from src.shared.config.client_settings import get_client_settings
        
        settings = get_client_settings()
        
        # Test WebSocket URL generation
        ws_url = settings.network.websocket_url
        expected_ws = "ws://localhost:8000/api/v1/ws/mt5"
        assert ws_url == expected_ws, f"Expected {expected_ws}, got {ws_url}"
        
        # Test API URL generation
        api_url = settings.network.api_url
        expected_api = "http://localhost:8000/api"
        assert api_url == expected_api, f"Expected {expected_api}, got {api_url}"
        
        # Test Health URL generation
        health_url = settings.network.health_url
        expected_health = "http://localhost:8000/health"
        assert health_url == expected_health, f"Expected {expected_health}, got {health_url}"
        
        print("✅ URL generation working correctly")
        print(f"   - WebSocket: {ws_url}")
        print(f"   - API: {api_url}")
        print(f"   - Health: {health_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ URL generation test failed: {e}")
        return False


def test_mt5_configuration():
    """Test MT5 specific configuration"""
    print("\n🤖 Testing MT5 Configuration...")
    
    try:
        from src.shared.config.client_settings import get_client_settings
        import platform
        
        settings = get_client_settings()
        
        # Test platform-specific path detection
        mt5_path = settings.mt5.installation_path
        current_platform = platform.system()
        
        if current_platform == "Windows":
            expected_path = settings.mt5.windows_path
        else:
            expected_path = settings.mt5.linux_path
        
        assert mt5_path == expected_path, f"Path mismatch for {current_platform}"
        
        # Test symbol configuration
        major_pairs = settings.mt5.major_pairs
        assert len(major_pairs) >= 6, "Should have at least 6 major pairs"
        assert "EURUSD" in major_pairs, "EURUSD should be in major pairs"
        
        # Test MT5 timeout settings
        assert settings.mt5.login_timeout > 0, "Login timeout should be positive"
        assert settings.mt5.connection_retry_attempts > 0, "Retry attempts should be positive"
        
        print("✅ MT5 configuration working correctly")
        print(f"   - Platform: {current_platform}")
        print(f"   - Installation path: {mt5_path}")
        print(f"   - Major pairs: {len(major_pairs)} pairs")
        print(f"   - Login timeout: {settings.mt5.login_timeout}s")
        
        return True
        
    except Exception as e:
        print(f"❌ MT5 configuration test failed: {e}")
        return False


def test_streaming_configuration():
    """Test streaming configuration"""
    print("\n📡 Testing Streaming Configuration...")
    
    try:
        from src.shared.config.client_settings import get_client_settings
        
        settings = get_client_settings()
        
        # Test bootstrap servers
        bootstrap_servers = settings.streaming.bootstrap_servers
        assert "," in bootstrap_servers or ":" in bootstrap_servers, "Bootstrap servers should contain port"
        
        # Test topics configuration
        topics = [
            settings.streaming.tick_data_topic,
            settings.streaming.events_topic,
            settings.streaming.responses_topic,
            settings.streaming.signals_topic,
            settings.streaming.analytics_topic
        ]
        
        for topic in topics:
            assert len(topic) > 0, f"Topic {topic} should not be empty"
        
        # Test producer settings
        assert settings.streaming.batch_size > 0, "Batch size should be positive"
        assert settings.streaming.retries >= 0, "Retries should be non-negative"
        
        print("✅ Streaming configuration working correctly")
        print(f"   - Bootstrap servers: {bootstrap_servers}")
        print(f"   - Topics configured: {len(topics)}")
        print(f"   - Batch size: {settings.streaming.batch_size}")
        print(f"   - Retries: {settings.streaming.retries}")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming configuration test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Client Settings Validation Test Suite")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Basic functionality
    if not test_client_settings():
        all_tests_passed = False
    
    # Test 2: Environment variable loading
    if not test_environment_variables():
        all_tests_passed = False
    
    # Test 3: URL generation
    if not test_url_generation():
        all_tests_passed = False
    
    # Test 4: MT5 configuration
    if not test_mt5_configuration():
        all_tests_passed = False
    
    # Test 5: Streaming configuration
    if not test_streaming_configuration():
        all_tests_passed = False
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! Client settings are ready for migration.")
        print("✅ Safe to proceed with gradual migration to client_settings.py")
        return 0
    else:
        print("❌ Some tests failed! Fix issues before proceeding with migration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())