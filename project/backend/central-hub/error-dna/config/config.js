const path = require('path');

module.exports = {
  // Service Configuration
  service: {
    name: 'ErrorDNA',
    version: '1.0.0',
    port: process.env.ERROR_DNA_PORT || 3005,
    environment: process.env.NODE_ENV || 'development'
  },

  // Storage Configuration
  storage: {
    baseDir: process.env.ERROR_STORAGE_DIR || path.join(__dirname, '..', 'storage'),
    errorLogFile: 'errors.json',
    patternFile: 'patterns.json',
    metricsFile: 'metrics.json',
    maxFileSize: '10MB',
    retentionDays: 30
  },

  // Pattern Detection Configuration
  patternDetection: {
    enabled: true,
    windowSize: 100, // Number of recent errors to analyze
    similarityThreshold: 0.8, // Threshold for pattern matching
    minOccurrences: 3, // Minimum occurrences to establish a pattern
    analysisInterval: 300000, // 5 minutes in milliseconds
    maxPatterns: 1000 // Maximum patterns to store
  },

  // Notification Configuration
  notifications: {
    enabled: true,
    channels: {
      email: {
        enabled: false,
        smtp: {
          host: process.env.SMTP_HOST,
          port: process.env.SMTP_PORT || 587,
          secure: false,
          auth: {
            user: process.env.SMTP_USER,
            pass: process.env.SMTP_PASS
          }
        }
      },
      webhook: {
        enabled: true,
        url: process.env.WEBHOOK_URL || 'http://localhost:3001/api/notifications',
        timeout: 5000
      },
      slack: {
        enabled: false,
        webhookUrl: process.env.SLACK_WEBHOOK_URL
      }
    }
  },

  // Recovery Configuration
  recovery: {
    enabled: true,
    strategies: {
      retry: {
        enabled: true,
        maxAttempts: 3,
        backoffMultiplier: 2,
        initialDelay: 1000
      },
      fallback: {
        enabled: true,
        timeout: 30000
      },
      circuit_breaker: {
        enabled: true,
        threshold: 5,
        timeout: 60000,
        resetTimeout: 300000
      }
    }
  },

  // Integration Configuration
  integration: {
    centralHub: {
      baseUrl: process.env.CENTRAL_HUB_URL || 'http://localhost:3001',
      apiKey: process.env.CENTRAL_HUB_API_KEY,
      timeout: 10000
    },
    importManager: {
      baseUrl: process.env.IMPORT_MANAGER_URL || 'http://localhost:3003',
      apiKey: process.env.IMPORT_MANAGER_API_KEY,
      timeout: 10000
    }
  },

  // Logging Configuration
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: 'json',
    maxFiles: 5,
    maxSize: '10m',
    datePattern: 'YYYY-MM-DD',
    filename: 'error-dna-%DATE%.log'
  },

  // Performance Configuration
  performance: {
    maxConcurrentAnalysis: 10,
    batchSize: 50,
    memoryThreshold: 0.8,
    cpuThreshold: 0.9
  }
};