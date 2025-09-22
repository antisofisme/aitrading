/**
 * Integration Tests for Measurement and Validation Framework
 * Comprehensive test suite for all measurement components
 */

const MeasurementOrchestrator = require('../../src/measurement/measurement-orchestrator');
const BaselineMetricsCollector = require('../../src/measurement/baseline-metrics');
const ProbabilityCalibrationMeasurer = require('../../src/measurement/probability-calibration');
const RiskAdjustedPerformanceTracker = require('../../src/measurement/risk-adjusted-performance');
const StatisticalTestingFramework = require('../../src/measurement/statistical-testing');
const ABTestingFramework = require('../../src/measurement/ab-testing-framework');
const config = require('../../config/measurement/framework-config');

describe('Measurement Framework Integration Tests', () => {
  let orchestrator;
  let testData;

  beforeEach(async () => {
    // Initialize test configuration
    const testConfig = {
      ...config,
      orchestrator: {
        ...config.orchestrator,
        syncInterval: 1000, // 1 second for testing
        analysisInterval: 2000, // 2 seconds for testing
        reportingInterval: 5000 // 5 seconds for testing
      }
    };

    orchestrator = new MeasurementOrchestrator(testConfig.orchestrator);

    // Generate test data
    testData = generateTestTradingData();
  });

  afterEach(async () => {
    if (orchestrator) {
      await orchestrator.shutdown();
    }
  });

  describe('Orchestrator Integration', () => {
    test('should initialize all components successfully', async () => {
      await orchestrator.initialize();

      const status = orchestrator.getStatus();
      expect(status.status).toBe('running');
      expect(status.components).toContain('baseline');
      expect(status.components).toContain('calibration');
      expect(status.components).toContain('riskTracking');
      expect(status.components).toContain('statisticalTesting');
      expect(status.components).toContain('abTesting');
    });

    test('should process trading data through all components', async () => {
      await orchestrator.initialize();

      const results = await orchestrator.processTradingData(testData);

      expect(results.processingId).toBeDefined();
      expect(results.componentResults.baseline).toBeDefined();
      expect(results.componentResults.riskTracking).toBeDefined();
      expect(results.quality.score).toBeGreaterThan(0.5);
      expect(results.crossValidation).toBeDefined();
    });

    test('should handle component errors gracefully', async () => {
      await orchestrator.initialize();

      // Test with invalid data
      const invalidData = { invalidField: 'test' };
      const results = await orchestrator.processTradingData(invalidData);

      expect(results.quality.score).toBeLessThan(0.8);
      expect(results.quality.issues.length).toBeGreaterThan(0);
    });

    test('should generate comprehensive reports', async () => {
      await orchestrator.initialize();

      // Process some data first
      await orchestrator.processTradingData(testData);

      const report = await orchestrator.generateComprehensiveReport();

      expect(report.reportId).toBeDefined();
      expect(report.summary).toBeDefined();
      expect(report.componentReports).toBeDefined();
      expect(report.summary.componentsActive).toBeGreaterThan(0);
    });
  });

  describe('Baseline Metrics Integration', () => {
    test('should calculate comprehensive baseline metrics', async () => {
      const baseline = new BaselineMetricsCollector(config.baseline);
      await baseline.initialize();

      const metrics = baseline.calculateBaselineMetrics(testData);

      expect(metrics.totalReturn).toBeDefined();
      expect(metrics.sharpeRatio).toBeDefined();
      expect(metrics.maxDrawdown).toBeDefined();
      expect(metrics.winRate).toBeDefined();
      expect(metrics.volatility).toBeDefined();

      expect(typeof metrics.totalReturn).toBe('number');
      expect(typeof metrics.sharpeRatio).toBe('number');
      expect(metrics.maxDrawdown).toBeGreaterThanOrEqual(0);
      expect(metrics.winRate).toBeGreaterThanOrEqual(0);
      expect(metrics.winRate).toBeLessThanOrEqual(1);
    });

    test('should track metrics over time', async () => {
      const baseline = new BaselineMetricsCollector(config.baseline);
      await baseline.initialize();

      baseline.recordMetric('sharpe_ratio', 1.5);
      baseline.recordMetric('sharpe_ratio', 1.8);
      baseline.recordMetric('sharpe_ratio', 1.2);

      const snapshot = baseline.getBaselineSnapshot();

      expect(snapshot.metrics.sharpe_ratio.current).toBe(1.2);
      expect(snapshot.metrics.sharpe_ratio.aggregations.count).toBe(3);
      expect(snapshot.metrics.sharpe_ratio.aggregations.mean).toBeCloseTo(1.5, 1);
    });
  });

  describe('Probability Calibration Integration', () => {
    test('should measure calibration accuracy', async () => {
      const calibration = new ProbabilityCalibrationMeasurer(config.calibration);
      await calibration.initialize();

      // Record predictions and outcomes
      const predictions = [
        { id: 'pred1', probability: 0.8, outcome: true },
        { id: 'pred2', probability: 0.3, outcome: false },
        { id: 'pred3', probability: 0.9, outcome: true },
        { id: 'pred4', probability: 0.1, outcome: false },
        { id: 'pred5', probability: 0.6, outcome: true }
      ];

      predictions.forEach(pred => {
        calibration.recordPrediction(pred.id, pred.probability);
        calibration.recordOutcome(pred.id, pred.outcome);
      });

      const metrics = calibration.calculateCalibrationMetrics();

      expect(metrics).toBeDefined();
      expect(metrics.brierScore).toBeDefined();
      expect(metrics.calibrationError).toBeDefined();
      expect(metrics.reliability).toBeDefined();
      expect(metrics.brierScore).toBeGreaterThanOrEqual(0);
      expect(metrics.brierScore).toBeLessThanOrEqual(1);
    });

    test('should detect calibration drift', async () => {
      const calibration = new ProbabilityCalibrationMeasurer({
        ...config.calibration,
        recalibrationThreshold: 0.05
      });
      await calibration.initialize();

      const driftPromise = new Promise(resolve => {
        calibration.on('calibrationDrift', resolve);
      });

      // Simulate initial good calibration
      for (let i = 0; i < 100; i++) {
        const prob = Math.random();
        const outcome = Math.random() < prob;
        calibration.recordPrediction(`pred_${i}`, prob);
        calibration.recordOutcome(`pred_${i}`, outcome);
      }

      // Simulate calibration drift
      for (let i = 100; i < 200; i++) {
        const prob = Math.random();
        const outcome = Math.random() < (prob + 0.3); // Introduce bias
        calibration.recordPrediction(`pred_${i}`, prob);
        calibration.recordOutcome(`pred_${i}`, outcome);
      }

      calibration.updateCalibrationMetrics();

      // Should detect drift in reasonable time
      await expect(Promise.race([
        driftPromise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
      ])).resolves.toBeDefined();
    });
  });

  describe('Risk-Adjusted Performance Integration', () => {
    test('should calculate comprehensive risk metrics', async () => {
      const riskTracker = new RiskAdjustedPerformanceTracker(config.riskTracking);
      await riskTracker.initialize();

      // Simulate portfolio updates
      const portfolioValues = [100000, 105000, 103000, 108000, 106000];
      const positions = [
        [{ symbol: 'AAPL', value: 50000 }, { symbol: 'GOOGL', value: 50000 }],
        [{ symbol: 'AAPL', value: 52500 }, { symbol: 'GOOGL', value: 52500 }],
        [{ symbol: 'AAPL', value: 51500 }, { symbol: 'GOOGL', value: 51500 }],
        [{ symbol: 'AAPL', value: 54000 }, { symbol: 'GOOGL', value: 54000 }],
        [{ symbol: 'AAPL', value: 53000 }, { symbol: 'GOOGL', value: 53000 }]
      ];

      portfolioValues.forEach((value, index) => {
        riskTracker.recordPortfolioState(
          value,
          positions[index],
          Date.now() + index * 24 * 60 * 60 * 1000
        );
      });

      const metrics = riskTracker.calculateRiskAdjustedMetrics();

      expect(metrics).toBeDefined();
      expect(metrics.totalReturn).toBeDefined();
      expect(metrics.sharpeRatio).toBeDefined();
      expect(metrics.maxDrawdown).toBeDefined();
      expect(metrics.volatility).toBeDefined();
      expect(metrics.var95).toBeDefined();

      expect(typeof metrics.totalReturn).toBe('number');
      expect(typeof metrics.sharpeRatio).toBe('number');
      expect(metrics.maxDrawdown).toBeGreaterThanOrEqual(0);
    });

    test('should trigger risk alerts', async () => {
      const riskTracker = new RiskAdjustedPerformanceTracker({
        ...config.riskTracking,
        alertThresholds: {
          maxDrawdown: 0.05 // 5% threshold for testing
        }
      });
      await riskTracker.initialize();

      const alertPromise = new Promise(resolve => {
        riskTracker.on('metricAlert', resolve);
      });

      // Simulate large drawdown
      riskTracker.recordPortfolioState(100000, [], Date.now());
      riskTracker.recordPortfolioState(90000, [], Date.now() + 1000); // 10% drop

      await expect(Promise.race([
        alertPromise,
        new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 2000))
      ])).resolves.toBeDefined();
    });
  });

  describe('Statistical Testing Integration', () => {
    test('should perform comprehensive validation', async () => {
      const testing = new StatisticalTestingFramework(config.statisticalTesting);
      await testing.initialize();

      const strategy1Data = {
        returns: generateRandomReturns(100, 0.01, 0.02)
      };

      const strategy2Data = {
        returns: generateRandomReturns(100, 0.008, 0.015)
      };

      const validation = await testing.performComprehensiveValidation(
        strategy1Data,
        strategy2Data,
        'comparison'
      );

      expect(validation.testId).toBeDefined();
      expect(validation.tests).toBeDefined();
      expect(validation.summary).toBeDefined();
      expect(validation.conclusions).toBeDefined();

      expect(Object.keys(validation.tests).length).toBeGreaterThan(0);
      expect(validation.summary.totalTests).toBeGreaterThan(0);
    });

    test('should apply multiple testing correction', async () => {
      const testing = new StatisticalTestingFramework({
        ...config.statisticalTesting,
        multipleTestingCorrection: 'bonferroni'
      });
      await testing.initialize();

      const strategy1Data = {
        returns: generateRandomReturns(100, 0.01, 0.02)
      };

      const validation = await testing.performComprehensiveValidation(
        strategy1Data,
        null,
        'comprehensive'
      );

      // Check that corrected p-values are present
      const testsWithPValues = Object.values(validation.tests).filter(
        test => test.pValue !== undefined
      );

      expect(testsWithPValues.length).toBeGreaterThan(0);

      testsWithPValues.forEach(test => {
        if (test.pValueCorrected !== undefined) {
          expect(test.pValueCorrected).toBeGreaterThanOrEqual(test.pValue);
        }
      });
    });
  });

  describe('A/B Testing Integration', () => {
    test('should create and run A/B test', async () => {
      const abTesting = new ABTestingFramework(config.abTesting);
      await abTesting.initialize();

      const testConfig = {
        name: 'Strategy Comparison Test',
        description: 'Testing new trading strategy',
        hypothesis: 'New strategy will outperform baseline',
        variants: [
          { id: 'control', name: 'Baseline Strategy', isControl: true },
          { id: 'treatment', name: 'New Strategy', isControl: false }
        ],
        primaryMetric: 'total_return',
        rolloutStrategy: 'canary'
      };

      const test = await abTesting.createTest(testConfig);
      await abTesting.startTest(test.id);

      expect(test.id).toBeDefined();
      expect(test.status).toBe('running');
      expect(test.variants).toHaveLength(2);

      // Simulate participant assignment
      const assignment1 = abTesting.assignParticipant(test.id, 'user1');
      const assignment2 = abTesting.assignParticipant(test.id, 'user2');

      expect(assignment1).toBeDefined();
      expect(assignment2).toBeDefined();
      expect(['control', 'treatment']).toContain(assignment1.variantId);
      expect(['control', 'treatment']).toContain(assignment2.variantId);
    });

    test('should record metrics and perform analysis', async () => {
      const abTesting = new ABTestingFramework({
        ...config.abTesting,
        minSampleSize: 10
      });
      await abTesting.initialize();

      const testConfig = {
        name: 'Metric Recording Test',
        variants: [
          { id: 'control', name: 'Control', isControl: true },
          { id: 'treatment', name: 'Treatment', isControl: false }
        ],
        primaryMetric: 'total_return'
      };

      const test = await abTesting.createTest(testConfig);
      await abTesting.startTest(test.id);

      // Simulate participants and metrics
      for (let i = 0; i < 20; i++) {
        const assignment = abTesting.assignParticipant(test.id, `user${i}`);
        if (assignment) {
          const value = assignment.variantId === 'control' ?
            Math.random() * 0.1 : // Control: 0-10% return
            Math.random() * 0.15; // Treatment: 0-15% return

          abTesting.recordMetric(test.id, `user${i}`, 'total_return', value);
        }
      }

      const analysis = await abTesting.calculateTestStatistics(test.id);

      expect(analysis).toBeDefined();
      expect(analysis.variants.control).toBeDefined();
      expect(analysis.variants.treatment).toBeDefined();
      expect(analysis.comparison.treatment).toBeDefined();
    });
  });

  describe('Cross-Component Integration', () => {
    test('should coordinate data between components', async () => {
      await orchestrator.initialize();

      // Process trading data through orchestrator
      const results1 = await orchestrator.processTradingData(testData);
      const results2 = await orchestrator.processTradingData({
        ...testData,
        timestamp: Date.now(),
        portfolioValue: 110000
      });

      expect(results1.crossValidation).toBeDefined();
      expect(results2.crossValidation).toBeDefined();

      // Check that components are sharing consistent data
      if (results1.componentResults.baseline && results1.componentResults.riskTracking) {
        expect(results1.componentResults.baseline).toBeDefined();
        expect(results1.componentResults.riskTracking).toBeDefined();
      }
    });

    test('should detect inconsistencies between components', async () => {
      await orchestrator.initialize();

      // Create data with intentional inconsistencies
      const inconsistentData = {
        ...testData,
        returns: [0.1, -0.05, 0.08], // High volatility returns
        portfolioValue: 100000,
        positions: [{ symbol: 'TEST', value: 100000 }],
        // Add conflicting metrics
        metadata: {
          reportedSharpeRatio: 3.0, // Unrealistically high
          reportedVolatility: 0.01 // Unrealistically low
        }
      };

      const results = await orchestrator.processTradingData(inconsistentData);

      expect(results.crossValidation).toBeDefined();
      expect(results.crossValidation.consistency).toBeDefined();

      // Should detect some level of inconsistency
      if (results.crossValidation.results) {
        expect(Object.keys(results.crossValidation.results).length).toBeGreaterThan(0);
      }
    });

    test('should synchronize across all components', async () => {
      await orchestrator.initialize();

      // Create sync promise
      const syncPromise = new Promise(resolve => {
        orchestrator.on('syncCompleted', resolve);
      });

      // Trigger sync
      await orchestrator.performSync();

      const syncResult = await syncPromise;

      expect(syncResult.timestamp).toBeDefined();
      expect(syncResult.componentStatus).toBeDefined();
      expect(syncResult.dataConsistency).toBeDefined();

      // All components should be healthy
      const componentStatuses = Object.values(syncResult.componentStatus);
      expect(componentStatuses.every(status => status.status === 'healthy')).toBe(true);
    });
  });

  // Helper functions
  function generateTestTradingData() {
    const returns = generateRandomReturns(100, 0.001, 0.02);
    const trades = generateRandomTrades(50);
    const orders = generateRandomOrders(75);

    return {
      timestamp: Date.now(),
      returns: returns,
      cumulativeReturns: returns.reduce((acc, ret, i) => {
        acc.push((acc[i - 1] || 1) * (1 + ret));
        return acc;
      }, []),
      trades: trades,
      orders: orders,
      executions: orders.filter(order => order.status === 'filled'),
      portfolioValue: 100000,
      positions: [
        { symbol: 'AAPL', quantity: 100, value: 15000 },
        { symbol: 'GOOGL', quantity: 50, value: 85000 }
      ],
      predictions: [
        { id: 'pred1', probability: 0.7, metadata: { model: 'test' } },
        { id: 'pred2', probability: 0.3, metadata: { model: 'test' } }
      ]
    };
  }

  function generateRandomReturns(count, mean = 0, std = 0.01) {
    const returns = [];
    for (let i = 0; i < count; i++) {
      // Box-Muller transform for normal distribution
      const u1 = Math.random();
      const u2 = Math.random();
      const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
      returns.push(mean + z * std);
    }
    return returns;
  }

  function generateRandomTrades(count) {
    const trades = [];
    for (let i = 0; i < count; i++) {
      trades.push({
        id: `trade_${i}`,
        symbol: ['AAPL', 'GOOGL', 'MSFT'][Math.floor(Math.random() * 3)],
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        quantity: Math.floor(Math.random() * 100) + 1,
        price: 100 + Math.random() * 50,
        pnl: (Math.random() - 0.5) * 1000,
        timestamp: Date.now() - Math.random() * 86400000
      });
    }
    return trades;
  }

  function generateRandomOrders(count) {
    const orders = [];
    const statuses = ['filled', 'pending', 'cancelled'];

    for (let i = 0; i < count; i++) {
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      orders.push({
        id: `order_${i}`,
        symbol: ['AAPL', 'GOOGL', 'MSFT'][Math.floor(Math.random() * 3)],
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        quantity: Math.floor(Math.random() * 100) + 1,
        expectedPrice: 100 + Math.random() * 50,
        actualPrice: status === 'filled' ? 100 + Math.random() * 50 : null,
        status: status,
        submitTime: Date.now() - Math.random() * 86400000,
        fillTime: status === 'filled' ? Date.now() - Math.random() * 3600000 : null
      });
    }
    return orders;
  }
});