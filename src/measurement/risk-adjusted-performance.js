/**
 * Risk-Adjusted Performance Tracking System
 * Comprehensive risk-adjusted metrics for probabilistic trading strategies
 */

const EventEmitter = require('events');

class RiskAdjustedPerformanceTracker extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      riskFreeRate: config.riskFreeRate || 0.02, // 2% annual
      benchmarkReturn: config.benchmarkReturn || 0.08, // 8% annual
      confidenceLevel: config.confidenceLevel || 0.95,
      lookbackPeriod: config.lookbackPeriod || 252, // Trading days
      rebalancingFrequency: config.rebalancingFrequency || 'daily',
      ...config
    };

    this.portfolioReturns = [];
    this.benchmarkReturns = [];
    this.riskMetrics = new Map();
    this.performanceHistory = [];
    this.portfolioStates = [];
    this.drawdownPeriods = [];
    this.isTracking = false;
  }

  /**
   * Initialize risk-adjusted performance tracking
   */
  async initialize() {
    this.initializeRiskMetrics();
    this.startTracking();
    this.emit('initialized', { timestamp: Date.now() });
  }

  initializeRiskMetrics() {
    const metricTypes = [
      // Return-based metrics
      'sharpe_ratio',
      'sortino_ratio',
      'calmar_ratio',
      'omega_ratio',
      'information_ratio',

      // Risk metrics
      'value_at_risk_95',
      'value_at_risk_99',
      'conditional_var',
      'maximum_drawdown',
      'average_drawdown',
      'drawdown_duration',

      // Advanced metrics
      'beta',
      'alpha',
      'treynor_ratio',
      'tracking_error',
      'upside_capture',
      'downside_capture',

      // Probabilistic metrics
      'kelly_criterion',
      'expected_shortfall',
      'tail_ratio',
      'skewness',
      'kurtosis'
    ];

    metricTypes.forEach(type => {
      this.riskMetrics.set(type, {
        current: 0,
        history: [],
        trend: 'stable',
        alertThreshold: this.getDefaultAlertThreshold(type)
      });
    });
  }

  getDefaultAlertThreshold(metricType) {
    const thresholds = {
      'sharpe_ratio': { min: 0.5, max: 3.0 },
      'sortino_ratio': { min: 0.7, max: 4.0 },
      'maximum_drawdown': { min: 0, max: 0.20 }, // 20%
      'value_at_risk_95': { min: 0, max: 0.05 }, // 5%
      'beta': { min: 0.5, max: 1.5 },
      'tracking_error': { min: 0, max: 0.10 } // 10%
    };

    return thresholds[metricType] || { min: -Infinity, max: Infinity };
  }

  /**
   * Record portfolio state and calculate performance metrics
   */
  recordPortfolioState(portfolioValue, positions, timestamp = Date.now()) {
    const state = {
      timestamp,
      portfolioValue,
      positions: [...positions],
      cash: portfolioValue - positions.reduce((sum, pos) => sum + pos.value, 0)
    };

    this.portfolioStates.push(state);

    // Calculate returns if we have previous state
    if (this.portfolioStates.length > 1) {
      const previousState = this.portfolioStates[this.portfolioStates.length - 2];
      const portfolioReturn = (portfolioValue - previousState.portfolioValue) / previousState.portfolioValue;

      this.portfolioReturns.push({
        return: portfolioReturn,
        timestamp: timestamp,
        period: timestamp - previousState.timestamp
      });

      // Update risk metrics
      this.updateRiskMetrics();
    }

    this.emit('portfolioStateRecorded', state);
  }

  /**
   * Record benchmark performance for comparison
   */
  recordBenchmarkReturn(benchmarkReturn, timestamp = Date.now()) {
    this.benchmarkReturns.push({
      return: benchmarkReturn,
      timestamp: timestamp
    });

    this.emit('benchmarkRecorded', { return: benchmarkReturn, timestamp });
  }

  /**
   * Calculate comprehensive risk-adjusted performance metrics
   */
  calculateRiskAdjustedMetrics() {
    if (this.portfolioReturns.length < 2) {
      return null;
    }

    const returns = this.portfolioReturns.map(r => r.return);
    const benchmarkReturns = this.benchmarkReturns.map(r => r.return);

    const metrics = {
      timestamp: Date.now(),

      // Basic statistics
      totalReturn: this.calculateTotalReturn(returns),
      annualizedReturn: this.calculateAnnualizedReturn(returns),
      volatility: this.calculateVolatility(returns),
      skewness: this.calculateSkewness(returns),
      kurtosis: this.calculateKurtosis(returns),

      // Risk-adjusted ratios
      sharpeRatio: this.calculateSharpeRatio(returns),
      sortinoRatio: this.calculateSortinoRatio(returns),
      calmarRatio: this.calculateCalmarRatio(returns),
      omegaRatio: this.calculateOmegaRatio(returns),

      // Drawdown analysis
      maxDrawdown: this.calculateMaximumDrawdown(),
      averageDrawdown: this.calculateAverageDrawdown(),
      drawdownDuration: this.calculateDrawdownDuration(),

      // Risk metrics
      var95: this.calculateVaR(returns, 0.95),
      var99: this.calculateVaR(returns, 0.99),
      conditionalVaR: this.calculateConditionalVaR(returns, 0.95),
      expectedShortfall: this.calculateExpectedShortfall(returns, 0.95),

      // Market comparison (if benchmark available)
      beta: benchmarkReturns.length > 0 ? this.calculateBeta(returns, benchmarkReturns) : null,
      alpha: benchmarkReturns.length > 0 ? this.calculateAlpha(returns, benchmarkReturns) : null,
      treynorRatio: benchmarkReturns.length > 0 ? this.calculateTreynorRatio(returns, benchmarkReturns) : null,
      informationRatio: benchmarkReturns.length > 0 ? this.calculateInformationRatio(returns, benchmarkReturns) : null,
      trackingError: benchmarkReturns.length > 0 ? this.calculateTrackingError(returns, benchmarkReturns) : null,

      // Advanced metrics
      kellyFraction: this.calculateKellyFraction(returns),
      tailRatio: this.calculateTailRatio(returns),
      upsideCapture: benchmarkReturns.length > 0 ? this.calculateUpsideCapture(returns, benchmarkReturns) : null,
      downsideCapture: benchmarkReturns.length > 0 ? this.calculateDownsideCapture(returns, benchmarkReturns) : null
    };

    // Store metrics
    this.performanceHistory.push(metrics);

    // Update individual metric tracking
    Object.entries(metrics).forEach(([key, value]) => {
      if (typeof value === 'number' && !isNaN(value) && this.riskMetrics.has(key)) {
        this.updateMetricHistory(key, value);
      }
    });

    return metrics;
  }

  calculateTotalReturn(returns) {
    return returns.reduce((total, ret) => total * (1 + ret), 1) - 1;
  }

  calculateAnnualizedReturn(returns) {
    if (returns.length === 0) return 0;

    const totalReturn = this.calculateTotalReturn(returns);
    const periods = returns.length;
    const periodsPerYear = 252; // Trading days

    return Math.pow(1 + totalReturn, periodsPerYear / periods) - 1;
  }

  calculateVolatility(returns) {
    if (returns.length < 2) return 0;

    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / (returns.length - 1);

    return Math.sqrt(variance * 252); // Annualized
  }

  calculateSharpeRatio(returns) {
    if (returns.length < 2) return 0;

    const annualizedReturn = this.calculateAnnualizedReturn(returns);
    const volatility = this.calculateVolatility(returns);

    return volatility === 0 ? 0 : (annualizedReturn - this.config.riskFreeRate) / volatility;
  }

  calculateSortinoRatio(returns) {
    if (returns.length < 2) return 0;

    const annualizedReturn = this.calculateAnnualizedReturn(returns);
    const downside = returns.filter(ret => ret < 0);

    if (downside.length === 0) return Infinity;

    const downsideDeviation = Math.sqrt(
      downside.reduce((sum, ret) => sum + Math.pow(ret, 2), 0) / downside.length * 252
    );

    return downsideDeviation === 0 ? 0 : (annualizedReturn - this.config.riskFreeRate) / downsideDeviation;
  }

  calculateCalmarRatio(returns) {
    const annualizedReturn = this.calculateAnnualizedReturn(returns);
    const maxDrawdown = this.calculateMaximumDrawdown();

    return maxDrawdown === 0 ? 0 : annualizedReturn / Math.abs(maxDrawdown);
  }

  calculateOmegaRatio(returns, threshold = 0) {
    const gains = returns.filter(ret => ret > threshold).reduce((sum, ret) => sum + (ret - threshold), 0);
    const losses = returns.filter(ret => ret < threshold).reduce((sum, ret) => sum + Math.abs(ret - threshold), 0);

    return losses === 0 ? (gains > 0 ? Infinity : 0) : gains / losses;
  }

  calculateMaximumDrawdown() {
    if (this.portfolioStates.length < 2) return 0;

    let maxDrawdown = 0;
    let peak = this.portfolioStates[0].portfolioValue;
    let currentDrawdown = 0;
    let drawdownStart = null;

    for (let i = 1; i < this.portfolioStates.length; i++) {
      const currentValue = this.portfolioStates[i].portfolioValue;

      if (currentValue > peak) {
        peak = currentValue;
        if (currentDrawdown < 0) {
          // End of drawdown period
          this.drawdownPeriods.push({
            start: drawdownStart,
            end: this.portfolioStates[i].timestamp,
            magnitude: Math.abs(currentDrawdown)
          });
        }
        currentDrawdown = 0;
        drawdownStart = null;
      } else {
        if (currentDrawdown === 0) {
          drawdownStart = this.portfolioStates[i].timestamp;
        }
        currentDrawdown = (currentValue - peak) / peak;
        maxDrawdown = Math.min(maxDrawdown, currentDrawdown);
      }
    }

    return Math.abs(maxDrawdown);
  }

  calculateAverageDrawdown() {
    if (this.drawdownPeriods.length === 0) return 0;

    const totalDrawdown = this.drawdownPeriods.reduce((sum, dd) => sum + dd.magnitude, 0);
    return totalDrawdown / this.drawdownPeriods.length;
  }

  calculateDrawdownDuration() {
    if (this.drawdownPeriods.length === 0) return 0;

    const avgDuration = this.drawdownPeriods.reduce((sum, dd) => sum + (dd.end - dd.start), 0) / this.drawdownPeriods.length;
    return avgDuration / (1000 * 60 * 60 * 24); // Convert to days
  }

  calculateVaR(returns, confidence) {
    if (returns.length === 0) return 0;

    const sortedReturns = returns.slice().sort((a, b) => a - b);
    const index = Math.floor((1 - confidence) * sortedReturns.length);

    return Math.abs(sortedReturns[index] || 0);
  }

  calculateConditionalVaR(returns, confidence) {
    const var = this.calculateVaR(returns, confidence);
    const tailReturns = returns.filter(ret => ret <= -var);

    if (tailReturns.length === 0) return 0;

    return Math.abs(tailReturns.reduce((sum, ret) => sum + ret, 0) / tailReturns.length);
  }

  calculateExpectedShortfall(returns, confidence) {
    return this.calculateConditionalVaR(returns, confidence);
  }

  calculateBeta(portfolioReturns, benchmarkReturns) {
    const minLength = Math.min(portfolioReturns.length, benchmarkReturns.length);
    const portfolio = portfolioReturns.slice(-minLength);
    const benchmark = benchmarkReturns.slice(-minLength);

    if (minLength < 2) return 1;

    const portfolioMean = portfolio.reduce((sum, ret) => sum + ret, 0) / portfolio.length;
    const benchmarkMean = benchmark.reduce((sum, ret) => sum + ret, 0) / benchmark.length;

    let covariance = 0;
    let benchmarkVariance = 0;

    for (let i = 0; i < minLength; i++) {
      const portfolioDeviation = portfolio[i] - portfolioMean;
      const benchmarkDeviation = benchmark[i] - benchmarkMean;

      covariance += portfolioDeviation * benchmarkDeviation;
      benchmarkVariance += benchmarkDeviation * benchmarkDeviation;
    }

    return benchmarkVariance === 0 ? 1 : covariance / benchmarkVariance;
  }

  calculateAlpha(portfolioReturns, benchmarkReturns) {
    const beta = this.calculateBeta(portfolioReturns, benchmarkReturns);
    const portfolioReturn = this.calculateAnnualizedReturn(portfolioReturns);
    const benchmarkReturn = this.calculateAnnualizedReturn(benchmarkReturns);

    return portfolioReturn - (this.config.riskFreeRate + beta * (benchmarkReturn - this.config.riskFreeRate));
  }

  calculateTreynorRatio(portfolioReturns, benchmarkReturns) {
    const beta = this.calculateBeta(portfolioReturns, benchmarkReturns);
    const portfolioReturn = this.calculateAnnualizedReturn(portfolioReturns);

    return beta === 0 ? 0 : (portfolioReturn - this.config.riskFreeRate) / beta;
  }

  calculateInformationRatio(portfolioReturns, benchmarkReturns) {
    const minLength = Math.min(portfolioReturns.length, benchmarkReturns.length);
    const excessReturns = [];

    for (let i = 0; i < minLength; i++) {
      excessReturns.push(portfolioReturns[i] - benchmarkReturns[i]);
    }

    if (excessReturns.length < 2) return 0;

    const meanExcess = excessReturns.reduce((sum, ret) => sum + ret, 0) / excessReturns.length;
    const trackingError = this.calculateTrackingError(portfolioReturns, benchmarkReturns);

    return trackingError === 0 ? 0 : meanExcess / trackingError;
  }

  calculateTrackingError(portfolioReturns, benchmarkReturns) {
    const minLength = Math.min(portfolioReturns.length, benchmarkReturns.length);
    const excessReturns = [];

    for (let i = 0; i < minLength; i++) {
      excessReturns.push(portfolioReturns[i] - benchmarkReturns[i]);
    }

    if (excessReturns.length < 2) return 0;

    const meanExcess = excessReturns.reduce((sum, ret) => sum + ret, 0) / excessReturns.length;
    const variance = excessReturns.reduce((sum, ret) => sum + Math.pow(ret - meanExcess, 2), 0) / (excessReturns.length - 1);

    return Math.sqrt(variance * 252); // Annualized
  }

  calculateKellyFraction(returns) {
    if (returns.length < 10) return 0;

    const winningReturns = returns.filter(ret => ret > 0);
    const losingReturns = returns.filter(ret => ret < 0);

    if (winningReturns.length === 0 || losingReturns.length === 0) return 0;

    const winRate = winningReturns.length / returns.length;
    const avgWin = winningReturns.reduce((sum, ret) => sum + ret, 0) / winningReturns.length;
    const avgLoss = Math.abs(losingReturns.reduce((sum, ret) => sum + ret, 0) / losingReturns.length);

    return avgLoss === 0 ? 0 : winRate - (1 - winRate) / (avgWin / avgLoss);
  }

  calculateTailRatio(returns) {
    if (returns.length < 20) return 1;

    const sortedReturns = returns.slice().sort((a, b) => b - a);
    const top10Percent = Math.floor(returns.length * 0.1);
    const bottom10Percent = Math.floor(returns.length * 0.9);

    const avgTopReturn = sortedReturns.slice(0, top10Percent).reduce((sum, ret) => sum + ret, 0) / top10Percent;
    const avgBottomReturn = Math.abs(sortedReturns.slice(bottom10Percent).reduce((sum, ret) => sum + ret, 0) / (returns.length - bottom10Percent));

    return avgBottomReturn === 0 ? Infinity : avgTopReturn / avgBottomReturn;
  }

  calculateUpsideCapture(portfolioReturns, benchmarkReturns) {
    const minLength = Math.min(portfolioReturns.length, benchmarkReturns.length);
    const upsidePairs = [];

    for (let i = 0; i < minLength; i++) {
      if (benchmarkReturns[i] > 0) {
        upsidePairs.push({
          portfolio: portfolioReturns[i],
          benchmark: benchmarkReturns[i]
        });
      }
    }

    if (upsidePairs.length === 0) return 0;

    const avgPortfolioUpside = upsidePairs.reduce((sum, pair) => sum + pair.portfolio, 0) / upsidePairs.length;
    const avgBenchmarkUpside = upsidePairs.reduce((sum, pair) => sum + pair.benchmark, 0) / upsidePairs.length;

    return avgBenchmarkUpside === 0 ? 0 : avgPortfolioUpside / avgBenchmarkUpside;
  }

  calculateDownsideCapture(portfolioReturns, benchmarkReturns) {
    const minLength = Math.min(portfolioReturns.length, benchmarkReturns.length);
    const downsidePairs = [];

    for (let i = 0; i < minLength; i++) {
      if (benchmarkReturns[i] < 0) {
        downsidePairs.push({
          portfolio: portfolioReturns[i],
          benchmark: benchmarkReturns[i]
        });
      }
    }

    if (downsidePairs.length === 0) return 0;

    const avgPortfolioDownside = downsidePairs.reduce((sum, pair) => sum + pair.portfolio, 0) / downsidePairs.length;
    const avgBenchmarkDownside = downsidePairs.reduce((sum, pair) => sum + pair.benchmark, 0) / downsidePairs.length;

    return avgBenchmarkDownside === 0 ? 0 : avgPortfolioDownside / avgBenchmarkDownside;
  }

  calculateSkewness(returns) {
    if (returns.length < 3) return 0;

    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / (returns.length - 1);
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    const skewness = returns.reduce((sum, ret) => sum + Math.pow((ret - mean) / stdDev, 3), 0) / returns.length;
    return skewness;
  }

  calculateKurtosis(returns) {
    if (returns.length < 4) return 0;

    const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / (returns.length - 1);
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    const kurtosis = returns.reduce((sum, ret) => sum + Math.pow((ret - mean) / stdDev, 4), 0) / returns.length;
    return kurtosis - 3; // Excess kurtosis
  }

  updateMetricHistory(metricKey, value) {
    const metric = this.riskMetrics.get(metricKey);
    if (metric) {
      metric.current = value;
      metric.history.push({
        value: value,
        timestamp: Date.now()
      });

      // Update trend
      metric.trend = this.calculateMetricTrend(metric.history);

      // Check alerts
      this.checkMetricAlert(metricKey, value, metric.alertThreshold);
    }
  }

  calculateMetricTrend(history) {
    if (history.length < 3) return 'stable';

    const recent = history.slice(-3);
    const values = recent.map(h => h.value);

    if (values[2] > values[1] && values[1] > values[0]) return 'improving';
    if (values[2] < values[1] && values[1] < values[0]) return 'declining';
    return 'stable';
  }

  checkMetricAlert(metricKey, value, threshold) {
    if (value < threshold.min || value > threshold.max) {
      this.emit('metricAlert', {
        metric: metricKey,
        value: value,
        threshold: threshold,
        timestamp: Date.now()
      });
    }
  }

  updateRiskMetrics() {
    const metrics = this.calculateRiskAdjustedMetrics();
    if (metrics) {
      this.emit('metricsUpdated', metrics);
    }
  }

  startTracking() {
    this.isTracking = true;
    this.emit('trackingStarted', { timestamp: Date.now() });
  }

  stopTracking() {
    this.isTracking = false;
    this.emit('trackingStopped', { timestamp: Date.now() });
  }

  /**
   * Export performance data
   */
  exportPerformanceData() {
    return {
      timestamp: Date.now(),
      config: this.config,
      portfolioStates: this.portfolioStates,
      portfolioReturns: this.portfolioReturns,
      benchmarkReturns: this.benchmarkReturns,
      performanceHistory: this.performanceHistory,
      riskMetrics: Object.fromEntries(this.riskMetrics),
      drawdownPeriods: this.drawdownPeriods,
      currentMetrics: this.calculateRiskAdjustedMetrics()
    };
  }
}

module.exports = RiskAdjustedPerformanceTracker;