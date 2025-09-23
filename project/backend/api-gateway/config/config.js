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

  // Database Configuration (Plan2 Multi-Database Architecture)
  database: {
    postgresql: {
      host: process.env.POSTGRES_HOST || 'localhost',
      port: parseInt(process.env.POSTGRES_PORT) || 5432,
      database: process.env.POSTGRES_DB || 'aitrading_operational',
      user: process.env.POSTGRES_USER || 'postgres',
      password: process.env.POSTGRES_PASSWORD || '',
      max: parseInt(process.env.POSTGRES_POOL_MAX) || 20
    },
    dragonflydb: {
      host: process.env.DRAGONFLY_HOST || 'localhost',
      port: parseInt(process.env.DRAGONFLY_PORT) || 6379,
      password: process.env.DRAGONFLY_PASSWORD || '',
      maxRetriesPerRequest: parseInt(process.env.DRAGONFLY_MAX_RETRIES) || 3,
      retryDelayOnFailover: parseInt(process.env.DRAGONFLY_RETRY_DELAY) || 100
    },
    clickhouse: {
      host: process.env.CLICKHOUSE_HOST || 'localhost',
      port: parseInt(process.env.CLICKHOUSE_PORT) || 8123,
      database: process.env.CLICKHOUSE_DB || 'aitrading_analytics',
      user: process.env.CLICKHOUSE_USER || 'default',
      password: process.env.CLICKHOUSE_PASSWORD || ''
    },
    weaviate: {
      scheme: process.env.WEAVIATE_SCHEME || 'http',
      host: process.env.WEAVIATE_HOST || 'localhost',
      port: parseInt(process.env.WEAVIATE_PORT) || 8080,
      apiKey: process.env.WEAVIATE_API_KEY || ''
    },
    arangodb: {
      url: process.env.ARANGO_URL || 'http://localhost:8529',
      database: process.env.ARANGO_DB || 'aitrading_graph',
      username: process.env.ARANGO_USER || 'root',
      password: process.env.ARANGO_PASSWORD || ''
    }
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