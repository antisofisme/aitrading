/**
 * Integration Test Configuration
 * Centralized configuration for all LEVEL 1 Foundation service tests
 */

require('dotenv').config();

const config = {
  // Test environment settings
  environment: {
    timeout: 30000, // 30 seconds default timeout
    retries: 3,
    parallel: false, // Run tests sequentially for stability
    verbose: true
  },

  // API Gateway configuration (Port 3001)
  apiGateway: {
    baseUrl: 'http://localhost:3001',
    endpoints: {
      health: '/health',
      api: '/api',
      auth: '/api/auth',
      integration: '/api/integration/central-hub'
    },
    expectedPort: 3001,
    expectedStatus: 200
  },

  // Database Service configuration (Port 8008)
  databaseService: {
    baseUrl: 'http://localhost:8008',
    endpoints: {
      health: '/health',
      info: '/api/info',
      users: '/api/users',
      query: '/api/query',
      migrate: '/api/migrate'
    },
    expectedPort: 8008,
    databases: {
      main: {
        host: process.env.DB_HOST || 'localhost',
        port: process.env.DB_PORT || 5432,
        database: process.env.DB_NAME || 'aitrading_main',
        user: process.env.DB_USER || 'postgres',
        password: process.env.DB_PASSWORD || 'postgres'
      },
      auth: {
        host: process.env.AUTH_DB_HOST || 'localhost',
        port: process.env.AUTH_DB_PORT || 5432,
        database: process.env.AUTH_DB_NAME || 'aitrading_auth',
        user: process.env.AUTH_DB_USER || 'postgres',
        password: process.env.AUTH_DB_PASSWORD || 'postgres'
      },
      trading: {
        host: process.env.TRADING_DB_HOST || 'localhost',
        port: process.env.TRADING_DB_PORT || 5432,
        database: process.env.TRADING_DB_NAME || 'aitrading_trading',
        user: process.env.TRADING_DB_USER || 'postgres',
        password: process.env.TRADING_DB_PASSWORD || 'postgres'
      },
      market: {
        host: process.env.MARKET_DB_HOST || 'localhost',
        port: process.env.MARKET_DB_PORT || 5432,
        database: process.env.MARKET_DB_NAME || 'aitrading_market',
        user: process.env.MARKET_DB_USER || 'postgres',
        password: process.env.MARKET_DB_PASSWORD || 'postgres'
      },
      analytics: {
        host: process.env.ANALYTICS_DB_HOST || 'localhost',
        port: process.env.ANALYTICS_DB_PORT || 5432,
        database: process.env.ANALYTICS_DB_NAME || 'aitrading_analytics',
        user: process.env.ANALYTICS_DB_USER || 'postgres',
        password: process.env.ANALYTICS_DB_PASSWORD || 'postgres'
      }
    }
  },

  // Data Bridge Service configuration (Dynamic port, likely 5000 series)
  dataBridge: {
    baseUrl: 'http://localhost:5001',
    wsUrl: 'ws://localhost:5001/ws',
    endpoints: {
      health: '/health',
      status: '/api/status',
      symbols: '/api/symbols',
      marketData: '/api/market-data'
    },
    expectedPort: 5001,
    websocket: {
      enabled: true,
      pingInterval: 30000,
      timeout: 60000
    }
  },

  // Central Hub Service configuration (Port 7000)
  centralHub: {
    baseUrl: 'http://localhost:7000',
    endpoints: {
      health: '/health',
      services: '/api/services',
      register: '/api/services/register',
      discovery: '/api/services/discovery',
      status: '/api/status'
    },
    expectedPort: 7000,
    expectedServices: [
      'api-gateway',
      'database-service',
      'data-bridge',
      'central-hub'
    ]
  },

  // Workspace Service (Configuration orchestrator)
  workspace: {
    configFiles: [
      '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/api-gateway/config/gateway.config.js',
      '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/database-service/config/database.config.js',
      '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/data-bridge/config/config.js',
      '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/central-hub/config/hub.config.js'
    ],
    expectedEnvVars: [
      'NODE_ENV',
      'DB_HOST',
      'DB_PORT',
      'GATEWAY_PORT',
      'CENTRAL_HUB_URL'
    ]
  },

  // Test data and credentials
  testData: {
    admin: {
      email: 'admin@aitrading.com',
      password: 'Admin123!'
    },
    user: {
      email: 'user@aitrading.com',
      password: 'User123!'
    },
    testUser: {
      email: 'test@integration.com',
      password: 'Test123!',
      name: 'Integration Test User'
    }
  },

  // Performance thresholds
  performance: {
    responseTime: {
      fast: 100,    // < 100ms
      acceptable: 500, // < 500ms
      slow: 2000    // < 2s
    },
    availability: {
      minimum: 0.99, // 99% uptime
      target: 0.999  // 99.9% uptime
    }
  },

  // Integration test flow configuration
  testFlow: {
    phases: [
      'connectivity',
      'authentication',
      'database',
      'service-discovery',
      'data-flow',
      'error-handling',
      'performance'
    ],
    dependencies: {
      'database': ['connectivity'],
      'authentication': ['connectivity', 'database'],
      'service-discovery': ['connectivity'],
      'data-flow': ['connectivity', 'database', 'service-discovery'],
      'error-handling': ['connectivity', 'database'],
      'performance': ['connectivity', 'database', 'authentication']
    }
  }
};

// Validation
if (!config.apiGateway.baseUrl) {
  throw new Error('API Gateway base URL is required');
}

if (!config.databaseService.baseUrl) {
  throw new Error('Database Service base URL is required');
}

module.exports = config;