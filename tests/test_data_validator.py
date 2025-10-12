"""
Test suite for DataValidator - Centralized NULL and quality validation

Tests:
1. Valid OHLCV bar validation
2. NULL value detection
3. NaN/Inf detection
4. OHLC relationship validation
5. Positive price validation
6. Volume validation
7. Timestamp validation
8. SQL clause generation
9. Tick data validation
10. Error logging functionality
"""

import pytest
from datetime import datetime, timezone, timedelta
import math
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from project3.backend.shared.components.utils.data_validator import (
    DataValidator,
    DataValidationError
)


class TestOHLCVValidation:
    """Test OHLCV bar validation"""

    def test_valid_ohlcv_bar(self):
        """Test validation of a valid OHLCV bar"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 100.5,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        # Should pass without exception
        result = DataValidator.validate_ohlcv_bar(bar)
        assert result is True

    def test_null_timestamp(self):
        """Test detection of NULL timestamp"""
        bar = {
            'timestamp': None,
            'open': 100.5,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        # With allow_null=True, should return False
        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

        # With allow_null=False (default), should raise exception
        with pytest.raises(DataValidationError) as exc_info:
            DataValidator.validate_ohlcv_bar(bar)
        assert "timestamp" in str(exc_info.value).lower()

    def test_null_price(self):
        """Test detection of NULL in OHLC"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': None,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_nan_value(self):
        """Test detection of NaN values"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': float('nan'),
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

        with pytest.raises(DataValidationError) as exc_info:
            DataValidator.validate_ohlcv_bar(bar)
        assert "nan" in str(exc_info.value).lower()

    def test_inf_value(self):
        """Test detection of Infinity values"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 100.5,
            'high': float('inf'),
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_invalid_ohlc_relationship(self):
        """Test OHLC relationship validation"""
        # High < Open (invalid)
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 101.0,
            'high': 100.0,  # High should be highest
            'low': 99.0,
            'close': 100.5,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

        with pytest.raises(DataValidationError) as exc_info:
            DataValidator.validate_ohlcv_bar(bar)
        assert "ohlc relationship" in str(exc_info.value).lower()

    def test_negative_price(self):
        """Test detection of negative prices"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': -100.5,
            'high': 101.0,
            'low': -100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_zero_price(self):
        """Test detection of zero prices"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 0.0,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_negative_volume(self):
        """Test detection of negative volume"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 100.5,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': -1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_timestamp_out_of_range(self):
        """Test detection of timestamp outside valid range"""
        # Year 1999 (before 2000)
        bar = {
            'timestamp': datetime(1999, 1, 1, tzinfo=timezone.utc),
            'open': 100.5,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

    def test_timestamp_string_format(self):
        """Test ISO string timestamp parsing"""
        bar = {
            'timestamp': '2025-10-12T10:30:00Z',
            'open': 100.5,
            'high': 101.0,
            'low': 100.0,
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar)
        assert result is True

    def test_missing_required_field(self):
        """Test detection of missing required fields"""
        bar = {
            'timestamp': datetime.now(timezone.utc),
            'open': 100.5,
            'high': 101.0,
            # 'low' is missing
            'close': 100.8,
            'volume': 1000
        }

        result = DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        assert result is False

        with pytest.raises(DataValidationError) as exc_info:
            DataValidator.validate_ohlcv_bar(bar)
        assert "missing" in str(exc_info.value).lower()


class TestTickValidation:
    """Test tick/quote data validation"""

    def test_valid_tick(self):
        """Test validation of valid tick data"""
        tick = {
            'timestamp': datetime.now(timezone.utc),
            'bid': 100.5,
            'ask': 100.6
        }

        result = DataValidator.validate_tick_data(tick)
        assert result is True

    def test_bid_greater_than_ask(self):
        """Test detection of bid > ask (invalid)"""
        tick = {
            'timestamp': datetime.now(timezone.utc),
            'bid': 100.7,
            'ask': 100.5
        }

        result = DataValidator.validate_tick_data(tick, allow_null=True)
        assert result is False

    def test_null_bid(self):
        """Test detection of NULL bid"""
        tick = {
            'timestamp': datetime.now(timezone.utc),
            'bid': None,
            'ask': 100.6
        }

        result = DataValidator.validate_tick_data(tick, allow_null=True)
        assert result is False


class TestSQLClauseGeneration:
    """Test SQL WHERE clause generation"""

    def test_null_sql_clause_basic(self):
        """Test basic NULL check SQL clause"""
        fields = ['open', 'high', 'low', 'close']
        clause = DataValidator.validate_null_sql_clause(fields)

        assert 'open IS NOT NULL' in clause
        assert 'high IS NOT NULL' in clause
        assert 'low IS NOT NULL' in clause
        assert 'close IS NOT NULL' in clause
        assert ' AND ' in clause

    def test_null_sql_clause_with_alias(self):
        """Test NULL check SQL clause with table alias"""
        fields = ['open', 'high']
        clause = DataValidator.validate_null_sql_clause(fields, table_alias='t')

        assert 't.open IS NOT NULL' in clause
        assert 't.high IS NOT NULL' in clause

    def test_ohlcv_sql_clause_full(self):
        """Test OHLCV SQL clause with all validations"""
        clause = DataValidator.validate_ohlcv_sql_clause()

        # Should contain NULL checks
        assert 'timestamp IS NOT NULL' in clause
        assert 'open IS NOT NULL' in clause

        # Should contain positive price checks
        assert 'open > 0' in clause
        assert 'high > 0' in clause
        assert 'low > 0' in clause
        assert 'close > 0' in clause

        # Should contain positive volume check
        assert 'volume > 0' in clause

    def test_ohlcv_sql_clause_with_alias(self):
        """Test OHLCV SQL clause with table alias"""
        clause = DataValidator.validate_ohlcv_sql_clause(table_alias='a')

        assert 'a.timestamp IS NOT NULL' in clause
        assert 'a.open > 0' in clause

    def test_ohlcv_sql_clause_no_volume_check(self):
        """Test OHLCV SQL clause without volume positivity check"""
        clause = DataValidator.validate_ohlcv_sql_clause(include_volume_positive=False)

        assert 'volume IS NOT NULL' in clause
        assert 'volume > 0' not in clause

    def test_tick_sql_clause(self):
        """Test tick data SQL clause generation"""
        clause = DataValidator.validate_tick_sql_clause()

        assert 'timestamp IS NOT NULL' in clause
        assert 'bid IS NOT NULL' in clause
        assert 'ask IS NOT NULL' in clause
        assert 'bid > 0' in clause
        assert 'ask > 0' in clause
        assert 'bid <= ask' in clause


class TestErrorLogging:
    """Test error logging functionality"""

    def test_log_no_errors(self, caplog):
        """Test logging when all records are valid"""
        import logging
        caplog.set_level(logging.INFO)

        DataValidator.log_validation_errors('test-service', 100, [])

        assert 'All 100 records passed validation' in caplog.text or 'passed validation' in caplog.text

    def test_log_with_errors(self, caplog):
        """Test logging with validation errors"""
        invalid_records = [
            {'error': 'NULL timestamp', 'data': {'symbol': 'EURUSD'}},
            {'error': 'NaN in price', 'data': {'symbol': 'GBPUSD'}},
            {'error': 'Negative volume', 'data': {'symbol': 'XAUUSD'}}
        ]

        DataValidator.log_validation_errors('test-service', 100, invalid_records, max_log=2)

        assert 'Validation failed' in caplog.text
        assert '3/100' in caplog.text
        assert 'NULL timestamp' in caplog.text
        assert 'NaN in price' in caplog.text


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_batch_validation(self):
        """Test validating a batch of bars"""
        bars = [
            {
                'timestamp': datetime.now(timezone.utc),
                'open': 100.0 + i,
                'high': 101.0 + i,
                'low': 99.0 + i,
                'close': 100.5 + i,
                'volume': 1000 * (i + 1)
            }
            for i in range(10)
        ]

        # All should be valid
        results = [DataValidator.validate_ohlcv_bar(bar) for bar in bars]
        assert all(results)

    def test_sql_integration_example(self):
        """Test SQL clause in a real query format"""
        # Example of how it would be used in gap_detector.py
        query = f"""
            SELECT * FROM aggregates
            WHERE symbol = 'EURUSD'
              AND timeframe = '1h'
              AND {DataValidator.validate_ohlcv_sql_clause()}
            ORDER BY timestamp DESC
        """

        assert 'timestamp IS NOT NULL' in query
        assert 'open > 0' in query
        assert 'volume > 0' in query

    def test_performance_with_large_dataset(self):
        """Test validator performance with large dataset"""
        import time

        # Create 1000 bars
        bars = [
            {
                'timestamp': datetime.now(timezone.utc) - timedelta(hours=i),
                'open': 100.0,
                'high': 101.0,
                'low': 99.0,
                'close': 100.5,
                'volume': 1000
            }
            for i in range(1000)
        ]

        start = time.time()
        valid_count = sum(
            1 for bar in bars
            if DataValidator.validate_ohlcv_bar(bar, allow_null=True)
        )
        elapsed = time.time() - start

        assert valid_count == 1000
        assert elapsed < 1.0  # Should complete in under 1 second


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
