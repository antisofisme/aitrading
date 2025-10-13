"""
Tick-to-OHLCV Aggregator
Converts raw tick data to 1-minute OHLCV bars
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class TickAggregator:
    """
    Aggregates tick data to 1-minute OHLCV bars

    Features:
    - Groups ticks by minute
    - Calculates OHLC from mid-prices
    - Tracks volume, tick count, spread statistics
    - Validates output bars
    """

    def __init__(self, use_mid_price: bool = True):
        """
        Args:
            use_mid_price: If True, use (bid+ask)/2 for OHLC. If False, use bid prices.
        """
        self.use_mid_price = use_mid_price

    def aggregate_to_1m(self, ticks: List[Dict], symbol: str) -> List[Dict]:
        """
        Aggregate ticks to 1-minute OHLCV bars

        Args:
            ticks: List of tick dictionaries from decoder
            symbol: Trading pair symbol (e.g., 'EUR/USD')

        Returns:
            List of 1-minute bar dictionaries
        """
        if not ticks:
            return []

        # Group ticks by minute
        bars_by_minute = defaultdict(list)

        for tick in ticks:
            # Round timestamp to minute (remove seconds, microseconds)
            minute_key = tick['timestamp'].replace(second=0, microsecond=0)
            bars_by_minute[minute_key].append(tick)

        # Calculate OHLCV for each minute
        bars_1m = []

        for minute, minute_ticks in sorted(bars_by_minute.items()):
            bar = self._calculate_bar(minute, minute_ticks, symbol)

            # Validate bar
            if self._validate_bar(bar):
                bars_1m.append(bar)
            else:
                logger.warning(f"Invalid bar at {minute}, skipping")

        logger.info(f"✅ Aggregated {len(ticks)} ticks → {len(bars_1m)} bars for {symbol}")
        return bars_1m

    def _calculate_bar(self, minute: datetime, minute_ticks: List[Dict], symbol: str) -> Dict:
        """
        Calculate OHLCV bar from ticks within a minute

        Args:
            minute: Minute timestamp
            minute_ticks: All ticks within this minute
            symbol: Trading pair

        Returns:
            Dictionary with OHLCV data
        """
        # Calculate prices (mid-price or bid-only)
        if self.use_mid_price:
            prices = [(t['bid'] + t['ask']) / 2 for t in minute_ticks]
        else:
            prices = [t['bid'] for t in minute_ticks]

        # Volume (sum of bid + ask volumes)
        volumes = [t['bid_volume'] + t['ask_volume'] for t in minute_ticks]

        # Spread statistics
        spreads = [t['spread'] for t in minute_ticks]

        # OHLCV calculation
        bar = {
            'symbol': symbol,
            'timeframe': '1m',
            'timestamp': minute.replace(tzinfo=timezone.utc),
            'timestamp_ms': int(minute.timestamp() * 1000),
            'open': prices[0],
            'high': max(prices),
            'low': min(prices),
            'close': prices[-1],
            'volume': sum(volumes),
            'tick_count': len(minute_ticks),
            'spread_avg': sum(spreads) / len(spreads),
            'spread_min': min(spreads),
            'spread_max': max(spreads),
            'event_type': 'ohlcv',
            'source': 'dukascopy_historical',
            '_transport': 'nats'
        }

        return bar

    def _validate_bar(self, bar: Dict) -> bool:
        """
        Validate OHLCV bar sanity

        Checks:
        - High >= Low
        - High >= Open, Close
        - Low <= Open, Close
        - All prices are positive
        - Volume >= 0
        - Tick count > 0
        """
        o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']

        # Positive prices
        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
            logger.warning(f"Invalid bar: Non-positive prices (O={o}, H={h}, L={l}, C={c})")
            return False

        # High/Low consistency
        if h < l:
            logger.warning(f"Invalid bar: High ({h}) < Low ({l})")
            return False

        # High >= Open, Close
        if h < o or h < c:
            logger.warning(f"Invalid bar: High ({h}) < Open ({o}) or Close ({c})")
            return False

        # Low <= Open, Close
        if l > o or l > c:
            logger.warning(f"Invalid bar: Low ({l}) > Open ({o}) or Close ({c})")
            return False

        # Volume and tick count
        if bar['volume'] < 0:
            logger.warning(f"Invalid bar: Negative volume ({bar['volume']})")
            return False

        if bar['tick_count'] <= 0:
            logger.warning(f"Invalid bar: No ticks ({bar['tick_count']})")
            return False

        return True

    def get_stats(self, bars: List[Dict]) -> Dict:
        """
        Calculate statistics for aggregated bars

        Returns:
            Dictionary with bar count, volume stats, price range
        """
        if not bars:
            return {
                'bar_count': 0,
                'total_volume': 0.0,
                'avg_tick_count': 0
            }

        return {
            'bar_count': len(bars),
            'total_volume': sum(b['volume'] for b in bars),
            'avg_volume': sum(b['volume'] for b in bars) / len(bars),
            'avg_tick_count': sum(b['tick_count'] for b in bars) / len(bars),
            'avg_spread': sum(b['spread_avg'] for b in bars) / len(bars),
            'price_range': {
                'high': max(b['high'] for b in bars),
                'low': min(b['low'] for b in bars)
            }
        }
