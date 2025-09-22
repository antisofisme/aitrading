/**
 * A/B Testing Framework for Gradual Rollout and Performance Validation
 * Comprehensive framework for controlled experiments in trading strategies
 */

const EventEmitter = require('events');
const crypto = require('crypto');

class ABTestingFramework extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      defaultSplitRatio: config.defaultSplitRatio || 0.5,
      minSampleSize: config.minSampleSize || 100,
      maxTestDuration: config.maxTestDuration || 30 * 24 * 60 * 60 * 1000, // 30 days
      significanceLevel: config.significanceLevel || 0.05,
      powerLevel: config.powerLevel || 0.8,
      minimumDetectableEffect: config.minimumDetectableEffect || 0.05, // 5%
      earlyStoppingEnabled: config.earlyStoppingEnabled || true,
      rolloutStrategy: config.rolloutStrategy || 'gradual', // gradual, canary, blue-green
      ...config
    };

    this.activeTests = new Map();
    this.completedTests = new Map();
    this.testHistory = [];
    this.userAssignments = new Map();
    this.rolloutStages = new Map();
    this.monitoringIntervals = new Map();
  }

  /**
   * Initialize A/B testing framework
   */
  async initialize() {
    this.startMonitoring();
    this.emit('initialized', { timestamp: Date.now() });
  }

  /**
   * Create a new A/B test
   */
  async createTest(testConfig) {
    const testId = this.generateTestId();

    const test = {
      id: testId,
      name: testConfig.name,
      description: testConfig.description || '',
      hypothesis: testConfig.hypothesis,

      // Test configuration
      variants: this.validateVariants(testConfig.variants),
      splitRatio: testConfig.splitRatio || this.config.defaultSplitRatio,

      // Success metrics
      primaryMetric: testConfig.primaryMetric,
      secondaryMetrics: testConfig.secondaryMetrics || [],

      // Test parameters
      minSampleSize: testConfig.minSampleSize || this.config.minSampleSize,
      maxDuration: testConfig.maxDuration || this.config.maxTestDuration,
      significanceLevel: testConfig.significanceLevel || this.config.significanceLevel,

      // Rollout configuration
      rolloutStrategy: testConfig.rolloutStrategy || this.config.rolloutStrategy,
      rolloutStages: this.generateRolloutStages(testConfig),

      // State
      status: 'created',
      startTime: null,
      endTime: null,
      currentStage: 0,

      // Data collection
      participants: new Map(),
      results: new Map(),
      metrics: new Map(),

      // Statistical analysis
      statisticalSignificance: null,
      confidenceInterval: null,
      pValue: null,
      effectSize: null,

      // Metadata
      createdAt: Date.now(),
      createdBy: testConfig.createdBy || 'system'
    };

    this.activeTests.set(testId, test);
    this.emit('testCreated', { testId, test });

    return test;
  }

  validateVariants(variants) {
    if (!variants || variants.length < 2) {
      throw new Error('At least 2 variants required for A/B test');
    }

    return variants.map((variant, index) => ({
      id: variant.id || `variant_${index}`,
      name: variant.name || `Variant ${index}`,
      description: variant.description || '',
      configuration: variant.configuration || {},
      isControl: variant.isControl || index === 0,
      weight: variant.weight || (1 / variants.length)
    }));
  }

  generateRolloutStages(testConfig) {
    const strategy = testConfig.rolloutStrategy || this.config.rolloutStrategy;

    switch (strategy) {
      case 'gradual':
        return [
          { stage: 1, percentage: 0.01, duration: 1 * 24 * 60 * 60 * 1000 }, // 1% for 1 day
          { stage: 2, percentage: 0.05, duration: 2 * 24 * 60 * 60 * 1000 }, // 5% for 2 days
          { stage: 3, percentage: 0.10, duration: 3 * 24 * 60 * 60 * 1000 }, // 10% for 3 days
          { stage: 4, percentage: 0.25, duration: 7 * 24 * 60 * 60 * 1000 }, // 25% for 7 days
          { stage: 5, percentage: 0.50, duration: 14 * 24 * 60 * 60 * 1000 }, // 50% for 14 days
          { stage: 6, percentage: 1.00, duration: null } // Full rollout
        ];

      case 'canary':
        return [
          { stage: 1, percentage: 0.05, duration: 7 * 24 * 60 * 60 * 1000 }, // 5% canary
          { stage: 2, percentage: 1.00, duration: null } // Full rollout
        ];

      case 'blue-green':
        return [
          { stage: 1, percentage: 0.50, duration: testConfig.maxDuration } // 50-50 split
        ];

      default:
        return [
          { stage: 1, percentage: 1.00, duration: testConfig.maxDuration }
        ];
    }
  }

  /**
   * Start an A/B test
   */
  async startTest(testId) {
    const test = this.activeTests.get(testId);
    if (!test) {
      throw new Error(`Test ${testId} not found`);
    }

    if (test.status !== 'created') {
      throw new Error(`Test ${testId} cannot be started (current status: ${test.status})`);
    }

    test.status = 'running';
    test.startTime = Date.now();
    test.currentStage = 0;

    // Initialize metrics tracking
    test.variants.forEach(variant => {
      test.metrics.set(variant.id, {
        participantCount: 0,
        conversionCount: 0,
        primaryMetricSum: 0,
        primaryMetricValues: [],
        secondaryMetrics: {}
      });
    });

    // Start first rollout stage
    await this.advanceToNextStage(testId);

    // Set up monitoring
    this.startTestMonitoring(testId);

    this.emit('testStarted', { testId, test });
    return test;
  }

  async advanceToNextStage(testId) {
    const test = this.activeTests.get(testId);
    if (!test) return;

    const nextStage = test.rolloutStages[test.currentStage];
    if (!nextStage) {
      await this.completeTest(testId, 'stages_completed');
      return;
    }

    test.currentStageConfig = nextStage;
    test.stageStartTime = Date.now();

    this.emit('stageAdvanced', {
      testId,
      stage: nextStage.stage,
      percentage: nextStage.percentage
    });

    // Schedule next stage if duration is specified
    if (nextStage.duration) {
      setTimeout(() => {
        this.checkStageCompletion(testId);
      }, nextStage.duration);
    }
  }

  async checkStageCompletion(testId) {
    const test = this.activeTests.get(testId);
    if (!test || test.status !== 'running') return;

    const stageElapsed = Date.now() - test.stageStartTime;
    const currentStage = test.currentStageConfig;

    // Check if stage duration is complete
    if (currentStage.duration && stageElapsed >= currentStage.duration) {
      // Perform interim analysis
      const interimAnalysis = await this.performInterimAnalysis(testId);

      if (this.shouldStopTestEarly(interimAnalysis)) {
        await this.completeTest(testId, 'early_stopping');
        return;
      }

      // Advance to next stage
      test.currentStage++;
      await this.advanceToNextStage(testId);
    }
  }

  /**
   * Assign participant to test variant
   */
  assignParticipant(testId, participantId, metadata = {}) {
    const test = this.activeTests.get(testId);
    if (!test || test.status !== 'running') {
      return null;
    }

    // Check if participant already assigned
    if (test.participants.has(participantId)) {
      return test.participants.get(participantId);
    }

    // Check rollout percentage
    const rolloutHash = this.generateRolloutHash(participantId, testId);
    if (rolloutHash > test.currentStageConfig.percentage) {
      return null; // Participant not included in current rollout stage
    }

    // Assign to variant
    const variant = this.selectVariant(test, participantId);
    const assignment = {
      participantId: participantId,
      variantId: variant.id,
      assignedAt: Date.now(),
      stage: test.currentStage,
      metadata: metadata
    };

    test.participants.set(participantId, assignment);
    this.userAssignments.set(participantId, { testId, assignment });

    // Update metrics
    const variantMetrics = test.metrics.get(variant.id);
    variantMetrics.participantCount++;

    this.emit('participantAssigned', { testId, assignment });
    return assignment;
  }

  selectVariant(test, participantId) {
    // Use deterministic hash for consistent assignment
    const hash = this.generateVariantHash(participantId, test.id);

    let cumulativeWeight = 0;
    for (const variant of test.variants) {
      cumulativeWeight += variant.weight;
      if (hash <= cumulativeWeight) {
        return variant;
      }
    }

    // Fallback to first variant
    return test.variants[0];
  }

  generateRolloutHash(participantId, testId) {
    const hash = crypto.createHash('md5').update(`rollout_${participantId}_${testId}`).digest('hex');
    return parseInt(hash.substring(0, 8), 16) / 0xffffffff;
  }

  generateVariantHash(participantId, testId) {
    const hash = crypto.createHash('md5').update(`variant_${participantId}_${testId}`).digest('hex');
    return parseInt(hash.substring(0, 8), 16) / 0xffffffff;
  }

  /**
   * Record metric for test participant
   */
  recordMetric(testId, participantId, metricName, value, timestamp = Date.now()) {
    const test = this.activeTests.get(testId);
    if (!test) return false;

    const assignment = test.participants.get(participantId);
    if (!assignment) return false;

    const variantMetrics = test.metrics.get(assignment.variantId);
    if (!variantMetrics) return false;

    // Record primary metric
    if (metricName === test.primaryMetric) {
      variantMetrics.primaryMetricSum += value;
      variantMetrics.primaryMetricValues.push({
        value: value,
        timestamp: timestamp,
        participantId: participantId
      });

      // Count conversions (assuming positive values are conversions)
      if (value > 0) {
        variantMetrics.conversionCount++;
      }
    } else {
      // Record secondary metrics
      if (!variantMetrics.secondaryMetrics[metricName]) {
        variantMetrics.secondaryMetrics[metricName] = {
          sum: 0,
          count: 0,
          values: []
        };
      }

      variantMetrics.secondaryMetrics[metricName].sum += value;
      variantMetrics.secondaryMetrics[metricName].count++;
      variantMetrics.secondaryMetrics[metricName].values.push({
        value: value,
        timestamp: timestamp,
        participantId: participantId
      });
    }

    this.emit('metricRecorded', { testId, participantId, metricName, value });

    // Check if we should perform analysis
    this.checkAnalysisThreshold(testId);

    return true;
  }

  checkAnalysisThreshold(testId) {
    const test = this.activeTests.get(testId);
    if (!test) return;

    // Check if minimum sample size reached
    const totalParticipants = Array.from(test.metrics.values())
      .reduce((sum, metrics) => sum + metrics.participantCount, 0);

    if (totalParticipants >= test.minSampleSize) {
      // Perform periodic analysis
      const lastAnalysis = test.lastAnalysisTime || 0;
      const timeSinceLastAnalysis = Date.now() - lastAnalysis;

      if (timeSinceLastAnalysis > 60 * 60 * 1000) { // 1 hour
        this.performPeriodicAnalysis(testId);
      }
    }
  }

  async performPeriodicAnalysis(testId) {
    const test = this.activeTests.get(testId);
    if (!test) return;

    test.lastAnalysisTime = Date.now();

    const analysis = await this.calculateTestStatistics(testId);
    test.currentAnalysis = analysis;

    this.emit('analysisPerformed', { testId, analysis });

    // Check for early stopping
    if (this.config.earlyStoppingEnabled && this.shouldStopTestEarly(analysis)) {
      await this.completeTest(testId, 'early_stopping');
    }
  }

  async performInterimAnalysis(testId) {
    return await this.calculateTestStatistics(testId);
  }

  async calculateTestStatistics(testId) {
    const test = this.activeTests.get(testId);
    if (!test) return null;

    const analysis = {
      timestamp: Date.now(),
      testId: testId,
      variants: {},
      comparison: {},
      recommendations: []
    };

    // Calculate metrics for each variant
    for (const variant of test.variants) {
      const metrics = test.metrics.get(variant.id);
      const variantAnalysis = {
        id: variant.id,
        name: variant.name,
        isControl: variant.isControl,
        participantCount: metrics.participantCount,
        conversionCount: metrics.conversionCount,
        conversionRate: metrics.participantCount > 0 ? metrics.conversionCount / metrics.participantCount : 0,
        primaryMetricMean: metrics.primaryMetricValues.length > 0 ?
          metrics.primaryMetricSum / metrics.primaryMetricValues.length : 0,
        primaryMetricStd: this.calculateStandardDeviation(metrics.primaryMetricValues.map(v => v.value)),
        confidence: this.calculateConfidenceInterval(metrics.primaryMetricValues.map(v => v.value))
      };

      analysis.variants[variant.id] = variantAnalysis;
    }

    // Perform statistical comparison
    const controlVariant = test.variants.find(v => v.isControl);
    const treatmentVariants = test.variants.filter(v => !v.isControl);

    for (const treatment of treatmentVariants) {
      const comparison = await this.performStatisticalComparison(
        analysis.variants[controlVariant.id],
        analysis.variants[treatment.id]
      );

      analysis.comparison[treatment.id] = comparison;
    }

    // Generate recommendations
    analysis.recommendations = this.generateRecommendations(analysis);

    return analysis;
  }

  async performStatisticalComparison(control, treatment) {
    const controlValues = control.primaryMetricValues || [];
    const treatmentValues = treatment.primaryMetricValues || [];

    if (controlValues.length < 10 || treatmentValues.length < 10) {
      return {
        significance: 'insufficient_data',
        pValue: null,
        effectSize: null,
        recommendation: 'continue_test'
      };
    }

    // Perform two-sample t-test
    const tTestResult = this.performTwoSampleTTest(controlValues, treatmentValues);

    // Calculate effect size (Cohen's d)
    const effectSize = this.calculateCohenD(controlValues, treatmentValues);

    // Calculate confidence interval for difference
    const meanDifference = treatment.primaryMetricMean - control.primaryMetricMean;
    const relativeLift = control.primaryMetricMean !== 0 ?
      (meanDifference / control.primaryMetricMean) * 100 : 0;

    return {
      pValue: tTestResult.pValue,
      isSignificant: tTestResult.pValue < this.config.significanceLevel,
      effectSize: effectSize,
      meanDifference: meanDifference,
      relativeLift: relativeLift,
      confidenceInterval: tTestResult.confidenceInterval,
      sampleSizesEqual: Math.abs(controlValues.length - treatmentValues.length) < 10,
      recommendation: this.determineRecommendation(tTestResult, effectSize)
    };
  }

  performTwoSampleTTest(sample1, sample2) {
    const n1 = sample1.length;
    const n2 = sample2.length;

    const mean1 = sample1.reduce((sum, val) => sum + val, 0) / n1;
    const mean2 = sample2.reduce((sum, val) => sum + val, 0) / n2;

    const var1 = this.calculateVariance(sample1);
    const var2 = this.calculateVariance(sample2);

    // Welch's t-test (unequal variances)
    const standardError = Math.sqrt(var1/n1 + var2/n2);
    const tStatistic = (mean1 - mean2) / standardError;

    // Degrees of freedom (Welch-Satterthwaite)
    const df = Math.pow(var1/n1 + var2/n2, 2) /
      (Math.pow(var1/n1, 2)/(n1-1) + Math.pow(var2/n2, 2)/(n2-1));

    // Calculate p-value (simplified)
    const pValue = 2 * (1 - this.tDistributionCDF(Math.abs(tStatistic), df));

    // Confidence interval for difference
    const criticalValue = this.tDistributionInverse(1 - this.config.significanceLevel/2, df);
    const marginOfError = criticalValue * standardError;
    const meanDifference = mean1 - mean2;

    return {
      tStatistic: tStatistic,
      pValue: pValue,
      degreesOfFreedom: df,
      confidenceInterval: {
        lower: meanDifference - marginOfError,
        upper: meanDifference + marginOfError,
        level: 1 - this.config.significanceLevel
      }
    };
  }

  calculateCohenD(sample1, sample2) {
    const mean1 = sample1.reduce((sum, val) => sum + val, 0) / sample1.length;
    const mean2 = sample2.reduce((sum, val) => sum + val, 0) / sample2.length;

    const var1 = this.calculateVariance(sample1);
    const var2 = this.calculateVariance(sample2);

    // Pooled standard deviation
    const pooledStd = Math.sqrt((var1 + var2) / 2);

    return pooledStd === 0 ? 0 : (mean1 - mean2) / pooledStd;
  }

  shouldStopTestEarly(analysis) {
    if (!analysis || !analysis.comparison) return false;

    for (const comparison of Object.values(analysis.comparison)) {
      // Stop if highly significant and large effect
      if (comparison.isSignificant &&
          comparison.pValue < 0.01 &&
          Math.abs(comparison.effectSize) > 0.5) {
        return true;
      }

      // Stop if futility detected (very small effect size with large sample)
      const totalSampleSize = Object.values(analysis.variants)
        .reduce((sum, variant) => sum + variant.participantCount, 0);

      if (totalSampleSize > this.config.minSampleSize * 2 &&
          Math.abs(comparison.effectSize) < 0.1) {
        return true;
      }
    }

    return false;
  }

  determineRecommendation(tTestResult, effectSize) {
    if (tTestResult.pValue < 0.01 && Math.abs(effectSize) > 0.5) {
      return 'stop_significant';
    } else if (tTestResult.pValue > 0.5 && Math.abs(effectSize) < 0.1) {
      return 'stop_futile';
    } else if (tTestResult.pValue < 0.05) {
      return 'trending_significant';
    } else {
      return 'continue_test';
    }
  }

  generateRecommendations(analysis) {
    const recommendations = [];

    for (const [variantId, comparison] of Object.entries(analysis.comparison)) {
      const variant = analysis.variants[variantId];

      if (comparison.isSignificant) {
        if (comparison.relativeLift > 0) {
          recommendations.push({
            type: 'winner_detected',
            variant: variantId,
            confidence: 'high',
            lift: comparison.relativeLift,
            message: `${variant.name} shows significant improvement (${comparison.relativeLift.toFixed(2)}% lift)`
          });
        } else {
          recommendations.push({
            type: 'performance_decline',
            variant: variantId,
            confidence: 'high',
            impact: comparison.relativeLift,
            message: `${variant.name} shows significant decline (${Math.abs(comparison.relativeLift).toFixed(2)}% drop)`
          });
        }
      } else if (comparison.recommendation === 'stop_futile') {
        recommendations.push({
          type: 'futile_test',
          variant: variantId,
          confidence: 'medium',
          message: 'Test is unlikely to detect meaningful difference with current sample size'
        });
      }
    }

    return recommendations;
  }

  /**
   * Complete an A/B test
   */
  async completeTest(testId, reason = 'manual') {
    const test = this.activeTests.get(testId);
    if (!test) {
      throw new Error(`Test ${testId} not found`);
    }

    test.status = 'completed';
    test.endTime = Date.now();
    test.completionReason = reason;

    // Perform final analysis
    const finalAnalysis = await this.calculateTestStatistics(testId);
    test.finalAnalysis = finalAnalysis;

    // Stop monitoring
    this.stopTestMonitoring(testId);

    // Move to completed tests
    this.completedTests.set(testId, test);
    this.activeTests.delete(testId);
    this.testHistory.push(test);

    this.emit('testCompleted', { testId, test, reason });

    return test;
  }

  startTestMonitoring(testId) {
    const interval = setInterval(() => {
      this.checkTestHealth(testId);
    }, 60 * 60 * 1000); // Check every hour

    this.monitoringIntervals.set(testId, interval);
  }

  stopTestMonitoring(testId) {
    const interval = this.monitoringIntervals.get(testId);
    if (interval) {
      clearInterval(interval);
      this.monitoringIntervals.delete(testId);
    }
  }

  checkTestHealth(testId) {
    const test = this.activeTests.get(testId);
    if (!test) return;

    // Check test duration
    const elapsed = Date.now() - test.startTime;
    if (elapsed > test.maxDuration) {
      this.completeTest(testId, 'max_duration_reached');
      return;
    }

    // Check for data quality issues
    const totalParticipants = Array.from(test.metrics.values())
      .reduce((sum, metrics) => sum + metrics.participantCount, 0);

    if (totalParticipants === 0 && elapsed > 24 * 60 * 60 * 1000) { // No participants after 1 day
      this.emit('testHealthAlert', {
        testId: testId,
        alert: 'no_participants',
        message: 'No participants assigned after 24 hours'
      });
    }
  }

  // Utility functions
  calculateVariance(data) {
    if (data.length < 2) return 0;
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    return data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (data.length - 1);
  }

  calculateStandardDeviation(data) {
    return Math.sqrt(this.calculateVariance(data));
  }

  calculateConfidenceInterval(data, confidence = 0.95) {
    if (data.length < 2) return { lower: 0, upper: 0 };

    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const std = this.calculateStandardDeviation(data);
    const margin = 1.96 * (std / Math.sqrt(data.length)); // Using z-score for large samples

    return {
      lower: mean - margin,
      upper: mean + margin,
      level: confidence
    };
  }

  tDistributionCDF(t, df) {
    // Simplified implementation
    if (df > 30) {
      return this.normalCDF(t);
    }
    return 0.5 + 0.5 * Math.sign(t) * Math.sqrt(1 - Math.exp(-2 * t * t / Math.PI));
  }

  normalCDF(z) {
    return 0.5 * (1 + this.erf(z / Math.sqrt(2)));
  }

  erf(x) {
    const a1 =  0.254829592;
    const a2 = -0.284496736;
    const a3 =  1.421413741;
    const a4 = -1.453152027;
    const a5 =  1.061405429;
    const p  =  0.3275911;

    const sign = x >= 0 ? 1 : -1;
    x = Math.abs(x);

    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);

    return sign * y;
  }

  generateTestId() {
    return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  startMonitoring() {
    this.emit('monitoringStarted', { timestamp: Date.now() });
  }

  /**
   * Get test status and results
   */
  getTestStatus(testId) {
    const activeTest = this.activeTests.get(testId);
    if (activeTest) {
      return {
        ...activeTest,
        currentAnalysis: activeTest.currentAnalysis || null,
        isActive: true
      };
    }

    const completedTest = this.completedTests.get(testId);
    if (completedTest) {
      return {
        ...completedTest,
        isActive: false
      };
    }

    return null;
  }

  /**
   * Export framework data
   */
  exportFrameworkData() {
    return {
      timestamp: Date.now(),
      config: this.config,
      activeTests: Object.fromEntries(this.activeTests),
      completedTests: Object.fromEntries(this.completedTests),
      testHistory: this.testHistory,
      summary: {
        totalTests: this.testHistory.length,
        activeTestCount: this.activeTests.size,
        completedTestCount: this.completedTests.size
      }
    };
  }
}

module.exports = ABTestingFramework;