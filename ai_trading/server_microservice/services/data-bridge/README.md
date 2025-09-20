# MT5 Bridge Microservice

> **Enterprise-grade MetaTrader 5 integration microservice with real-time WebSocket communication and comprehensive trading functionality.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](Dockerfile)

## 🎯 Overview

The MT5 Bridge Microservice provides a robust, scalable interface between your trading applications and the MetaTrader 5 platform. Built with FastAPI and integrated with shared infrastructure components, it offers:

- **Real-time WebSocket communication** for live trading data
- **RESTful API endpoints** for MT5 operations
- **Cross-platform compatibility** (Windows with MT5, Linux/WSL with mock support)
- **Enterprise-grade monitoring** and performance tracking
- **Comprehensive error handling** and logging
- **Secure credential management** and validation

## 📋 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [WebSocket API](#websocket-api)
- [Security](#security)
- [Performance](#performance)
- [Monitoring](#monitoring)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 📚 Comprehensive Documentation

### **Core Documentation**
- **[Architecture Guide](ARCHITECTURE.md)** - Complete system architecture and component interactions
- **[WebSocket Protocol](WEBSOCKET_PROTOCOL.md)** - Detailed WebSocket message format and examples
- **[Performance Guide](PERFORMANCE_GUIDE.md)** - Performance optimizations and benchmarks
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Error handling and systematic troubleshooting
- **[Deployment Guide](DEPLOYMENT.md)** - Production deployment and monitoring setup

### **API Reference**
- **[API Documentation](API.md)** - Complete REST and WebSocket API reference
- **[Security Guidelines](SECURITY.md)** - Security best practices and compliance

## ✨ Features

### Core Functionality
- **MT5 Platform Integration**: Direct connection to MetaTrader 5 terminal
- **Real-time Data Streaming**: Live tick data, account information, and position updates
- **Trading Operations**: Order placement, modification, and cancellation
- **Account Monitoring**: Real-time balance, equity, and margin tracking
- **Symbol Management**: Symbol information caching and validation

### Architecture & Integration
- **Microservice Architecture**: Standalone service with clear API boundaries
- **Shared Infrastructure**: Integrated logging, configuration, error handling, and performance tracking
- **Event-Driven Communication**: WebSocket-based real-time messaging
- **Horizontal Scalability**: Designed for distributed deployment
- **Health Monitoring**: Comprehensive health checks and metrics

### Security & Reliability
- **Secure Configuration Management**: Centralized credential handling
- **Input Validation**: Comprehensive data validation for all operations
- **Error Recovery**: Automatic reconnection and error handling
- **Cross-Platform Support**: Mock MT5 implementation for development on Linux/WSL
- **Performance Optimization**: Connection pooling, caching, and async operations

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for containerized deployment)
- **MetaTrader 5 Terminal** (for Windows production environment)
- **Redis** (for caching - optional but recommended)

### 1. Clone and Setup

```bash
# Navigate to the microservice directory
cd /path/to/server_microservice/services/mt5-bridge

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your MT5 configuration
```

### 2. Configuration

```bash
# Basic configuration in .env
MT5_BRIDGE_PORT=8001
MT5_SERVER=FBS-Real
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
LOG_LEVEL=INFO
REDIS_URL=redis://localhost:6379
```

### 3. Run the Service

```bash
# Development mode
python main.py

# Or using Docker
docker-compose up --build
```

### 4. Test the Service

```bash
# Health check
curl http://localhost:8001/health

# Run comprehensive tests
python test_mt5_bridge.py
```

## 🔧 Installation

### Development Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download service wheels for offline deployment (optional)
python scripts/download_wheels.py --tier tier2

# 3. Set up pre-commit hooks (optional)
pre-commit install
```

### Docker Installation

```bash
# Build the service
docker build -t mt5-bridge:latest .

# Run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f mt5-bridge
```

### Production Installation

```bash
# 1. Set up production environment
export ENVIRONMENT=production

# 2. Configure secure credentials
# Use AWS Secrets Manager, HashiCorp Vault, or secure env file

# 3. Deploy with resource limits
docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MT5_BRIDGE_PORT` | Service port | `8001` | No |
| `MT5_SERVER` | MT5 server name | `FBS-Real` | Yes |
| `MT5_LOGIN` | MT5 account login | - | Yes |
| `MT5_PASSWORD` | MT5 account password | - | Yes |
| `MT5_PATH` | MT5 terminal path | - | No |
| `MT5_TIMEOUT` | Connection timeout (ms) | `10000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `REDIS_URL` | Redis connection URL | - | No |
| `MAX_CONNECTIONS` | Max WebSocket connections | `100` | No |

### Configuration File Structure

```yaml
# config/mt5_bridge.yaml
mt5_bridge:
  mt5:
    server: "FBS-Real"
    login: 12345
    timeout: 10000
    auto_reconnect: true
    max_reconnect_attempts: 5
  
  websocket:
    port: 8001
    max_connections: 100
    heartbeat_interval: 30
  
  performance:
    enable_caching: true
    cache_ttl: 300
    batch_size: 100
  
  security:
    validate_all_inputs: true
    rate_limiting: true
    max_requests_per_minute: 1000
```

## 📚 API Documentation

### RESTful Endpoints

#### Health & Status

```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "service": "mt5-bridge",
  "timestamp": "2025-01-27T10:00:00Z",
  "mt5_status": {
    "status": "connected",
    "server": "FBS-Real",
    "last_update": "2025-01-27T09:59:55Z"
  }
}
```

#### MT5 Connection

```http
POST /connect
Content-Type: application/json

{
  "server": "FBS-Real",
  "login": 12345,
  "password": "your_password"
}
```

#### Account Information

```http
GET /account
```
**Response:**
```json
{
  "success": true,
  "account": {
    "login": 12345,
    "balance": 10000.00,
    "equity": 9950.00,
    "margin": 100.00,
    "free_margin": 9850.00,
    "server": "FBS-Real",
    "currency": "USD"
  }
}
```

#### Tick Data

```http
POST /ticks
Content-Type: application/json

{
  "symbol": "EURUSD",
  "count": 100
}
```

#### Place Order

```http
POST /order
Content-Type: application/json

{
  "symbol": "EURUSD",
  "order_type": "buy",
  "volume": 0.1,
  "price": 1.0850,
  "sl": 1.0800,
  "tp": 1.0900,
  "comment": "API Order"
}
```

For complete API documentation with interactive examples, visit: `/docs` (Swagger UI) or `/redoc` (ReDoc)

## 🌐 WebSocket API

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8001/websocket/ws');
```

### Message Types

#### Account Information Streaming

```json
{
  "type": "account_info",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "balance": 10000.00,
    "equity": 9950.00,
    "margin": 100.00,
    "free_margin": 9850.00,
    "currency": "USD",
    "leverage": 100
  }
}
```

#### Real-time Tick Data

```json
{
  "type": "tick_data",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "symbol": "EURUSD",
    "bid": 1.0845,
    "ask": 1.0847,
    "spread": 2,
    "time": "2025-01-27T10:00:00Z",
    "volume": 1.0
  }
}
```

#### Trading Signal Execution

```json
{
  "type": "trading_signal",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "signal_id": "uuid-string",
    "symbol": "EURUSD",
    "action": "BUY",
    "volume": 0.1,
    "stop_loss": 1.0800,
    "take_profit": 1.0900,
    "comment": "AI Signal",
    "urgency": "high"
  }
}
```

#### Heartbeat

```json
{
  "type": "heartbeat",
  "timestamp": "2025-01-27T10:00:00Z",
  "data": {
    "client": "trading_client_1"
  }
}
```

## 🔒 Security

### Credential Management

⚠️ **CRITICAL SECURITY REQUIREMENTS**

1. **Never commit credentials to version control**
2. **Use environment variables or secure secret management**
3. **Rotate credentials regularly**
4. **Monitor for unauthorized access**

### Secure Configuration

```bash
# Use environment variables
export MT5_LOGIN="your_login"
export MT5_PASSWORD="your_secure_password"

# Or use secure secret management
# AWS Secrets Manager, HashiCorp Vault, etc.
```

### WebSocket Security

```javascript
// Client-side authentication (example)
const ws = new WebSocket('ws://localhost:8001/websocket/ws', {
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    'Client-ID': 'your-client-id'
  }
});
```

### Input Validation

All inputs are validated using centralized validation infrastructure:

```python
# Automatic validation for all trading parameters
{
  "symbol": "EURUSD",     # Validated against allowed symbols
  "volume": 0.1,          # Range: 0.01 - 10.0
  "action": "BUY"         # Enum: BUY, SELL, CLOSE
}
```

### Rate Limiting

```yaml
# Automatic rate limiting
max_requests_per_minute: 1000
websocket_messages_per_second: 100
```

## ⚡ Performance

### Optimizations Implemented

- **Connection Pooling**: Efficient WebSocket and database connections
- **Multi-layer Caching**: Redis + Memory cache for MT5 operations
- **Async Processing**: Non-blocking I/O operations
- **Batch Operations**: Bulk processing for high-frequency data
- **Resource Management**: Automatic cleanup and monitoring

### Performance Metrics

```http
GET /websocket/ws/status
```

**Response:**
```json
{
  "active_connections": 25,
  "messages_processed": 150000,
  "success_rate": 99.8,
  "average_response_time": 2.5,
  "cache_hit_rate": 85.2
}
```

### Benchmarks

| Operation | Response Time | Throughput |
|-----------|---------------|------------|
| REST API calls | < 10ms | 1000 req/s |
| WebSocket messages | < 5ms | 5000 msg/s |
| Tick processing | < 2ms | 10000 ticks/s |
| Order placement | < 50ms | 100 orders/s |

## 📊 Monitoring

### Health Checks

```http
GET /websocket/ws/health
```

**Monitors:**
- Service status
- MT5 connection health
- Database connectivity
- Memory and CPU usage
- WebSocket connections
- Cache performance

### Metrics Collection

The service automatically collects:

- **Performance metrics**: Response times, throughput, error rates
- **Business metrics**: Orders placed, account balance changes, trading volume
- **Infrastructure metrics**: CPU, memory, network I/O
- **Security metrics**: Authentication attempts, rate limiting triggers

### Logging

Structured logging with centralized infrastructure:

```json
{
  "timestamp": "2025-01-27T10:00:00Z",
  "level": "INFO",
  "service": "mt5-bridge",
  "component": "websocket",
  "message": "Order placed successfully",
  "context": {
    "order_id": "12345",
    "symbol": "EURUSD",
    "volume": 0.1,
    "price": 1.0850
  }
}
```

## 🧪 Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/

# With coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### Integration Tests

```bash
# Run integration tests (requires running service)
python test_mt5_bridge.py

# Specific test suites
pytest tests/integration/test_websocket.py
pytest tests/integration/test_mt5_connection.py
```

### Performance Tests

```bash
# Load testing
python tests/performance/test_websocket_load.py
python tests/performance/test_api_performance.py
```

### Test Results Example

```bash
🎯 Overall: 8/8 tests passed (100.0%)
✅ PASS - Health Endpoint
✅ PASS - Status Endpoint  
✅ PASS - Connect Endpoint
✅ PASS - Account Endpoint
✅ PASS - Ticks Endpoint
✅ PASS - WebSocket Connection
✅ PASS - WebSocket Status
✅ PASS - WebSocket Health
```

## 🚀 Deployment

### Docker Deployment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With resource limits
docker run -d \
  --name mt5-bridge \
  --memory="1g" \
  --cpus="2.0" \
  -p 8001:8001 \
  mt5-bridge:latest
```

### Kubernetes Deployment

```yaml
# kubernetes/mt5-bridge-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mt5-bridge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mt5-bridge
  template:
    metadata:
      labels:
        app: mt5-bridge
    spec:
      containers:
      - name: mt5-bridge
        image: mt5-bridge:1.0.0
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        env:
        - name: MT5_SERVER
          valueFrom:
            secretKeyRef:
              name: mt5-credentials
              key: server
```

### Environment-Specific Configurations

```bash
# Development
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Staging  
ENVIRONMENT=staging
LOG_LEVEL=INFO

# Production
ENVIRONMENT=production
LOG_LEVEL=WARNING
```

## 🔧 Troubleshooting

### Common Issues

#### MT5 Connection Failed

```bash
# Check MT5 terminal is running
# Verify credentials in .env file
# Check network connectivity
curl http://localhost:8001/health
```

#### WebSocket Connection Drops

```bash
# Check client heartbeat implementation
# Verify network stability
# Monitor service logs
docker-compose logs -f mt5-bridge
```

#### High Memory Usage

```bash
# Monitor memory metrics
curl http://localhost:8001/websocket/ws/status

# Check for memory leaks
docker stats mt5-bridge
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py

# Verbose WebSocket logging
export WEBSOCKET_DEBUG=true
```

### Support

For technical support:

1. **Check logs**: `docker-compose logs mt5-bridge`
2. **Review metrics**: Visit `/websocket/ws/health`
3. **Run diagnostics**: `python test_mt5_bridge.py`
4. **Create issue**: Include logs, configuration, and error details

## 🤝 Contributing

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-org/mt5-bridge.git

# Set up development environment
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Code Standards

- **Follow PEP 8** style guidelines
- **Use type hints** for all functions
- **Write comprehensive tests** for new features
- **Update documentation** for API changes
- **Use conventional commits** for version control

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Update documentation
4. Run full test suite
5. Submit pull request with description

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [API Docs](/docs)
- **Issues**: [GitHub Issues](https://github.com/your-org/mt5-bridge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mt5-bridge/discussions)

---

**MT5 Bridge Microservice** - Built with ❤️ for enterprise trading applications.