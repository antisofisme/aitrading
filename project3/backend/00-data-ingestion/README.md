# Data Ingestion - Twelve Data Collector

## 🎯 Overview

**Twelve Data Collector** mengumpulkan market data real-time dari Twelve Data API dan menyimpannya ke database menggunakan **hybrid approach** (database-first + streaming).

---

## 🏗️ Architecture - Hybrid Approach

```
┌────────────────────────────────────────────────────────┐
│              TWELVE DATA COLLECTION                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────────┐                                 │
│  │ Twelve Data API  │  (Primary Source)               │
│  │ - REST API       │  Pro Plan: $29/month            │
│  │ - WebSocket      │  40 Symbols (Refined)           │
│  └────────┬─────────┘                                 │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────────────┐                         │
│  │ Twelve Data Collector    │                         │
│  │ - WebSocket (8 symbols)  │                         │
│  │ - REST Poll (32 symbols) │                         │
│  │ - Rate Limit Management  │                         │
│  └────────┬─────────────────┘                         │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────────────┐                         │
│  │ Data Manager             │ ← CRITICAL LAYER        │
│  │ - Database Abstraction   │                         │
│  │ - Multi-DB Routing       │                         │
│  │ - Connection Pooling     │                         │
│  └────────┬─────────────────┘                         │
│           │                                            │
│           ├──→ DATABASE (PRIMARY - Data Safety)       │
│           │    ├─ TimescaleDB (ticks, candles)        │
│           │    ├─ ClickHouse (analytics)              │
│           │    └─ DragonflyDB (cache)                 │
│           │                                            │
│           └──→ NATS/Kafka (OPTIONAL - Streaming)      │
│                └─ For real-time consumers             │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### **Key Principles:**

1. **Database-First**: Data saved to database BEFORE streaming
2. **Data Safety**: No data loss if NATS/Kafka down
3. **Replay Capability**: From database, not message queue
4. **Multi-Level Caching**: Memory → DragonflyDB → Database
5. **Smart Routing**: Data Manager routes to optimal database

---

## 📊 Data Coverage - Pro Plan ($29/month)

### **40 Symbols (Quality Over Quantity)**

**TIER 1: WebSocket Real-time** (8 symbols)
- **Trading Pairs** (4): EUR/USD, USD/JPY, USD/CAD, XAU/USD
- **Analysis Pairs** (4): AUD/JPY, EUR/GBP, GBP/JPY, EUR/JPY

**TIER 2: REST Polling** (32 symbols)
- **Macro** (8): US10Y, DXY, SPX, VIX, DE10Y, JP10Y, COPPER, SILVER
- **Forex** (20): GBP/USD, AUD/USD, NZD/USD, USD/CHF, etc.
- **Commodities** (2): WTI/USD, NATGAS
- **Crypto** (2): BTC/USD, ETH/USD

**See**: `PRO_PLAN_SUMMARY.md` for complete breakdown

---

## 🔄 Data Flow

### **1. Collection Layer**

```python
# twelve-data-collector/main.py

class TwelveDataCollector:
    async def collect_tick(self, symbol: str):
        """Collect tick from Twelve Data API"""

        # Get from Twelve Data
        tick_data = await self.twelve_data_client.get_quote(symbol)

        # Convert to internal format
        tick = TickData(
            symbol=tick_data['symbol'],
            timestamp=tick_data['timestamp'],
            bid=tick_data['bid'],
            ask=tick_data['ask'],
            source='twelve-data'
        )

        # Save via Data Manager (DATABASE FIRST)
        await self.data_manager.save_tick(tick)
```

### **2. Data Manager Layer**

```python
# central-hub/shared/components/data-manager/router.py

class DataRouter:
    async def save_tick(self, tick: TickData):
        """Save tick to database + cache"""

        # 1. Save to TimescaleDB (PRIMARY)
        await self.timescale_pool.save_tick(tick)

        # 2. Cache in DragonflyDB (1 hour TTL)
        await self.dragonfly_pool.cache_tick(tick, ttl=3600)

        # 3. Optional: Publish to NATS (for real-time consumers)
        if self.streaming_enabled:
            await self.nats_publisher.publish(f"tick.{tick.symbol}", tick)
```

### **3. Database Storage**

```sql
-- TimescaleDB (Primary storage)
CREATE TABLE market_ticks (
    time        TIMESTAMPTZ NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    bid         DOUBLE PRECISION,
    ask         DOUBLE PRECISION,
    spread      DOUBLE PRECISION,
    volume      DOUBLE PRECISION,
    source      VARCHAR(50)
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('market_ticks', 'time');

-- Create index for fast symbol lookups
CREATE INDEX idx_symbol_time ON market_ticks (symbol, time DESC);
```

---

## 🚀 Quick Start

### **1. Prerequisites**

```bash
# Twelve Data API Key
# Get from: https://twelvedata.com/pricing
# Pro Plan: $29/month (recommended)
```

### **2. Configuration**

```bash
# Edit backend/.env
TWELVE_DATA_API_KEY_1=your-api-key-here
TWELVE_DATA_API_KEY_2=optional-backup-key
TWELVE_DATA_API_KEY_3=optional-backup-key
```

### **3. Deploy**

```bash
cd /mnt/g/khoirul/aitrading/project3/backend/00-data-ingestion

# Start services
docker-compose up -d

# Check logs
docker logs twelve-data-collector-1 -f
```

### **4. Verify**

```bash
# Check collector health
curl http://localhost:8090/health

# Check database
docker exec -it suho-postgresql psql -U suho_admin -d suho_trading -c "SELECT COUNT(*) FROM market_ticks;"

# Check cache
docker exec -it suho-dragonflydb redis-cli -a dragonfly_secure_2024 GET "tick:latest:EUR/USD"
```

---

## 📁 Project Structure

```
00-data-ingestion/
├── README.md                           # This file
├── README_TWELVE_DATA.md               # Twelve Data details
├── QUICK_START.md                      # Quick deployment guide
├── DOCUMENTATION_INDEX.md              # Doc navigator
│
├── PRO_PLAN_SUMMARY.md                 # 40 symbols strategy
├── REFINED_ALLOCATION_PRO.md           # Symbol selection rationale
├── QUICK_REFERENCE.md                  # Trading guide
├── PAIR_CLASSIFICATION.md              # Pair details
├── GROW_PLAN_TIERS.md                  # Pricing info
│
├── twelve-data-collector/              # Main collector service
│   ├── main.py                         # Entry point
│   ├── config/
│   │   └── config-pro-plan-refined.yaml  # 40 symbols config
│   ├── api/                            # API layer
│   ├── business/                       # Business logic
│   ├── infrastructure/                 # Infra (logging, config)
│   └── integration/                    # External integrations
│       ├── twelve_data/                # Twelve Data client
│       ├── central_hub/                # Central Hub client
│       └── streaming/                  # NATS publisher
│
└── _archived/                          # Old documentation
    ├── broker-api/                     # Old OANDA collector
    ├── external-data/                  # Old external data
    └── outdated-broker-docs/           # Old broker-focused docs
```

---

## ⚙️ Configuration

### **Symbol Configuration**

**File**: `twelve-data-collector/config/config-pro-plan-refined.yaml`

```yaml
# TIER 1: WebSocket (8 symbols max)
streaming:
  instruments:
    forex_trading:
      - "EUR/USD"
      - "USD/JPY"
      - "USD/CAD"
    commodities_trading:
      - "XAU/USD"
    forex_analysis:
      - "AUD/JPY"
      - "EUR/GBP"
      - "GBP/JPY"
      - "EUR/JPY"

# TIER 2: REST (32 symbols)
rest_instruments:
  macro:
    yields: [US10Y, DE10Y, JP10Y]
    indices: [DXY, SPX, VIX]
    commodities: [COPPER, SILVER]
  forex: [GBP/USD, AUD/USD, ...20 pairs]
  commodities_extended: [WTI/USD, NATGAS]
  crypto: [BTC/USD, ETH/USD]
```

### **Rate Limits (Pro Plan)**

```yaml
rate_limits:
  rest_per_minute: 55       # Pro: 55 req/min
  rest_per_day: 15000       # Pro: 15,000 req/day
  batch_size: 12            # 12 symbols = 1 API call
```

---

## 📊 Monitoring

### **Health Check**

```bash
curl http://localhost:8090/health

# Response
{
  "status": "healthy",
  "service": "twelve-data-collector",
  "version": "2.0.0-pro-refined",
  "uptime": 3600,
  "collectors": {
    "websocket": {
      "status": "connected",
      "symbols": 8,
      "latency_ms": 170
    },
    "rest": {
      "status": "active",
      "symbols": 32,
      "requests_today": 1250,
      "daily_limit": 15000
    }
  },
  "database": {
    "timescale": "healthy",
    "clickhouse": "healthy",
    "dragonfly": "healthy"
  }
}
```

### **Metrics**

```bash
# Check tick count
curl http://localhost:8090/metrics

# Database metrics
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c "
SELECT
    symbol,
    COUNT(*) as tick_count,
    MAX(time) as last_tick
FROM market_ticks
WHERE time > NOW() - INTERVAL '1 hour'
GROUP BY symbol
ORDER BY tick_count DESC;
"
```

---

## 🔧 Integration Points

### **1. Data Manager Integration**

```python
from central_hub.shared.components.data_manager import DataRouter

# Initialize router
data_router = DataRouter()

# Save tick (database-first)
await data_router.save_tick(tick_data)

# Query latest
latest = await data_router.get_latest_tick('EUR/USD')
```

### **2. NATS Streaming (Optional)**

```python
from integration.streaming.nats_publisher import NATSPublisher

# After database save, optionally publish
nats = NATSPublisher(nats_url='nats://suho-nats-server:4222')
await nats.publish(f'tick.{symbol}', tick_data)
```

### **3. Central Hub Registration**

```python
from integration.central_hub.client import CentralHubClient

hub = CentralHubClient(host='suho-central-hub', port=7000)
await hub.register_service({
    'service_name': 'twelve-data-collector',
    'capabilities': ['rest-api', 'websocket-streaming'],
    'symbols_count': 40
})
```

---

## 💰 Cost Analysis

### **Pro Plan: $29/month**

```yaml
Investment: $29/month = $348/year

What You Get:
✅ 40 high-quality symbols (refined allocation)
✅ Real-time WebSocket (8 symbols, ~170ms latency)
✅ REST API (55 req/min, 15,000 req/day)
✅ Historical data (up to 20 years)
✅ Macro instruments (US10Y, DXY, SPX, VIX)
✅ Complete forex correlation matrix
✅ Commodities + Crypto coverage

Break-Even:
- Prevent 1 bad trade/month, OR
- Improve win rate by 1-2%, OR
- Better entries by 5-10 pips

ROI: Excellent! ⭐⭐⭐⭐⭐
```

---

## 🎯 Performance Targets

### **Collection Performance**

- **WebSocket Latency**: <200ms (target: 170ms)
- **REST Polling**: Every 3 minutes (32 symbols)
- **Database Save**: <5ms (p95)
- **Cache Update**: <2ms (p95)
- **Total Pipeline**: <10ms (collection → database → cache)

### **Reliability**

- **Uptime**: >99.5%
- **Data Completeness**: >99%
- **Failover Time**: <5s (API key rotation)
- **Reconnect**: Auto (WebSocket disconnection)

### **Scalability**

- **Tick Rate**: 50+ ticks/second (supported)
- **Daily Volume**: ~2M ticks/day (estimated)
- **Storage**: ~100MB/day (compressed TimescaleDB)
- **Database Query**: <10ms (recent data with cache)

---

## 📚 Documentation

### **Quick References**

- **[QUICK_START.md](./QUICK_START.md)** - 5-minute deployment
- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Trading guide
- **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Complete navigator

### **Strategy & Allocation**

- **[PRO_PLAN_SUMMARY.md](./PRO_PLAN_SUMMARY.md)** - 40 symbols overview
- **[REFINED_ALLOCATION_PRO.md](./REFINED_ALLOCATION_PRO.md)** - Why these symbols?
- **[PAIR_CLASSIFICATION.md](./PAIR_CLASSIFICATION.md)** - Trading vs analysis

### **Pricing**

- **[GROW_PLAN_TIERS.md](./GROW_PLAN_TIERS.md)** - Pricing tiers ($29/$49/$79)

### **Technical**

- **[README_TWELVE_DATA.md](./README_TWELVE_DATA.md)** - Twelve Data details
- **[Central Hub Data Manager](../01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md)** - Database layer

---

## 🚨 Troubleshooting

### **WebSocket Not Connecting**

```bash
# Check API key
echo $TWELVE_DATA_API_KEY_1

# Check config
cat twelve-data-collector/config/config-pro-plan-refined.yaml | grep "enabled: true"

# Check logs
docker logs twelve-data-collector-1 | grep -i websocket
```

### **Rate Limit Exceeded**

```bash
# Check current usage
curl http://localhost:8090/metrics | jq '.api_usage'

# Reduce polling frequency
# Edit: config-pro-plan-refined.yaml
# Change: poll_interval from 180 to 300 seconds
```

### **Database Connection Failed**

```bash
# Check database health
docker exec suho-postgresql pg_isready

# Check credentials
echo $POSTGRES_PASSWORD

# Restart collector
docker-compose restart twelve-data-collector
```

---

## ✅ Next Steps

1. **Deploy Collector**: Follow `QUICK_START.md`
2. **Verify Data Flow**: Check database + cache
3. **Historical Backfill**: Download 10 years data (separate service)
4. **Build Strategies**: Use collected data for trading signals
5. **Monitor Performance**: Set up dashboards

---

## 📞 Support

- **Twelve Data**: https://twelvedata.com/docs
- **Central Hub**: http://suho-central-hub:7000/health
- **Data Manager Spec**: `../01-core-infrastructure/central-hub/DATA_MANAGER_SPEC.md`

---

**🚀 Architecture**: Hybrid Approach (Database-First + Optional Streaming)
**📊 Coverage**: 40 Symbols (Quality Over Quantity)
**💰 Cost**: $29/month Pro Plan
**✅ Status**: Production Ready

---

**Last Updated**: 2025-10-02
**Version**: 2.0.0-hybrid
