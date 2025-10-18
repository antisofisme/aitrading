"""
Data Validator - Centralized NULL and data quality validation

PROBLEM SOLVED:
- Scattered NULL validation logic across multiple services
- Inconsistent validation rules
- Duplicated SQL NULL checks
- Missing runtime data validation

SOLUTION:
- Centralized validator with consistent rules
- SQL clause generator for query-level validation
- Python object validation for runtime checks
- Comprehensive OHLCV-specific validation

USAGE:
    # Runtime validation
    from shared.components.utils.data_validator import DataValidator

    bar = {
        'timestamp': datetime.now(timezone.utc),
        'open': 100.5,
        'high': 101.0,
        'low': 100.0,
        'close': 100.8,
        'volume': 1000
    }

    # Validate with exception on failure
    DataValidator.validate_ohlcv_bar(bar)

    # Validate with boolean return (no exception)
    is_valid = DataValidator.validate_ohlcv_bar(bar, allow_null=True)

    # SQL query validation
    query = f'''
        SELECT * FROM aggregates
        WHERE {DataValidator.validate_ohlcv_sql_clause()}
    '''
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import math
import logging

logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Raised when data validation fails"""
    pass


class DataValidator:
    """
    Centralized data validation for trading data

    Key Features:
    1. NULL/None validation
    2. Numeric validity (NaN, Inf checks)
    3. OHLC relationship validation
    4. Price positivity validation
    5. Volume non-negativity validation
    6. Timestamp range validation
    7. SQL clause generation for query-level validation
    """

    # Valid timestamp range for trading data
    MIN_TIMESTAMP = datetime(2000, 1, 1, tzinfo=timezone.utc)
    MAX_TIMESTAMP = datetime(2100, 1, 1, tzinfo=timezone.utc)

    @staticmethod
    def validate_ohlcv_bar(
        bar: Dict[str, Any],
        allow_null: bool = False,
        check_ohlc_relationship: bool = True
    ) -> bool:
        """
        Validate OHLCV bar data

        Args:
            bar: Dictionary with keys: timestamp, open, high, low, close, volume
            allow_null: If True, returns False on invalid data; If False, raises exception
            check_ohlc_relationship: If True, validates OHLC relationships (L <= O,C <= H)

        Returns:
            True if valid, False if invalid (when allow_null=True)

        Raises:
            DataValidationError: When data is invalid (when allow_null=False)

        Examples:
            >>> # Valid bar
            >>> bar = {
            ...     'timestamp': datetime.now(timezone.utc),
            ...     'open': 100.5,
            ...     'high': 101.0,
            ...     'low': 100.0,
            ...     'close': 100.8,
            ...     'volume': 1000
            ... }
            >>> DataValidator.validate_ohlcv_bar(bar)
            True

            >>> # Invalid bar (NULL value)
            >>> bar = {'timestamp': None, 'open': 100, 'high': 101, 'low': 99, 'close': 100, 'volume': 1000}
            >>> DataValidator.validate_ohlcv_bar(bar, allow_null=True)
            False

            >>> # Invalid bar (NaN value)
            >>> bar = {'timestamp': datetime.now(timezone.utc), 'open': float('nan'), ...}
            >>> DataValidator.validate_ohlcv_bar(bar, allow_null=True)
            False
        """
        required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

        # Check required fields exist
        for field in required_fields:
            if field not in bar:
                if allow_null:
                    return False
                raise DataValidationError(f"Missing required field: {field}")

        # Check for NULL/None
        for field in required_fields:
            if bar[field] is None:
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' is NULL")

        # Validate numeric fields (OHLCV)
        numeric_fields = ['open', 'high', 'low', 'close', 'volume']
        for field in numeric_fields:
            value = bar[field]

            # Type check
            if not isinstance(value, (int, float)):
                if allow_null:
                    return False
                raise DataValidationError(
                    f"Field '{field}' is not numeric: {type(value).__name__}"
                )

            # NaN/Inf check
            if math.isnan(value) or math.isinf(value):
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' is NaN or Inf")

        # Validate OHLC relationships
        if check_ohlc_relationship:
            o, h, l, c = bar['open'], bar['high'], bar['low'], bar['close']

            # High must be highest, Low must be lowest
            if not (l <= o <= h and l <= c <= h):
                if allow_null:
                    return False
                raise DataValidationError(
                    f"Invalid OHLC relationship: O={o} H={h} L={l} C={c} "
                    f"(Expected: L <= O,C <= H)"
                )

        # Validate positive prices
        price_fields = ['open', 'high', 'low', 'close']
        for field in price_fields:
            if bar[field] <= 0:
                if allow_null:
                    return False
                raise DataValidationError(
                    f"Price '{field}' must be positive: {bar[field]}"
                )

        # Validate non-negative volume
        if bar['volume'] < 0:
            if allow_null:
                return False
            raise DataValidationError(f"Volume cannot be negative: {bar['volume']}")

        # Validate timestamp
        ts = bar['timestamp']

        # Handle string timestamps
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except Exception as e:
                if allow_null:
                    return False
                raise DataValidationError(f"Invalid timestamp format: {ts} - {e}")

        # Check timestamp range
        if isinstance(ts, datetime):
            # Ensure timezone-aware
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            # Check reasonable range
            if ts < DataValidator.MIN_TIMESTAMP or ts > DataValidator.MAX_TIMESTAMP:
                if allow_null:
                    return False
                raise DataValidationError(
                    f"Timestamp out of range [{DataValidator.MIN_TIMESTAMP} - "
                    f"{DataValidator.MAX_TIMESTAMP}]: {ts}"
                )
        else:
            if allow_null:
                return False
            raise DataValidationError(
                f"Timestamp must be datetime or ISO string: {type(ts).__name__}"
            )

        return True

    @staticmethod
    def validate_tick_data(
        tick: Dict[str, Any],
        allow_null: bool = False
    ) -> bool:
        """
        Validate tick/quote data

        Args:
            tick: Dictionary with keys: timestamp, bid, ask, (optional: volume)
            allow_null: If True, returns False on invalid data; If False, raises exception

        Returns:
            True if valid, False if invalid (when allow_null=True)

        Raises:
            DataValidationError: When data is invalid (when allow_null=False)
        """
        required_fields = ['timestamp', 'bid', 'ask']

        # Check required fields
        for field in required_fields:
            if field not in tick:
                if allow_null:
                    return False
                raise DataValidationError(f"Missing required field: {field}")

        # Check for NULL
        for field in required_fields:
            if tick[field] is None:
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' is NULL")

        # Validate numeric fields
        bid, ask = tick['bid'], tick['ask']

        for field, value in [('bid', bid), ('ask', ask)]:
            if not isinstance(value, (int, float)):
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' is not numeric")

            if math.isnan(value) or math.isinf(value):
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' is NaN or Inf")

            if value <= 0:
                if allow_null:
                    return False
                raise DataValidationError(f"Field '{field}' must be positive: {value}")

        # Validate bid/ask relationship
        if bid > ask:
            if allow_null:
                return False
            raise DataValidationError(
                f"Bid cannot be greater than Ask: bid={bid}, ask={ask}"
            )

        # Validate timestamp (same as OHLCV)
        ts = tick['timestamp']
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except Exception as e:
                if allow_null:
                    return False
                raise DataValidationError(f"Invalid timestamp format: {ts}")

        if isinstance(ts, datetime):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)

            if ts < DataValidator.MIN_TIMESTAMP or ts > DataValidator.MAX_TIMESTAMP:
                if allow_null:
                    return False
                raise DataValidationError(f"Timestamp out of range: {ts}")

        return True

    @staticmethod
    def validate_null_sql_clause(
        fields: List[str],
        table_alias: Optional[str] = None
    ) -> str:
        """
        Generate SQL WHERE clause for NULL validation

        Args:
            fields: List of field names to check
            table_alias: Optional table alias (e.g., "t" for "t.field")

        Returns:
            SQL WHERE clause string

        Examples:
            >>> DataValidator.validate_null_sql_clause(['open', 'high', 'low', 'close'])
            'open IS NOT NULL AND high IS NOT NULL AND low IS NOT NULL AND close IS NOT NULL'

            >>> DataValidator.validate_null_sql_clause(['open', 'high'], table_alias='t')
            't.open IS NOT NULL AND t.high IS NOT NULL'
        """
        prefix = f"{table_alias}." if table_alias else ""
        conditions = [f"{prefix}{field} IS NOT NULL" for field in fields]
        return " AND ".join(conditions)

    @staticmethod
    def validate_ohlcv_sql_clause(
        table_alias: Optional[str] = None,
        include_volume_positive: bool = True,
        include_price_positive: bool = True
    ) -> str:
        """
        Generate SQL WHERE clause for OHLCV NULL and quality validation

        Args:
            table_alias: Optional table alias
            include_volume_positive: If True, adds "volume > 0" check
            include_price_positive: If True, adds price > 0 checks

        Returns:
            SQL WHERE clause string

        Examples:
            >>> DataValidator.validate_ohlcv_sql_clause()
            'time IS NOT NULL AND open IS NOT NULL AND high IS NOT NULL AND low IS NOT NULL AND close IS NOT NULL AND volume IS NOT NULL AND open > 0 AND high > 0 AND low > 0 AND close > 0 AND volume > 0'

            >>> DataValidator.validate_ohlcv_sql_clause(table_alias='a', include_volume_positive=False)
            'a.time IS NOT NULL AND a.open IS NOT NULL AND ... AND a.close > 0'
        """
        prefix = f"{table_alias}." if table_alias else ""
        # Note: Using 'time' instead of 'timestamp' to match ClickHouse schema
        fields = ['time', 'open', 'high', 'low', 'close', 'volume']

        # NULL checks
        conditions = [f"{prefix}{field} IS NOT NULL" for field in fields]

        # Positive price checks
        if include_price_positive:
            price_fields = ['open', 'high', 'low', 'close']
            conditions.extend([f"{prefix}{field} > 0" for field in price_fields])

        # Positive volume check
        if include_volume_positive:
            conditions.append(f"{prefix}volume > 0")

        return " AND ".join(conditions)

    @staticmethod
    def validate_tick_sql_clause(
        table_alias: Optional[str] = None,
        include_price_positive: bool = True
    ) -> str:
        """
        Generate SQL WHERE clause for tick/quote data validation

        Args:
            table_alias: Optional table alias
            include_price_positive: If True, adds price > 0 checks

        Returns:
            SQL WHERE clause string
        """
        prefix = f"{table_alias}." if table_alias else ""
        # Note: Using 'time' instead of 'timestamp' to match ClickHouse schema
        fields = ['time', 'bid', 'ask']

        # NULL checks
        conditions = [f"{prefix}{field} IS NOT NULL" for field in fields]

        # Positive price checks
        if include_price_positive:
            conditions.extend([f"{prefix}bid > 0", f"{prefix}ask > 0"])

        # Bid/Ask relationship check
        conditions.append(f"{prefix}bid <= {prefix}ask")

        return " AND ".join(conditions)

    @staticmethod
    def log_validation_errors(
        data_source: str,
        total_records: int,
        invalid_records: List[Dict[str, Any]],
        max_log: int = 5
    ) -> None:
        """
        Log validation errors in a consistent format

        Args:
            data_source: Source of data (e.g., "tick-aggregator", "historical-downloader")
            total_records: Total number of records processed
            invalid_records: List of invalid records with error details
            max_log: Maximum number of errors to log (default: 5)
        """
        if not invalid_records:
            logger.info(
                f"✅ [{data_source}] All {total_records} records passed validation"
            )
            return

        error_count = len(invalid_records)
        error_rate = (error_count / total_records * 100) if total_records > 0 else 0

        logger.warning(
            f"⚠️ [{data_source}] Validation failed: {error_count}/{total_records} "
            f"records ({error_rate:.2f}%)"
        )

        # Log first N errors
        for i, record in enumerate(invalid_records[:max_log]):
            error_msg = record.get('error', 'Unknown error')
            data_summary = record.get('data', {})
            logger.warning(f"   [{i+1}] {error_msg}")
            if data_summary:
                logger.warning(f"       Data: {data_summary}")

        if error_count > max_log:
            logger.warning(f"   ... and {error_count - max_log} more errors")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("DATA VALIDATOR - CENTRALIZED NULL & QUALITY VALIDATION")
    print("=" * 80)

    # Example 1: Valid OHLCV bar
    print("\n1. Valid OHLCV bar:")
    valid_bar = {
        'timestamp': datetime.now(timezone.utc),
        'open': 100.5,
        'high': 101.0,
        'low': 100.0,
        'close': 100.8,
        'volume': 1000
    }
    try:
        result = DataValidator.validate_ohlcv_bar(valid_bar)
        print(f"   ✅ Validation passed: {result}")
    except DataValidationError as e:
        print(f"   ❌ Validation failed: {e}")

    # Example 2: Invalid OHLCV bar (NULL value)
    print("\n2. Invalid OHLCV bar (NULL value):")
    invalid_bar = {
        'timestamp': datetime.now(timezone.utc),
        'open': None,
        'high': 101.0,
        'low': 100.0,
        'close': 100.8,
        'volume': 1000
    }
    result = DataValidator.validate_ohlcv_bar(invalid_bar, allow_null=True)
    print(f"   ❌ Validation result: {result}")

    # Example 3: Invalid OHLCV bar (NaN value)
    print("\n3. Invalid OHLCV bar (NaN value):")
    nan_bar = {
        'timestamp': datetime.now(timezone.utc),
        'open': float('nan'),
        'high': 101.0,
        'low': 100.0,
        'close': 100.8,
        'volume': 1000
    }
    result = DataValidator.validate_ohlcv_bar(nan_bar, allow_null=True)
    print(f"   ❌ Validation result: {result}")

    # Example 4: Invalid OHLC relationship
    print("\n4. Invalid OHLC relationship:")
    bad_relationship = {
        'timestamp': datetime.now(timezone.utc),
        'open': 100.5,
        'high': 99.0,  # High < Open (invalid!)
        'low': 100.0,
        'close': 100.8,
        'volume': 1000
    }
    result = DataValidator.validate_ohlcv_bar(bad_relationship, allow_null=True)
    print(f"   ❌ Validation result: {result}")

    # Example 5: SQL clause generation
    print("\n5. SQL WHERE clause generation:")
    print("   OHLCV clause:")
    print(f"   {DataValidator.validate_ohlcv_sql_clause()}")
    print("\n   OHLCV clause with alias:")
    print(f"   {DataValidator.validate_ohlcv_sql_clause(table_alias='a')}")
    print("\n   Tick clause:")
    print(f"   {DataValidator.validate_tick_sql_clause()}")

    print("\n" + "=" * 80)
