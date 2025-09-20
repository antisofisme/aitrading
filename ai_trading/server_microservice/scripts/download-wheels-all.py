#!/usr/bin/env python3
"""
Microservice Wheels Management - Download All Services
Implements CLAUDE.md Section 13 tiered library management
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Tuple
import concurrent.futures
import json

# Service configurations with tiers
SERVICES_CONFIG = {
    # TIER 1: Core Services (< 50MB each)
    "api-gateway": {
        "tier": 1,
        "priority": 1,
        "dependencies": ["fastapi>=0.104.1", "uvicorn>=0.24.0", "pydantic>=2.5.0", "redis>=5.0.1"],
        "max_size_mb": 50
    },
    "user-service": {
        "tier": 1, 
        "priority": 1,
        "dependencies": ["fastapi>=0.104.1", "uvicorn>=0.24.0", "pydantic>=2.5.0", "redis>=5.0.1"],
        "max_size_mb": 50
    },
    "database-service": {
        "tier": 1,
        "priority": 1, 
        "dependencies": ["fastapi>=0.104.1", "psycopg2-binary>=2.9.9", "clickhouse-connect>=0.6.8"],
        "max_size_mb": 100
    },
    
    # TIER 2: Data Services (< 200MB each)
    "data-bridge": {
        "tier": 2,
        "priority": 2,
        "dependencies": ["pandas>=2.1.0", "numpy>=1.25.0", "aiohttp>=3.8.0", "beautifulsoup4>=4.12.0"],
        "max_size_mb": 150
    },
    "trading-engine": {
        "tier": 2,
        "priority": 2,
        "dependencies": ["scikit-learn>=1.3.0", "pandas>=2.1.0", "numpy>=1.25.0", "redis>=5.0.1"],
        "max_size_mb": 200
    },
    
    # TIER 3: AI Basic (< 500MB)
    "ai-provider": {
        "tier": 3,
        "priority": 3,
        "dependencies": ["litellm>=1.30.0", "langfuse>=2.20.0", "openai>=1.12.0"],
        "max_size_mb": 300
    },
    
    # TIER 4: AI Advanced (< 2GB)
    "ai-orchestration": {
        "tier": 4,
        "priority": 4,
        "dependencies": ["langchain>=0.1.0", "transformers>=4.36.0", "sentence-transformers>=2.2.2"],
        "max_size_mb": 800
    },
    "ml-processing": {
        "tier": 4,
        "priority": 4,
        "dependencies": ["scikit-learn>=1.3.0", "pandas>=2.1.0", "numpy>=1.25.0", "joblib>=1.3.0"],
        "max_size_mb": 1000
    },
    
    # TIER 5: ML Heavy (< 4GB)
    "deep-learning": {
        "tier": 5,
        "priority": 5,
        "dependencies": ["torch>=2.0.0", "tensorflow>=2.13.0", "transformers>=4.36.0"],
        "max_size_mb": 2000
    }
}

class WheelsManager:
    """Manage wheels download across all microservices"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.wheels_dir = self.base_path / "wheels"
        self.wheels_dir.mkdir(exist_ok=True)
        self.download_stats = {
            "total_services": len(SERVICES_CONFIG),
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_size_mb": 0,
            "download_time_seconds": 0
        }
    
    def download_service_wheels(self, service_name: str, config: Dict) -> Tuple[bool, str, float]:
        """Download wheels for specific service"""
        start_time = time.time()
        service_wheels_dir = self.wheels_dir / service_name
        service_wheels_dir.mkdir(exist_ok=True)
        
        print(f"📦 Downloading {service_name} (Tier {config['tier']})...")
        
        try:
            # Create requirements file
            requirements_content = "\\n".join(config["dependencies"])
            requirements_file = service_wheels_dir / "requirements.txt"
            requirements_file.write_text(requirements_content)
            
            # Download wheels
            cmd = [
                sys.executable, "-m", "pip", "wheel",
                "-r", str(requirements_file),
                "-w", str(service_wheels_dir),
                "--no-deps"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Calculate size
                total_size = sum(f.stat().st_size for f in service_wheels_dir.rglob('*.whl'))
                size_mb = total_size / (1024 * 1024)
                
                duration = time.time() - start_time
                
                if size_mb > config["max_size_mb"]:
                    return False, f"Size exceeded: {size_mb:.1f}MB > {config['max_size_mb']}MB", duration
                
                print(f"✅ {service_name}: {size_mb:.1f}MB in {duration:.1f}s")
                return True, f"Success: {size_mb:.1f}MB", duration
            else:
                return False, f"pip wheel failed: {result.stderr}", time.time() - start_time
                
        except subprocess.TimeoutExpired:
            return False, "Timeout after 5 minutes", time.time() - start_time
        except Exception as e:
            return False, f"Error: {str(e)}", time.time() - start_time
    
    def download_by_tier(self, max_tier: int = 5) -> Dict:
        """Download wheels by tier (sequential for dependencies)"""
        results = {}
        total_start = time.time()
        
        print(f"🚀 Starting tiered download (Tiers 1-{max_tier})...")
        
        for tier in range(1, max_tier + 1):
            print(f"\\n🎯 TIER {tier} DEPLOYMENT:")
            tier_services = {name: config for name, config in SERVICES_CONFIG.items() if config["tier"] == tier}
            
            if not tier_services:
                continue
                
            # Download tier services in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_service = {
                    executor.submit(self.download_service_wheels, name, config): name 
                    for name, config in tier_services.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_service):
                    service_name = future_to_service[future]
                    try:
                        success, message, duration = future.result()
                        results[service_name] = {
                            "success": success,
                            "message": message,
                            "duration": duration,
                            "tier": SERVICES_CONFIG[service_name]["tier"]
                        }
                        
                        if success:
                            self.download_stats["successful_downloads"] += 1
                        else:
                            self.download_stats["failed_downloads"] += 1
                            print(f"❌ {service_name}: {message}")
                            
                    except Exception as e:
                        results[service_name] = {
                            "success": False,
                            "message": f"Exception: {str(e)}",
                            "duration": 0,
                            "tier": SERVICES_CONFIG[service_name]["tier"]
                        }
                        self.download_stats["failed_downloads"] += 1
        
        self.download_stats["download_time_seconds"] = time.time() - total_start
        return results
    
    def download_specific_services(self, service_names: List[str]) -> Dict:
        """Download wheels for specific services only"""
        results = {}
        
        print(f"🎯 Downloading specific services: {', '.join(service_names)}")
        
        for service_name in service_names:
            if service_name not in SERVICES_CONFIG:
                results[service_name] = {
                    "success": False,
                    "message": f"Unknown service: {service_name}",
                    "duration": 0
                }
                continue
                
            config = SERVICES_CONFIG[service_name]
            success, message, duration = self.download_service_wheels(service_name, config)
            results[service_name] = {
                "success": success,
                "message": message,
                "duration": duration,
                "tier": config["tier"]
            }
            
            if success:
                self.download_stats["successful_downloads"] += 1
            else:
                self.download_stats["failed_downloads"] += 1
        
        return results
    
    def print_summary(self, results: Dict):
        """Print download summary"""
        print(f"\\n🎉 DOWNLOAD SUMMARY:")
        print(f"   ✅ Successful: {self.download_stats['successful_downloads']}")
        print(f"   ❌ Failed: {self.download_stats['failed_downloads']}")
        print(f"   ⏱️  Total Time: {self.download_stats['download_time_seconds']:.1f}s")
        
        # Group by tier
        by_tier = {}
        for service, result in results.items():
            tier = result.get("tier", 0)
            if tier not in by_tier:
                by_tier[tier] = []
            by_tier[tier].append((service, result))
        
        for tier in sorted(by_tier.keys()):
            print(f"\\n   📦 TIER {tier}:")
            for service, result in by_tier[tier]:
                status = "✅" if result["success"] else "❌"
                print(f"      {status} {service}: {result['message']}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download wheels for microservices")
    parser.add_argument("--tier", type=int, default=5, help="Maximum tier to download (1-5)")
    parser.add_argument("--services", nargs="+", help="Specific services to download")
    parser.add_argument("--base-path", help="Base path for microservice project")
    
    args = parser.parse_args()
    
    manager = WheelsManager(args.base_path)
    
    if args.services:
        results = manager.download_specific_services(args.services)
    else:
        results = manager.download_by_tier(args.tier)
    
    manager.print_summary(results)
    
    # Save results to JSON
    results_file = manager.wheels_dir / "download_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "stats": manager.download_stats,
            "results": results
        }, f, indent=2)
    
    print(f"\\n📄 Results saved to: {results_file}")
    
    # Exit with error code if any downloads failed
    if manager.download_stats["failed_downloads"] > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()