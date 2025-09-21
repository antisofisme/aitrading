require('dotenv').config();

const config = {
  environment: process.env.NODE_ENV || 'development',

  server: {
    host: process.env.API_GATEWAY_HOST || 'localhost',
    port: parseInt(process.env.API_GATEWAY_PORT) || 8000
  },

  services: {
    auth: {
      url: process.env.AUTH_SERVICE_URL || 'http://localhost:8001',
      healthPath: '/health'
    },
    trading: {
      url: process.env.TRADING_SERVICE_URL || 'http://localhost:8002',
      healthPath: '/health'
    },
    hub: {
      url: process.env.HUB_SERVICE_URL || 'http://localhost:8003',
      healthPath: '/health'
    }
  },

  cors: {
    origins: process.env.CORS_ORIGINS ?
      process.env.CORS_ORIGINS.split(',') :
      ['http://localhost:3000', 'http://localhost:3001']
  },

  rateLimit: {
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
    max: parseInt(process.env.RATE_LIMIT_MAX) || 100 // limit each IP to 100 requests per windowMs
  },

  proxy: {
    timeout: parseInt(process.env.PROXY_TIMEOUT) || 30000 // 30 seconds
  },

  auth: {
    jwtSecret: process.env.JWT_SECRET || 'your-secret-key-change-this',
    jwtExpiry: process.env.JWT_EXPIRY || '24h'
  },

  registry: {
    hubUrl: process.env.REGISTRY_HUB_URL || 'http://localhost:8003',
    registrationPath: '/api/registry/register',
    heartbeatInterval: parseInt(process.env.HEARTBEAT_INTERVAL) || 30000 // 30 seconds
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'json'
  }
};

module.exports = config;