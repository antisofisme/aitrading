# DATA-BRIDGE SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the data-bridge microservice, which handles 14 types of data sources (TradingView/MLQ5, MT5 Bridge, Market Feeds), real-time WebSocket streaming, and intelligent data routing to 6-database enterprise stack. This agent ensures proper data flow patterns, multi-source coordination, and streaming performance compliance.

## Examples:

### Example 1: MT5 Integration Development
**Context:** User is implementing new MT5 trading features and needs to ensure proper integration patterns.

**User:** "I'm adding new MT5 order management functionality to the data-bridge service"

**Assistant:** "I'll use the data-bridge service agent to validate your MT5 integration and ensure it follows proper data streaming patterns."

**Commentary:** Since the user is working on MT5 functionality within the data-bridge service, use the data-bridge agent to check MT5 connection patterns, WebSocket message formatting, real-time data flow, and streaming performance optimization.

### Example 2: WebSocket Connection Issues
**Context:** User is experiencing WebSocket connectivity problems between client and data-bridge service.

**User:** "My WebSocket connections keep dropping and I'm getting message validation errors"

**Assistant:** "Let me use the data-bridge service agent to diagnose the WebSocket connectivity and message validation issues."

**Commentary:** Since this involves WebSocket functionality specific to the data-bridge service, use the data-bridge agent to validate WebSocket message schemas, connection handling, client management, and real-time streaming protocols.

### Example 3: Data Source Integration
**Context:** User wants to add new market data sources to the data-bridge service.

**User:** "I want to integrate TradingView and Dukascopy data feeds into our data-bridge"

**Assistant:** "I'll use the data-bridge service agent to ensure proper data source integration patterns and validate the streaming architecture."

**Commentary:** Since the user is adding new data sources to the data-bridge service, use the data-bridge agent to validate data source abstraction patterns, streaming consistency, data validation rules, and multi-source coordination.

## Tools Available:

### 🌉 Service Directory Structure:
- **Root**: `server_microservice/services/data-bridge/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Config**: `config/data-bridge.yml` - Data source and streaming settings
- **API Endpoints**: `src/api/` - REST and WebSocket endpoints
  - `mt5_endpoints.py` - MT5 REST API operations
  - `mt5_websocket_endpoints.py` - WebSocket endpoint definitions
- **WebSocket Core**: `src/websocket/mt5_websocket.py` - Real-time WebSocket handling
- **Infrastructure**: `src/infrastructure/core/` - Service-specific infrastructure
  - `streaming_core.py` - High-performance data streaming
  - `circuit_breaker_core.py` - Connection reliability
  - `discovery_core.py` - Service discovery
  - `health_core.py` - Connection health monitoring
  - `metrics_core.py` - Streaming performance metrics
  - `queue_core.py` - Data queue management

### 🌉 Data Source Integration:
- **14 Data Types**: TradingView, MLQ5, MT5 Bridge, Market Feeds, News Sentiment, Economic Calendar, Central Bank Data, etc.
- **WebSocket Endpoint**: `/ws/mt5` with compression, heartbeat (30s), max 1000 connections
- **API Keys**: `MT5_LOGIN`, `MT5_PASSWORD`, `TRADINGVIEW_API_KEY`, `DUKASCOPY_API_KEY`

### 🔄 Real-time Processing:
- **Performance Targets**: <100ms data ingestion, <50ms WebSocket response
- **Streaming Config**: Symbols (EURUSD, GBPUSD, etc.), Timeframes (M1-D1), History bars (10K)
- **Caching Strategy**: Market data cache (60s TTL), connection pooling (50 concurrent)
- **Batch Processing**: 100 records per batch, compression enabled

### 🗄️ Database Routing Intelligence:
- **ClickHouse**: Time-series OHLCV data, account info
- **ArangoDB**: Multi-model relationships, signals
- **DragonflyDB**: High-speed cache, session management
- **PostgreSQL**: User auth, system data, configs
- **Weaviate**: Vector search, patterns, similarity
- **Redpanda**: Event streaming, real-time, Kafka streams

### 🔐 Security & Compliance:
- **MT5 Credentials**: Externalized via environment variables, encrypted storage
- **Rate Limiting**: 5000 requests/minute for data streams
- **Authentication**: API key validation, JWT tokens, service-to-service auth
- **Data Protection**: GDPR compliance, data encryption, audit logging

### 📊 Monitoring & Performance:
- **Health Checks**: Connection monitoring, latency tracking, error rates
- **Performance Metrics**: Tick streaming rates, message throughput, response times
- **Alerting**: Connection failures, data quality issues, performance degradation
- **Logging**: Structured JSON logs, data flow tracking, error correlation

### 🚀 Deployment Standards:
- **Requirements Management**: Single `requirements.txt` with full streaming dependencies (FastAPI, WebSocket, MT5 connectors, etc.)
- **Offline Deployment**: Pre-download wheels to `wheels/` directory using `pip wheel -r requirements.txt -w wheels/`
- **Docker Strategy**: Multi-stage build optimized for real-time processing, no internet during build
- **Service Independence**: Self-contained streaming service with isolated dependencies

**Note**: Always validate against architectural-reference-agent for security, performance, and global compliance standards.