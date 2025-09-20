#!/usr/bin/env python3
"""
AI Provider Service - Tiered Wheels Download Script
Download wheels for offline deployment based on CLAUDE.md Section 13 strategy
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

def get_service_name():
    """Detect service name from current directory"""
    current_path = os.getcwd()
    if 'services' in current_path:
        return current_path.split('services/')[-1].split('/')[0]
    return 'ai-provider'

def get_folder_size(folder):
    """Get human-readable folder size"""
    total = sum(f.stat().st_size for f in Path(folder).rglob('*') if f.is_file())
    return f"{total / (1024*1024):.1f}MB"

def download_service_wheels(requirements_file: str, service_name: str):
    """Download wheels for AI Provider service - OFFLINE DEPLOYMENT READY"""
    
    wheels_dir = "wheels"
    
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    # Create wheels directory
    os.makedirs(wheels_dir, exist_ok=True)
    
    print(f"📦 Downloading wheels for {service_name} service ({requirements_file})...")
    print(f"🎯 Target: {wheels_dir}/")
    
    # Download wheels command with dependencies to match Docker Python 3.11
    cmd = [
        "pip", "wheel",
        "-r", requirements_file,
        "-w", wheels_dir,
        "--no-cache-dir"  # Don't use pip cache
    ]
    
    try:
        print(f"🚀 Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        size = get_folder_size(wheels_dir)
        print(f"✅ {service_name} wheels completed - Size: {size}")
        
        # List downloaded wheels
        wheels = list(Path(wheels_dir).glob("*.whl"))
        print(f"📊 Downloaded {len(wheels)} wheel files:")
        for wheel in sorted(wheels)[:10]:  # Show first 10
            print(f"   - {wheel.name}")
        if len(wheels) > 10:
            print(f"   ... and {len(wheels) - 10} more")
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {service_name} wheels download failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download wheels for AI Provider service"
    )
    parser.add_argument(
        "--requirements", 
        default="requirements.txt",
        help="Requirements file to use (default: requirements.txt)"
    )
    parser.add_argument(
        "--update",
        action="store_true", 
        help="Update existing wheels"
    )
    
    args = parser.parse_args()
    service_name = get_service_name()
    
    print(f"🤖 AI Provider Service - Wheels Download")
    print(f"🎯 Service: {service_name}")
    print("=" * 50)
    
    if args.update:
        print("🔄 Update mode: Clearing existing wheels...")
        import shutil
        if os.path.exists("wheels"):
            shutil.rmtree("wheels")
    
    # Download wheels
    success = download_service_wheels(args.requirements, service_name)
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ All wheels downloaded! Ready for offline deployment.")
        print("🚀 Next: docker-compose build --no-cache")
    else:
        print("⚠️  Wheels download failed. Check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()