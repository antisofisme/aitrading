#!/usr/bin/env python3
"""
Comprehensive Central Hub Service Test Script
Tests all functionality and reports readiness status
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any

class CentralHubTester:
    """Comprehensive Central Hub functionality tester"""

    def __init__(self, base_url: str = "http://localhost:7000"):
        self.base_url = base_url
        self.results: Dict[str, Dict[str, Any]] = {}

    async def run_comprehensive_test(self):
        """Run all tests and generate report"""
        print("🔬 Starting Comprehensive Central Hub Testing...")
        print("=" * 60)

        async with aiohttp.ClientSession() as session:
            # Core Health Tests
            await self.test_service_health(session)
            await self.test_basic_endpoints(session)

            # Configuration Management Tests
            await self.test_configuration_apis(session)

            # Service Discovery Tests
            await self.test_service_discovery(session)

            # Transport Integration Tests
            await self.test_transport_status(session)

            # Database Integration Tests
            await self.test_database_integration(session)

            # Generate comprehensive report
            self.generate_report()

    async def test_service_health(self, session: aiohttp.ClientSession):
        """Test service health and availability"""
        print("🏥 Testing Service Health...")

        test_results = {
            "container_status": "unknown",
            "http_availability": "unknown",
            "health_endpoint": "unknown",
            "response_time": 0
        }

        try:
            start_time = time.time()
            async with session.get(f"{self.base_url}/health") as response:
                response_time = (time.time() - start_time) * 1000
                test_results["response_time"] = round(response_time, 2)

                if response.status == 200:
                    health_data = await response.json()
                    test_results["http_availability"] = "healthy"
                    test_results["health_endpoint"] = "responsive"
                    test_results["health_data"] = health_data
                else:
                    test_results["http_availability"] = "degraded"
                    test_results["health_endpoint"] = f"http_{response.status}"

        except Exception as e:
            test_results["http_availability"] = "failed"
            test_results["health_endpoint"] = "unreachable"
            test_results["error"] = str(e)

        self.results["service_health"] = test_results
        print(f"  ✅ Health Status: {test_results['health_endpoint']}")
        print(f"  📊 Response Time: {test_results['response_time']}ms")

    async def test_basic_endpoints(self, session: aiohttp.ClientSession):
        """Test basic API endpoints"""
        print("🔗 Testing Basic Endpoints...")

        endpoints = {
            "/": "root_info",
            "/health": "health_check",
            "/discovery": "service_discovery",
            "/metrics": "metrics_collection"
        }

        test_results = {}

        for endpoint, test_name in endpoints.items():
            try:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        test_results[test_name] = {
                            "status": "success",
                            "http_code": response.status,
                            "data_keys": list(data.keys()) if isinstance(data, dict) else None
                        }
                    else:
                        test_results[test_name] = {
                            "status": "failed",
                            "http_code": response.status
                        }
            except Exception as e:
                test_results[test_name] = {
                    "status": "error",
                    "error": str(e)
                }

        self.results["basic_endpoints"] = test_results

        for endpoint, result in test_results.items():
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"  {status_emoji} {endpoint}: {result['status']}")

    async def test_configuration_apis(self, session: aiohttp.ClientSession):
        """Test configuration management APIs"""
        print("⚙️  Testing Configuration APIs...")

        test_results = {}

        # Test config retrieval
        config_payload = {
            "service_name": "test-service",
            "environment": "development"
        }

        try:
            async with session.post(
                f"{self.base_url}/config",
                json=config_payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                test_results["config_retrieval"] = {
                    "status": "success" if response.status in [200, 201] else "failed",
                    "http_code": response.status
                }
                if response.status in [200, 201]:
                    config_data = await response.json()
                    test_results["config_retrieval"]["response_data"] = config_data

        except Exception as e:
            test_results["config_retrieval"] = {
                "status": "error",
                "error": str(e)
            }

        self.results["configuration_apis"] = test_results

        status_emoji = "✅" if test_results.get("config_retrieval", {}).get("status") == "success" else "❌"
        print(f"  {status_emoji} Configuration Retrieval: {test_results.get('config_retrieval', {}).get('status', 'unknown')}")

    async def test_service_discovery(self, session: aiohttp.ClientSession):
        """Test service discovery functionality"""
        print("🔍 Testing Service Discovery...")

        test_results = {}

        # Test service registration (if available)
        registration_payload = {
            "service_name": "test-client",
            "host": "localhost",
            "port": 9999,
            "health_endpoint": "/health"
        }

        try:
            async with session.post(
                f"{self.base_url}/discovery/register",
                json=registration_payload
            ) as response:
                test_results["service_registration"] = {
                    "status": "success" if response.status in [200, 201] else "failed",
                    "http_code": response.status
                }
        except Exception as e:
            test_results["service_registration"] = {
                "status": "error",
                "error": str(e)
            }

        # Test service list retrieval
        try:
            async with session.get(f"{self.base_url}/discovery/services") as response:
                test_results["service_list"] = {
                    "status": "success" if response.status == 200 else "failed",
                    "http_code": response.status
                }
                if response.status == 200:
                    services_data = await response.json()
                    test_results["service_list"]["services_count"] = len(services_data.get("services", []))

        except Exception as e:
            test_results["service_list"] = {
                "status": "error",
                "error": str(e)
            }

        self.results["service_discovery"] = test_results

        for test_name, result in test_results.items():
            status_emoji = "✅" if result.get("status") == "success" else "❌"
            print(f"  {status_emoji} {test_name.replace('_', ' ').title()}: {result.get('status', 'unknown')}")

    async def test_transport_status(self, session: aiohttp.ClientSession):
        """Test transport method integration status"""
        print("🚌 Testing Transport Integration...")

        try:
            async with session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    service_info = await response.json()
                    transports = service_info.get("transports", {})

                    test_results = {
                        "nats_status": "connected" if transports.get("nats") else "disconnected",
                        "kafka_status": "connected" if transports.get("kafka") else "disconnected",
                        "redis_status": "connected" if transports.get("redis") else "disconnected",
                        "grpc_status": "enabled" if transports.get("grpc") else "disabled",
                        "http_status": "enabled" if transports.get("http") else "disabled"
                    }
                else:
                    test_results = {"error": f"Failed to get service info: HTTP {response.status}"}

        except Exception as e:
            test_results = {"error": str(e)}

        self.results["transport_integration"] = test_results

        for transport, status in test_results.items():
            if "error" not in transport:
                status_emoji = "✅" if "connected" in status or "enabled" in status else "❌"
                print(f"  {status_emoji} {transport.replace('_', ' ').title()}: {status}")

    async def test_database_integration(self, session: aiohttp.ClientSession):
        """Test database integration status"""
        print("💾 Testing Database Integration...")

        try:
            async with session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    service_info = await response.json()

                    test_results = {
                        "database_connected": service_info.get("database", False),
                        "cache_connected": service_info.get("cache", False),
                        "registered_services": service_info.get("registered_services", 0)
                    }
                else:
                    test_results = {"error": f"Failed to get service info: HTTP {response.status}"}

        except Exception as e:
            test_results = {"error": str(e)}

        self.results["database_integration"] = test_results

        if "error" not in test_results:
            db_emoji = "✅" if test_results["database_connected"] else "❌"
            cache_emoji = "✅" if test_results["cache_connected"] else "❌"
            print(f"  {db_emoji} Database Connection: {'connected' if test_results['database_connected'] else 'disconnected'}")
            print(f"  {cache_emoji} Cache Connection: {'connected' if test_results['cache_connected'] else 'disconnected'}")
            print(f"  📊 Registered Services: {test_results['registered_services']}")

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📋 CENTRAL HUB COMPREHENSIVE TEST REPORT")
        print("=" * 60)

        # Overall Status Assessment
        total_tests = 0
        passed_tests = 0

        for category, tests in self.results.items():
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and "status" in result:
                        total_tests += 1
                        if result["status"] == "success":
                            passed_tests += 1
                    elif isinstance(result, bool):
                        total_tests += 1
                        if result:
                            passed_tests += 1

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")

        # Detailed Results
        print("\n🔍 DETAILED RESULTS:")
        print("-" * 40)

        for category, results in self.results.items():
            print(f"\n📁 {category.replace('_', ' ').title()}:")
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, dict):
                        status = value.get("status", "unknown")
                        emoji = "✅" if status == "success" else "❌" if status == "failed" else "⚠️"
                        print(f"  {emoji} {key.replace('_', ' ').title()}: {status}")
                        if "error" in value:
                            print(f"    ⚠️  Error: {value['error']}")
                    else:
                        emoji = "✅" if value else "❌"
                        print(f"  {emoji} {key.replace('_', ' ').title()}: {value}")

        # Readiness Assessment
        print("\n" + "=" * 60)
        print("🎯 CENTRAL HUB READINESS ASSESSMENT")
        print("=" * 60)

        readiness_criteria = {
            "Service Health": self.results.get("service_health", {}).get("health_endpoint") == "responsive",
            "Database Connection": self.results.get("database_integration", {}).get("database_connected", False),
            "Cache Connection": self.results.get("database_integration", {}).get("cache_connected", False),
            "Transport Methods": any([
                self.results.get("transport_integration", {}).get("nats_status") == "connected",
                self.results.get("transport_integration", {}).get("kafka_status") == "connected"
            ]),
            "API Endpoints": any([
                test.get("status") == "success"
                for test in self.results.get("basic_endpoints", {}).values()
            ])
        }

        ready_count = sum(readiness_criteria.values())
        total_criteria = len(readiness_criteria)

        for criterion, status in readiness_criteria.items():
            emoji = "✅" if status else "❌"
            print(f"{emoji} {criterion}: {'READY' if status else 'NOT READY'}")

        overall_readiness = ready_count / total_criteria

        if overall_readiness >= 0.8:
            readiness_status = "🟢 READY FOR PRODUCTION"
        elif overall_readiness >= 0.6:
            readiness_status = "🟡 READY WITH WARNINGS"
        else:
            readiness_status = "🔴 NOT READY"

        print(f"\n🎯 OVERALL READINESS: {readiness_status}")
        print(f"📊 Readiness Score: {overall_readiness*100:.1f}% ({ready_count}/{total_criteria})")

        if overall_readiness < 1.0:
            print("\n⚠️  RECOMMENDED ACTIONS:")
            for criterion, status in readiness_criteria.items():
                if not status:
                    print(f"  • Fix {criterion}")

        print("\n" + "=" * 60)
        print("✅ Central Hub Testing Complete!")
        print("=" * 60)

async def main():
    """Run comprehensive Central Hub tests"""
    tester = CentralHubTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())