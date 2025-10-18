"""
Dukascopy Binary Decoder (.bi5 format)
Decodes LZMA-compressed tick data from Dukascopy datafeed
"""
import lzma
import struct
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


class DukascopyDecoder:
    """
    Decodes Dukascopy .bi5 binary tick data files

    Format:
    - LZMA compressed binary file
    - Each tick = 20 bytes (5 fields × 4 bytes)
    - Big-endian byte order
    - Structure: >IIIff (3 uint32, 2 float32)
    """

    TICK_SIZE = 20  # bytes per tick
    PRICE_SCALE = 100000.0  # Prices stored as integer * 100000

    def decode_bi5(self, binary_data: bytes, symbol: str, year: int, month: int, day: int, hour: int) -> List[Dict]:
        """
        Decode .bi5 file to tick list

        Args:
            binary_data: Raw .bi5 file bytes (LZMA compressed)
            symbol: Trading pair (e.g., 'EURUSD')
            year, month, day, hour: Timestamp components for this file

        Returns:
            List of tick dictionaries with timestamp, bid, ask, volumes
        """
        try:
            # Step 1: Decompress LZMA
            decompressed = lzma.decompress(binary_data)

            # Step 2: Parse ticks
            ticks = []
            tick_count = len(decompressed) // self.TICK_SIZE

            # Hour start timestamp
            hour_start = datetime(year, month, day, hour, 0, 0)

            for i in range(tick_count):
                offset = i * self.TICK_SIZE
                chunk = decompressed[offset:offset + self.TICK_SIZE]

                if len(chunk) < self.TICK_SIZE:
                    logger.warning(f"Incomplete tick at offset {offset}, skipping")
                    break

                # Parse 20-byte structure (big-endian)
                # Format: >IIIff
                # - time_ms: milliseconds from hour start (uint32)
                # - ask_raw: ask price * 100000 (uint32)
                # - bid_raw: bid price * 100000 (uint32)
                # - ask_vol: ask volume (float32)
                # - bid_vol: bid volume (float32)
                try:
                    time_ms, ask_raw, bid_raw, ask_vol, bid_vol = struct.unpack('>IIIff', chunk)
                except struct.error as e:
                    logger.warning(f"Failed to parse tick at offset {offset}: {e}")
                    continue

                # Convert prices (stored as integer * 100000)
                ask = ask_raw / self.PRICE_SCALE
                bid = bid_raw / self.PRICE_SCALE

                # Calculate timestamp
                timestamp = hour_start + timedelta(milliseconds=time_ms)

                # Validate tick data
                if not self._validate_tick(bid, ask, bid_vol, ask_vol):
                    continue

                # Total volume (optional field, not in core schema)
                total_volume = bid_vol + ask_vol

                # NEW: 6-column schema aligned with live_ticks/historical_ticks
                # Mid and spread removed (calculate on-the-fly when needed)
                ticks.append({
                    'timestamp': timestamp,
                    'symbol': symbol.replace('', ''),  # Will be formatted in main.py
                    'bid': bid,
                    'ask': ask,
                    'volume': total_volume,  # Optional metadata
                    'source': 'dukascopy_historical'
                })

            logger.info(f"✅ Decoded {len(ticks)} ticks from {symbol} {year}-{month:02d}-{day:02d} {hour:02d}:00")
            return ticks

        except lzma.LZMAError as e:
            logger.error(f"❌ LZMA decompression failed for {symbol} {year}-{month:02d}-{day:02d} {hour:02d}h: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Decode error for {symbol} {year}-{month:02d}-{day:02d} {hour:02d}h: {e}")
            return []

    def _validate_tick(self, bid: float, ask: float, bid_vol: float, ask_vol: float) -> bool:
        """
        Validate tick data sanity

        Checks:
        - Prices are positive
        - Ask >= Bid (no negative spread)
        - Spread is reasonable (< 1% of price)
        - Volumes are non-negative
        """
        # Positive prices
        if bid <= 0 or ask <= 0:
            return False

        # No negative spread
        if ask < bid:
            logger.warning(f"Invalid tick: ask ({ask}) < bid ({bid})")
            return False

        # Reasonable spread (< 1% of mid-price)
        mid = (bid + ask) / 2
        spread = ask - bid
        if spread > (mid * 0.01):
            logger.warning(f"Excessive spread: {spread} ({spread/mid*100:.2f}%)")
            return False

        # Non-negative volumes
        if bid_vol < 0 or ask_vol < 0:
            return False

        return True

    def get_stats(self, ticks: List[Dict]) -> Dict:
        """
        Calculate statistics for decoded ticks

        Returns:
            Dictionary with tick count, spread stats, volume stats
        """
        if not ticks:
            return {
                'tick_count': 0,
                'avg_spread': 0.0,
                'avg_volume': 0.0
            }

        spreads = [t['spread'] for t in ticks]
        volumes = [t['bid_volume'] + t['ask_volume'] for t in ticks]

        return {
            'tick_count': len(ticks),
            'avg_spread': sum(spreads) / len(spreads),
            'min_spread': min(spreads),
            'max_spread': max(spreads),
            'avg_volume': sum(volumes) / len(volumes),
            'total_volume': sum(volumes)
        }
