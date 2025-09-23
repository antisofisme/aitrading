# Central Hub Service

## 🎯 Purpose
**Centralized coordination and shared infrastructure hub** yang handle service discovery, health monitoring, shared resources, dan system-wide coordination untuk semua backend services.

---

## 📊 ChainFlow Diagram

```
All Services ↔ Central Hub ↔ System Coordination
     ↓              ↓              ↓
Service Calls   Discovery      Health Monitor
Import Libs     Config Mgmt    Load Balance
Use Schemas     ErrorDNA       Circuit Breaker
```

---

## 🏗️ Central Hub Architecture

### **Static Resources** (Import/Library-based)
**Function**: Shared components yang di-import oleh services
**Usage**: Compile-time dependencies, static schema generation
**Performance**: No runtime overhead, optimal untuk high-frequency trading

### **Runtime Coordination** (Service-based)
**Function**: Real-time service coordination dan monitoring
**Usage**: Runtime service discovery, health checks, load balancing
**Performance**: <2ms coordination response time

### **Management Services** (Event-driven)
**Function**: System-wide management dan orchestration
**Usage**: Dynamic config updates, deployment coordination
**Performance**: Async processing untuk non-critical path

---

## 📁 Service Structure

```
central-hub/
├── static/                    # Static shared resources (import-based)
│   ├── proto/                # Protocol Buffers schemas
│   │   ├── common/           # Core data types (tick-data, user-context)
│   │   ├── trading/          # Trading schemas (signals, orders)
│   │   ├── business/         # Business schemas (user-mgmt, subscriptions)
│   │   └── ml/               # ML schemas (features, predictions)
│   ├── generated/            # Auto-generated code
│   │   ├── python/           # Python Protocol Buffers classes
│   │   ├── nodejs/           # Node.js Protocol Buffers classes
│   │   └── typescript/       # TypeScript definitions
│   ├── logging/              # ErrorDNA & logging libraries
│   │   ├── error-dna/        # Error pattern analysis
│   │   ├── loggers/          # Structured logging utilities
│   │   └── collectors/       # Log aggregation tools
│   ├── config/               # Base configuration templates
│   │   ├── development.json  # Dev environment settings
│   │   ├── production.json   # Prod environment settings
│   │   └── service-discovery.json # Service endpoints
│   └── utils/                # Common utilities
│       ├── performance/      # Performance monitoring tools
│       ├── validation/       # Data validation utilities
│       └── security/         # Security helpers
├── runtime/                  # Dynamic coordination services
│   ├── service-discovery/    # Real-time service registry
│   ├── health-monitor/       # Live health checks
│   ├── load-balancer/        # Traffic routing
│   └── circuit-breaker/      # System protection
└── management/               # Active system management
    ├── config-manager/       # Dynamic config updates
    ├── deployment-coord/     # Rolling updates coordination
    └── backup-coord/         # System-wide backup management
```

---

## 🔧 Static Resources (Import-based)

### **Protocol Buffers Management**
```python
# Service usage example
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from common.tick_data_pb2 import BatchTickData, MessageEnvelope
from trading.signals_pb2 import TradingSignal
from business.user_management_pb2 import UserContext
```

### **Enhanced MessageEnvelope Schema:**
```protobuf
syntax = "proto3";
package aitrading.common;

message MessageEnvelope {
  string message_type = 1;      // "tick_data", "user_event", "trading_signal"
  string user_id = 2;           // For Kafka partitioning
  bytes payload = 3;            // Actual protobuf message
  int64 timestamp = 4;          // For message ordering
  string service_source = 5;    // Originating service
  string correlation_id = 6;    // Request tracing
}
```

### **ErrorDNA Integration:**
```python
# ErrorDNA library usage
from central_hub.static.logging.error_dna import ErrorDNA, ErrorClassifier

error_dna = ErrorDNA()
classifier = ErrorClassifier()

# Usage in any service
try:
    process_trading_data()
except Exception as e:
    error_pattern = error_dna.analyze_error(e)
    classification = classifier.classify(error_pattern)
    logger.error(f"Trading error: {classification}", extra={"error_dna": error_pattern})
```

### **Performance Monitoring Utilities:**
```python
from central_hub.static.utils.performance import PerformanceTracker

# Usage
tracker = PerformanceTracker(service_name="api-gateway")
with tracker.measure("websocket_processing"):
    process_websocket_message()
```

---

## ⚡ Runtime Coordination Services

### **Service Discovery:**
```python
# Register service
await central_hub.register_service({
    "name": "data-bridge",
    "host": "localhost",
    "port": 8001,
    "protocol": "http",
    "health_endpoint": "/health"
})

# Discover service
data_bridge_url = await central_hub.discover_service("data-bridge")
```

### **Health Monitoring:**
```python
# Health check results
{
    "api-gateway": {"status": "healthy", "latency": 15, "last_check": "2024-01-20T10:30:00Z"},
    "data-bridge": {"status": "healthy", "latency": 8, "last_check": "2024-01-20T10:30:05Z"},
    "ml-processing": {"status": "degraded", "latency": 45, "last_check": "2024-01-20T10:29:58Z"}
}
```

### **Load Balancing:**
```python
# Get best available instance
best_instance = await central_hub.get_load_balanced_endpoint("data-bridge")
# Returns: {"host": "data-bridge-2", "port": 8001, "load": 0.3}
```

### **Circuit Breaker:**
```python
# Circuit breaker state management
circuit_state = await central_hub.get_circuit_state("ml-processing")
if circuit_state == "OPEN":
    # Route to fallback service or cache
    return cached_ml_result
```

---

## 🔄 Management Services

### **Dynamic Configuration:**
```python
# Push config update to all services
await central_hub.update_global_config({
    "rate_limits": {
        "free_tier": 50,
        "pro_tier": 200,
        "enterprise_tier": 1000
    }
})

# Services receive update via webhook/polling
```

### **Deployment Coordination:**
```python
# Rolling update coordination
await central_hub.coordinate_deployment({
    "service": "trading-engine",
    "version": "v2.1.0",
    "strategy": "rolling",
    "batch_size": 2
})
```

---

## 📊 Monitoring & Observability

### **System-wide Metrics:**
- **Service Health**: Real-time health status all services
- **Performance Metrics**: Latency, throughput, error rates
- **Resource Usage**: CPU, memory, network per service
- **Business Metrics**: Trading volume, user activity, revenue

### **Centralized Logging:**
```python
# Structured logging with ErrorDNA
from central_hub.static.logging import StructuredLogger

logger = StructuredLogger(service="api-gateway")
logger.info("WebSocket connection established", extra={
    "user_id": "user123",
    "connection_id": "conn456",
    "latency_ms": 15
})
```

### **Alert Management:**
- **Service Down**: Auto-alert when service health check fails
- **Performance Degradation**: Latency > threshold alerts
- **Error Spike**: ErrorDNA pattern analysis alerts
- **Business Impact**: Trading volume drops, user complaints

---

## 🔗 Integration Patterns

### **Service Integration:**
1. **Import Static Resources**: Protocol Buffers, ErrorDNA, utilities
2. **Register with Runtime**: Service discovery registration
3. **Health Check Endpoint**: Implement /health endpoint
4. **Config Updates**: Subscribe to dynamic config changes

### **Communication Patterns:**
- **Static Import**: Libraries, schemas, utilities (compile-time)
- **HTTP Calls**: Service discovery, health checks (runtime)
- **WebSocket**: Real-time config updates (optional)
- **Kafka Events**: System-wide notifications (async)

---

## Dependencies
- **None** - Central-Hub is the foundational coordination service
- **All services depend on Central-Hub** for coordination and shared resources

---

## 🎯 Business Value

### **Operational Excellence:**
- **Single Source of Truth**: All coordination centralized
- **Zero Downtime**: Health monitoring dengan auto-failover
- **Performance Optimization**: Load balancing dan circuit breaker protection
- **System Reliability**: Comprehensive monitoring dan alerting

### **Development Efficiency:**
- **Shared Resources**: No duplicate implementations
- **Type Safety**: Protocol Buffers schema enforcement
- **Error Intelligence**: ErrorDNA pattern analysis
- **Easy Integration**: Standard patterns untuk all services

### **Scalability Benefits:**
- **Service Discovery**: Easy addition of new services
- **Load Distribution**: Intelligent traffic routing
- **Performance Monitoring**: Proactive scaling decisions
- **System Evolution**: Smooth deployment coordination

---

**Key Innovation**: Unified static + runtime coordination hub yang optimize both development efficiency dan operational reliability untuk high-frequency trading platform.