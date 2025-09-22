/**
 * ChainHealthMonitor
 * Real-time chain health monitoring with ML-powered anomaly detection
 */

import EventEmitter from 'eventemitter3';
import cron from 'node-cron';
import logger from '../utils/logger.js';
import { AnomalyDetector } from '../ml/AnomalyDetector.js';
import { BaselineCalculator } from '../ml/BaselineCalculator.js';
import { ChainMetrics } from '../models/ChainMetrics.js';
import { Anomaly } from '../models/Anomaly.js';

export class ChainHealthMonitor extends EventEmitter {
  constructor({ database, redis, metricsCollector }) {
    super();

    this.database = database;
    this.redis = redis;
    this.metricsCollector = metricsCollector;

    this.isMonitoring = false;
    this.monitoringInterval = null;
    this.cronJob = null;

    // Alert thresholds (configurable)
    this.alertThresholds = {
      chain_duration_p99: parseInt(process.env.CHAIN_DURATION_P99_THRESHOLD) || 5000, // 5 seconds
      error_rate: parseFloat(process.env.ERROR_RATE_THRESHOLD) || 0.01, // 1%
      dependency_failure_rate: parseFloat(process.env.DEPENDENCY_FAILURE_THRESHOLD) || 0.005, // 0.5%
      bottleneck_duration_ratio: parseFloat(process.env.BOTTLENECK_RATIO_THRESHOLD) || 0.7, // 70%
      cascade_risk_score: parseFloat(process.env.CASCADE_RISK_THRESHOLD) || 0.8 // 80%
    };

    // Initialize ML components
    this.anomalyDetector = null;
    this.baselineCalculator = null;

    this.isHealthy = true;
  }

  async initialize() {
    try {
      logger.info('Initializing ChainHealthMonitor...');

      // Initialize ML components
      this.anomalyDetector = new AnomalyDetector({
        database: this.database,
        redis: this.redis
      });

      this.baselineCalculator = new BaselineCalculator({
        database: this.database,
        redis: this.redis
      });

      await this.anomalyDetector.initialize();
      await this.baselineCalculator.initialize();

      // Load existing baselines
      await this.loadBaselines();

      logger.info('ChainHealthMonitor initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize ChainHealthMonitor:', error);
      this.isHealthy = false;
      throw error;
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) {
      logger.warn('ChainHealthMonitor is already monitoring');
      return;
    }

    try {
      logger.info('Starting chain health monitoring...');

      // Start real-time monitoring
      this.isMonitoring = true;
      this.monitoringInterval = setInterval(
        () => this.performHealthCheck(),
        parseInt(process.env.CHAIN_HEALTH_CHECK_INTERVAL) || 10000 // 10 seconds
      );

      // Schedule baseline recalculation (every hour)
      this.cronJob = cron.schedule('0 * * * *', async () => {
        try {
          await this.recalculateBaselines();
        } catch (error) {
          logger.error('Failed to recalculate baselines:', error);
        }
      });

      this.emit('monitoring:started');
      logger.info('Chain health monitoring started');

    } catch (error) {
      logger.error('Failed to start monitoring:', error);
      this.isHealthy = false;
      throw error;
    }
  }

  async stopMonitoring() {
    if (!this.isMonitoring) {
      logger.warn('ChainHealthMonitor is not currently monitoring');
      return;
    }

    logger.info('Stopping chain health monitoring...');

    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    if (this.cronJob) {
      this.cronJob.destroy();
      this.cronJob = null;
    }

    this.emit('monitoring:stopped');
    logger.info('Chain health monitoring stopped');
  }

  async performHealthCheck() {
    try {
      // Get active chains from the last monitoring interval
      const activeChains = await this.getActiveChains();

      if (activeChains.length === 0) {
        return; // No active chains to monitor
      }

      logger.debug(`Monitoring ${activeChains.length} active chains`);

      // Monitor each chain
      const monitoringPromises = activeChains.map(chainId =>
        this.monitorChainHealth(chainId)
      );

      const results = await Promise.allSettled(monitoringPromises);

      // Process results and handle failures
      results.forEach((result, index) => {
        if (result.status === 'rejected') {
          logger.error(`Failed to monitor chain ${activeChains[index]}:`, result.reason);
        }
      });

      // Update monitoring metrics
      await this.updateMonitoringMetrics(activeChains.length, results);

    } catch (error) {
      logger.error('Error during health check:', error);
      this.emit('monitoring:error', error);
    }
  }

  async monitorChainHealth(chainId) {
    try {
      // Analyze chain health metrics
      const healthMetrics = await this.analyzeChainHealth(chainId);

      if (!healthMetrics) {
        return;
      }

      // Detect anomalies
      const anomalies = await this.detectAnomalies(healthMetrics);

      // Store metrics
      await this.storeHealthMetrics(healthMetrics);

      // Process anomalies if found
      if (anomalies.length > 0) {
        await this.processAnomalies(chainId, anomalies, healthMetrics);
      }

      // Emit health update
      this.emit('chain:health:update', {
        chainId,
        healthMetrics,
        anomalies,
        timestamp: new Date()
      });

    } catch (error) {
      logger.error(`Failed to monitor chain ${chainId}:`, error);
      throw error;
    }
  }

  async analyzeChainHealth(chainId) {
    try {
      // Get chain events from the last monitoring period
      const timeWindow = parseInt(process.env.CHAIN_HEALTH_CHECK_INTERVAL) || 10000;
      const startTime = new Date(Date.now() - timeWindow);

      const events = await this.getRecentChainEvents(chainId, startTime);

      if (events.length === 0) {
        return null; // No recent events
      }

      // Calculate performance metrics
      const durationMetrics = this.calculateDurationMetrics(events);
      const errorMetrics = this.calculateErrorMetrics(events);
      const dependencyMetrics = await this.calculateDependencyMetrics(events);

      // Calculate overall health score
      const healthScore = this.calculateHealthScore(
        durationMetrics,
        errorMetrics,
        dependencyMetrics
      );

      return new ChainMetrics({
        chainId,
        timestamp: new Date(),
        totalRequests: events.length,
        avgDuration: durationMetrics.avg,
        p50Duration: durationMetrics.p50,
        p95Duration: durationMetrics.p95,
        p99Duration: durationMetrics.p99,
        errorRate: errorMetrics.rate,
        errorCount: errorMetrics.count,
        dependencyFailureRate: dependencyMetrics.failureRate,
        bottleneckServices: dependencyMetrics.bottlenecks,
        healthScore,
        events
      });

    } catch (error) {
      logger.error(`Failed to analyze chain health for ${chainId}:`, error);
      throw error;
    }
  }

  calculateDurationMetrics(events) {
    const durations = events
      .filter(event => event.duration_ms && event.duration_ms > 0)
      .map(event => event.duration_ms)
      .sort((a, b) => a - b);

    if (durations.length === 0) {
      return { avg: 0, p50: 0, p95: 0, p99: 0 };
    }

    const sum = durations.reduce((acc, val) => acc + val, 0);
    const avg = sum / durations.length;

    const p50Index = Math.floor(durations.length * 0.5);
    const p95Index = Math.floor(durations.length * 0.95);
    const p99Index = Math.floor(durations.length * 0.99);

    return {
      avg: Math.round(avg),
      p50: durations[p50Index] || 0,
      p95: durations[p95Index] || 0,
      p99: durations[p99Index] || 0
    };
  }

  calculateErrorMetrics(events) {
    const errorEvents = events.filter(event =>
      event.event_type === 'error' ||
      event.status === 'error' ||
      (event.http_status && event.http_status >= 400)
    );

    return {
      count: errorEvents.length,
      rate: events.length > 0 ? errorEvents.length / events.length : 0,
      types: this.categorizeErrors(errorEvents)
    };
  }

  async calculateDependencyMetrics(events) {
    const dependencyMap = new Map();
    const failedDependencies = new Set();

    for (const event of events) {
      if (event.dependencies && Array.isArray(event.dependencies)) {
        for (const dep of event.dependencies) {
          const key = `${event.service_name}->${dep.target_service}`;

          if (!dependencyMap.has(key)) {
            dependencyMap.set(key, { total: 0, failed: 0, durations: [] });
          }

          const depMetrics = dependencyMap.get(key);
          depMetrics.total++;

          if (dep.status === 'error' || dep.status === 'timeout') {
            depMetrics.failed++;
            failedDependencies.add(dep.target_service);
          }

          if (dep.duration_ms) {
            depMetrics.durations.push(dep.duration_ms);
          }
        }
      }
    }

    // Calculate failure rate
    const totalDependencies = Array.from(dependencyMap.values())
      .reduce((sum, metrics) => sum + metrics.total, 0);
    const failedDependencies_count = Array.from(dependencyMap.values())
      .reduce((sum, metrics) => sum + metrics.failed, 0);

    // Identify bottlenecks
    const bottlenecks = this.identifyBottleneckServices(dependencyMap);

    return {
      failureRate: totalDependencies > 0 ? failedDependencies_count / totalDependencies : 0,
      failedServices: Array.from(failedDependencies),
      bottlenecks,
      dependencyMap: Object.fromEntries(dependencyMap)
    };
  }

  identifyBottleneckServices(dependencyMap) {
    const bottlenecks = [];

    for (const [dependency, metrics] of dependencyMap) {
      if (metrics.durations.length === 0) continue;

      const avgDuration = metrics.durations.reduce((sum, d) => sum + d, 0) / metrics.durations.length;
      const failureRate = metrics.failed / metrics.total;

      // Consider as bottleneck if average duration > 2 seconds or failure rate > 10%
      if (avgDuration > 2000 || failureRate > 0.1) {
        const [sourceService, targetService] = dependency.split('->');
        bottlenecks.push({
          sourceService,
          targetService,
          avgDuration: Math.round(avgDuration),
          failureRate: Math.round(failureRate * 100) / 100,
          severity: this.calculateBottleneckSeverity(avgDuration, failureRate)
        });
      }
    }

    return bottlenecks.sort((a, b) => b.severity - a.severity);
  }

  calculateBottleneckSeverity(avgDuration, failureRate) {
    // Normalize and combine duration and failure rate impact
    const durationScore = Math.min(avgDuration / 10000, 1); // Normalize to 0-1 (10s max)
    const failureScore = Math.min(failureRate * 10, 1); // Normalize to 0-1 (10% max)

    return Math.round((durationScore * 0.6 + failureScore * 0.4) * 100) / 100;
  }

  calculateHealthScore(durationMetrics, errorMetrics, dependencyMetrics) {
    // Health score calculation (0-100)
    let score = 100;

    // Duration impact (max -30 points)
    if (durationMetrics.p99 > 10000) score -= 30; // >10s is critical
    else if (durationMetrics.p99 > 5000) score -= 20; // >5s is major
    else if (durationMetrics.p99 > 2000) score -= 10; // >2s is minor

    // Error rate impact (max -40 points)
    if (errorMetrics.rate > 0.05) score -= 40; // >5% is critical
    else if (errorMetrics.rate > 0.02) score -= 25; // >2% is major
    else if (errorMetrics.rate > 0.01) score -= 15; // >1% is minor

    // Dependency failure impact (max -30 points)
    if (dependencyMetrics.failureRate > 0.02) score -= 30; // >2% is critical
    else if (dependencyMetrics.failureRate > 0.01) score -= 20; // >1% is major
    else if (dependencyMetrics.failureRate > 0.005) score -= 10; // >0.5% is minor

    return Math.max(0, Math.round(score));
  }

  async detectAnomalies(healthMetrics) {
    try {
      const anomalies = [];

      // Get baseline for comparison
      const baseline = await this.baselineCalculator.getBaseline(healthMetrics.chainId);

      if (!baseline) {
        // No baseline available yet, return empty anomalies
        return anomalies;
      }

      // Duration anomalies
      if (healthMetrics.p99Duration > baseline.p99Duration * 2) {
        anomalies.push(new Anomaly({
          type: 'performance_degradation',
          severity: this.calculateSeverity(healthMetrics.p99Duration, baseline.p99Duration),
          description: `P99 duration increased by ${Math.round((healthMetrics.p99Duration / baseline.p99Duration - 1) * 100)}%`,
          affectedMetric: 'p99_duration',
          currentValue: healthMetrics.p99Duration,
          baselineValue: baseline.p99Duration,
          confidence: this.calculateConfidence(healthMetrics.p99Duration, baseline.p99Duration),
          chainId: healthMetrics.chainId,
          timestamp: healthMetrics.timestamp
        }));
      }

      // Error rate anomalies
      if (healthMetrics.errorRate > baseline.errorRate * 3) {
        anomalies.push(new Anomaly({
          type: 'error_spike',
          severity: 'critical',
          description: `Error rate increased to ${(healthMetrics.errorRate * 100).toFixed(2)}%`,
          affectedMetric: 'error_rate',
          currentValue: healthMetrics.errorRate,
          baselineValue: baseline.errorRate,
          confidence: this.calculateConfidence(healthMetrics.errorRate, baseline.errorRate),
          chainId: healthMetrics.chainId,
          timestamp: healthMetrics.timestamp
        }));
      }

      // Dependency failure anomalies
      if (healthMetrics.dependencyFailureRate > this.alertThresholds.dependency_failure_rate) {
        anomalies.push(new Anomaly({
          type: 'dependency_failure',
          severity: 'high',
          description: `Dependency failure rate: ${(healthMetrics.dependencyFailureRate * 100).toFixed(2)}%`,
          affectedMetric: 'dependency_failure_rate',
          currentValue: healthMetrics.dependencyFailureRate,
          baselineValue: baseline.dependencyFailureRate || 0,
          confidence: 0.9,
          chainId: healthMetrics.chainId,
          timestamp: healthMetrics.timestamp
        }));
      }

      // Use ML model for pattern-based anomaly detection
      const mlAnomalies = await this.anomalyDetector.detectAnomalies(healthMetrics, baseline);
      anomalies.push(...mlAnomalies);

      return anomalies;

    } catch (error) {
      logger.error('Failed to detect anomalies:', error);
      return [];
    }
  }

  calculateSeverity(currentValue, baselineValue) {
    const ratio = currentValue / baselineValue;
    if (ratio > 5) return 'critical';
    if (ratio > 3) return 'high';
    if (ratio > 2) return 'medium';
    return 'low';
  }

  calculateConfidence(currentValue, baselineValue) {
    const ratio = Math.max(currentValue, baselineValue) / Math.min(currentValue, baselineValue);
    return Math.min(0.95, Math.max(0.5, 1 - (1 / ratio)));
  }

  async processAnomalies(chainId, anomalies, healthMetrics) {
    try {
      logger.warn(`Detected ${anomalies.length} anomalies for chain ${chainId}`);

      // Store anomalies
      await this.storeAnomalies(anomalies);

      // Emit anomaly events
      for (const anomaly of anomalies) {
        this.emit('anomaly:detected', {
          chainId,
          anomaly,
          healthMetrics,
          timestamp: new Date()
        });
      }

      // Trigger immediate investigation for critical anomalies
      const criticalAnomalies = anomalies.filter(a => a.severity === 'critical');
      if (criticalAnomalies.length > 0) {
        this.emit('chain:investigation:required', {
          chainId,
          anomalies: criticalAnomalies,
          healthMetrics,
          priority: 'immediate'
        });
      }

    } catch (error) {
      logger.error('Failed to process anomalies:', error);
    }
  }

  async getActiveChains(timeWindow = 3600000) { // 1 hour default
    try {
      const query = `
        SELECT DISTINCT chain_id
        FROM chain_events
        WHERE created_at > $1
        ORDER BY chain_id
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - timeWindow)
      ]);

      return result.rows.map(row => row.chain_id);

    } catch (error) {
      logger.error('Failed to get active chains:', error);
      return [];
    }
  }

  async getRecentChainEvents(chainId, startTime) {
    try {
      const query = `
        SELECT * FROM chain_events
        WHERE chain_id = $1 AND created_at > $2
        ORDER BY created_at DESC
        LIMIT 1000
      `;

      const result = await this.database.query(query, [chainId, startTime]);
      return result.rows;

    } catch (error) {
      logger.error(`Failed to get recent events for chain ${chainId}:`, error);
      return [];
    }
  }

  async storeHealthMetrics(healthMetrics) {
    try {
      const query = `
        INSERT INTO chain_health_metrics
        (chain_id, timestamp, total_requests, avg_duration, p50_duration, p95_duration, p99_duration,
         error_rate, error_count, dependency_failure_rate, bottleneck_services, health_score, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
      `;

      await this.database.query(query, [
        healthMetrics.chainId,
        healthMetrics.timestamp,
        healthMetrics.totalRequests,
        healthMetrics.avgDuration,
        healthMetrics.p50Duration,
        healthMetrics.p95Duration,
        healthMetrics.p99Duration,
        healthMetrics.errorRate,
        healthMetrics.errorCount,
        healthMetrics.dependencyFailureRate,
        JSON.stringify(healthMetrics.bottleneckServices),
        healthMetrics.healthScore,
        JSON.stringify({
          events: healthMetrics.events.length,
          calculated_at: new Date()
        })
      ]);

    } catch (error) {
      logger.error('Failed to store health metrics:', error);
    }
  }

  async storeAnomalies(anomalies) {
    try {
      const query = `
        INSERT INTO chain_anomalies
        (chain_id, type, severity, description, affected_metric, current_value,
         baseline_value, confidence, timestamp, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      `;

      for (const anomaly of anomalies) {
        await this.database.query(query, [
          anomaly.chainId,
          anomaly.type,
          anomaly.severity,
          anomaly.description,
          anomaly.affectedMetric,
          anomaly.currentValue,
          anomaly.baselineValue,
          anomaly.confidence,
          anomaly.timestamp,
          JSON.stringify(anomaly)
        ]);
      }

    } catch (error) {
      logger.error('Failed to store anomalies:', error);
    }
  }

  categorizeErrors(errorEvents) {
    const categories = {};

    for (const event of errorEvents) {
      let category = 'unknown';

      if (event.http_status) {
        if (event.http_status >= 500) category = 'server_error';
        else if (event.http_status >= 400) category = 'client_error';
      } else if (event.error_type) {
        category = event.error_type;
      } else if (event.message) {
        // Simple categorization based on error message
        if (event.message.includes('timeout')) category = 'timeout';
        else if (event.message.includes('connection')) category = 'connection';
        else if (event.message.includes('database')) category = 'database';
      }

      categories[category] = (categories[category] || 0) + 1;
    }

    return categories;
  }

  async loadBaselines() {
    try {
      // Load existing baselines from database or calculate initial ones
      logger.info('Loading chain baselines...');
      await this.baselineCalculator.loadBaselines();

    } catch (error) {
      logger.error('Failed to load baselines:', error);
    }
  }

  async recalculateBaselines() {
    try {
      logger.info('Recalculating chain baselines...');
      await this.baselineCalculator.recalculateBaselines();

      this.emit('baselines:updated');

    } catch (error) {
      logger.error('Failed to recalculate baselines:', error);
    }
  }

  async updateMonitoringMetrics(chainsMonitored, results) {
    try {
      const successCount = results.filter(r => r.status === 'fulfilled').length;
      const failureCount = results.filter(r => r.status === 'rejected').length;

      await this.metricsCollector.recordMetric('chain_monitoring', {
        chains_monitored: chainsMonitored,
        successful_checks: successCount,
        failed_checks: failureCount,
        timestamp: new Date()
      });

    } catch (error) {
      logger.error('Failed to update monitoring metrics:', error);
    }
  }

  // Public API methods
  async getChainHealth(chainId) {
    try {
      const query = `
        SELECT * FROM chain_health_metrics
        WHERE chain_id = $1
        ORDER BY timestamp DESC
        LIMIT 1
      `;

      const result = await this.database.query(query, [chainId]);
      return result.rows[0] || null;

    } catch (error) {
      logger.error(`Failed to get chain health for ${chainId}:`, error);
      return null;
    }
  }

  async getChainAnomalies(chainId, timeWindow = 3600000) {
    try {
      const query = `
        SELECT * FROM chain_anomalies
        WHERE chain_id = $1 AND timestamp > $2
        ORDER BY timestamp DESC
      `;

      const result = await this.database.query(query, [
        chainId,
        new Date(Date.now() - timeWindow)
      ]);

      return result.rows;

    } catch (error) {
      logger.error(`Failed to get anomalies for chain ${chainId}:`, error);
      return [];
    }
  }

  async getOverallSystemHealth() {
    try {
      const query = `
        SELECT
          COUNT(DISTINCT chain_id) as active_chains,
          AVG(health_score) as avg_health_score,
          COUNT(CASE WHEN health_score < 70 THEN 1 END) as unhealthy_chains,
          COUNT(CASE WHEN health_score >= 90 THEN 1 END) as healthy_chains
        FROM chain_health_metrics
        WHERE timestamp > $1
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - 300000) // Last 5 minutes
      ]);

      return result.rows[0];

    } catch (error) {
      logger.error('Failed to get system health:', error);
      return null;
    }
  }
}