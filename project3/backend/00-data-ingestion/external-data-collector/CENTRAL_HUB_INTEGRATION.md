# Central Hub Integration - External Data Collector

## 🏗️ Architecture Pattern

External Data Collector kini menggunakan **Central Hub pattern** yang sama dengan service lain (polygon-live-collector, polygon-historical-downloader).

### Central Hub SDK Integration

```python
from central_hub_sdk import CentralHubClient

# Initialize client
central_hub = CentralHubClient(
    service_name="external-data-collector",
    service_type="data-collector",
    version="1.0.0",
    capabilities=[
        "economic-calendar",
        "historical-backfill",
        "incremental-scraping",
        "mql5-data-source",
        "zai-parsing",
        "date-tracking"
    ],
    metadata={
        "sources": ["mql5.com"],
        "data_types": ["economic_calendar"],
        "storage": "json",
        "backfill_enabled": False
    }
)

# Register with Central Hub
await central_hub.register()

# Send periodic heartbeat with metrics
await central_hub.send_heartbeat(metrics={
    'events_scraped': 18000,
    'dates_tracked': 250,
    'errors': 0,
    'last_scrape': '2025-10-05T12:00:00'
})
```

## 📁 New File Structure

```
external-data-collector/
├── src/
│   ├── main.py                          # ✨ NEW - Central Hub integration
│   ├── config/
│   │   ├── __init__.py                  # ✨ NEW
│   │   └── config.py                    # ✨ NEW - YAML config loader
│   ├── scrapers/
│   │   └── mql5_historical_scraper.py   # Existing scraper
│   └── utils/
│       └── date_tracker.py              # Existing utility
│
├── config/
│   └── scrapers.yaml                    # ✨ NEW - Configuration file
│
├── Dockerfile                            # ✨ UPDATED - SDK installation
├── docker-compose.yml                    # ✨ UPDATED - Central Hub integration
├── requirements.txt                      # ✨ UPDATED - Removed Playwright
└── CENTRAL_HUB_INTEGRATION.md           # ✨ NEW - This file
```

## ⚙️ Configuration

### YAML Configuration (`config/scrapers.yaml`)

```yaml
scrapers:
  mql5_economic_calendar:
    enabled: true
    source: mql5.com
    priority: 1
    scrape_interval: 3600  # 1 hour
    metadata:
      data_type: economic_calendar
      update_mode: incremental
      parser: zai
      rate_limit_seconds: 2

storage:
  type: json  # or postgresql
  json_path: /app/data
  postgresql:
    host: suho-postgresql
    port: 5432
    database: aitrading

messaging:
  nats:
    enabled: false
  kafka:
    enabled: false

backfill:
  enabled: false  # Set true for initial backfill
  months_back: 12
  batch_days: 30

monitoring:
  metrics_enabled: true
  health_check_port: 8080
```

### Environment Variables

```bash
# Service identity
INSTANCE_ID=external-data-collector-1
LOG_LEVEL=INFO

# Central Hub
CENTRAL_HUB_URL=http://suho-central-hub:7000
HEARTBEAT_INTERVAL=30

# API Keys
ZAI_API_KEY=your-key-here

# Database (optional)
DB_HOST=suho-postgresql
DB_PORT=5432
DB_NAME=aitrading
DB_USER=postgres
DB_PASSWORD=your-password
```

## 🚀 Deployment

### Build Docker Image

```bash
# Build from backend root directory
cd /mnt/g/khoirul/aitrading/project3/backend

docker build \
  -f 00-data-ingestion/external-data-collector/Dockerfile \
  -t external-data-collector:latest \
  .
```

### Run with Docker Compose

```bash
cd 00-data-ingestion/external-data-collector

# Start service
docker-compose up -d

# Check logs
docker logs -f external-data-collector

# Expected output:
# ================================================================================
# EXTERNAL DATA COLLECTOR + CENTRAL HUB
# ================================================================================
# Instance ID: external-data-collector-1
# Log Level: INFO
# Central Hub: Enabled
# 🚀 Starting External Data Collector...
# ✅ Registered with Central Hub: external-data-collector
# 🔧 Initializing scrapers...
# ✅ Initialized MQL5 Economic Calendar scraper
#    Z.ai Parser: Enabled
#    Database: JSON fallback
# 🔄 Starting scraping loop for mql5_economic_calendar (interval: 3600s)
# ✅ External Data Collector started with 1 scrapers
```

## 🔗 Central Hub Features

### 1. Service Registration

Automatically registers with Central Hub on startup:

```python
{
    "name": "external-data-collector",
    "type": "data-collector",
    "version": "1.0.0",
    "capabilities": [
        "economic-calendar",
        "historical-backfill",
        "mql5-data-source"
    ],
    "metadata": {
        "sources": ["mql5.com"],
        "data_types": ["economic_calendar"]
    }
}
```

### 2. Periodic Heartbeat

Sends heartbeat every 30 seconds with metrics:

```python
{
    "service_name": "external-data-collector",
    "status": "healthy",
    "timestamp": 1696512000000,
    "metrics": {
        "events_scraped": 18000,
        "dates_tracked": 250,
        "errors": 0,
        "last_scrape": "2025-10-05T12:00:00"
    }
}
```

### 3. Graceful Shutdown

Deregisters from Central Hub on shutdown:

```bash
# Graceful stop
docker-compose down

# Logs:
# 🛑 Stopping External Data Collector...
# ✅ Deregistered from Central Hub
# ✅ External Data Collector stopped
```

## 📊 Monitoring & Metrics

### Service Metrics

- `events_scraped` - Total events collected
- `dates_tracked` - Total dates in coverage
- `errors` - Error count
- `last_scrape` - Last successful scrape timestamp

### Central Hub Dashboard

Access via Central Hub:

```bash
curl http://suho-central-hub:7000/api/discovery/services

# Response:
{
  "services": [
    {
      "name": "external-data-collector",
      "status": "healthy",
      "last_heartbeat": "2025-10-05T12:00:00Z",
      "metrics": {
        "events_scraped": 18000,
        "dates_tracked": 250
      }
    }
  ]
}
```

## 🔄 Scraping Loop

### Main Loop Flow

```
1. Register with Central Hub
   ↓
2. Initialize scrapers (MQL5)
   ↓
3. Run initial backfill (if enabled)
   ↓
4. Start heartbeat loop (every 30s)
   ↓
5. Start scraping loop (every 1 hour)
   ├── Scrape recent data (last 7 days)
   ├── Update metrics
   └── Send heartbeat
```

### Scraping Interval

- **Default**: 1 hour (3600 seconds)
- **Configurable**: `scrape_interval` in YAML
- **Rate Limiting**: 2 seconds between requests

## 🛡️ Error Handling

### Fallback Behavior

If Central Hub unavailable:

```python
# Collector will run in standalone mode
logger.warning("Central Hub SDK not available - running in standalone mode")

# All scraping functions work normally
# Just no registration/heartbeat with Central Hub
```

### Database Fallback

If PostgreSQL unavailable:

```python
# Falls back to JSON file tracking
storage_type = "json"
json_path = "/app/data/date_tracking.json"
```

## 🔧 Configuration Options

### Scraper Settings

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable scraper |
| `scrape_interval` | `3600` | Scrape interval (seconds) |
| `rate_limit_seconds` | `2` | Delay between requests |

### Storage Settings

| Option | Default | Description |
|--------|---------|-------------|
| `type` | `json` | Storage type (json/postgresql) |
| `json_path` | `/app/data` | JSON file directory |

### Backfill Settings

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `false` | Run backfill on start |
| `months_back` | `12` | Months to backfill |
| `batch_days` | `30` | Days per batch |

## 📝 Comparison with Old Setup

### Before (Without Central Hub)

```bash
# Old structure
external-data-collector/
├── test_mql5_simple.py           # Standalone test
├── Dockerfile.historical         # Standalone Docker
└── No service registration
    No heartbeat
    No centralized config
```

### After (With Central Hub)

```bash
# New structure
external-data-collector/
├── src/main.py                   # Central Hub integration
├── src/config/config.py          # YAML config loader
├── config/scrapers.yaml          # Centralized config
├── Dockerfile                    # SDK installation
└── ✅ Service registration
    ✅ Periodic heartbeat
    ✅ Centralized config
    ✅ Metrics reporting
```

## 🎯 Next Steps

1. ✅ Central Hub integration implemented
2. ✅ Configuration system created
3. ✅ Dockerfile updated with SDK
4. 🔄 Test deployment with Central Hub
5. 🔄 Enable database storage (optional)
6. 🔄 Enable messaging (NATS/Kafka) for data streaming
7. 🔄 Add monitoring dashboard integration

---

**Status**: ✅ Ready for deployment with Central Hub integration
**Version**: 1.0.0
**Last Updated**: 2025-10-05
