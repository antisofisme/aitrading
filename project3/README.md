# Project3 - AI Trading Platform

## Structure Overview

This project implements a 3-tier AI trading platform architecture based on plan3 concepts with **Hybrid Processing Architecture** for optimal performance.

## 🏗️ Architecture Design: Hybrid Processing

**Performance Strategy**: Client-side preprocessing + Server-side AI processing for optimal latency (<30ms total).

### 📈 Performance Comparison:
- **Full Server Processing**: ~50-100ms latency
- **Hybrid Processing**: ~20-40ms latency ✅
- **Target**: <30ms end-to-end response time

### 🔄 Data Flow:
```
MT5 → Client (basic processing) → Server (AI) → Response
5ms     +     10ms network      +   15ms    = 30ms total
```

---

## 📁 Subfolders

### `/backend` (12 Optimized Services)
- **Purpose**: Server-side AI processing and business logic
- **Structure**: 5 groups with 12 total services (63% reduction from original 32)
- **Technologies**: Node.js, Express, Multi-database stack
- **Responsibilities**:
  - Complex AI/ML processing and multi-agent decisions
  - Business platform (user management, billing, analytics)
  - Trading core engine and risk management
  - Centralized coordination and database management

```
backend/
├── 01-core-infrastructure/     # API Gateway, Central Hub, Database
├── 02-data-processing/         # Data Bridge, Feature Engineering, ML Processing
├── 03-trading-core/           # Trading Engine, Risk Management, Backtesting
├── 04-business-platform/      # User Management, Notifications, Analytics
└── 05-support/               # Shared utilities, config, docs
```

### `/client-mt5` (Hybrid Local Processing)
- **Purpose**: MT5 integration with local preprocessing
- **Strategy**: Handle basic processing locally, send clean data to server
- **Technologies**: Python, MT5 API, WebSocket
- **Responsibilities**:
  - Real-time MT5 data collection and basic validation (<5ms)
  - Technical indicators calculation (SMA, RSI) locally
  - WebSocket communication with backend (<10ms network)
  - Client-side ErrorDNA implementation

```
client-mt5/
├── 01-mt5-integration/        # API Connector, Data Normalizer
├── 02-local-processing/       # Data Validator, Technical Indicators, Error Handler
├── 03-communication/          # WebSocket Client, Data Streamer
├── 04-infrastructure/         # Central Hub, Configuration, Monitoring
└── 05-support/               # Shared utilities
```

### `/frontend`
- **Purpose**: User interface and dashboard
- **Contains**: Web application, trading interface, analytics dashboard
- **Technologies**: React, WebSocket client
- **Responsibilities**:
  - Trading dashboard and controls
  - Real-time data visualization
  - User management interface
  - Subscription and billing UI

---

## ⚡ Performance Benefits of Hybrid Architecture

### **Client-Side Processing:**
✅ Reduced server load and bandwidth usage
✅ Lower latency (direct MT5 access)
✅ Better scalability (distributed processing)
✅ Pre-validated data sent to server

### **Server-Side Processing:**
✅ Focus on complex AI/ML algorithms
✅ Multi-agent coordination and consensus
✅ Centralized business logic and user management
✅ Advanced risk management and compliance

### **Overall Performance Target:**
- **Client Processing**: <5ms (basic indicators, validation)
- **Network Transfer**: <10ms (processed data only)
- **Server AI Processing**: <15ms (complex algorithms)
- **Total Latency**: **<30ms** (vs 50-100ms pure server)

---

## 🚀 Development Flow

1. **Backend**: Core infrastructure and AI services (12 optimized services)
2. **Client-MT5**: Hybrid local processing and MT5 integration
3. **Frontend**: User interface with real-time performance

**Key Innovation**: Hybrid processing architecture that distributes computational load while maintaining centralized intelligence and business logic.