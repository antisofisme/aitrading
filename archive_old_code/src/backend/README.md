# AI Trading Platform Backend API

A robust, scalable Node.js/Express backend API for the AI Trading Platform featuring zero-trust security, multi-tenant subscription management, MT5 integration with sub-50ms latency, and intelligent error handling.

## 🚀 Features

### Core Capabilities
- **JWT Authentication**: Multi-tenant support with subscription tiers ($49-999/month)
- **RESTful API**: Complete trading operations with proper error handling
- **MT5 Integration**: WebSocket bridge with sub-50ms latency optimization
- **Zero-Trust Security**: Comprehensive security model with audit logging
- **Database Layer**: PostgreSQL + ClickHouse + Redis with connection pooling
- **ErrorDNA Integration**: Intelligent error handling with pattern recognition
- **Optimized Logging**: 81% cost reduction with level-based retention

### Security Features
- Rate limiting and DDoS protection
- Request/response validation
- Security event logging with risk scoring
- Multi-factor authentication support
- Encrypted credential storage

### Performance Optimizations
- Connection pooling for all databases
- Redis caching layer
- WebSocket connection management
- Query optimization and indexing
- Compression and response optimization

## 📁 Project Structure

```
src/backend/
├── api/                    # API route handlers
│   ├── auth.routes.ts     # Authentication endpoints
│   └── trading.routes.ts  # Trading operations
├── auth/                  # Authentication services
│   ├── jwt.ts            # JWT token management
│   └── auth.service.ts   # Authentication business logic
├── config/               # Configuration management
│   └── index.ts         # Environment configuration
├── database/            # Database layer
│   ├── index.ts        # Database service
│   └── schema.sql      # PostgreSQL schema
├── logging/             # Logging system
│   └── index.ts        # Optimized logging service
├── middleware/          # Express middleware
├── mt5/                # MT5 integration
│   └── index.ts       # WebSocket connection manager
├── security/           # Security services
│   └── index.ts       # Security middleware & services
├── types/              # TypeScript definitions
│   └── index.ts       # Core types
├── utils/              # Utility functions
│   └── errorDna.ts    # ErrorDNA integration
└── server.ts          # Main application server
```

## 🛠 Installation & Setup

### Prerequisites
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- ClickHouse 23+
- Docker & Docker Compose (recommended)

### Environment Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure required variables:
```bash
# Application
NODE_ENV=development
PORT=8000

# JWT Secrets (generate strong secrets!)
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_REFRESH_SECRET=your-super-secret-refresh-key-change-in-production

# Database
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password

# Subscription Tiers
BASIC_TIER_PRICE=49
PRO_TIER_PRICE=199
ENTERPRISE_TIER_PRICE=999
```

### Development Setup

1. Install dependencies:
```bash
npm install
```

2. Build TypeScript:
```bash
npm run build
```

3. Start development server:
```bash
npm run dev
```

### Docker Setup (Recommended)

1. Build and start all services:
```bash
docker-compose up -d
```

2. Check service health:
```bash
docker-compose ps
curl http://localhost:8000/health
```

3. View logs:
```bash
docker-compose logs -f aitrading-backend
```

## 🔧 Configuration

### Subscription Tiers

| Tier | Price/Month | Features |
|------|-------------|----------|
| Free | $0 | Basic access |
| Basic | $49 | Basic signals, Email support |
| Pro | $199 | Advanced signals, Priority support, API access |
| Enterprise | $999 | All features, Dedicated support, Custom integration |

### Security Configuration

- **Rate Limiting**: 100 requests per 15 minutes
- **JWT Expiration**: 15 minutes (access), 7 days (refresh)
- **Password Requirements**: 8+ chars, mixed case, numbers, symbols
- **Zero-Trust Model**: All requests validated and logged

### Log Retention Strategy (81% Cost Optimization)

| Level | Retention | Storage Tier | Compression | Cost Impact |
|-------|-----------|--------------|-------------|-------------|
| DEBUG | 7 days | Hot (DragonflyDB) | None | $45/month |
| INFO | 30 days | Warm (ClickHouse SSD) | LZ4 | $85/month |
| WARN | 90 days | Warm (ClickHouse SSD) | ZSTD | Included |
| ERROR | 180 days | Cold (ClickHouse) | ZSTD | $90/month |
| CRITICAL | 365 days | Cold (ClickHouse) | ZSTD | Included |

**Total Cost**: $220/month (vs $1,170 uniform retention = 81% savings)

## 🌐 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/profile` - Get user profile
- `POST /api/v1/auth/change-password` - Change password

### Trading Operations
- `GET /api/v1/trading/signals` - Get trading signals
- `POST /api/v1/trading/signals` - Create trading signal (Pro+)
- `POST /api/v1/trading/signals/execute` - Execute signal
- `GET /api/v1/trading/mt5-accounts` - Get MT5 accounts
- `POST /api/v1/trading/mt5-accounts` - Add MT5 account
- `GET /api/v1/trading/performance` - Performance metrics (Pro+)

### User Management
- `GET /api/v1/users/subscription` - Get subscription info

### System Monitoring
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed health with metrics
- `GET /api/v1/system/metrics` - System metrics (Enterprise)

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### Load Testing
```bash
npm run test:load
```

### API Testing with curl

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "firstName": "John",
    "lastName": "Doe",
    "subscriptionTier": "basic"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'

# Create trading signal (requires Pro tier)
curl -X POST http://localhost:8000/api/v1/trading/signals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "symbol": "EURUSD",
    "type": "buy",
    "entry_price": 1.1850,
    "stop_loss": 1.1800,
    "take_profit": 1.1900,
    "volume": 0.1,
    "confidence": 85,
    "reasoning": "Technical analysis shows strong upward momentum"
  }'
```

## 📊 Monitoring & Analytics

### Health Monitoring
- Service health endpoints
- Database connection monitoring
- MT5 connection status
- Performance metrics

### Error Analytics
- ErrorDNA pattern recognition
- Automated error classification
- Recovery recommendations
- Performance impact analysis

### Cost Analytics
- Log storage optimization tracking
- Database query performance
- Resource utilization metrics
- Cost savings reporting

## 🔒 Security

### Zero-Trust Architecture
- Server-side trading authority
- Client credential encryption (Windows DPAPI)
- Subscription validation real-time
- Comprehensive audit logging

### Security Events
- Login/logout tracking
- Failed authentication attempts
- Suspicious activity detection
- Risk scoring and alerting

### Compliance
- GDPR data minimization
- Financial record retention
- Audit trail immutability
- Regulatory reporting ready

## 🚀 Deployment

### Production Checklist
- [ ] Strong JWT secrets configured
- [ ] Database passwords secured
- [ ] SSL/TLS certificates installed
- [ ] Rate limiting configured
- [ ] Monitoring enabled
- [ ] Backup strategy implemented
- [ ] Security scanning completed

### Docker Production
```bash
# Set production environment
export NODE_ENV=production

# Start with monitoring
docker-compose --profile monitoring up -d

# Scale backend instances
docker-compose up -d --scale aitrading-backend=3
```

### Kubernetes Deployment
```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment
kubectl get pods -l app=aitrading-backend
```

## 📈 Performance Benchmarks

### Target Metrics
- **API Response Time**: <100ms (95th percentile)
- **MT5 Latency**: <50ms (signal to execution)
- **Database Queries**: <10ms (95th percentile)
- **Throughput**: 1000+ requests/second
- **Uptime**: 99.9%

### Optimization Features
- Connection pooling (20 connections per database)
- Query optimization with proper indexing
- Redis caching (85%+ hit rate)
- WebSocket connection reuse
- Compression and response optimization

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the [documentation](./docs/)
- Review the [troubleshooting guide](./docs/troubleshooting.md)

---

**Built with ❤️ for the AI Trading Platform**