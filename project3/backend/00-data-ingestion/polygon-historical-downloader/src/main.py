#!/usr/bin/env python3
"""
Polygon.io Historical Downloader
Downloads historical forex data and publishes to NATS/Kafka
Integrated with Central Hub for progress tracking
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from downloader import PolygonHistoricalDownloader
from publisher import MessagePublisher

# Central Hub SDK (installed via pip)
from central_hub_sdk import CentralHubClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PolygonHistoricalService:
    def __init__(self):
        self.config = Config()
        self.downloader = PolygonHistoricalDownloader(
            api_key=self.config.polygon_api_key,
            config=self.config.download_config
        )

        # Publisher will be initialized after getting config from Central Hub
        self.publisher = None

        # Central Hub integration
        self.central_hub = CentralHubClient(
            service_name="polygon-historical-downloader",
            service_type="data-downloader",
            version="1.0.0",
            capabilities=[
                "historical-data-download",
                "bulk-publishing",
                "gap-detection",
                "nats-publishing",
                "kafka-publishing"
            ],
            metadata={
                "source": "polygon.io",
                "mode": "historical",
                "run_type": "continuous",
                "data_types": ["aggregates", "bars"],
                "transport": ["nats", "kafka"]
            }
        )

        logger.info("=" * 80)
        logger.info("POLYGON.IO HISTORICAL DOWNLOADER + CENTRAL HUB")
        logger.info("=" * 80)

    async def run_initial_download(self):
        """Download historical data for all pairs and publish to NATS/Kafka"""
        logger.info("📥 Starting initial historical download...")

        # Get messaging configs from Central Hub
        try:
            logger.info("⚙️  Fetching messaging configs from Central Hub...")
            nats_config = await self.central_hub.get_messaging_config('nats')
            kafka_config = await self.central_hub.get_messaging_config('kafka')

            # Build connection URLs from config
            nats_url = f"nats://{nats_config['connection']['host']}:{nats_config['connection']['port']}"
            kafka_brokers = ','.join(kafka_config['connection']['bootstrap_servers'])

            logger.info(f"✅ Using NATS: {nats_url}")
            logger.info(f"✅ Using Kafka: {kafka_brokers}")

        except Exception as e:
            # Fallback to environment variables if Central Hub config fails
            logger.warning(f"⚠️  Failed to get messaging config from Central Hub: {e}")
            logger.warning("⚠️  Falling back to environment variables...")
            nats_url = os.getenv('NATS_URL', 'nats://suho-nats-server:4222')
            kafka_brokers = os.getenv('KAFKA_BROKERS', 'suho-kafka:9092')

        # Initialize publisher with config
        self.publisher = MessagePublisher(
            nats_url=nats_url,
            kafka_brokers=kafka_brokers
        )

        # Report start status
        if self.central_hub.registered:
            await self.central_hub.send_heartbeat(metrics={
                "status": "starting",
                "message": "Beginning historical data download"
            })

        download_cfg = self.config.download_config
        pairs = self.config.pairs

        # Connect publisher
        await self.publisher.connect()

        try:
            results = await self.downloader.download_all_pairs(
                pairs=pairs,
                start_date=download_cfg['start_date'],
                end_date=download_cfg['end_date'],
                get_timeframe_func=self.config.get_timeframe_for_pair
            )

            # Publish to NATS/Kafka
            total_published = 0
            for symbol, bars in results.items():
                if bars:
                    logger.info(f"📤 Publishing {len(bars)} bars for {symbol} to NATS/Kafka...")

                    # Convert to aggregate format
                    aggregates = []
                    for bar in bars:
                        # Determine timeframe from config
                        pair = next(p for p in pairs if p.symbol == symbol)
                        timeframe, multiplier = self.config.get_timeframe_for_pair(pair)
                        timeframe_str = f"{multiplier}{timeframe[0]}"  # "1m", "5m", etc

                        aggregate = {
                            'symbol': bar['symbol'],
                            'timeframe': timeframe_str,
                            'timestamp_ms': bar['timestamp_ms'],
                            'open': bar['open'],
                            'high': bar['high'],
                            'low': bar['low'],
                            'close': bar['close'],
                            'volume': bar['volume'],
                            'vwap': bar.get('vwap', 0),
                            'range_pips': (bar['high'] - bar['low']) * 10000,  # Pips
                            'start_time': bar['timestamp'],
                            'end_time': bar['timestamp'],  # Historical data is already aggregated
                            'source': 'polygon_historical',
                            'event_type': 'ohlcv'
                        }
                        aggregates.append(aggregate)

                    # Publish in batches
                    batch_size = 100
                    for i in range(0, len(aggregates), batch_size):
                        batch = aggregates[i:i+batch_size]
                        await self.publisher.publish_batch(batch)
                        total_published += len(batch)

                    logger.info(f"✅ Published {len(aggregates)} bars for {symbol}")

            # Show stats
            stats = self.publisher.get_stats()
            logger.info(f"📊 Publishing Stats:")
            logger.info(f"   NATS: {stats['published_nats']} messages")
            logger.info(f"   Kafka: {stats['published_kafka']} messages")
            logger.info(f"   Errors: {stats['errors']}")
            logger.info(f"   Total Published: {total_published}")

            # Report completion to Central Hub
            if self.central_hub.registered:
                await self.central_hub.send_heartbeat(metrics={
                    "status": "completed",
                    "message": "Historical download complete",
                    "total_published": total_published,
                    "nats_published": stats['published_nats'],
                    "kafka_published": stats['published_kafka'],
                    "errors": stats['errors']
                })

        finally:
            await self.publisher.disconnect()

        logger.info("✅ Initial download complete")

    async def check_and_fill_gaps(self):
        """Check for gaps and download missing data"""
        try:
            logger.info("🔍 Checking for data gaps...")

            # Get ClickHouse config from Central Hub
            try:
                clickhouse_config = await self.central_hub.get_database_config('clickhouse')
                ch_connection = clickhouse_config['connection']
                gap_config = {
                    'host': ch_connection['host'],
                    'port': ch_connection.get('native_port', 9000),
                    'user': ch_connection['user'],
                    'password': ch_connection['password'],
                    'database': ch_connection['database'],
                    'table': 'aggregates'
                }
            except Exception as e:
                logger.warning(f"⚠️  Failed to get ClickHouse config from Central Hub: {e}")
                # Skip gap detection if can't get config
                return

            # Initialize gap detector
            from gap_detector import GapDetector
            gap_detector = GapDetector(gap_config)

            # Get messaging configs
            nats_config = await self.central_hub.get_messaging_config('nats')
            kafka_config = await self.central_hub.get_messaging_config('kafka')
            nats_url = f"nats://{nats_config['connection']['host']}:{nats_config['connection']['port']}"
            kafka_brokers = ','.join(kafka_config['connection']['bootstrap_servers'])

            # Reinitialize publisher
            self.publisher = MessagePublisher(
                nats_url=nats_url,
                kafka_brokers=kafka_brokers
            )
            await self.publisher.connect()

            # Check gaps for all pairs
            pairs = self.config.pairs
            total_gaps_filled = 0

            for pair in pairs:
                symbol = pair.symbol
                logger.info(f"🔍 Checking gaps for {symbol}...")

                # Detect gaps in last 30 days
                gaps = gap_detector.detect_gaps(symbol, days=30, max_gap_minutes=60)

                if gaps:
                    logger.info(f"📥 Found {len(gaps)} gaps for {symbol}, downloading...")

                    for gap_start, gap_end in gaps:
                        try:
                            # Download data for this gap
                            timeframe, multiplier = self.config.get_timeframe_for_pair(pair)
                            bars = await self.downloader.download_range(
                                symbol=symbol,
                                from_date=gap_start.strftime('%Y-%m-%d'),
                                to_date=gap_end.strftime('%Y-%m-%d'),
                                timeframe=timeframe,
                                multiplier=multiplier
                            )

                            if bars:
                                # Convert and publish
                                timeframe_str = f"{multiplier}{timeframe[0]}"
                                aggregates = []
                                for bar in bars:
                                    aggregate = {
                                        'symbol': bar['symbol'],
                                        'timeframe': timeframe_str,
                                        'timestamp_ms': bar['timestamp_ms'],
                                        'open': bar['open'],
                                        'high': bar['high'],
                                        'low': bar['low'],
                                        'close': bar['close'],
                                        'volume': bar['volume'],
                                        'vwap': bar.get('vwap', 0),
                                        'range_pips': (bar['high'] - bar['low']) * 10000,
                                        'start_time': bar['timestamp'],
                                        'end_time': bar['timestamp'],
                                        'source': 'polygon_gap_fill',
                                        'event_type': 'ohlcv'
                                    }
                                    aggregates.append(aggregate)

                                # Publish in batches
                                batch_size = 100
                                for i in range(0, len(aggregates), batch_size):
                                    batch = aggregates[i:i+batch_size]
                                    await self.publisher.publish_batch(batch)
                                    total_gaps_filled += len(batch)

                                logger.info(f"✅ Filled gap for {symbol}: {gap_start} -> {gap_end} ({len(bars)} bars)")

                        except Exception as e:
                            logger.error(f"❌ Error filling gap for {symbol}: {e}")

                else:
                    logger.info(f"✅ No gaps found for {symbol}")

            await self.publisher.disconnect()

            if total_gaps_filled > 0:
                logger.info(f"✅ Gap filling complete: {total_gaps_filled} bars published")
                if self.central_hub.registered:
                    await self.central_hub.send_heartbeat(metrics={
                        "status": "gap_fill_complete",
                        "gaps_filled": total_gaps_filled
                    })
            else:
                logger.info("✅ No gaps to fill")

        except Exception as e:
            logger.error(f"❌ Error in gap checking: {e}", exc_info=True)

    async def start(self):
        """Start the historical downloader in continuous mode"""
        try:
            schedules = self.config.schedules
            gap_check_interval = schedules.get('gap_check', {}).get('interval_hours', 1)

            logger.info("🚀 Starting CONTINUOUS historical downloader...")
            logger.info(f"⏰ Gap check interval: {gap_check_interval} hour(s)")

            # Register with Central Hub once at startup
            await self.central_hub.register()

            # Initial download on startup
            if schedules.get('initial_download', {}).get('on_startup', True):
                await self.run_initial_download()

            # Continuous gap checking loop
            while True:
                try:
                    logger.info(f"⏰ Waiting {gap_check_interval} hour(s) until next gap check...")
                    await asyncio.sleep(gap_check_interval * 3600)

                    # Check and fill gaps
                    await self.check_and_fill_gaps()

                except Exception as e:
                    logger.error(f"❌ Error in gap check cycle: {e}", exc_info=True)
                    # Continue running even if one cycle fails
                    await asyncio.sleep(60)  # Wait 1 minute before retrying

        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
        finally:
            # Deregister from Central Hub on shutdown
            if self.central_hub.registered:
                await self.central_hub.deregister()
            logger.info("✅ Historical downloader stopped")

async def main():
    service = PolygonHistoricalService()
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
