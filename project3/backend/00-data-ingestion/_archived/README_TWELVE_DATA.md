# Data Ingestion Services - Twelve Data Primary Source

## Overview

Data ingestion layer mengumpulkan data pasar real-time dari Twelve Data API dan streaming ke NATS untuk diproses oleh Data Bridge.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           DATA INGESTION ARCHITECTURE               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐                              │
│  │  Twelve Data API │                              │
│  │  (Primary Source)│                              │
│  └────────┬─────────┘                              │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────┐                          │
│  │ Twelve Data Collector│                          │
│  │  - REST API (free)   │                          │
│  │  - WebSocket (Pro)   │                          │
│  │  - Rate: 800/day     │                          │
│  └────────┬─────────────┘                          │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────┐                          │
│  │   NATS Streaming     │                          │
│  │  - JetStream enabled │                          │
│  │  - Cluster: trading  │                          │
│  └────────┬─────────────┘                          │
│           │                                         │
│           ▼                                         │
│  ┌──────────────────────┐                          │
│  │    Data Bridge       │                          │
│  │  (02-data-pipeline)  │                          │
│  └──────────────────────┘                          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Services

### 1. **NATS Server** 📡
- **Purpose**: Message streaming infrastructure
- **Port**: 4222 (client), 8222 (monitoring)
- **Features**:
  - JetStream enabled (persistent streaming)
  - Cluster name: `trading-cluster`
  - Max payload: 8MB
  - Monitoring: http://localhost:8222

### 2. **Twelve Data Collector** 📊
- **Purpose**: Primary market data source
- **API Key**: Configured in `.env`
- **Features**:
  - REST API (free tier: 800 req/day)
  - WebSocket (Pro plan: $29/month)
  - Multi-API key failover
  - Rate limiting & usage tracking
  - Auto-fallback: WebSocket → REST

**Data Coverage:**
- 2,000+ Forex pairs
- 100,000+ total symbols
- Stocks, Crypto, Commodities
- 20 years historical data

**Quality:**
- Latency: ~170ms (WebSocket)
- Source: Major banks (institutional-grade)
- Rating: 4.4/5

## Quick Start

### 1. Setup Network
```bash
docker network create suho-network
```

### 2. Configure Environment
```bash
# Edit parent .env file
cd /mnt/g/khoirul/aitrading/project3/backend
nano .env

# Add your Twelve Data API key:
TWELVE_DATA_API_KEY_1=your-api-key-here
```

### 3. Deploy Services
```bash
cd 00-data-ingestion
docker-compose up -d
```

### 4. Verify Running
```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f twelve-data-collector
```

## Configuration

See `/backend/.env` for complete configuration.

Key settings:
- `TWELVE_DATA_API_KEY_1`: Your API key from twelvedata.com
- `NATS_URL`: NATS server connection
- `LOG_LEVEL`: INFO, DEBUG, WARNING, ERROR

## Monitoring

### NATS Dashboard
```
http://localhost:8222
```

### Check Logs
```bash
docker-compose logs -f
```

## Upgrading to Pro ($29/month)

Benefits:
- ✅ WebSocket real-time streaming
- ✅ 3,000 API calls/day
- ✅ ~170ms latency

To enable:
1. Subscribe at https://twelvedata.com/pricing
2. Update API key in `.env`
3. Set `streaming.enabled: true` in `config/config.yaml`
4. Restart: `docker-compose restart`

## Support

- Twelve Data: https://twelvedata.com/docs
- NATS: https://docs.nats.io

---

**Status**: ✅ Ready for Production (Free Tier)
