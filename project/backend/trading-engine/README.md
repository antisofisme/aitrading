# Trading Engine - Forex & Gold Specialization

High-performance trading engine optimized for Forex and Gold trading with Indonesian market specialization, featuring Islamic trading compliance, sub-10ms order execution, and comprehensive correlation analysis.

## 🚀 Key Features

### Trading Specialization
- **28 Major Forex Pairs** - Complete coverage of major, minor, and exotic pairs
- **Gold Trading Optimization** - XAUUSD, XAGUSD with volatility handling
- **Currency Correlation Analysis** - Real-time correlation monitoring and alerts
- **Session-Based Trading** - Asia/Europe/US session-specific strategies

### Islamic Trading Compliance
- **Swap-Free Accounts** - Full Shariah compliance
- **No Riba/Interest** - Interest-free trading
- **Compliance Monitoring** - Real-time validation and reporting
- **Audit Trail** - Complete compliance audit logs

### High-Performance Execution
- **Sub-10ms Target Latency** - Optimized order execution
- **Circuit Breaker Protection** - Automatic failover during disruptions
- **Queue-Based Processing** - Bull queue with Redis backend
- **Performance Monitoring** - Real-time latency and throughput metrics

### Indonesian Market Optimization
- **Timezone Support** - Asia/Jakarta timezone integration
- **Local Session Handling** - Optimized for Asian trading hours
- **Currency Pairs** - Popular pairs for Indonesian traders
- **Islamic Features** - Designed for Muslim traders

## 📋 Architecture

```
Trading Engine
├── Order Executor         # High-performance order processing
├── Correlation Analyzer   # Real-time correlation analysis
├── Session Manager        # Trading session management
├── Islamic Trading Service # Shariah compliance
├── MT5 Integration        # Data bridge integration
├── Forex Strategies       # Trading strategy engine
└── WebSocket API          # Real-time communication
```

## 🛠 Installation

### Prerequisites
- Node.js >= 18.0.0
- Redis server
- MT5 Data Bridge service

### Setup

1. **Install Dependencies**
```bash
npm install
```

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or system Redis
sudo systemctl start redis
```

4. **Start Trading Engine**
```bash
# Development
npm run dev

# Production
npm start
```

## 🔧 Configuration

### Key Environment Variables

```env
# Performance
TARGET_LATENCY=10          # Target execution latency (ms)
MAX_LATENCY=50             # Maximum acceptable latency (ms)

# MT5 Integration
DATA_BRIDGE_URL=http://localhost:3002
DATA_BRIDGE_WS=ws://localhost:3002/ws

# Islamic Trading
ISLAMIC_TRADING_ENABLED=true
SWAP_FREE_ENABLED=true

# Correlation Analysis
CORRELATION_THRESHOLD=0.7
CORRELATION_UPDATE_INTERVAL=30000
```

### Forex Pairs Configuration

The engine supports 28 major forex pairs organized by category:

- **Major Pairs (7)**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
- **Minor Pairs (14)**: EURGBP, EURJPY, EURCHF, EURAUD, EURCAD, GBPJPY, etc.
- **Exotic Pairs (7)**: EURSGD, USDSGD, USDHKD, EURNOK, EURSEK, USDZAR, USDTRY

### Gold Trading Configuration

- **XAUUSD**: Gold vs USD with safe haven strategies
- **XAGUSD**: Silver vs USD with industrial demand factors
- **Volatility Handling**: Dynamic spreads and position sizing
- **Correlation Tracking**: Monitor gold-dollar relationships

## 📊 API Endpoints

### Order Execution
```bash
# Execute Order
POST /api/orders/execute
{
  "symbol": "EURUSD",
  "side": "buy",
  "quantity": 100000,
  "type": "market"
}

# Get Performance Metrics
GET /api/orders/performance
```

### Correlation Analysis
```bash
# Get Correlation Matrix
GET /api/correlation/matrix

# Get Symbol Correlations
GET /api/correlation/EURUSD

# Get Forex-Gold Analysis
GET /api/correlation/forex-gold
```

### Session Management
```bash
# Current Session
GET /api/sessions/current

# Session Recommendations
GET /api/sessions/recommendations

# Session Statistics
GET /api/sessions/statistics
```

### Islamic Trading
```bash
# Register Islamic Account
POST /api/islamic/register
{
  "accountId": "ISLAMIC_001",
  "maxPositionSize": 100000,
  "religionVerified": true
}

# Validate Trade
POST /api/islamic/validate-trade
{
  "accountId": "ISLAMIC_001",
  "tradeRequest": {
    "symbol": "EURUSD",
    "type": "market",
    "positionSize": 50000
  }
}

# Compliance Report
GET /api/islamic/compliance-report/:accountId?period=30
```

## 🔌 WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:3005/ws');

// Subscribe to order updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'orders'
}));

// Subscribe to correlation alerts
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'correlations'
}));
```

### Real-time Events
- `order_executed` - Order execution notifications
- `order_failed` - Order failure alerts
- `performance_alert` - Latency/performance warnings
- `high_correlation` - Correlation threshold alerts
- `session_start` - Trading session changes
- `session_alert` - Session transition warnings

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### Coverage Report
```bash
npm run test:coverage
```

### Performance Tests
```bash
# Test order execution latency
npm run test:performance

# Load testing
npm run test:load
```

## 📈 Performance Metrics

### Target Performance
- **Order Execution**: < 10ms average latency
- **Throughput**: 1000+ orders per second
- **Availability**: 99.9% uptime
- **Data Accuracy**: 99.99% accuracy

### Monitoring
- Real-time latency tracking
- Circuit breaker monitoring
- Correlation analysis performance
- Islamic compliance metrics

## 🔄 Integration with MT5 Data Bridge

The trading engine integrates with the existing MT5 Data Bridge:

```javascript
// Automatic connection
const mt5Integration = new MT5Integration({
  dataBridgeUrl: 'http://localhost:3002',
  wsUrl: 'ws://localhost:3002/ws'
});

// Subscribe to market data
await mt5Integration.subscribeToSymbol('EURUSD', 'tick');

// Execute orders
const execution = await mt5Integration.executeOrder(order);
```

## 🏗 Trading Strategies

### Session-Based Strategies
- **Asian Range Trading** - Low volatility range strategies
- **European Breakout** - High volatility breakout capture
- **NY News Trading** - Event-driven momentum
- **Sydney Gap Trading** - Weekend gap strategies

### Correlation Strategies
- **Divergence Trading** - Broken correlation opportunities
- **Currency Basket** - Strength/weakness arbitrage
- **Gold-Dollar Divergence** - Metal-currency correlation breaks

### Volatility Strategies
- **High Volatility Breakout** - Momentum capture
- **Low Volatility Range** - Mean reversion
- **Gold Safe Haven** - Risk-off positioning

## 🛡 Risk Management

### Position Limits
- Maximum position size: 10M units
- Maximum daily volume: 100M units
- Maximum correlation exposure: 30%
- Maximum drawdown: 10%

### Islamic Compliance
- No interest/swap charges
- No gambling (Maysir) patterns
- No excessive uncertainty (Gharar)
- Shariah-compliant instruments only

## 📋 Logging and Monitoring

### Log Categories
- Order execution logs
- Performance metrics
- Correlation updates
- Session changes
- Islamic compliance events
- Error and system logs

### Log Files
- `trading-engine.log` - General application logs
- `trading-errors.log` - Error logs
- `order-execution.log` - High-frequency trading logs

## 🚨 Alerts and Notifications

### Performance Alerts
- High latency warnings (> 10ms)
- Circuit breaker activations
- Queue backlog alerts
- Connection failures

### Trading Alerts
- High correlation detection
- Session transitions
- Islamic compliance violations
- Unusual market activity

## 🔧 Troubleshooting

### Common Issues

1. **High Latency**
   - Check Redis connection
   - Monitor MT5 bridge performance
   - Review system resources

2. **Order Failures**
   - Verify MT5 connectivity
   - Check symbol availability
   - Review market hours

3. **Correlation Issues**
   - Ensure sufficient price data
   - Check data quality
   - Verify update intervals

### Health Checks
```bash
# Service health
curl http://localhost:3005/health

# Performance metrics
curl http://localhost:3005/api/orders/performance

# Connection status
curl http://localhost:3005/api/mt5/status
```

## 📚 Documentation

- [API Reference](./docs/api-reference.md)
- [Strategy Documentation](./docs/strategies.md)
- [Islamic Trading Guide](./docs/islamic-trading.md)
- [Performance Tuning](./docs/performance.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Services

- [MT5 Data Bridge](../data-bridge/README.md) - Market data integration
- [Risk Management](../risk-management/README.md) - Risk control system
- [API Gateway](../api-gateway/README.md) - API orchestration
- [Central Hub](../central-hub/README.md) - Service coordination

---

**Trading Engine v1.0.0** - Built for Indonesian Forex & Gold traders with Islamic compliance and high-performance execution.