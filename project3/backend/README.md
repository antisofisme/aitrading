# Backend - AI Trading Platform Server

## 🎯 Purpose
**Server-side processing layer** yang handle AI/ML analysis, business logic, dan multi-tenant management untuk hybrid AI trading platform dengan <30ms total response time.

---

## 📊 ChainFlow Diagram

```
Client-MT5 → Core Infrastructure → Data Processing → Trading Core → Business Platform
    ↓              ↓                    ↓               ↓              ↓
Processed Data  API Gateway         Advanced ML      AI Decisions   User Management
WebSocket      Central Hub         Feature Eng      Risk Mgmt      Notifications
User Context   Database Coord      Pattern Analysis  Backtesting   Analytics

Total Server Processing: <25ms (15ms AI + 10ms infrastructure)
```

---

## 🏗️ Backend Architecture Overview

### **Optimized 12-Service Architecture**
**Performance Strategy**: 63% reduction dari 35→12 services untuk optimal maintainability

```
4 Layers × 3 Services Each = 12 Core Services
├── Layer 1: Core Infrastructure (Foundation)
├── Layer 2: Data Processing (AI/ML Pipeline)
├── Layer 3: Trading Core (Decision Engine)
└── Layer 4: Business Platform (SaaS Features)
```

### **Service Communication Pattern**
```
Layer 1 (Infrastructure) ← All layers depend on this
Layer 2 (Data Processing) ← Receives from Client-MT5, outputs to Layer 3
Layer 3 (Trading Core) ← Receives from Layer 2, outputs decisions
Layer 4 (Business Platform) ← Orchestrates all layers for user features
```

---

## 🔧 Layer 1: Core Infrastructure

### **Purpose**: Foundation services yang handle basic operations untuk semua layers

### **api-gateway/**
**Input Flow**: HTTP requests dari frontend, WebSocket dari client-mt5
**Output Flow**: Authenticated requests routed ke appropriate services
**Function**:
- **Request Authentication**: JWT validation dan user context extraction
- **Rate Limiting**: Per-subscription tier enforcement (Free, Pro, Enterprise)
- **Service Routing**: Intelligent routing ke backend services
- **Response Aggregation**: Combine responses dari multiple services
- **Performance Target**: <5ms request routing dan authentication

**Dependencies**: database-service (user validation), central-hub (service discovery)

### **central-hub/**
**Input Flow**: Service registration requests, health check data
**Output Flow**: Service coordination commands, system status updates
**Function**:
- **Service Discovery**: Dynamic service registration dan discovery
- **Inter-service Communication**: Message routing antar services
- **System Monitoring**: Health checks dan performance tracking
- **Configuration Management**: Centralized config distribution
- **Performance Target**: <3ms service coordination

**Dependencies**: database-service (configuration storage)

### **database-service/**
**Input Flow**: Database operation requests dari all services
**Output Flow**: Query results, connection status, health metrics
**Function**:
- **Multi-Database Coordination**: PostgreSQL, ClickHouse, DragonflyDB, Weaviate, ArangoDB
- **Connection Pooling**: Optimized connection management
- **Transaction Management**: ACID compliance across databases
- **Data Consistency**: Cross-database synchronization
- **Performance Target**: <10ms multi-database operations

**Dependencies**: None (foundational service)

---

## 🧠 Layer 2: Data Processing

### **Purpose**: Advanced ML/AI processing yang transform client data menjadi trading insights

### **data-bridge/**
**Input Flow**: Pre-processed tick data dari client-mt5 via WebSocket
**Output Flow**: Validated, enriched market data ke feature-engineering
**Function**:
- **WebSocket Server**: Real-time connection management untuk multiple clients
- **Data Validation**: Advanced validation beyond client-side processing
- **Multi-User Distribution**: Route data ke appropriate user contexts
- **Usage Tracking**: Real-time billing data collection
- **Performance Target**: <3ms data validation dan routing

**Dependencies**: database-service (data storage), central-hub (service coordination)

### **feature-engineering/**
**Input Flow**: Validated market data dari data-bridge
**Output Flow**: Advanced feature vectors ke ml-processing
**Function**:
- **Advanced Technical Analysis**: Complex indicators (MACD, Bollinger Bands, custom patterns)
- **Cross-Asset Correlation**: Multi-pair correlation analysis
- **Market Regime Detection**: Bull/bear/sideways market classification
- **Feature Normalization**: ML-ready feature preparation
- **Performance Target**: <8ms advanced feature calculation

**Dependencies**: data-bridge (market data), database-service (historical data)

### **ml-processing/**
**Input Flow**: Feature vectors dari feature-engineering
**Output Flow**: AI predictions, patterns, confidence scores ke trading-core
**Function**:
- **Multi-Model Inference**: LSTM, CNN, XGBoost, ensemble methods
- **Pattern Recognition**: Chart patterns, anomaly detection
- **Prediction Generation**: Price direction, volatility, momentum forecasts
- **Model Performance Tracking**: Real-time accuracy monitoring
- **Performance Target**: <15ms AI inference (core requirement)

**Dependencies**: feature-engineering (features), database-service (model storage)

---

## ⚡ Layer 3: Trading Core

### **Purpose**: Trading decision engine yang convert AI insights menjadi actionable trading signals

### **trading-engine/**
**Input Flow**: AI predictions dari ml-processing, user preferences dari business-platform
**Output Flow**: Trading signals, execution commands, performance metrics
**Function**:
- **Decision Synthesis**: Combine AI predictions dengan user risk tolerance
- **Signal Generation**: Buy/sell/hold signals dengan confidence levels
- **Execution Logic**: Order placement strategy dan timing optimization
- **Performance Attribution**: Track decision accuracy dan profitability
- **Performance Target**: <5ms signal generation

**Dependencies**: ml-processing (predictions), risk-management (risk approval), database-service (user settings)

### **risk-management/**
**Input Flow**: Trading signals dari trading-engine, portfolio data
**Output Flow**: Risk-adjusted signals, position sizing recommendations
**Function**:
- **Risk Assessment**: VaR calculation, stress testing, correlation analysis
- **Position Sizing**: Kelly criterion, risk parity, custom algorithms
- **Portfolio Optimization**: Diversification, rebalancing recommendations
- **Risk Limits Enforcement**: Stop-loss, maximum drawdown protection
- **Performance Target**: <4ms risk calculation

**Dependencies**: trading-engine (signals), database-service (portfolio data)

### **backtesting-engine/**
**Input Flow**: Trading strategies, historical data requests
**Output Flow**: Backtesting results, performance metrics, optimization suggestions
**Function**:
- **Historical Simulation**: Strategy performance on historical data
- **Performance Metrics**: Sharpe ratio, maximum drawdown, win rate calculation
- **Strategy Optimization**: Parameter tuning untuk strategy improvement
- **Walk-Forward Analysis**: Out-of-sample strategy validation
- **Performance Target**: <2 seconds untuk standard backtest

**Dependencies**: database-service (historical data), trading-engine (strategy definitions)

---

## 💼 Layer 4: Business Platform

### **Purpose**: SaaS business logic yang handle user management, billing, dan enterprise features

### **user-management/**
**Input Flow**: User registration, authentication requests, profile updates
**Output Flow**: User context, subscription status, permission levels
**Function**:
- **User Lifecycle**: Registration, verification, subscription management
- **Authentication**: JWT token generation, session management
- **Authorization**: Role-based access control, feature gating
- **Profile Management**: User preferences, trading settings, account details
- **Performance Target**: <8ms user context resolution

**Dependencies**: database-service (user data), api-gateway (authentication)

### **notification-hub/**
**Input Flow**: Events dari all services, user notification preferences
**Output Flow**: Multi-channel notifications (Telegram, email, SMS, push)
**Function**:
- **Multi-Channel Delivery**: Telegram bots, email, SMS, push notifications
- **Event Processing**: Trading alerts, system notifications, performance updates
- **User Preferences**: Notification frequency, channel selection, content filtering
- **Template Management**: Dynamic notification content generation
- **Performance Target**: <2 seconds notification delivery

**Dependencies**: user-management (user preferences), all services (event sources)

### **analytics-service/**
**Input Flow**: Performance data dari all services, user activity logs
**Output Flow**: Business intelligence, user analytics, system metrics
**Function**:
- **Performance Analytics**: Trading performance, strategy effectiveness, user behavior
- **Business Intelligence**: Revenue analytics, user engagement, retention metrics
- **Real-time Dashboards**: System health, trading activity, financial metrics
- **Reporting**: Automated reports, custom analytics, data exports
- **Performance Target**: <5ms real-time analytics queries

**Dependencies**: All services (data sources), database-service (analytics storage)

---

## 🔄 Inter-Layer Data Flow

### **Primary Data Flow Chain**:
```
Client-MT5 → data-bridge → feature-engineering → ml-processing → trading-engine → risk-management
     ↓           ↓              ↓                    ↓               ↓              ↓
User Context  Validation    Advanced Features   AI Predictions   Trading Signals  Risk-Adjusted
Multi-pair    Real-time     Pattern Analysis    15ms Inference   Decision Logic   Position Sizing
```

### **Business Flow Chain**:
```
User Request → api-gateway → user-management → business-logic → analytics-service → notification-hub
      ↓            ↓             ↓                ↓                ↓                    ↓
Authentication  Routing    User Context     Feature Access   Performance Track   User Alerts
Rate Limiting   Validation  Subscription    Tier Enforcement  Real-time Metrics  Multi-channel
```

### **Infrastructure Flow Chain**:
```
All Services → central-hub → database-service → health-monitoring → system-optimization
     ↓             ↓              ↓                 ↓                    ↓
Service Coord  Discovery     Multi-DB Mgmt      Performance Track   Auto-scaling
Load Balance   Config Mgmt   Connection Pool     Error Detection     Resource Alloc
```

---

## ⚡ Performance Targets Summary

### **Layer Performance**:
- **Core Infrastructure**: <10ms total (API routing + DB operations)
- **Data Processing**: <26ms total (3ms + 8ms + 15ms)
- **Trading Core**: <11ms total (5ms + 4ms + 2ms async)
- **Business Platform**: <15ms total (8ms + 2ms + 5ms)

### **Total Server Performance**: **<25ms** (excluding async operations)
**Combined with Client**: **<30ms total** (5ms client + 25ms server)

---

## 🔧 Configuration Management

### **Centralized Configuration System**
**Single Source of Truth**: All configurations managed through environment variables in `.env` file

```bash
# Master configuration - all services use these values
POSTGRES_HOST=suho-postgresql
POSTGRES_PASSWORD=suho_secure_password_2024
KAFKA_BROKERS=suho-kafka:9092
NATS_URL=nats://suho-nats-server:4222
JWT_SECRET=your-super-secret-jwt-key-change-in-production
```

### **Configuration Flow**:
```
.env (Master) → docker-compose.yml → Central Hub → Services
     ↓              ↓                    ↓          ↓
Single Source    ${VAR} syntax      ENV: resolution  Config API
All Values      Environment Vars   Dynamic Loading  Service Ready
```

### **Key Benefits**:
- ✅ **Zero Hardcode**: No hardcoded values in any service
- ✅ **Single Update**: Change .env file, all services follow
- ✅ **Environment Safety**: Different values per environment
- ✅ **Security**: Centralized credential management
- ✅ **Maintainability**: 80% reduction in config complexity

### **Configuration Categories**:
- **Database Infrastructure**: 12 variables (PostgreSQL, ClickHouse, DragonflyDB, etc.)
- **Messaging Infrastructure**: 6 variables (Kafka, NATS, Zookeeper)
- **Core Services**: 8 variables (Central Hub, API Gateway, JWT)
- **Security & Authentication**: 4 variables (JWT secrets, API keys)
- **Development Settings**: 5 variables (Node env, logging, hot reload)

**Total**: 35+ environment variables managed centrally

---

## 🔧 Technology Stack

### **Core Technologies**:
- **Runtime**: Node.js 16+, Python 3.11+
- **Frameworks**: FastAPI, Express.js, WebSocket
- **Databases**: PostgreSQL + TimescaleDB, ClickHouse, DragonflyDB, Weaviate, ArangoDB
- **AI/ML**: TensorFlow, PyTorch, Scikit-learn, XGBoost
- **Communication**: REST APIs, WebSocket, NATS, Kafka

### **Infrastructure**:
- **Containerization**: Docker, Docker Compose
- **Configuration**: Centralized environment variables
- **Monitoring**: Health checks, performance metrics
- **Logging**: Structured JSON logging
- **Caching**: DragonflyDB (Redis-compatible)

---

## 🔗 Integration Points

### **External Integrations**:
- **Client-MT5**: WebSocket connection untuk real-time data
- **Frontend**: REST APIs + WebSocket untuk real-time updates
- **Payment Gateway**: Midtrans integration untuk subscription billing
- **Notification Channels**: Telegram Bot API, Email SMTP, SMS providers

### **Internal Communication**:
- **Synchronous**: HTTP/REST untuk request-response patterns
- **Asynchronous**: Message queues untuk event-driven processing
- **Real-time**: WebSocket untuk live data streaming
- **Database**: Connection pooling dengan automatic failover

---

## 🛡️ Multi-Tenant Architecture

### **Data Isolation Strategy**:
```
User Request → Tenant Context → Service Processing → Isolated Storage
     ↓              ↓               ↓                   ↓
User ID        Tenant Scope    User-specific Logic   Partitioned Data
Subscription   Access Control   Resource Limits       Separate Schemas
```

### **Resource Management**:
- **CPU/Memory**: Per-tenant resource allocation
- **Database**: Schema isolation per tenant
- **Caching**: User-specific cache namespaces
- **Rate Limiting**: Subscription-based limits enforcement

---

## 🎯 Business Value

### **Scalability Benefits**:
- **12 Services vs 35**: 63% reduction in complexity
- **Optimized Performance**: <30ms end-to-end response
- **Multi-tenant Ready**: Isolated processing per user
- **Enterprise Grade**: 99.99% availability target

### **Development Benefits**:
- **Clear Boundaries**: Each service has specific responsibility
- **Independent Scaling**: Scale services based on load patterns
- **Technology Flexibility**: Choose best tech per service function
- **Team Organization**: Teams can own specific services

### **Operational Benefits**:
- **Simplified Monitoring**: 12 services vs 35 to monitor
- **Faster Debugging**: Clear flow chains untuk troubleshooting
- **Cost Efficiency**: Optimized resource utilization
- **Maintenance**: Easier updates dan patches

---

## 📚 Documentation

### **Configuration Guides**:
- **Environment Variables**: `/docs/ENVIRONMENT_VARIABLES.md` - Complete reference for all 35+ variables
- **Configuration Management**: `/docs/CONFIGURATION_MANAGEMENT.md` - Centralized config system guide
- **Core Infrastructure**: `/01-core-infrastructure/README.md` - Service architecture overview

### **Quick Setup**:
```bash
# 1. Set environment variables in .env
cp .env.example .env
edit .env  # Update passwords and secrets

# 2. Start all services
docker-compose up -d

# 3. Verify health
curl http://localhost:7000/health  # Central Hub
curl http://localhost:8000/health  # API Gateway
```

### **Troubleshooting**:
- **Config Issues**: Check `.env` file syntax and required variables
- **Service Startup**: Verify Central Hub is running first
- **Network Issues**: Ensure Docker service names are used (not localhost)
- **Database Connection**: Check database credentials and network connectivity

---

**Next Integration**: Backend services ← Client-MT5 (hybrid processing) ← Frontend (user interface)
**Key Innovation**: Optimized 12-service architecture with centralized configuration management