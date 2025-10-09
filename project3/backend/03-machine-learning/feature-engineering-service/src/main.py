"""
Feature Engineering Service - Main Entry Point

Extracts 63 ML features from aggregates + external data
Based on: TRADING_STRATEGY_AND_ML_DESIGN.md

Data Flow:
ClickHouse (aggregates + external) → Feature Calculation → ml_training_data table
"""

import asyncio
import logging
import yaml
import sys
from pathlib import Path
from datetime import datetime, timedelta

from .clickhouse_client import ClickHouseClient
from .feature_calculator import FeatureCalculator
from .central_hub_sdk import CentralHubSDK

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FeatureEngineeringService:
    """
    Main service for feature engineering

    Responsibilities:
    1. Read OHLCV + indicators from aggregates table
    2. Read external data (6 sources)
    3. Calculate 72 ML features (63 original + 9 Fibonacci)
    4. Write to ml_training_data table
    """

    def __init__(self, config_path: str = "config/features.yaml"):
        self.config = self._load_config(config_path)

        # Initialize clients
        self.central_hub = CentralHubSDK(
            base_url="http://suho-central-hub:7000"
        )

        self.clickhouse = None
        self.feature_calculator = None

        # Stats
        self.total_rows_processed = 0
        self.total_features_generated = 0
        self.errors = 0

        logger.info("🤖 Feature Engineering Service initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"✅ Configuration loaded from {config_path}")
        return config

    async def start(self):
        """Start feature engineering service"""
        try:
            # 1. Register with Central Hub
            await self.central_hub.register(
                service_name="feature-engineering-service",
                service_type="ml",
                version=self.config['service']['version'],
                metadata={
                    'feature_count': 72,  # v2.3: 63 original + 9 Fibonacci
                    'timeframes': list(self.config['timeframes'].values()),
                    'primary_pair': self.config['primary_pair']
                }
            )
            logger.info("✅ Registered with Central Hub")

            # 2. Get ClickHouse config from Central Hub
            ch_config_response = await self.central_hub.get_database_config("clickhouse")
            ch_config = ch_config_response.get('config', ch_config_response)  # Extract 'config' key
            logger.info("✅ Retrieved ClickHouse config from Central Hub")

            # 3. Initialize ClickHouse client
            self.clickhouse = ClickHouseClient(ch_config)
            await self.clickhouse.connect()
            logger.info("✅ Connected to ClickHouse")

            # 4. Initialize Feature Calculator
            self.feature_calculator = FeatureCalculator(
                config=self.config,
                clickhouse_client=self.clickhouse
            )
            logger.info("✅ Feature Calculator initialized")

            # 5. Process historical data (5 years for training)
            await self.process_historical_data()

            # 6. Start continuous processing for new data
            await self.continuous_processing()

        except Exception as e:
            logger.error(f"❌ Service failed to start: {e}", exc_info=True)
            raise

    async def process_historical_data(self):
        """
        Process historical data for ML training (2.8 years available)

        Goal: Generate training dataset with 72 features (v2.3)
        Period: ALL available data (2023-2025, ~2.8 years = ~43,800 H1 candles)
        Primary: H1 timeframe
        """
        logger.info("📊 Starting historical data processing (ALL available data)")

        primary_pair = self.config['primary_pair']

        # Query ALL available H1 data
        # This will work with whatever data exists in aggregates table (2023-2025)
        query = f"""
        SELECT
            symbol, timeframe, timestamp, timestamp_ms,
            open, high, low, close, volume,
            vwap, range_pips, body_pips,
            start_time, end_time, source,
            indicators
        FROM aggregates
        WHERE symbol = '{primary_pair}'
          AND timeframe = '1h'
        ORDER BY timestamp ASC
        """

        logger.info(f"📥 Fetching historical data: {primary_pair} H1 (ALL available)")
        aggregates = await self.clickhouse.query(query)

        if aggregates.empty:
            logger.warning("⚠️ No historical data found!")
            return

        logger.info(f"✅ Fetched {len(aggregates)} H1 candles")

        # Process in batches
        batch_size = self.config['processing']['batch_size']
        total_batches = (len(aggregates) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(aggregates))
            batch = aggregates.iloc[start_idx:end_idx]

            logger.info(f"🔄 Processing batch {batch_idx + 1}/{total_batches} ({len(batch)} candles)")

            try:
                # Calculate 72 features for this batch (v2.3)
                features_df = await self.feature_calculator.calculate_features(
                    aggregates_batch=batch,
                    timeframe='1h'
                )

                if not features_df.empty:
                    # Write to ml_training_data table
                    await self.clickhouse.insert_training_data(features_df)

                    self.total_rows_processed += len(features_df)
                    self.total_features_generated += len(features_df) * 72  # v2.3

                    logger.info(f"✅ Batch {batch_idx + 1} complete: {len(features_df)} rows with 72 features")

            except Exception as e:
                self.errors += 1
                logger.error(f"❌ Batch {batch_idx + 1} failed: {e}")
                continue

        logger.info(f"""
        📊 Historical processing complete:
           - Total rows: {self.total_rows_processed}
           - Total features: {self.total_features_generated:,}
           - Errors: {self.errors}
        """)

    async def continuous_processing(self):
        """
        Continuous processing for new candles (real-time feature engineering)

        Runs every hour to process new H1 candles
        """
        logger.info("🔄 Starting continuous processing mode")

        while True:
            try:
                # Wait for next hour boundary
                now = datetime.utcnow()
                next_hour = (now.replace(minute=0, second=0, microsecond=0) +
                            timedelta(hours=1))
                wait_seconds = (next_hour - now).total_seconds()

                if wait_seconds > 0:
                    logger.info(f"⏰ Waiting {wait_seconds:.0f}s until next hour...")
                    await asyncio.sleep(wait_seconds)

                # Process last hour candle
                await self.process_latest_candle()

                # Send heartbeat
                await self.central_hub.send_heartbeat({
                    'rows_processed': self.total_rows_processed,
                    'features_generated': self.total_features_generated,
                    'errors': self.errors
                })

            except Exception as e:
                logger.error(f"❌ Continuous processing error: {e}")
                await asyncio.sleep(60)  # Wait 1 min before retry

    async def process_latest_candle(self):
        """Process the latest completed H1 candle"""
        primary_pair = self.config['primary_pair']

        # Get last completed H1 candle (1 hour ago)
        query = f"""
        SELECT *
        FROM aggregates
        WHERE symbol = '{primary_pair}'
          AND timeframe = '1h'
        ORDER BY timestamp DESC
        LIMIT 1
        """

        latest = await self.clickhouse.query(query)

        if not latest.empty:
            logger.info(f"🔄 Processing latest candle: {latest.iloc[0]['timestamp']}")

            # Calculate features
            features = await self.feature_calculator.calculate_features(
                aggregates_batch=latest,
                timeframe='1h'
            )

            if not features.empty:
                # Write to ml_training_data
                await self.clickhouse.insert_training_data(features)

                self.total_rows_processed += 1
                self.total_features_generated += 72  # v2.3

                logger.info("✅ Latest candle processed with 72 features")

    async def close(self):
        """Cleanup and shutdown"""
        logger.info("🛑 Shutting down Feature Engineering Service...")

        if self.clickhouse:
            await self.clickhouse.close()

        if self.central_hub:
            await self.central_hub.deregister()

        logger.info("✅ Service shutdown complete")


async def main():
    """Main entry point"""
    service = FeatureEngineeringService()

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("⏸️ Received shutdown signal")
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
