# System Architecture - Suho AI Trading Platform

## Core Infrastructure Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Central Hub   │◄──►│ Component Manager│◄──►│  API Gateway    │
│   (Config +     │    │   (Hot Reload)   │    │  (Main Entry)   │
│   Components)   │    └──────────────────┘    └─────────────────┘
└─────────────────┘              │                       │
        │                        ▼                       ▼
        ▼                  ┌──────────┐            ┌──────────┐
┌─────────────────┐        │   NATS   │            │   HTTP   │
│   PostgreSQL    │        │ Message  │            │ Clients  │
│   DragonflyDB   │        │  Queue   │            │   MT5    │
│   ClickHouse    │        └──────────┘            │ WebSocket│
└─────────────────┘                                └──────────┘
```

## Centralized Configuration System

### 🎯 Configuration Strategy: Hybrid Approach

**STATIC Configuration (Environment Variables)**
- Database connections (PostgreSQL, ClickHouse, DragonflyDB)
- Message queue URLs (NATS, Kafka)
- Security credentials and API keys
- Infrastructure endpoints

**HOT RELOAD Configuration (Central Hub)**
- Business rules and logic parameters
- Feature toggles and A/B testing flags
- Rate limiting and timeout settings
- Trading algorithm parameters

### 📁 Centralized Config Structure

```
central-hub/config/
├── config_api_gateway.py          # API Gateway business config
├── config_component_manager.py    # Component Manager settings
├── config_trading_engine.py       # Trading engine parameters
├── config_data_processor.py       # Data processing rules
├── config_market_analyzer.py      # Market analysis settings
├── config_risk_manager.py         # Risk management rules
└── templates/
    ├── service_config_template.py # Base template
    └── README.md                  # Configuration guidelines
```

### 🔄 Configuration Loading Pattern

```python
# Static Config (Loaded at startup)
STATIC_CONFIG = {
    "database": {
        "postgresql_url": os.getenv("DATABASE_URL"),
        "clickhouse_url": os.getenv("CLICKHOUSE_URL"),
        "dragonflydb_url": os.getenv("CACHE_URL")
    },
    "messaging": {
        "nats_url": os.getenv("NATS_URL"),
        "kafka_brokers": os.getenv("KAFKA_BROKERS")
    }
}

# Hot Reload Config (From Central Hub)
DYNAMIC_CONFIG = await central_hub.get_config("api_gateway")
```

### 📋 Service Configuration Templates

Each service will have `config_servicename.py` in Central Hub:

#### Template Structure:
```python
# config_api_gateway.py example
{
    "service_info": {
        "name": "api-gateway",
        "version": "2.0.0",
        "description": "Main API Gateway with hot reload support"
    },

    # HOT RELOAD: Business Logic
    "business_rules": {
        "rate_limiting": {
            "requests_per_minute": 1000,
            "burst_limit": 100
        },
        "timeouts": {
            "request_timeout_ms": 30000,
            "connection_timeout_ms": 5000
        },
        "retry_policy": {
            "max_attempts": 3,
            "backoff_multiplier": 2
        }
    },

    # HOT RELOAD: Feature Flags
    "features": {
        "enable_new_routing_algorithm": True,
        "enable_request_logging": False,
        "enable_performance_metrics": True,
        "debug_mode": False
    },

    # HOT RELOAD: Trading Parameters
    "trading": {
        "max_concurrent_orders": 100,
        "position_size_limits": {
            "forex": 1000000,
            "crypto": 50000
        }
    },

    # STATIC: Infrastructure (Reference only)
    "static_references": {
        "database_url": "ENV:DATABASE_URL",
        "nats_url": "ENV:NATS_URL",
        "kafka_brokers": "ENV:KAFKA_BROKERS"
    }
}
```

## Hot Reload Architecture

### 🔥 Component Hot Reload Flow

1. **Developer** edits file in `central-hub/shared/` or `central-hub/config/`
2. **Component Manager** detects change via file watcher (chokidar)
3. **Component Manager** publishes update to NATS topic:
   - `suho.components.update.{component.path}` for components
   - `suho.config.update.{service.name}` for configurations
4. **Services** subscribe to relevant NATS topics
5. **Services** auto-reload modules/config without restart

### 📡 NATS Topics Structure

```
suho.components.update.*        # Component updates
├── suho.components.update.js.utils.Logger
├── suho.components.update.js.transport.TransferManager
└── suho.components.update.shared.index

suho.config.update.*            # Configuration updates
├── suho.config.update.api-gateway
├── suho.config.update.trading-engine
└── suho.config.update.market-analyzer
```

### 🔐 Security Considerations

- **Database credentials**: Never in hot reload, static only
- **API keys**: Environment variables, not in Central Hub config
- **Secrets management**: Use Docker secrets or external vault
- **Config validation**: Validate all hot reload configs before apply
- **Rollback mechanism**: Keep previous config version for quick rollback

## Service Integration Pattern

### 📦 Hot Reload Client Integration

Each service implements:

```javascript
// 1. ComponentSubscriber for shared components
const componentSubscriber = new ComponentSubscriber({
    service_name: 'api-gateway',
    nats_client: natsClient,
    topics: ['suho.components.update.*']
});

// 2. ConfigSubscriber for service-specific config
const configSubscriber = new ConfigSubscriber({
    service_name: 'api-gateway',
    nats_client: natsClient,
    topics: ['suho.config.update.api-gateway']
});

// 3. Event handlers
configSubscriber.on('config_updated', (newConfig) => {
    // Update business rules without restart
    rateLimiter.updateLimits(newConfig.business_rules.rate_limiting);
    featureFlags.update(newConfig.features);
});
```

### 🚀 Benefits

1. **Zero Downtime Updates**: Change business logic without service restarts
2. **Consistent Configuration**: Single source of truth in Central Hub
3. **A/B Testing**: Toggle features across services in real-time
4. **Emergency Response**: Quick parameter adjustments during incidents
5. **Development Velocity**: Faster iteration on business rules

### ⚡ Performance Characteristics

- **Config Update Latency**: < 100ms via NATS
- **Component Reload Time**: < 50ms for typical modules
- **Memory Overhead**: ~2MB per service for hot reload infrastructure
- **Network Traffic**: Minimal, only changed configs broadcast

---

## Next Steps

1. ✅ Create centralized config folder structure
2. ✅ Implement service config templates
3. ✅ Update services to consume centralized config
4. ✅ Add config validation and rollback mechanisms
5. ✅ Implement config update NATS topics