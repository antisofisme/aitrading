# Tick Aggregator Service

## Purpose
Aggregates raw tick data from TimescaleDB into OHLCV candles for multiple timeframes.

## Architecture

```
TimescaleDB.market_ticks (tick data)
↓
Tick Aggregator Service
- Query ticks from TimescaleDB (batch)
- Aggregate to 7 timeframes: M5, M15, M30, H1, H4, D1, W1
- Calculate OHLCV + indicators (future)
↓
NATS/Kafka (source='live_aggregated')
↓
Data Bridge → ClickHouse.aggregates
```

## Features

- **Batch Processing**: Queries TimescaleDB in batches for efficiency
- **Multi-Timeframe**: Supports 7 timeframes (M5, M15, M30, H1, H4, D1, W1)
- **Scheduled**: Runs on cron schedules (e.g., every 5 min for M5, every 15 min for M15)
- **Fault Tolerant**: Tracks last aggregation timestamp, can resume on restart
- **Indicator Ready**: Architecture supports adding technical indicators

## Timeframes

| Timeframe | Interval | Schedule | Use Case |
|-----------|----------|----------|----------|
| M5 | 5 minutes | Every 5 min | Entry timing & micro patterns |
| M15 | 15 minutes | Every 15 min | Intraday signals |
| M30 | 30 minutes | Every 30 min | Confirmation |
| H1 | 1 hour | Every hour | Short-term trend |
| H4 | 4 hours | Every 4 hours | Medium-term trend |
| D1 | 1 day | Daily at 00:00 UTC | Long-term trend |
| W1 | 1 week | Weekly on Monday | Major market structure |

## Output Format

```json
{
  "symbol": "EUR/USD",
  "timeframe": "5m",
  "timestamp_ms": 1706198400000,
  "open": 1.0850,
  "high": 1.0855,
  "low": 1.0848,
  "close": 1.0852,
  "volume": 1234,
  "vwap": 1.0851,
  "range_pips": 0.70,
  "body_pips": 0.20,
  "start_time": "2024-01-25T10:00:00+00:00",
  "end_time": "2024-01-25T10:05:00+00:00",
  "source": "live_aggregated",
  "event_type": "ohlcv"
}
```

## Configuration

See `config/aggregator.yaml` for:
- Timeframe schedules
- Batch sizes
- Lookback windows
- Database connections (from Central Hub)

## Usage

```bash
# Build
docker build -t suho-tick-aggregator .

# Run
docker run -d \
  --name suho-tick-aggregator \
  --env-file ../.env \
  suho-tick-aggregator
```
