"""
Feature Engineering Service - Main Entry Point
Generates 110 ML features from aggregates data
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import clickhouse_connect
import yaml
from pathlib import Path

# Add calculators to path
sys.path.insert(0, str(Path(__file__).parent))

from calculators import (
    TechnicalIndicatorCalculator,
    FibonacciCalculator,
    LaggedFeatureCalculator,
    RollingStatCalculator,
    MultiTimeframeCalculator,
    TargetCalculator,
    TemporalFeatureCalculator,
    ExternalDataCalculator
)

class FeatureEngineeringService:
    """Main feature engineering service"""

    def __init__(self, config_path: str):
        """Initialize service with config"""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Initialize ClickHouse client
        self.client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', self.config['clickhouse']['host']),
            port=int(os.getenv('CLICKHOUSE_PORT', self.config['clickhouse']['port'])),
            database=self.config['clickhouse']['database'],
            username=self.config['clickhouse']['username'],
            password=os.getenv('CLICKHOUSE_PASSWORD', self.config['clickhouse']['password'])
        )

        # Initialize calculators
        self.tech_calc = TechnicalIndicatorCalculator()
        self.fib_calc = FibonacciCalculator()
        self.lag_calc = LaggedFeatureCalculator()
        self.roll_calc = RollingStatCalculator()
        self.mtf_calc = MultiTimeframeCalculator(self.config['processing']['timeframe_mapping'])
        self.target_calc = TargetCalculator(self.config['processing']['calculate_targets'])
        self.temporal_calc = TemporalFeatureCalculator()
        self.ext_calc = ExternalDataCalculator(self.client)

        print(f"✅ Feature Engineering Service initialized (v{self.config['service']['version']})")

    async def run(self):
        """Main service loop"""
        print("🚀 Starting feature generation...")

        while True:
            try:
                await self.process_batch()
                await asyncio.sleep(self.config['processing']['poll_interval'])
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)

    async def process_batch(self):
        """Process a batch of aggregates"""
        # Query recent aggregates that don't have features yet
        query = """
            SELECT a.*
            FROM suho_analytics.live_aggregates a
            LEFT JOIN suho_analytics.ml_features f
                ON a.time = f.time
                AND a.symbol = f.symbol
                AND a.timeframe = f.timeframe
            WHERE f.time IS NULL
            ORDER BY a.time DESC
            LIMIT 1000
        """

        result = self.client.query(query)
        if result.row_count == 0:
            print("ℹ️  No new aggregates to process")
            return

        df = result.result_as_dataframe()
        print(f"📊 Processing {len(df)} new aggregates...")

        # Process each row
        features_batch = []
        for idx, row in df.iterrows():
            features = await self.calculate_features(row)
            if features:
                features_batch.append(features)

        # Insert to ClickHouse
        if features_batch:
            self.insert_features(features_batch)
            print(f"✅ Inserted {len(features_batch)} feature rows")

    async def calculate_features(self, candle_row) -> dict:
        """Calculate all 110 features for a single candle"""
        try:
            symbol = candle_row['symbol']
            timeframe = candle_row['timeframe']
            timestamp = pd.to_datetime(candle_row['time'])

            # Get historical data for indicators
            hist_df = self.get_historical_data(symbol, timeframe, timestamp, lookback=200)

            # Calculate all features
            features = {
                'time': timestamp,
                'symbol': symbol,
                'timeframe': timeframe,
                'feature_version': 'v2.0',
                'created_at': datetime.utcnow()
            }

            # Temporal features (21)
            features.update(self.temporal_calc.calculate(timestamp))

            # Technical indicators (14)
            features.update(self.tech_calc.calculate(hist_df))

            # Fibonacci (7)
            features.update(self.fib_calc.calculate(hist_df))

            # Lagged (15)
            features.update(self.lag_calc.calculate(hist_df))

            # Rolling (8)
            features.update(self.roll_calc.calculate(hist_df))

            # Multi-TF (10) - simplified for now
            features.update(self.mtf_calc.calculate(hist_df, timeframe))

            # External data (12)
            features.update(self.ext_calc.calculate(timestamp, symbol))

            # Targets (5) - only for historical data
            if self.config['processing']['calculate_targets']:
                future_df = self.get_future_data(symbol, timeframe, timestamp)
                features.update(self.target_calc.calculate(timestamp, candle_row['close'], future_df))

            return features

        except Exception as e:
            print(f"❌ Error calculating features for {candle_row['symbol']} {candle_row['time']}: {e}")
            return None

    def get_historical_data(self, symbol: str, timeframe: str, current_time, lookback: int = 200):
        """Get historical candles for feature calculation"""
        query = f"""
            SELECT *
            FROM suho_analytics.live_aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND time <= '{current_time.isoformat()}'
            ORDER BY time DESC
            LIMIT {lookback}
        """
        result = self.client.query(query)
        df = result.result_as_dataframe()
        return df.sort_values('time') if not df.empty else pd.DataFrame()

    def get_future_data(self, symbol: str, timeframe: str, current_time):
        """Get future candles for target calculation"""
        query = f"""
            SELECT *
            FROM suho_analytics.live_aggregates
            WHERE symbol = '{symbol}'
              AND timeframe = '{timeframe}'
              AND time > '{current_time.isoformat()}'
            ORDER BY time ASC
            LIMIT 20
        """
        result = self.client.query(query)
        df = result.result_as_dataframe()
        return df if not df.empty else pd.DataFrame()

    def insert_features(self, features_batch):
        """Insert features to ClickHouse"""
        # Convert to DataFrame
        df = pd.DataFrame(features_batch)

        # Insert to ml_features table
        self.client.insert_df('ml_features', df)

if __name__ == '__main__':
    config_path = 'config/infrastructure.yaml'
    service = FeatureEngineeringService(config_path)
    asyncio.run(service.run())
