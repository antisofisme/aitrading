# External Data Collector

Economic Calendar and market data collection system with **Central Hub integration**.

## 🎯 New Features (Central Hub Integration)

### ✅ What Changed

1. **Central Hub SDK Integration**
   - Service registration & discovery
   - Periodic heartbeat with metrics
   - Graceful deregistration

2. **YAML Configuration System**
   - `config/scrapers.yaml` - Centralized configuration
   - Environment variable support
   - Hot-reload ready

3. **Modern Architecture**
   - `src/main.py` - Service orchestrator with Central Hub
   - `src/config/` - Configuration module
   - Clean separation of concerns

4. **Production Ready**
   - Dockerfile with SDK installation
   - docker-compose.yml with Central Hub dependency
   - Health checks and monitoring

### 📦 File Structure

```
external-data-collector/
├── src/
│   ├── main.py                          # Central Hub integrated service
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py                    # YAML config loader
│   ├── scrapers/
│   │   └── mql5_historical_scraper.py   # MQL5 Economic Calendar
│   └── utils/
│       └── date_tracker.py              # Date tracking utility
│
├── config/
│   └── scrapers.yaml                    # Service configuration
│
├── Dockerfile                            # With Central Hub SDK
├── docker-compose.yml                    # Full stack deployment
├── requirements.txt                      # Dependencies (no Playwright!)
│
├── docs/
│   └── HISTORICAL_SCRAPING_STRATEGY.md  # Technical details
│
├── README.md                             # This file
├── CENTRAL_HUB_INTEGRATION.md           # Integration guide
├── DEPLOYMENT.md                         # Deployment instructions
└── PROJECT_STRUCTURE.md                  # Project structure docs
```

## 🚀 Quick Start

### 1. Build & Deploy with Central Hub

```bash
# Build from backend root
cd /mnt/g/khoirul/aitrading/project3/backend

docker build \
  -f 00-data-ingestion/external-data-collector/Dockerfile \
  -t external-data-collector:latest \
  .

# Deploy with docker-compose
cd 00-data-ingestion/external-data-collector
docker-compose up -d

# Check logs
docker logs -f external-data-collector
```

### 2. Expected Output

```
================================================================================
EXTERNAL DATA COLLECTOR + CENTRAL HUB
================================================================================
Instance ID: external-data-collector-1
Log Level: INFO
Central Hub: Enabled
🚀 Starting External Data Collector...
✅ Registered with Central Hub: external-data-collector
🔧 Initializing scrapers...
✅ Initialized MQL5 Economic Calendar scraper
   Z.ai Parser: Enabled
   Database: JSON fallback
🔄 Starting scraping loop for mql5_economic_calendar (interval: 3600s)
✅ External Data Collector started with 1 scrapers
```

## ⚙️ Configuration

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
```

### YAML Configuration (`config/scrapers.yaml`)

```yaml
scrapers:
  mql5_economic_calendar:
    enabled: true
    source: mql5.com
    scrape_interval: 3600  # 1 hour

storage:
  type: json  # or postgresql

backfill:
  enabled: false  # Set true for 1-year backfill
  months_back: 12
```

## 📊 Features

### MQL5 Economic Calendar Scraper

- ✅ **aiohttp + BeautifulSoup** - No Playwright (no bot detection)
- ✅ **Z.ai Integration** - AI-powered adaptive HTML parsing
- ✅ **Smart Date Tracking** - Automatic missing date detection
- ✅ **Incremental Scraping** - Only update what's needed
- ✅ **Historical Backfill** - 1-year+ data collection

### Central Hub Features

- ✅ **Service Registration** - Auto-register on startup
- ✅ **Periodic Heartbeat** - Health & metrics reporting
- ✅ **Graceful Shutdown** - Proper deregistration
- ✅ **Metrics Tracking** - Events, dates, errors

### Data Quality

From production tests (405 events, 8 days):
- 87.9% have forecast values
- 95.1% have previous values
- 69.4% have actual values
- 64.4% complete (F+P+A)

## 🔄 Scraping Strategy

### Three Modes

1. **Initial Backfill** (One-time)
   ```bash
   # Set in config/scrapers.yaml
   backfill:
     enabled: true
     months_back: 12
   ```

2. **Daily Updates** (Automatic)
   - Runs every 1 hour (configurable)
   - Updates recent 7 days for actual values

3. **Custom Scraping** (Manual)
   ```bash
   docker exec -it external-data-collector \
     python3 scripts/run_backfill.py backfill --months 6
   ```

## 📈 Monitoring

### Central Hub Dashboard

```bash
curl http://suho-central-hub:7000/api/discovery/services

# Response includes:
{
  "name": "external-data-collector",
  "status": "healthy",
  "metrics": {
    "events_scraped": 18000,
    "dates_tracked": 250,
    "errors": 0
  }
}
```

### Service Metrics

- `events_scraped` - Total events collected
- `dates_tracked` - Total dates in coverage
- `errors` - Error count
- `last_scrape` - Last successful scrape

## 🛡️ Error Handling

### Fallback Behavior

- **No Central Hub**: Runs in standalone mode
- **No Database**: Falls back to JSON file tracking
- **No Z.ai Key**: Uses regex parser (still works!)

## 📚 Documentation

- **[CENTRAL_HUB_INTEGRATION.md](CENTRAL_HUB_INTEGRATION.md)** - Integration guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment instructions
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - File structure
- **[docs/HISTORICAL_SCRAPING_STRATEGY.md](docs/HISTORICAL_SCRAPING_STRATEGY.md)** - Technical strategy

## 🔧 Development

### Run Tests

```bash
# Build test image
docker build -f Dockerfile.historical -t mql5-test .

# Run tests
docker run --rm mql5-test
```

### Manual Scraping

```bash
# Enter container
docker exec -it external-data-collector bash

# Run backfill
python3 scripts/run_backfill.py backfill --months 12

# Update recent data
python3 scripts/run_backfill.py update --days 7

# Check coverage
python3 scripts/run_backfill.py report
```

## 🎯 Integration Pattern

Follows same pattern as other collectors:

- **polygon-live-collector** ✅
- **polygon-historical-downloader** ✅
- **external-data-collector** ✅ (THIS)

All use:
- Central Hub SDK
- YAML configuration
- Service registration
- Heartbeat monitoring

## 📝 Changes Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Integration** | Standalone | Central Hub SDK |
| **Configuration** | Hardcoded | YAML + environment |
| **Service Discovery** | None | Auto-registration |
| **Monitoring** | Manual | Automated heartbeat |
| **Architecture** | Script-based | Service-based |

## 🚨 Migration from Old Setup

Old files moved to `_archived/`:
- `economic_calendar_ai.py` - Old ForexFactory scraper
- `test_playwright_stealth.py` - Bot detection tests
- All Playwright/Selenium dependencies removed

## 🎉 Production Status

**✅ Ready for Production**

- All tests passed (4/4)
- Central Hub integrated
- Configuration system ready
- Documentation complete
- Docker deployment ready

---

**Version**: 2.0.0 (With Central Hub)
**Last Updated**: 2025-10-05
**Status**: Production Ready ✅
