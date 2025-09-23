require('dotenv').config();

const config = {
  server: {
    port: process.env.PORT || 3001,
    host: process.env.HOST || '0.0.0.0',
    environment: process.env.NODE_ENV || 'development'
  },

  cors: {
    allowedOrigins: process.env.CORS_ORIGINS ?
      process.env.CORS_ORIGINS.split(',') :
      ['http://localhost:3000', 'http://localhost:3001']
  },

  mt5: {
    server: process.env.MT5_SERVER || 'localhost',
    port: process.env.MT5_PORT || 8222,
    login: process.env.MT5_LOGIN || '',
    password: process.env.MT5_PASSWORD || '',
    timeout: parseInt(process.env.MT5_TIMEOUT) || 30000,
    reconnectInterval: parseInt(process.env.MT5_RECONNECT_INTERVAL) || 5000,
    maxReconnectAttempts: parseInt(process.env.MT5_MAX_RECONNECT_ATTEMPTS) || 10
  },

  // DragonflyDB (High-Performance Cache - replaces Redis)
  dragonflydb: {
    host: process.env.DRAGONFLY_HOST || 'localhost',
    port: parseInt(process.env.DRAGONFLY_PORT) || 6379,
    password: process.env.DRAGONFLY_PASSWORD || '',
    maxRetriesPerRequest: parseInt(process.env.DRAGONFLY_MAX_RETRIES) || 3,
    retryDelayOnFailover: parseInt(process.env.DRAGONFLY_RETRY_DELAY) || 100,
    keyPrefix: process.env.DRAGONFLY_KEY_PREFIX || 'data-bridge:'
  },

  // Legacy Redis support (for backward compatibility)
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT) || 6379,
    password: process.env.REDIS_PASSWORD || '',
    db: parseInt(process.env.REDIS_DB) || 0,
    keyPrefix: process.env.REDIS_KEY_PREFIX || 'data-bridge:'
  },

  // ClickHouse (Time-Series Analytics)
  clickhouse: {
    host: process.env.CLICKHOUSE_HOST || 'localhost',
    port: parseInt(process.env.CLICKHOUSE_PORT) || 8123,
    database: process.env.CLICKHOUSE_DB || 'aitrading_analytics',
    user: process.env.CLICKHOUSE_USER || 'default',
    password: process.env.CLICKHOUSE_PASSWORD || ''
  },

  // PostgreSQL (Operational Data)
  postgresql: {
    host: process.env.POSTGRES_HOST || 'localhost',
    port: parseInt(process.env.POSTGRES_PORT) || 5432,
    database: process.env.POSTGRES_DB || 'aitrading_operational',
    user: process.env.POSTGRES_USER || 'postgres',
    password: process.env.POSTGRES_PASSWORD || '',
    max: parseInt(process.env.POSTGRES_POOL_MAX) || 20
  },

  logging: {
    level: process.env.LOG_LEVEL || 'info',
    file: process.env.LOG_FILE || 'logs/data-bridge.log',
    maxSize: process.env.LOG_MAX_SIZE || '10m',
    maxFiles: parseInt(process.env.LOG_MAX_FILES) || 5,
    format: process.env.LOG_FORMAT || 'json'
  },

  websocket: {
    maxConnections: parseInt(process.env.WS_MAX_CONNECTIONS) || 1000,
    pingInterval: parseInt(process.env.WS_PING_INTERVAL) || 30000,
    timeout: parseInt(process.env.WS_TIMEOUT) || 60000,
    compression: process.env.WS_COMPRESSION !== 'false'
  },

  data: {
    bufferSize: parseInt(process.env.DATA_BUFFER_SIZE) || 1000,
    flushInterval: parseInt(process.env.DATA_FLUSH_INTERVAL) || 1000,
    retentionPeriod: parseInt(process.env.DATA_RETENTION_PERIOD) || 86400000, // 24 hours
    compressionLevel: parseInt(process.env.DATA_COMPRESSION_LEVEL) || 6
  },

  security: {
    rateLimitWindow: parseInt(process.env.RATE_LIMIT_WINDOW) || 900000, // 15 minutes
    rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX) || 100,
    allowedIPs: process.env.ALLOWED_IPS ?
      process.env.ALLOWED_IPS.split(',') :
      [],
    jwtSecret: process.env.JWT_SECRET || 'your-secret-key',
    jwtExpiration: process.env.JWT_EXPIRATION || '1h'
  },

  monitoring: {
    healthCheckInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL) || 60000,
    metricsEnabled: process.env.METRICS_ENABLED !== 'false',
    alertingEnabled: process.env.ALERTING_ENABLED !== 'false'
  }
};

// Validation
const requiredEnvVars = ['MT5_LOGIN', 'MT5_PASSWORD'];
const missingVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingVars.length > 0 && config.server.environment === 'production') {
  console.error('Missing required environment variables:', missingVars);
  process.exit(1);
}

module.exports = config;