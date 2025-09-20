#!/usr/bin/env python3
"""
Health Check Script - API Gateway Service
Service-specific health monitoring following microservice patterns
"""

import asyncio
import aiohttp
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
import argparse

class ServiceHealthChecker:
    """Health checker for API Gateway service"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.service_name = "api-gateway"
        
    async def check_basic_health(self) -> Dict:
        """Check basic service health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time": response.headers.get('X-Response-Time', 'unknown'),
                            "data": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_ready_endpoint(self) -> Dict:
        """Check service readiness"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/ready", timeout=5) as response:
                    if response.status == 200:
                        return {"status": "ready"}
                    else:
                        return {
                            "status": "not_ready",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def check_api_endpoints(self) -> Dict:
        """Check key API endpoints"""
        endpoints = [
            "/api/v1/status",
            "/api/v1/auth/status",
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}", timeout=3) as response:
                        results[endpoint] = {
                            "status": "ok" if response.status < 500 else "error",
                            "http_status": response.status
                        }
                except Exception as e:
                    results[endpoint] = {
                        "status": "error",
                        "error": str(e)
                    }
                    
        return results
    
    async def check_dependencies(self) -> Dict:
        """Check service dependencies (Redis, etc.)"""
        # This would check Redis, database connections, etc.
        # For now, return a placeholder
        return {
            "redis": {"status": "unknown", "note": "dependency check not implemented"},
            "auth_service": {"status": "unknown", "note": "dependency check not implemented"}
        }
    
    async def run_full_health_check(self) -> Dict:
        """Run comprehensive health check"""
        print(f"🔍 Running health check for {self.service_name} service...")
        
        results = {
            "service": self.service_name,
            "timestamp": time.time(),
            "checks": {}
        }
        
        # Basic health
        print("📋 Checking basic health...")
        results["checks"]["health"] = await self.check_basic_health()
        
        # Readiness
        print("📋 Checking readiness...")
        results["checks"]["ready"] = await self.check_ready_endpoint()
        
        # API endpoints
        print("📋 Checking API endpoints...")
        results["checks"]["api_endpoints"] = await self.check_api_endpoints()
        
        # Dependencies
        print("📋 Checking dependencies...")
        results["checks"]["dependencies"] = await self.check_dependencies()
        
        return results
    
    def print_results(self, results: Dict, verbose: bool = False):
        """Print health check results in a readable format"""
        print(f"\n🏥 Health Check Results for {results['service']}")
        print("=" * 50)
        
        overall_status = "healthy"
        
        for check_name, check_result in results["checks"].items():
            if isinstance(check_result, dict):
                if check_result.get("status") in ["error", "unhealthy", "not_ready"]:
                    overall_status = "unhealthy"
                    print(f"❌ {check_name}: {check_result.get('status', 'unknown')}")
                    if check_result.get("error"):
                        print(f"   Error: {check_result['error']}")
                else:
                    print(f"✅ {check_name}: {check_result.get('status', 'ok')}")
                    
                if verbose and check_result.get("data"):
                    print(f"   Data: {json.dumps(check_result['data'], indent=2)}")
            else:
                print(f"📋 {check_name}: {check_result}")
        
        print(f"\n🎯 Overall Status: {'✅ HEALTHY' if overall_status == 'healthy' else '❌ UNHEALTHY'}")
        
        return overall_status == "healthy"

async def main():
    parser = argparse.ArgumentParser(description="API Gateway Service Health Check")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Service base URL (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--continuous", "-c", action="store_true",
                       help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=30,
                       help="Continuous check interval in seconds (default: 30)")
    
    args = parser.parse_args()
    
    checker = ServiceHealthChecker(args.url)
    
    if args.continuous:
        print(f"🔄 Starting continuous health monitoring (interval: {args.interval}s)")
        print("Press Ctrl+C to stop...")
        
        try:
            while True:
                results = await checker.run_full_health_check()
                is_healthy = checker.print_results(results, args.verbose)
                
                if not is_healthy:
                    print("⚠️  Service is unhealthy!")
                
                await asyncio.sleep(args.interval)
                
        except KeyboardInterrupt:
            print("\n👋 Health monitoring stopped")
    else:
        results = await checker.run_full_health_check()
        is_healthy = checker.print_results(results, args.verbose)
        
        # Exit with error code if unhealthy
        if not is_healthy:
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())