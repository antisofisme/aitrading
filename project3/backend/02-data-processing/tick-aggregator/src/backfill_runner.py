#!/usr/bin/env python3
"""
Historical Backfill Runner
Runs once on startup to aggregate all 1m historical bars to higher timeframes
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from historical_aggregator import HistoricalAggregator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def run_backfill():
    """
    Run historical backfill for all symbols and timeframes

    Aggregates: 1m → 5m, 15m, 30m, 1h, 4h, 1d, 1w
    """
    logger.info("=" * 80)
    logger.info("HISTORICAL BACKFILL - AGGREGATE 1M BARS TO ALL TIMEFRAMES")
    logger.info("=" * 80)

    try:
        # Load config
        config = Config()
        await config.initialize_central_hub()

        # Get symbols to process
        symbols = [
            'XAU/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY',
            'AUD/USD', 'USD/CAD', 'GBP/JPY', 'EUR/JPY',
            'AUD/JPY', 'EUR/GBP', 'USD/CHF', 'NZD/USD',
            'CHF/JPY', 'NZD/JPY'
        ]

        # Target timeframes (exclude 1m - already exists)
        target_timeframes = [
            {'name': '5m', 'interval_minutes': 5},
            {'name': '15m', 'interval_minutes': 15},
            {'name': '30m', 'interval_minutes': 30},
            {'name': '1h', 'interval_minutes': 60},
            {'name': '4h', 'interval_minutes': 240},
            {'name': '1d', 'interval_minutes': 1440},
            {'name': '1w', 'interval_minutes': 10080}
        ]

        # Initialize historical aggregator
        logger.info("📊 Initializing Historical Aggregator...")
        aggregator = HistoricalAggregator(
            clickhouse_config=config.clickhouse_config,
            aggregation_config=config.aggregation_config
        )
        aggregator.connect()

        # Process each symbol
        total_candles = 0
        start_time = datetime.utcnow()

        for symbol in symbols:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"📊 Processing {symbol}")
            logger.info(f"{'=' * 80}")

            for tf_config in target_timeframes:
                timeframe = tf_config['name']
                interval_minutes = tf_config['interval_minutes']

                try:
                    candles_generated = aggregator.aggregate_symbol_timeframe(
                        symbol=symbol,
                        target_timeframe=timeframe,
                        interval_minutes=interval_minutes
                    )

                    total_candles += candles_generated
                    logger.info(f"✅ {symbol} {timeframe}: {candles_generated} candles")

                except Exception as e:
                    logger.error(f"❌ Failed to aggregate {symbol} {timeframe}: {e}")
                    continue

        # Summary
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        stats = aggregator.get_stats()

        logger.info("\n" + "=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"📊 Total 1m bars read: {stats['total_1m_bars_read']:,}")
        logger.info(f"📈 Total candles generated: {stats['total_candles_generated']:,}")
        logger.info(f"⏱️ Time elapsed: {elapsed:.1f}s")
        logger.info(f"🚀 Throughput: {stats['total_candles_generated'] / elapsed:.0f} candles/sec")
        logger.info("=" * 80)

        # Close connection
        aggregator.close()

    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(run_backfill())
