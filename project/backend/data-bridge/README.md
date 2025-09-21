# Data Bridge Service

A high-performance WebSocket service for bridging MT5 trading platform data to the AI Trading Platform.

## Overview

The Data Bridge Service acts as a real-time data gateway between MetaTrader 5 (MT5) and the AI Trading Platform. It provides:

- **WebSocket API** for real-time market data streaming
- **REST API** for historical data retrieval
- **MT5 Integration** for forex and CFD data
- **Rate Limiting** and security features
- **Monitoring** and health checks

## Features

- ✅ Real-time WebSocket connections
- ✅ MT5 data integration (simulated)
- ✅ Multi-symbol subscriptions
- ✅ Rate limiting and security
- ✅ Comprehensive logging
- ✅ Health monitoring
- ✅ Configuration management
- ✅ Error handling and reconnection

## Quick Start

### Prerequisites

- Node.js 18+
- MT5 Terminal (for production)
- Redis (optional, for scaling)

### Installation

```bash
# Install dependencies
npm install

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### Configuration

Update `.env` with your MT5 credentials:

```env
# MT5 Connection
MT5_SERVER=your-mt5-server.com
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password

# Server Settings
PORT=3001
NODE_ENV=development
```

### Running

```bash
# Development
npm run dev

# Production
npm start

# Health check
npm run health
```

## API Documentation

### WebSocket API

Connect to: `ws://localhost:3001/ws`

#### Message Types

**Subscribe to Symbol:**
```json
{
  "type": "subscribe",
  "symbol": "EURUSD",
  "dataType": "tick"
}
```

**Unsubscribe:**
```json
{
  "type": "unsubscribe",
  "symbol": "EURUSD",
  "dataType": "tick"
}
```

**Heartbeat:**
```json
{
  "type": "ping"
}
```

#### Data Types

- `tick` - Real-time tick data (bid/ask/volume)
- `quote` - Quote data (bid/ask)
- `bar` - OHLCV candlestick data
- `book` - Market depth (Level II)

#### Sample Data Stream

```json
{
  "type": "data",
  "symbol": "EURUSD",
  "dataType": "tick",
  "data": {
    "bid": 1.05234,
    "ask": 1.05245,
    "volume": 50,
    "timestamp": 1640995200000
  },
  "timestamp": "2021-12-31T18:00:00.000Z"
}
```

### REST API

#### Get Service Status
```
GET /api/status
```

#### Get Available Symbols
```
GET /api/symbols
```

#### Get Market Data
```
GET /api/market-data/EURUSD?from=2024-01-01&to=2024-01-02&limit=100
```

#### Health Check
```
GET /health
```

## Project Structure

```
backend/data-bridge/
├── src/
│   ├── controllers/      # Request handlers
│   ├── middleware/       # Validation & security
│   ├── services/         # Business logic
│   ├── types/           # Type definitions
│   ├── utils/           # Utilities
│   └── server.js        # Main server file
├── config/
│   └── config.js        # Configuration
├── tests/               # Test files
├── logs/               # Log files
└── docs/               # Documentation
```

## Development

### Scripts

```bash
npm run dev        # Development with auto-reload
npm run test       # Run tests
npm run test:watch # Watch mode testing
npm run lint       # Code linting
npm run lint:fix   # Fix linting issues
```

### Testing

```bash
# Unit tests
npm test

# Integration tests
npm run test:integration

# Load testing
npm run test:load
```

## Monitoring

### Health Checks

The service provides multiple health check endpoints:

- `/health` - Basic health status
- `/api/status` - Detailed service status
- `/metrics` - Performance metrics

### Logging

Logs are written to:
- `logs/data-bridge.log` - General logs
- `logs/error.log` - Error logs only
- `logs/exceptions.log` - Unhandled exceptions

### Metrics

Key metrics tracked:
- Connection counts
- Message throughput
- MT5 connection status
- Memory usage
- Response times

## Security

### Rate Limiting

- 100 requests per 15 minutes per IP
- WebSocket connection limits
- Message validation

### Access Control

- IP whitelisting support
- JWT authentication ready
- CORS configuration
- Request validation

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | 3001 |
| `MT5_SERVER` | MT5 server address | localhost |
| `MT5_LOGIN` | MT5 account number | - |
| `MT5_PASSWORD` | MT5 password | - |
| `LOG_LEVEL` | Logging level | info |
| `REDIS_HOST` | Redis host | localhost |

### Advanced Configuration

See `config/config.js` for all available options:

- WebSocket settings
- Rate limiting
- Data buffering
- Security options
- Monitoring settings

## Deployment

### Docker

```bash
# Build image
docker build -t data-bridge .

# Run container
docker run -p 3001:3001 --env-file .env data-bridge
```

### Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Configure MT5 credentials
- [ ] Set up Redis for scaling
- [ ] Configure monitoring
- [ ] Set up log rotation
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS termination

## Troubleshooting

### Common Issues

**MT5 Connection Failed:**
- Verify MT5 server address and port
- Check firewall settings
- Validate credentials

**High Memory Usage:**
- Check subscription count
- Review data retention settings
- Monitor for memory leaks

**WebSocket Disconnections:**
- Check network stability
- Review timeout settings
- Monitor client implementations

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=debug npm run dev

# Monitor MT5 connection
npx nodemon --inspect src/server.js
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

## License

MIT License - see LICENSE file for details.

## Support

- GitHub Issues: Report bugs and request features
- Documentation: Check `/docs` directory
- Logs: Review service logs for debugging