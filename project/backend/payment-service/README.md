# Payment Service

Unified payment service with comprehensive Midtrans integration for the Indonesian market, replacing the legacy payment-gateway with enterprise-grade features.

## 🚀 Features

### Core Payment Processing
- **Midtrans Integration**: Complete SDK wrapper for all payment methods
- **Indonesian Payment Methods**: OVO, GoPay, DANA, LinkAja, ShopeePay support
- **Credit/Debit Cards**: Secure processing with 3D Secure authentication
- **Bank Transfers**: Virtual accounts for major Indonesian banks
- **Convenience Stores**: Indomaret and Alfamart payment options

### Subscription Management
- **Recurring Billing**: Automated subscription renewals
- **Multiple Billing Cycles**: Monthly, quarterly, and yearly plans
- **Plan Management**: Basic, Premium, Professional, and Enterprise tiers
- **Pro-rated Refunds**: Automatic calculation for partial refunds

### Security & Compliance
- **PCI DSS Compliance**: Enterprise-grade security implementation
- **Indonesian Regulations**: Full compliance with local financial laws
- **Data Protection**: Encrypted sensitive data storage
- **Audit Logging**: Comprehensive audit trail for all transactions

### Integration & Monitoring
- **Service Integration**: Seamless connection with user-management and billing services
- **Real-time Webhooks**: Instant payment status updates
- **Health Monitoring**: Comprehensive health checks and metrics
- **Error Handling**: Robust error handling with automatic retries

## 📁 Project Structure

```
payment-service/
├── src/
│   ├── config/           # Configuration files
│   │   ├── database.js   # MongoDB connection
│   │   ├── redis.js      # Redis connection
│   │   ├── logger.js     # Winston logger
│   │   └── midtrans.js   # Midtrans configuration
│   ├── controllers/      # Request handlers
│   │   └── PaymentController.js
│   ├── middleware/       # Express middleware
│   │   ├── security.js   # Security & PCI DSS compliance
│   │   └── validation.js # Input validation
│   ├── models/          # Database models
│   │   └── Payment.js   # Payment schema
│   ├── routes/          # API routes
│   │   ├── payments.js  # Payment endpoints
│   │   └── subscriptions.js # Subscription endpoints
│   ├── services/        # Business logic
│   │   ├── PaymentService.js      # Core payment logic
│   │   ├── MidtransService.js     # Midtrans SDK wrapper
│   │   ├── SubscriptionService.js # Subscription management
│   │   └── IntegrationService.js  # Service integration
│   └── app.js           # Express application
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── setup.js         # Test configuration
├── docs/                # Documentation
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-container setup
└── package.json         # Dependencies
```

## 🛠 Installation

### Prerequisites
- Node.js 18+
- MongoDB 6+
- Redis 7+
- Midtrans account (sandbox/production)

### Local Development

1. **Clone and install dependencies**
```bash
cd payment-service
npm install
```

2. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start dependencies**
```bash
# Using Docker Compose
docker-compose up -d mongo redis

# Or install locally
# MongoDB: https://docs.mongodb.com/manual/installation/
# Redis: https://redis.io/docs/getting-started/installation/
```

4. **Run the service**
```bash
# Development
npm run dev

# Production
npm start
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t payment-service .
docker run -p 3003:3003 payment-service
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NODE_ENV` | Environment mode | No | `development` |
| `PORT` | Service port | No | `3003` |
| `MONGODB_URI` | MongoDB connection string | Yes | - |
| `REDIS_HOST` | Redis host | Yes | `localhost` |
| `MIDTRANS_SERVER_KEY_SANDBOX` | Midtrans sandbox server key | Yes | - |
| `MIDTRANS_CLIENT_KEY_SANDBOX` | Midtrans sandbox client key | Yes | - |
| `JWT_SECRET` | JWT signing secret | Yes | - |
| `SERVICE_TOKEN` | Inter-service auth token | Yes | - |

### Midtrans Configuration

1. **Create Midtrans Account**
   - Sign up at [midtrans.com](https://midtrans.com)
   - Get sandbox credentials for testing
   - Configure production credentials for live usage

2. **Webhook Setup**
   - Set webhook URL: `https://yourdomain.com/api/payments/webhook`
   - Configure callback URLs for each payment method

3. **Payment Methods**
   - Enable required payment methods in Midtrans dashboard
   - Configure bank partnerships for virtual accounts

## 🔧 API Documentation

### Authentication

All endpoints except webhooks require authentication:

```bash
# Bearer token
Authorization: Bearer <jwt_token>

# Or service token
X-Service-Token: <service_token>
```

### Core Endpoints

#### Create Payment
```http
POST /api/payments
Content-Type: application/json

{
  "amount": 100000,
  "currency": "IDR",
  "paymentType": "credit_card",
  "customerDetails": {
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com",
    "phone": "+6281234567890",
    "billingAddress": {
      "address": "Jl. Sudirman No. 1",
      "city": "Jakarta",
      "postalCode": "10110"
    }
  },
  "itemDetails": [{
    "id": "plan-basic",
    "name": "Basic Trading Plan",
    "price": 100000,
    "quantity": 1
  }]
}
```

#### Get Payment Status
```http
GET /api/payments/{orderId}
```

#### Payment History
```http
GET /api/payments/user/history?page=1&limit=20&status=settlement
```

#### Cancel Payment
```http
PUT /api/payments/{orderId}/cancel
Content-Type: application/json

{
  "reason": "Customer cancellation"
}
```

### Subscription Endpoints

#### Create Subscription
```http
POST /api/subscriptions/create
Content-Type: application/json

{
  "planType": "premium",
  "billingCycle": "monthly",
  "startDate": "2024-01-01T00:00:00Z"
}
```

#### Get User Subscriptions
```http
GET /api/subscriptions/user/active
```

#### Cancel Subscription
```http
PUT /api/subscriptions/{subscriptionId}/cancel
Content-Type: application/json

{
  "reason": "User cancellation"
}
```

### Webhook Processing

Midtrans will send notifications to:
```http
POST /api/payments/webhook
X-Midtrans-Signature: <signature>

{
  "order_id": "PAY-1234567890",
  "transaction_status": "settlement",
  "fraud_status": "accept",
  "gross_amount": "100000.00"
}
```

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

### Test Environment Setup
```bash
# Uses MongoDB Memory Server for isolated testing
# No external dependencies required for testing
```

## 📊 Monitoring

### Health Checks
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "database": { "isConnected": true },
    "redis": { "isConnected": true },
    "midtrans": { "environment": "sandbox" }
  }
}
```

### Metrics
- Payment success/failure rates
- Response time monitoring
- Error rate tracking
- Subscription churn analysis

### Logging
- Structured JSON logging with Winston
- PCI DSS compliant audit trails
- Request/response logging (sanitized)
- Error tracking with stack traces

## 🔒 Security Features

### PCI DSS Compliance
- ✅ Secure data storage and transmission
- ✅ Access control and authentication
- ✅ Network security (HTTPS only)
- ✅ Vulnerability management
- ✅ Security monitoring and testing
- ✅ Information security policy

### Security Measures
- Helmet.js security headers
- Rate limiting (payment: 10/5min, API: 100/15min)
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection
- IP whitelisting for admin endpoints

## 🌍 Indonesian Market Support

### Payment Methods
- **Credit Cards**: Visa, Mastercard, JCB, Amex
- **Debit Cards**: Local Indonesian banks
- **Bank Transfer**: BCA, BNI, BRI, Mandiri, Permata, CIMB
- **E-Wallets**: OVO, GoPay, DANA, LinkAja, ShopeePay
- **Convenience Stores**: Indomaret, Alfamart
- **Buy Now Pay Later**: Akulaku

### Local Compliance
- Indonesian phone number validation
- Local address formats
- IDR currency handling (no cents)
- Jakarta timezone for billing
- Indonesian language support
- Local banking regulations compliance

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] HTTPS certificates installed
- [ ] Midtrans production credentials
- [ ] Database backups configured
- [ ] Monitoring setup (logs, metrics)
- [ ] Security scan completed
- [ ] Load testing performed

### Scaling Considerations
- Horizontal scaling with load balancer
- Redis cluster for high availability
- Database read replicas
- CDN for static assets
- Container orchestration (Kubernetes)

## 🔄 Migration from Legacy Payment Gateway

The new payment service replaces the old payment-gateway with:

### Enhanced Features
- ✅ Complete Midtrans integration (vs partial)
- ✅ All Indonesian payment methods
- ✅ Subscription management
- ✅ PCI DSS compliance
- ✅ Real-time webhooks
- ✅ Comprehensive testing

### Migration Steps
1. Deploy new payment-service
2. Update service integrations
3. Migrate existing payment data
4. Update frontend integration
5. Decommission old payment-gateway

## 📞 Support

### Development Team
- **Repository**: Internal Git Repository
- **Documentation**: `/docs` directory
- **Issue Tracking**: Internal issue tracker

### Midtrans Support
- **Documentation**: [docs.midtrans.com](https://docs.midtrans.com)
- **Support**: [support.midtrans.com](https://support.midtrans.com)
- **Status Page**: [status.midtrans.com](https://status.midtrans.com)

## 📋 License

Internal use only - Neliti AI Trading Platform

---

**Built with ❤️ for the Indonesian trading community**