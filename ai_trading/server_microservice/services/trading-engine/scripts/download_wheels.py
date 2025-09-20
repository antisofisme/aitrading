#!/usr/bin/env python3
"""
Download Wheels Script - Trading Engine Service
Implements offline-first deployment strategy from CLAUDE.md Section 13
"""

import subprocess
import os
import sys
from pathlib import Path
import argparse

def run_command(cmd, description):
    """Run command with proper error handling"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def get_folder_size(folder):
    """Get human-readable folder size"""
    if not Path(folder).exists():
        return "0MB"
    total = sum(f.stat().st_size for f in Path(folder).rglob('*') if f.is_file())
    return f"{total / (1024*1024):.1f}MB"

def download_wheels():
    """Download wheels for offline deployment"""
    wheels_dir = Path("wheels")
    wheels_dir.mkdir(exist_ok=True)
    
    print("🚀 Trading Engine - Offline Wheels Download Strategy")
    print("   Based on CLAUDE.md Section 13: Tiered Library Management")
    
    # Use poetry to export requirements, then download wheels
    print("\n📋 Exporting poetry dependencies...")
    export_cmd = "poetry export -f requirements.txt --output requirements-export.txt --without-hashes"
    if not run_command(export_cmd, "Export poetry dependencies"):
        return False
    
    # Download wheels
    print(f"\n📦 Downloading wheels to {wheels_dir}...")
    wheel_cmd = f"pip wheel -r requirements-export.txt -w {wheels_dir} --no-deps"
    if not run_command(wheel_cmd, "Download wheels"):
        return False
    
    # Get final size
    size = get_folder_size(wheels_dir)
    print(f"\n✅ Wheels download completed!")
    print(f"   📊 Total size: {size}")
    print(f"   📁 Location: {wheels_dir.absolute()}")
    
    # Cleanup
    if Path("requirements-export.txt").exists():
        Path("requirements-export.txt").unlink()
    
    return True

def test_offline_install():
    """Test offline installation from wheels"""
    wheels_dir = Path("wheels")
    if not wheels_dir.exists():
        print("❌ No wheels directory found. Run download first.")
        return False
    
    print("\n🧪 Testing offline installation...")
    test_cmd = f"pip install --dry-run --no-index --find-links {wheels_dir} fastapi uvicorn"
    return run_command(test_cmd, "Test offline installation")

def main():
    parser = argparse.ArgumentParser(description="Trading Engine Wheels Management")
    parser.add_argument("--download", action="store_true", help="Download wheels for offline deployment")
    parser.add_argument("--test", action="store_true", help="Test offline installation")
    parser.add_argument("--info", action="store_true", help="Show wheels information")
    
    args = parser.parse_args()
    
    if not any([args.download, args.test, args.info]):
        print("Usage: python scripts/download_wheels.py [--download] [--test] [--info]")
        return
    
    # Change to script's directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    if args.info:
        wheels_dir = Path("wheels")
        if wheels_dir.exists():
            wheel_count = len(list(wheels_dir.glob("*.whl")))
            size = get_folder_size(wheels_dir)
            print(f"📊 Wheels Info:")
            print(f"   📦 Wheel files: {wheel_count}")
            print(f"   📊 Total size: {size}")
            print(f"   📁 Location: {wheels_dir.absolute()}")
        else:
            print("❌ No wheels directory found")
    
    if args.download:
        if download_wheels():
            print("\n🎯 Ready for offline deployment!")
            print("   Next: docker build -f Dockerfile.offline -t trading-engine:offline .")
        else:
            print("\n❌ Download failed")
            sys.exit(1)
    
    if args.test:
        if not test_offline_install():
            sys.exit(1)

if __name__ == "__main__":
    main()