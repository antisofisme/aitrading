/**
 * Baseline Performance Metrics System
 * Establishes fundamental trading performance measurements
 */

const EventEmitter = require('events');

class BaselineMetricsCollector extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      samplingInterval: config.samplingInterval || 1000, // 1 second
      rollingWindowSize: config.rollingWindowSize || 3600, // 1 hour
      metricsRetention: config.metricsRetention || 86400000, // 24 hours
      ...config
    };

    this.metrics = new Map();
    this.rollingWindows = new Map();
    this.startTime = Date.now();
    this.isCollecting = false;
  }

  /**
   * Initialize baseline metrics collection
   */
  async initialize() {
    this.initializeMetricTypes();
    this.startCollection();
    this.emit('initialized', { timestamp: Date.now() });
  }

  initializeMetricTypes() {
    const metricTypes = [
      // Trading Performance Metrics
      'total_return',
      'sharpe_ratio',
      'max_drawdown',
      'win_rate',
      'profit_factor',
      'average_trade_duration',
      'volatility',

      // Execution Metrics
      'order_fill_rate',
      'slippage',
      'execution_latency',
      'market_impact',

      // Risk Metrics
      'var_95',
      'var_99',
      'expected_shortfall',
      'beta',
      'correlation_to_market',

      // Strategy-Specific Metrics
      'signal_accuracy',
      'signal_frequency',
      'position_sizing_efficiency',
      'rebalancing_frequency'
    ];

    metricTypes.forEach(type => {
      this.metrics.set(type, {
        current: 0,
        history: [],
        aggregations: {
          min: Infinity,
          max: -Infinity,
          mean: 0,
          std: 0,
          count: 0
        }
      });

      this.rollingWindows.set(type, []);
    });
  }

  /**
   * Record a metric value
   */
  recordMetric(type, value, timestamp = Date.now()) {
    if (!this.metrics.has(type)) {
      throw new Error(`Unknown metric type: ${type}`);
    }

    const metric = this.metrics.get(type);
    const rollingWindow = this.rollingWindows.get(type);

    // Update current value
    metric.current = value;

    // Add to history
    const dataPoint = { value, timestamp };
    metric.history.push(dataPoint);
    rollingWindow.push(dataPoint);

    // Maintain rolling window size
    while (rollingWindow.length > this.config.rollingWindowSize) {
      rollingWindow.shift();
    }

    // Update aggregations
    this.updateAggregations(type, value);

    // Cleanup old data
    this.cleanupOldData(type, timestamp);

    this.emit('metricRecorded', { type, value, timestamp });
  }

  updateAggregations(type, value) {
    const metric = this.metrics.get(type);
    const agg = metric.aggregations;

    agg.count++;
    agg.min = Math.min(agg.min, value);
    agg.max = Math.max(agg.max, value);

    // Update running mean and standard deviation
    const delta = value - agg.mean;
    agg.mean += delta / agg.count;

    if (agg.count > 1) {
      const delta2 = value - agg.mean;
      agg.variance = ((agg.count - 2) * agg.variance + delta * delta2) / (agg.count - 1);
      agg.std = Math.sqrt(agg.variance);
    }
  }

  cleanupOldData(type, currentTimestamp) {
    const metric = this.metrics.get(type);
    const cutoffTime = currentTimestamp - this.config.metricsRetention;

    metric.history = metric.history.filter(point => point.timestamp > cutoffTime);
  }

  /**
   * Calculate comprehensive baseline metrics
   */
  calculateBaselineMetrics(tradingData) {
    const metrics = {};

    try {
      // Trading Performance Calculations
      metrics.totalReturn = this.calculateTotalReturn(tradingData.returns);
      metrics.sharpeRatio = this.calculateSharpeRatio(tradingData.returns);
      metrics.maxDrawdown = this.calculateMaxDrawdown(tradingData.cumulativeReturns);
      metrics.winRate = this.calculateWinRate(tradingData.trades);
      metrics.profitFactor = this.calculateProfitFactor(tradingData.trades);
      metrics.volatility = this.calculateVolatility(tradingData.returns);

      // Execution Metrics
      metrics.orderFillRate = this.calculateOrderFillRate(tradingData.orders);
      metrics.slippage = this.calculateSlippage(tradingData.executions);
      metrics.executionLatency = this.calculateExecutionLatency(tradingData.executions);

      // Risk Metrics
      metrics.var95 = this.calculateVaR(tradingData.returns, 0.95);
      metrics.var99 = this.calculateVaR(tradingData.returns, 0.99);
      metrics.expectedShortfall = this.calculateExpectedShortfall(tradingData.returns, 0.95);

      // Record all metrics
      Object.entries(metrics).forEach(([key, value]) => {
        if (typeof value === 'number' && !isNaN(value)) {
          this.recordMetric(key, value);
        }
      });

      return metrics;

    } catch (error) {
      this.emit('error', {
        message: 'Error calculating baseline metrics',
        error: error.message
      });
      throw error;
    }
  }

  calculateTotalReturn(returns) {
    if (!returns || returns.length === 0) return 0;
    return returns.reduce((total, ret) => total * (1 + ret), 1) - 1;
  }

  calculateSharpeRatio(returns, riskFreeRate = 0) {
    if (!returns || returns.length < 2) return 0;

    const meanReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - meanReturn, 2), 0) / (returns.length - 1);
    const volatility = Math.sqrt(variance);

    return volatility === 0 ? 0 : (meanReturn - riskFreeRate) / volatility;
  }

  calculateMaxDrawdown(cumulativeReturns) {
    if (!cumulativeReturns || cumulativeReturns.length === 0) return 0;

    let maxDrawdown = 0;
    let peak = cumulativeReturns[0];

    for (let i = 1; i < cumulativeReturns.length; i++) {
      if (cumulativeReturns[i] > peak) {
        peak = cumulativeReturns[i];
      } else {
        const drawdown = (peak - cumulativeReturns[i]) / peak;
        maxDrawdown = Math.max(maxDrawdown, drawdown);
      }
    }

    return maxDrawdown;
  }

  calculateWinRate(trades) {
    if (!trades || trades.length === 0) return 0;

    const winningTrades = trades.filter(trade => trade.pnl > 0).length;
    return winningTrades / trades.length;
  }

  calculateProfitFactor(trades) {
    if (!trades || trades.length === 0) return 0;

    const profits = trades.filter(trade => trade.pnl > 0).reduce((sum, trade) => sum + trade.pnl, 0);
    const losses = Math.abs(trades.filter(trade => trade.pnl < 0).reduce((sum, trade) => sum + trade.pnl, 0));

    return losses === 0 ? (profits > 0 ? Infinity : 0) : profits / losses;
  }

  calculateVolatility(returns) {
    if (!returns || returns.length < 2) return 0;

    const meanReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - meanReturn, 2), 0) / (returns.length - 1);

    return Math.sqrt(variance * 252); // Annualized volatility
  }

  calculateOrderFillRate(orders) {
    if (!orders || orders.length === 0) return 0;

    const filledOrders = orders.filter(order => order.status === 'filled').length;
    return filledOrders / orders.length;
  }

  calculateSlippage(executions) {
    if (!executions || executions.length === 0) return 0;

    const slippages = executions
      .filter(exec => exec.expectedPrice && exec.actualPrice)
      .map(exec => Math.abs(exec.actualPrice - exec.expectedPrice) / exec.expectedPrice);

    return slippages.length === 0 ? 0 : slippages.reduce((sum, slip) => sum + slip, 0) / slippages.length;
  }

  calculateExecutionLatency(executions) {
    if (!executions || executions.length === 0) return 0;

    const latencies = executions
      .filter(exec => exec.submitTime && exec.fillTime)
      .map(exec => exec.fillTime - exec.submitTime);

    return latencies.length === 0 ? 0 : latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;
  }

  calculateVaR(returns, confidence) {
    if (!returns || returns.length === 0) return 0;

    const sortedReturns = returns.slice().sort((a, b) => a - b);
    const index = Math.floor((1 - confidence) * sortedReturns.length);

    return Math.abs(sortedReturns[index] || 0);
  }

  calculateExpectedShortfall(returns, confidence) {
    if (!returns || returns.length === 0) return 0;

    const var = this.calculateVaR(returns, confidence);
    const tailReturns = returns.filter(ret => ret <= -var);

    return tailReturns.length === 0 ? 0 : Math.abs(tailReturns.reduce((sum, ret) => sum + ret, 0) / tailReturns.length);
  }

  /**
   * Get current baseline snapshot
   */
  getBaselineSnapshot() {
    const snapshot = {
      timestamp: Date.now(),
      collectionDuration: Date.now() - this.startTime,
      metrics: {}
    };

    this.metrics.forEach((metric, type) => {
      snapshot.metrics[type] = {
        current: metric.current,
        aggregations: { ...metric.aggregations },
        recentHistory: this.rollingWindows.get(type).slice(-100) // Last 100 data points
      };
    });

    return snapshot;
  }

  /**
   * Start automatic metrics collection
   */
  startCollection() {
    if (this.isCollecting) return;

    this.isCollecting = true;
    this.collectionInterval = setInterval(() => {
      this.emit('collectionTick', { timestamp: Date.now() });
    }, this.config.samplingInterval);
  }

  /**
   * Stop metrics collection
   */
  stopCollection() {
    if (!this.isCollecting) return;

    this.isCollecting = false;
    if (this.collectionInterval) {
      clearInterval(this.collectionInterval);
      this.collectionInterval = null;
    }

    this.emit('collectionStopped', { timestamp: Date.now() });
  }

  /**
   * Export metrics for external analysis
   */
  exportMetrics() {
    const exportData = {
      timestamp: Date.now(),
      config: this.config,
      baseline: this.getBaselineSnapshot(),
      fullHistory: {}
    };

    this.metrics.forEach((metric, type) => {
      exportData.fullHistory[type] = metric.history;
    });

    return exportData;
  }
}

module.exports = BaselineMetricsCollector;