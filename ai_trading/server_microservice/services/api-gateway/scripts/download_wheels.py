#!/usr/bin/env python3
"""
Download Wheels Script - API Gateway Service  
Service-specific progressive deployment strategy from CLAUDE.md Section 13
"""

import subprocess
import os
import sys
from pathlib import Path
import argparse

# Service-specific tiers configuration
SERVICE_TIERS = {
    'tier1': 'tier1-core.txt',
    'tier2': 'tier2-service.txt'
}

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

def download_service_tier(tier_name):
    """Download wheels for specific service tier - OFFLINE DEPLOYMENT READY"""
    wheels_dir = Path(f"wheels/{tier_name}")
    requirements_file = Path(f"requirements/{SERVICE_TIERS[tier_name]}")
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    wheels_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Downloading {tier_name} for API Gateway service ({requirements_file})...")
    
    cmd = f"pip wheel -r {requirements_file} -w {wheels_dir} --no-deps"
    
    if run_command(cmd, f"Download {tier_name} wheels"):
        size = get_folder_size(wheels_dir)
        print(f"✅ API Gateway {tier_name} completed - Size: {size}")
        return True
    return False

def download_all_tiers():
    """Download all service tiers"""
    print("🚀 API Gateway Service - Complete Offline Wheels Download")
    print("   Based on CLAUDE.md Section 13: Per-Service Tiered Management")
    
    success_count = 0
    for tier in SERVICE_TIERS.keys():
        if download_service_tier(tier):
            success_count += 1
        print()  # Empty line between tiers
    
    total_size = get_folder_size("wheels")
    print(f"📊 Download Summary:")
    print(f"   ✅ Successful tiers: {success_count}/{len(SERVICE_TIERS)}")
    print(f"   📊 Total size: {total_size}")
    print(f"   📁 Location: {Path('wheels').absolute()}")
    
    return success_count == len(SERVICE_TIERS)

def main():
    parser = argparse.ArgumentParser(description="API Gateway Service Wheels Management")
    parser.add_argument("--tier", choices=list(SERVICE_TIERS.keys()) + ['all'], 
                       help="Download specific tier or all tiers")
    parser.add_argument("--info", action="store_true", help="Show wheels information")
    
    args = parser.parse_args()
    
    if not any([args.tier, args.info]):
        print("Usage: python scripts/download_wheels.py [--tier TIER] [--info]")
        print(f"Available tiers: {', '.join(SERVICE_TIERS.keys())}, all")
        return
    
    # Change to service root directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    if args.info:
        wheels_dir = Path("wheels")
        if wheels_dir.exists():
            for tier in SERVICE_TIERS.keys():
                tier_dir = wheels_dir / tier
                if tier_dir.exists():
                    wheel_count = len(list(tier_dir.glob("*.whl")))
                    size = get_folder_size(tier_dir)
                    print(f"📊 {tier}: {wheel_count} wheels, {size}")
        else:
            print("❌ No wheels directory found")
    
    if args.tier:
        if args.tier == 'all':
            success = download_all_tiers()
        else:
            success = download_service_tier(args.tier)
        
        if success:
            print(f"\n🎯 API Gateway service ready for offline deployment!")
            print(f"   Next: docker-compose build api-gateway-{args.tier}")
        else:
            print(f"\n❌ Download failed for {args.tier}")
            sys.exit(1)

if __name__ == "__main__":
    main()