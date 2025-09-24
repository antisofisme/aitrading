"""
IC Markets MT5 Collector - MetaTrader5 Terminal Integration
Handles single MT5 connection to IC Markets untuk serve 1000+ users
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional

import MetaTrader5 as mt5
from nats.aio.client import Client as NATS
import sys
import os

# Add shared path for proto imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../01-core-infrastructure/central-hub/shared/generated/python'))

from common.tick_data_pb2 import MarketTick, QualityMetrics
from trading.broker_data_pb2 import BrokerTick, BrokerInfo

logger = logging.getLogger("ic_markets_mt5_collector")

class ICMarketsCollector:
    """IC Markets MT5 Data Collector using MetaTrader5 Python API"""

    def __init__(self, config: Dict):
        self.config = config
        self.broker_name = "ic_markets"
        self.broker_type = "mt5"
        self.nats_client: Optional[NATS] = None
        self.symbols = config.get('symbols', [])
        self.is_collecting = False

        # MT5 specific settings
        self.server = config['server']
        self.login = config['login']
        self.password = config['password']
        self.terminal_path = config.get('terminal_path', '')

        # Performance tracking
        self.tick_count = 0
        self.last_performance_log = time.time()

        # MT5 quality tracking
        self.mt5_metrics = {
            'total_ticks': 0,
            'valid_ticks': 0,
            'mt5_errors': 0,
            'connection_losses': 0
        }

    async def initialize(self):
        """Initialize MT5 terminal and NATS streaming"""
        try:
            # Initialize MetaTrader5 terminal
            if not mt5.initialize(path=self.terminal_path):
                error_code, error_msg = mt5.last_error()
                raise Exception(f"MT5 initialization failed: {error_code} - {error_msg}")

            # Connect to NATS message bus
            self.nats_client = NATS()
            await self.nats_client.connect("nats://nats-server:4222")

            logger.info(f"IC Markets MT5 collector initialized successfully")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            raise

    async def connect_to_mt5_broker(self):
        """Establish MT5 connection to IC Markets server"""
        try:
            # Login to MT5 broker account
            authorized = mt5.login(
                login=self.login,
                password=self.password,
                server=self.server
            )

            if not authorized:
                error_code, error_msg = mt5.last_error()
                raise Exception(f"MT5 login failed: {error_code} - {error_msg}")

            # Verify account info
            account_info = mt5.account_info()
            if account_info is None:
                raise Exception("Failed to retrieve MT5 account information")

            logger.info(f"Connected to IC Markets MT5 server: {self.server}")
            logger.info(f"Account: {account_info.login}, Balance: {account_info.balance}")
            return True

        except Exception as e:
            logger.error(f"MT5 broker connection failed: {e}")
            return False

    async def subscribe_to_symbols(self):
        """Subscribe to symbol tick data in MT5 terminal"""
        try:
            successful_subscriptions = 0

            for symbol in self.symbols:
                # Add symbol to Market Watch
                if not mt5.symbol_select(symbol, True):
                    logger.warning(f"Failed to select symbol {symbol} in Market Watch")
                    continue

                # Verify symbol information is available
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is None:
                    logger.warning(f"Symbol {symbol} information not available")
                    continue

                # Check if symbol allows trading (indicates data availability)
                if not symbol_info.visible:
                    logger.warning(f"Symbol {symbol} is not visible in Market Watch")
                    continue

                successful_subscriptions += 1
                logger.info(f"Successfully subscribed to {symbol} - Spread: {symbol_info.spread}")

            logger.info(f"MT5 subscribed to {successful_subscriptions}/{len(self.symbols)} symbols")

            if successful_subscriptions == 0:
                raise Exception("No symbols successfully subscribed")

        except Exception as e:
            logger.error(f"MT5 symbol subscription failed: {e}")
            raise

    def convert_mt5_tick_to_protobuf(self, tick_data, symbol: str) -> MarketTick:
        """Convert MT5 MqlTick to Protocol Buffer format"""
        market_tick = MarketTick()

        # Basic MT5 tick data
        market_tick.symbol = symbol
        market_tick.bid = float(tick_data.bid)
        market_tick.ask = float(tick_data.ask)
        market_tick.last = float(tick_data.last)
        market_tick.volume = int(tick_data.volume)

        # MT5 timestamps (both seconds and milliseconds)
        market_tick.timestamp = int(tick_data.time * 1000)  # Convert to milliseconds
        if hasattr(tick_data, 'time_msc'):
            market_tick.timestamp = int(tick_data.time_msc)

        # Calculated fields
        market_tick.spread = market_tick.ask - market_tick.bid

        # MT5 specific fields
        if hasattr(tick_data, 'flags'):
            market_tick.flags = int(tick_data.flags)
        if hasattr(tick_data, 'volume_real'):
            market_tick.volume_real = float(tick_data.volume_real)

        # Broker context
        market_tick.broker_source = self.broker_name
        market_tick.broker_type = self.broker_type
        market_tick.broker_timestamp = int(time.time() * 1000)

        # Quality metrics for MT5 data
        quality = QualityMetrics()
        quality.latency_ms = (time.time() * 1000) - market_tick.timestamp
        quality.confidence = self.calculate_mt5_tick_confidence(market_tick)
        market_tick.quality.CopyFrom(quality)

        return market_tick

    def calculate_mt5_tick_confidence(self, tick: MarketTick) -> float:
        """Calculate MT5 tick data confidence score (0.0 - 1.0)"""
        confidence = 1.0

        # Check spread reasonableness for MT5 data
        max_spread = self.config.get('quality_thresholds', {}).get('max_spread', 0.005)
        if tick.spread > max_spread:
            confidence -= 0.3
            self.mt5_metrics['mt5_errors'] += 1

        # Check timestamp freshness (MT5 should be real-time)
        age_ms = abs(int(time.time() * 1000) - tick.timestamp)
        if age_ms > 5000:  # 5 seconds tolerance for MT5
            confidence -= 0.2

        # MT5 bid/ask validation
        if tick.bid <= 0 or tick.ask <= 0 or tick.bid >= tick.ask:
            confidence -= 0.5

        # MT5 volume validation (should be positive)
        if tick.volume <= 0:
            confidence -= 0.1

        return max(0.0, confidence)

    async def stream_to_aggregator(self, market_tick: MarketTick):
        """Stream MT5 tick data to Market Aggregator via NATS"""
        try:
            # Serialize protobuf
            binary_data = market_tick.SerializeToString()

            # NATS topic specifically for MT5 broker data
            topic = f"mt5-broker.{self.broker_name}.{market_tick.symbol}.ticks"

            # Publish to NATS message bus
            await self.nats_client.publish(topic, binary_data)

            # Performance tracking
            self.tick_count += 1
            self.mt5_metrics['total_ticks'] += 1

            if market_tick.quality.confidence >= 0.7:
                self.mt5_metrics['valid_ticks'] += 1

        except Exception as e:
            logger.error(f"Failed to stream MT5 tick: {e}")

    async def start_mt5_collection(self):
        """Start main MT5 data collection loop"""
        self.is_collecting = True
        logger.info("Starting IC Markets MT5 data collection...")

        try:
            while self.is_collecting:
                # Check MT5 terminal connection
                if not mt5.terminal_info():
                    logger.error("MT5 terminal connection lost")
                    self.mt5_metrics['connection_losses'] += 1
                    await asyncio.sleep(5)
                    continue

                # Get ticks for all symbols via MT5 API
                for symbol in self.symbols:
                    try:
                        # Get latest tick from MT5
                        tick = mt5.symbol_info_tick(symbol)
                        if tick is not None:
                            # Convert MT5 tick and stream
                            market_tick = self.convert_mt5_tick_to_protobuf(tick, symbol)
                            await self.stream_to_aggregator(market_tick)

                    except Exception as e:
                        logger.error(f"Error processing MT5 {symbol}: {e}")
                        continue

                # Performance logging
                await self.log_mt5_performance()

                # Small delay to prevent excessive MT5 API calls
                await asyncio.sleep(0.01)  # 10ms delay = up to 100 ticks/second

        except Exception as e:
            logger.error(f"MT5 collection loop error: {e}")
        finally:
            self.is_collecting = False

    async def log_mt5_performance(self):
        """Log MT5 performance metrics periodically"""
        current_time = time.time()
        if current_time - self.last_performance_log >= 60:  # Every minute
            ticks_per_minute = self.tick_count
            quality_rate = (self.mt5_metrics['valid_ticks'] /
                          max(1, self.mt5_metrics['total_ticks'])) * 100

            # MT5 specific metrics
            terminal_info = mt5.terminal_info()
            account_info = mt5.account_info()

            logger.info(f"IC Markets MT5 Performance - Ticks/min: {ticks_per_minute}, "
                       f"Quality: {quality_rate:.1f}%, "
                       f"MT5 Errors: {self.mt5_metrics['mt5_errors']}, "
                       f"Connection: {terminal_info.connected if terminal_info else 'Unknown'}")

            # Reset counters
            self.tick_count = 0
            self.last_performance_log = current_time

    async def get_mt5_health_status(self) -> Dict:
        """Get MT5 collector health status"""
        terminal_info = mt5.terminal_info()
        account_info = mt5.account_info()

        return {
            "collector": "ic_markets",
            "broker_type": "mt5",
            "status": "healthy" if self.is_collecting else "stopped",
            "mt5_terminal_connected": terminal_info is not None and terminal_info.connected,
            "mt5_account_connected": account_info is not None,
            "mt5_server": self.server,
            "symbols_count": len(self.symbols),
            "ticks_per_minute": self.tick_count,
            "mt5_metrics": self.mt5_metrics.copy(),
            "uptime_seconds": time.time() - (self.last_performance_log - 60),
            "terminal_info": {
                "build": terminal_info.build if terminal_info else None,
                "name": terminal_info.name if terminal_info else None,
                "path": terminal_info.path if terminal_info else None
            } if terminal_info else None
        }

    async def stop_mt5_collection(self):
        """Stop MT5 data collection and cleanup"""
        logger.info("Stopping IC Markets MT5 collector...")
        self.is_collecting = False

        if self.nats_client:
            await self.nats_client.close()

        # Shutdown MT5 terminal connection
        mt5.shutdown()
        logger.info("IC Markets MT5 collector stopped")

async def main():
    """Main MT5 collector entry point"""
    # Load MT5 configuration
    config = {
        'server': 'ICMarkets-Demo01',
        'login': 12345678,  # Replace with actual MT5 login
        'password': 'demo_password',  # Replace with actual MT5 password
        'terminal_path': '/opt/mt5-icmarkets/',  # Optional MT5 terminal path
        'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'],
        'quality_thresholds': {
            'max_spread': 0.003,  # 3 pips
            'min_tick_interval': 10  # 10ms
        }
    }

    collector = ICMarketsCollector(config)

    try:
        await collector.initialize()
        await collector.connect_to_mt5_broker()
        await collector.subscribe_to_symbols()
        await collector.start_mt5_collection()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"MT5 collector error: {e}")
    finally:
        await collector.stop_mt5_collection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())