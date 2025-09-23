# Support Layer - Shared Infrastructure

## 🎯 Purpose
**Centralized support infrastructure** yang menyediakan shared components, Protocol Buffers schemas, configuration management, dan utilities untuk semua backend services.

---

## 📊 ChainFlow Diagram

```
All Services → Shared Protocol Buffers → Generated Code → Service Communication
     ↓              ↓                      ↓                ↓
Import Code    Single Source Truth    Auto-generated    Type-safe Contracts
Use Schemas    Schema Evolution       Multi-language     Inter-service Calls
Config Mgmt    Version Control        Python/Node.js     Performance Optimized
```

---

## 🏗️ Support Structure Overview

### **shared/** - Centralized Shared Components
**Input Flow**: Schema definitions, configuration templates
**Output Flow**: Generated code, shared utilities, configuration files
**Function**:
- **Protocol Buffers Management**: Centralized schema definitions
- **Code Generation**: Multi-language protobuf generation
- **Shared Utilities**: Common functions across services
- **Configuration Templates**: Standardized config patterns

### **config/** - Global Configuration Management
**Input Flow**: Environment variables, deployment settings
**Output Flow**: Service-specific configurations
**Function**:
- **Environment Management**: Dev, staging, production configs
- **Service Discovery**: Service endpoints dan connection details
- **Database Configuration**: Multi-database connection strings
- **API Keys Management**: External service credentials

### **docs/** - Technical Documentation
**Input Flow**: Service documentation, API specs
**Output Flow**: Generated documentation, integration guides
**Function**:
- **API Documentation**: Auto-generated dari Protocol Buffers
- **Integration Guides**: Service integration patterns
- **Deployment Documentation**: Infrastructure setup guides
- **Performance Specifications**: Benchmarks dan targets

---

## 🔧 Protocol Buffers Schema Management

### **Centralized Schema Structure:**
```
shared/proto/
├── common/                    # Core data types
│   ├── tick-data.proto       # Market tick data structure
│   ├── user-context.proto    # User authentication & context
│   ├── api-response.proto    # Standard API response format
│   ├── error-types.proto     # Error codes & error handling
│   └── pagination.proto      # Pagination untuk large datasets
├── trading/                  # Trading-specific schemas
│   ├── signals.proto         # Trading signals & recommendations
│   ├── orders.proto          # Order placement & management
│   ├── positions.proto       # Position tracking & management
│   ├── risk-metrics.proto    # Risk assessment data
│   └── backtest-results.proto # Backtesting results format
├── business/                 # Business logic schemas
│   ├── user-management.proto # User registration & profiles
│   ├── subscription.proto    # Subscription tiers & billing
│   ├── notifications.proto   # Multi-channel notifications
│   └── analytics.proto       # Business analytics data
└── ml/                       # Machine Learning schemas
    ├── features.proto        # Feature vectors & engineering
    ├── predictions.proto     # ML model predictions
    ├── model-metadata.proto  # Model versioning & metadata
    └── training-data.proto   # Training dataset format
```

### **Auto-Generated Code Structure:**
```
shared/generated/
├── python/                   # Python generated code
│   ├── common/
│   │   ├── tick_data_pb2.py
│   │   ├── user_context_pb2.py
│   │   └── api_response_pb2.py
│   ├── trading/
│   │   ├── signals_pb2.py
│   │   └── orders_pb2.py
│   └── business/
│       ├── user_management_pb2.py
│       └── subscription_pb2.py
├── nodejs/                   # Node.js generated code
│   ├── common/
│   │   ├── tick_data_pb.js
│   │   ├── user_context_pb.js
│   │   └── api_response_pb.js
│   └── trading/
│       ├── signals_pb.js
│       └── orders_pb.js
└── typescript/               # TypeScript definitions
    ├── common/
    │   ├── tick_data_pb.d.ts
    │   └── user_context_pb.d.ts
    └── trading/
        ├── signals_pb.d.ts
        └── orders_pb.d.ts
```

---

## 🔄 Schema Definition Examples

### **Core Tick Data Schema (common/tick-data.proto):**
```protobuf
syntax = "proto3";

package aitrading.common;

message TickData {
  string symbol = 1;           // Trading pair (e.g., "EURUSD")
  double bid = 2;              // Bid price
  double ask = 3;              // Ask price
  double last = 4;             // Last trade price
  int64 volume = 5;            // Trade volume
  int64 timestamp = 6;         // Unix timestamp (milliseconds)
  double spread = 7;           // Bid-ask spread
}

message BatchTickData {
  repeated TickData ticks = 1; // Array of tick data
  string user_id = 2;          // User context
  int32 batch_id = 3;          // Batch identifier
  int64 batch_timestamp = 4;   // Batch creation time
  QualityMetrics quality = 5;  // Data quality metrics
}

message QualityMetrics {
  int32 validation_passed = 1; // Successfully validated ticks
  int32 validation_failed = 2; // Failed validation ticks
  double processing_time_ms = 3; // Processing time in milliseconds
}
```

### **Trading Signals Schema (trading/signals.proto):**
```protobuf
syntax = "proto3";

package aitrading.trading;

import "common/tick-data.proto";

message TradingSignal {
  string symbol = 1;           // Trading pair
  SignalType type = 2;         // BUY, SELL, HOLD
  double confidence = 3;       // Confidence level (0.0 - 1.0)
  double target_price = 4;     // Recommended entry price
  double stop_loss = 5;        // Stop loss level
  double take_profit = 6;      // Take profit level
  int64 timestamp = 7;         // Signal generation time
  string agent_source = 8;     // Which AI agent generated signal
  ModelPrediction ml_data = 9; // ML model prediction data
}

enum SignalType {
  SIGNAL_UNKNOWN = 0;
  SIGNAL_BUY = 1;
  SIGNAL_SELL = 2;
  SIGNAL_HOLD = 3;
  SIGNAL_CLOSE = 4;
}

message ModelPrediction {
  string model_id = 1;         // Model identifier
  string model_version = 2;    // Model version
  double accuracy_score = 3;   // Model accuracy
  repeated double features = 4; // Input features used
}
```

### **User Context Schema (common/user-context.proto):**
```protobuf
syntax = "proto3";

package aitrading.common;

message UserContext {
  string user_id = 1;          // Unique user identifier
  string tenant_id = 2;        // Multi-tenant isolation
  SubscriptionTier tier = 3;   // User subscription level
  repeated string permissions = 4; // User permissions
  UserPreferences preferences = 5; // Trading preferences
  int64 session_timestamp = 6; // Session creation time
}

enum SubscriptionTier {
  TIER_FREE = 0;
  TIER_PRO = 1;
  TIER_ENTERPRISE = 2;
}

message UserPreferences {
  repeated string preferred_symbols = 1; // User's trading pairs
  double risk_tolerance = 2;   // Risk level (0.0 - 1.0)
  bool enable_notifications = 3; // Notification preferences
  string timezone = 4;         // User timezone
  TradingSettings trading = 5; // Trading-specific settings
}

message TradingSettings {
  double max_position_size = 1; // Maximum position size
  double max_daily_loss = 2;   // Daily loss limit
  bool auto_trading_enabled = 3; // Auto-trading permission
  repeated string allowed_strategies = 4; // Allowed trading strategies
}
```

---

## 🚀 Code Generation & Build Process

### **Build Script (shared/generate-proto.sh):**
```bash
#!/bin/bash

# Protocol Buffers Code Generation Script
# Generates Python, Node.js, and TypeScript code from .proto schemas

PROTO_DIR="./proto"
OUTPUT_DIR="./generated"

echo "🔧 Generating Protocol Buffers code..."

# Create output directories
mkdir -p $OUTPUT_DIR/{python,nodejs,typescript}

# Generate Python code
echo "📦 Generating Python code..."
protoc --python_out=$OUTPUT_DIR/python \
       --proto_path=$PROTO_DIR \
       $PROTO_DIR/**/*.proto

# Generate Node.js code
echo "📦 Generating Node.js code..."
protoc --js_out=import_style=commonjs,binary:$OUTPUT_DIR/nodejs \
       --proto_path=$PROTO_DIR \
       $PROTO_DIR/**/*.proto

# Generate TypeScript definitions
echo "📦 Generating TypeScript definitions..."
protoc --plugin=protoc-gen-ts=./node_modules/.bin/protoc-gen-ts \
       --ts_out=$OUTPUT_DIR/typescript \
       --proto_path=$PROTO_DIR \
       $PROTO_DIR/**/*.proto

echo "✅ Code generation completed!"
echo "📁 Generated files available in: $OUTPUT_DIR"
```

### **Service Integration Example:**
```python
# In any service (e.g., data-bridge/src/main.py)
import sys
sys.path.append('../../../05-support/shared/generated/python')

from common.tick_data_pb2 import BatchTickData, TickData
from trading.signals_pb2 import TradingSignal

# Use generated classes
batch = BatchTickData()
tick = TickData()
tick.symbol = "EURUSD"
tick.bid = 1.08945
batch.ticks.append(tick)

# Serialize for inter-service communication
binary_data = batch.SerializeToString()
```

---

## ⚡ Performance Benefits

### **Protobuf vs JSON Performance:**
```
Data Size Comparison (1000 ticks):
JSON: ~150KB
Protobuf: ~60KB (60% reduction)

Serialization Speed:
JSON: ~15ms
Protobuf: ~1.5ms (10x faster)

Network Transfer (50 ticks/second):
JSON: 7.5MB/minute
Protobuf: 3MB/minute (60% bandwidth saving)
```

### **Trading Performance Impact:**
- **Serialization**: 15ms → 1.5ms = **13.5ms saved** per batch
- **Network**: 60% smaller payloads = **faster transmission**
- **Parsing**: 10x faster = **quicker service communication**
- **Total**: Significant contribution to **<30ms total latency** target

---

## 🔧 Configuration Management

### **Environment Configurations (config/):**
```
config/
├── development.json         # Local development settings
├── staging.json            # Staging environment
├── production.json         # Production environment
└── service-discovery.json  # Service endpoints mapping
```

### **Service Discovery Configuration:**
```json
{
  "services": {
    "api-gateway": {
      "host": "localhost",
      "port": 8000,
      "protocol": "http"
    },
    "data-bridge": {
      "host": "localhost",
      "port": 8001,
      "protocol": "ws"
    },
    "database-service": {
      "host": "localhost",
      "port": 8006,
      "protocol": "http"
    }
  },
  "databases": {
    "postgresql": "postgresql://user:pass@localhost:5432/aitrading",
    "clickhouse": "clickhouse://localhost:8123/market_data",
    "redis": "redis://localhost:6379/0"
  }
}
```

---

## 📚 Documentation Generation

### **Auto-Generated API Docs:**
- **Protocol Documentation**: Auto-generated dari .proto files
- **Service Interfaces**: API contracts per service
- **Integration Examples**: Code samples untuk each service
- **Performance Benchmarks**: Latency dan throughput metrics

### **Documentation Build Process:**
```bash
# Generate documentation
./generate-docs.sh

# Output:
# docs/api/ - Protocol Buffers API documentation
# docs/integration/ - Service integration guides
# docs/performance/ - Performance benchmarks
```

---

## 🎯 Integration Guidelines

### **Service Integration Pattern:**
1. **Import Schemas**: Add shared/generated to service imports
2. **Use Contracts**: Implement using generated protobuf classes
3. **Validate Data**: Use protobuf built-in validation
4. **Serialize/Deserialize**: Use protobuf methods untuk communication

### **Version Management:**
- **Schema Evolution**: Backward-compatible schema changes
- **Versioning Strategy**: Semantic versioning for major changes
- **Migration Path**: Gradual rollout for schema updates

### **Performance Monitoring:**
- **Serialization Time**: Track protobuf performance metrics
- **Data Size**: Monitor payload sizes
- **Error Rates**: Schema validation failures
- **Service Communication**: Inter-service latency tracking

---

## 🔗 Integration Points

### **Service Dependencies:**
- **All Backend Services**: Import shared protobuf schemas
- **Client-MT5**: Future integration dengan same schemas
- **Frontend**: TypeScript definitions untuk type safety
- **Database Services**: Protobuf serialization untuk storage

### **External Tools:**
- **Protocol Compiler**: protoc untuk code generation
- **Language Plugins**: Python, Node.js, TypeScript generators
- **Documentation Tools**: protoc-gen-doc untuk API docs
- **Validation Libraries**: Built-in protobuf validation

---

## 🎯 Business Value

### **Development Efficiency:**
- **Type Safety**: Compile-time error detection
- **Code Generation**: No manual contract coding
- **Consistent APIs**: Same interface patterns across services
- **Reduced Bugs**: Schema validation prevents data errors

### **Performance Benefits:**
- **60% Smaller Payloads**: Faster network transmission
- **10x Faster Serialization**: Lower CPU usage
- **Better Caching**: Efficient binary format
- **Reduced Latency**: Contributing to <30ms target

### **Maintenance Benefits:**
- **Single Source of Truth**: Centralized schema management
- **Version Control**: Schema evolution tracking
- **Backward Compatibility**: Gradual migration support
- **Team Coordination**: Clear API contracts for all teams

---

**Key Innovation**: Centralized Protocol Buffers schema management yang optimize performance dan maintainability untuk high-frequency trading platform.