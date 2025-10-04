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
                "run_type": "once",
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

        # Register with Central Hub
        await self.central_hub.register()

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

            # Deregister from Central Hub
            await self.central_hub.deregister()

        logger.info("✅ Initial download complete")

    async def start(self):
        """Start the historical downloader"""
        try:
            schedules = self.config.schedules

            # Initial download on startup
            if schedules.get('initial_download', {}).get('on_startup', True):
                await self.run_initial_download()

            logger.info("✅ Historical downloader service complete")

        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            sys.exit(1)

async def main():
    service = PolygonHistoricalService()
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
