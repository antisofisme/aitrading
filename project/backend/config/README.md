# Forex & Gold Trading Platform Configuration Guide

## Overview

This configuration guide covers the updated Docker Compose setup for the Forex & Gold trading platform with Indonesian market focus, Midtrans payment integration, and high-frequency trading optimization.

## Key Changes from Previous Configuration

### 1. Trading Focus Shift
- **Previous**: General AI trading platform
- **Current**: Specialized Forex & Gold trading for Indonesian market
- **Impact**: All services now optimized for currency and precious metals trading

### 2. Payment Integration
- **Added**: Midtrans payment gateway integration
- **Features**: Indonesian e-wallets (GoPay, OVO, DANA, ShopeePay) and bank transfers
- **Configuration**: Sandbox for development, production keys for live deployment

### 3. Performance Optimization
- **High-Frequency Trading**: Optimized container resources and tick processing
- **Container Resources**: Increased memory and CPU allocation for trading engines
- **Rate Limiting**: Adjusted for high-frequency operations (1000+ requests/minute)

### 4. Indonesian Localization
- **Timezone**: Asia/Jakarta
- **Currency**: IDR (Indonesian Rupiah)
- **Locale**: id_ID
- **Trading Hours**: 07:00-17:00 WIB

## Service Architecture

### Core Services

| Service | Port | Purpose | Resources |
|---------|------|---------|-----------|
| api-gateway | 8000/8001 | Main entry point | 2GB RAM, 2 CPU |
| central-hub | 8002/8003 | Business logic | 2GB RAM, 2 CPU |
| database-service | 8006/8007 | Data management | 1GB RAM, 1 CPU |
| data-bridge | 8001/8002 | MT5 integration | 1GB RAM, 1 CPU |

### Trading Engines (New)

| Service | Port | Purpose | Resources |
|---------|------|---------|-----------|
| forex-engine | 8026 | Forex trading | 2GB RAM, 2 CPU |
| gold-engine | 8027 | Gold trading | 2GB RAM, 2 CPU |
| risk-management | 8028 | Risk control | 1GB RAM, 1 CPU |

### Business Services

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| user-management | 8021 | User accounts | PostgreSQL |
| subscription-service | 8022 | Subscriptions | PostgreSQL |
| payment-gateway | 8023 | Midtrans integration | PostgreSQL |
| notification-service | 8024 | Alerts & notifications | PostgreSQL |
| billing-service | 8025 | Invoicing | PostgreSQL |

### Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache & sessions |
| MongoDB | 27017 | Logs & documents |
| Consul | 8500 | Service discovery |

### Monitoring

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| Elasticsearch | 9200 | Log storage |
| Kibana | 5601 | Log analysis |

## Environment Files

### Production (.env.production)
- Real Midtrans keys
- Production database credentials
- Optimized trading parameters
- 50ms tick processing interval
- 2000 max concurrent trades

### Staging (.env.staging)
- Midtrans sandbox
- Staging database
- Production-like settings
- 100ms tick processing interval
- 1000 max concurrent trades

### Development (.env.development)
- Midtrans sandbox
- Local database credentials
- Debug logging
- 500ms tick processing interval
- 100 max concurrent trades

## High-Frequency Trading Configuration

### Performance Optimizations
```yaml
# Forex Engine
TICK_PROCESSING_INTERVAL=50  # 50ms for production
MAX_CONCURRENT_TRADES=2000
HIGH_FREQUENCY_MODE=true

# Resource Allocation
memory: 2G
cpus: '2.0'

# Rate Limiting
RATE_LIMIT_WINDOW=60000
RATE_LIMIT_MAX=5000
```

### Database Optimization
```yaml
# Multiple databases for performance
POSTGRES_MULTIPLE_DATABASES=forex,gold,analytics,payments,logs

# Specialized databases
forex_db: Currency pair data
gold_db: Precious metals data
analytics_db: Trading analytics
payments_db: Midtrans transactions
logs_db: Application logs
```

## Midtrans Payment Integration

### Supported Payment Methods
- **Bank Transfer**: All major Indonesian banks
- **E-Wallets**: GoPay, OVO, DANA, ShopeePay
- **Credit Cards**: Visa, MasterCard, JCB
- **Installments**: Credit card installments

### Configuration
```yaml
# Production
MIDTRANS_IS_PRODUCTION=true
MIDTRANS_SERVER_KEY=your-production-server-key
MIDTRANS_CLIENT_KEY=your-production-client-key

# Sandbox (Development/Staging)
MIDTRANS_IS_PRODUCTION=false
MIDTRANS_SERVER_KEY=SB-Mid-server-sandbox-key
MIDTRANS_CLIENT_KEY=SB-Mid-client-sandbox-key
```

## Indonesian Localization

### Core Settings
```yaml
TZ=Asia/Jakarta
CURRENCY=IDR
LOCALE=id_ID
TAX_RATE=11  # Indonesian VAT rate
```

### Trading Hours
```yaml
TRADING_HOURS_START=07:00  # 7:00 AM WIB
TRADING_HOURS_END=17:00    # 5:00 PM WIB
```

### Language Support
- Indonesian (Bahasa Indonesia) as primary language
- English as secondary language
- Currency formatting for IDR
- Date/time formatting for Indonesian locale

## Security Enhancements

### JWT Configuration
```yaml
JWT_SECRET=your-super-secure-jwt-secret-key-minimum-32-characters
SERVICE_SECRET=service-communication-secret
```

### Database Security
```yaml
# Strong passwords for production
POSTGRES_PASSWORD=your-super-secure-production-password
MONGO_PASSWORD=your-super-secure-mongo-password
REDIS_PASSWORD=your-super-secure-redis-password
```

## Development Setup

### Quick Start
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up -d

# Production environment
docker-compose up -d

# View logs
docker-compose logs -f forex-engine
```

### Development Tools
- **MailHog**: Email testing (port 8025)
- **Redis Commander**: Redis GUI (port 8081)
- **MongoDB Express**: MongoDB GUI (port 8082)
- **Debug Ports**: Node.js debugging enabled

### Hot Reload
All development services support hot reload with volume mounts:
```yaml
volumes:
  - ./forex-engine:/app
  - /app/node_modules
```

## Risk Management

### Default Risk Parameters
```yaml
MAX_RISK_EXPOSURE=0.05      # 5% max exposure
STOP_LOSS_THRESHOLD=0.02    # 2% stop loss
MARGIN_CALL_LEVEL=0.3       # 30% margin call
```

### Risk Controls
- Real-time position monitoring
- Automated stop-loss execution
- Margin requirement validation
- Exposure limit enforcement

## MT5 Integration

### Trading Symbols
```yaml
# Forex pairs
FOREX_SYMBOLS=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD,NZDUSD,USDCHF

# Precious metals
GOLD_SYMBOLS=XAUUSD,XAGUSD
```

### Connection Settings
```yaml
MT5_HOST=your-mt5-server.com
MT5_PORT=443
MT5_LOGIN=your-mt5-login
MT5_PASSWORD=your-mt5-password
MT5_SERVER=your-mt5-server-name
```

## Monitoring & Alerting

### Health Checks
All services include comprehensive health checks with:
- 10-30 second intervals
- 3-5 retry attempts
- Startup grace periods
- Dependency validation

### Alert Channels
- **Telegram**: Real-time trade alerts
- **Email**: System notifications
- **SMS**: Critical alerts via Twilio
- **Dashboard**: Grafana monitoring

## Deployment Instructions

### Environment Setup
1. Copy appropriate `.env` file for your environment
2. Update sensitive values (passwords, API keys)
3. Configure Midtrans credentials
4. Set up MT5 connection parameters

### Production Deployment
```bash
# Set environment
export NODE_ENV=production

# Load production environment
cp config/env/.env.production .env

# Deploy services
docker-compose up -d

# Verify deployment
docker-compose ps
```

### Health Verification
```bash
# Check all services
curl http://localhost:8001/health  # API Gateway
curl http://localhost:8026/health  # Forex Engine
curl http://localhost:8027/health  # Gold Engine
curl http://localhost:8028/health  # Risk Management
```

## Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 8000-8028 are available
2. **Memory Issues**: Increase Docker memory allocation for trading engines
3. **Database Connections**: Verify PostgreSQL multiple database setup
4. **Midtrans Integration**: Check sandbox vs production key configuration

### Log Analysis
```bash
# View trading engine logs
docker-compose logs -f forex-engine gold-engine

# Monitor risk management
docker-compose logs -f risk-management

# Check payment processing
docker-compose logs -f payment-gateway
```

## Performance Tuning

### Container Resources
- **Trading Engines**: 2GB RAM, 2 CPU cores
- **API Gateway**: 2GB RAM, 2 CPU cores
- **Database Services**: 1GB RAM, 1 CPU core
- **Monitoring**: Standard allocation

### Database Optimization
- Connection pooling enabled
- Query optimization for high-frequency operations
- Separate databases for different data types
- Redis caching for frequently accessed data

## Support & Maintenance

### Regular Tasks
- Monitor trading engine performance
- Update Midtrans configuration as needed
- Review and adjust risk parameters
- Backup database configurations
- Update security credentials

### Scaling Considerations
- Horizontal scaling for trading engines
- Database partitioning for high volume
- Load balancing for API gateway
- Redis clustering for cache scaling