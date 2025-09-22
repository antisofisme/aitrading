/**
 * Global Setup for Flow-Aware Error Handling Tests
 * Initializes test infrastructure, databases, and external dependencies
 */

const fs = require('fs').promises;
const path = require('path');

module.exports = async () => {
  console.log('🚀 Setting up Flow-Aware Error Handling Test Environment...');

  try {
    // Create test directories
    await createTestDirectories();

    // Initialize test databases
    await initializeTestDatabases();

    // Setup test services
    await setupTestServices();

    // Configure test environment variables
    await configureTestEnvironment();

    // Initialize performance baselines
    await initializePerformanceBaselines();

    // Setup monitoring and metrics
    await setupMonitoringInfrastructure();

    // Initialize chaos engineering tools
    await initializeChaosTools();

    // Setup test data
    await setupTestData();

    console.log('✅ Flow-Aware Error Handling Test Environment Ready');

  } catch (error) {
    console.error('❌ Failed to setup test environment:', error);
    throw error;
  }
};

async function createTestDirectories() {
  const directories = [
    'temp',
    'temp/logs',
    'temp/data',
    'temp/metrics',
    'temp/reports',
    'temp/coverage',
    'temp/artifacts'
  ];

  for (const dir of directories) {
    const dirPath = path.join(__dirname, '..', dir);
    try {
      await fs.mkdir(dirPath, { recursive: true });
    } catch (error) {
      if (error.code !== 'EEXIST') {
        throw error;
      }
    }
  }

  console.log('📁 Test directories created');
}

async function initializeTestDatabases() {
  // Mock database initialization for testing
  global.testDatabases = {
    flow_registry: {
      flows: new Map(),
      indexes: {
        by_service: new Map(),
        by_status: new Map(),
        by_time: new Map()
      }
    },
    health_monitor: {
      services: new Map(),
      health_history: new Map(),
      alerts: new Map()
    },
    impact_analyzer: {
      errors: new Map(),
      correlations: new Map(),
      ml_models: new Map()
    }
  };

  // Initialize test schemas
  const schemas = {
    flows: `
      CREATE TABLE IF NOT EXISTS flows (
        id VARCHAR PRIMARY KEY,
        service_id VARCHAR NOT NULL,
        status VARCHAR NOT NULL,
        timestamp BIGINT NOT NULL,
        metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_flows_service ON flows(service_id);
      CREATE INDEX IF NOT EXISTS idx_flows_status ON flows(status);
      CREATE INDEX IF NOT EXISTS idx_flows_timestamp ON flows(timestamp);
    `,
    health_checks: `
      CREATE TABLE IF NOT EXISTS health_checks (
        id SERIAL PRIMARY KEY,
        service_id VARCHAR NOT NULL,
        status VARCHAR NOT NULL,
        response_time INTEGER,
        timestamp BIGINT NOT NULL,
        metadata JSONB
      );
      CREATE INDEX IF NOT EXISTS idx_health_service ON health_checks(service_id);
      CREATE INDEX IF NOT EXISTS idx_health_timestamp ON health_checks(timestamp);
    `,
    errors: `
      CREATE TABLE IF NOT EXISTS errors (
        id VARCHAR PRIMARY KEY,
        service_id VARCHAR NOT NULL,
        error_type VARCHAR NOT NULL,
        severity VARCHAR NOT NULL,
        message TEXT,
        stack_trace TEXT,
        timestamp BIGINT NOT NULL,
        metadata JSONB
      );
      CREATE INDEX IF NOT EXISTS idx_errors_service ON errors(service_id);
      CREATE INDEX IF NOT EXISTS idx_errors_type ON errors(error_type);
      CREATE INDEX IF NOT EXISTS idx_errors_timestamp ON errors(timestamp);
    `
  };

  global.testSchemas = schemas;
  console.log('🗄️ Test databases initialized');
}

async function setupTestServices() {
  // Mock service registry for testing
  global.testServices = new Map();

  const mockServices = [
    {
      id: 'api-gateway',
      name: 'API Gateway',
      port: 3001,
      healthEndpoint: '/health',
      dependencies: [],
      criticality: 'high'
    },
    {
      id: 'auth-service',
      name: 'Authentication Service',
      port: 3002,
      healthEndpoint: '/health',
      dependencies: ['database'],
      criticality: 'high'
    },
    {
      id: 'trading-engine',
      name: 'Trading Engine',
      port: 3003,
      healthEndpoint: '/health',
      dependencies: ['auth-service', 'market-data', 'risk-engine'],
      criticality: 'critical'
    },
    {
      id: 'market-data',
      name: 'Market Data Service',
      port: 3004,
      healthEndpoint: '/health',
      dependencies: ['external-feed'],
      criticality: 'high'
    },
    {
      id: 'risk-engine',
      name: 'Risk Engine',
      port: 3005,
      healthEndpoint: '/health',
      dependencies: ['database', 'market-data'],
      criticality: 'high'
    },
    {
      id: 'portfolio-service',
      name: 'Portfolio Service',
      port: 3006,
      healthEndpoint: '/health',
      dependencies: ['database', 'trading-engine'],
      criticality: 'medium'
    },
    {
      id: 'notification-service',
      name: 'Notification Service',
      port: 3007,
      healthEndpoint: '/health',
      dependencies: ['message-queue'],
      criticality: 'low'
    },
    {
      id: 'database',
      name: 'Database Cluster',
      port: 5432,
      healthEndpoint: '/health',
      dependencies: [],
      criticality: 'critical'
    }
  ];

  for (const service of mockServices) {
    global.testServices.set(service.id, {
      ...service,
      status: 'healthy',
      responseTime: 100 + Math.random() * 50,
      errorRate: Math.random() * 0.01,
      availability: 0.99 + Math.random() * 0.01,
      lastCheck: Date.now()
    });
  }

  console.log('🔧 Test services configured');
}

async function configureTestEnvironment() {
  // Set test-specific environment variables
  process.env.NODE_ENV = 'test';
  process.env.LOG_LEVEL = 'error'; // Reduce log noise in tests
  process.env.METRICS_ENABLED = 'true';
  process.env.CHAOS_TESTING = 'enabled';
  process.env.PERFORMANCE_MONITORING = 'enabled';

  // Test timeouts
  process.env.HEALTH_CHECK_TIMEOUT = '5000';
  process.env.FLOW_TIMEOUT = '30000';
  process.env.ANALYSIS_TIMEOUT = '10000';

  // Test thresholds
  process.env.ERROR_RATE_THRESHOLD = '0.1';
  process.env.RESPONSE_TIME_THRESHOLD = '5000';
  process.env.AVAILABILITY_THRESHOLD = '0.95';

  // Mock external endpoints
  process.env.MOCK_EXTERNAL_SERVICES = 'true';
  process.env.EXTERNAL_API_BASE_URL = 'http://localhost:8080/mock';

  console.log('⚙️ Test environment configured');
}

async function initializePerformanceBaselines() {
  global.performanceBaselines = {
    flowRegistration: {
      p50: 10,    // 10ms
      p95: 50,    // 50ms
      p99: 100    // 100ms
    },
    healthCheck: {
      p50: 5,     // 5ms
      p95: 20,    // 20ms
      p99: 50     // 50ms
    },
    impactAnalysis: {
      p50: 100,   // 100ms
      p95: 500,   // 500ms
      p99: 1000   // 1000ms
    },
    queryResponse: {
      p50: 20,    // 20ms
      p95: 100,   // 100ms
      p99: 200    // 200ms
    },
    memoryUsage: {
      heapUsed: 100,      // 100MB baseline
      maxPerFlow: 2048,   // 2KB per flow
      maxTotal: 512       // 512MB total
    },
    throughput: {
      flowsPerSecond: 1000,
      queriesPerSecond: 500,
      healthChecksPerSecond: 200
    }
  };

  console.log('📊 Performance baselines established');
}

async function setupMonitoringInfrastructure() {
  // Mock metrics collection
  global.testMetrics = {
    counters: new Map(),
    gauges: new Map(),
    histograms: new Map(),
    summaries: new Map()
  };

  // Mock alerting system
  global.testAlerts = {
    active: new Map(),
    history: [],
    channels: ['console', 'test'],
    suppressions: new Map()
  };

  // Mock dashboards
  global.testDashboards = {
    flow_aware_debugging: {
      panels: [
        'flow_registration_rate',
        'error_analysis_latency',
        'health_check_success_rate',
        'cascade_failure_detection',
        'recovery_time_distribution'
      ]
    }
  };

  console.log('📈 Monitoring infrastructure initialized');
}

async function initializeChaosTools() {
  global.chaosTools = {
    failureInjectors: {
      network: {
        latency: (min, max) => min + Math.random() * (max - min),
        packetLoss: (probability) => Math.random() < probability,
        partition: (duration) => new Promise(resolve => setTimeout(resolve, duration))
      },
      service: {
        crash: (serviceId) => {
          const service = global.testServices.get(serviceId);
          if (service) {
            service.status = 'crashed';
            service.lastError = new Error('Service crashed');
          }
        },
        hang: (serviceId, duration) => {
          const service = global.testServices.get(serviceId);
          if (service) {
            service.status = 'hanging';
            setTimeout(() => {
              service.status = 'healthy';
            }, duration);
          }
        },
        slowdown: (serviceId, factor) => {
          const service = global.testServices.get(serviceId);
          if (service) {
            service.responseTime *= factor;
          }
        }
      },
      resource: {
        memoryPressure: (targetMB) => {
          const arrays = [];
          try {
            while (arrays.length < targetMB) {
              arrays.push(new Array(1024 * 1024).fill('X'));
            }
          } catch (e) {
            // Memory exhausted
          }
          return () => arrays.length = 0;
        },
        cpuBurn: (duration) => {
          const end = Date.now() + duration;
          while (Date.now() < end) {
            Math.random();
          }
        }
      }
    },
    scenarios: {
      cascadeFailure: async (originService, depth = 3) => {
        const service = global.testServices.get(originService);
        if (!service) return;

        // Fail origin service
        global.chaosTools.failureInjectors.service.crash(originService);

        // Propagate to dependents
        const dependents = Array.from(global.testServices.values())
          .filter(s => s.dependencies.includes(originService))
          .slice(0, depth);

        for (const dependent of dependents) {
          setTimeout(() => {
            global.chaosTools.failureInjectors.service.crash(dependent.id);
          }, Math.random() * 5000);
        }
      },
      networkPartition: async (serviceIds, duration) => {
        for (const serviceId of serviceIds) {
          const service = global.testServices.get(serviceId);
          if (service) {
            service.status = 'partitioned';
            service.lastError = new Error('Network partition');
          }
        }

        setTimeout(() => {
          for (const serviceId of serviceIds) {
            const service = global.testServices.get(serviceId);
            if (service) {
              service.status = 'healthy';
              delete service.lastError;
            }
          }
        }, duration);
      }
    }
  };

  console.log('🔥 Chaos engineering tools initialized');
}

async function setupTestData() {
  // Create test flows
  global.testFlows = new Map();

  for (let i = 0; i < 100; i++) {
    const flowId = `test_flow_${i}`;
    const serviceId = ['api-gateway', 'trading-engine', 'market-data'][i % 3];

    global.testFlows.set(flowId, {
      id: flowId,
      serviceId,
      status: ['pending', 'in_progress', 'completed', 'error'][i % 4],
      timestamp: Date.now() - Math.random() * 3600000, // Random within 1 hour
      metadata: {
        userId: `user_${Math.floor(i / 10)}`,
        symbol: ['BTCUSD', 'ETHUSD', 'ADAUSD'][i % 3],
        amount: 1000 + Math.random() * 9000
      },
      steps: [],
      errors: []
    });
  }

  // Create test errors
  global.testErrors = new Map();

  const errorTypes = [
    'database_connection_error',
    'api_timeout',
    'validation_error',
    'network_error',
    'service_unavailable'
  ];

  for (let i = 0; i < 50; i++) {
    const errorId = `test_error_${i}`;
    const serviceId = ['trading-engine', 'database', 'market-data'][i % 3];

    global.testErrors.set(errorId, {
      id: errorId,
      serviceId,
      type: errorTypes[i % errorTypes.length],
      severity: ['low', 'medium', 'high', 'critical'][i % 4],
      message: `Test error ${i}`,
      timestamp: Date.now() - Math.random() * 3600000,
      metadata: {
        requestId: `req_${i}`,
        userId: `user_${Math.floor(i / 5)}`
      }
    });
  }

  console.log('📋 Test data created');
}

// Cleanup function (will be called by globalTeardown)
global.cleanupTestEnvironment = async () => {
  console.log('🧹 Cleaning up test environment...');

  try {
    // Clear test data
    if (global.testFlows) global.testFlows.clear();
    if (global.testErrors) global.testErrors.clear();
    if (global.testServices) global.testServices.clear();
    if (global.testDatabases) {
      Object.values(global.testDatabases).forEach(db => {
        if (db.flows) db.flows.clear();
        if (db.services) db.services.clear();
        if (db.errors) db.errors.clear();
      });
    }

    // Clear metrics
    if (global.testMetrics) {
      global.testMetrics.counters.clear();
      global.testMetrics.gauges.clear();
      global.testMetrics.histograms.clear();
      global.testMetrics.summaries.clear();
    }

    // Clear alerts
    if (global.testAlerts) {
      global.testAlerts.active.clear();
      global.testAlerts.history = [];
    }

    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }

    console.log('✅ Test environment cleanup completed');

  } catch (error) {
    console.error('❌ Error during cleanup:', error);
    throw error;
  }
};

// Export for use in tests
module.exports.cleanupTestEnvironment = global.cleanupTestEnvironment;