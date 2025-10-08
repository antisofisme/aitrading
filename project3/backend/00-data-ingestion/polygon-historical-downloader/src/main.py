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

        # Connect publisher ONCE at start
        await self.publisher.connect()

        try:
            # Download and publish EACH PAIR immediately (don't wait for all!)
            total_published = 0

            for pair in pairs:
                try:
                    logger.info(f"📊 Starting download for {pair.symbol} (Priority {pair.priority})")

                    # Determine timeframe from config
                    timeframe, multiplier = self.config.get_timeframe_for_pair(pair)
                    timeframe_str = f"{multiplier}{timeframe[0]}"  # "1m", "5m", etc

                    # Download SINGLE pair using download_all_pairs with single pair list
                    results = await self.downloader.download_all_pairs(
                        pairs=[pair],  # Single pair only!
                        start_date=download_cfg['start_date'],
                        end_date=download_cfg['end_date'],
                        get_timeframe_func=self.config.get_timeframe_for_pair
                    )

                    # Get bars for this pair
                    bars = results.get(pair.symbol, [])
                    logger.info(f"✅ Downloaded {len(bars)} bars for {pair.symbol}")

                    if bars:
                        logger.info(f"📤 Publishing {len(bars)} bars for {pair.symbol} to NATS/Kafka...")

                        # Convert to aggregate format
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

                        logger.info(f"✅ Published {len(aggregates)} bars for {pair.symbol}")

                        # ✅ CRITICAL: VERIFY data reached ClickHouse before continuing!
                        logger.info(f"🔍 Verifying {pair.symbol} data in ClickHouse...")
                        await asyncio.sleep(5)  # Wait for data-bridge to process

                        try:
                            # Get ClickHouse config from Central Hub
                            clickhouse_config = await self.central_hub.get_database_config('clickhouse')
                            ch_connection = clickhouse_config['connection']

                            from clickhouse_driver import Client
                            ch_client = Client(
                                host=ch_connection['host'],
                                port=ch_connection.get('native_port', 9000),
                                user=ch_connection['user'],
                                password=ch_connection['password'],
                                database=ch_connection['database']
                            )

                            # Count bars in ClickHouse for this pair
                            query = """
                                SELECT COUNT(*) as count
                                FROM aggregates
                                WHERE symbol = %(symbol)s
                                  AND timeframe = %(timeframe)s
                                  AND timestamp >= %(start_date)s
                            """
                            result = ch_client.execute(query, {
                                'symbol': pair.symbol,
                                'timeframe': timeframe_str,
                                'start_date': download_cfg['start_date']
                            })

                            bars_in_clickhouse = result[0][0] if result else 0
                            verification_ratio = bars_in_clickhouse / len(bars) if len(bars) > 0 else 0

                            logger.info(f"📊 Verification: {bars_in_clickhouse}/{len(bars)} bars in ClickHouse ({verification_ratio*100:.1f}%)")

                            if verification_ratio < 0.95:  # Less than 95% received
                                logger.error(f"⚠️  VERIFICATION FAILED: Only {verification_ratio*100:.1f}% of data reached ClickHouse!")
                                logger.error(f"⚠️  Expected: {len(bars)}, Got: {bars_in_clickhouse}")
                                logger.error(f"⚠️  Data-bridge might have crashed during publish. Re-publishing...")

                                # Re-publish missing data
                                await asyncio.sleep(10)  # Wait longer
                                for i in range(0, len(aggregates), batch_size):
                                    batch = aggregates[i:i+batch_size]
                                    await self.publisher.publish_batch(batch)

                                logger.info(f"♻️  Re-published {len(aggregates)} bars for {pair.symbol}")
                            else:
                                logger.info(f"✅ Verification PASSED: {pair.symbol} data complete in ClickHouse")

                        except Exception as verify_error:
                            logger.warning(f"⚠️  Could not verify ClickHouse data: {verify_error}")
                            logger.warning(f"⚠️  Continuing anyway, gap detection will handle missing data")

                        # Report progress to Central Hub after each pair
                        if self.central_hub.registered:
                            await self.central_hub.send_heartbeat(metrics={
                                "status": "downloading",
                                "current_pair": pair.symbol,
                                "total_published": total_published,
                                "bars_verified": bars_in_clickhouse if 'bars_in_clickhouse' in locals() else 0,
                                "message": f"Completed {pair.symbol}"
                            })

                except Exception as pair_error:
                    logger.error(f"❌ Error downloading/publishing {pair.symbol}: {pair_error}", exc_info=True)
                    # Continue with next pair even if one fails
                    continue

            # Show final stats
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
        heartbeat_task = None  # Initialize at method level for finally block

        try:
            schedules = self.config.schedules
            gap_check_interval = schedules.get('gap_check', {}).get('interval_hours', 1)

            logger.info("🚀 Starting CONTINUOUS historical downloader...")
            logger.info(f"⏰ Gap check interval: {gap_check_interval} hour(s)")

            # Register with Central Hub once at startup
            await self.central_hub.register()

            # Start continuous heartbeat loop in background (BEFORE initial download)
            if self.central_hub.registered:
                heartbeat_task = asyncio.create_task(self.central_hub.start_heartbeat_loop())
                logger.info("💓 Continuous heartbeat loop started")

            # Initial download on startup
            if schedules.get('initial_download', {}).get('on_startup', True):
                await self.run_initial_download()

            # Continuous gap checking + buffer flushing loop
            buffer_flush_interval = 300  # Flush buffer every 5 minutes
            last_buffer_flush = asyncio.get_event_loop().time()

            while True:
                try:
                    current_time = asyncio.get_event_loop().time()

                    # Check if time to flush buffer (every 5 minutes)
                    if current_time - last_buffer_flush >= buffer_flush_interval:
                        logger.info("♻️ Flushing disk buffer...")

                        # Initialize publisher if needed
                        if not self.publisher:
                            nats_config = await self.central_hub.get_messaging_config('nats')
                            kafka_config = await self.central_hub.get_messaging_config('kafka')
                            nats_url = f"nats://{nats_config['connection']['host']}:{nats_config['connection']['port']}"
                            kafka_brokers = ','.join(kafka_config['connection']['bootstrap_servers'])

                            self.publisher = MessagePublisher(nats_url, kafka_brokers)
                            await self.publisher.connect()

                        flushed = await self.publisher.flush_buffer()

                        if flushed > 0:
                            logger.info(f"♻️ Flushed {flushed} buffered messages")

                        await self.publisher.disconnect()
                        self.publisher = None

                        last_buffer_flush = current_time

                    # Wait and then check gaps (hourly)
                    logger.info(f"⏰ Waiting {gap_check_interval} hour(s) until next gap check...")
                    await asyncio.sleep(min(gap_check_interval * 3600, buffer_flush_interval))

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
            # Cancel heartbeat task if running
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Deregister from Central Hub on shutdown
            if self.central_hub.registered:
                await self.central_hub.deregister()
            logger.info("✅ Historical downloader stopped")

async def main():
    service = PolygonHistoricalService()
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
