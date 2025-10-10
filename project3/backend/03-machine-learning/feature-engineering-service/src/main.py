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

# Central Hub SDK for progress logging
from central_hub_sdk import ProgressLogger

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
        Process historical data for ML training with memory-efficient chunking

        Goal: Generate training dataset with 72 features (v2.3)
        Period: ALL available data (up to 10 years with new historical download)
        Primary: H1 timeframe
        Strategy: Query in time-based chunks (6 months) to prevent memory issues
        """
        logger.info("📊 Starting historical data processing (memory-efficient chunked mode)")

        primary_pair = self.config['primary_pair']

        # Get date range for available data
        range_query = f"""
        SELECT
            MIN(timestamp) as min_date,
            MAX(timestamp) as max_date,
            COUNT(*) as total_candles
        FROM aggregates
        WHERE symbol = '{primary_pair}'
          AND timeframe = '1h'
        """

        date_range = await self.clickhouse.query(range_query)

        if date_range.empty or date_range.iloc[0]['total_candles'] == 0:
            logger.warning("⚠️ No historical data found!")
            return

        min_date = date_range.iloc[0]['min_date']
        max_date = date_range.iloc[0]['max_date']
        total_candles = date_range.iloc[0]['total_candles']

        logger.info(f"📊 Found {total_candles:,} H1 candles: {min_date} to {max_date}")

        # Process in 6-month time chunks to manage memory
        from datetime import datetime, timedelta
        chunk_months = 6

        # Calculate total chunks for progress tracking
        def calculate_total_chunks(min_date, max_date, chunk_months=6):
            total = 0
            current = min_date
            while current < max_date:
                total += 1
                new_month = current.month + chunk_months
                new_year = current.year + (new_month - 1) // 12
                new_month = ((new_month - 1) % 12) + 1
                try:
                    current = current.replace(year=new_year, month=new_month)
                except ValueError:
                    current = current.replace(year=new_year, month=new_month, day=1)
                if current >= max_date:
                    break
            return total

        total_chunks = calculate_total_chunks(min_date, max_date)

        # Initialize progress logger
        progress = ProgressLogger(
            task_name=f"Processing {primary_pair} features",
            total_items=total_chunks,
            service_name="feature-engineering",
            milestones=[25, 50, 75, 100],
            heartbeat_interval=30
        )
        progress.start()

        current_date = min_date
        chunk_number = 0

        while current_date < max_date:
            chunk_number += 1

            # Calculate chunk end date
            new_month = current_date.month + chunk_months
            new_year = current_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1

            try:
                chunk_end = current_date.replace(year=new_year, month=new_month)
            except ValueError:
                chunk_end = current_date.replace(year=new_year, month=new_month, day=1)

            chunk_end = min(chunk_end, max_date)

            # Query ONLY this time chunk
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
              AND timestamp >= '{current_date}'
              AND timestamp < '{chunk_end}'
            ORDER BY timestamp ASC
            """

            aggregates = await self.clickhouse.query(query)

            if aggregates.empty:
                # Still update progress for empty chunks
                progress.update(
                    current=chunk_number,
                    additional_info={"status": "empty", "rows": self.total_rows_processed}
                )
                current_date = chunk_end
                continue

            # Process in smaller batches within chunk
            batch_size = self.config['processing']['batch_size']
            total_batches = (len(aggregates) + batch_size - 1) // batch_size

            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min((batch_idx + 1) * batch_size, len(aggregates))
                batch = aggregates.iloc[start_idx:end_idx]

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

                except Exception as e:
                    self.errors += 1
                    logger.error(f"   ❌ Batch {batch_idx + 1} failed: {e}")
                    continue

            # Update progress after chunk completion
            progress.update(
                current=chunk_number,
                additional_info={
                    "rows": self.total_rows_processed,
                    "features": self.total_features_generated,
                    "errors": self.errors
                }
            )

            # Free memory
            del aggregates

            # Move to next chunk
            current_date = chunk_end

        progress.complete(summary={
            "total_rows": self.total_rows_processed,
            "total_features": self.total_features_generated,
            "errors": self.errors
        })

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
