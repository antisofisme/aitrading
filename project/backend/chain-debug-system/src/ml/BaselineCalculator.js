/**
 * BaselineCalculator
 * Calculates and maintains baseline metrics for chain performance
 */

import logger from '../utils/logger.js';

export class BaselineCalculator {
  constructor({ database, redis }) {
    this.database = database;
    this.redis = redis;

    this.baselines = new Map();
    this.calculationInProgress = new Set();

    // Configuration
    this.config = {
      baselineWindow: 7 * 24 * 60 * 60 * 1000, // 7 days
      minDataPoints: 50,
      percentiles: [50, 75, 90, 95, 99],
      updateInterval: 3600000, // 1 hour
      outlierThreshold: 3, // 3 sigma
      seasonalityWindow: 24 * 60 * 60 * 1000 // 24 hours for daily patterns
    };

    this.isInitialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing BaselineCalculator...');

      // Load existing baselines
      await this.loadBaselines();

      // Start periodic baseline updates
      this.startPeriodicUpdates();

      this.isInitialized = true;
      logger.info('BaselineCalculator initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize BaselineCalculator:', error);
      throw error;
    }
  }

  async getBaseline(chainId) {
    try {
      // Check in-memory cache first
      if (this.baselines.has(chainId)) {
        const baseline = this.baselines.get(chainId);

        // Check if baseline is still fresh
        const age = Date.now() - baseline.calculatedAt.getTime();
        if (age < this.config.updateInterval) {
          return baseline;
        }
      }

      // Check Redis cache
      const cached = await this.getBaselineFromCache(chainId);
      if (cached) {
        this.baselines.set(chainId, cached);
        return cached;
      }

      // Calculate new baseline
      return await this.calculateBaseline(chainId);

    } catch (error) {
      logger.error(`Failed to get baseline for chain ${chainId}:`, error);
      return null;
    }
  }

  async calculateBaseline(chainId) {
    try {
      // Prevent concurrent calculations for same chain
      if (this.calculationInProgress.has(chainId)) {
        logger.debug(`Baseline calculation already in progress for chain ${chainId}`);
        return null;
      }

      this.calculationInProgress.add(chainId);

      try {
        logger.info(`Calculating baseline for chain ${chainId}`);

        // Get historical data
        const historicalData = await this.getHistoricalData(chainId);

        if (historicalData.length < this.config.minDataPoints) {
          logger.warn(`Insufficient data for baseline calculation: ${historicalData.length} points`);
          return null;
        }

        // Clean and validate data
        const cleanData = this.cleanData(historicalData);

        if (cleanData.length < this.config.minDataPoints) {
          logger.warn(`Insufficient clean data for baseline calculation: ${cleanData.length} points`);
          return null;
        }

        // Calculate baseline metrics
        const baseline = await this.computeBaseline(chainId, cleanData);

        // Store baseline
        await this.storeBaseline(chainId, baseline);

        // Cache baseline
        this.baselines.set(chainId, baseline);
        await this.cacheBaseline(chainId, baseline);

        logger.info(`Baseline calculated for chain ${chainId}`);

        return baseline;

      } finally {
        this.calculationInProgress.delete(chainId);
      }

    } catch (error) {
      logger.error(`Failed to calculate baseline for chain ${chainId}:`, error);
      this.calculationInProgress.delete(chainId);
      return null;
    }
  }

  async getHistoricalData(chainId) {
    try {
      const endTime = new Date();
      const startTime = new Date(endTime.getTime() - this.config.baselineWindow);

      const query = `
        SELECT
          timestamp,
          total_requests,
          avg_duration,
          p50_duration,
          p95_duration,
          p99_duration,
          error_rate,
          error_count,
          dependency_failure_rate,
          health_score,
          bottleneck_services,
          raw_data
        FROM chain_health_metrics
        WHERE chain_id = $1
          AND timestamp BETWEEN $2 AND $3
          AND total_requests > 0
        ORDER BY timestamp ASC
      `;

      const result = await this.database.query(query, [chainId, startTime, endTime]);

      return result.rows.map(row => ({
        timestamp: row.timestamp,
        totalRequests: row.total_requests,
        avgDuration: row.avg_duration,
        p50Duration: row.p50_duration,
        p95Duration: row.p95_duration,
        p99Duration: row.p99_duration,
        errorRate: row.error_rate,
        errorCount: row.error_count,
        dependencyFailureRate: row.dependency_failure_rate,
        healthScore: row.health_score,
        bottleneckServices: row.bottleneck_services || [],
        metadata: row.raw_data || {}
      }));

    } catch (error) {
      logger.error(`Failed to get historical data for chain ${chainId}:`, error);
      return [];
    }
  }

  cleanData(data) {
    // Remove outliers and invalid data points
    const cleanedData = [];

    // Calculate metrics for outlier detection
    const metrics = ['avgDuration', 'p99Duration', 'errorRate', 'dependencyFailureRate'];
    const outlierBounds = {};

    for (const metric of metrics) {
      const values = data.map(d => d[metric]).filter(v => v != null && !isNaN(v));

      if (values.length > 0) {
        const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);

        outlierBounds[metric] = {
          lower: mean - (this.config.outlierThreshold * stdDev),
          upper: mean + (this.config.outlierThreshold * stdDev)
        };
      }
    }

    // Filter out outliers and invalid data
    for (const point of data) {
      let isValid = true;

      // Check for basic validity
      if (!point.timestamp || point.totalRequests <= 0) {
        continue;
      }

      // Check for outliers
      for (const metric of metrics) {
        const value = point[metric];
        const bounds = outlierBounds[metric];

        if (value != null && bounds && (value < bounds.lower || value > bounds.upper)) {
          isValid = false;
          break;
        }
      }

      if (isValid) {
        cleanedData.push(point);
      }
    }

    logger.debug(`Data cleaning: ${data.length} -> ${cleanedData.length} points`);

    return cleanedData;
  }

  async computeBaseline(chainId, data) {
    try {
      const baseline = {
        chainId,
        calculatedAt: new Date(),
        dataPoints: data.length,
        timeWindow: this.config.baselineWindow,
        version: '1.0'
      };

      // Calculate basic statistics
      baseline.totalRequests = this.calculateStatistics(data, 'totalRequests');
      baseline.avgDuration = this.calculateStatistics(data, 'avgDuration');
      baseline.p50Duration = this.calculateStatistics(data, 'p50Duration');
      baseline.p95Duration = this.calculateStatistics(data, 'p95Duration');
      baseline.p99Duration = this.calculateStatistics(data, 'p99Duration');
      baseline.errorRate = this.calculateStatistics(data, 'errorRate');
      baseline.dependencyFailureRate = this.calculateStatistics(data, 'dependencyFailureRate');
      baseline.healthScore = this.calculateStatistics(data, 'healthScore');

      // Calculate derived metrics
      baseline.stabilityScore = this.calculateStabilityScore(data);
      baseline.performancePattern = this.analyzePerformancePattern(data);
      baseline.errorPattern = this.analyzeErrorPattern(data);

      // Seasonal analysis
      baseline.seasonalPatterns = this.analyzeSeasonalPatterns(data);

      // Trend analysis
      baseline.trends = this.analyzeTrends(data);

      // Recent history for time series analysis
      baseline.recentHistory = data.slice(-50).map(d => ({
        timestamp: d.timestamp,
        duration: d.p99Duration,
        errorRate: d.errorRate,
        healthScore: d.healthScore
      }));

      return baseline;

    } catch (error) {
      logger.error('Failed to compute baseline:', error);
      throw error;
    }
  }

  calculateStatistics(data, metric) {
    const values = data.map(d => d[metric]).filter(v => v != null && !isNaN(v));

    if (values.length === 0) {
      return { mean: 0, median: 0, std: 0, min: 0, max: 0, count: 0 };
    }

    values.sort((a, b) => a - b);

    const sum = values.reduce((acc, val) => acc + val, 0);
    const mean = sum / values.length;

    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);

    const median = values.length % 2 === 0
      ? (values[values.length / 2 - 1] + values[values.length / 2]) / 2
      : values[Math.floor(values.length / 2)];

    // Calculate percentiles
    const percentiles = {};
    for (const p of this.config.percentiles) {
      const index = Math.floor((p / 100) * values.length);
      percentiles[`p${p}`] = values[Math.min(index, values.length - 1)];
    }

    return {
      mean,
      median,
      std,
      min: values[0],
      max: values[values.length - 1],
      count: values.length,
      ...percentiles
    };
  }

  calculateStabilityScore(data) {
    // Calculate coefficient of variation for key metrics
    const metrics = ['avgDuration', 'errorRate', 'healthScore'];
    let totalCV = 0;
    let validMetrics = 0;

    for (const metric of metrics) {
      const stats = this.calculateStatistics(data, metric);

      if (stats.count > 0 && stats.mean > 0) {
        const cv = stats.std / stats.mean;
        totalCV += cv;
        validMetrics++;
      }
    }

    if (validMetrics === 0) return 0;

    // Lower coefficient of variation = higher stability
    const avgCV = totalCV / validMetrics;
    return Math.max(0, 1 - Math.min(1, avgCV));
  }

  analyzePerformancePattern(data) {
    const durations = data.map(d => d.p99Duration).filter(d => d != null);

    if (durations.length < 10) {
      return { pattern: 'insufficient_data', confidence: 0 };
    }

    // Analyze trend
    const trend = this.calculateTrend(durations);

    // Analyze volatility
    const volatility = this.calculateVolatility(durations);

    // Classify pattern
    let pattern = 'stable';
    let confidence = 0.5;

    if (Math.abs(trend) > 0.1) {
      pattern = trend > 0 ? 'degrading' : 'improving';
      confidence = Math.min(0.9, Math.abs(trend));
    } else if (volatility > 0.3) {
      pattern = 'volatile';
      confidence = Math.min(0.9, volatility);
    } else {
      confidence = 0.8;
    }

    return {
      pattern,
      confidence,
      trend,
      volatility,
      meanDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length
    };
  }

  analyzeErrorPattern(data) {
    const errorRates = data.map(d => d.errorRate).filter(e => e != null);

    if (errorRates.length < 10) {
      return { pattern: 'insufficient_data', confidence: 0 };
    }

    const meanErrorRate = errorRates.reduce((sum, e) => sum + e, 0) / errorRates.length;
    const maxErrorRate = Math.max(...errorRates);
    const trend = this.calculateTrend(errorRates);

    let pattern = 'stable';
    let confidence = 0.5;

    if (meanErrorRate > 0.05) {
      pattern = 'high_error_rate';
      confidence = 0.9;
    } else if (maxErrorRate > 0.1) {
      pattern = 'error_spikes';
      confidence = 0.8;
    } else if (Math.abs(trend) > 0.01) {
      pattern = trend > 0 ? 'increasing_errors' : 'decreasing_errors';
      confidence = Math.min(0.9, Math.abs(trend) * 100);
    } else {
      confidence = 0.8;
    }

    return {
      pattern,
      confidence,
      meanErrorRate,
      maxErrorRate,
      trend
    };
  }

  analyzeSeasonalPatterns(data) {
    const patterns = {};

    // Group by hour of day
    const hourlyGroups = this.groupByTimeUnit(data, 'hour');
    patterns.hourly = this.calculateTimeUnitStats(hourlyGroups);

    // Group by day of week
    const dailyGroups = this.groupByTimeUnit(data, 'dayOfWeek');
    patterns.daily = this.calculateTimeUnitStats(dailyGroups);

    return patterns;
  }

  groupByTimeUnit(data, unit) {
    const groups = {};

    for (const point of data) {
      let key;

      switch (unit) {
        case 'hour':
          key = point.timestamp.getHours();
          break;
        case 'dayOfWeek':
          key = point.timestamp.getDay();
          break;
        default:
          continue;
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(point);
    }

    return groups;
  }

  calculateTimeUnitStats(groups) {
    const stats = {};

    for (const [key, points] of Object.entries(groups)) {
      if (points.length > 0) {
        stats[key] = {
          count: points.length,
          avgDuration: points.reduce((sum, p) => sum + (p.avgDuration || 0), 0) / points.length,
          avgErrorRate: points.reduce((sum, p) => sum + (p.errorRate || 0), 0) / points.length,
          avgHealthScore: points.reduce((sum, p) => sum + (p.healthScore || 0), 0) / points.length
        };
      }
    }

    return stats;
  }

  analyzeTrends(data) {
    const trends = {};
    const metrics = ['avgDuration', 'errorRate', 'healthScore'];

    for (const metric of metrics) {
      const values = data.map(d => d[metric]).filter(v => v != null);
      trends[metric] = this.calculateTrend(values);
    }

    return trends;
  }

  calculateTrend(values) {
    if (values.length < 2) return 0;

    // Simple linear regression slope
    const n = values.length;
    const sumX = (n * (n - 1)) / 2; // Sum of indices 0, 1, 2, ..., n-1
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXY = values.reduce((sum, val, index) => sum + (index * val), 0);
    const sumXX = (n * (n - 1) * (2 * n - 1)) / 6; // Sum of squares of indices

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);

    // Normalize by mean to get relative trend
    const mean = sumY / n;
    return mean > 0 ? slope / mean : 0;
  }

  calculateVolatility(values) {
    if (values.length < 2) return 0;

    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    // Coefficient of variation
    return mean > 0 ? stdDev / mean : 0;
  }

  async storeBaseline(chainId, baseline) {
    try {
      const query = `
        INSERT INTO chain_baselines
        (chain_id, baseline_data, calculated_at, data_points, version)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (chain_id)
        DO UPDATE SET
          baseline_data = $2,
          calculated_at = $3,
          data_points = $4,
          version = $5
      `;

      await this.database.query(query, [
        chainId,
        JSON.stringify(baseline),
        baseline.calculatedAt,
        baseline.dataPoints,
        baseline.version
      ]);

    } catch (error) {
      logger.error('Failed to store baseline:', error);
    }
  }

  async loadBaselines() {
    try {
      const query = `
        SELECT chain_id, baseline_data, calculated_at
        FROM chain_baselines
        WHERE calculated_at > $1
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - this.config.updateInterval * 2) // Load recent baselines
      ]);

      for (const row of result.rows) {
        try {
          const baseline = JSON.parse(row.baseline_data);
          baseline.calculatedAt = row.calculated_at;
          this.baselines.set(row.chain_id, baseline);
        } catch (error) {
          logger.error(`Failed to parse baseline for chain ${row.chain_id}:`, error);
        }
      }

      logger.info(`Loaded ${this.baselines.size} baselines`);

    } catch (error) {
      logger.error('Failed to load baselines:', error);
    }
  }

  async cacheBaseline(chainId, baseline) {
    try {
      const key = `baseline:${chainId}`;
      const value = JSON.stringify(baseline);
      const expiry = Math.floor(this.config.updateInterval / 1000); // seconds

      await this.redis.setex(key, expiry, value);

    } catch (error) {
      logger.error('Failed to cache baseline:', error);
    }
  }

  async getBaselineFromCache(chainId) {
    try {
      const key = `baseline:${chainId}`;
      const value = await this.redis.get(key);

      if (value) {
        return JSON.parse(value);
      }

      return null;

    } catch (error) {
      logger.error('Failed to get baseline from cache:', error);
      return null;
    }
  }

  async recalculateBaselines() {
    try {
      logger.info('Recalculating all baselines...');

      // Get list of active chains
      const activeChains = await this.getActiveChains();

      // Recalculate baselines for active chains
      for (const chainId of activeChains) {
        try {
          await this.calculateBaseline(chainId);
        } catch (error) {
          logger.error(`Failed to recalculate baseline for chain ${chainId}:`, error);
        }
      }

      logger.info(`Recalculated baselines for ${activeChains.length} chains`);

    } catch (error) {
      logger.error('Failed to recalculate baselines:', error);
    }
  }

  async getActiveChains() {
    try {
      const query = `
        SELECT DISTINCT chain_id
        FROM chain_health_metrics
        WHERE timestamp > $1
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - 24 * 60 * 60 * 1000) // Last 24 hours
      ]);

      return result.rows.map(row => row.chain_id);

    } catch (error) {
      logger.error('Failed to get active chains:', error);
      return [];
    }
  }

  startPeriodicUpdates() {
    // Schedule periodic baseline updates
    setInterval(() => {
      this.recalculateBaselines().catch(error => {
        logger.error('Periodic baseline update failed:', error);
      });
    }, this.config.updateInterval);

    logger.info('Periodic baseline updates started');
  }
}