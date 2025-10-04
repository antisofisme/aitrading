# OANDA Collector Service

Multi-account OANDA data collector with automatic failover support for the Suho AI Trading Platform.

## 🎯 Overview

The OANDA Collector is a Python-based microservice that:
- Streams real-time pricing data from OANDA v20 API
- Supports multiple OANDA accounts with automatic failover
- Publishes market data directly to NATS for Data Bridge consumption
- Integrates with Central Hub for service discovery and configuration
- Handles up to 20 concurrent streams per IP address

## 🏗️ Architecture

```
┌─────────────────┐
│  OANDA v20 API  │
└────────┬────────┘
         │ Real-time Streaming
         ▼
┌─────────────────────────────────────────┐
│     OANDA Collector Service             │
│  ┌───────────────────────────────────┐  │
│  │  API Layer                        │  │
│  │  - StreamingAPI                   │  │
│  │  - PricingAPI                     │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Business Layer                   │  │
│  │  - AccountManager (Failover)      │  │
│  │  - StreamManager (Buffering)      │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Integration Layer                │  │
│  │  - OandaClient                    │  │
│  │  - CentralHubClient               │  │
│  │  - NatsPublisher                  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  Infrastructure Layer             │  │
│  │  - ServiceRegistry                │  │
│  │  - ConfigManager                  │  │
│  │  - MemoryStore                    │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │                    │
         ▼                    ▼
  ┌────────────┐      ┌─────────────┐
  │    NATS    │      │ Central Hub │
  │ (To Data   │      │ (Discovery) │
  │  Bridge)   │      └─────────────┘
  └────────────┘
```

## 📋 Features

### Multi-Account Support
- Configure up to 4 OANDA accounts
- Priority-based account selection
- Automatic failover on connection failures
- Health monitoring per account
- Cooldown period for failed accounts

### Real-time Streaming
- Concurrent streaming for multiple instruments
- Automatic reconnection on disconnects
- Buffering with configurable size
- Heartbeat monitoring
- Rate limit tracking (20 streams/IP)

### Data Publishing
- Direct NATS publishing to Data Bridge
- Structured message contracts
- Pricing data: `market.pricing.oanda.{instrument}`
- Candles data: `market.candles.oanda.{instrument}.{granularity}`
- Heartbeat: `service.heartbeat.oanda-collector.{instance_id}`

### Integration
- Service discovery via Central Hub
- Dynamic configuration updates
- Health reporting
- Shared memory coordination
- Contract-based communication

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OANDA API account(s)
- Access to Central Hub and NATS services
- Parent `.env` file configured

### Environment Variables

All variables are configured in the parent `.env` file:
```bash
# Located at: project3/backend/.env

# OANDA Configuration
OANDA_ENVIRONMENT=practice  # or 'live'
OANDA_ACCOUNT_ID_1=7030924
OANDA_API_TOKEN_1=your_token_here

# Central Hub
CENTRAL_HUB_HOST=central-hub
CENTRAL_HUB_PORT=3000

# NATS
NATS_URL=nats://nats:4222
NATS_CLUSTER_ID=trading-cluster
```

### Running with Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f oanda-collector-1

# Stop
docker-compose down
```

### Running Standalone

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py
```

## 📁 Project Structure

```
oanda-collector/
├── api/                          # API Layer
│   ├── streaming.py              # Streaming API
│   └── pricing.py                # Pricing API
├── business/                     # Business Logic
│   ├── account_manager.py        # Multi-account management
│   └── stream_manager.py         # Stream lifecycle
├── integration/                  # External Integrations
│   ├── oanda/                    # OANDA v20 client
│   ├── central_hub/              # Central Hub client
│   └── streaming/                # NATS publisher
├── infrastructure/               # Infrastructure Layer
│   ├── discovery/                # Service registry
│   ├── config/                   # Configuration management
│   ├── memory/                   # Memory store
│   └── logging/                  # Logging setup
├── contracts/                    # Communication contracts
│   ├── http-rest/                # REST contracts
│   ├── nats-kafka/               # Message contracts
│   └── internal/                 # Internal contracts
├── config/                       # Configuration files
│   └── config.yaml               # Service configuration
├── tests/                        # Tests
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
├── main.py                       # Main application
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
├── docker-compose.yml            # Multi-instance setup
└── README.md                     # This file
```

## ⚙️ Configuration

### config.yaml

Main configuration file with environment variable substitution:

```yaml
service:
  name: "oanda-collector"
  instance_id: "${INSTANCE_ID:-oanda-collector-1}"

oanda:
  environment: "${OANDA_ENVIRONMENT:-practice}"
  accounts:
    - id: "${OANDA_ACCOUNT_ID_1}"
      token: "${OANDA_API_TOKEN_1}"
      priority: 1
      enabled: true

streaming:
  instruments:
    forex:
      - "EUR_USD"
      - "GBP_USD"
      # ... more instruments

nats:
  url: "${NATS_URL:-nats://nats:4222}"
  subjects:
    pricing: "market.pricing.oanda"
    candles: "market.candles.oanda"
```

## 🔄 Data Flow

### Pricing Stream Flow
```
OANDA API → OandaClient → StreamManager → StreamingAPI → NatsPublisher
                                                              ↓
                                                         Data Bridge
```

### Account Failover Flow
```
Connection Error → AccountManager.failover() → New Account Selected
                         ↓
              StreamManager reconnects streams
                         ↓
              Publishes failover notification
```

## 📊 Monitoring

### Health Checks
- Service health endpoint (planned)
- Central Hub health reports
- NATS heartbeat messages
- Account health monitoring

### Metrics
- Ticks per second
- Active streams count
- Account failover events
- Buffer utilization
- NATS publish success rate

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=. tests/
```

## 🔐 Security

- API tokens stored in parent `.env` file
- No credentials in code or config files
- Secure container networking
- Rate limiting enforcement
- Connection timeout handling

## 📝 Contracts

All communication follows standardized contracts:

- **To Central Hub**: Service registration, health reports
- **From Central Hub**: Configuration updates
- **To Data Bridge**: Pricing/candles streams (via NATS)
- **Internal**: Account failover notifications

See [contracts/README.md](contracts/README.md) for details.

## 🐛 Troubleshooting

### Common Issues

**No data streaming:**
- Check OANDA credentials
- Verify network connectivity
- Check NATS connection
- Review logs for errors

**Frequent failovers:**
- Check account health
- Verify API rate limits
- Review network stability
- Check cooldown settings

**High memory usage:**
- Adjust buffer size in config
- Reduce flush interval
- Limit concurrent streams

## 📚 Related Documentation

- [OANDA v20 API Docs](https://developer.oanda.com/rest-live-v20/introduction/)
- [Central Hub Contracts](../../01-core-infrastructure/central-hub/docs/CONTRACTS_GUIDE.md)
- [Data Bridge Integration](../../02-data-processing/data-bridge/README.md)
- [Service Architecture](../docs/ARCHITECTURE.md)

## 📄 License

Part of Suho AI Trading Platform - Internal Use Only
