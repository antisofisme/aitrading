/**
 * Unit Tests for ChainHealthMonitor Component
 * Tests service health tracking, chain monitoring, and alerting
 */

const ChainHealthMonitor = require('@mocks/chain-health-monitor');
const { generateChainId, generateServiceId, createMockService } = require('@utils/test-helpers');

describe('ChainHealthMonitor Unit Tests', () => {
  let chainHealthMonitor;
  let mockLogger;
  let mockMetrics;
  let mockAlertManager;

  beforeEach(() => {
    mockLogger = {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    mockMetrics = {
      increment: jest.fn(),
      gauge: jest.fn(),
      histogram: jest.fn(),
      timer: jest.fn()
    };

    mockAlertManager = {
      sendAlert: jest.fn().mockResolvedValue({ success: true }),
      escalateAlert: jest.fn().mockResolvedValue({ success: true })
    };

    chainHealthMonitor = new ChainHealthMonitor({
      logger: mockLogger,
      metrics: mockMetrics,
      alertManager: mockAlertManager,
      healthCheckInterval: 1000, // 1 second for testing
      alertThresholds: {
        errorRate: 0.1, // 10%
        responseTime: 5000, // 5 seconds
        availability: 0.95 // 95%
      }
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    if (chainHealthMonitor.isMonitoring) {
      chainHealthMonitor.stopMonitoring();
    }
  });

  describe('Service Registration', () => {
    it('should register a service for monitoring', async () => {
      const serviceId = generateServiceId();
      const serviceConfig = {
        name: 'Trading Engine',
        healthEndpoint: 'http://localhost:3001/health',
        dependencies: ['database', 'cache'],
        criticality: 'high'
      };

      const result = await chainHealthMonitor.registerService(serviceId, serviceConfig);

      expect(result.success).toBe(true);
      expect(mockMetrics.increment).toHaveBeenCalledWith('service.registered');
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('Service registered'),
        expect.objectContaining({ serviceId })
      );
    });

    it('should validate service registration parameters', async () => {
      // Test invalid serviceId
      const result1 = await chainHealthMonitor.registerService('', {});
      expect(result1.success).toBe(false);
      expect(result1.error).toContain('Invalid serviceId');

      // Test missing health endpoint
      const result2 = await chainHealthMonitor.registerService('service1', {
        name: 'Test Service'
      });
      expect(result2.success).toBe(false);
      expect(result2.error).toContain('healthEndpoint required');
    });

    it('should handle duplicate service registration', async () => {
      const serviceId = generateServiceId();
      const config = {
        name: 'Test Service',
        healthEndpoint: 'http://localhost:3001/health'
      };

      await chainHealthMonitor.registerService(serviceId, config);
      const result = await chainHealthMonitor.registerService(serviceId, config);

      expect(result.success).toBe(true); // Should update existing
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('Service updated'),
        expect.objectContaining({ serviceId })
      );
    });
  });

  describe('Health Monitoring', () => {
    let serviceId1, serviceId2;

    beforeEach(async () => {
      serviceId1 = generateServiceId();
      serviceId2 = generateServiceId();

      await chainHealthMonitor.registerService(serviceId1, {
        name: 'Service 1',
        healthEndpoint: 'http://localhost:3001/health',
        dependencies: []
      });

      await chainHealthMonitor.registerService(serviceId2, {
        name: 'Service 2',
        healthEndpoint: 'http://localhost:3002/health',
        dependencies: [serviceId1]
      });
    });

    it('should start monitoring services', async () => {
      const result = await chainHealthMonitor.startMonitoring();

      expect(result.success).toBe(true);
      expect(chainHealthMonitor.isMonitoring).toBe(true);
      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('Health monitoring started')
      );
    });

    it('should perform health checks on services', async () => {
      // Mock successful health response
      const mockHealthCheck = jest.fn().mockResolvedValue({
        status: 'healthy',
        responseTime: 150,
        timestamp: Date.now()
      });

      chainHealthMonitor._performHealthCheck = mockHealthCheck;
      await chainHealthMonitor.startMonitoring();

      // Wait for health check cycle
      await new Promise(resolve => setTimeout(resolve, 1200));

      expect(mockHealthCheck).toHaveBeenCalledTimes(2); // Two services
      expect(mockMetrics.gauge).toHaveBeenCalledWith(
        'service.health.response_time',
        150,
        expect.any(Object)
      );
    });

    it('should detect service failures', async () => {
      // Mock failed health response
      const mockHealthCheck = jest.fn().mockResolvedValue({
        status: 'unhealthy',
        error: 'Connection timeout',
        responseTime: 5500,
        timestamp: Date.now()
      });

      chainHealthMonitor._performHealthCheck = mockHealthCheck;
      await chainHealthMonitor.startMonitoring();

      // Wait for health check cycle
      await new Promise(resolve => setTimeout(resolve, 1200));

      expect(mockMetrics.increment).toHaveBeenCalledWith(
        'service.health.failure',
        expect.any(Object)
      );
      expect(mockAlertManager.sendAlert).toHaveBeenCalled();
    });

    it('should track service availability metrics', async () => {
      const serviceHealth = chainHealthMonitor._getServiceHealth(serviceId1);

      // Simulate health check results
      serviceHealth.addHealthCheck({ status: 'healthy', timestamp: Date.now() - 5000 });
      serviceHealth.addHealthCheck({ status: 'healthy', timestamp: Date.now() - 4000 });
      serviceHealth.addHealthCheck({ status: 'unhealthy', timestamp: Date.now() - 3000 });
      serviceHealth.addHealthCheck({ status: 'healthy', timestamp: Date.now() - 2000 });
      serviceHealth.addHealthCheck({ status: 'healthy', timestamp: Date.now() - 1000 });

      const availability = serviceHealth.calculateAvailability();
      expect(availability).toBe(0.8); // 4 out of 5 healthy
    });
  });

  describe('Chain Health Analysis', () => {
    let chainId, services;

    beforeEach(async () => {
      chainId = generateChainId();
      services = [
        { id: 'gateway', name: 'API Gateway', dependencies: [] },
        { id: 'auth', name: 'Auth Service', dependencies: ['gateway'] },
        { id: 'trading', name: 'Trading Engine', dependencies: ['auth', 'database'] },
        { id: 'database', name: 'Database', dependencies: [] }
      ];

      for (const service of services) {
        await chainHealthMonitor.registerService(service.id, {
          name: service.name,
          healthEndpoint: `http://localhost:300${services.indexOf(service) + 1}/health`,
          dependencies: service.dependencies
        });
      }

      await chainHealthMonitor.registerChain(chainId, {
        name: 'Trade Execution Chain',
        services: services.map(s => s.id),
        entryPoint: 'gateway'
      });
    });

    it('should analyze chain health status', async () => {
      // Set service health states
      chainHealthMonitor._setServiceHealth('gateway', 'healthy');
      chainHealthMonitor._setServiceHealth('auth', 'healthy');
      chainHealthMonitor._setServiceHealth('trading', 'degraded');
      chainHealthMonitor._setServiceHealth('database', 'healthy');

      const chainHealth = await chainHealthMonitor.analyzeChainHealth(chainId);

      expect(chainHealth.success).toBe(true);
      expect(chainHealth.overallStatus).toBe('degraded');
      expect(chainHealth.healthyServices).toBe(3);
      expect(chainHealth.degradedServices).toBe(1);
      expect(chainHealth.unhealthyServices).toBe(0);
    });

    it('should identify critical path failures', async () => {
      // Simulate failure in critical service
      chainHealthMonitor._setServiceHealth('auth', 'unhealthy');

      const chainHealth = await chainHealthMonitor.analyzeChainHealth(chainId);

      expect(chainHealth.overallStatus).toBe('unhealthy');
      expect(chainHealth.criticalPathFailure).toBe(true);
      expect(chainHealth.affectedServices).toContain('trading'); // Depends on auth
    });

    it('should calculate chain availability score', async () => {
      // Set all services healthy except one
      chainHealthMonitor._setServiceHealth('gateway', 'healthy', 0.99);
      chainHealthMonitor._setServiceHealth('auth', 'healthy', 0.98);
      chainHealthMonitor._setServiceHealth('trading', 'healthy', 0.95);
      chainHealthMonitor._setServiceHealth('database', 'healthy', 0.99);

      const chainHealth = await chainHealthMonitor.analyzeChainHealth(chainId);

      // Chain availability should be the minimum of critical path
      expect(chainHealth.availabilityScore).toBe(0.95);
    });
  });

  describe('Alert Management', () => {
    let serviceId;

    beforeEach(async () => {
      serviceId = generateServiceId();
      await chainHealthMonitor.registerService(serviceId, {
        name: 'Critical Service',
        healthEndpoint: 'http://localhost:3001/health',
        criticality: 'high',
        alertThresholds: {
          errorRate: 0.05,
          responseTime: 2000
        }
      });
    });

    it('should trigger alerts on service failure', async () => {
      await chainHealthMonitor._processHealthCheck(serviceId, {
        status: 'unhealthy',
        error: 'Service unavailable',
        responseTime: 0,
        timestamp: Date.now()
      });

      expect(mockAlertManager.sendAlert).toHaveBeenCalledWith({
        type: 'service_failure',
        serviceId,
        severity: 'high',
        message: expect.stringContaining('Service unavailable'),
        timestamp: expect.any(Number)
      });
    });

    it('should trigger alerts on performance degradation', async () => {
      // Simulate multiple slow responses
      for (let i = 0; i < 5; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'healthy',
          responseTime: 3000, // Above threshold
          timestamp: Date.now()
        });
      }

      expect(mockAlertManager.sendAlert).toHaveBeenCalledWith({
        type: 'performance_degradation',
        serviceId,
        severity: 'medium',
        message: expect.stringContaining('Response time'),
        metrics: expect.objectContaining({
          averageResponseTime: expect.any(Number)
        }),
        timestamp: expect.any(Number)
      });
    });

    it('should escalate persistent issues', async () => {
      const alertData = {
        type: 'service_failure',
        serviceId,
        severity: 'high'
      };

      // Simulate repeated failures
      for (let i = 0; i < 3; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'unhealthy',
          error: 'Persistent failure',
          timestamp: Date.now()
        });
      }

      expect(mockAlertManager.escalateAlert).toHaveBeenCalled();
    });

    it('should handle alert rate limiting', async () => {
      // Configure rate limiting
      chainHealthMonitor.config.alertRateLimit = 2; // Max 2 alerts per minute

      // Trigger multiple failures rapidly
      for (let i = 0; i < 5; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'unhealthy',
          error: `Failure ${i}`,
          timestamp: Date.now()
        });
      }

      // Should only send limited number of alerts
      expect(mockAlertManager.sendAlert).toHaveBeenCalledTimes(2);
    });
  });

  describe('Performance Monitoring', () => {
    it('should track response time distributions', async () => {
      const serviceId = generateServiceId();
      await chainHealthMonitor.registerService(serviceId, {
        name: 'Performance Test Service',
        healthEndpoint: 'http://localhost:3001/health'
      });

      // Simulate various response times
      const responseTimes = [100, 150, 200, 300, 500, 1000, 1500];

      for (const responseTime of responseTimes) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'healthy',
          responseTime,
          timestamp: Date.now()
        });
      }

      const metrics = chainHealthMonitor._getServiceMetrics(serviceId);
      expect(metrics.averageResponseTime).toBeCloseTo(535.7, 1);
      expect(metrics.p95ResponseTime).toBeGreaterThan(1000);
    });

    it('should detect performance anomalies', async () => {
      const serviceId = generateServiceId();
      await chainHealthMonitor.registerService(serviceId, {
        name: 'Anomaly Test Service',
        healthEndpoint: 'http://localhost:3001/health'
      });

      // Establish baseline (normal response times)
      for (let i = 0; i < 20; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'healthy',
          responseTime: 100 + Math.random() * 50, // 100-150ms
          timestamp: Date.now()
        });
      }

      // Introduce anomaly
      await chainHealthMonitor._processHealthCheck(serviceId, {
        status: 'healthy',
        responseTime: 5000, // Significant spike
        timestamp: Date.now()
      });

      const anomalies = chainHealthMonitor._detectAnomalies(serviceId);
      expect(anomalies).toHaveLength(1);
      expect(anomalies[0].type).toBe('response_time_spike');
    });
  });

  describe('Recovery and Self-Healing', () => {
    let serviceId;

    beforeEach(async () => {
      serviceId = generateServiceId();
      await chainHealthMonitor.registerService(serviceId, {
        name: 'Self-Healing Service',
        healthEndpoint: 'http://localhost:3001/health',
        recoveryStrategies: ['restart', 'scale_up', 'circuit_breaker']
      });
    });

    it('should attempt automatic recovery on failure', async () => {
      const mockRecovery = jest.fn().mockResolvedValue({ success: true });
      chainHealthMonitor._attemptRecovery = mockRecovery;

      await chainHealthMonitor._processHealthCheck(serviceId, {
        status: 'unhealthy',
        error: 'Service crashed',
        timestamp: Date.now()
      });

      expect(mockRecovery).toHaveBeenCalledWith(serviceId, 'restart');
    });

    it('should track recovery success rates', async () => {
      const mockRecovery = jest.fn()
        .mockResolvedValueOnce({ success: true })
        .mockResolvedValueOnce({ success: false })
        .mockResolvedValueOnce({ success: true });

      chainHealthMonitor._attemptRecovery = mockRecovery;

      // Trigger multiple failures and recoveries
      for (let i = 0; i < 3; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'unhealthy',
          error: `Failure ${i}`,
          timestamp: Date.now()
        });
      }

      const stats = chainHealthMonitor._getRecoveryStats(serviceId);
      expect(stats.totalAttempts).toBe(3);
      expect(stats.successfulRecoveries).toBe(2);
      expect(stats.successRate).toBeCloseTo(0.67, 2);
    });

    it('should disable auto-recovery after repeated failures', async () => {
      const mockRecovery = jest.fn().mockResolvedValue({ success: false });
      chainHealthMonitor._attemptRecovery = mockRecovery;

      // Configure failure threshold
      chainHealthMonitor.config.maxRecoveryAttempts = 3;

      // Trigger failures beyond threshold
      for (let i = 0; i < 5; i++) {
        await chainHealthMonitor._processHealthCheck(serviceId, {
          status: 'unhealthy',
          error: `Persistent failure ${i}`,
          timestamp: Date.now()
        });
      }

      // Should stop attempting recovery after threshold
      expect(mockRecovery).toHaveBeenCalledTimes(3);
      expect(mockLogger.warn).toHaveBeenCalledWith(
        expect.stringContaining('Auto-recovery disabled'),
        expect.objectContaining({ serviceId })
      );
    });
  });

  describe('Data Aggregation and Reporting', () => {
    it('should generate health summary reports', async () => {
      // Setup multiple services with different health states
      const services = [
        { id: 'service1', status: 'healthy', availability: 0.99 },
        { id: 'service2', status: 'degraded', availability: 0.90 },
        { id: 'service3', status: 'unhealthy', availability: 0.75 }
      ];

      for (const service of services) {
        await chainHealthMonitor.registerService(service.id, {
          name: `Service ${service.id}`,
          healthEndpoint: `http://localhost:3001/health`
        });
        chainHealthMonitor._setServiceHealth(service.id, service.status, service.availability);
      }

      const report = await chainHealthMonitor.generateHealthReport();

      expect(report.totalServices).toBe(3);
      expect(report.healthyServices).toBe(1);
      expect(report.degradedServices).toBe(1);
      expect(report.unhealthyServices).toBe(1);
      expect(report.overallAvailability).toBeCloseTo(0.88, 2);
    });

    it('should export metrics in Prometheus format', async () => {
      const serviceId = generateServiceId();
      await chainHealthMonitor.registerService(serviceId, {
        name: 'Metrics Test Service',
        healthEndpoint: 'http://localhost:3001/health'
      });

      const prometheusMetrics = await chainHealthMonitor.exportPrometheusMetrics();

      expect(prometheusMetrics).toContain('service_health_status');
      expect(prometheusMetrics).toContain('service_response_time');
      expect(prometheusMetrics).toContain('service_availability');
    });
  });
});