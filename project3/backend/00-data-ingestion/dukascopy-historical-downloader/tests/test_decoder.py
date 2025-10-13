"""
Unit tests for Dukascopy decoder
Tests binary .bi5 decoding functionality
"""
import pytest
import lzma
import struct
from datetime import datetime
import sys
sys.path.insert(0, '../src')

from decoder import DukascopyDecoder


class TestDukascopyDecoder:
    """Test binary tick decoder"""

    @pytest.fixture
    def decoder(self):
        return DukascopyDecoder()

    def test_decode_valid_ticks(self, decoder):
        """Test decoding valid tick data"""
        # Create mock binary data (2 ticks)
        ticks_data = b''

        # Tick 1: 0ms, ask=1.10000, bid=1.09990
        ticks_data += struct.pack('>IIIff',
            0,  # time_ms
            110000,  # ask_raw (1.10000 * 100000)
            109990,  # bid_raw (1.09990 * 100000)
            1.0,  # ask_volume
            1.0   # bid_volume
        )

        # Tick 2: 30000ms (30 seconds), ask=1.10010, bid=1.10000
        ticks_data += struct.pack('>IIIff',
            30000,  # time_ms
            110010,  # ask_raw
            110000,  # bid_raw
            2.0,  # ask_volume
            2.0   # bid_volume
        )

        # Compress with LZMA
        binary_data = lzma.compress(ticks_data)

        # Decode
        ticks = decoder.decode_bi5(
            binary_data,
            'EURUSD',
            2024, 1, 1, 0  # 2024-01-01 00:00
        )

        # Assertions
        assert len(ticks) == 2

        # Tick 1
        assert ticks[0]['bid'] == 1.09990
        assert ticks[0]['ask'] == 1.10000
        assert ticks[0]['spread'] == 0.00010

        # Tick 2
        assert ticks[1]['bid'] == 1.10000
        assert ticks[1]['ask'] == 1.10010
        assert ticks[1]['timestamp'].second == 30

    def test_decode_empty_data(self, decoder):
        """Test decoding empty binary data"""
        binary_data = lzma.compress(b'')

        ticks = decoder.decode_bi5(
            binary_data,
            'EURUSD',
            2024, 1, 1, 0
        )

        assert ticks == []

    def test_validate_tick(self, decoder):
        """Test tick validation logic"""
        # Valid tick
        assert decoder._validate_tick(1.09990, 1.10000, 1.0, 1.0) == True

        # Invalid: negative spread
        assert decoder._validate_tick(1.10000, 1.09990, 1.0, 1.0) == False

        # Invalid: zero price
        assert decoder._validate_tick(0, 1.10000, 1.0, 1.0) == False

        # Invalid: negative volume
        assert decoder._validate_tick(1.09990, 1.10000, -1.0, 1.0) == False

    def test_get_stats(self, decoder):
        """Test statistics calculation"""
        ticks = [
            {'spread': 0.0001, 'bid_volume': 1.0, 'ask_volume': 1.0},
            {'spread': 0.0002, 'bid_volume': 2.0, 'ask_volume': 2.0},
        ]

        stats = decoder.get_stats(ticks)

        assert stats['tick_count'] == 2
        assert stats['avg_spread'] == 0.00015
        assert stats['total_volume'] == 6.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
