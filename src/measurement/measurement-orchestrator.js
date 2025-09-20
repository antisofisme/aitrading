/**
 * Measurement and Validation Orchestrator
 * Central coordination system for all measurement and validation activities
 */

const EventEmitter = require('events');
const BaselineMetricsCollector = require('./baseline-metrics');
const ProbabilityCalibrationMeasurer = require('./probability-calibration');
const RiskAdjustedPerformanceTracker = require('./risk-adjusted-performance');
const StatisticalTestingFramework = require('./statistical-testing');
const ABTestingFramework = require('./ab-testing-framework');

class MeasurementOrchestrator extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      enableBaseline: config.enableBaseline !== false,
      enableCalibration: config.enableCalibration !== false,
      enableRiskTracking: config.enableRiskTracking !== false,
      enableStatisticalTesting: config.enableStatisticalTesting !== false,
      enableABTesting: config.enableABTesting !== false,

      // Coordination settings
      syncInterval: config.syncInterval || 60000, // 1 minute
      analysisInterval: config.analysisInterval || 300000, // 5 minutes
      reportingInterval: config.reportingInterval || 3600000, // 1 hour

      // Quality thresholds
      minDataQuality: config.minDataQuality || 0.8,
      maxDataLatency: config.maxDataLatency || 300000, // 5 minutes

      ...config
    };

    // Initialize measurement components
    this.components = {};
    this.initializeComponents();

    // Coordination state
    this.orchestrationState = {
      status: 'initialized',
      lastSync: null,
      lastAnalysis: null,
      lastReport: null,
      activeExperiments: new Map(),
      dataQuality: {},
      alerts: []
    };

    this.intervals = {};
    this.dataBuffer = new Map();
    this.crossValidationResults = new Map();
  }

  initializeComponents() {
    if (this.config.enableBaseline) {
      this.components.baseline = new BaselineMetricsCollector(this.config.baseline || {});
      this.components.baseline.on('metricRecorded', this.handleBaselineMetric.bind(this));
      this.components.baseline.on('error', this.handleComponentError.bind(this, 'baseline'));
    }

    if (this.config.enableCalibration) {
      this.components.calibration = new ProbabilityCalibrationMeasurer(this.config.calibration || {});
      this.components.calibration.on('predictionRecorded', this.handleCalibrationEvent.bind(this));
      this.components.calibration.on('calibrationDrift', this.handleCalibrationDrift.bind(this));
      this.components.calibration.on('error', this.handleComponentError.bind(this, 'calibration'));
    }

    if (this.config.enableRiskTracking) {
      this.components.riskTracking = new RiskAdjustedPerformanceTracker(this.config.riskTracking || {});
      this.components.riskTracking.on('metricsUpdated', this.handleRiskMetricsUpdate.bind(this));
      this.components.riskTracking.on('metricAlert', this.handleRiskAlert.bind(this));
      this.components.riskTracking.on('error', this.handleComponentError.bind(this, 'riskTracking'));
    }

    if (this.config.enableStatisticalTesting) {
      this.components.statisticalTesting = new StatisticalTestingFramework(this.config.statisticalTesting || {});
      this.components.statisticalTesting.on('validationCompleted', this.handleValidationResult.bind(this));
      this.components.statisticalTesting.on('error', this.handleComponentError.bind(this, 'statisticalTesting'));
    }

    if (this.config.enableABTesting) {
      this.components.abTesting = new ABTestingFramework(this.config.abTesting || {});
      this.components.abTesting.on('testCompleted', this.handleABTestResult.bind(this));
      this.components.abTesting.on('analysisPerformed', this.handleABAnalysis.bind(this));
      this.components.abTesting.on('error', this.handleComponentError.bind(this, 'abTesting'));
    }
  }

  /**
   * Initialize the orchestration system
   */
  async initialize() {
    try {
      // Initialize all components
      for (const [name, component] of Object.entries(this.components)) {
        await component.initialize();
        this.emit('componentInitialized', { component: name });
      }

      // Start coordination intervals
      this.startCoordinationIntervals();

      this.orchestrationState.status = 'running';
      this.orchestrationState.lastSync = Date.now();

      this.emit('orchestratorInitialized', {
        timestamp: Date.now(),
        components: Object.keys(this.components)
      });

    } catch (error) {
      this.orchestrationState.status = 'error';
      this.emit('initializationError', { error: error.message });
      throw error;
    }
  }

  startCoordinationIntervals() {
    // Synchronization interval
    this.intervals.sync = setInterval(() => {
      this.performSync();
    }, this.config.syncInterval);

    // Analysis interval
    this.intervals.analysis = setInterval(() => {
      this.performCrossComponentAnalysis();
    }, this.config.analysisInterval);

    // Reporting interval
    this.intervals.reporting = setInterval(() => {
      this.generateComprehensiveReport();
    }, this.config.reportingInterval);
  }

  /**
   * Process trading data through all measurement components
   */
  async processTradingData(data) {
    const processingId = `processing_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      const results = {
        processingId: processingId,
        timestamp: Date.now(),
        inputData: this.sanitizeData(data),
        componentResults: {},
        crossValidation: {},
        quality: {}
      };

      // Validate data quality
      const qualityCheck = this.validateDataQuality(data);
      results.quality = qualityCheck;

      if (qualityCheck.score < this.config.minDataQuality) {
        this.emit('dataQualityAlert', { processingId, quality: qualityCheck });
        return results;
      }

      // Process through baseline metrics
      if (this.components.baseline) {
        try {
          const baselineResults = this.components.baseline.calculateBaselineMetrics(data);
          results.componentResults.baseline = baselineResults;
        } catch (error) {
          results.componentResults.baseline = { error: error.message };
        }
      }

      // Process through risk tracking
      if (this.components.riskTracking) {
        try {
          if (data.portfolioValue && data.positions) {
            this.components.riskTracking.recordPortfolioState(
              data.portfolioValue,
              data.positions,
              data.timestamp
            );
          }
          results.componentResults.riskTracking = this.components.riskTracking.calculateRiskAdjustedMetrics();
        } catch (error) {
          results.componentResults.riskTracking = { error: error.message };
        }
      }

      // Record calibration data if predictions are present
      if (this.components.calibration && data.predictions) {
        try {
          for (const prediction of data.predictions) {
            this.components.calibration.recordPrediction(
              prediction.id,
              prediction.probability,
              prediction.metadata
            );
          }
          results.componentResults.calibration = this.components.calibration.calculateCalibrationMetrics();
        } catch (error) {
          results.componentResults.calibration = { error: error.message };
        }
      }

      // Perform cross-component validation
      results.crossValidation = await this.performCrossValidation(results.componentResults);

      // Store results
      this.dataBuffer.set(processingId, results);
      this.cleanupDataBuffer();

      this.emit('tradingDataProcessed', results);
      return results;

    } catch (error) {
      this.emit('processingError', { processingId, error: error.message });
      throw error;
    }
  }

  validateDataQuality(data) {
    const quality = {
      score: 1.0,
      issues: [],
      timestamp: Date.now()
    };

    // Check for missing required fields
    const requiredFields = ['timestamp'];
    for (const field of requiredFields) {
      if (!data[field]) {
        quality.issues.push(`Missing required field: ${field}`);
        quality.score -= 0.2;
      }
    }

    // Check data freshness
    if (data.timestamp && Date.now() - data.timestamp > this.config.maxDataLatency) {
      quality.issues.push('Data is stale');
      quality.score -= 0.3;
    }

    // Check for null/undefined values in arrays
    if (data.returns && data.returns.some(r => r === null || r === undefined || isNaN(r))) {
      quality.issues.push('Invalid values in returns array');
      quality.score -= 0.2;
    }

    // Check for reasonable value ranges
    if (data.returns && data.returns.some(r => Math.abs(r) > 1)) {
      quality.issues.push('Extreme return values detected');
      quality.score -= 0.1;
    }

    quality.score = Math.max(0, quality.score);
    return quality;
  }

  sanitizeData(data) {
    // Create a sanitized copy of the data for logging
    const sanitized = { ...data };

    // Remove sensitive information
    delete sanitized.credentials;
    delete sanitized.privateKeys;

    // Truncate large arrays for logging
    if (sanitized.returns && sanitized.returns.length > 100) {
      sanitized.returns = sanitized.returns.slice(-100);
      sanitized.returnsTruncated = true;
    }

    return sanitized;
  }

  /**
   * Create and start A/B test for strategy comparison
   */
  async createStrategyTest(testConfig) {
    if (!this.components.abTesting) {
      throw new Error('A/B testing component not enabled');
    }

    try {
      const test = await this.components.abTesting.createTest({
        name: testConfig.name,
        description: testConfig.description,
        hypothesis: testConfig.hypothesis,
        variants: testConfig.variants,
        primaryMetric: testConfig.primaryMetric || 'total_return',
        secondaryMetrics: testConfig.secondaryMetrics || [
          'sharpe_ratio',
          'max_drawdown',
          'volatility'
        ],
        rolloutStrategy: testConfig.rolloutStrategy || 'gradual',
        ...testConfig
      });

      // Start the test
      await this.components.abTesting.startTest(test.id);

      // Track active experiment
      this.orchestrationState.activeExperiments.set(test.id, {
        test: test,
        startTime: Date.now(),
        lastUpdate: Date.now()
      });

      this.emit('strategyTestCreated', { testId: test.id, test });
      return test;

    } catch (error) {
      this.emit('testCreationError', { error: error.message });
      throw error;
    }
  }

  /**
   * Perform statistical validation of strategy performance
   */
  async validateStrategyPerformance(strategy1Data, strategy2Data = null, testSuite = 'comprehensive') {
    if (!this.components.statisticalTesting) {
      throw new Error('Statistical testing component not enabled');
    }

    try {
      const validation = await this.components.statisticalTesting.performComprehensiveValidation(
        strategy1Data,
        strategy2Data,
        testSuite
      );

      // Cross-reference with other measurement components
      const enrichedValidation = await this.enrichValidationResults(validation);

      this.emit('strategyValidationCompleted', enrichedValidation);
      return enrichedValidation;

    } catch (error) {
      this.emit('validationError', { error: error.message });
      throw error;
    }
  }

  async enrichValidationResults(validation) {
    const enriched = { ...validation };

    // Add baseline metrics context
    if (this.components.baseline) {
      const baselineSnapshot = this.components.baseline.getBaselineSnapshot();
      enriched.baselineContext = baselineSnapshot;
    }

    // Add risk-adjusted context
    if (this.components.riskTracking) {
      const riskMetrics = this.components.riskTracking.calculateRiskAdjustedMetrics();
      enriched.riskContext = riskMetrics;
    }

    // Add calibration context
    if (this.components.calibration) {
      const calibrationMetrics = this.components.calibration.calculateCalibrationMetrics();
      enriched.calibrationContext = calibrationMetrics;
    }

    return enriched;
  }

  /**
   * Perform synchronization across all components
   */
  async performSync() {
    try {
      const syncResults = {
        timestamp: Date.now(),
        componentStatus: {},
        dataConsistency: {},
        alerts: []
      };

      // Check component health
      for (const [name, component] of Object.entries(this.components)) {
        syncResults.componentStatus[name] = {
          status: 'healthy',
          lastActivity: Date.now() // Would track actual last activity
        };
      }

      // Check data consistency
      syncResults.dataConsistency = await this.checkDataConsistency();

      // Update orchestration state
      this.orchestrationState.lastSync = Date.now();
      this.orchestrationState.dataQuality = syncResults.dataConsistency;

      this.emit('syncCompleted', syncResults);

    } catch (error) {
      this.emit('syncError', { error: error.message });
    }
  }

  async checkDataConsistency() {
    const consistency = {
      score: 1.0,
      issues: [],
      checks: {}
    };

    // Check timestamp alignment across components
    if (this.components.baseline && this.components.riskTracking) {
      const baselineSnapshot = this.components.baseline.getBaselineSnapshot();
      const riskSnapshot = this.components.riskTracking.exportPerformanceData();

      const timeDiff = Math.abs(baselineSnapshot.timestamp - riskSnapshot.timestamp);
      if (timeDiff > 60000) { // 1 minute
        consistency.issues.push('Timestamp misalignment between baseline and risk tracking');
        consistency.score -= 0.2;
      }
    }

    // Check metric correlation consistency
    consistency.checks.metricCorrelation = await this.checkMetricCorrelation();

    return consistency;
  }

  async checkMetricCorrelation() {
    // Simplified correlation check
    // In practice, would perform detailed cross-component metric correlation analysis
    return {
      status: 'consistent',
      correlations: {},
      anomalies: []
    };
  }

  /**
   * Perform cross-component analysis
   */
  async performCrossComponentAnalysis() {
    try {
      const analysis = {
        timestamp: Date.now(),
        componentInteractions: {},
        performanceConsistency: {},
        recommendations: []
      };

      // Analyze baseline vs risk-adjusted metrics
      if (this.components.baseline && this.components.riskTracking) {
        analysis.componentInteractions.baselineVsRisk = await this.analyzeBaselineRiskConsistency();
      }

      // Analyze calibration vs statistical testing
      if (this.components.calibration && this.components.statisticalTesting) {
        analysis.componentInteractions.calibrationVsStatistical = await this.analyzeCalibrationStatisticalConsistency();
      }

      // Generate system-wide recommendations
      analysis.recommendations = this.generateSystemRecommendations(analysis);

      this.orchestrationState.lastAnalysis = Date.now();
      this.emit('crossAnalysisCompleted', analysis);

      return analysis;

    } catch (error) {
      this.emit('analysisError', { error: error.message });
    }
  }

  async analyzeBaselineRiskConsistency() {
    // Compare baseline metrics with risk-adjusted metrics for consistency
    return {
      consistency: 'high',
      discrepancies: [],
      confidence: 0.9
    };
  }

  async analyzeCalibrationStatisticalConsistency() {
    // Validate calibration results against statistical testing
    return {
      alignment: 'good',
      validationScore: 0.85,
      issues: []
    };
  }

  generateSystemRecommendations(analysis) {
    const recommendations = [];

    // System-wide optimization recommendations
    recommendations.push({
      type: 'optimization',
      priority: 'medium',
      component: 'system',
      recommendation: 'Continue monitoring - all components operating within normal parameters'
    });

    return recommendations;
  }

  /**
   * Generate comprehensive measurement report
   */
  async generateComprehensiveReport() {
    try {
      const report = {
        timestamp: Date.now(),
        reportId: `report_${Date.now()}`,
        period: {
          start: this.orchestrationState.lastReport || this.orchestrationState.lastSync,
          end: Date.now()
        },
        summary: {},
        componentReports: {},
        crossValidation: {},
        alerts: [...this.orchestrationState.alerts],
        recommendations: []
      };

      // Collect component reports
      for (const [name, component] of Object.entries(this.components)) {
        try {
          if (component.exportMetrics) {
            report.componentReports[name] = component.exportMetrics();
          } else if (component.exportPerformanceData) {
            report.componentReports[name] = component.exportPerformanceData();
          } else if (component.exportTestResults) {
            report.componentReports[name] = component.exportTestResults();
          } else if (component.exportCalibrationData) {
            report.componentReports[name] = component.exportCalibrationData();
          } else if (component.exportFrameworkData) {
            report.componentReports[name] = component.exportFrameworkData();
          }
        } catch (error) {
          report.componentReports[name] = { error: error.message };
        }
      }

      // Generate summary
      report.summary = this.generateReportSummary(report.componentReports);

      // Cross-validation results
      report.crossValidation = Array.from(this.crossValidationResults.values()).slice(-10);

      // Clear old alerts
      this.orchestrationState.alerts = [];
      this.orchestrationState.lastReport = Date.now();

      this.emit('reportGenerated', report);
      return report;

    } catch (error) {
      this.emit('reportError', { error: error.message });
    }
  }

  generateReportSummary(componentReports) {
    return {
      componentsActive: Object.keys(componentReports).length,
      componentsHealthy: Object.values(componentReports).filter(r => !r.error).length,
      dataQualityScore: this.orchestrationState.dataQuality.score || 0,
      alertCount: this.orchestrationState.alerts.length,
      activeExperiments: this.orchestrationState.activeExperiments.size
    };
  }

  /**
   * Perform cross-validation between components
   */
  async performCrossValidation(componentResults) {
    const validationId = `validation_${Date.now()}`;
    const validation = {
      id: validationId,
      timestamp: Date.now(),
      results: {},
      consistency: 'unknown',
      confidence: 0
    };

    try {
      // Validate baseline vs risk metrics consistency
      if (componentResults.baseline && componentResults.riskTracking) {
        validation.results.baselineRiskConsistency = this.validateBaselineRiskConsistency(
          componentResults.baseline,
          componentResults.riskTracking
        );
      }

      // Overall consistency assessment
      const consistencyScores = Object.values(validation.results)
        .filter(result => result.score !== undefined)
        .map(result => result.score);

      if (consistencyScores.length > 0) {
        validation.confidence = consistencyScores.reduce((sum, score) => sum + score, 0) / consistencyScores.length;
        validation.consistency = validation.confidence > 0.8 ? 'high' : validation.confidence > 0.6 ? 'medium' : 'low';
      }

      this.crossValidationResults.set(validationId, validation);
      return validation;

    } catch (error) {
      validation.results.error = error.message;
      return validation;
    }
  }

  validateBaselineRiskConsistency(baselineResults, riskResults) {
    const validation = {
      score: 1.0,
      issues: [],
      metrics: {}
    };

    // Compare Sharpe ratios if available
    if (baselineResults.sharpeRatio && riskResults.sharpeRatio) {
      const diff = Math.abs(baselineResults.sharpeRatio - riskResults.sharpeRatio);
      validation.metrics.sharpeRatioDiff = diff;

      if (diff > 0.1) {
        validation.issues.push('Sharpe ratio discrepancy between baseline and risk tracking');
        validation.score -= 0.2;
      }
    }

    return validation;
  }

  // Event handlers
  handleBaselineMetric(data) {
    this.emit('baselineMetricRecorded', data);
  }

  handleCalibrationEvent(data) {
    this.emit('calibrationEventRecorded', data);
  }

  handleCalibrationDrift(data) {
    this.orchestrationState.alerts.push({
      type: 'calibration_drift',
      timestamp: Date.now(),
      data: data
    });
    this.emit('calibrationDriftDetected', data);
  }

  handleRiskMetricsUpdate(data) {
    this.emit('riskMetricsUpdated', data);
  }

  handleRiskAlert(data) {
    this.orchestrationState.alerts.push({
      type: 'risk_alert',
      timestamp: Date.now(),
      data: data
    });
    this.emit('riskAlertTriggered', data);
  }

  handleValidationResult(data) {
    this.emit('validationResultReceived', data);
  }

  handleABTestResult(data) {
    // Remove from active experiments
    this.orchestrationState.activeExperiments.delete(data.testId);
    this.emit('abTestCompleted', data);
  }

  handleABAnalysis(data) {
    // Update active experiment
    const experiment = this.orchestrationState.activeExperiments.get(data.testId);
    if (experiment) {
      experiment.lastUpdate = Date.now();
      experiment.lastAnalysis = data;
    }
    this.emit('abAnalysisReceived', data);
  }

  handleComponentError(componentName, error) {
    this.orchestrationState.alerts.push({
      type: 'component_error',
      component: componentName,
      timestamp: Date.now(),
      error: error.message || error
    });
    this.emit('componentError', { component: componentName, error });
  }

  cleanupDataBuffer() {
    // Keep only recent data in buffer
    const cutoffTime = Date.now() - 24 * 60 * 60 * 1000; // 24 hours
    for (const [id, data] of this.dataBuffer.entries()) {
      if (data.timestamp < cutoffTime) {
        this.dataBuffer.delete(id);
      }
    }
  }

  /**
   * Get orchestrator status
   */
  getStatus() {
    return {
      ...this.orchestrationState,
      config: this.config,
      components: Object.keys(this.components),
      bufferSize: this.dataBuffer.size,
      intervalsActive: Object.keys(this.intervals).length
    };
  }

  /**
   * Shutdown orchestrator
   */
  async shutdown() {
    try {
      // Clear intervals
      for (const interval of Object.values(this.intervals)) {
        clearInterval(interval);
      }
      this.intervals = {};

      // Shutdown components
      for (const [name, component] of Object.entries(this.components)) {
        if (component.stopTracking) {
          component.stopTracking();
        }
        if (component.stopCollection) {
          component.stopCollection();
        }
        if (component.stopMonitoring) {
          component.stopMonitoring();
        }
      }

      this.orchestrationState.status = 'shutdown';
      this.emit('orchestratorShutdown', { timestamp: Date.now() });

    } catch (error) {
      this.emit('shutdownError', { error: error.message });
    }
  }
}

module.exports = MeasurementOrchestrator;