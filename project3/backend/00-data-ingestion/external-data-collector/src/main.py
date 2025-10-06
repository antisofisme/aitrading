#!/usr/bin/env python3
"""
External Data Collector - Economic Calendar & Market Data
Real-time and historical data collection for trading system
Integrated with Central Hub for service coordination
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from scrapers.mql5_historical_scraper import MQL5HistoricalScraper
from scrapers.fred_economic import FREDEconomicCollector
from scrapers.coingecko_sentiment import CoinGeckoSentimentCollector
from scrapers.fear_greed_index import FearGreedIndexCollector
from scrapers.yahoo_finance_commodity import YahooFinanceCommodityCollector
from scrapers.market_sessions import MarketSessionsCollector
from publishers import ExternalDataPublisher

# Central Hub SDK (installed via pip)
# REQUIRED: Service MUST have Central Hub SDK installed
from central_hub_sdk import CentralHubClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ExternalDataCollector:
    """Main External Data Collector service"""

    def __init__(self):
        self.config = Config()
        self.scrapers = {}
        self.publisher = None

        # Initialize Central Hub client (REQUIRED)
        self.central_hub = CentralHubClient(
            service_name="external-data-collector",
            service_type="data-collector",
            version="1.0.0",
            capabilities=[
                "economic-calendar",
                "historical-backfill",
                "incremental-scraping",
                "mql5-data-source",
                "zai-parsing",
                "date-tracking",
                "nats-kafka-publishing"
            ],
            metadata={
                "sources": ["mql5.com"],
                "data_types": ["economic_calendar"],
                "storage": self.config.storage_config.get('type', 'json'),
                "backfill_enabled": self.config.backfill_config.get('enabled', False),
                "messaging": {
                    "nats_enabled": self.config.messaging_config.get('nats', {}).get('enabled', False),
                    "kafka_enabled": self.config.messaging_config.get('kafka', {}).get('enabled', False)
                }
            }
        )

        self.start_time = datetime.now()
        self.is_running = False
        self.registered = False
        self.metrics = {
            'events_scraped': 0,
            'dates_tracked': 0,
            'errors': 0,
            'last_scrape': None
        }

        logger.info("=" * 80)
        logger.info("EXTERNAL DATA COLLECTOR + CENTRAL HUB")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")
        logger.info(f"Central Hub URL: {self.config.central_hub_url}")

    async def start(self):
        """Start the collector - REQUIRES Central Hub registration"""
        try:
            logger.info("🚀 Starting External Data Collector...")

            # CRITICAL: Register with Central Hub with retry logic
            await self._register_with_retry()

            # Initialize scrapers
            await self._initialize_scrapers()

            # Start heartbeat loop
            self.heartbeat_task = asyncio.create_task(
                self._heartbeat_loop()
            )

            # Start scraping loops
            self.is_running = True
            scraping_tasks = []

            for scraper_name, scraper in self.scrapers.items():
                task = asyncio.create_task(
                    self._scraping_loop(scraper_name, scraper)
                )
                scraping_tasks.append(task)

            logger.info(f"✅ External Data Collector started with {len(scraping_tasks)} scrapers")

            # Keep running
            await asyncio.gather(*scraping_tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ Failed to start collector: {e}", exc_info=True)
            raise

    async def _register_with_retry(self):
        """
        Register with Central Hub with retry logic
        FAILS FAST if registration fails after max retries
        """
        max_retries = 10
        retry_delay = 5  # seconds

        logger.info(f"📡 Registering with Central Hub (max retries: {max_retries})...")

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"🔄 Registration attempt {attempt}/{max_retries}...")

                # Attempt registration
                await self.central_hub.register()

                # Success!
                self.registered = True
                logger.info(f"✅ Successfully registered with Central Hub on attempt {attempt}")
                return

            except Exception as e:
                logger.warning(f"⚠️ Registration attempt {attempt}/{max_retries} failed: {e}")

                if attempt == max_retries:
                    # Final attempt failed - FAIL FAST
                    logger.error("=" * 80)
                    logger.error("❌ CRITICAL: Failed to register with Central Hub after all retries")
                    logger.error("=" * 80)
                    logger.error(f"Error: {e}")
                    logger.error("Service CANNOT start without Central Hub coordination")
                    logger.error("Check Central Hub availability and network connectivity")
                    logger.error("=" * 80)
                    raise RuntimeError(
                        f"Failed to register with Central Hub after {max_retries} attempts. "
                        f"Last error: {e}"
                    )

                # Wait before retry
                logger.info(f"⏳ Waiting {retry_delay}s before retry...")
                await asyncio.sleep(retry_delay)

    async def _initialize_scrapers(self):
        """Initialize all enabled scrapers"""
        logger.info("🔧 Initializing scrapers...")

        # Initialize NATS+Kafka publisher if enabled
        nats_config = self.config.messaging_config.get('nats', {})
        kafka_config = self.config.messaging_config.get('kafka', {})

        if nats_config.get('enabled') or kafka_config.get('enabled'):
            logger.info("📡 Initializing NATS+Kafka publisher...")
            self.publisher = ExternalDataPublisher(nats_config, kafka_config)
            await self.publisher.connect()
            logger.info(f"✅ Publisher initialized | NATS: {nats_config.get('enabled')} | Kafka: {kafka_config.get('enabled')}")

        for scraper_config in self.config.scrapers:
            scraper_name = None
            scraper = None

            # MQL5 Economic Calendar
            if scraper_config.source == 'mql5.com':
                use_zai = bool(self.config.zai_api_key)
                db_conn = self.config.get_db_connection_string()

                scraper = MQL5HistoricalScraper(
                    zai_api_key=self.config.zai_api_key or "test",
                    db_connection_string=db_conn,
                    use_zai=use_zai,
                    publisher=self.publisher
                )
                scraper_name = 'mql5_economic_calendar'
                logger.info(f"✅ MQL5 Economic Calendar | Z.ai: {use_zai} | DB: {bool(db_conn)}")

            # FRED Economic Indicators
            elif scraper_config.source == 'fred.stlouisfed.org':
                fred_api_key = scraper_config.api_key
                indicators = scraper_config.indicators

                scraper = FREDEconomicCollector(
                    api_key=fred_api_key,
                    indicators=indicators,
                    publisher=self.publisher
                )
                await scraper.initialize()
                scraper_name = 'fred_economic'
                logger.info(f"✅ FRED Economic | Indicators: {len(indicators)}")

            # CoinGecko Crypto Sentiment
            elif scraper_config.source == 'coingecko.com':
                coins = scraper_config.coins

                scraper = CoinGeckoSentimentCollector(
                    coins=coins,
                    publisher=self.publisher
                )
                await scraper.initialize()
                scraper_name = 'coingecko_sentiment'
                logger.info(f"✅ CoinGecko Sentiment | Coins: {len(coins)}")

            # Fear & Greed Index
            elif scraper_config.source == 'alternative.me':
                scraper = FearGreedIndexCollector(publisher=self.publisher)
                await scraper.initialize()
                scraper_name = 'fear_greed_index'
                logger.info(f"✅ Fear & Greed Index")

            # Yahoo Finance Commodities
            elif scraper_config.source == 'finance.yahoo.com':
                symbols = scraper_config.symbols

                scraper = YahooFinanceCommodityCollector(
                    symbols=symbols,
                    publisher=self.publisher
                )
                await scraper.initialize()
                scraper_name = 'yahoo_finance_commodity'
                logger.info(f"✅ Yahoo Finance | Commodities: {len(symbols)}")

            # Market Sessions
            elif scraper_config.source == 'market_sessions':
                sessions = scraper_config.sessions

                scraper = MarketSessionsCollector(
                    sessions=sessions,
                    publisher=self.publisher
                )
                scraper_name = 'market_sessions'
                logger.info(f"✅ Market Sessions | Sessions: {len(sessions)}")

            # Store scraper if initialized
            if scraper and scraper_name:
                self.scrapers[scraper_name] = {
                    'scraper': scraper,
                    'config': scraper_config,
                    'last_run': None
                }

        logger.info(f"✅ Initialized {len(self.scrapers)} collectors")

        # Run backfill if enabled and first time
        if self.config.backfill_config.get('enabled', False):
            await self._run_initial_backfill()

    async def _run_initial_backfill(self):
        """Run initial historical backfill"""
        logger.info("📊 Running initial historical backfill...")

        months_back = self.config.backfill_config.get('months_back', 12)

        if 'mql5_economic_calendar' in self.scrapers:
            scraper_data = self.scrapers['mql5_economic_calendar']
            scraper = scraper_data['scraper']

            try:
                await scraper.backfill_historical_data(months_back=months_back)
                logger.info("✅ Initial backfill completed")
            except Exception as e:
                logger.error(f"❌ Backfill failed: {e}", exc_info=True)
                self.metrics['errors'] += 1

    async def _scraping_loop(self, scraper_name: str, scraper_data: dict):
        """Main scraping loop for a scraper"""
        scraper = scraper_data['scraper']
        config = scraper_data['config']
        interval = config.scrape_interval

        logger.info(f"🔄 Starting scraping loop for {scraper_name} (interval: {interval}s)")

        while self.is_running:
            try:
                # MQL5 scraper uses update_recent_actuals
                if scraper_name == 'mql5_economic_calendar':
                    await scraper.update_recent_actuals(days_back=7)

                    # Get coverage stats
                    stats = await scraper.tracker.get_coverage_stats()
                    self.metrics['events_scraped'] = stats.get('total_events', 0)
                    self.metrics['dates_tracked'] = stats.get('total_dates', 0)

                # All other collectors use collect()
                else:
                    await scraper.collect()

                # Update metrics
                scraper_data['last_run'] = datetime.now()
                self.metrics['last_scrape'] = datetime.now().isoformat()

                logger.info(f"✅ {scraper_name} completed")

            except Exception as e:
                logger.error(f"❌ Scraping error for {scraper_name}: {e}", exc_info=True)
                self.metrics['errors'] += 1

            # Wait for next scrape
            await asyncio.sleep(interval)

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to Central Hub (REQUIRED for service coordination)"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)

                # Send heartbeat with metrics
                await self.central_hub.send_heartbeat(metrics=self.metrics)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")
                logger.warning("⚠️ Lost connection to Central Hub - service may be deregistered")

    async def stop(self):
        """Graceful shutdown"""
        logger.info("🛑 Stopping External Data Collector...")
        self.is_running = False

        # Cancel heartbeat
        if hasattr(self, 'heartbeat_task') and self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close publisher
        if self.publisher:
            try:
                await self.publisher.close()
                logger.info("✅ NATS+Kafka publisher closed")
            except Exception as e:
                logger.error(f"⚠️ Failed to close publisher: {e}")

        # Deregister from Central Hub (REQUIRED for clean shutdown)
        try:
            await self.central_hub.deregister()
            logger.info("✅ Deregistered from Central Hub")
        except Exception as e:
            logger.error(f"⚠️ Failed to deregister from Central Hub: {e}")

        logger.info("✅ External Data Collector stopped")


# Global instance for signal handling
collector = None


async def main():
    """Main entry point"""
    global collector

    try:
        # Create collector
        collector = ExternalDataCollector()

        # Setup signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(collector.stop())
            )

        # Start collector
        await collector.start()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if collector:
            await collector.stop()


if __name__ == '__main__':
    asyncio.run(main())
