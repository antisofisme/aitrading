# Shared Architecture Guide - Central Hub

## 📁 Shared Folder Structure

```
shared/
├── static/                     # 🔒 Infrastructure Configurations (Stable)
│   ├── database/               #    Database connection configs
│   │   ├── postgresql.json     #      PostgreSQL connection settings
│   │   ├── clickhouse.json     #      ClickHouse analytics database
│   │   ├── dragonflydb.json    #      DragonflyDB cache settings
│   │   ├── arangodb.json       #      ArangoDB graph database
│   │   └── weaviate.json       #      Weaviate vector database
│   └── messaging/              #    Message broker configurations
│       ├── nats.json           #      NATS streaming settings
│       ├── kafka.json          #      Kafka event streaming
│       └── zookeeper.json      #      Zookeeper coordination
│
├── hot-reload/                 # 🔥 Business Configurations (Dynamic)
│   ├── api_gateway.py          #    API Gateway business rules & features
│   └── service_config_template.py #  Service configuration templates
│
└── components/                 # 🔧 Shared Utility Components
    ├── utils/                  #    Common utilities
    │   ├── base_service.py     #      Base service class
    │   ├── patterns/           #      Design patterns
    │   └── log_utils/          #      Logging utilities
    └── cache/                  #    Component cache
```

## 🔒 Static Configurations (`shared/static/`)

### Purpose
- **Infrastructure connection details** yang jarang berubah
- **Database credentials** dan connection pooling settings
- **Message broker** endpoint dan authentication
- **Network configuration** untuk container-to-container communication

### Characteristics
- **Requires service restart** untuk apply changes
- **Environment-specific** (development, staging, production)
- **Security-sensitive** information
- **High stability** requirements

### Configuration Files

#### Database Configurations
```json
// postgresql.json
{
  "host": "suho-postgresql",
  "port": 5432,
  "database": "suho_trading",
  "user": "suho_admin",
  "pool_size": 10,
  "max_overflow": 20,
  "pool_timeout": 30,
  "pool_recycle": 3600,
  "ssl_mode": "prefer"
}

// clickhouse.json
{
  "host": "suho-clickhouse",
  "port": 8123,
  "database": "suho_analytics",
  "user": "suho_analytics",
  "protocol": "http",
  "compression": true
}

// dragonflydb.json
{
  "host": "suho-dragonflydb",
  "port": 6379,
  "max_connections": 20,
  "retry_on_timeout": true,
  "health_check_interval": 30
}
```

#### Messaging Configurations
```json
// nats.json
{
  "servers": ["nats://suho-nats-server:4222"],
  "cluster_id": "suho-cluster",
  "subjects": {
    "service_discovery": "suho.services.discovery",
    "health_reports": "suho.health.reports",
    "config_updates": "suho.config.updates"
  }
}

// kafka.json
{
  "brokers": ["suho-kafka:9092"],
  "topics": {
    "market_data": "suho.market.data",
    "trade_events": "suho.trade.events",
    "system_events": "suho.system.events"
  }
}
```

## 🔥 Hot-reload Configurations (`shared/hot-reload/`)

### Purpose
- **Business logic** dan rules yang frequently updated
- **Feature flags** untuk A/B testing
- **Performance tuning** parameters
- **Runtime behavior** modifications

### Characteristics
- **Zero-downtime updates** via hot-reload
- **Business-focused** configurations
- **Rapid iteration** support
- **Real-time effectiveness**

### Service Configurations

#### API Gateway Configuration (`api_gateway.py`)
```python
CONFIG_API_GATEWAY = {
    "business_rules": {
        "rate_limiting": {
            "requests_per_minute": 1000,
            "burst_limit": 100,
            "enabled": True
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

    "features": {
        "enable_debug_logging": False,
        "enable_performance_metrics": True,
        "enable_circuit_breaker": True,
        "maintenance_mode": False
    },

    "trading": {
        "max_concurrent_orders": 100,
        "position_size_limits": {
            "forex": 1000000,
            "crypto": 50000
        }
    }
}
```

#### Service Config Template (`service_config_template.py`)
```python
def create_service_config(service_name, service_type, **overrides):
    """Generate standardized service configuration"""

    base_config = {
        "service_info": {
            "name": service_name,
            "type": service_type,
            "version": "1.0.0",
            "environment": "development"
        },

        "performance": {
            "thread_pool_size": 10,
            "connection_pool_size": 20,
            "cache_ttl_seconds": 300
        },

        "monitoring": {
            "metrics_enabled": True,
            "health_check_interval": 30,
            "alert_thresholds": {
                "error_rate_percent": 5.0,
                "response_time_p95_ms": 1000
            }
        }
    }

    # Apply service-specific overrides
    return merge_configs(base_config, overrides)
```

## 🔧 Shared Components (`shared/components/`)

### Component Categories

#### Base Services (`utils/base_service.py`)
```python
class BaseService:
    """Standard base class for all services"""

    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = setup_logging(config.service_name)
        self.metrics = MetricsCollector(config.service_name)

    async def start(self):
        """Standard service startup"""
        await self.initialize_database()
        await self.initialize_cache()
        await self.register_with_central_hub()

    async def health_check(self):
        """Standard health check implementation"""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": self.config.version
        }
```

#### Design Patterns (`utils/patterns/`)
- **Database Manager**: Standardized database connection handling
- **Cache Manager**: Redis/DragonflyDB caching patterns
- **Circuit Breaker**: Fault tolerance patterns
- **Message Bus**: Event-driven communication patterns

#### Logging Utilities (`utils/log_utils/`)
- **ErrorDNA**: Advanced error tracking and analysis
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Performance Metrics**: Request timing and resource usage
- **Audit Trails**: Security and compliance logging

## 🔄 Configuration Flow

### Static Configuration Loading
```
1. Container Start → Read static/*.json files
2. Parse environment variables → Merge with static configs
3. Validate configurations → Fail fast on errors
4. Initialize connections → Database, cache, messaging
5. Service ready → Accept requests
```

### Hot-reload Configuration Updates
```
1. Configuration change → Update hot-reload/*.py files
2. File watcher detects → Trigger reload process
3. Validate new config → Check for syntax/logic errors
4. Apply atomically → Zero-downtime config swap
5. Notify services → Broadcast configuration updates
```

### Configuration Precedence
```
Environment Variables > Hot-reload Configs > Static Configs > Defaults
```

## 🛡️ Security & Validation

### Static Configuration Security
- **Environment variables** untuk sensitive data
- **File permissions** restricted to service user
- **Encryption at rest** untuk production credentials
- **Secret rotation** support via environment updates

### Hot-reload Configuration Validation
- **Schema validation** before applying changes
- **Business rule validation** untuk consistency
- **Permission checks** untuk configuration updates
- **Rollback capability** pada validation failures

### Access Control
```python
# Configuration access patterns
@require_permission("config:read")
def get_service_config(service_name: str):
    """Read service configuration"""

@require_permission("config:write")
def update_service_config(service_name: str, config: dict):
    """Update service configuration"""

@require_permission("config:admin")
def reload_all_configurations():
    """Reload all service configurations"""
```

## 📊 Monitoring & Observability

### Configuration Metrics
- **Reload frequency** per service
- **Validation errors** count dan details
- **Configuration drift** detection
- **Performance impact** of config changes

### Health Monitoring
```python
async def configuration_health_check():
    """Monitor configuration system health"""
    return {
        "static_configs_loaded": True,
        "hot_reload_active": True,
        "last_reload_time": "2024-01-15T10:30:00Z",
        "validation_errors": 0,
        "active_services": 5
    }
```

### Audit Logging
- **Configuration changes** dengan user attribution
- **Access patterns** untuk security monitoring
- **Error tracking** untuk debugging
- **Performance metrics** untuk optimization

## 🚀 Best Practices

### Configuration Design
1. **Separate concerns**: Infrastructure vs business logic
2. **Environment parity**: Consistent across environments
3. **Validation first**: Fail fast on invalid configurations
4. **Documentation**: Self-documenting configuration schemas

### Hot-reload Patterns
1. **Atomic updates**: All-or-nothing configuration changes
2. **Gradual rollout**: Feature flags untuk controlled releases
3. **Monitoring**: Track impact of configuration changes
4. **Rollback ready**: Quick revert mechanisms

### Security Guidelines
1. **Least privilege**: Minimal permissions untuk configuration access
2. **Audit trails**: Log all configuration changes
3. **Encryption**: Protect sensitive configuration data
4. **Validation**: Prevent malicious configuration injection

## 🎯 Usage Examples

### Reading Static Configuration
```python
from shared.components.config_loader import load_static_config

# Load database configuration
db_config = load_static_config("database", "postgresql")
connection_url = f"postgresql://{db_config['user']}@{db_config['host']}/{db_config['database']}"
```

### Using Hot-reload Configuration
```python
from shared.hot_reload.api_gateway import CONFIG_API_GATEWAY

# Access business rules
rate_limit = CONFIG_API_GATEWAY["business_rules"]["rate_limiting"]["requests_per_minute"]
timeout = CONFIG_API_GATEWAY["business_rules"]["timeouts"]["request_timeout_ms"]
```

### Creating Service Configuration
```python
from shared.hot_reload.service_config_template import create_service_config

# Generate trading engine configuration
trading_config = create_service_config(
    "trading-engine",
    "trading",
    performance={"thread_pool_size": 20},
    trading={"max_orders_per_second": 1000}
)
```

---

**🔄 Shared Architecture: Fundasi Konfigurasi yang Scalable dan Maintainable**