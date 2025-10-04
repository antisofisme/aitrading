# OANDA Collector Contracts

## 📋 Overview

Contracts define standardized communication interfaces for the OANDA Collector service. All external and internal communications must conform to these contracts for type safety and protocol-agnostic communication.

## 🏗️ Contract Structure

```
contracts/
├── http-rest/                                    # HTTP REST API Contracts
│   ├── service-registration-to-central-hub.js   # Register service
│   ├── configuration-response-from-central-hub.js # Get configuration
│   └── health-report-to-central-hub.js          # Health reporting
│
├── nats-kafka/                                   # Message Broker Contracts
│   ├── pricing-stream-to-data-bridge.js         # Real-time pricing
│   ├── candles-stream-to-data-bridge.js         # Historical candles
│   └── heartbeat-stream-to-central-hub.js       # Service heartbeat
│
└── internal/                                     # Internal Contracts
    └── account-failover-notification.md         # Account failover events
```

## 🔄 Communication Flow

### To Central Hub (Discovery & Config)
1. **Service Registration** (HTTP REST)
   - `POST /discovery/register`
   - Register OANDA Collector instance
   - Provide capabilities and metadata

2. **Health Reporting** (HTTP REST)
   - `POST /health/report`
   - Report service health and metrics
   - Include OANDA-specific metrics

3. **Service Heartbeat** (NATS)
   - `service.heartbeat.oanda-collector.{instance_id}`
   - Continuous health stream
   - Real-time status updates

### From Central Hub (Config Updates)
1. **Configuration Response** (HTTP REST)
   - `GET /config/{service_name}`
   - Receive service configuration
   - Dynamic config updates

### To Data Bridge (Market Data)
1. **Pricing Stream** (NATS)
   - `market.pricing.oanda.{instrument}`
   - Real-time bid/ask prices
   - Direct to Data Bridge

2. **Candles Stream** (NATS)
   - `market.candles.oanda.{instrument}.{granularity}`
   - Historical OHLC data
   - Direct to Data Bridge

### Internal (Service Coordination)
1. **Account Failover**
   - Internal event bus
   - Coordinate failover between components
   - No external communication

## 📨 NATS Subject Patterns

### Market Data Subjects
```
market.pricing.oanda.EUR_USD
market.pricing.oanda.GBP_USD
market.pricing.oanda.USD_JPY

market.candles.oanda.EUR_USD.M1
market.candles.oanda.EUR_USD.H1
market.candles.oanda.GBP_USD.D
```

### Service Management Subjects
```
service.heartbeat.oanda-collector.oanda-collector-1
service.heartbeat.oanda-collector.oanda-collector-2
```

## 🎯 Data Flow Architecture

```
┌─────────────────┐
│  OANDA v20 API  │
└────────┬────────┘
         │ Real-time Stream
         ▼
┌─────────────────────────┐
│  OANDA Collector        │
│  ├── Pricing Stream     │──── NATS ────┐
│  ├── Candles Stream     │──── NATS ────┤
│  ├── Health Report      │──── HTTP ────┤
│  └── Heartbeat          │──── NATS ────┤
└─────────────────────────┘              │
         │                                │
         ▼                                ▼
┌─────────────────┐            ┌──────────────────┐
│  Central Hub    │            │   Data Bridge    │
│  (Discovery)    │            │   (Processing)   │
└─────────────────┘            └──────────────────┘
```

## 🛡️ Contract Validation

All contracts use **Joi schema validation** for:
- Type safety
- Data consistency
- Security sanitization
- Business rule enforcement

### Example Validation
```javascript
const { error, value } = PricingStreamSchema.validate(inputData);
if (error) {
    throw new Error(`Contract validation failed: ${error.message}`);
}
```

## 📊 Contract Categories

### 1. Service Lifecycle
- Registration
- Configuration
- Health reporting
- Heartbeat

### 2. Market Data
- Real-time pricing
- Historical candles
- Instrument metadata

### 3. Internal Coordination
- Account failover
- Stream management
- Error handling

## 🚀 Usage Guidelines

### 1. Always Validate
```javascript
const contract = require('./contracts/nats-kafka/pricing-stream-to-data-bridge');
const result = contract.process(pricingData);
```

### 2. Use Subject Generators
```javascript
const { generateSubject } = require('./contracts/nats-kafka/pricing-stream-to-data-bridge');
const subject = generateSubject('EUR_USD');
// Returns: "market.pricing.oanda.EUR_USD"
```

### 3. Handle Errors Gracefully
```javascript
try {
    const validated = contract.process(data);
    await nats.publish(validated.subject, validated.data);
} catch (error) {
    logger.error('Contract validation failed', error);
    // Fallback logic
}
```

## 🔍 Contract Versioning

Contracts follow semantic versioning:
- **Major**: Breaking changes to schema
- **Minor**: Backward-compatible additions
- **Patch**: Bug fixes and clarifications

Current version: **1.0.0**

## 📝 Adding New Contracts

1. Create contract file in appropriate folder
2. Define Joi schema
3. Implement processing function
4. Add subject/endpoint generators
5. Update this README
6. Add validation tests

## 🤝 Related Documentation

- [Central Hub Contracts Guide](../../01-core-infrastructure/central-hub/docs/CONTRACTS_GUIDE.md)
- [Data Bridge Contracts](../../02-data-processing/data-bridge/contracts/)
- [Service Architecture](../docs/ARCHITECTURE.md)
