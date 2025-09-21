import dotenv from 'dotenv';
import { AppConfig, DatabaseConfig, LogLevel } from '@/types';

// Load environment variables
dotenv.config();

const requiredEnvVars = [
  'JWT_SECRET',
  'JWT_REFRESH_SECRET',
  'POSTGRES_HOST',
  'POSTGRES_DB',
  'POSTGRES_USER',
  'POSTGRES_PASSWORD'
];

// Validate required environment variables
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Required environment variable ${envVar} is not set`);
  }
}

// Helper function to parse boolean environment variables
const parseBoolean = (value: string | undefined, defaultValue: boolean = false): boolean => {
  if (!value) return defaultValue;
  return value.toLowerCase() === 'true';
};

// Helper function to parse number environment variables
const parseNumber = (value: string | undefined, defaultValue: number): number => {
  if (!value) return defaultValue;
  const parsed = parseInt(value, 10);
  return isNaN(parsed) ? defaultValue : parsed;
};

// Helper function to parse string array
const parseStringArray = (value: string | undefined, defaultValue: string[] = []): string[] => {
  if (!value) return defaultValue;
  return value.split(',').map(item => item.trim()).filter(Boolean);
};

// PostgreSQL Configuration
const postgresConfig: DatabaseConfig = {
  host: process.env.POSTGRES_HOST!,
  port: parseNumber(process.env.POSTGRES_PORT, 5432),
  database: process.env.POSTGRES_DB!,
  username: process.env.POSTGRES_USER!,
  password: process.env.POSTGRES_PASSWORD!,
  ssl: parseBoolean(process.env.POSTGRES_SSL),
  pool: {
    min: parseNumber(process.env.POSTGRES_POOL_MIN, 2),
    max: parseNumber(process.env.POSTGRES_POOL_MAX, 20)
  }
};

// ClickHouse Configuration
const clickhouseConfig: DatabaseConfig = {
  host: process.env.CLICKHOUSE_HOST || 'localhost',
  port: parseNumber(process.env.CLICKHOUSE_PORT, 8123),
  database: process.env.CLICKHOUSE_DB || 'aitrading_analytics',
  username: process.env.CLICKHOUSE_USER || 'default',
  password: process.env.CLICKHOUSE_PASSWORD || '',
  ssl: parseBoolean(process.env.CLICKHOUSE_SECURE)
};

// Application Configuration
export const config: AppConfig = {
  // Application
  port: parseNumber(process.env.PORT, 8000),
  nodeEnv: process.env.NODE_ENV || 'development',
  apiVersion: process.env.API_VERSION || 'v1',

  // CORS Configuration
  cors: {
    origin: process.env.CORS_ORIGIN ?
      process.env.CORS_ORIGIN.includes(',') ?
        parseStringArray(process.env.CORS_ORIGIN) :
        process.env.CORS_ORIGIN :
      'http://localhost:3000',
    credentials: parseBoolean(process.env.CORS_CREDENTIALS, true)
  },

  // JWT Configuration
  jwt: {
    secret: process.env.JWT_SECRET!,
    refreshSecret: process.env.JWT_REFRESH_SECRET!,
    expiresIn: process.env.JWT_EXPIRES_IN || '15m',
    refreshExpiresIn: process.env.JWT_REFRESH_EXPIRES_IN || '7d'
  },

  // Database Configuration
  database: {
    postgres: postgresConfig,
    clickhouse: clickhouseConfig,
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseNumber(process.env.REDIS_PORT, 6379),
      password: process.env.REDIS_PASSWORD,
      db: parseNumber(process.env.REDIS_DB, 0)
    }
  },

  // MT5 Integration Configuration
  mt5: {
    websocketHost: process.env.MT5_WEBSOCKET_HOST || 'localhost',
    websocketPort: parseNumber(process.env.MT5_WEBSOCKET_PORT, 8001),
    connectionTimeout: parseNumber(process.env.MT5_CONNECTION_TIMEOUT, 5000),
    retryAttempts: parseNumber(process.env.MT5_RETRY_ATTEMPTS, 3),
    poolSize: parseNumber(process.env.MT5_POOL_SIZE, 5)
  },

  // Security Configuration
  security: {
    bcryptRounds: parseNumber(process.env.BCRYPT_ROUNDS, 12),
    rateLimiting: {
      windowMs: parseNumber(process.env.RATE_LIMIT_WINDOW_MS, 900000), // 15 minutes
      max: parseNumber(process.env.RATE_LIMIT_MAX_REQUESTS, 100),
      message: 'Too many requests from this IP, please try again later.',
      skipSuccessfulRequests: parseBoolean(process.env.RATE_LIMIT_SKIP_SUCCESSFUL_REQUESTS, true)
    }
  },

  // Logging Configuration
  logging: {
    level: (process.env.LOG_LEVEL as LogLevel) || LogLevel.INFO,
    maxFiles: process.env.LOG_MAX_FILES || '30d',
    maxSize: process.env.LOG_MAX_SIZE || '100mb',
    compress: parseBoolean(process.env.LOG_COMPRESS, true)
  }
};

// Subscription Tier Configuration
export const subscriptionConfig = {
  tiers: {
    basic: {
      price: parseNumber(process.env.BASIC_TIER_PRICE, 49),
      features: parseStringArray(process.env.BASIC_TIER_FEATURES, ['basic_signals', 'email_support'])
    },
    pro: {
      price: parseNumber(process.env.PRO_TIER_PRICE, 199),
      features: parseStringArray(process.env.PRO_TIER_FEATURES, ['advanced_signals', 'priority_support', 'api_access'])
    },
    enterprise: {
      price: parseNumber(process.env.ENTERPRISE_TIER_PRICE, 999),
      features: parseStringArray(process.env.ENTERPRISE_TIER_FEATURES, ['all_features', 'dedicated_support', 'custom_integration'])
    }
  }
};

// Error DNA Configuration
export const errorDnaConfig = {
  enabled: parseBoolean(process.env.ERROR_DNA_ENABLED, true),
  apiKey: process.env.ERROR_DNA_API_KEY,
  projectId: process.env.ERROR_DNA_PROJECT_ID || 'aitrading-backend'
};

// Monitoring Configuration
export const monitoringConfig = {
  healthCheckInterval: parseNumber(process.env.HEALTH_CHECK_INTERVAL, 30000),
  performanceMonitoring: parseBoolean(process.env.PERFORMANCE_MONITORING, true),
  auditLogging: parseBoolean(process.env.AUDIT_LOGGING, true)
};

// Zero-Trust Security Configuration
export const securityConfig = {
  mutualTlsEnabled: parseBoolean(process.env.MUTUAL_TLS_ENABLED, false),
  certificatePath: process.env.CERTIFICATE_PATH || './certs/',
  privateKeyPath: process.env.PRIVATE_KEY_PATH || './certs/private/',
  securityHeadersEnabled: parseBoolean(process.env.SECURITY_HEADERS_ENABLED, true),
  cspEnabled: parseBoolean(process.env.CSP_ENABLED, true)
};

// Validate configuration
export const validateConfig = (): void => {
  const errors: string[] = [];

  // Validate JWT secrets strength
  if (config.jwt.secret.length < 32) {
    errors.push('JWT_SECRET must be at least 32 characters long');
  }

  if (config.jwt.refreshSecret.length < 32) {
    errors.push('JWT_REFRESH_SECRET must be at least 32 characters long');
  }

  // Validate database configuration
  if (!config.database.postgres.host) {
    errors.push('PostgreSQL host is required');
  }

  // Validate subscription configuration
  if (subscriptionConfig.tiers.basic.price <= 0) {
    errors.push('Basic tier price must be greater than 0');
  }

  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }
};

// Development mode helper
export const isDevelopment = (): boolean => config.nodeEnv === 'development';
export const isProduction = (): boolean => config.nodeEnv === 'production';
export const isTest = (): boolean => config.nodeEnv === 'test';

// Export default configuration
export default config;