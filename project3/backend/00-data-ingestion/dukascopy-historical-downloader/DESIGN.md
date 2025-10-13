# Dukascopy Historical Downloader - Design Document

## Overview

Service untuk download historical tick data dari Dukascopy, aggregate ke 1m bars, dan publish ke NATS.

**Key Differences vs Polygon:**
- Source: Dukascopy (FREE, Swiss bank quality)
- Format: Binary .bi5 files (tick data)
- Processing: Decode binary → Aggregate ticks → Publish 1m bars
- Table: `historical_dukascopy` (separate from Polygon)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DUKASCOPY HISTORICAL DOWNLOADER                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. DOWNLOADER                                              │
│     ├─ Download .bi5 files (hourly tick data)              │
│     └─ URL: datafeed.dukascopy.com/datafeed/{symbol}/...   │
│                                                             │
│  2. DECODER                                                 │
│     ├─ Decompress LZMA                                      │
│     ├─ Parse 20-byte tick structures                        │
│     └─ Convert to timestamp + bid/ask prices                │
│                                                             │
│  3. AGGREGATOR                                              │
│     ├─ Group ticks by minute                                │
│     ├─ Calculate OHLCV from ticks                           │
│     └─ Output: 60 bars per hour                             │
│                                                             │
│  4. PUBLISHER (NATS)                                        │
│     ├─ Publish to: market.{symbol}.1m                       │
│     ├─ Cluster: nats-1, nats-2, nats-3                      │
│     └─ Fallback: Disk buffer                                │
│                                                             │
│  5. CENTRAL HUB INTEGRATION                                 │
│     ├─ Get NATS/Kafka config from Central Hub               │
│     ├─ Send heartbeat & progress                            │
│     └─ Report completion status                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ NATS Publish
         ▼
┌─────────────────────┐
│   NATS Cluster      │
│  nats-1, 2, 3       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Data Bridge       │
│  (3 instances)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  ClickHouse                         │
│  Table: historical_dukascopy        │
│  Source: 'dukascopy_historical'     │
└─────────────────────────────────────┘
```

---

## Data Flow

### 1. Download Phase
```python
# For each symbol, each date, each hour:
url = f"https://datafeed.dukascopy.com/datafeed/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

# Example: EUR/USD, 2024-01-01, 00:00-00:59
url = "https://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/01/00h_ticks.bi5"
response = requests.get(url)
binary_data = response.content
```

### 2. Decode Phase
```python
import lzma
import struct

# Decompress LZMA
decompressed = lzma.decompress(binary_data)

# Parse ticks (20 bytes each)
ticks = []
for i in range(0, len(decompressed), 20):
    chunk = decompressed[i:i+20]

    # Struct: >IIIff (big-endian: 3 uint32, 2 float)
    time_ms, ask_raw, bid_raw, ask_vol, bid_vol = struct.unpack('>IIIff', chunk)

    # Convert prices (stored as integer * 100000)
    ask = ask_raw / 100000.0
    bid = bid_raw / 100000.0

    # Calculate timestamp
    hour_start = datetime(year, month, day, hour, 0, 0)
    timestamp = hour_start + timedelta(milliseconds=time_ms)

    ticks.append({
        'timestamp': timestamp,
        'bid': bid,
        'ask': ask,
        'bid_volume': bid_vol,
        'ask_volume': ask_vol
    })
```

### 3. Aggregate Phase
```python
# Group ticks by minute
from collections import defaultdict

bars_by_minute = defaultdict(list)
for tick in ticks:
    minute_key = tick['timestamp'].replace(second=0, microsecond=0)
    bars_by_minute[minute_key].append(tick)

# Calculate OHLCV for each minute
bars_1m = []
for minute, minute_ticks in sorted(bars_by_minute.items()):
    # Use mid-price: (bid + ask) / 2
    prices = [(t['bid'] + t['ask']) / 2 for t in minute_ticks]
    volumes = [t['bid_volume'] + t['ask_volume'] for t in minute_ticks]

    bar = {
        'symbol': symbol,
        'timeframe': '1m',
        'timestamp': minute,
        'timestamp_ms': int(minute.timestamp() * 1000),
        'open': prices[0],
        'high': max(prices),
        'low': min(prices),
        'close': prices[-1],
        'volume': sum(volumes),
        'tick_count': len(minute_ticks),
        'spread_avg': sum((t['ask'] - t['bid']) for t in minute_ticks) / len(minute_ticks)
    }
    bars_1m.append(bar)
```

### 4. Publish Phase
```python
# Publish to NATS (same as Polygon)
for bar in bars_1m:
    message = {
        **bar,
        'event_type': 'ohlcv',
        'source': 'dukascopy_historical',
        '_transport': 'nats'
    }

    subject = f"market.{symbol.replace('/', '')}.1m"
    await nats_client.publish(subject, json.dumps(message).encode())
```

---

## Database Schema

### ClickHouse Table (via data-bridge)

```sql
-- Same table structure as Polygon, but with 'source' differentiation
-- Table: suho_analytics.aggregates (reuse existing table)

-- Query examples:
-- Polygon data:
SELECT * FROM aggregates WHERE source = 'polygon_historical'

-- Dukascopy data:
SELECT * FROM aggregates WHERE source = 'dukascopy_historical'

-- Compare sources:
SELECT
    source,
    COUNT(*) as bars,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest
FROM aggregates
WHERE symbol = 'EUR/USD' AND timeframe = '1m'
GROUP BY source
```

**Reuse existing table, differentiate by `source` field:**
- `polygon_historical` - From Polygon API
- `polygon_live` - From Polygon WebSocket
- `dukascopy_historical` - From Dukascopy (this service)

---

## Service Components

### File Structure
```
dukascopy-historical-downloader/
├── Dockerfile
├── requirements.txt
├── config/
│   └── pairs.yaml          # Trading pairs configuration
├── src/
│   ├── main.py             # Main service entry point
│   ├── config.py           # Config loader (Central Hub integration)
│   ├── downloader.py       # Download .bi5 files from Dukascopy
│   ├── decoder.py          # Decode binary tick data
│   ├── aggregator.py       # Aggregate ticks to 1m OHLCV bars
│   ├── publisher.py        # NATS/Kafka publisher (reuse from polygon)
│   └── period_tracker.py   # Track downloaded periods (prevent re-download)
└── tests/
    ├── test_decoder.py     # Test binary decoding
    ├── test_aggregator.py  # Test OHLCV calculation
    └── test_integration.py # End-to-end test
```

### Dependencies (requirements.txt)
```txt
# HTTP client
requests>=2.31.0
aiohttp>=3.9.0

# Binary decoding
lzma
struct

# Messaging
nats-py>=2.6.0
aiokafka>=0.10.0

# ClickHouse (for verification)
clickhouse-driver>=0.2.6

# Central Hub SDK
central-hub-sdk>=1.0.0

# Utilities
pyyaml>=6.0
python-dateutil>=2.8.2
pytz>=2023.3
```

---

## Configuration

### pairs.yaml (Same as Polygon)
```yaml
# Trading pairs configuration
trading_pairs:
  - symbol: "EUR/USD"
    dukascopy_symbol: "EURUSD"
    priority: 1

  - symbol: "GBP/USD"
    dukascopy_symbol: "GBPUSD"
    priority: 1

  - symbol: "USD/JPY"
    dukascopy_symbol: "USDJPY"
    priority: 1

  # ... all 14 pairs

# Download configuration
download:
  start_date: "2015-01-01"
  end_date: "today"
  chunk_months: 3  # Download in 3-month chunks to prevent OOM

# Aggregation settings
aggregation:
  timeframe: "1m"
  use_mid_price: true  # Use (bid+ask)/2 for OHLC

# Schedule
schedule:
  initial_download:
    on_startup: true
  gap_check:
    interval_hours: 24  # Daily gap check
```

---

## Central Hub Integration

### Service Registration
```python
from central_hub_sdk import CentralHubClient, ProgressLogger

central_hub = CentralHubClient(
    service_name="dukascopy-historical-downloader",
    service_type="data-downloader",
    version="1.0.0",
    capabilities=[
        "historical-tick-download",
        "binary-decoding",
        "tick-aggregation",
        "nats-publishing"
    ],
    metadata={
        "source": "dukascopy.com",
        "mode": "historical",
        "data_types": ["tick", "1m_bars"],
        "quality": "swiss_bank_grade"
    }
)

await central_hub.register()
```

### Progress Reporting
```python
# During download
progress = ProgressLogger(
    task_name=f"Downloading {symbol} ticks",
    total_items=total_hours,  # e.g., 8760 hours for 1 year
    service_name="dukascopy-downloader",
    milestones=[25, 50, 75, 100],
    heartbeat_interval=30
)

progress.start()
for hour in range(total_hours):
    download_hour(...)
    progress.update(current=hour, additional_info={"ticks": tick_count})

progress.complete(summary={"total_ticks": total, "total_bars": bars})
```

---

## Performance Considerations

### Download Speed
- **Concurrent downloads**: 5-10 parallel requests
- **Rate limiting**: Dukascopy no official limit, but use 10 req/sec max
- **Retry logic**: 3 attempts with exponential backoff

### Memory Management
- **Stream processing**: Process hour-by-hour (don't load full year)
- **Batch publishing**: Publish 100 bars at a time
- **Cleanup**: Delete .bi5 files after processing

### Storage Optimization
- **No tick storage**: Only store aggregated 1m bars
- **Compression**: LZMA for any local cache files
- **Deduplication**: Check period_tracker before download

---

## Monitoring & Alerts

### Health Checks
```python
# Every 5 minutes
await central_hub.send_heartbeat(metrics={
    "status": "downloading",
    "current_symbol": symbol,
    "current_date": date,
    "progress_pct": progress_percentage,
    "ticks_processed": tick_count,
    "bars_published": bar_count
})
```

### Alerts
- Download failures (> 3 retries)
- Decoding errors (corrupt .bi5 files)
- OHLCV validation failures (H < L, etc)
- NATS publish failures (circuit breaker)

---

## Testing Strategy

### Unit Tests
```python
# test_decoder.py
def test_decode_sample_bi5():
    """Test decoding a sample .bi5 file"""
    binary_data = load_sample_bi5()
    ticks = decode_bi5(binary_data)

    assert len(ticks) > 0
    assert all('timestamp' in t for t in ticks)
    assert all('bid' in t for t in ticks)
    assert all('ask' in t for t in ticks)

# test_aggregator.py
def test_aggregate_ticks_to_1m():
    """Test OHLCV calculation from ticks"""
    ticks = generate_test_ticks(count=100)
    bars = aggregate_to_1m(ticks)

    assert len(bars) == 1  # All ticks within same minute
    assert bars[0]['high'] >= bars[0]['low']
    assert bars[0]['open'] == ticks[0]['price']
    assert bars[0]['close'] == ticks[-1]['price']
```

### Integration Test
```python
# test_integration.py
async def test_full_pipeline():
    """Test end-to-end: Download → Decode → Aggregate → Publish"""
    # Download 1 hour of data
    binary_data = await download_hour('EURUSD', '2024-01-01', hour=0)

    # Decode
    ticks = decode_bi5(binary_data)
    assert len(ticks) > 0

    # Aggregate
    bars_1m = aggregate_to_1m(ticks)
    assert len(bars_1m) == 60  # 60 minutes

    # Publish (mock NATS)
    published = await publish_bars(bars_1m, mock=True)
    assert published == 60
```

---

## Deployment

### Docker Compose
```yaml
dukascopy-historical-downloader:
  build:
    context: .
    dockerfile: 00-data-ingestion/dukascopy-historical-downloader/Dockerfile
  container_name: suho-dukascopy-historical
  hostname: suho-dukascopy-historical
  environment:
    - INSTANCE_ID=dukascopy-historical-1
    - LOG_LEVEL=INFO
  volumes:
    - ./00-data-ingestion/dukascopy-historical-downloader/config:/app/config:ro
    - dukascopy_logs:/var/log/dukascopy
    - dukascopy_data:/data  # For period tracker
  depends_on:
    - nats-1
    - nats-2
    - nats-3
    - kafka
    - central-hub
  networks:
    - suho-network
  labels:
    - "com.suho.service=dukascopy-historical-downloader"
    - "com.suho.type=data-ingestion"
```

---

## Migration Plan

### Phase 1: Initial Setup (Week 1)
1. ✅ Create service structure
2. ✅ Implement downloader + decoder
3. ✅ Implement aggregator
4. ✅ Integrate with Central Hub
5. ✅ Test with 1 day of data

### Phase 2: Full Download (Week 2)
1. Download 2015-2025 for all 14 pairs
2. Monitor progress via Central Hub
3. Validate data quality
4. Estimated: 2-3 days download time

### Phase 3: Validation (Week 3)
1. Compare Dukascopy vs Polygon (sample periods)
2. Check gap coverage
3. Validate OHLCV calculations
4. Performance tuning

### Phase 4: Production (Week 4)
1. Daily maintenance mode (download yesterday's data)
2. Gap detection and filling
3. Monitoring and alerts
4. Documentation

---

## Success Metrics

### Data Quality
- ✅ 100% date coverage (no gaps)
- ✅ OHLCV validation (H >= L, O/C within range)
- ✅ Tick count > 0 for all minutes
- ✅ No decoding errors

### Performance
- ✅ Download: ~1 hour per year per symbol
- ✅ Processing: ~10 minutes per year per symbol
- ✅ Total: ~2-3 days for full historical (2015-2025, 14 pairs)

### Reliability
- ✅ Retry success rate > 99%
- ✅ NATS publish success rate > 99.9%
- ✅ Zero data loss (disk buffer for failures)

---

## Future Enhancements

### Phase 2 Features
1. **Tick storage** (optional): Store raw ticks for re-aggregation
2. **Custom timeframes**: 3m, 7m, 2h, etc.
3. **Spread analysis**: Track bid-ask spread statistics
4. **Data validation**: Compare with other sources (FXCM, OANDA)

### Phase 3 Features
1. **Real-time mode**: Download hourly data with 1-2 hour delay
2. **Backfill detection**: Auto-detect and fill gaps
3. **Data export**: Export to CSV/Parquet for external analysis

---

**Status:** Design Complete ✅
**Next Step:** Implementation
**Estimated Effort:** 1-2 weeks
**Dependencies:** Central Hub SDK, NATS cluster, ClickHouse
