/**
 * MetricsCollector
 * System metrics collection and aggregation
 */

import EventEmitter from 'eventemitter3';
import logger from '../utils/logger.js';

export class MetricsCollector extends EventEmitter {
  constructor({ database, redis }) {
    super();

    this.database = database;
    this.redis = redis;

    this.isInitialized = false;
    this.metrics = new Map();
    this.aggregators = new Map();

    // Metric types
    this.metricTypes = {
      COUNTER: 'counter',
      GAUGE: 'gauge',
      HISTOGRAM: 'histogram',
      SUMMARY: 'summary'
    };

    // Collection intervals
    this.intervals = {
      realtime: 10000,    // 10 seconds
      aggregate: 60000,   // 1 minute
      persist: 300000     // 5 minutes
    };
  }

  async initialize() {
    try {
      logger.info('Initializing MetricsCollector...');

      // Initialize metric aggregators
      this.initializeAggregators();

      // Start metric collection
      this.startCollection();

      this.isInitialized = true;
      logger.info('MetricsCollector initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize MetricsCollector:', error);
      throw error;
    }
  }

  initializeAggregators() {
    // Chain monitoring metrics
    this.registerMetric('chain_health_checks', this.metricTypes.COUNTER, {
      description: 'Total number of chain health checks performed',
      labels: ['chain_id', 'status']
    });

    this.registerMetric('chain_anomalies_detected', this.metricTypes.COUNTER, {
      description: 'Total number of anomalies detected',
      labels: ['chain_id', 'type', 'severity']
    });

    this.registerMetric('chain_health_score', this.metricTypes.GAUGE, {
      description: 'Current chain health score',
      labels: ['chain_id']
    });

    // Impact analysis metrics
    this.registerMetric('impact_assessments', this.metricTypes.COUNTER, {
      description: 'Total number of impact assessments performed',
      labels: ['chain_id', 'priority_level']
    });

    this.registerMetric('cascade_risk_score', this.metricTypes.GAUGE, {
      description: 'Current cascade risk score',
      labels: ['chain_id']
    });

    // Root cause analysis metrics
    this.registerMetric('root_cause_analyses', this.metricTypes.COUNTER, {
      description: 'Total number of root cause analyses performed',
      labels: ['chain_id', 'root_cause_type']
    });

    this.registerMetric('analysis_confidence', this.metricTypes.HISTOGRAM, {
      description: 'Root cause analysis confidence scores',
      labels: ['chain_id', 'analysis_type']
    });

    // Recovery metrics
    this.registerMetric('recovery_attempts', this.metricTypes.COUNTER, {
      description: 'Total number of recovery attempts',
      labels: ['chain_id', 'recovery_type', 'status']
    });

    this.registerMetric('recovery_duration', this.metricTypes.HISTOGRAM, {
      description: 'Recovery operation duration in milliseconds',
      labels: ['chain_id', 'recovery_type']
    });

    // System performance metrics
    this.registerMetric('api_requests', this.metricTypes.COUNTER, {
      description: 'Total number of API requests',
      labels: ['endpoint', 'method', 'status']
    });

    this.registerMetric('api_response_time', this.metricTypes.HISTOGRAM, {
      description: 'API response time in milliseconds',
      labels: ['endpoint', 'method']
    });

    this.registerMetric('websocket_connections', this.metricTypes.GAUGE, {
      description: 'Current number of WebSocket connections',
      labels: ['client_type']
    });

    logger.info('Metric aggregators initialized');
  }

  registerMetric(name, type, config = {}) {
    this.metrics.set(name, {
      name,
      type,
      description: config.description || '',
      labels: config.labels || [],
      values: new Map(),
      lastUpdated: new Date()
    });
  }

  recordMetric(metricName, value, labels = {}) {
    try {
      const metric = this.metrics.get(metricName);

      if (!metric) {
        logger.warn(`Metric ${metricName} not registered`);
        return;
      }

      const labelKey = this.generateLabelKey(labels);
      const timestamp = new Date();

      switch (metric.type) {
        case this.metricTypes.COUNTER:
          this.recordCounter(metric, labelKey, value, timestamp);
          break;

        case this.metricTypes.GAUGE:
          this.recordGauge(metric, labelKey, value, timestamp);
          break;

        case this.metricTypes.HISTOGRAM:
          this.recordHistogram(metric, labelKey, value, timestamp);
          break;

        case this.metricTypes.SUMMARY:
          this.recordSummary(metric, labelKey, value, timestamp);
          break;

        default:
          logger.warn(`Unknown metric type: ${metric.type}`);
      }

      metric.lastUpdated = timestamp;

      // Store in Redis for real-time access
      this.cacheMetric(metricName, labelKey, value, timestamp);

    } catch (error) {
      logger.error(`Failed to record metric ${metricName}:`, error);
    }
  }

  recordCounter(metric, labelKey, value, timestamp) {
    if (!metric.values.has(labelKey)) {
      metric.values.set(labelKey, { count: 0, firstSeen: timestamp });
    }

    const current = metric.values.get(labelKey);
    current.count += (value || 1);
    current.lastSeen = timestamp;
  }

  recordGauge(metric, labelKey, value, timestamp) {
    metric.values.set(labelKey, {
      value,
      timestamp,
      history: metric.values.get(labelKey)?.history || []
    });

    // Keep last 100 values for trend analysis
    const entry = metric.values.get(labelKey);
    entry.history.push({ value, timestamp });
    if (entry.history.length > 100) {
      entry.history.shift();
    }
  }

  recordHistogram(metric, labelKey, value, timestamp) {
    if (!metric.values.has(labelKey)) {
      metric.values.set(labelKey, {
        count: 0,
        sum: 0,
        buckets: new Map(),
        min: Infinity,
        max: -Infinity,
        values: []
      });
    }

    const histogram = metric.values.get(labelKey);
    histogram.count++;
    histogram.sum += value;
    histogram.min = Math.min(histogram.min, value);
    histogram.max = Math.max(histogram.max, value);

    // Keep recent values for percentile calculation
    histogram.values.push(value);
    if (histogram.values.length > 1000) {
      histogram.values.shift();
    }

    // Update buckets (predefined buckets for performance metrics)
    const buckets = [10, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
    for (const bucket of buckets) {
      if (value <= bucket) {
        histogram.buckets.set(bucket, (histogram.buckets.get(bucket) || 0) + 1);
      }
    }
  }

  recordSummary(metric, labelKey, value, timestamp) {
    if (!metric.values.has(labelKey)) {
      metric.values.set(labelKey, {
        count: 0,
        sum: 0,
        quantiles: new Map(),
        values: []
      });
    }

    const summary = metric.values.get(labelKey);
    summary.count++;
    summary.sum += value;
    summary.values.push(value);

    // Keep only recent values
    if (summary.values.length > 1000) {
      summary.values.shift();
    }

    // Calculate quantiles
    this.calculateQuantiles(summary);
  }

  calculateQuantiles(summary) {
    if (summary.values.length === 0) return;

    const sorted = [...summary.values].sort((a, b) => a - b);
    const quantiles = [0.5, 0.75, 0.9, 0.95, 0.99];

    for (const q of quantiles) {
      const index = Math.floor(sorted.length * q);
      summary.quantiles.set(q, sorted[Math.min(index, sorted.length - 1)]);
    }
  }

  generateLabelKey(labels) {
    return Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join(',');
  }

  async cacheMetric(metricName, labelKey, value, timestamp) {
    try {
      const key = `metric:${metricName}:${labelKey}`;
      const data = JSON.stringify({ value, timestamp: timestamp.toISOString() });

      await this.redis.setex(key, 3600, data); // 1 hour expiry
    } catch (error) {
      logger.debug('Failed to cache metric:', error);
    }
  }

  startCollection() {
    // Real-time metric collection
    setInterval(() => {
      this.collectSystemMetrics();
    }, this.intervals.realtime);

    // Periodic aggregation
    setInterval(() => {
      this.aggregateMetrics();
    }, this.intervals.aggregate);

    // Persist metrics to database
    setInterval(() => {
      this.persistMetrics();
    }, this.intervals.persist);

    logger.info('Metric collection started');
  }

  async collectSystemMetrics() {
    try {
      // Database connection metrics
      if (this.database && this.database.pool) {
        const dbInfo = await this.database.getConnectionInfo();
        this.recordMetric('db_connections_total', dbInfo.totalCount);
        this.recordMetric('db_connections_idle', dbInfo.idleCount);
        this.recordMetric('db_connections_waiting', dbInfo.waitingCount);
      }

      // Redis metrics
      if (this.redis && this.redis.isConnected) {
        const redisHealth = await this.redis.healthCheck();
        this.recordMetric('redis_latency', redisHealth.latency);
        if (redisHealth.keyspaceHits !== undefined) {
          this.recordMetric('redis_keyspace_hits', redisHealth.keyspaceHits);
          this.recordMetric('redis_keyspace_misses', redisHealth.keyspaceMisses);
        }
      }

      // Memory usage
      const memUsage = process.memoryUsage();
      this.recordMetric('memory_used_bytes', memUsage.heapUsed);
      this.recordMetric('memory_total_bytes', memUsage.heapTotal);
      this.recordMetric('memory_external_bytes', memUsage.external);

      // CPU usage (simplified)
      const cpuUsage = process.cpuUsage();
      this.recordMetric('cpu_user_microseconds', cpuUsage.user);
      this.recordMetric('cpu_system_microseconds', cpuUsage.system);

    } catch (error) {
      logger.error('Failed to collect system metrics:', error);
    }
  }

  async aggregateMetrics() {
    try {
      const now = new Date();
      const aggregations = new Map();

      // Aggregate metrics by time windows
      for (const [metricName, metric] of this.metrics) {
        const aggregation = this.calculateAggregation(metric, now);
        if (aggregation) {
          aggregations.set(metricName, aggregation);
        }
      }

      // Store aggregations in Redis
      for (const [metricName, aggregation] of aggregations) {
        const key = `aggregation:${metricName}:${Math.floor(now.getTime() / 60000)}`;
        await this.redis.setex(key, 3600, JSON.stringify(aggregation));
      }

    } catch (error) {
      logger.error('Failed to aggregate metrics:', error);
    }
  }

  calculateAggregation(metric, timestamp) {
    const aggregation = {
      metricName: metric.name,
      type: metric.type,
      timestamp: timestamp.toISOString(),
      labels: {},
      summary: {}
    };

    switch (metric.type) {
      case this.metricTypes.COUNTER:
        aggregation.summary.total = 0;
        for (const [labelKey, data] of metric.values) {
          aggregation.labels[labelKey] = data.count;
          aggregation.summary.total += data.count;
        }
        break;

      case this.metricTypes.GAUGE:
        const values = Array.from(metric.values.values()).map(v => v.value);
        if (values.length > 0) {
          aggregation.summary.current = values[values.length - 1];
          aggregation.summary.avg = values.reduce((sum, v) => sum + v, 0) / values.length;
          aggregation.summary.min = Math.min(...values);
          aggregation.summary.max = Math.max(...values);
        }
        break;

      case this.metricTypes.HISTOGRAM:
        let totalCount = 0;
        let totalSum = 0;
        for (const [labelKey, histogram] of metric.values) {
          totalCount += histogram.count;
          totalSum += histogram.sum;
          aggregation.labels[labelKey] = {
            count: histogram.count,
            sum: histogram.sum,
            avg: histogram.count > 0 ? histogram.sum / histogram.count : 0,
            min: histogram.min === Infinity ? 0 : histogram.min,
            max: histogram.max === -Infinity ? 0 : histogram.max,
            percentiles: this.calculatePercentiles(histogram.values)
          };
        }
        aggregation.summary.totalCount = totalCount;
        aggregation.summary.totalSum = totalSum;
        aggregation.summary.avgAcrossLabels = totalCount > 0 ? totalSum / totalCount : 0;
        break;
    }

    return aggregation;
  }

  calculatePercentiles(values) {
    if (values.length === 0) return {};

    const sorted = [...values].sort((a, b) => a - b);
    const percentiles = [50, 75, 90, 95, 99];
    const result = {};

    for (const p of percentiles) {
      const index = Math.floor((sorted.length * p) / 100);
      result[`p${p}`] = sorted[Math.min(index, sorted.length - 1)];
    }

    return result;
  }

  async persistMetrics() {
    try {
      const now = new Date();
      const batchSize = 100;
      const metricsToStore = [];

      // Collect metrics to persist
      for (const [metricName, metric] of this.metrics) {
        for (const [labelKey, data] of metric.values) {
          const labels = this.parseLabelKey(labelKey);

          metricsToStore.push({
            metric_name: metricName,
            metric_type: metric.type,
            value: this.extractValue(data, metric.type),
            labels: JSON.stringify(labels),
            timestamp: now
          });
        }
      }

      // Store in batches
      for (let i = 0; i < metricsToStore.length; i += batchSize) {
        const batch = metricsToStore.slice(i, i + batchSize);
        await this.storeBatch(batch);
      }

      logger.debug(`Persisted ${metricsToStore.length} metrics to database`);

    } catch (error) {
      logger.error('Failed to persist metrics:', error);
    }
  }

  async storeBatch(metrics) {
    if (metrics.length === 0) return;

    try {
      const query = `
        INSERT INTO system_metrics (metric_name, metric_type, value, labels, timestamp)
        VALUES ${metrics.map((_, i) => `($${i * 5 + 1}, $${i * 5 + 2}, $${i * 5 + 3}, $${i * 5 + 4}, $${i * 5 + 5})`).join(', ')}
      `;

      const params = metrics.flatMap(m => [
        m.metric_name,
        m.metric_type,
        m.value,
        m.labels,
        m.timestamp
      ]);

      await this.database.query(query, params);

    } catch (error) {
      logger.error('Failed to store metrics batch:', error);
    }
  }

  extractValue(data, metricType) {
    switch (metricType) {
      case this.metricTypes.COUNTER:
        return data.count;
      case this.metricTypes.GAUGE:
        return data.value;
      case this.metricTypes.HISTOGRAM:
        return data.count > 0 ? data.sum / data.count : 0; // Average
      case this.metricTypes.SUMMARY:
        return data.count > 0 ? data.sum / data.count : 0; // Average
      default:
        return 0;
    }
  }

  parseLabelKey(labelKey) {
    if (!labelKey) return {};

    const labels = {};
    const pairs = labelKey.split(',');

    for (const pair of pairs) {
      const [key, value] = pair.split('=');
      if (key && value !== undefined) {
        labels[key] = value;
      }
    }

    return labels;
  }

  // Public API methods
  async getMetric(metricName, labels = {}) {
    try {
      const metric = this.metrics.get(metricName);
      if (!metric) return null;

      const labelKey = this.generateLabelKey(labels);
      return metric.values.get(labelKey) || null;

    } catch (error) {
      logger.error(`Failed to get metric ${metricName}:`, error);
      return null;
    }
  }

  async getSystemMetrics(timeWindow = 3600000) {
    try {
      const query = `
        SELECT metric_name, AVG(value) as avg_value, MAX(value) as max_value,
               MIN(value) as min_value, COUNT(*) as data_points
        FROM system_metrics
        WHERE timestamp > $1
        GROUP BY metric_name
        ORDER BY metric_name
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - timeWindow)
      ]);

      return result.rows;

    } catch (error) {
      logger.error('Failed to get system metrics:', error);
      return [];
    }
  }

  async getPerformanceMetrics(timeWindow = 3600000) {
    try {
      const performanceMetrics = [
        'api_response_time',
        'recovery_duration',
        'analysis_confidence',
        'chain_health_score'
      ];

      const query = `
        SELECT metric_name, labels, value, timestamp
        FROM system_metrics
        WHERE timestamp > $1 AND metric_name = ANY($2)
        ORDER BY timestamp DESC
        LIMIT 1000
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - timeWindow),
        performanceMetrics
      ]);

      return result.rows;

    } catch (error) {
      logger.error('Failed to get performance metrics:', error);
      return [];
    }
  }

  getMetricsList() {
    return Array.from(this.metrics.keys());
  }

  getMetricInfo(metricName) {
    const metric = this.metrics.get(metricName);
    if (!metric) return null;

    return {
      name: metric.name,
      type: metric.type,
      description: metric.description,
      labels: metric.labels,
      lastUpdated: metric.lastUpdated,
      valueCount: metric.values.size
    };
  }

  // Helper methods for specific metrics
  incrementCounter(metricName, labels = {}, value = 1) {
    this.recordMetric(metricName, value, labels);
  }

  setGauge(metricName, value, labels = {}) {
    this.recordMetric(metricName, value, labels);
  }

  observeHistogram(metricName, value, labels = {}) {
    this.recordMetric(metricName, value, labels);
  }

  // Cleanup methods
  async cleanup() {
    try {
      // Clear metrics older than 24 hours
      const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000);

      const query = `
        DELETE FROM system_metrics
        WHERE timestamp < $1
      `;

      await this.database.query(query, [cutoff]);

      logger.info('Metrics cleanup completed');

    } catch (error) {
      logger.error('Failed to cleanup metrics:', error);
    }
  }
}