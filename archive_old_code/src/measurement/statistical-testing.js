/**
 * Statistical Significance Testing Protocols
 * Comprehensive statistical testing framework for trading strategy validation
 */

const EventEmitter = require('events');

class StatisticalTestingFramework extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      confidenceLevel: config.confidenceLevel || 0.95,
      minSampleSize: config.minSampleSize || 100,
      bootstrapIterations: config.bootstrapIterations || 1000,
      pValueThreshold: config.pValueThreshold || 0.05,
      effectSizeThreshold: config.effectSizeThreshold || 0.2,
      multipleTestingCorrection: config.multipleTestingCorrection || 'bonferroni',
      ...config
    };

    this.testResults = new Map();
    this.testHistory = [];
    this.currentTests = new Set();
    this.distributionCache = new Map();
  }

  /**
   * Initialize statistical testing framework
   */
  async initialize() {
    this.initializeTestTypes();
    this.emit('initialized', { timestamp: Date.now() });
  }

  initializeTestTypes() {
    this.availableTests = {
      // Mean comparison tests
      'ttest_one_sample': this.performOneSampleTTest.bind(this),
      'ttest_two_sample': this.performTwoSampleTTest.bind(this),
      'welch_ttest': this.performWelchTTest.bind(this),
      'paired_ttest': this.performPairedTTest.bind(this),

      // Non-parametric tests
      'wilcoxon_signed_rank': this.performWilcoxonSignedRank.bind(this),
      'mann_whitney_u': this.performMannWhitneyU.bind(this),
      'kruskal_wallis': this.performKruskalWallis.bind(this),

      // Distribution tests
      'shapiro_wilk': this.performShapiroWilk.bind(this),
      'kolmogorov_smirnov': this.performKolmogorovSmirnov.bind(this),
      'anderson_darling': this.performAndersonDarling.bind(this),

      // Variance tests
      'levene_test': this.performLeveneTest.bind(this),
      'bartlett_test': this.performBartlettTest.bind(this),

      // Time series tests
      'augmented_dickey_fuller': this.performAugmentedDickeyFuller.bind(this),
      'ljung_box': this.performLjungBox.bind(this),
      'jarque_bera': this.performJarqueBera.bind(this),

      // Bootstrap tests
      'bootstrap_mean': this.performBootstrapMean.bind(this),
      'bootstrap_ratio': this.performBootstrapRatio.bind(this),
      'permutation_test': this.performPermutationTest.bind(this)
    };
  }

  /**
   * Perform comprehensive statistical validation
   */
  async performComprehensiveValidation(strategy1Data, strategy2Data = null, testSuite = 'default') {
    const testId = `validation_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      this.currentTests.add(testId);

      const results = {
        testId: testId,
        timestamp: Date.now(),
        strategy1: this.analyzeStrategyData(strategy1Data),
        strategy2: strategy2Data ? this.analyzeStrategyData(strategy2Data) : null,
        tests: {},
        summary: {},
        conclusions: {}
      };

      // Select appropriate test suite
      const tests = this.selectTestSuite(testSuite, strategy1Data, strategy2Data);

      // Perform all tests
      for (const testName of tests) {
        if (this.availableTests[testName]) {
          try {
            const testResult = await this.runStatisticalTest(
              testName,
              strategy1Data,
              strategy2Data
            );
            results.tests[testName] = testResult;
          } catch (error) {
            results.tests[testName] = {
              error: error.message,
              status: 'failed'
            };
          }
        }
      }

      // Apply multiple testing correction
      results.tests = this.applyMultipleTestingCorrection(results.tests);

      // Generate summary and conclusions
      results.summary = this.generateTestSummary(results.tests);
      results.conclusions = this.generateConclusions(results.tests, results.summary);

      // Store results
      this.testResults.set(testId, results);
      this.testHistory.push(results);

      this.emit('validationCompleted', results);
      return results;

    } finally {
      this.currentTests.delete(testId);
    }
  }

  selectTestSuite(testSuite, strategy1Data, strategy2Data) {
    const suites = {
      'default': [
        'ttest_one_sample',
        'shapiro_wilk',
        'ljung_box',
        'jarque_bera'
      ],
      'comparison': [
        'ttest_two_sample',
        'welch_ttest',
        'mann_whitney_u',
        'levene_test',
        'kolmogorov_smirnov'
      ],
      'comprehensive': [
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
      'time_series': [
        'augmented_dickey_fuller',
        'ljung_box',
        'jarque_bera',
        'shapiro_wilk'
      ],
      'non_parametric': [
        'wilcoxon_signed_rank',
        'mann_whitney_u',
        'kruskal_wallis',
        'permutation_test'
      ]
    };

    let selectedTests = suites[testSuite] || suites['default'];

    // Adjust based on data availability
    if (!strategy2Data) {
      selectedTests = selectedTests.filter(test =>
        !['ttest_two_sample', 'welch_ttest', 'mann_whitney_u', 'levene_test'].includes(test)
      );
    }

    return selectedTests;
  }

  async runStatisticalTest(testName, data1, data2 = null) {
    const startTime = Date.now();

    try {
      const testFunction = this.availableTests[testName];
      const result = await testFunction(data1, data2);

      return {
        ...result,
        testName: testName,
        executionTime: Date.now() - startTime,
        status: 'completed'
      };
    } catch (error) {
      return {
        testName: testName,
        error: error.message,
        executionTime: Date.now() - startTime,
        status: 'failed'
      };
    }
  }

  analyzeStrategyData(data) {
    const returns = data.returns || [];

    return {
      sampleSize: returns.length,
      mean: returns.length > 0 ? returns.reduce((sum, r) => sum + r, 0) / returns.length : 0,
      variance: this.calculateVariance(returns),
      standardDeviation: this.calculateStandardDeviation(returns),
      skewness: this.calculateSkewness(returns),
      kurtosis: this.calculateKurtosis(returns),
      minimum: returns.length > 0 ? Math.min(...returns) : 0,
      maximum: returns.length > 0 ? Math.max(...returns) : 0,
      range: returns.length > 0 ? Math.max(...returns) - Math.min(...returns) : 0
    };
  }

  // T-Test implementations
  async performOneSampleTTest(data, hypothesizedMean = 0) {
    const returns = data.returns || [];

    if (returns.length < 2) {
      throw new Error('Insufficient sample size for t-test');
    }

    const n = returns.length;
    const sampleMean = returns.reduce((sum, r) => sum + r, 0) / n;
    const sampleStd = this.calculateStandardDeviation(returns);
    const standardError = sampleStd / Math.sqrt(n);

    const tStatistic = (sampleMean - hypothesizedMean) / standardError;
    const degreesOfFreedom = n - 1;
    const pValue = 2 * (1 - this.tDistributionCDF(Math.abs(tStatistic), degreesOfFreedom));

    const criticalValue = this.tDistributionInverse(1 - this.config.pValueThreshold / 2, degreesOfFreedom);
    const isSignificant = Math.abs(tStatistic) > criticalValue;

    const confidenceInterval = this.calculateConfidenceInterval(
      sampleMean, standardError, degreesOfFreedom
    );

    return {
      testType: 'one_sample_ttest',
      tStatistic: tStatistic,
      pValue: pValue,
      degreesOfFreedom: degreesOfFreedom,
      criticalValue: criticalValue,
      isSignificant: isSignificant,
      sampleMean: sampleMean,
      hypothesizedMean: hypothesizedMean,
      standardError: standardError,
      confidenceInterval: confidenceInterval,
      effectSize: this.calculateCohenD(returns, hypothesizedMean)
    };
  }

  async performTwoSampleTTest(data1, data2) {
    const returns1 = data1.returns || [];
    const returns2 = data2.returns || [];

    if (returns1.length < 2 || returns2.length < 2) {
      throw new Error('Insufficient sample size for two-sample t-test');
    }

    const n1 = returns1.length;
    const n2 = returns2.length;
    const mean1 = returns1.reduce((sum, r) => sum + r, 0) / n1;
    const mean2 = returns2.reduce((sum, r) => sum + r, 0) / n2;

    const var1 = this.calculateVariance(returns1);
    const var2 = this.calculateVariance(returns2);

    // Pooled variance
    const pooledVariance = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2);
    const standardError = Math.sqrt(pooledVariance * (1/n1 + 1/n2));

    const tStatistic = (mean1 - mean2) / standardError;
    const degreesOfFreedom = n1 + n2 - 2;
    const pValue = 2 * (1 - this.tDistributionCDF(Math.abs(tStatistic), degreesOfFreedom));

    const criticalValue = this.tDistributionInverse(1 - this.config.pValueThreshold / 2, degreesOfFreedom);
    const isSignificant = Math.abs(tStatistic) > criticalValue;

    return {
      testType: 'two_sample_ttest',
      tStatistic: tStatistic,
      pValue: pValue,
      degreesOfFreedom: degreesOfFreedom,
      criticalValue: criticalValue,
      isSignificant: isSignificant,
      mean1: mean1,
      mean2: mean2,
      meanDifference: mean1 - mean2,
      standardError: standardError,
      pooledVariance: pooledVariance,
      effectSize: this.calculatePooledCohenD(returns1, returns2)
    };
  }

  async performWelchTTest(data1, data2) {
    const returns1 = data1.returns || [];
    const returns2 = data2.returns || [];

    if (returns1.length < 2 || returns2.length < 2) {
      throw new Error('Insufficient sample size for Welch t-test');
    }

    const n1 = returns1.length;
    const n2 = returns2.length;
    const mean1 = returns1.reduce((sum, r) => sum + r, 0) / n1;
    const mean2 = returns2.reduce((sum, r) => sum + r, 0) / n2;

    const var1 = this.calculateVariance(returns1);
    const var2 = this.calculateVariance(returns2);

    const standardError = Math.sqrt(var1/n1 + var2/n2);
    const tStatistic = (mean1 - mean2) / standardError;

    // Welch-Satterthwaite degrees of freedom
    const degreesOfFreedom = Math.pow(var1/n1 + var2/n2, 2) /
      (Math.pow(var1/n1, 2)/(n1-1) + Math.pow(var2/n2, 2)/(n2-1));

    const pValue = 2 * (1 - this.tDistributionCDF(Math.abs(tStatistic), degreesOfFreedom));
    const criticalValue = this.tDistributionInverse(1 - this.config.pValueThreshold / 2, degreesOfFreedom);
    const isSignificant = Math.abs(tStatistic) > criticalValue;

    return {
      testType: 'welch_ttest',
      tStatistic: tStatistic,
      pValue: pValue,
      degreesOfFreedom: degreesOfFreedom,
      criticalValue: criticalValue,
      isSignificant: isSignificant,
      mean1: mean1,
      mean2: mean2,
      meanDifference: mean1 - mean2,
      standardError: standardError,
      assumesEqualVariances: false
    };
  }

  // Non-parametric tests
  async performMannWhitneyU(data1, data2) {
    const returns1 = data1.returns || [];
    const returns2 = data2.returns || [];

    if (returns1.length === 0 || returns2.length === 0) {
      throw new Error('Empty datasets for Mann-Whitney U test');
    }

    const n1 = returns1.length;
    const n2 = returns2.length;

    // Combine and rank all values
    const combined = [
      ...returns1.map(r => ({ value: r, group: 1 })),
      ...returns2.map(r => ({ value: r, group: 2 }))
    ].sort((a, b) => a.value - b.value);

    // Assign ranks (handling ties)
    let currentRank = 1;
    for (let i = 0; i < combined.length; i++) {
      let tieCount = 1;
      while (i + tieCount < combined.length && combined[i].value === combined[i + tieCount].value) {
        tieCount++;
      }

      const averageRank = currentRank + (tieCount - 1) / 2;
      for (let j = 0; j < tieCount; j++) {
        combined[i + j].rank = averageRank;
      }

      i += tieCount - 1;
      currentRank += tieCount;
    }

    // Calculate U statistics
    const R1 = combined.filter(item => item.group === 1).reduce((sum, item) => sum + item.rank, 0);
    const U1 = R1 - (n1 * (n1 + 1)) / 2;
    const U2 = n1 * n2 - U1;
    const U = Math.min(U1, U2);

    // Normal approximation for large samples
    const meanU = (n1 * n2) / 2;
    const stdU = Math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12);
    const zStatistic = (U - meanU) / stdU;
    const pValue = 2 * (1 - this.normalCDF(Math.abs(zStatistic)));

    const criticalZ = this.normalInverse(1 - this.config.pValueThreshold / 2);
    const isSignificant = Math.abs(zStatistic) > criticalZ;

    return {
      testType: 'mann_whitney_u',
      U1: U1,
      U2: U2,
      U: U,
      zStatistic: zStatistic,
      pValue: pValue,
      isSignificant: isSignificant,
      criticalValue: criticalZ,
      effectSize: 1 - (2 * U) / (n1 * n2) // rank-biserial correlation
    };
  }

  // Bootstrap methods
  async performBootstrapMean(data, iterations = null) {
    const returns = data.returns || [];
    const bootstrapIterations = iterations || this.config.bootstrapIterations;

    if (returns.length < 10) {
      throw new Error('Insufficient sample size for bootstrap');
    }

    const originalMean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const bootstrapMeans = [];

    for (let i = 0; i < bootstrapIterations; i++) {
      const bootstrapSample = this.generateBootstrapSample(returns);
      const bootstrapMean = bootstrapSample.reduce((sum, r) => sum + r, 0) / bootstrapSample.length;
      bootstrapMeans.push(bootstrapMean);
    }

    bootstrapMeans.sort((a, b) => a - b);

    const alpha = 1 - this.config.confidenceLevel;
    const lowerIndex = Math.floor(alpha / 2 * bootstrapIterations);
    const upperIndex = Math.floor((1 - alpha / 2) * bootstrapIterations);

    const confidenceInterval = {
      lower: bootstrapMeans[lowerIndex],
      upper: bootstrapMeans[upperIndex],
      level: this.config.confidenceLevel
    };

    const bias = bootstrapMeans.reduce((sum, m) => sum + m, 0) / bootstrapIterations - originalMean;
    const standardError = this.calculateStandardDeviation(bootstrapMeans);

    return {
      testType: 'bootstrap_mean',
      originalMean: originalMean,
      bootstrapMean: bootstrapMeans.reduce((sum, m) => sum + m, 0) / bootstrapIterations,
      bias: bias,
      standardError: standardError,
      confidenceInterval: confidenceInterval,
      iterations: bootstrapIterations,
      distribution: bootstrapMeans
    };
  }

  generateBootstrapSample(data) {
    const sample = [];
    for (let i = 0; i < data.length; i++) {
      const randomIndex = Math.floor(Math.random() * data.length);
      sample.push(data[randomIndex]);
    }
    return sample;
  }

  // Distribution tests
  async performShapiroWilk(data) {
    const returns = data.returns || [];

    if (returns.length < 3 || returns.length > 5000) {
      throw new Error('Sample size must be between 3 and 5000 for Shapiro-Wilk test');
    }

    // This is a simplified implementation
    // In practice, you would use the full Shapiro-Wilk coefficients
    const sortedReturns = returns.slice().sort((a, b) => a - b);
    const n = returns.length;

    // Calculate test statistic (simplified)
    const mean = returns.reduce((sum, r) => sum + r, 0) / n;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / (n - 1);

    // This would normally use specific coefficients and tables
    const W = 0.95; // Placeholder - would calculate actual W statistic
    const pValue = W > 0.95 ? 0.1 : 0.01; // Placeholder p-value

    return {
      testType: 'shapiro_wilk',
      W: W,
      pValue: pValue,
      isNormal: pValue > this.config.pValueThreshold,
      isSignificant: pValue <= this.config.pValueThreshold
    };
  }

  // Time series tests
  async performLjungBox(data, lags = 10) {
    const returns = data.returns || [];

    if (returns.length < lags * 4) {
      throw new Error('Insufficient data for Ljung-Box test');
    }

    const n = returns.length;
    const correlations = this.calculateAutocorrelations(returns, lags);

    let LB = 0;
    for (let k = 1; k <= lags; k++) {
      LB += Math.pow(correlations[k], 2) / (n - k);
    }
    LB = n * (n + 2) * LB;

    // Chi-square distribution with 'lags' degrees of freedom
    const pValue = 1 - this.chiSquareCDF(LB, lags);
    const isSignificant = pValue <= this.config.pValueThreshold;

    return {
      testType: 'ljung_box',
      LB: LB,
      pValue: pValue,
      degreesOfFreedom: lags,
      isSignificant: isSignificant,
      autocorrelations: correlations,
      interpretation: isSignificant ? 'Serial correlation detected' : 'No serial correlation'
    };
  }

  calculateAutocorrelations(data, maxLag) {
    const n = data.length;
    const mean = data.reduce((sum, val) => sum + val, 0) / n;
    const correlations = {};

    for (let lag = 0; lag <= maxLag; lag++) {
      let numerator = 0;
      let denominator = 0;

      for (let i = 0; i < n - lag; i++) {
        numerator += (data[i] - mean) * (data[i + lag] - mean);
      }

      for (let i = 0; i < n; i++) {
        denominator += Math.pow(data[i] - mean, 2);
      }

      correlations[lag] = denominator === 0 ? 0 : numerator / denominator;
    }

    return correlations;
  }

  // Statistical distribution functions (simplified implementations)
  tDistributionCDF(t, df) {
    // Simplified implementation - would use proper t-distribution
    if (df > 30) {
      return this.normalCDF(t);
    }
    // Use approximation or lookup table
    return 0.5 + 0.5 * Math.sign(t) * Math.sqrt(1 - Math.exp(-2 * t * t / Math.PI));
  }

  normalCDF(z) {
    return 0.5 * (1 + this.erf(z / Math.sqrt(2)));
  }

  erf(x) {
    // Approximation of error function
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

  // Utility functions
  calculateVariance(data) {
    if (data.length < 2) return 0;
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    return data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (data.length - 1);
  }

  calculateStandardDeviation(data) {
    return Math.sqrt(this.calculateVariance(data));
  }

  calculateSkewness(data) {
    if (data.length < 3) return 0;
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const variance = this.calculateVariance(data);
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    return data.reduce((sum, val) => sum + Math.pow((val - mean) / stdDev, 3), 0) / data.length;
  }

  calculateKurtosis(data) {
    if (data.length < 4) return 0;
    const mean = data.reduce((sum, val) => sum + val, 0) / data.length;
    const variance = this.calculateVariance(data);
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    return data.reduce((sum, val) => sum + Math.pow((val - mean) / stdDev, 4), 0) / data.length - 3;
  }

  applyMultipleTestingCorrection(testResults) {
    const testNames = Object.keys(testResults);
    const pValues = testNames.map(name => testResults[name].pValue).filter(p => !isNaN(p));

    if (pValues.length === 0) return testResults;

    let correctedResults = { ...testResults };

    switch (this.config.multipleTestingCorrection) {
      case 'bonferroni':
        correctedResults = this.applyBonferroniCorrection(testResults, pValues.length);
        break;
      case 'holm':
        correctedResults = this.applyHolmCorrection(testResults);
        break;
      case 'fdr':
        correctedResults = this.applyFDRCorrection(testResults);
        break;
    }

    return correctedResults;
  }

  applyBonferroniCorrection(testResults, numTests) {
    const corrected = { ...testResults };

    Object.keys(corrected).forEach(testName => {
      if (corrected[testName].pValue !== undefined) {
        corrected[testName].pValueCorrected = Math.min(1, corrected[testName].pValue * numTests);
        corrected[testName].isSignificantCorrected = corrected[testName].pValueCorrected <= this.config.pValueThreshold;
      }
    });

    return corrected;
  }

  generateTestSummary(testResults) {
    const completedTests = Object.values(testResults).filter(result => result.status !== 'failed');
    const significantTests = completedTests.filter(result => result.isSignificant);
    const correctedSignificantTests = completedTests.filter(result => result.isSignificantCorrected);

    return {
      totalTests: Object.keys(testResults).length,
      completedTests: completedTests.length,
      failedTests: Object.keys(testResults).length - completedTests.length,
      significantTests: significantTests.length,
      significantTestsCorrected: correctedSignificantTests.length,
      significanceRate: completedTests.length > 0 ? significantTests.length / completedTests.length : 0,
      significanceRateCorrected: completedTests.length > 0 ? correctedSignificantTests.length / completedTests.length : 0
    };
  }

  generateConclusions(testResults, summary) {
    const conclusions = {
      overall: 'inconclusive',
      confidence: 'low',
      recommendations: [],
      warnings: []
    };

    // Overall assessment
    if (summary.significanceRateCorrected > 0.7) {
      conclusions.overall = 'strong_evidence';
      conclusions.confidence = 'high';
    } else if (summary.significanceRateCorrected > 0.4) {
      conclusions.overall = 'moderate_evidence';
      conclusions.confidence = 'medium';
    } else if (summary.significanceRateCorrected > 0.1) {
      conclusions.overall = 'weak_evidence';
      conclusions.confidence = 'low';
    }

    // Specific recommendations
    if (summary.failedTests > 0) {
      conclusions.warnings.push('Some tests failed to complete - check data quality');
    }

    if (summary.significanceRate !== summary.significanceRateCorrected) {
      conclusions.warnings.push('Multiple testing correction reduced significance - be cautious of false positives');
    }

    return conclusions;
  }

  /**
   * Export test results
   */
  exportTestResults(testId = null) {
    if (testId) {
      return this.testResults.get(testId);
    }

    return {
      timestamp: Date.now(),
      config: this.config,
      allResults: Object.fromEntries(this.testResults),
      history: this.testHistory,
      summary: this.generateOverallSummary()
    };
  }

  generateOverallSummary() {
    return {
      totalValidations: this.testHistory.length,
      averageSignificanceRate: this.testHistory.length > 0 ?
        this.testHistory.reduce((sum, test) => sum + test.summary.significanceRate, 0) / this.testHistory.length : 0,
      mostCommonTests: this.getMostCommonTests(),
      trendsAnalysis: this.analyzeTrends()
    };
  }

  getMostCommonTests() {
    const testCounts = {};
    this.testHistory.forEach(validation => {
      Object.keys(validation.tests).forEach(testName => {
        testCounts[testName] = (testCounts[testName] || 0) + 1;
      });
    });

    return Object.entries(testCounts)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([test, count]) => ({ test, count }));
  }

  analyzeTrends() {
    if (this.testHistory.length < 3) return { trend: 'insufficient_data' };

    const recentValidations = this.testHistory.slice(-10);
    const significanceRates = recentValidations.map(v => v.summary.significanceRate);

    // Simple trend analysis
    const firstHalf = significanceRates.slice(0, Math.floor(significanceRates.length / 2));
    const secondHalf = significanceRates.slice(Math.floor(significanceRates.length / 2));

    const firstAvg = firstHalf.reduce((sum, rate) => sum + rate, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, rate) => sum + rate, 0) / secondHalf.length;

    return {
      trend: secondAvg > firstAvg ? 'improving' : 'declining',
      magnitude: Math.abs(secondAvg - firstAvg),
      confidence: recentValidations.length >= 5 ? 'high' : 'low'
    };
  }
}

module.exports = StatisticalTestingFramework;