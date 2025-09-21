/**
 * JWT Configuration
 * Centralized JWT settings and token management
 */

require('dotenv').config();

const jwtConfig = {
  // JWT Secrets
  accessTokenSecret: process.env.JWT_SECRET || 'fallback-secret-change-in-production',
  refreshTokenSecret: process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret-change-in-production',

  // Token Expiry
  accessTokenExpiry: process.env.JWT_ACCESS_EXPIRY || '15m',
  refreshTokenExpiry: process.env.JWT_REFRESH_EXPIRY || '7d',

  // Token Options
  accessTokenOptions: {
    issuer: 'ai-trading-platform',
    audience: 'api-gateway',
    algorithm: 'HS256'
  },

  refreshTokenOptions: {
    issuer: 'ai-trading-platform',
    audience: 'refresh-service',
    algorithm: 'HS256'
  },

  // Security Settings
  bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS) || 12,

  // Rate Limiting
  rateLimitWindow: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  rateLimitMax: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,

  // CORS Settings
  allowedOrigins: process.env.ALLOWED_ORIGINS
    ? process.env.ALLOWED_ORIGINS.split(',')
    : ['http://localhost:3000', 'http://localhost:3001'],

  // Central Hub Integration
  centralHub: {
    url: process.env.CENTRAL_HUB_URL || 'http://localhost:3000',
    apiKey: process.env.CENTRAL_HUB_API_KEY || 'central-hub-api-key',
    timeout: 5000
  }
};

// Validation
if (process.env.NODE_ENV === 'production') {
  if (jwtConfig.accessTokenSecret === 'fallback-secret-change-in-production') {
    throw new Error('JWT_SECRET must be set in production');
  }
  if (jwtConfig.refreshTokenSecret === 'fallback-refresh-secret-change-in-production') {
    throw new Error('JWT_REFRESH_SECRET must be set in production');
  }
}

module.exports = jwtConfig;