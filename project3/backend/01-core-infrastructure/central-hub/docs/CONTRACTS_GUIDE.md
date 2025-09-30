# Contracts Architecture Guide - Central Hub

## 📝 Contract System Overview

The **contracts/** folder defines standardized communication interfaces between Central Hub and all services in the Suho AI Trading Platform. This enables loose coupling, type safety, and protocol-agnostic communication.

## 🏗️ Contract Architecture

```
contracts/
├── http-rest/                          # 🌐 REST API Contracts
│   ├── service-registration-to-central-hub.js      # Service → Central Hub
│   ├── service-discovery-to-central-hub.js         # Service → Central Hub
│   ├── service-discovery-response-from-central-hub.js # Central Hub → Service
│   └── configuration-request-to-central-hub.js     # Service → Central Hub
│
├── grpc/                               # ⚡ gRPC Stream Contracts
│   ├── configuration-update-from-central-hub.js    # Central Hub → Service
│   └── health-report-to-central-hub.js             # Service → Central Hub
│
├── nats-kafka/                         # 📨 Message Broker Contracts
│   ├── health-stream-to-central-hub.js             # Service → Central Hub
│   └── scaling-command-from-central-hub.js         # Central Hub → Service
│
└── internal/                           # 🔒 Internal Service Contracts
    └── (Internal service-to-service contracts)
```

## 🌐 HTTP REST Contracts

### Service Registration Contract
**File**: `http-rest/service-registration-to-central-hub.js`

```javascript
const ServiceRegistrationSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required().min(2).max(50),
    host: Joi.string().required(),
    port: Joi.number().integer().min(1).max(65535).required(),
    protocol: Joi.string().valid('http', 'https', 'grpc', 'tcp', 'udp').default('http'),

    // Service metadata
    version: Joi.string().default('1.0.0'),
    environment: Joi.string().valid('development', 'staging', 'production'),
    health_endpoint: Joi.string().default('/health'),

    // Service capabilities
    metadata: Joi.object({
        type: Joi.string().valid('api-gateway', 'trading-engine', 'data-bridge').required(),
        capabilities: Joi.array().items(Joi.string()).default([]),
        max_connections: Joi.number().integer().min(1).default(1000)
    }).required()
});
```

**Usage Example**:
```bash
POST /discovery/register
{
  "service_name": "api-gateway",
  "host": "suho-api-gateway",
  "port": 8000,
  "protocol": "http",
  "metadata": {
    "type": "api-gateway",
    "capabilities": ["http", "websocket", "trading"],
    "max_connections": 1000
  }
}
```

### Service Discovery Contract
**File**: `http-rest/service-discovery-to-central-hub.js`

```javascript
const ServiceDiscoverySchema = Joi.object({
    // Query parameters
    service_name: Joi.string().optional(),
    service_type: Joi.string().optional(),
    capabilities: Joi.array().items(Joi.string()).optional(),

    // Filtering options
    environment: Joi.string().valid('development', 'staging', 'production').optional(),
    status: Joi.string().valid('active', 'inactive', 'maintenance').default('active'),

    // Response preferences
    include_metadata: Joi.boolean().default(true),
    include_health_status: Joi.boolean().default(false)
});
```

**Usage Example**:
```bash
GET /discovery/services?service_type=trading-engine&capabilities=real-time

Response:
{
  "services": [
    {
      "service_name": "trading-engine-1",
      "url": "http://trading-engine-1:8080",
      "status": "active",
      "capabilities": ["real-time", "backtesting"],
      "last_seen": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Configuration Request Contract
**File**: `http-rest/configuration-request-to-central-hub.js`

```javascript
const ConfigurationRequestSchema = Joi.object({
    service_name: Joi.string().required(),
    config_version: Joi.string().optional(),
    sections: Joi.array().items(Joi.string()).optional(), // ['business_rules', 'features']
    format: Joi.string().valid('json', 'yaml', 'env').default('json')
});
```

## ⚡ gRPC Stream Contracts

### Configuration Update Stream
**File**: `grpc/configuration-update-from-central-hub.js`

```javascript
const ConfigurationUpdateSchema = Joi.object({
    // Update metadata
    update_id: Joi.string().required(),
    service_name: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Configuration changes
    config_section: Joi.string().required(), // 'business_rules', 'features', etc.
    config_data: Joi.object().required(),

    // Update options
    update_type: Joi.string().valid('partial', 'full', 'merge').default('partial'),
    requires_restart: Joi.boolean().default(false),
    priority: Joi.string().valid('low', 'medium', 'high', 'critical').default('medium')
});
```

**Usage Pattern**:
```javascript
// Central Hub pushes config updates via gRPC stream
stream.write({
  update_id: "cfg-001",
  service_name: "api-gateway",
  config_section: "business_rules",
  config_data: {
    rate_limiting: { requests_per_minute: 2000 }
  },
  update_type: "partial"
});
```

### Health Report Stream
**File**: `grpc/health-report-to-central-hub.js`

```javascript
const HealthReportSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required(),
    instance_id: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Health data
    status: Joi.string().valid('healthy', 'degraded', 'unhealthy').required(),
    metrics: Joi.object({
        cpu_usage_percent: Joi.number().min(0).max(100),
        memory_usage_percent: Joi.number().min(0).max(100),
        active_connections: Joi.number().integer().min(0),
        requests_per_second: Joi.number().min(0)
    }).optional(),

    // Detailed status
    checks: Joi.object().pattern(
        Joi.string(),
        Joi.object({
            status: Joi.string().valid('pass', 'fail', 'warn'),
            details: Joi.string().optional()
        })
    ).optional()
});
```

## 📨 Message Broker Contracts

### Health Stream Contract
**File**: `nats-kafka/health-stream-to-central-hub.js`

```javascript
const HealthStreamSchema = Joi.object({
    // Message routing
    subject: Joi.string().default('suho.health.reports'),
    correlation_id: Joi.string().required(),

    // Health payload
    service_name: Joi.string().required(),
    health_data: Joi.object({
        status: Joi.string().valid('healthy', 'degraded', 'unhealthy'),
        timestamp: Joi.number().integer(),
        metrics: Joi.object().optional(),
        alerts: Joi.array().items(Joi.object()).optional()
    }).required(),

    // Stream metadata
    stream_sequence: Joi.number().integer().min(1),
    retention_policy: Joi.string().valid('workqueue', 'interest', 'limits').default('limits')
});
```

### Scaling Command Contract
**File**: `nats-kafka/scaling-command-from-central-hub.js`

```javascript
const ScalingCommandSchema = Joi.object({
    // Command metadata
    command_id: Joi.string().required(),
    target_service: Joi.string().required(),
    timestamp: Joi.number().integer().required(),

    // Scaling instructions
    action: Joi.string().valid('scale_up', 'scale_down', 'restart', 'stop').required(),
    parameters: Joi.object({
        replicas: Joi.number().integer().min(0).optional(),
        cpu_limit: Joi.string().optional(),
        memory_limit: Joi.string().optional()
    }).optional(),

    // Execution options
    priority: Joi.string().valid('low', 'medium', 'high', 'emergency').default('medium'),
    timeout_seconds: Joi.number().integer().min(1).default(300),
    rollback_on_failure: Joi.boolean().default(true)
});
```

## 🔄 Contract Processing Flow

### 1. Contract Validation Pipeline
```
Incoming Request → Schema Validation → Business Rules → Security Checks → Processing
```

### 2. Multi-Transport Support
```javascript
// Contract processor supports multiple transports
const contractProcessor = new ContractProcessorIntegration();

// HTTP REST
app.post('/discovery/register', (req, res) => {
    const result = contractProcessor.process('service-registration', req.body, 'http');
    res.json(result);
});

// gRPC Stream
grpcServer.addService(ConfigurationService, {
    streamUpdates: (call) => {
        call.on('data', (data) => {
            contractProcessor.process('configuration-update', data, 'grpc');
        });
    }
});

// NATS Message
natsClient.subscribe('suho.health.reports', (msg) => {
    const data = JSON.parse(msg.data);
    contractProcessor.process('health-stream', data, 'nats');
});
```

### 3. Contract Response Generation
```javascript
function processServiceRegistration(inputData, context = {}) {
    // Validate input against contract
    const { error, value } = ServiceRegistrationSchema.validate(inputData);
    if (error) {
        throw new Error(`Validation failed: ${error.details[0].message}`);
    }

    // Process and enrich data
    const registrationData = {
        ...value,
        registered_at: Date.now(),
        registration_id: `${value.service_name}-${Date.now()}`,
        url: `${value.protocol}://${value.host}:${value.port}`
    };

    // Return standardized response
    return {
        type: 'service_registration',
        data: registrationData,
        routing_targets: ['service-registry'],
        response_format: 'service_registration_response'
    };
}
```

## 🛡️ Contract Security & Validation

### Input Validation
- **Schema validation** menggunakan Joi for type safety
- **Business rule validation** untuk logical consistency
- **Security sanitization** untuk prevent injection attacks
- **Rate limiting** per contract type

### Access Control
```javascript
// Contract-level permissions
const contractPermissions = {
    'service-registration': ['api-gateway', 'trading-engine', 'analytics'],
    'configuration-update': ['central-hub'],
    'scaling-command': ['central-hub', 'orchestrator']
};

function validateContractAccess(contractName, serviceIdentity) {
    const allowedServices = contractPermissions[contractName];
    return allowedServices.includes(serviceIdentity.service_type);
}
```

### Error Handling
```javascript
// Standardized contract error responses
const ContractError = {
    VALIDATION_FAILED: { code: 4001, message: 'Contract validation failed' },
    UNAUTHORIZED: { code: 4003, message: 'Service not authorized for this contract' },
    PROCESSING_ERROR: { code: 5001, message: 'Contract processing failed' }
};
```

## 📊 Contract Monitoring

### Contract Metrics
- **Usage frequency** per contract type
- **Validation error rates** dan failure patterns
- **Processing latency** per contract
- **Success/failure ratios** by service

### Contract Health Monitoring
```javascript
async function getContractSystemHealth() {
    return {
        total_contracts: 12,
        active_transports: ['http', 'grpc', 'nats', 'kafka'],
        validation_errors_24h: 5,
        processing_latency_p95: '45ms',
        contract_usage: {
            'service-registration': 150,
            'service-discovery': 3420,
            'health-reports': 8640
        }
    };
}
```

## 🚀 Best Practices

### Contract Design
1. **Backward compatibility**: Version contracts properly
2. **Clear semantics**: Self-documenting field names
3. **Validation first**: Fail fast on invalid data
4. **Transport agnostic**: Work across HTTP, gRPC, messaging

### Error Handling
1. **Graceful degradation**: Handle contract failures
2. **Detailed errors**: Provide actionable error messages
3. **Retry logic**: Implement appropriate retry strategies
4. **Circuit breakers**: Prevent cascade failures

### Performance
1. **Schema caching**: Avoid repeated parsing
2. **Async processing**: Non-blocking contract validation
3. **Batch operations**: Group related contract calls
4. **Connection pooling**: Reuse transport connections

## 🎯 Usage Examples

### Service Registration Flow
```bash
# 1. API Gateway registers with Central Hub
POST /discovery/register
{
  "service_name": "api-gateway",
  "host": "suho-api-gateway",
  "port": 8000,
  "metadata": { "type": "api-gateway" }
}

# 2. Central Hub validates and stores registration
# 3. Central Hub responds with registration confirmation
{
  "status": "registered",
  "registration_id": "api-gateway-1642234567890",
  "url": "http://suho-api-gateway:8000"
}
```

### Service Discovery Flow
```bash
# 1. Trading Engine looks for market data service
GET /discovery/services?service_type=market-data

# 2. Central Hub returns matching services
{
  "services": [
    {
      "service_name": "market-data-1",
      "url": "http://market-data-1:8080",
      "status": "active"
    }
  ]
}

# 3. Trading Engine calls market data service directly
GET http://market-data-1:8080/api/prices/EURUSD
```

### Configuration Update Flow
```bash
# 1. Central Hub detects config change in hot-reload/
# 2. Central Hub pushes update via gRPC stream
{
  "update_id": "cfg-001",
  "service_name": "api-gateway",
  "config_section": "business_rules",
  "config_data": { "rate_limiting": { "requests_per_minute": 2000 } }
}

# 3. API Gateway applies config without restart
# 4. API Gateway acknowledges update
```

---

**📝 Contracts: Fundasi Komunikasi yang Type-Safe dan Protocol-Agnostic**