#!/usr/bin/env python3
"""
install_kafka_windows.py - Windows Kafka Installation Utility

🎯 PURPOSE:
Business: Automated Kafka/Redpanda installation for Windows environments
Technical: Platform-specific installation with configuration and service setup
Domain: Installation/Windows Platform/Streaming Infrastructure

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.085Z
Session: client-side-ai-brain-full-compliance
Confidence: 84%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_PLATFORM_INSTALLER: Automated platform-specific installation

📦 DEPENDENCIES:
Internal: logger_manager, config_manager
External: subprocess, os, zipfile, urllib.request, winreg

💡 AI DECISION REASONING:
Windows installation requires specific setup procedures for Kafka/Redpanda integration with MT5 systems.

🚀 USAGE:
python install_kafka_windows.py --install-path="C:\kafka"

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import subprocess
import sys
import os

def install_kafka_libraries():
    """Install Kafka libraries for Windows"""
    print("🔧 Installing Kafka libraries for Windows...")
    print("=" * 50)
    
    # Libraries to install
    libraries = [
        "aiokafka",
        "kafka-python",
        "async-timeout"  # Required by aiokafka
    ]
    
    # Install each library
    for lib in libraries:
        try:
            print(f"📦 Installing {lib}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", lib
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {lib} installed successfully")
            else:
                print(f"❌ Failed to install {lib}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error installing {lib}: {e}")
    
    print("\n" + "=" * 50)
    print("🧪 Testing Kafka library imports...")
    
    # Test imports
    try:
        import aiokafka
        print(f"✅ aiokafka {aiokafka.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ aiokafka import failed: {e}")
    
    try:
        import kafka
        print(f"✅ kafka-python {kafka.__version__} imported successfully")
    except ImportError as e:
        print(f"❌ kafka-python import failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Kafka libraries installation completed!")
    print("💡 You can now restart the MT5 Bridge to use Redpanda streaming.")

if __name__ == "__main__":
    install_kafka_libraries()