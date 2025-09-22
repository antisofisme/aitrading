/**
 * Unit Tests for ChainImpactAnalyzer Component
 * Tests error impact analysis, root cause detection, and dependency mapping
 */

const ChainImpactAnalyzer = require('@mocks/chain-impact-analyzer');
const { generateErrorId, generateChainId, createMockError } = require('@utils/test-helpers');

describe('ChainImpactAnalyzer Unit Tests', () => {
  let chainImpactAnalyzer;
  let mockLogger;
  let mockMetrics;
  let mockFlowRegistry;
  let mockHealthMonitor;

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

    mockFlowRegistry = {
      getFlow: jest.fn(),
      getFlowsByService: jest.fn(),
      queryFlows: jest.fn()
    };

    mockHealthMonitor = {
      getServiceHealth: jest.fn(),
      getChainHealth: jest.fn(),
      getServiceDependencies: jest.fn()
    };

    chainImpactAnalyzer = new ChainImpactAnalyzer({
      logger: mockLogger,
      metrics: mockMetrics,
      flowRegistry: mockFlowRegistry,
      healthMonitor: mockHealthMonitor,
      analysisDepth: 5,
      timeWindow: 300000 // 5 minutes
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Error Impact Analysis', () => {
    it('should analyze direct impact of an error', async () => {
      const errorId = generateErrorId();
      const error = createMockError({
        serviceId: 'trading-engine',
        type: 'database_connection_error',
        severity: 'high',
        timestamp: Date.now()
      });

      mockFlowRegistry.getFlowsByService.mockResolvedValue({
        success: true,
        flows: [
          { id: 'flow1', status: 'in_progress', userId: 'user1' },
          { id: 'flow2', status: 'in_progress', userId: 'user2' }
        ]
      });

      const result = await chainImpactAnalyzer.analyzeError(errorId, error);

      expect(result.success).toBe(true);
      expect(result.impact.directlyAffectedFlows).toBe(2);
      expect(result.impact.affectedUsers).toEqual(['user1', 'user2']);
      expect(result.impact.severity).toBe('high');
      expect(mockMetrics.increment).toHaveBeenCalledWith('impact.analysis.completed');
    });

    it('should analyze cascading impact across services', async () => {
      const error = createMockError({
        serviceId: 'auth-service',
        type: 'authentication_failure',
        severity: 'medium'
      });

      // Mock service dependencies
      mockHealthMonitor.getServiceDependencies.mockResolvedValue({
        dependents: ['api-gateway', 'trading-engine', 'user-management'],
        dependencies: ['database', 'cache']
      });

      // Mock flows in dependent services
      mockFlowRegistry.queryFlows.mockResolvedValue({
        success: true,
        flows: [
          { id: 'flow1', serviceId: 'api-gateway', status: 'in_progress' },
          { id: 'flow2', serviceId: 'trading-engine', status: 'in_progress' },
          { id: 'flow3', serviceId: 'user-management', status: 'in_progress' }
        ]
      });

      const result = await chainImpactAnalyzer.analyzeError('error1', error);

      expect(result.impact.cascadingServices).toHaveLength(3);
      expect(result.impact.cascadingFlows).toBe(3);
      expect(result.impact.impactRadius).toBe(2); // Two levels deep
    });

    it('should calculate business impact metrics', async () => {
      const error = createMockError({
        serviceId: 'payment-processor',
        type: 'payment_gateway_timeout',
        severity: 'critical'
      });

      // Mock high-value flows
      mockFlowRegistry.getFlowsByService.mockResolvedValue({
        success: true,
        flows: [
          {
            id: 'flow1',
            status: 'in_progress',
            metadata: { tradeValue: 100000, currency: 'USD' }
          },
          {
            id: 'flow2',
            status: 'in_progress',
            metadata: { tradeValue: 50000, currency: 'USD' }
          }
        ]
      });

      const result = await chainImpactAnalyzer.analyzeError('error1', error);

      expect(result.businessImpact.totalValue).toBe(150000);
      expect(result.businessImpact.currency).toBe('USD');
      expect(result.businessImpact.riskLevel).toBe('critical');
      expect(result.businessImpact.estimatedLoss).toBeGreaterThan(0);
    });

    it('should identify temporal impact patterns', async () => {
      const error = createMockError({
        serviceId: 'market-data',
        type: 'feed_interruption',
        timestamp: Date.now()
      });

      // Mock historical errors in time window
      const historicalErrors = [
        { timestamp: Date.now() - 60000, serviceId: 'market-data' },
        { timestamp: Date.now() - 120000, serviceId: 'market-data' },
        { timestamp: Date.now() - 180000, serviceId: 'trading-engine' }
      ];

      chainImpactAnalyzer._getHistoricalErrors = jest.fn().mockResolvedValue(historicalErrors);

      const result = await chainImpactAnalyzer.analyzeError('error1', error);

      expect(result.temporalImpact.errorFrequency).toBe(3);
      expect(result.temporalImpact.pattern).toBe('increasing');
      expect(result.temporalImpact.relatedErrors).toHaveLength(2); // Same service
    });
  });

  describe('Root Cause Detection', () => {
    it('should identify root cause through dependency analysis', async () => {
      const error = createMockError({
        serviceId: 'trading-engine',
        type: 'execution_timeout',
        timestamp: Date.now()
      });

      // Mock dependency chain
      mockHealthMonitor.getServiceDependencies.mockResolvedValue({
        dependencies: ['database', 'market-data', 'risk-engine']
      });

      // Mock health status showing database issue
      mockHealthMonitor.getServiceHealth.mockImplementation((serviceId) => {
        if (serviceId === 'database') {
          return Promise.resolve({
            status: 'unhealthy',
            lastError: 'connection_pool_exhausted',
            timestamp: Date.now() - 30000
          });
        }
        return Promise.resolve({ status: 'healthy' });
      });

      const result = await chainImpactAnalyzer.detectRootCause('error1', error);

      expect(result.success).toBe(true);
      expect(result.rootCause.serviceId).toBe('database');
      expect(result.rootCause.type).toBe('connection_pool_exhausted');
      expect(result.rootCause.confidence).toBeGreaterThan(0.8);
      expect(result.propagationPath).toEqual(['database', 'trading-engine']);
    });

    it('should analyze error correlation patterns', async () => {
      const error = createMockError({
        serviceId: 'api-gateway',
        type: 'rate_limit_exceeded'
      });

      // Mock correlated errors
      const correlatedErrors = [
        {
          serviceId: 'load-balancer',
          type: 'connection_refused',
          timestamp: Date.now() - 10000,
          correlation: 0.95
        },
        {
          serviceId: 'auth-service',
          type: 'high_cpu_usage',
          timestamp: Date.now() - 5000,
          correlation: 0.87
        }
      ];

      chainImpactAnalyzer._findCorrelatedErrors = jest.fn().mockResolvedValue(correlatedErrors);

      const result = await chainImpactAnalyzer.detectRootCause('error1', error);

      expect(result.correlatedErrors).toHaveLength(2);
      expect(result.correlatedErrors[0].correlation).toBe(0.95);
      expect(result.rootCause.serviceId).toBe('load-balancer');
    });

    it('should use machine learning for pattern recognition', async () => {
      const error = createMockError({
        serviceId: 'ml-prediction',
        type: 'model_inference_error'
      });

      // Mock ML analysis result
      const mlAnalysis = {
        predictedRootCause: 'memory_leak',
        confidence: 0.92,
        contributingFactors: ['high_load', 'memory_pressure', 'gc_frequency'],
        similarIncidents: ['incident_123', 'incident_456']
      };

      chainImpactAnalyzer._runMLAnalysis = jest.fn().mockResolvedValue(mlAnalysis);

      const result = await chainImpactAnalyzer.detectRootCause('error1', error);

      expect(result.mlAnalysis.confidence).toBe(0.92);
      expect(result.mlAnalysis.predictedRootCause).toBe('memory_leak');
      expect(result.mlAnalysis.contributingFactors).toHaveLength(3);
    });

    it('should handle complex multi-root scenarios', async () => {
      const error = createMockError({
        serviceId: 'order-processing',
        type: 'processing_failure'
      });

      // Mock multiple potential root causes
      const multipleRoots = [
        { serviceId: 'database', confidence: 0.6, type: 'slow_query' },
        { serviceId: 'network', confidence: 0.7, type: 'packet_loss' },
        { serviceId: 'cache', confidence: 0.5, type: 'cache_miss_storm' }
      ];

      chainImpactAnalyzer._analyzeMultipleRoots = jest.fn().mockResolvedValue(multipleRoots);

      const result = await chainImpactAnalyzer.detectRootCause('error1', error);

      expect(result.multipleRoots).toHaveLength(3);
      expect(result.primaryRootCause.serviceId).toBe('network'); // Highest confidence
      expect(result.analysis.complexity).toBe('high');
    });
  });

  describe('Flow Impact Mapping', () => {
    it('should map error impact across active flows', async () => {
      const error = createMockError({
        serviceId: 'payment-service',
        type: 'gateway_error'
      });

      // Mock active flows
      const activeFlows = [
        {
          id: 'flow1',
          status: 'in_progress',
          currentStep: 'payment_processing',
          metadata: { amount: 1000, currency: 'USD' }
        },
        {
          id: 'flow2',
          status: 'in_progress',
          currentStep: 'order_confirmation',
          metadata: { amount: 500, currency: 'EUR' }
        },
        {
          id: 'flow3',
          status: 'completed',
          metadata: { amount: 2000, currency: 'USD' }
        }
      ];

      mockFlowRegistry.queryFlows.mockResolvedValue({
        success: true,
        flows: activeFlows
      });

      const result = await chainImpactAnalyzer.mapFlowImpact('error1', error);

      expect(result.affectedFlows).toHaveLength(2); // Only in_progress flows
      expect(result.totalImpactValue).toBe(1500); // 1000 USD + 500 EUR (converted)
      expect(result.criticalFlows).toHaveLength(1); // High-value flow
    });

    it('should analyze flow recovery strategies', async () => {
      const error = createMockError({
        serviceId: 'trade-execution',
        type: 'market_unavailable'
      });

      const impactedFlow = {
        id: 'flow1',
        status: 'error',
        currentStep: 'market_order_placement',
        metadata: {
          symbol: 'BTCUSD',
          quantity: 1.5,
          orderType: 'market',
          urgency: 'high'
        }
      };

      mockFlowRegistry.getFlow.mockResolvedValue({
        success: true,
        flow: impactedFlow
      });

      const result = await chainImpactAnalyzer.analyzeRecoveryOptions('flow1', error);

      expect(result.recoveryStrategies).toContain('retry_with_delay');
      expect(result.recoveryStrategies).toContain('switch_to_backup_exchange');
      expect(result.recommendedStrategy).toBe('switch_to_backup_exchange');
      expect(result.estimatedRecoveryTime).toBeLessThan(30000); // 30 seconds
    });

    it('should prioritize flows by business criticality', async () => {
      const error = createMockError({
        serviceId: 'core-engine',
        type: 'service_unavailable'
      });

      const flows = [
        { id: 'flow1', priority: 'low', value: 100 },
        { id: 'flow2', priority: 'high', value: 1000 },
        { id: 'flow3', priority: 'critical', value: 500 },
        { id: 'flow4', priority: 'medium', value: 2000 }
      ];

      mockFlowRegistry.queryFlows.mockResolvedValue({
        success: true,
        flows: flows.map(f => ({ ...f, status: 'in_progress' }))
      });

      const result = await chainImpactAnalyzer.prioritizeFlowRecovery('error1', error);

      expect(result.prioritizedFlows[0].id).toBe('flow3'); // Critical priority
      expect(result.prioritizedFlows[1].id).toBe('flow2'); // High priority
      expect(result.prioritizedFlows[2].id).toBe('flow4'); // Medium priority, high value
      expect(result.prioritizedFlows[3].id).toBe('flow1'); // Low priority
    });
  });

  describe('Performance Impact Analysis', () => {
    it('should analyze system performance degradation', async () => {
      const error = createMockError({
        serviceId: 'database',
        type: 'slow_query',
        metrics: {
          queryTime: 5000,
          normalQueryTime: 200
        }
      });

      // Mock performance metrics
      const performanceData = {
        beforeError: {
          avgResponseTime: 150,
          throughput: 1000,
          errorRate: 0.01
        },
        afterError: {
          avgResponseTime: 800,
          throughput: 600,
          errorRate: 0.15
        }
      };

      chainImpactAnalyzer._getPerformanceMetrics = jest.fn().mockResolvedValue(performanceData);

      const result = await chainImpactAnalyzer.analyzePerformanceImpact('error1', error);

      expect(result.responseTimeDegradation).toBeCloseTo(433.3, 1); // 433% increase
      expect(result.throughputReduction).toBe(40); // 40% reduction
      expect(result.errorRateIncrease).toBe(1400); // 1400% increase
      expect(result.overallImpact).toBe('severe');
    });

    it('should predict performance recovery timeline', async () => {
      const error = createMockError({
        serviceId: 'cache-service',
        type: 'cache_invalidation_storm'
      });

      // Mock historical recovery data
      const historicalRecoveries = [
        { duration: 300000, scenario: 'cache_rebuild' }, // 5 minutes
        { duration: 600000, scenario: 'cache_rebuild' }, // 10 minutes
        { duration: 450000, scenario: 'cache_rebuild' }  // 7.5 minutes
      ];

      chainImpactAnalyzer._getHistoricalRecoveries = jest.fn().mockResolvedValue(historicalRecoveries);

      const result = await chainImpactAnalyzer.predictRecoveryTimeline('error1', error);

      expect(result.estimatedRecoveryTime).toBeCloseTo(450000, 50000); // ~7.5 minutes ±50s
      expect(result.confidence).toBeGreaterThan(0.7);
      expect(result.factorsConsidered).toContain('historical_patterns');
    });
  });

  describe('Alert and Notification Management', () => {
    it('should generate impact-based alert priorities', async () => {
      const highImpactError = createMockError({
        serviceId: 'core-trading',
        type: 'critical_failure',
        severity: 'critical'
      });

      mockFlowRegistry.queryFlows.mockResolvedValue({
        success: true,
        flows: new Array(100).fill().map((_, i) => ({
          id: `flow_${i}`,
          status: 'in_progress',
          metadata: { value: 10000 }
        }))
      });

      const result = await chainImpactAnalyzer.generateAlertPriority('error1', highImpactError);

      expect(result.priority).toBe('P0'); // Highest priority
      expect(result.escalationLevel).toBe('immediate');
      expect(result.notificationChannels).toContain('pager_duty');
      expect(result.notificationChannels).toContain('incident_response');
    });

    it('should customize alerts based on business hours', async () => {
      const error = createMockError({
        serviceId: 'reporting-service',
        type: 'report_generation_failure'
      });

      // Mock off-hours timestamp
      const offHoursTimestamp = new Date();
      offHoursTimestamp.setHours(2); // 2 AM

      error.timestamp = offHoursTimestamp.getTime();

      const result = await chainImpactAnalyzer.generateAlertPriority('error1', error);

      expect(result.businessHoursAdjustment).toBe(true);
      expect(result.priority).toBe('P2'); // Lower priority off-hours
      expect(result.notificationChannels).not.toContain('pager_duty');
    });
  });

  describe('Historical Analysis and Learning', () => {
    it('should learn from past incident patterns', async () => {
      const error = createMockError({
        serviceId: 'payment-gateway',
        type: 'connection_timeout'
      });

      // Mock historical incidents
      const historicalIncidents = [
        {
          id: 'incident_1',
          rootCause: 'network_congestion',
          resolution: 'traffic_rerouting',
          resolutionTime: 900000 // 15 minutes
        },
        {
          id: 'incident_2',
          rootCause: 'gateway_overload',
          resolution: 'scale_up',
          resolutionTime: 600000 // 10 minutes
        }
      ];

      chainImpactAnalyzer._getSimilarIncidents = jest.fn().mockResolvedValue(historicalIncidents);

      const result = await chainImpactAnalyzer.learnFromHistory('error1', error);

      expect(result.similarIncidents).toHaveLength(2);
      expect(result.recommendedActions).toContain('traffic_rerouting');
      expect(result.avgResolutionTime).toBe(750000); // 12.5 minutes
    });

    it('should update impact models based on outcomes', async () => {
      const error = createMockError({
        serviceId: 'ml-model',
        type: 'prediction_accuracy_drop'
      });

      const actualOutcome = {
        actualImpact: 'medium',
        actualRecoveryTime: 1200000, // 20 minutes
        actualCost: 5000,
        lessons: ['model_retrain_needed', 'monitoring_insufficient']
      };

      const result = await chainImpactAnalyzer.updateImpactModel('error1', error, actualOutcome);

      expect(result.modelUpdated).toBe(true);
      expect(result.accuracyImprovement).toBeGreaterThan(0);
      expect(mockMetrics.increment).toHaveBeenCalledWith('model.update.completed');
    });
  });

  describe('Integration and Data Export', () => {
    it('should export impact analysis for external systems', async () => {
      const error = createMockError({
        serviceId: 'trade-engine',
        type: 'execution_failure'
      });

      const impactAnalysis = {
        errorId: 'error1',
        impact: {
          affectedFlows: 25,
          affectedUsers: 15,
          estimatedLoss: 50000
        },
        rootCause: {
          serviceId: 'database',
          confidence: 0.9
        }
      };

      chainImpactAnalyzer._generateImpactAnalysis = jest.fn().mockResolvedValue(impactAnalysis);

      const result = await chainImpactAnalyzer.exportImpactAnalysis('error1', 'json');

      expect(result.format).toBe('json');
      expect(result.data).toMatchObject(impactAnalysis);
      expect(result.exportedAt).toBeDefined();
    });

    it('should integrate with incident management systems', async () => {
      const error = createMockError({
        serviceId: 'critical-service',
        type: 'service_down'
      });

      const incidentData = {
        title: 'Critical Service Down - High Impact',
        description: expect.any(String),
        priority: 'P0',
        assignee: 'on-call-engineer',
        tags: ['service-down', 'high-impact', 'critical-service']
      };

      const mockIncidentManagement = {
        createIncident: jest.fn().mockResolvedValue({ id: 'INC-12345' })
      };

      chainImpactAnalyzer.incidentManagement = mockIncidentManagement;

      const result = await chainImpactAnalyzer.createIncident('error1', error);

      expect(mockIncidentManagement.createIncident).toHaveBeenCalledWith(
        expect.objectContaining(incidentData)
      );
      expect(result.incidentId).toBe('INC-12345');
    });
  });
});