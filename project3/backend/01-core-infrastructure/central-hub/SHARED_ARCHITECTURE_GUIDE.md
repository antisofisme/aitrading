# Central Hub Shared Architecture Guide

**Date**: September 30, 2025
**Version**: 3.0.0 (Refactored)
**Audience**: Developers, DevOps, System Architects

## 🎯 **OVERVIEW: UNIFIED SHARED RESOURCES**

Central Hub manages **all shared resources** for the Suho Trading System with clear separation:
- **`base/`** - Central Hub's own service code (FastAPI application)
- **`shared/`** - Resources distributed to other services (components, configs)

**Component Manager functionality is now handled directly by Central Hub itself** - no separate service needed.

## 📁 **SHARED DIRECTORY STRUCTURE**

```
central-hub/shared/
├── components/          # 🔧 CODE COMPONENTS (Hot-reload distributed)
│   ├── js/             # JavaScript shared utilities
│   │   ├── utils/      # BaseService, ComponentSubscriber, Logger
│   │   ├── adapters/   # NATSKafkaAdapter, TransportAdapter
│   │   ├── transport/  # TransferManager, MessageRouter
│   │   └── logging/    # Structured logging utilities
│   ├── proto/          # Protocol Buffer definitions
│   ├── suho-binary/    # Suho Binary Protocol implementations
│   └── utils/          # Cross-language utilities (Python, Go, etc.)
│
├── static/             # ⚙️ STATIC CONFIGURATION (Startup distributed)
│   ├── database/       # Database connection configurations
│   │   ├── postgresql.json
│   │   ├── clickhouse.json
│   │   └── dragonflydb.json
│   ├── security/       # Security configurations
│   │   ├── jwt.json
│   │   ├── api-keys.json
│   │   └── encryption.json
│   └── services/       # Service-specific static configurations
│       ├── api-gateway/
│       │   ├── server.json
│       │   ├── cors.json
│       │   └── middleware.json
│       ├── trading-engine/
│       └── analytics/
│
└── hot-reload/         # 🔄 DYNAMIC CONFIGURATION (Runtime distributed)
    ├── business/       # Business rule configurations
    │   ├── rate-limits.json
    │   ├── trading-rules.json
    │   └── validation-rules.json
    ├── features/       # Feature flag configurations
    │   ├── api-features.json
    │   ├── ui-features.json
    │   └── experimental.json
    └── routing/        # Dynamic routing configurations
        ├── api-routing.json
        ├── load-balancing.json
        └── circuit-breakers.json
```

## 🔄 **DISTRIBUTION MECHANISMS**

### **1️⃣ Components Distribution (Hot-Reload)**

**Purpose**: Share reusable code components across services
**Mechanism**: ComponentSubscriber + NATS + Hot-reload
**Frequency**: Real-time updates when components change

```javascript
// API Gateway uses ComponentSubscriber
const ComponentSubscriber = require('../central-hub/shared/components/js/utils/ComponentSubscriber');

// Hot-reload flow:
// 1. Central Hub updates component
// 2. NATS broadcast to all services
// 3. ComponentSubscriber downloads new version
// 4. Service hot-reloads new component
```

**Files Distributed**:
- JavaScript utilities (`BaseService`, `Logger`, `NATSKafkaAdapter`)
- Protocol definitions (`.proto` files)
- Binary protocol implementations
- Cross-language utilities

### **2️⃣ Static Configuration Distribution (Startup)**

**Purpose**: Provide secure, environment-specific configurations
**Mechanism**: HTTP API + ConfigService
**Frequency**: At service startup and restart

```javascript
// API Gateway ConfigService
const config = await configService.getConfig();
// Fetches from: http://central-hub:7000/config

// Flow:
// 1. Service starts up
// 2. ConfigService.getConfig() calls Central Hub
// 3. Central Hub returns static config for service
// 4. Service caches config locally
```

**Configuration Types**:
- **Database connections**: URLs, credentials, pool settings
- **Security settings**: JWT secrets, API keys, certificates
- **Service configuration**: Port numbers, timeouts, limits
- **Infrastructure**: Message broker URLs, cache settings

### **3️⃣ Hot-Reload Configuration Distribution (Runtime)**

**Purpose**: Update business logic without service restart
**Mechanism**: NATS + Configuration Subscriber
**Frequency**: Real-time when business rules change

```javascript
// Services subscribe to config updates
natsClient.subscribe('config.business.rate-limits', (msg) => {
    const newRateLimits = JSON.parse(msg.data);
    updateRateLimiting(newRateLimits);
});

// Flow:
// 1. Admin updates business rule in Central Hub
// 2. Central Hub validates change
// 3. NATS broadcast to all affected services
// 4. Services apply new rules immediately
```

**Configuration Types**:
- **Business rules**: Rate limits, validation rules, trading parameters
- **Feature flags**: Enable/disable features dynamically
- **Routing rules**: Load balancing, circuit breakers, failover

## 🎯 **CLEAR BOUNDARIES**

### **`components/` vs `static/` vs `hot-reload/`**

| Aspect | **components/** | **static/** | **hot-reload/** |
|--------|----------------|-------------|-----------------|
| **Content** | Code libraries | Environment config | Business rules |
| **Distribution** | Hot-reload | HTTP API | NATS broadcast |
| **Update Frequency** | When code changes | At startup | Runtime changes |
| **Requires Restart** | No | Yes | No |
| **Security Level** | Medium | High | Medium |
| **Examples** | BaseService.js | DB credentials | Rate limits |

### **When to Use Which?**

#### **Use `components/`** when:
- ✅ Sharing JavaScript utilities, classes, or functions
- ✅ Distributing protocol definitions (protobuf)
- ✅ Providing cross-language utilities
- ✅ Code that multiple services need to import

#### **Use `static/`** when:
- ✅ Database connection strings and credentials
- ✅ Service configuration (ports, timeouts)
- ✅ Security settings (JWT secrets, API keys)
- ✅ Infrastructure configuration (message brokers)

#### **Use `hot-reload/`** when:
- ✅ Business rules that change frequently
- ✅ Feature flags for A/B testing
- ✅ Dynamic routing and load balancing rules
- ✅ Configuration that needs real-time updates

## 🔧 **DEVELOPER WORKFLOWS**

### **Adding New Shared Component**

1. **Create component**: Add to `shared/components/js/utils/NewUtility.js`
2. **Update version**: Increment version in `component_versions.json`
3. **Test locally**: Verify component works in isolation
4. **Deploy**: Central Hub will auto-distribute to services
5. **Import in services**: Services can now `require()` the new component

### **Adding Static Configuration**

1. **Create config file**: Add to `shared/static/services/my-service/config.json`
2. **Define schema**: Add validation schema in `contracts/`
3. **Update Central Hub**: Register new config endpoint
4. **Update service**: Use ConfigService to fetch config at startup

### **Adding Hot-Reload Configuration**

1. **Create config file**: Add to `shared/hot-reload/business/new-rule.json`
2. **Define NATS topic**: Register topic in Central Hub
3. **Update services**: Subscribe to new configuration topic
4. **Test updates**: Verify live updates work without restart

## 📊 **MONITORING & DEBUGGING**

### **Component Distribution Status**
```bash
# Check component versions across services
curl http://central-hub:7000/components/versions

# Check which services have which component versions
curl http://central-hub:7000/components/distribution-status
```

### **Configuration Distribution Status**
```bash
# Check static config distribution
curl http://central-hub:7000/config/static/status

# Check hot-reload config distribution
curl http://central-hub:7000/config/hot-reload/status
```

### **Service Health with Shared Resources**
```bash
# Check service health including shared resource status
curl http://api-gateway:8000/health/shared-resources
```

## 🚨 **TROUBLESHOOTING**

### **Component Not Updating**
1. Check NATS connectivity: `docker logs suho-nats-server`
2. Verify ComponentSubscriber: Check service logs for download errors
3. Check component cache: Services cache components locally
4. Verify version: `component_versions.json` should be updated

### **Static Config Not Loading**
1. Check Central Hub health: `curl http://central-hub:7000/health`
2. Verify config file exists: Check `shared/static/` structure
3. Check ConfigService logs: API Gateway should log config fetch attempts
4. Verify network connectivity: Services must reach Central Hub

### **Hot-Reload Not Working**
1. Check NATS subscription: Services should log topic subscriptions
2. Verify NATS topic: Check Central Hub publishes to correct topic
3. Check config validation: Invalid config may be rejected
4. Verify service handling: Services must implement update handlers

## 🎯 **BEST PRACTICES**

### **File Organization**
- Use **clear, descriptive filenames**: `rate-limits.json`, not `config1.json`
- Group related configs in **subfolders**: `database/`, `security/`
- Maintain **consistent naming**: kebab-case for files, camelCase for JSON keys

### **Version Management**
- **Always update versions** when changing components
- Use **semantic versioning**: `1.2.3` format
- **Document breaking changes** in component README files

### **Security**
- **Never commit secrets** to static config files
- Use **environment variable substitution** for sensitive values
- **Validate all configuration** before distribution

### **Performance**
- **Cache static configs** locally in services
- **Batch hot-reload updates** to avoid spam
- **Monitor distribution lag** between Central Hub and services

---

This unified architecture provides **clear separation of concerns** while **simplifying the mental model** for developers working with shared resources.