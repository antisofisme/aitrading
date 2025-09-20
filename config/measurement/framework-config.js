/**
 * Comprehensive Measurement Framework Configuration
 * Central configuration for all measurement and validation components
 */

const frameworkConfig = {
  // Global framework settings
  global: {
    environment: process.env.NODE_ENV || 'development',
    logLevel: process.env.LOG_LEVEL || 'info',
    timezone: 'UTC',
    precision: 6, // Decimal places for calculations
    enableRealTimeUpdates: true,
    enableCrossValidation: true,
    enableAlerts: true
  },

  // Orchestrator configuration
  orchestrator: {
    enableBaseline: true,
    enableCalibration: true,
    enableRiskTracking: true,
    enableStatisticalTesting: true,
    enableABTesting: true,

    // Coordination intervals
    syncInterval: 60000, // 1 minute
    analysisInterval: 300000, // 5 minutes
    reportingInterval: 3600000, // 1 hour

    // Quality control
    minDataQuality: 0.8,
    maxDataLatency: 300000, // 5 minutes
    maxBufferSize: 1000,
    dataRetentionPeriod: 86400000, // 24 hours

    // Alert thresholds
    alertThresholds: {
      componentError: 'high',
      dataQuality: 0.7,
      calibrationDrift: 0.1,
      riskMetricAlert: 'medium'
    }
  },

  // Baseline metrics configuration
  baseline: {
    samplingInterval: 1000, // 1 second
    rollingWindowSize: 3600, // 1 hour
    metricsRetention: 86400000, // 24 hours

    // Metrics to track
    enabledMetrics: [
      'total_return',
      'sharpe_ratio',
      'max_drawdown',
      'win_rate',
      'profit_factor',
      'volatility',
      'order_fill_rate',
      'slippage',
      'var_95',
      'var_99'
    ],

    // Alert thresholds
    alertThresholds: {
      sharpe_ratio: { min: 0.5, max: 3.0 },
      max_drawdown: { min: 0, max: 0.20 },
      win_rate: { min: 0.4, max: 0.8 },
      volatility: { min: 0.05, max: 0.30 }
    },

    // Calculation parameters
    riskFreeRate: 0.02, // 2% annual
    tradingDaysPerYear: 252
  },

  // Probability calibration configuration
  calibration: {
    binCount: 10,
    minSampleSize: 100,
    confidenceLevel: 0.95,
    slidingWindowSize: 1000,
    recalibrationThreshold: 0.1,

    // Quality thresholds
    brierScoreThreshold: 0.25,
    calibrationErrorThreshold: 0.05,
    reliabilityThreshold: 0.02,

    // Monitoring settings
    evaluationInterval: 3600000, // 1 hour
    driftDetectionEnabled: true,
    autoRecalibrationEnabled: false,

    // Notification settings
    notifyOnDrift: true,
    notifyOnPoorCalibration: true,
    calibrationReportFrequency: 86400000 // Daily
  },

  // Risk-adjusted performance configuration
  riskTracking: {
    riskFreeRate: 0.02, // 2% annual
    benchmarkReturn: 0.08, // 8% annual
    confidenceLevel: 0.95,
    lookbackPeriod: 252, // Trading days
    rebalancingFrequency: 'daily',

    // Risk metrics thresholds
    alertThresholds: {
      maxDrawdown: 0.15, // 15%
      sharpeRatio: 0.5,
      sortinoRatio: 0.7,
      var95: 0.05, // 5%
      beta: { min: 0.5, max: 1.5 },
      trackingError: 0.10 // 10%
    },

    // Performance calculation settings
    annualizationFactor: 252,
    confidenceIntervalMethod: 'bootstrap',
    bootstrapIterations: 1000,

    // Monitoring frequency
    updateFrequency: 'real_time',
    reportingFrequency: 'daily',
    alertEnabled: true
  },

  // Statistical testing configuration
  statisticalTesting: {
    confidenceLevel: 0.95,
    minSampleSize: 100,
    bootstrapIterations: 1000,
    pValueThreshold: 0.05,
    effectSizeThreshold: 0.2,
    multipleTestingCorrection: 'bonferroni',

    // Test suites
    defaultTestSuite: [
      'ttest_one_sample',
      'shapiro_wilk',
      'ljung_box',
      'jarque_bera'
    ],

    comparisonTestSuite: [
      'ttest_two_sample',
      'welch_ttest',
      'mann_whitney_u',
      'levene_test',
      'kolmogorov_smirnov'
    ],

    comprehensiveTestSuite: [
      'ttest_one_sample',
      'ttest_two_sample',
      'welch_ttest',
      'paired_ttest',
      'wilcoxon_signed_rank',
      'mann_whitney_u',
      'shapiro_wilk',
      'kolmogorov_smirnov',
      'levene_test',
      'ljung_box',
      'jarque_bera',
      'bootstrap_mean'
    ],

    // Validation settings
    enableCrossValidation: true,
    validationFrequency: 'weekly',
    archiveResults: true,
    maxResultsHistory: 100
  },

  // A/B testing configuration
  abTesting: {
    defaultSplitRatio: 0.5,
    minSampleSize: 100,
    maxTestDuration: 30 * 24 * 60 * 60 * 1000, // 30 days
    significanceLevel: 0.05,
    powerLevel: 0.8,
    minimumDetectableEffect: 0.05, // 5%

    // Early stopping settings
    earlyStoppingEnabled: true,
    interimAnalysisFrequency: 24 * 60 * 60 * 1000, // Daily
    futilityThreshold: 0.1,
    efficacyThreshold: 0.01,

    // Rollout strategies
    rolloutStrategies: {
      gradual: {
        stages: [
          { percentage: 0.01, duration: 1 * 24 * 60 * 60 * 1000 },
          { percentage: 0.05, duration: 2 * 24 * 60 * 60 * 1000 },
          { percentage: 0.10, duration: 3 * 24 * 60 * 60 * 1000 },
          { percentage: 0.25, duration: 7 * 24 * 60 * 60 * 1000 },
          { percentage: 0.50, duration: 14 * 24 * 60 * 60 * 1000 },
          { percentage: 1.00, duration: null }
        ]
      },
      canary: {
        stages: [
          { percentage: 0.05, duration: 7 * 24 * 60 * 60 * 1000 },
          { percentage: 1.00, duration: null }
        ]
      },
      blueGreen: {
        stages: [
          { percentage: 0.50, duration: null }
        ]
      }
    },

    // Default metrics to track
    defaultPrimaryMetric: 'total_return',
    defaultSecondaryMetrics: [
      'sharpe_ratio',
      'max_drawdown',
      'volatility',
      'win_rate'
    ],

    // Monitoring settings
    monitoringEnabled: true,
    healthCheckInterval: 3600000, // 1 hour
    autoAnalysisEnabled: true,
    reportGenerationEnabled: true
  },

  // Data storage configuration
  storage: {
    // Memory storage settings
    maxMemorySize: 1000, // Maximum items in memory
    compressionEnabled: true,
    encryptionEnabled: false,

    // Persistence settings
    persistenceEnabled: true,
    persistenceInterval: 300000, // 5 minutes
    backupEnabled: true,
    backupInterval: 3600000, // 1 hour
    maxBackupFiles: 24,

    // Data retention
    dataRetentionPolicies: {
      baseline: 7 * 24 * 60 * 60 * 1000, // 7 days
      calibration: 30 * 24 * 60 * 60 * 1000, // 30 days
      riskTracking: 30 * 24 * 60 * 60 * 1000, // 30 days
      statisticalTesting: 90 * 24 * 60 * 60 * 1000, // 90 days
      abTesting: 180 * 24 * 60 * 60 * 1000 // 180 days
    }
  },

  // Logging and monitoring
  logging: {
    level: 'info',
    format: 'json',
    includeTimestamp: true,
    includeStackTrace: true,

    // Log destinations
    console: true,
    file: {
      enabled: true,
      path: './logs/measurement-framework.log',
      maxSize: '10MB',
      maxFiles: 5
    },

    // Remote logging
    remote: {
      enabled: false,
      endpoint: null,
      apiKey: null
    }
  },

  // Performance monitoring
  performance: {
    enableMetrics: true,
    metricsInterval: 60000, // 1 minute
    enableProfiling: false,

    // Performance thresholds
    thresholds: {
      processingLatency: 1000, // 1 second
      memoryUsage: 500 * 1024 * 1024, // 500 MB
      cpuUsage: 80, // 80%
      errorRate: 0.05 // 5%
    },

    // Alert settings
    alertOnThresholdExceeded: true,
    alertCooldownPeriod: 300000 // 5 minutes
  },

  // Integration settings
  integration: {
    // External APIs
    apis: {
      rateLimit: 100, // requests per minute
      timeout: 30000, // 30 seconds
      retryAttempts: 3,
      retryDelay: 1000 // 1 second
    },

    // Webhook notifications
    webhooks: {
      enabled: false,
      endpoints: [],
      events: [
        'test_completed',
        'calibration_drift',
        'risk_alert',
        'validation_failed'
      ]
    },

    // Email notifications
    email: {
      enabled: false,
      smtp: {
        host: null,
        port: 587,
        secure: false,
        auth: {
          user: null,
          pass: null
        }
      },
      templates: {
        testCompletion: null,
        riskAlert: null,
        calibrationDrift: null
      }
    }
  },

  // Security settings
  security: {
    enableEncryption: false,
    encryptionKey: null,
    enableAuthentication: false,
    tokenExpiry: 3600000, // 1 hour

    // Access control
    accessControl: {
      enabled: false,
      roles: ['admin', 'analyst', 'viewer'],
      permissions: {
        admin: ['read', 'write', 'delete', 'configure'],
        analyst: ['read', 'write'],
        viewer: ['read']
      }
    },

    // Audit logging
    auditLogging: {
      enabled: true,
      includeDataAccess: false,
      includeConfigChanges: true,
      retentionPeriod: 90 * 24 * 60 * 60 * 1000 // 90 days
    }
  },

  // Development and testing
  development: {
    enableDebugMode: process.env.NODE_ENV === 'development',
    enableTestData: false,
    enableMockComponents: false,
    testDataSize: 1000,

    // Performance testing
    loadTesting: {
      enabled: false,
      maxConcurrentUsers: 100,
      testDuration: 300000, // 5 minutes
      rampUpTime: 60000 // 1 minute
    }
  }
};

// Environment-specific overrides
const environmentOverrides = {
  development: {
    global: {
      logLevel: 'debug'
    },
    orchestrator: {
      syncInterval: 30000, // 30 seconds
      analysisInterval: 120000, // 2 minutes
      reportingInterval: 600000 // 10 minutes
    },
    development: {
      enableDebugMode: true,
      enableTestData: true
    }
  },

  production: {
    global: {
      logLevel: 'warn'
    },
    security: {
      enableEncryption: true,
      enableAuthentication: true,
      auditLogging: {
        enabled: true,
        includeDataAccess: true
      }
    },
    performance: {
      enableProfiling: true
    }
  },

  testing: {
    global: {
      logLevel: 'error'
    },
    storage: {
      persistenceEnabled: false,
      backupEnabled: false
    },
    development: {
      enableMockComponents: true,
      enableTestData: true
    }
  }
};

// Apply environment-specific overrides
function applyEnvironmentOverrides(config, env) {
  const overrides = environmentOverrides[env];
  if (!overrides) return config;

  function deepMerge(target, source) {
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        target[key] = target[key] || {};
        deepMerge(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
    return target;
  }

  return deepMerge({ ...config }, overrides);
}

// Export final configuration
const finalConfig = applyEnvironmentOverrides(frameworkConfig, frameworkConfig.global.environment);

module.exports = finalConfig;