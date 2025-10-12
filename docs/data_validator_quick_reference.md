# DataValidator Quick Reference

## Import
```python
from shared.components.utils.data_validator import DataValidator, DataValidationError
```

## Runtime Validation

### OHLCV Bar Validation
```python
# Validate with exception on error
DataValidator.validate_ohlcv_bar(bar)

# Validate with boolean return (no exception)
is_valid = DataValidator.validate_ohlcv_bar(bar, allow_null=True)

# Skip OHLC relationship check
DataValidator.validate_ohlcv_bar(bar, check_ohlc_relationship=False)
```

### Tick Data Validation
```python
# Validate tick/quote data
DataValidator.validate_tick_data(tick)
DataValidator.validate_tick_data(tick, allow_null=True)
```

## SQL Clause Generation

### OHLCV Clauses
```python
# Full validation (NULL + positive prices + positive volume)
WHERE {DataValidator.validate_ohlcv_sql_clause()}
# Output: timestamp IS NOT NULL AND open IS NOT NULL AND ... AND open > 0 AND ... AND volume > 0

# With table alias
WHERE {DataValidator.validate_ohlcv_sql_clause(table_alias='a')}
# Output: a.timestamp IS NOT NULL AND a.open IS NOT NULL AND ...

# Without volume positivity check
WHERE {DataValidator.validate_ohlcv_sql_clause(include_volume_positive=False)}
# Output: ... AND volume IS NOT NULL (but NOT volume > 0)

# Without price positivity check
WHERE {DataValidator.validate_ohlcv_sql_clause(include_price_positive=False)}
```

### Tick Clauses
```python
# Tick validation (bid/ask)
WHERE {DataValidator.validate_tick_sql_clause()}
# Output: timestamp IS NOT NULL AND bid IS NOT NULL AND ask IS NOT NULL AND bid > 0 AND ask > 0 AND bid <= ask

# With table alias
WHERE {DataValidator.validate_tick_sql_clause(table_alias='t')}
```

### Generic NULL Check
```python
# Custom field NULL validation
WHERE {DataValidator.validate_null_sql_clause(['field1', 'field2', 'field3'])}
# Output: field1 IS NOT NULL AND field2 IS NOT NULL AND field3 IS NOT NULL

# With table alias
WHERE {DataValidator.validate_null_sql_clause(['field1', 'field2'], table_alias='t')}
```

## Error Logging

```python
# Log validation errors
DataValidator.log_validation_errors(
    data_source='my-service',
    total_records=100,
    invalid_records=[
        {'error': 'NULL timestamp', 'data': {'symbol': 'EURUSD'}},
        {'error': 'NaN in price', 'data': {'symbol': 'GBPUSD'}}
    ],
    max_log=5  # Log first 5 errors
)
```

## Validation Checks Performed

### OHLCV Bar
- Required fields exist: timestamp, open, high, low, close, volume
- No NULL/None values
- Numeric validity (no NaN, no Inf)
- OHLC relationship: L <= O,C <= H
- Price positivity: O,H,L,C > 0
- Volume non-negativity: volume >= 0
- Timestamp range: 2000-01-01 to 2100-01-01

### Tick Data
- Required fields exist: timestamp, bid, ask
- No NULL/None values
- Numeric validity (no NaN, no Inf)
- Price positivity: bid, ask > 0
- Bid/Ask relationship: bid <= ask
- Timestamp range validation

## Exception Handling

```python
try:
    DataValidator.validate_ohlcv_bar(bar)
    # Process valid data
    process_bar(bar)
except DataValidationError as e:
    logger.error(f"Validation failed: {e}")
    # Handle invalid data
```

## Common Patterns

### Pattern 1: Batch Validation
```python
valid_bars = []
invalid_bars = []

for bar in bars:
    if DataValidator.validate_ohlcv_bar(bar, allow_null=True):
        valid_bars.append(bar)
    else:
        invalid_bars.append(bar)

logger.info(f"Valid: {len(valid_bars)}, Invalid: {len(invalid_bars)}")
```

### Pattern 2: Query with Validation
```python
query = f"""
    SELECT *
    FROM aggregates
    WHERE symbol = %(symbol)s
      AND timeframe = %(timeframe)s
      AND {DataValidator.validate_ohlcv_sql_clause()}
    ORDER BY timestamp DESC
    LIMIT 1000
"""
```

### Pattern 3: Inverted Validation (Find BAD Data)
```python
# Find records with invalid data
query = f"""
    SELECT *
    FROM aggregates
    WHERE symbol = %(symbol)s
      AND NOT ({DataValidator.validate_ohlcv_sql_clause()})
"""
```

## Files

- **Validator**: `/mnt/g/khoirul/aitrading/project3/backend/shared/components/utils/data_validator.py`
- **Tests**: `/mnt/g/khoirul/aitrading/tests/test_data_validator.py`
- **Docs**: `/mnt/g/khoirul/aitrading/docs/data_validator_implementation.md`

## Run Tests

```bash
cd /mnt/g/khoirul/aitrading
python3 -m pytest tests/test_data_validator.py -v
```

## Run Example

```bash
python3 project3/backend/shared/components/utils/data_validator.py
```
