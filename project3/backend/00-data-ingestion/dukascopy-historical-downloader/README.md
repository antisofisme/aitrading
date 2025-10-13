# Dukascopy Historical Downloader

Service for downloading historical forex/gold tick data from Dukascopy, aggregating to 1-minute OHLCV bars, and publishing to NATS.

## Features

- **Swiss Bank Grade Data**: FREE tick-level data from Dukascopy
- **Binary Decoding**: LZMA decompression and 20-byte tick parsing
- **Tick Aggregation**: Converts raw ticks to 1-minute OHLCV bars
- **NATS Publishing**: Publishes to 3-node NATS cluster
- **Central Hub Integration**: Centralized config and heartbeat
- **Gap Detection**: Auto-detects and fills missing dates
- **Period Tracking**: Prevents duplicate downloads

## Architecture

```
Download → Decode → Aggregate → Publish → Data Bridge → ClickHouse
  .bi5      Ticks     1m OHLCV    NATS       (3x)      historical_data
```

## Data Source

- **Provider**: Dukascopy (datafeed.dukascopy.com)
- **Format**: Binary .bi5 files (LZMA compressed)
- **Granularity**: Tick data (bid/ask/volume)
- **Coverage**: 2008+ for major pairs
- **Delay**: 1-2 hours from real-time
- **Cost**: FREE

## Configuration

### pairs.yaml

```yaml
trading_pairs:
  - symbol: "EUR/USD"
    dukascopy_symbol: "EURUSD"
    priority: 1

download:
  start_date: "2015-01-01"
  end_date: "today"
  max_concurrent: 10

aggregation:
  timeframe: "1m"
  use_mid_price: true

schedule:
  initial_download:
    on_startup: true
  gap_check:
    enabled: true
    lookback_days: 90
```

## Environment Variables

```bash
INSTANCE_ID=dukascopy-historical-1
LOG_LEVEL=INFO
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=9000
```

## Usage

### Build and Run

```bash
# Build
docker-compose build dukascopy-historical-downloader

# Run
docker-compose up -d dukascopy-historical-downloader

# Logs
docker logs -f suho-dukascopy-historical
```

### Manual Trigger

```bash
# Restart to trigger full download
docker restart suho-dukascopy-historical

# Check progress
docker exec suho-dukascopy-historical cat /var/log/dukascopy/downloader.log
```

## Testing

```bash
# Run unit tests
cd tests
pytest test_decoder.py -v
pytest test_aggregator.py -v

# Test with sample data
python test_integration.py
```

## Data Flow

1. **Gap Detection**: Query ClickHouse for missing dates
2. **Download**: Fetch .bi5 files for each missing hour
3. **Decode**: LZMA decompress + binary parsing
4. **Aggregate**: Group ticks by minute, calculate OHLCV
5. **Publish**: Send to NATS (market.{symbol}.1m)
6. **Storage**: Data Bridge inserts to ClickHouse

## Performance

- **Download Speed**: ~10 hours/second (rate limited)
- **Processing**: ~1000 ticks/second per core
- **Memory**: ~500MB peak (streaming processing)
- **Estimated Time**: 2-3 days for full 2015-2025 download (14 pairs)

## Monitoring

- **Heartbeat**: Every 60 seconds to Central Hub
- **Progress**: Logged every 100 hours downloaded
- **Errors**: Automatic retry (3 attempts, exponential backoff)
- **Statistics**: Download count, error rate, bars published

## Troubleshooting

### Issue: Download failures

**Cause**: Network timeout, rate limiting
**Fix**: Service auto-retries with exponential backoff

### Issue: LZMA decompression errors

**Cause**: Corrupt .bi5 file, no data for hour
**Fix**: Service skips and logs warning

### Issue: NATS publish failures

**Cause**: NATS cluster connection lost
**Fix**: Auto-reconnect, publishes after reconnection

## Comparison: Polygon vs Dukascopy

| Feature | Polygon | Dukascopy |
|---------|---------|-----------|
| Cost | Paid (unlimited) | FREE |
| Granularity | 1m pre-aggregated | Tick-level |
| Coverage | 2023+ (gaps) | 2008+ (complete) |
| Quality | Good | Swiss bank grade |
| Delay | Real-time | 1-2 hours |
| Use Case | Live trading | Historical training |

## Next Steps

1. Run initial download (2015-2025)
2. Validate data quality vs Polygon
3. Enable daily gap checks
4. Monitor performance and optimize

## Related Services

- **polygon-historical-downloader**: Similar architecture for Polygon data
- **data-bridge**: Consumes NATS and writes to ClickHouse
- **central-hub**: Configuration and heartbeat management

---

**Status**: Implementation Complete ✅
**Version**: 1.0.0
**Last Updated**: 2025-01-12
