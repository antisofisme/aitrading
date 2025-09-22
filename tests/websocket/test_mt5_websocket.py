"""
WebSocket Testing Framework for MT5 Bridge
Tests real-time communication with MetaTrader 5 bridge service
"""

import asyncio
import websockets
import json
import pytest
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebSocketTestResult:
    """WebSocket test result container"""
    test_name: str
    connection_time_ms: float
    message_latency_ms: float
    messages_sent: int
    messages_received: int
    success: bool
    error_message: str = None

@dataclass
class MT5Message:
    """MT5 WebSocket message structure"""
    type: str
    symbol: str
    data: Dict[str, Any]
    timestamp: int

class MT5WebSocketTester:
    """Comprehensive WebSocket testing for MT5 bridge"""

    def __init__(self, ws_url: str = "ws://localhost:8009/ws"):
        self.ws_url = ws_url
        self.test_results: List[WebSocketTestResult] = []
        self.message_queue = queue.Queue()
        self.connection_pool = []

    async def test_connection_establishment(self):
        """Test WebSocket connection establishment"""
        logger.info("Testing WebSocket connection establishment...")

        start_time = time.time()
        try:
            async with websockets.connect(self.ws_url, timeout=5) as websocket:
                connection_time = (time.time() - start_time) * 1000

                # Send ping to verify connection
                ping_data = {
                    "type": "ping",
                    "timestamp": int(time.time() * 1000)
                }

                await websocket.send(json.dumps(ping_data))
                response = await asyncio.wait_for(websocket.recv(), timeout=5)

                result = WebSocketTestResult(
                    test_name="connection_establishment",
                    connection_time_ms=connection_time,
                    message_latency_ms=0,
                    messages_sent=1,
                    messages_received=1,
                    success=True
                )

                self.test_results.append(result)
                logger.info(f"✅ Connection established in {connection_time:.2f}ms")
                return True

        except Exception as e:
            result = WebSocketTestResult(
                test_name="connection_establishment",
                connection_time_ms=0,
                message_latency_ms=0,
                messages_sent=0,
                messages_received=0,
                success=False,
                error_message=str(e)
            )
            self.test_results.append(result)
            logger.error(f"❌ Connection failed: {str(e)}")
            return False

    async def test_market_data_subscription(self):
        """Test market data subscription and real-time updates"""
        logger.info("Testing market data subscription...")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Subscribe to EURUSD market data
                subscription_msg = {
                    "type": "subscribe",
                    "symbol": "EURUSD",
                    "data_type": "tick",
                    "timestamp": int(time.time() * 1000)
                }

                start_time = time.time()
                await websocket.send(json.dumps(subscription_msg))

                # Wait for subscription confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_data = json.loads(response)

                if response_data.get("type") == "subscription_confirmed":
                    logger.info("✅ Market data subscription confirmed")

                    # Wait for market data updates
                    messages_received = 0
                    total_latency = 0

                    for _ in range(10):  # Receive 10 market data updates
                        try:
                            msg_start = time.time()
                            data = await asyncio.wait_for(websocket.recv(), timeout=15)
                            latency = (time.time() - msg_start) * 1000

                            message = json.loads(data)
                            if message.get("type") == "market_data":
                                messages_received += 1
                                total_latency += latency
                                logger.info(f"Market data received: {message['data']['symbol']} - Latency: {latency:.2f}ms")

                        except asyncio.TimeoutError:
                            logger.warning("Timeout waiting for market data")
                            break

                    avg_latency = total_latency / messages_received if messages_received > 0 else 0

                    result = WebSocketTestResult(
                        test_name="market_data_subscription",
                        connection_time_ms=(time.time() - start_time) * 1000,
                        message_latency_ms=avg_latency,
                        messages_sent=1,
                        messages_received=messages_received,
                        success=messages_received >= 5  # At least 5 updates
                    )

                    self.test_results.append(result)
                    return messages_received >= 5

                else:
                    logger.error("❌ Subscription not confirmed")
                    return False

        except Exception as e:
            logger.error(f"❌ Market data subscription failed: {str(e)}")
            return False

    async def test_order_placement_via_websocket(self):
        """Test order placement through WebSocket"""
        logger.info("Testing order placement via WebSocket...")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Place a test order
                order_msg = {
                    "type": "place_order",
                    "symbol": "EURUSD",
                    "order_type": "market",
                    "side": "buy",
                    "volume": 0.01,
                    "timestamp": int(time.time() * 1000)
                }

                start_time = time.time()
                await websocket.send(json.dumps(order_msg))

                # Wait for order confirmation
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                response_time = (time.time() - start_time) * 1000

                order_response = json.loads(response)

                if order_response.get("type") == "order_confirmation":
                    result = WebSocketTestResult(
                        test_name="order_placement",
                        connection_time_ms=0,
                        message_latency_ms=response_time,
                        messages_sent=1,
                        messages_received=1,
                        success=True
                    )

                    self.test_results.append(result)
                    logger.info(f"✅ Order placed successfully in {response_time:.2f}ms")
                    return True

                else:
                    logger.error(f"❌ Order placement failed: {order_response}")
                    return False

        except Exception as e:
            logger.error(f"❌ Order placement error: {str(e)}")
            return False

    async def test_concurrent_connections(self, num_connections: int = 50):
        """Test multiple concurrent WebSocket connections"""
        logger.info(f"Testing {num_connections} concurrent WebSocket connections...")

        async def single_connection_test(connection_id: int):
            """Test single WebSocket connection"""
            try:
                start_time = time.time()
                async with websockets.connect(self.ws_url, timeout=10) as websocket:
                    connection_time = (time.time() - start_time) * 1000

                    # Send test message
                    test_msg = {
                        "type": "test",
                        "connection_id": connection_id,
                        "timestamp": int(time.time() * 1000)
                    }

                    msg_start = time.time()
                    await websocket.send(json.dumps(test_msg))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    message_latency = (time.time() - msg_start) * 1000

                    return {
                        "connection_id": connection_id,
                        "success": True,
                        "connection_time": connection_time,
                        "message_latency": message_latency
                    }

            except Exception as e:
                return {
                    "connection_id": connection_id,
                    "success": False,
                    "error": str(e)
                }

        # Run concurrent connections
        tasks = [single_connection_test(i) for i in range(num_connections)]
        start_time = time.time()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        successful_connections = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        avg_connection_time = np.mean([r["connection_time"] for r in results
                                     if isinstance(r, dict) and r.get("success")])
        avg_message_latency = np.mean([r["message_latency"] for r in results
                                     if isinstance(r, dict) and r.get("success")])

        result = WebSocketTestResult(
            test_name="concurrent_connections",
            connection_time_ms=avg_connection_time,
            message_latency_ms=avg_message_latency,
            messages_sent=num_connections,
            messages_received=successful_connections,
            success=successful_connections >= num_connections * 0.9  # 90% success rate
        )

        self.test_results.append(result)

        logger.info(f"Concurrent connection results:")
        logger.info(f"  Successful connections: {successful_connections}/{num_connections}")
        logger.info(f"  Average connection time: {avg_connection_time:.2f}ms")
        logger.info(f"  Average message latency: {avg_message_latency:.2f}ms")
        logger.info(f"  Total test time: {total_time:.2f}s")

        return successful_connections >= num_connections * 0.9

    async def test_message_throughput(self, duration_seconds: int = 30):
        """Test WebSocket message throughput"""
        logger.info(f"Testing message throughput for {duration_seconds} seconds...")

        try:
            async with websockets.connect(self.ws_url) as websocket:
                messages_sent = 0
                messages_received = 0
                total_latency = 0

                # Start receiving messages
                async def message_receiver():
                    nonlocal messages_received, total_latency
                    while True:
                        try:
                            start_time = time.time()
                            data = await asyncio.wait_for(websocket.recv(), timeout=1)
                            latency = (time.time() - start_time) * 1000
                            messages_received += 1
                            total_latency += latency
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            break

                # Start receiver task
                receiver_task = asyncio.create_task(message_receiver())

                # Send messages
                start_time = time.time()
                while time.time() - start_time < duration_seconds:
                    test_msg = {
                        "type": "throughput_test",
                        "sequence": messages_sent,
                        "timestamp": int(time.time() * 1000)
                    }

                    await websocket.send(json.dumps(test_msg))
                    messages_sent += 1
                    await asyncio.sleep(0.001)  # 1ms between messages

                # Stop receiver
                receiver_task.cancel()

                avg_latency = total_latency / messages_received if messages_received > 0 else 0
                throughput = messages_sent / duration_seconds

                result = WebSocketTestResult(
                    test_name="message_throughput",
                    connection_time_ms=0,
                    message_latency_ms=avg_latency,
                    messages_sent=messages_sent,
                    messages_received=messages_received,
                    success=throughput >= 100  # At least 100 msg/s
                )

                self.test_results.append(result)

                logger.info(f"Throughput test results:")
                logger.info(f"  Messages sent: {messages_sent}")
                logger.info(f"  Messages received: {messages_received}")
                logger.info(f"  Throughput: {throughput:.2f} msg/s")
                logger.info(f"  Average latency: {avg_latency:.2f}ms")

                return throughput >= 100

        except Exception as e:
            logger.error(f"❌ Throughput test failed: {str(e)}")
            return False

    async def test_connection_recovery(self):
        """Test WebSocket connection recovery after disconnect"""
        logger.info("Testing connection recovery...")

        try:
            # Establish initial connection
            websocket = await websockets.connect(self.ws_url)

            # Send initial message
            test_msg = {"type": "test", "message": "before_disconnect"}
            await websocket.send(json.dumps(test_msg))
            response1 = await websocket.recv()

            # Simulate connection drop
            await websocket.close()
            await asyncio.sleep(1)

            # Attempt reconnection
            start_time = time.time()
            websocket = await websockets.connect(self.ws_url)
            reconnection_time = (time.time() - start_time) * 1000

            # Send message after reconnection
            test_msg = {"type": "test", "message": "after_reconnect"}
            await websocket.send(json.dumps(test_msg))
            response2 = await websocket.recv()

            await websocket.close()

            result = WebSocketTestResult(
                test_name="connection_recovery",
                connection_time_ms=reconnection_time,
                message_latency_ms=0,
                messages_sent=2,
                messages_received=2,
                success=True
            )

            self.test_results.append(result)
            logger.info(f"✅ Connection recovery successful in {reconnection_time:.2f}ms")
            return True

        except Exception as e:
            logger.error(f"❌ Connection recovery failed: {str(e)}")
            return False

    async def run_full_websocket_test_suite(self):
        """Run complete WebSocket test suite"""
        logger.info("🚀 Starting WebSocket test suite...")

        test_results = {
            'connection_test': await self.test_connection_establishment(),
            'market_data_test': await self.test_market_data_subscription(),
            'order_placement_test': await self.test_order_placement_via_websocket(),
            'concurrent_connections_test': await self.test_concurrent_connections(25),
            'throughput_test': await self.test_message_throughput(15),
            'recovery_test': await self.test_connection_recovery()
        }

        # Calculate results
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = passed_tests / total_tests

        logger.info("\n" + "="*50)
        logger.info("WEBSOCKET TEST RESULTS")
        logger.info("="*50)

        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")

        logger.info(f"\nOverall Success Rate: {success_rate:.1%}")
        logger.info(f"Tests Passed: {passed_tests}/{total_tests}")

        # Performance summary
        if self.test_results:
            avg_latency = np.mean([r.message_latency_ms for r in self.test_results if r.message_latency_ms > 0])
            logger.info(f"Average message latency: {avg_latency:.2f}ms")

        return {
            'test_results': test_results,
            'success_rate': success_rate,
            'detailed_results': self.test_results
        }

# Pytest fixtures and test functions
@pytest.fixture
def mt5_websocket_tester():
    """Fixture for MT5 WebSocket tester"""
    return MT5WebSocketTester()

@pytest.mark.asyncio
async def test_websocket_connection(mt5_websocket_tester):
    """Test WebSocket connection"""
    result = await mt5_websocket_tester.test_connection_establishment()
    assert result, "WebSocket connection test failed"

@pytest.mark.asyncio
async def test_market_data_subscription(mt5_websocket_tester):
    """Test market data subscription"""
    result = await mt5_websocket_tester.test_market_data_subscription()
    assert result, "Market data subscription test failed"

@pytest.mark.asyncio
async def test_order_placement(mt5_websocket_tester):
    """Test order placement via WebSocket"""
    result = await mt5_websocket_tester.test_order_placement_via_websocket()
    assert result, "Order placement test failed"

@pytest.mark.asyncio
async def test_concurrent_ws_connections(mt5_websocket_tester):
    """Test concurrent WebSocket connections"""
    result = await mt5_websocket_tester.test_concurrent_connections(10)
    assert result, "Concurrent connections test failed"

@pytest.mark.asyncio
async def test_message_throughput(mt5_websocket_tester):
    """Test WebSocket message throughput"""
    result = await mt5_websocket_tester.test_message_throughput(10)
    assert result, "Message throughput test failed"

@pytest.mark.asyncio
async def test_connection_recovery(mt5_websocket_tester):
    """Test connection recovery"""
    result = await mt5_websocket_tester.test_connection_recovery()
    assert result, "Connection recovery test failed"

@pytest.mark.asyncio
async def test_full_websocket_suite(mt5_websocket_tester):
    """Run full WebSocket test suite"""
    results = await mt5_websocket_tester.run_full_websocket_test_suite()
    assert results['success_rate'] >= 0.8, f"WebSocket test success rate too low: {results['success_rate']:.1%}"

if __name__ == "__main__":
    async def main():
        tester = MT5WebSocketTester()
        results = await tester.run_full_websocket_test_suite()

        # Store results
        import json
        with open('/tmp/websocket_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nWebSocket test results saved. Success rate: {results['success_rate']:.1%}")

    asyncio.run(main())