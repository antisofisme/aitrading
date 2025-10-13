"""
Dukascopy Historical Downloader - Main Service
Downloads historical tick data from Dukascopy, aggregates to 1m bars, and publishes to NATS
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import List, Dict

# Add src to path
sys.path.insert(0, '/app/src')

from config import Config
from downloader import DukascopyDownloader
from decoder import DukascopyDecoder
from publisher import NATSPublisher
from gap_detector import GapDetector
from period_tracker import PeriodTracker

# Import Central Hub SDK
try:
    from central_hub_sdk import CentralHubClient, ProgressLogger
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("Central Hub SDK not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/dukascopy/downloader.log')
    ]
)

logger = logging.getLogger(__name__)


class DukascopyHistoricalDownloader:
    """
    Main service for downloading Dukascopy historical data

    Pipeline:
    1. Gap Detection: Find missing dates in ClickHouse market_ticks
    2. Download: Fetch .bi5 files from Dukascopy
    3. Decode: Decompress and parse raw tick data
    4. Publish: Send ticks to NATS → Data Bridge → ClickHouse market_ticks

    Note: NO aggregation here - ticks are stored raw.
    Aggregation to timeframes (1m, 5m, 15m, etc) is done by separate tick-aggregator service.
    """

    def __init__(self, config: Config):
        self.config = config

        # Components
        self.downloader = DukascopyDownloader(max_concurrent=10, rate_limit_per_sec=10)
        self.decoder = DukascopyDecoder()
        self.publisher: NATSPublisher = None
        self.gap_detector: GapDetector = None
        self.period_tracker = PeriodTracker(storage_path="/data/period_tracker.json")

        # Central Hub client
        self.central_hub: CentralHubClient = None

    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 80)
        logger.info("Dukascopy Historical Downloader - Starting")
        logger.info("=" * 80)

        # Initialize Central Hub client
        if SDK_AVAILABLE:
            try:
                self.central_hub = CentralHubClient(
                    service_name="dukascopy-historical-downloader",
                    service_type="data-downloader",
                    version="1.0.0",
                    capabilities=[
                        "historical-tick-download",
                        "binary-decoding",
                        "nats-publishing"
                    ],
                    metadata={
                        "source": "dukascopy.com",
                        "mode": "historical",
                        "data_types": ["tick"],
                        "quality": "swiss_bank_grade",
                        "note": "Raw tick data - aggregation done by tick-aggregator service"
                    }
                )

                await self.central_hub.register()
                logger.info("✅ Central Hub registration successful")

                # Link config to Central Hub
                self.config.central_hub = self.central_hub

                # Fetch NATS config from Central Hub
                await self.config.fetch_nats_config_from_central_hub()

            except Exception as e:
                logger.warning(f"⚠️  Central Hub registration failed: {e}")
                logger.warning("⚠️  Continuing without Central Hub")

        # Initialize downloader
        await self.downloader.connect()

        # Initialize NATS publisher
        nats_config = self.config.nats_config
        self.publisher = NATSPublisher(nats_config)
        await self.publisher.connect()

        # Initialize gap detector
        clickhouse_config = self.config.clickhouse_config
        self.gap_detector = GapDetector(clickhouse_config)
        self.gap_detector.connect()

        logger.info("✅ All components initialized")

    async def download_date_range(self, symbol: str, dukascopy_symbol: str, start_date: str, end_date: str):
        """
        Download and process historical tick data for a date range

        Args:
            symbol: Standard symbol format (EUR/USD)
            dukascopy_symbol: Dukascopy format (EURUSD)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        logger.info(f"📥 Starting download: {symbol} ({start_date} to {end_date})")

        # Find gaps in market_ticks table
        missing_dates = self.gap_detector.get_date_range_gaps(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            source='dukascopy_historical'
        )

        if not missing_dates:
            logger.info(f"✅ No gaps found for {symbol}")
            return

        logger.info(f"📊 Found {len(missing_dates)} missing dates for {symbol}")

        # Initialize progress logger
        progress = None
        if self.central_hub and self.central_hub.registered:
            progress = ProgressLogger(
                task_name=f"Downloading {symbol} ({len(missing_dates)} dates)",
                total_items=len(missing_dates),
                service_name="dukascopy-downloader",
                milestones=[25, 50, 75, 100],
                heartbeat_interval=60
            )
            progress.start()

        # Download each missing date
        total_ticks = 0
        for i, date_str in enumerate(missing_dates):
            try:
                # Check if already downloaded
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if self.period_tracker.is_downloaded(dukascopy_symbol, date):
                    logger.info(f"⏭️  Skipping {date_str} (already downloaded)")
                    continue

                # Download all hours for this date
                ticks = await self._download_and_process_date(
                    symbol, dukascopy_symbol, date
                )

                if ticks:
                    # Publish raw ticks to NATS (batch 1000 at a time)
                    await self.publisher.publish_batch(ticks, batch_size=1000)
                    total_ticks += len(ticks)

                    # Mark as downloaded
                    self.period_tracker.mark_downloaded(dukascopy_symbol, date)

                    logger.info(f"✅ Processed {date_str}: {len(ticks)} ticks")

                # Update progress
                if progress:
                    progress.update(
                        current=i + 1,
                        additional_info={
                            'date': date_str,
                            'ticks_published': total_ticks
                        }
                    )

                # Send heartbeat every 10 dates
                if (i + 1) % 10 == 0:
                    await self._send_heartbeat(symbol, i + 1, len(missing_dates), total_ticks)

            except Exception as e:
                logger.error(f"❌ Error processing {date_str}: {e}")
                continue

        # Complete progress
        if progress:
            progress.complete(summary={
                'total_dates': len(missing_dates),
                'total_ticks': total_ticks
            })

        logger.info(f"✅ Completed {symbol}: {total_ticks} ticks published")

    async def _download_and_process_date(
        self,
        symbol: str,
        dukascopy_symbol: str,
        date: datetime
    ) -> List[Dict]:
        """
        Download and process all hours for a single date

        Args:
            symbol: Standard symbol format (EUR/USD)
            dukascopy_symbol: Dukascopy format (EURUSD)
            date: Date to download

        Returns:
            List of raw ticks (NOT aggregated)
        """
        all_ticks = []

        # Download all 24 hours
        for hour in range(24):
            binary_data = await self.downloader.download_hour(
                dukascopy_symbol,
                date.year,
                date.month,
                date.day,
                hour
            )

            if not binary_data:
                continue

            # Decode ticks
            ticks = self.decoder.decode_bi5(
                binary_data,
                dukascopy_symbol,
                date.year,
                date.month,
                date.day,
                hour
            )

            if not ticks:
                continue

            # Set symbol in standard format (EUR/USD)
            for tick in ticks:
                tick['symbol'] = symbol

            all_ticks.extend(ticks)

        return all_ticks

    async def _send_heartbeat(self, symbol: str, current: int, total: int, ticks_published: int):
        """Send heartbeat to Central Hub"""
        if not self.central_hub or not self.central_hub.registered:
            return

        try:
            await self.central_hub.send_heartbeat(metrics={
                'status': 'downloading',
                'current_symbol': symbol,
                'progress': f"{current}/{total}",
                'progress_pct': round(current / total * 100, 2),
                'ticks_published': ticks_published,
                **self.downloader.get_stats(),
                **self.publisher.get_stats()
            })
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def run_initial_download(self):
        """
        Run initial download for all pairs

        Downloads full historical range defined in config
        """
        logger.info("🚀 Starting initial historical download")

        download_config = self.config.download_config
        start_date = download_config.get('start_date', '2015-01-01')
        end_date = download_config.get('end_date', datetime.now().strftime('%Y-%m-%d'))

        # Process each pair
        for pair in self.config.trading_pairs:
            try:
                await self.download_date_range(
                    pair.symbol,
                    pair.dukascopy_symbol,
                    start_date,
                    end_date
                )
            except Exception as e:
                logger.error(f"❌ Error processing {pair.symbol}: {e}")
                continue

        logger.info("✅ Initial download complete")

    async def run_gap_check(self):
        """
        Run gap check for all pairs

        Scans recent period for gaps and fills them
        """
        logger.info("🔍 Starting gap check")

        # Check last 90 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        for pair in self.config.trading_pairs:
            try:
                await self.download_date_range(
                    pair.symbol,
                    pair.dukascopy_symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
            except Exception as e:
                logger.error(f"❌ Gap check error for {pair.symbol}: {e}")
                continue

        logger.info("✅ Gap check complete")

    async def cleanup(self):
        """Cleanup and close connections"""
        logger.info("Cleaning up...")

        if self.downloader:
            await self.downloader.close()

        if self.publisher:
            await self.publisher.close()

        if self.gap_detector:
            self.gap_detector.close()

        if self.central_hub and self.central_hub.registered:
            await self.central_hub.deregister()

        logger.info("✅ Cleanup complete")


async def main():
    """Main entry point"""
    # Load config
    config = Config(config_path="/app/config/pairs.yaml")

    # Initialize service
    service = DukascopyHistoricalDownloader(config)
    await service.initialize()

    try:
        # Run based on schedule config
        schedule_config = config.schedule_config
        initial_download = schedule_config.get('initial_download', {})

        if initial_download.get('on_startup', True):
            # Run initial download
            await service.run_initial_download()

        # Run gap check
        gap_check = schedule_config.get('gap_check', {})
        if gap_check.get('enabled', True):
            await service.run_gap_check()

        logger.info("✅ Service completed successfully")

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"❌ Service error: {e}", exc_info=True)
    finally:
        await service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
