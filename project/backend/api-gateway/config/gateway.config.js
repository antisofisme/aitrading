require('dotenv').config();

const config = {
  server: {
    port: parseInt(process.env.GATEWAY_PORT) || 8000,
    host: process.env.GATEWAY_HOST || '0.0.0.0',
    bodyLimit: process.env.BODY_LIMIT || '10mb',
    environment: process.env.NODE_ENV || 'development'
  },

  cors: {
    origins: process.env.CORS_ORIGINS ?
      process.env.CORS_ORIGINS.split(',') :
      ['http://localhost:3000', 'http://localhost:3001']
  },

  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX) || 100 // requests per window
  },

  services: {
    auth: {
      url: process.env.AUTH_SERVICE_URL || 'http://localhost:8001',
      timeout: parseInt(process.env.AUTH_SERVICE_TIMEOUT) || 30000
    },
    users: {
      url: process.env.USER_SERVICE_URL || 'http://localhost:8002',
      timeout: parseInt(process.env.USER_SERVICE_TIMEOUT) || 30000
    },
    trading: {
      url: process.env.TRADING_SERVICE_URL || 'http://localhost:8003',
      timeout: parseInt(process.env.TRADING_SERVICE_TIMEOUT) || 60000
    },
    market: {
      url: process.env.MARKET_SERVICE_URL || 'http://localhost:8004',
      timeout: parseInt(process.env.MARKET_SERVICE_TIMEOUT) || 30000
    },
    ai: {
      url: process.env.AI_SERVICE_URL || 'http://localhost:8005',
      timeout: parseInt(process.env.AI_SERVICE_TIMEOUT) || 120000
    },
    notifications: {
      url: process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:8006',
      timeout: parseInt(process.env.NOTIFICATION_SERVICE_TIMEOUT) || 30000
    },
    centralHub: {
      url: process.env.CENTRAL_HUB_URL || 'http://localhost:7000',
      timeout: parseInt(process.env.CENTRAL_HUB_TIMEOUT) || 30000
    }
  },

  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT) || 6379,
    password: process.env.REDIS_PASSWORD || '',
    db: parseInt(process.env.REDIS_DB) || 0,
    maxRetriesPerRequest: 3,
    retryDelayOnFailover: 100,
    enableReadyCheck: false,
    maxRetriesPerRequest: null
  },

  jwt: {
    secret: process.env.JWT_SECRET || 'your-super-secret-key-change-in-production',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
    issuer: process.env.JWT_ISSUER || 'ai-trading-platform',
    audience: process.env.JWT_AUDIENCE || 'ai-trading-users'
  },

  security: {
    bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS) || 12,
    maxLoginAttempts: parseInt(process.env.MAX_LOGIN_ATTEMPTS) || 5,
    lockoutTime: parseInt(process.env.LOCKOUT_TIME) || 15 * 60 * 1000, // 15 minutes
    passwordMinLength: parseInt(process.env.PASSWORD_MIN_LENGTH) || 8
  },

  monitoring: {
    metricsEnabled: process.env.METRICS_ENABLED !== 'false',
    metricsPort: parseInt(process.env.METRICS_PORT) || 9090,
    healthCheckInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL) || 30000,
    logLevel: process.env.LOG_LEVEL || 'info'
  },

  circuitBreaker: {
    threshold: parseInt(process.env.CIRCUIT_BREAKER_THRESHOLD) || 5,
    timeout: parseInt(process.env.CIRCUIT_BREAKER_TIMEOUT) || 60000,
    resetTimeout: parseInt(process.env.CIRCUIT_BREAKER_RESET_TIMEOUT) || 30000
  }
};

// Validation
if (config.server.port < 1 || config.server.port > 65535) {
  throw new Error('Invalid port number. Must be between 1 and 65535.');
}

if (config.jwt.secret === 'your-super-secret-key-change-in-production' &&
    config.server.environment === 'production') {
  throw new Error('JWT secret must be changed in production environment');
}

module.exports = config;