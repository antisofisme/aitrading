# LEVEL 2 Business Services - Implementation Templates
**Template Specifications for 5 Business Services**

## Service Template Architecture

### Universal Service Structure
```
src/backend/services/[service-name]/
├── controllers/
│   ├── [service].controller.ts       # REST API endpoints
│   └── health.controller.ts          # Health check endpoints
├── services/
│   ├── [service].service.ts          # Business logic
│   ├── database.service.ts           # Database operations
│   └── cache.service.ts              # Redis operations
├── models/
│   ├── [service].model.ts            # Data models
│   └── validation.schema.ts          # Input validation
├── middleware/
│   ├── auth.middleware.ts            # Authentication
│   ├── tenant.middleware.ts          # Multi-tenant isolation
│   └── rate-limit.middleware.ts      # Rate limiting
├── database/
│   ├── migrations/                   # Database migrations
│   ├── seeds/                        # Test data
│   └── schema.sql                    # Database schema
├── tests/
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   └── performance/                  # Performance tests
├── config/
│   ├── service.config.ts             # Service configuration
│   └── database.config.ts            # Database configuration
├── Dockerfile                        # Container configuration
├── docker-compose.yml                # Development setup
└── README.md                         # Service documentation
```

## 1. User Management Service (Port 8021)

### Service Configuration
```typescript
// src/backend/services/user-management/config/service.config.ts
export const UserManagementConfig = {
  port: 8021,
  service: 'user-management',
  database: {
    postgresql: {
      host: process.env.POSTGRES_HOST || 'localhost',
      port: parseInt(process.env.POSTGRES_PORT || '5432'),
      database: process.env.POSTGRES_DB || 'ai_trading_users',
      username: process.env.POSTGRES_USER || 'postgres',
      password: process.env.POSTGRES_PASSWORD
    },
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      keyPrefix: 'user-sessions:'
    }
  },
  auth: {
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiry: '24h',
    refreshTokenExpiry: '7d',
    saltRounds: 12
  },
  multiTenant: {
    enabled: true,
    tenantHeader: 'X-Tenant-ID',
    defaultTenant: 'default'
  }
};
```

### Database Schema
```sql
-- src/backend/services/user-management/database/schema.sql
CREATE SCHEMA IF NOT EXISTS user_management;

-- Users table with tenant isolation
CREATE TABLE user_management.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, deleted
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, email),
    UNIQUE(tenant_id, username)
);

-- User roles for RBAC
CREATE TABLE user_management.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- User role assignments
CREATE TABLE user_management.user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_management.users(id),
    role_id UUID NOT NULL REFERENCES user_management.roles(id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES user_management.users(id),
    UNIQUE(user_id, role_id)
);

-- User sessions (complemented by Redis)
CREATE TABLE user_management.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user_management.users(id),
    session_token VARCHAR(255) NOT NULL,
    refresh_token VARCHAR(255),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Indexes for performance
CREATE INDEX idx_users_tenant_email ON user_management.users(tenant_id, email);
CREATE INDEX idx_users_tenant_username ON user_management.users(tenant_id, username);
CREATE INDEX idx_user_sessions_token ON user_management.user_sessions(session_token);
CREATE INDEX idx_user_sessions_user_id ON user_management.user_sessions(user_id);
```

### Core Service Implementation
```typescript
// src/backend/services/user-management/services/user-auth.service.ts
import { Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import bcrypt from 'bcrypt';
import { UserRepository } from '../repositories/user.repository';
import { RedisService } from './redis.service';

@Injectable()
export class UserAuthService {
  constructor(
    private userRepository: UserRepository,
    private jwtService: JwtService,
    private redisService: RedisService
  ) {}

  async register(tenantId: string, userData: RegisterUserDto): Promise<UserResponse> {
    // Multi-tenant user registration
    const existingUser = await this.userRepository.findByEmailAndTenant(
      userData.email,
      tenantId
    );

    if (existingUser) {
      throw new ConflictException('User already exists in this tenant');
    }

    const passwordHash = await bcrypt.hash(userData.password, 12);

    const user = await this.userRepository.create({
      ...userData,
      tenantId,
      passwordHash,
      status: 'active'
    });

    // Generate verification token
    const verificationToken = this.generateVerificationToken(user.id);
    await this.redisService.setEmailVerification(user.id, verificationToken);

    return this.formatUserResponse(user);
  }

  async authenticate(tenantId: string, email: string, password: string): Promise<AuthResponse> {
    const user = await this.userRepository.findByEmailAndTenant(email, tenantId);

    if (!user || !await bcrypt.compare(password, user.passwordHash)) {
      throw new UnauthorizedException('Invalid credentials');
    }

    if (user.status !== 'active') {
      throw new UnauthorizedException('Account is not active');
    }

    // Generate JWT tokens
    const accessToken = this.generateAccessToken(user);
    const refreshToken = this.generateRefreshToken(user);

    // Store session in Redis
    await this.redisService.setUserSession(user.id, {
      accessToken,
      refreshToken,
      tenantId,
      lastAccessed: new Date()
    });

    // Update last login
    await this.userRepository.updateLastLogin(user.id);

    return {
      user: this.formatUserResponse(user),
      accessToken,
      refreshToken,
      expiresIn: '24h'
    };
  }

  async validateToken(token: string): Promise<UserTokenPayload> {
    try {
      const payload = this.jwtService.verify(token);

      // Check if session exists in Redis
      const session = await this.redisService.getUserSession(payload.userId);
      if (!session) {
        throw new UnauthorizedException('Session not found');
      }

      return payload;
    } catch (error) {
      throw new UnauthorizedException('Invalid token');
    }
  }

  private generateAccessToken(user: User): string {
    return this.jwtService.sign({
      userId: user.id,
      tenantId: user.tenantId,
      email: user.email,
      roles: user.roles.map(r => r.name)
    });
  }

  private generateRefreshToken(user: User): string {
    return this.jwtService.sign(
      { userId: user.id, tenantId: user.tenantId, type: 'refresh' },
      { expiresIn: '7d' }
    );
  }
}
```

## 2. Subscription Service (Port 8022)

### Service Configuration
```typescript
// src/backend/services/subscription-service/config/service.config.ts
export const SubscriptionConfig = {
  port: 8022,
  service: 'subscription-service',
  database: {
    postgresql: {
      // PostgreSQL for transactional data
      schema: 'subscription_management'
    },
    clickhouse: {
      // ClickHouse for analytics
      host: process.env.CLICKHOUSE_HOST || 'localhost',
      port: parseInt(process.env.CLICKHOUSE_PORT || '8123'),
      database: 'ai_trading_analytics'
    }
  },
  subscriptionTiers: {
    free: {
      name: 'Free',
      price: 0,
      features: ['basic_predictions', 'limited_api_calls'],
      limits: {
        apiCallsPerDay: 100,
        predictionsPerMonth: 50
      }
    },
    pro: {
      name: 'Professional',
      price: 29.99,
      features: ['advanced_predictions', 'extended_api_calls', 'analytics'],
      limits: {
        apiCallsPerDay: 10000,
        predictionsPerMonth: 1000
      }
    },
    enterprise: {
      name: 'Enterprise',
      price: 99.99,
      features: ['unlimited_predictions', 'unlimited_api_calls', 'custom_models'],
      limits: {
        apiCallsPerDay: -1, // Unlimited
        predictionsPerMonth: -1 // Unlimited
      }
    }
  }
};
```

### Database Schema
```sql
-- src/backend/services/subscription-service/database/schema.sql
CREATE SCHEMA IF NOT EXISTS subscription_management;

-- Subscription tiers
CREATE TABLE subscription_management.subscription_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL, -- monthly, yearly
    features JSONB DEFAULT '[]',
    limits JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User subscriptions
CREATE TABLE subscription_management.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    tier_id UUID NOT NULL REFERENCES subscription_management.subscription_tiers(id),
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, cancelled, expired
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Usage tracking
CREATE TABLE subscription_management.usage_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscription_management.subscriptions(id),
    feature_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 0,
    tracking_period DATE NOT NULL, -- Daily tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subscription_id, feature_name, tracking_period)
);

-- Indexes
CREATE INDEX idx_subscriptions_user_tenant ON subscription_management.subscriptions(user_id, tenant_id);
CREATE INDEX idx_usage_tracking_subscription ON subscription_management.usage_tracking(subscription_id, tracking_period);
```

### ClickHouse Analytics Schema
```sql
-- ClickHouse schema for analytics
CREATE DATABASE IF NOT EXISTS ai_trading_analytics;

-- Usage analytics table
CREATE TABLE ai_trading_analytics.usage_analytics (
    timestamp DateTime,
    user_id String,
    tenant_id String,
    subscription_id String,
    feature_name String,
    usage_count UInt32,
    request_duration_ms UInt32,
    response_size_bytes UInt32,
    success Boolean,
    error_code String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (tenant_id, user_id, timestamp);

-- Subscription metrics
CREATE TABLE ai_trading_analytics.subscription_metrics (
    date Date,
    tenant_id String,
    tier_name String,
    total_subscriptions UInt32,
    new_subscriptions UInt32,
    cancelled_subscriptions UInt32,
    revenue_usd Decimal(10,2)
) ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (tenant_id, tier_name, date);
```

## 3. Payment Gateway Service (Port 8023)

### Midtrans Integration Configuration
```typescript
// src/backend/services/payment-gateway/config/service.config.ts
export const PaymentGatewayConfig = {
  port: 8023,
  service: 'payment-gateway',
  providers: {
    midtrans: {
      serverKey: process.env.MIDTRANS_SERVER_KEY,
      clientKey: process.env.MIDTRANS_CLIENT_KEY,
      isProduction: process.env.NODE_ENV === 'production',
      apiUrl: process.env.NODE_ENV === 'production'
        ? 'https://api.midtrans.com'
        : 'https://api.sandbox.midtrans.com'
    }
  },
  supportedMethods: [
    'credit_card',
    'bank_transfer',
    'gopay',
    'dana',
    'shopeepay',
    'indomaret',
    'alfamart'
  ],
  security: {
    encryptionKey: process.env.PAYMENT_ENCRYPTION_KEY,
    webhookSecret: process.env.MIDTRANS_WEBHOOK_SECRET
  }
};
```

### Database Schema
```sql
-- src/backend/services/payment-gateway/database/schema.sql
CREATE SCHEMA IF NOT EXISTS payment_management;

-- Payment transactions
CREATE TABLE payment_management.payment_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,
    subscription_id UUID,
    external_transaction_id VARCHAR(255) NOT NULL, -- Midtrans transaction ID
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, success, failed, cancelled
    provider_response JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Payment methods for users
CREATE TABLE payment_management.user_payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    type VARCHAR(50) NOT NULL, -- credit_card, bank_account, e_wallet
    provider VARCHAR(50) NOT NULL, -- midtrans, etc.
    encrypted_data TEXT, -- Encrypted payment method details
    is_default BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_transactions_user_tenant ON payment_management.payment_transactions(user_id, tenant_id);
CREATE INDEX idx_transactions_external_id ON payment_management.payment_transactions(external_transaction_id);
CREATE INDEX idx_transactions_status ON payment_management.payment_transactions(status);
```

## 4. Notification Service (Port 8024)

### Multi-Bot Configuration
```typescript
// src/backend/services/notification-service/config/service.config.ts
export const NotificationConfig = {
  port: 8024,
  service: 'notification-service',
  telegram: {
    botTokens: {
      default: process.env.TELEGRAM_BOT_TOKEN_DEFAULT,
      premium: process.env.TELEGRAM_BOT_TOKEN_PREMIUM,
      enterprise: process.env.TELEGRAM_BOT_TOKEN_ENTERPRISE
    },
    webhookUrl: process.env.TELEGRAM_WEBHOOK_URL,
    maxRetries: 3
  },
  queue: {
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      keyPrefix: 'notifications:'
    },
    priorities: {
      critical: 1,
      high: 2,
      medium: 3,
      low: 4
    }
  },
  templates: {
    welcome: 'Welcome to AI Trading Platform! 🚀',
    subscription_activated: 'Your {{tier}} subscription is now active! ✅',
    payment_received: 'Payment received: ${{amount}}. Thank you! 💳',
    usage_limit_warning: 'You have used {{percentage}}% of your {{feature}} quota.',
    trading_alert: '🔔 Trading Alert: {{symbol}} - {{signal}}'
  }
};
```

### Database Schema
```sql
-- src/backend/services/notification-service/database/schema.sql
CREATE SCHEMA IF NOT EXISTS notification_management;

-- User notification preferences
CREATE TABLE notification_management.user_notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    telegram_chat_id VARCHAR(100),
    bot_assignment VARCHAR(50) DEFAULT 'default', -- default, premium, enterprise
    notification_types JSONB DEFAULT '{}', -- Which notifications to receive
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tenant_id)
);

-- Notification queue (complemented by Redis)
CREATE TABLE notification_management.notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255),
    message TEXT NOT NULL,
    priority INTEGER DEFAULT 3,
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, failed, retrying
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Indexes
CREATE INDEX idx_notification_prefs_user ON notification_management.user_notification_preferences(user_id, tenant_id);
CREATE INDEX idx_notification_history_status ON notification_management.notification_history(status, created_at);
```

## 5. Billing Service (Port 8025)

### Service Configuration
```typescript
// src/backend/services/billing-service/config/service.config.ts
export const BillingConfig = {
  port: 8025,
  service: 'billing-service',
  billing: {
    currencies: ['USD', 'IDR'],
    defaultCurrency: 'USD',
    taxRates: {
      IDR: 0.11, // 11% VAT in Indonesia
      USD: 0.0   // No tax for international
    },
    invoicePrefix: 'INV',
    invoiceNumberFormat: 'YYYY-MM-####'
  },
  integrations: {
    paymentGateway: {
      baseUrl: 'http://payment-gateway:8023',
      timeout: 30000
    },
    subscriptionService: {
      baseUrl: 'http://subscription-service:8022',
      timeout: 15000
    }
  },
  schedules: {
    billingCycle: '0 0 1 * *', // First day of every month
    reminderCycle: '0 0 * * 1', // Every Monday
    overdueCheck: '0 0 * * *'   // Daily
  }
};
```

### Database Schema
```sql
-- src/backend/services/billing-service/database/schema.sql
CREATE SCHEMA IF NOT EXISTS billing_management;

-- Invoices
CREATE TABLE billing_management.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id UUID NOT NULL,
    subscription_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, overdue, cancelled
    due_date DATE NOT NULL,
    paid_date TIMESTAMP,
    payment_transaction_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice line items
CREATE TABLE billing_management.invoice_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES billing_management.invoices(id),
    description VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    metadata JSONB DEFAULT '{}'
);

-- Billing history
CREATE TABLE billing_management.billing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- invoice_created, payment_received, etc.
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_invoices_user_tenant ON billing_management.invoices(user_id, tenant_id);
CREATE INDEX idx_invoices_status ON billing_management.invoices(status, due_date);
CREATE INDEX idx_invoices_subscription ON billing_management.invoices(subscription_id);
```

## Service Coordination Templates

### Inter-Service Communication
```typescript
// src/backend/shared/services/service-client.ts
export class ServiceClient {
  private baseUrl: string;
  private timeout: number;
  private circuitBreaker: CircuitBreaker;

  constructor(serviceName: string, config: ServiceConfig) {
    this.baseUrl = config.baseUrl;
    this.timeout = config.timeout || 30000;
    this.circuitBreaker = new CircuitBreaker(this.makeRequest.bind(this), {
      timeout: this.timeout,
      errorThresholdPercentage: 50,
      resetTimeout: 30000
    });
  }

  async get<T>(endpoint: string, params?: any): Promise<T> {
    return this.circuitBreaker.fire('GET', endpoint, null, params);
  }

  async post<T>(endpoint: string, data: any): Promise<T> {
    return this.circuitBreaker.fire('POST', endpoint, data);
  }

  private async makeRequest(method: string, endpoint: string, data?: any, params?: any) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      method,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-Service-Name': 'ai-trading-platform'
      }
    };

    if (data) {
      config.body = JSON.stringify(data);
    }

    if (params) {
      const urlParams = new URLSearchParams(params);
      url += `?${urlParams}`;
    }

    const response = await fetch(url, config);

    if (!response.ok) {
      throw new Error(`Service request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}
```

### Multi-Tenant Middleware
```typescript
// src/backend/shared/middleware/multi-tenant.middleware.ts
export const multiTenantMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const tenantId = req.headers['x-tenant-id'] as string ||
                   req.query.tenant_id as string ||
                   'default';

  if (!tenantId) {
    return res.status(400).json({
      error: 'Tenant ID is required',
      code: 'MISSING_TENANT_ID'
    });
  }

  // Validate tenant ID format
  if (!/^[a-zA-Z0-9_-]+$/.test(tenantId)) {
    return res.status(400).json({
      error: 'Invalid tenant ID format',
      code: 'INVALID_TENANT_ID'
    });
  }

  // Add tenant context to request
  req.tenantId = tenantId;

  // Set tenant-specific database schema
  req.dbSchema = `tenant_${tenantId}`;

  next();
};
```

## Testing Templates

### Integration Test Template
```typescript
// src/backend/services/[service]/tests/integration/service.integration.test.ts
describe('[Service Name] Integration Tests', () => {
  let app: any;
  let testTenantId: string;
  let testUserId: string;

  beforeAll(async () => {
    app = await createTestApp();
    testTenantId = 'test-tenant';
    testUserId = 'test-user-uuid';
  });

  afterAll(async () => {
    await cleanupTestData(testTenantId);
    await app.close();
  });

  describe('Multi-tenant isolation', () => {
    it('should isolate data between tenants', async () => {
      // Test tenant isolation
    });

    it('should enforce tenant-specific rate limiting', async () => {
      // Test rate limiting per tenant
    });
  });

  describe('Service communication', () => {
    it('should communicate with other services', async () => {
      // Test inter-service communication
    });

    it('should handle service failures gracefully', async () => {
      // Test circuit breaker patterns
    });
  });

  describe('Performance benchmarks', () => {
    it('should meet response time requirements', async () => {
      // Test performance targets
    });
  });
});
```

## Docker Configuration Templates

### Service Dockerfile
```dockerfile
# src/backend/services/[service]/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Change ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

CMD ["npm", "start"]
```

### Docker Compose for Development
```yaml
# src/backend/services/[service]/docker-compose.yml
version: '3.8'

services:
  [service-name]:
    build: .
    ports:
      - "${PORT}:${PORT}"
    environment:
      - NODE_ENV=development
      - PORT=${PORT}
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
      - /app/node_modules
    networks:
      - ai-trading-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ai_trading
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - ai-trading-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - ai-trading-network

networks:
  ai-trading-network:
    driver: bridge

volumes:
  postgres_data:
```

## Implementation Coordination

### Daily Execution Protocol
```bash
# Start of day
npx claude-flow@alpha hooks session-restore --session-id "level-2-connectivity"
npx claude-flow@alpha hooks pre-task --description "[Service Implementation Day X]"

# During implementation
npx claude-flow@alpha hooks post-edit --file "[service-file]" --memory-key "connectivity/business-services/[service]/[component]"
npx claude-flow@alpha hooks notify --message "[Progress update]"

# End of day
npx claude-flow@alpha hooks post-task --task-id "[task-id]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

### Performance Validation Checklist
- [ ] Service startup time: <10 seconds
- [ ] API response time: <50ms (95th percentile)
- [ ] Database query time: <10ms (average)
- [ ] Multi-tenant overhead: <15ms
- [ ] Memory usage: <512MB per service
- [ ] CPU usage: <70% under normal load

This template provides the foundation for implementing all 5 business services with consistent architecture, multi-tenant support, and proper coordination protocols.