#!/usr/bin/env python3
"""
MetaTrader 5 Bridge - Real MT5 Integration
Connects to MT5 terminal and streams real-time market data
"""

import MetaTrader5 as mt5
import sys
import json
import time
import argparse
import threading
import queue
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import signal
import asyncio

class MT5Bridge:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.connections = []
        self.data_queue = queue.Queue()
        self.performance_metrics = {
            'ticks_processed': 0,
            'ticks_per_second': 0,
            'average_latency': 0,
            'connection_uptime': 0,
            'start_time': time.time(),
            'last_tick_time': 0
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Signal handling for graceful shutdown
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    async def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:
            # Initialize MT5
            if not mt5.initialize():
                error_msg = f"MT5 initialization failed: {mt5.last_error()}"
                self.logger.error(error_msg)
                print(f"ERROR:{error_msg}")
                return False

            # Login to MT5
            if not mt5.login(
                login=int(self.config['login']),
                password=self.config['password'],
                server=self.config['server']
            ):
                error_msg = f"MT5 login failed: {mt5.last_error()}"
                self.logger.error(error_msg)
                print(f"ERROR:{error_msg}")
                return False

            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                error_msg = "Failed to get account info"
                self.logger.error(error_msg)
                print(f"ERROR:{error_msg}")
                return False

            self.logger.info(f"Connected to MT5 account: {account_info.login}")

            # Initialize multiple connections for the pool
            await self.initialize_connection_pool()

            print("READY:MT5 Bridge initialized successfully")
            return True

        except Exception as e:
            error_msg = f"MT5 initialization error: {str(e)}"
            self.logger.error(error_msg)
            print(f"ERROR:{error_msg}")
            return False

    async def initialize_connection_pool(self):
        """Initialize connection pool for high-frequency trading"""
        max_connections = int(self.config.get('max_connections', 5))

        for i in range(max_connections):
            connection = {
                'id': f'conn_{i}',
                'active': True,
                'last_used': time.time(),
                'requests': 0,
                'errors': 0
            }
            self.connections.append(connection)

        self.logger.info(f"Initialized connection pool with {len(self.connections)} connections")

    def get_optimal_connection(self) -> str:
        """Get the connection with the lowest load"""
        if not self.connections:
            return 'conn_0'

        # Find connection with lowest request count
        optimal = min(self.connections, key=lambda x: x['requests'] if x['active'] else float('inf'))
        optimal['requests'] += 1
        optimal['last_used'] = time.time()

        return optimal['id']

    async def start_streaming(self, symbols: List[str], target_tps: int = 50):
        """Start real-time data streaming"""
        self.logger.info(f"Starting data streaming for symbols: {symbols}")
        self.running = True

        # Start multiple threads for different data types
        threads = [
            threading.Thread(target=self.tick_streaming_worker, args=(symbols, target_tps)),
            threading.Thread(target=self.market_data_worker, args=(symbols,)),
            threading.Thread(target=self.performance_monitor_worker),
            threading.Thread(target=self.data_processor_worker)
        ]

        for thread in threads:
            thread.daemon = True
            thread.start()

        self.logger.info("All streaming workers started")

    def tick_streaming_worker(self, symbols: List[str], target_tps: int):
        """Worker thread for tick data streaming"""
        tick_interval = 1.0 / target_tps  # Target interval between ticks

        while self.running:
            try:
                for symbol in symbols:
                    start_time = time.time()

                    # Get latest tick
                    tick = mt5.symbol_info_tick(symbol)
                    if tick is not None:
                        tick_data = {
                            'type': 'tick',
                            'symbol': symbol,
                            'bid': tick.bid,
                            'ask': tick.ask,
                            'last': tick.last,
                            'volume': tick.volume,
                            'time': tick.time,
                            'flags': tick.flags,
                            'volume_real': tick.volume_real,
                            'timestamp': int(time.time() * 1000),
                            'connection_id': self.get_optimal_connection(),
                            'processing_latency': 0
                        }

                        # Calculate processing latency
                        processing_time = (time.time() - start_time) * 1000
                        tick_data['processing_latency'] = processing_time

                        # Queue for processing
                        self.data_queue.put(('tick', tick_data))

                        # Update metrics
                        self.performance_metrics['ticks_processed'] += 1
                        self.performance_metrics['last_tick_time'] = time.time()

                        # Update average latency
                        current_avg = self.performance_metrics['average_latency']
                        if current_avg == 0:
                            self.performance_metrics['average_latency'] = processing_time
                        else:
                            self.performance_metrics['average_latency'] = (current_avg * 0.9) + (processing_time * 0.1)

                # Control tick rate
                elapsed = time.time() - start_time
                sleep_time = max(0, tick_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                self.logger.error(f"Tick streaming error: {e}")
                time.sleep(0.1)  # Brief pause on error

    def market_data_worker(self, symbols: List[str]):
        """Worker thread for market data collection"""
        while self.running:
            try:
                for symbol in symbols:
                    # Get symbol info
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info is not None:
                        market_data = {
                            'type': 'market_data',
                            'symbol': symbol,
                            'currency_base': symbol_info.currency_base,
                            'currency_profit': symbol_info.currency_profit,
                            'currency_margin': symbol_info.currency_margin,
                            'contract_size': symbol_info.contract_size,
                            'digits': symbol_info.digits,
                            'point': symbol_info.point,
                            'spread': symbol_info.spread,
                            'stop_level': symbol_info.stops_level,
                            'freeze_level': symbol_info.freeze_level,
                            'trade_mode': symbol_info.trade_mode,
                            'timestamp': int(time.time() * 1000),
                            'connection_id': self.get_optimal_connection()
                        }

                        self.data_queue.put(('market_data', market_data))

                # Update every 5 seconds
                time.sleep(5)

            except Exception as e:
                self.logger.error(f"Market data error: {e}")
                time.sleep(5)

    def performance_monitor_worker(self):
        """Worker thread for performance monitoring"""
        while self.running:
            try:
                # Calculate current TPS
                current_time = time.time()
                uptime = current_time - self.performance_metrics['start_time']

                if uptime > 0:
                    self.performance_metrics['ticks_per_second'] = (
                        self.performance_metrics['ticks_processed'] / uptime
                    )
                    self.performance_metrics['connection_uptime'] = uptime

                # Send metrics update
                metrics_data = {
                    'type': 'metrics',
                    'timestamp': int(current_time * 1000),
                    **self.performance_metrics,
                    'connection_pool': [
                        {
                            'id': conn['id'],
                            'active': conn['active'],
                            'requests': conn['requests'],
                            'last_used': conn['last_used']
                        }
                        for conn in self.connections
                    ]
                }

                print(f"METRICS:{json.dumps(metrics_data)}")

                # Monitor every 10 seconds
                time.sleep(10)

            except Exception as e:
                self.logger.error(f"Performance monitor error: {e}")
                time.sleep(10)

    def data_processor_worker(self):
        """Worker thread for processing and sending data"""
        while self.running:
            try:
                # Process queued data
                if not self.data_queue.empty():
                    data_type, data = self.data_queue.get(timeout=1)

                    if data_type == 'tick':
                        print(f"TICK:{json.dumps(data)}")
                    elif data_type == 'market_data':
                        print(f"MARKET:{json.dumps(data)}")

                    self.data_queue.task_done()
                else:
                    time.sleep(0.01)  # Short sleep when queue is empty

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Data processor error: {e}")

    def handle_command(self, command: str):
        """Handle commands from Node.js client"""
        try:
            if command.startswith('START_STREAMING:'):
                config_str = command[16:]  # Remove 'START_STREAMING:' prefix
                streaming_config = json.loads(config_str)

                symbols = streaming_config.get('symbols', ['EURUSD'])
                target_tps = streaming_config.get('targetTPS', 50)

                asyncio.create_task(self.start_streaming(symbols, target_tps))

            elif command.startswith('SEND_ORDER:'):
                order_str = command[11:]  # Remove 'SEND_ORDER:' prefix
                order_data = json.loads(order_str)
                self.send_order(order_data)

            elif command == 'GET_ACCOUNT':
                self.send_account_info()

            elif command == 'STOP':
                self.shutdown()

        except Exception as e:
            error_msg = f"Command handling error: {str(e)}"
            self.logger.error(error_msg)
            print(f"ERROR:{error_msg}")

    def send_order(self, order_data: Dict[str, Any]):
        """Send trading order to MT5"""
        try:
            # Prepare order request
            request = {
                'action': getattr(mt5, f"TRADE_ACTION_{order_data.get('action', 'DEAL')}"),
                'symbol': order_data['symbol'],
                'volume': float(order_data['volume']),
                'type': getattr(mt5, f"ORDER_TYPE_{order_data.get('type', 'BUY')}"),
                'price': float(order_data.get('price', 0)),
                'sl': float(order_data.get('sl', 0)),
                'tp': float(order_data.get('tp', 0)),
                'deviation': int(order_data.get('deviation', 20)),
                'magic': int(order_data.get('magic', 0)),
                'comment': order_data.get('comment', 'AI Trading'),
                'type_time': getattr(mt5, 'ORDER_TIME_GTC'),
                'type_filling': getattr(mt5, 'ORDER_FILLING_IOC'),
            }

            # Send order
            result = mt5.order_send(request)

            # Send result back
            order_result = {
                'type': 'order_result',
                'request_id': order_data.get('request_id'),
                'retcode': result.retcode,
                'deal': result.deal,
                'order': result.order,
                'volume': result.volume,
                'price': result.price,
                'bid': result.bid,
                'ask': result.ask,
                'comment': result.comment,
                'request': result.request._asdict() if result.request else None,
                'timestamp': int(time.time() * 1000)
            }

            print(f"ORDER_RESULT:{json.dumps(order_result)}")

        except Exception as e:
            error_msg = f"Order execution error: {str(e)}"
            self.logger.error(error_msg)
            print(f"ERROR:{error_msg}")

    def send_account_info(self):
        """Send account information"""
        try:
            account_info = mt5.account_info()
            if account_info is not None:
                account_data = {
                    'type': 'account_info',
                    'login': account_info.login,
                    'trade_mode': account_info.trade_mode,
                    'leverage': account_info.leverage,
                    'limit_orders': account_info.limit_orders,
                    'margin_so_mode': account_info.margin_so_mode,
                    'trade_allowed': account_info.trade_allowed,
                    'trade_expert': account_info.trade_expert,
                    'margin_mode': account_info.margin_mode,
                    'currency_digits': account_info.currency_digits,
                    'balance': account_info.balance,
                    'credit': account_info.credit,
                    'profit': account_info.profit,
                    'equity': account_info.equity,
                    'margin': account_info.margin,
                    'margin_free': account_info.margin_free,
                    'margin_level': account_info.margin_level,
                    'timestamp': int(time.time() * 1000)
                }

                print(f"ACCOUNT_INFO:{json.dumps(account_data)}")

        except Exception as e:
            error_msg = f"Account info error: {str(e)}"
            self.logger.error(error_msg)
            print(f"ERROR:{error_msg}")

    def shutdown(self):
        """Shutdown MT5 bridge"""
        self.logger.info("Shutting down MT5 bridge...")
        self.running = False

        # Disconnect from MT5
        mt5.shutdown()

        self.logger.info("MT5 bridge shutdown complete")
        sys.exit(0)

    async def run(self):
        """Main run loop"""
        if not await self.initialize():
            sys.exit(1)

        # Process stdin commands
        try:
            while self.running:
                try:
                    # Check for commands from stdin (non-blocking)
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        command = sys.stdin.readline().strip()
                        if command:
                            self.handle_command(command)

                    # Small sleep to prevent busy waiting
                    await asyncio.sleep(0.01)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.logger.error(f"Main loop error: {e}")
                    time.sleep(1)

        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
        finally:
            self.shutdown()

def main():
    parser = argparse.ArgumentParser(description='MetaTrader 5 Bridge')
    parser.add_argument('--server', required=True, help='MT5 server name')
    parser.add_argument('--login', required=True, help='MT5 login')
    parser.add_argument('--password', required=True, help='MT5 password')
    parser.add_argument('--max-connections', type=int, default=5, help='Maximum connections')
    parser.add_argument('--target-tps', type=int, default=50, help='Target ticks per second')

    args = parser.parse_args()

    config = {
        'server': args.server,
        'login': args.login,
        'password': args.password,
        'max_connections': args.max_connections,
        'target_tps': args.target_tps
    }

    bridge = MT5Bridge(config)

    # Run the bridge
    try:
        asyncio.run(bridge.run())
    except KeyboardInterrupt:
        print("Bridge interrupted by user")
    except Exception as e:
        print(f"ERROR:Bridge fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()