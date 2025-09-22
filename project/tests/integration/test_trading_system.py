"""
Comprehensive Integration Tests for AI Trading Platform
Tests all 11 microservices with real-time performance validation
"""

import asyncio
import pytest
import aiohttp
import websocket
import json
import time
import psycopg2
import redis
import pymongo
from influxdb_client import InfluxDBClient
from clickhouse_driver import Client as ClickHouseClient
from typing import Dict, List, Any
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for each microservice"""
    name: str
    port: int
    health_endpoint: str
    test_endpoints: List[str]
    expected_response_time_ms: int = 500

@dataclass
class TestResult:
    """Test result container"""
    service: str
    endpoint: str
    response_time_ms: float
    status_code: int
    success: bool
    error_message: str = None

class TradingSystemIntegrationTest:
    """Comprehensive integration test suite for the trading platform"""

    def __init__(self):
        self.base_url = "http://localhost"
        self.services = [
            ServiceConfig("gateway", 8000, "/health", ["/api/v1/status", "/api/v1/trades"]),
            ServiceConfig("market-data", 8001, "/health", ["/api/v1/symbols", "/api/v1/prices"]),
            ServiceConfig("trading-engine", 8002, "/health", ["/api/v1/orders", "/api/v1/positions"]),
            ServiceConfig("portfolio", 8003, "/health", ["/api/v1/portfolio", "/api/v1/performance"]),
            ServiceConfig("risk-management", 8004, "/health", ["/api/v1/risk", "/api/v1/limits"]),
            ServiceConfig("analytics", 8005, "/health", ["/api/v1/analytics", "/api/v1/reports"]),
            ServiceConfig("notification", 8006, "/health", ["/api/v1/alerts", "/api/v1/webhooks"]),
            ServiceConfig("user-management", 8007, "/health", ["/api/v1/users", "/api/v1/auth"]),
            ServiceConfig("audit", 8008, "/health", ["/api/v1/logs", "/api/v1/compliance"]),
            ServiceConfig("mt5-bridge", 8009, "/health", ["/api/v1/mt5/connect", "/api/v1/mt5/symbols"]),
            ServiceConfig("backtesting", 8010, "/health", ["/api/v1/backtest", "/api/v1/strategies"])
        ]

        self.database_configs = {
            'postgresql': {'host': 'localhost', 'port': 5432, 'database': 'trading_db'},
            'influxdb': {'host': 'localhost', 'port': 8086, 'database': 'market_data'},
            'redis': {'host': 'localhost', 'port': 6379, 'db': 0},
            'mongodb': {'host': 'localhost', 'port': 27017, 'database': 'trading_analytics'},
            'clickhouse': {'host': 'localhost', 'port': 9000, 'database': 'trading_events'}
        }

        self.test_results: List[TestResult] = []
        self.performance_metrics = {}

    async def test_all_services_health(self):
        """Test health endpoints of all microservices"""
        logger.info("Testing health endpoints for all 11 microservices...")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for service in self.services:
                task = self._test_service_health(session, service)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            healthy_services = sum(1 for r in results if isinstance(r, bool) and r)
            logger.info(f"Health check results: {healthy_services}/{len(self.services)} services healthy")

            return healthy_services == len(self.services)

    async def _test_service_health(self, session: aiohttp.ClientSession, service: ServiceConfig) -> bool:
        """Test individual service health"""
        try:
            start_time = time.time()
            url = f"{self.base_url}:{service.port}{service.health_endpoint}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response_time = (time.time() - start_time) * 1000

                result = TestResult(
                    service=service.name,
                    endpoint=service.health_endpoint,
                    response_time_ms=response_time,
                    status_code=response.status,
                    success=response.status == 200
                )

                self.test_results.append(result)

                if response.status == 200:
                    logger.info(f"✅ {service.name} health check passed ({response_time:.2f}ms)")
                    return True
                else:
                    logger.error(f"❌ {service.name} health check failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"❌ {service.name} health check error: {str(e)}")
            result = TestResult(
                service=service.name,
                endpoint=service.health_endpoint,
                response_time_ms=0,
                status_code=0,
                success=False,
                error_message=str(e)
            )
            self.test_results.append(result)
            return False

    async def test_api_endpoints_performance(self):
        """Test all API endpoints with performance validation"""
        logger.info("Testing API endpoints performance (target: <500ms)...")

        async with aiohttp.ClientSession() as session:
            tasks = []
            for service in self.services:
                for endpoint in service.test_endpoints:
                    task = self._test_endpoint_performance(session, service, endpoint)
                    tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            fast_endpoints = sum(1 for r in results if isinstance(r, bool) and r)
            total_endpoints = sum(len(s.test_endpoints) for s in self.services)

            logger.info(f"Performance test results: {fast_endpoints}/{total_endpoints} endpoints under 500ms")
            return fast_endpoints / total_endpoints >= 0.8  # 80% should be fast

    async def _test_endpoint_performance(self, session: aiohttp.ClientSession,
                                       service: ServiceConfig, endpoint: str) -> bool:
        """Test individual endpoint performance"""
        try:
            start_time = time.time()
            url = f"{self.base_url}:{service.port}{endpoint}"

            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_time = (time.time() - start_time) * 1000

                result = TestResult(
                    service=service.name,
                    endpoint=endpoint,
                    response_time_ms=response_time,
                    status_code=response.status,
                    success=response_time < service.expected_response_time_ms
                )

                self.test_results.append(result)

                if response_time < service.expected_response_time_ms:
                    logger.info(f"✅ {service.name}{endpoint} performance OK ({response_time:.2f}ms)")
                    return True
                else:
                    logger.warning(f"⚠️ {service.name}{endpoint} slow ({response_time:.2f}ms)")
                    return False

        except Exception as e:
            logger.error(f"❌ {service.name}{endpoint} error: {str(e)}")
            return False

    async def test_real_time_data_flow(self):
        """Test real-time data flow between services"""
        logger.info("Testing real-time data flow...")

        # Simulate market data ingestion
        market_data_payload = {
            "symbol": "EURUSD",
            "bid": 1.0850,
            "ask": 1.0852,
            "timestamp": int(time.time() * 1000)
        }

        async with aiohttp.ClientSession() as session:
            # 1. Send market data
            start_time = time.time()

            async with session.post(
                f"{self.base_url}:8001/api/v1/prices",
                json=market_data_payload
            ) as response:
                if response.status != 200:
                    return False

            # 2. Check if data propagated to trading engine
            await asyncio.sleep(0.1)  # Allow propagation

            async with session.get(
                f"{self.base_url}:8002/api/v1/prices/EURUSD"
            ) as response:
                if response.status != 200:
                    return False

                data = await response.json()
                propagation_time = (time.time() - start_time) * 1000

                logger.info(f"Data propagation time: {propagation_time:.2f}ms")
                return propagation_time < 100  # Should propagate in <100ms

    def test_database_connections(self):
        """Test all database connections and basic operations"""
        logger.info("Testing database connections...")

        results = {}

        # Test PostgreSQL
        try:
            conn = psycopg2.connect(
                host=self.database_configs['postgresql']['host'],
                port=self.database_configs['postgresql']['port'],
                database=self.database_configs['postgresql']['database'],
                user='trading_user',
                password='trading_pass'
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            results['postgresql'] = True
            conn.close()
            logger.info("✅ PostgreSQL connection successful")
        except Exception as e:
            results['postgresql'] = False
            logger.error(f"❌ PostgreSQL connection failed: {str(e)}")

        # Test Redis
        try:
            r = redis.Redis(
                host=self.database_configs['redis']['host'],
                port=self.database_configs['redis']['port'],
                db=self.database_configs['redis']['db']
            )
            r.ping()
            results['redis'] = True
            logger.info("✅ Redis connection successful")
        except Exception as e:
            results['redis'] = False
            logger.error(f"❌ Redis connection failed: {str(e)}")

        # Test MongoDB
        try:
            client = pymongo.MongoClient(
                f"mongodb://{self.database_configs['mongodb']['host']}:{self.database_configs['mongodb']['port']}"
            )
            client.admin.command('ping')
            results['mongodb'] = True
            logger.info("✅ MongoDB connection successful")
        except Exception as e:
            results['mongodb'] = False
            logger.error(f"❌ MongoDB connection failed: {str(e)}")

        # Test InfluxDB
        try:
            client = InfluxDBClient(
                url=f"http://{self.database_configs['influxdb']['host']}:{self.database_configs['influxdb']['port']}",
                token="trading-token",
                org="trading-org"
            )
            health = client.health()
            results['influxdb'] = health.status == "pass"
            logger.info("✅ InfluxDB connection successful")
        except Exception as e:
            results['influxdb'] = False
            logger.error(f"❌ InfluxDB connection failed: {str(e)}")

        # Test ClickHouse
        try:
            client = ClickHouseClient(
                host=self.database_configs['clickhouse']['host'],
                port=self.database_configs['clickhouse']['port']
            )
            client.execute("SELECT 1")
            results['clickhouse'] = True
            logger.info("✅ ClickHouse connection successful")
        except Exception as e:
            results['clickhouse'] = False
            logger.error(f"❌ ClickHouse connection failed: {str(e)}")

        return all(results.values())

    async def test_concurrent_load(self, concurrent_users: int = 100, duration_seconds: int = 30):
        """Test system under concurrent load"""
        logger.info(f"Testing concurrent load: {concurrent_users} users for {duration_seconds}s...")

        async def user_session():
            """Simulate a user session"""
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                requests_made = 0

                while time.time() - start_time < duration_seconds:
                    try:
                        # Random endpoint selection
                        service = np.random.choice(self.services)
                        endpoint = np.random.choice(service.test_endpoints)

                        async with session.get(
                            f"{self.base_url}:{service.port}{endpoint}",
                            timeout=aiohttp.ClientTimeout(total=5)
                        ) as response:
                            requests_made += 1

                    except Exception:
                        pass

                    await asyncio.sleep(0.1)  # 10 requests per second per user

                return requests_made

        # Run concurrent user sessions
        tasks = [user_session() for _ in range(concurrent_users)]
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time
        total_requests = sum(r for r in results if isinstance(r, int))

        throughput = total_requests / total_time

        logger.info(f"Load test results:")
        logger.info(f"  Total requests: {total_requests}")
        logger.info(f"  Total time: {total_time:.2f}s")
        logger.info(f"  Throughput: {throughput:.2f} req/s")

        self.performance_metrics['load_test'] = {
            'total_requests': total_requests,
            'duration': total_time,
            'throughput': throughput,
            'concurrent_users': concurrent_users
        }

        return throughput > 100  # Should handle >100 req/s

    async def run_full_integration_test(self):
        """Run complete integration test suite"""
        logger.info("🚀 Starting full integration test suite...")

        test_results = {
            'health_check': await self.test_all_services_health(),
            'performance_check': await self.test_api_endpoints_performance(),
            'data_flow_check': await self.test_real_time_data_flow(),
            'database_check': self.test_database_connections(),
            'load_test_check': await self.test_concurrent_load()
        }

        # Calculate overall score
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests

        logger.info("\n" + "="*50)
        logger.info("INTEGRATION TEST RESULTS")
        logger.info("="*50)

        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")

        logger.info(f"\nOverall Success Rate: {success_rate:.1%}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")

        # Performance summary
        if self.test_results:
            avg_response_time = np.mean([r.response_time_ms for r in self.test_results])
            fast_responses = sum(1 for r in self.test_results if r.response_time_ms < 500)
            total_responses = len(self.test_results)

            logger.info(f"\nPerformance Summary:")
            logger.info(f"  Average response time: {avg_response_time:.2f}ms")
            logger.info(f"  Fast responses (<500ms): {fast_responses}/{total_responses} ({fast_responses/total_responses:.1%})")

        return {
            'test_results': test_results,
            'success_rate': success_rate,
            'performance_metrics': self.performance_metrics,
            'detailed_results': self.test_results
        }

# Pytest fixtures and test functions
@pytest.fixture
def trading_system():
    """Fixture for trading system integration test"""
    return TradingSystemIntegrationTest()

@pytest.mark.asyncio
async def test_health_endpoints(trading_system):
    """Test all service health endpoints"""
    result = await trading_system.test_all_services_health()
    assert result, "Not all services are healthy"

@pytest.mark.asyncio
async def test_api_performance(trading_system):
    """Test API endpoint performance"""
    result = await trading_system.test_api_endpoints_performance()
    assert result, "API performance requirements not met"

@pytest.mark.asyncio
async def test_data_flow(trading_system):
    """Test real-time data flow"""
    result = await trading_system.test_real_time_data_flow()
    assert result, "Real-time data flow test failed"

def test_databases(trading_system):
    """Test database connections"""
    result = trading_system.test_database_connections()
    assert result, "Database connection test failed"

@pytest.mark.asyncio
async def test_system_load(trading_system):
    """Test system under load"""
    result = await trading_system.test_concurrent_load(concurrent_users=50, duration_seconds=15)
    assert result, "Load test failed"

@pytest.mark.asyncio
async def test_full_integration(trading_system):
    """Run full integration test suite"""
    results = await trading_system.run_full_integration_test()
    assert results['success_rate'] >= 0.8, f"Integration test success rate too low: {results['success_rate']:.1%}"

if __name__ == "__main__":
    async def main():
        test_suite = TradingSystemIntegrationTest()
        results = await test_suite.run_full_integration_test()

        # Store results in memory for swarm coordination
        import json
        with open('/tmp/integration_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nTest results saved. Success rate: {results['success_rate']:.1%}")

    asyncio.run(main())