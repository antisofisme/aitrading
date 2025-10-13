"""
Unit tests for tick aggregator
Tests tick-to-OHLCV aggregation
"""
import pytest
from datetime import datetime, timezone
import sys
sys.path.insert(0, '../src')

from aggregator import TickAggregator


class TestTickAggregator:
    """Test OHLCV aggregation from ticks"""

    @pytest.fixture
    def aggregator(self):
        return TickAggregator(use_mid_price=True)

    def test_aggregate_single_minute(self, aggregator):
        """Test aggregation of ticks within one minute"""
        # Create ticks for same minute with varying prices
        base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        ticks = [
            {
                'timestamp': base_time,
                'bid': 1.09990,
                'ask': 1.10000,
                'bid_volume': 1.0,
                'ask_volume': 1.0,
                'spread': 0.00010
            },
            {
                'timestamp': base_time.replace(second=15),
                'bid': 1.10010,
                'ask': 1.10020,
                'bid_volume': 2.0,
                'ask_volume': 2.0,
                'spread': 0.00010
            },
            {
                'timestamp': base_time.replace(second=30),
                'bid': 1.09980,
                'ask': 1.09990,
                'bid_volume': 1.5,
                'ask_volume': 1.5,
                'spread': 0.00010
            },
            {
                'timestamp': base_time.replace(second=45),
                'bid': 1.10000,
                'ask': 1.10010,
                'bid_volume': 1.0,
                'ask_volume': 1.0,
                'spread': 0.00010
            }
        ]

        bars = aggregator.aggregate_to_1m(ticks, 'EUR/USD')

        # Should create 1 bar
        assert len(bars) == 1

        bar = bars[0]

        # Check OHLC (mid-prices)
        assert bar['open'] == 1.09995  # (1.09990 + 1.10000) / 2
        assert bar['close'] == 1.10005  # (1.10000 + 1.10010) / 2
        assert bar['high'] == 1.10015  # max mid-price
        assert bar['low'] == 1.09985   # min mid-price

        # Check metadata
        assert bar['symbol'] == 'EUR/USD'
        assert bar['timeframe'] == '1m'
        assert bar['tick_count'] == 4
        assert bar['volume'] == 11.0  # Sum of all volumes
        assert bar['source'] == 'dukascopy_historical'

    def test_aggregate_multiple_minutes(self, aggregator):
        """Test aggregation across multiple minutes"""
        base_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        ticks = [
            # Minute 0
            {
                'timestamp': base_time,
                'bid': 1.10000,
                'ask': 1.10010,
                'bid_volume': 1.0,
                'ask_volume': 1.0,
                'spread': 0.00010
            },
            # Minute 1
            {
                'timestamp': base_time.replace(minute=1),
                'bid': 1.10020,
                'ask': 1.10030,
                'bid_volume': 2.0,
                'ask_volume': 2.0,
                'spread': 0.00010
            },
            # Minute 2
            {
                'timestamp': base_time.replace(minute=2),
                'bid': 1.10040,
                'ask': 1.10050,
                'bid_volume': 1.0,
                'ask_volume': 1.0,
                'spread': 0.00010
            }
        ]

        bars = aggregator.aggregate_to_1m(ticks, 'EUR/USD')

        # Should create 3 bars
        assert len(bars) == 3

        # Check timestamps
        assert bars[0]['timestamp'].minute == 0
        assert bars[1]['timestamp'].minute == 1
        assert bars[2]['timestamp'].minute == 2

    def test_validate_bar(self, aggregator):
        """Test bar validation logic"""
        # Valid bar
        valid_bar = {
            'open': 1.10000,
            'high': 1.10020,
            'low': 1.09980,
            'close': 1.10010,
            'volume': 5.0,
            'tick_count': 10
        }
        assert aggregator._validate_bar(valid_bar) == True

        # Invalid: High < Low
        invalid_bar_1 = {
            'open': 1.10000,
            'high': 1.09980,
            'low': 1.10020,
            'close': 1.10000,
            'volume': 5.0,
            'tick_count': 10
        }
        assert aggregator._validate_bar(invalid_bar_1) == False

        # Invalid: High < Open
        invalid_bar_2 = {
            'open': 1.10020,
            'high': 1.10000,
            'low': 1.09980,
            'close': 1.10000,
            'volume': 5.0,
            'tick_count': 10
        }
        assert aggregator._validate_bar(invalid_bar_2) == False

    def test_get_stats(self, aggregator):
        """Test statistics calculation"""
        bars = [
            {
                'volume': 10.0,
                'tick_count': 100,
                'spread_avg': 0.0001,
                'high': 1.10020,
                'low': 1.09980
            },
            {
                'volume': 20.0,
                'tick_count': 200,
                'spread_avg': 0.0002,
                'high': 1.10030,
                'low': 1.09970
            }
        ]

        stats = aggregator.get_stats(bars)

        assert stats['bar_count'] == 2
        assert stats['total_volume'] == 30.0
        assert stats['avg_volume'] == 15.0
        assert stats['avg_tick_count'] == 150.0
        assert stats['price_range']['high'] == 1.10030
        assert stats['price_range']['low'] == 1.09970


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
