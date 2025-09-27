/**
 * Metrics Collector - Performance and Business Metrics Collection
 *
 * Comprehensive metrics collection system for:
 * - Performance metrics (response time, throughput, error rate)
 * - Business metrics (request count, user actions, feature usage)
 * - System metrics (CPU, memory, connections)
 * - Custom metrics (service-specific measurements)
 * - Prometheus-compatible output
 */

class MetricsCollector {
    constructor(serviceName, options = {}) {
        this.serviceName = serviceName;
        this.options = {
            enabled: options.enabled !== false,
            maxHistorySize: options.maxHistorySize || 10000,
            aggregationInterval: options.aggregationInterval || 60000, // 1 minute
            retentionPeriod: options.retentionPeriod || 3600000, // 1 hour
            enableSystemMetrics: options.enableSystemMetrics !== false,
            enableCustomMetrics: options.enableCustomMetrics !== false,
            ...options
        };

        // Metrics storage
        this.counters = new Map();
        this.gauges = new Map();
        this.histograms = new Map();
        this.timers = new Map();
        this.customMetrics = new Map();

        // Time-series data for aggregation
        this.timeSeriesData = new Map();

        // Active timers for ongoing operations
        this.activeTimers = new Map();

        // System metrics
        this.systemMetrics = {
            cpu: [],
            memory: [],
            eventLoop: []
        };

        // Start collection if enabled
        if (this.options.enabled) {
            this.startCollection();
        }
    }

    /**
     * Start metrics collection
     */
    startCollection() {
        // Start system metrics collection
        if (this.options.enableSystemMetrics) {
            this.startSystemMetricsCollection();
        }

        // Start aggregation timer
        this.aggregationTimer = setInterval(() => {
            this.aggregateMetrics();
        }, this.options.aggregationInterval);

        // Start cleanup timer
        this.cleanupTimer = setInterval(() => {
            this.cleanupOldMetrics();
        }, this.options.retentionPeriod / 4); // Cleanup every quarter of retention period
    }

    /**
     * Stop metrics collection
     */
    stopCollection() {
        if (this.aggregationTimer) {
            clearInterval(this.aggregationTimer);
            this.aggregationTimer = null;
        }

        if (this.cleanupTimer) {
            clearInterval(this.cleanupTimer);
            this.cleanupTimer = null;
        }

        if (this.systemMetricsTimer) {
            clearInterval(this.systemMetricsTimer);
            this.systemMetricsTimer = null;
        }
    }

    /**
     * Counter: Incrementing value
     */
    incrementCounter(name, value = 1, labels = {}) {
        if (!this.options.enabled) return;

        const key = this.getMetricKey(name, labels);
        const current = this.counters.get(key) || 0;
        this.counters.set(key, current + value);

        this.recordTimeSeries('counter', name, current + value, labels);
    }

    /**
     * Gauge: Point-in-time value
     */
    setGauge(name, value, labels = {}) {
        if (!this.options.enabled) return;

        const key = this.getMetricKey(name, labels);
        this.gauges.set(key, value);

        this.recordTimeSeries('gauge', name, value, labels);
    }

    /**
     * Histogram: Distribution of values
     */
    recordHistogram(name, value, labels = {}) {
        if (!this.options.enabled) return;

        const key = this.getMetricKey(name, labels);
        let histogram = this.histograms.get(key);

        if (!histogram) {
            histogram = {
                count: 0,
                sum: 0,
                min: Infinity,
                max: -Infinity,
                buckets: this.createHistogramBuckets(),
                values: []
            };
            this.histograms.set(key, histogram);
        }

        // Update histogram
        histogram.count++;
        histogram.sum += value;
        histogram.min = Math.min(histogram.min, value);
        histogram.max = Math.max(histogram.max, value);

        // Update buckets
        for (const bucket of histogram.buckets) {
            if (value <= bucket.upperBound) {
                bucket.count++;
            }
        }

        // Store value for percentile calculation
        histogram.values.push(value);
        if (histogram.values.length > this.options.maxHistorySize) {
            histogram.values.shift();
        }

        this.recordTimeSeries('histogram', name, value, labels);
    }

    /**
     * Timer: Start timing an operation
     */
    startTimer(name, labels = {}) {
        if (!this.options.enabled) return null;

        const timerId = this.generateTimerId(name, labels);
        const timer = {
            name,
            labels,
            startTime: Date.now(),
            startHrTime: process.hrtime.bigint()
        };

        this.activeTimers.set(timerId, timer);
        return timerId;
    }

    /**
     * Timer: End timing an operation
     */
    endTimer(timerId) {
        if (!this.options.enabled || !timerId) return;

        const timer = this.activeTimers.get(timerId);
        if (!timer) return;

        const endTime = Date.now();
        const endHrTime = process.hrtime.bigint();

        const durationMs = endTime - timer.startTime;
        const durationNs = Number(endHrTime - timer.startHrTime);

        // Record as histogram
        this.recordHistogram(`${timer.name}_duration_ms`, durationMs, timer.labels);

        // Store in timers map for summary
        const key = this.getMetricKey(timer.name, timer.labels);
        let timerSummary = this.timers.get(key);

        if (!timerSummary) {
            timerSummary = {
                count: 0,
                totalMs: 0,
                avgMs: 0,
                minMs: Infinity,
                maxMs: -Infinity
            };
            this.timers.set(key, timerSummary);
        }

        timerSummary.count++;
        timerSummary.totalMs += durationMs;
        timerSummary.avgMs = timerSummary.totalMs / timerSummary.count;
        timerSummary.minMs = Math.min(timerSummary.minMs, durationMs);
        timerSummary.maxMs = Math.max(timerSummary.maxMs, durationMs);

        this.activeTimers.delete(timerId);

        return {
            durationMs,
            durationNs
        };
    }

    /**
     * Custom Metric: Service-specific measurement
     */
    recordCustomMetric(name, value, type = 'gauge', labels = {}) {
        if (!this.options.enabled || !this.options.enableCustomMetrics) return;

        const key = this.getMetricKey(name, labels);
        const metric = {
            name,
            type,
            value,
            labels,
            timestamp: Date.now()
        };

        this.customMetrics.set(key, metric);
        this.recordTimeSeries('custom', name, value, labels);
    }

    /**
     * Convenience method: Track HTTP request
     */
    trackHttpRequest(method, path, statusCode, durationMs, labels = {}) {
        const requestLabels = {
            method,
            path,
            status_code: statusCode.toString(),
            ...labels
        };

        this.incrementCounter('http_requests_total', 1, requestLabels);
        this.recordHistogram('http_request_duration_ms', durationMs, requestLabels);

        if (statusCode >= 400) {
            this.incrementCounter('http_errors_total', 1, requestLabels);
        }
    }

    /**
     * Convenience method: Track business event
     */
    trackBusinessEvent(eventType, eventName, value = 1, labels = {}) {
        const eventLabels = {
            event_type: eventType,
            event_name: eventName,
            ...labels
        };

        this.incrementCounter('business_events_total', value, eventLabels);
        this.recordCustomMetric(`business_${eventType}_${eventName}`, value, 'counter', eventLabels);
    }

    /**
     * Convenience method: Track feature usage
     */
    trackFeatureUsage(feature, action, userId = null, labels = {}) {
        const featureLabels = {
            feature,
            action,
            ...labels
        };

        if (userId) {
            featureLabels.user_id = userId;
        }

        this.incrementCounter('feature_usage_total', 1, featureLabels);
        this.recordCustomMetric(`feature_${feature}_${action}`, 1, 'counter', featureLabels);
    }

    /**
     * Start system metrics collection
     */
    startSystemMetricsCollection() {
        this.systemMetricsTimer = setInterval(() => {
            this.collectSystemMetrics();
        }, 5000); // Collect every 5 seconds
    }

    /**
     * Collect system metrics
     */
    collectSystemMetrics() {
        try {
            // Memory metrics
            const memoryUsage = process.memoryUsage();
            this.setGauge('system_memory_rss_bytes', memoryUsage.rss);
            this.setGauge('system_memory_heap_used_bytes', memoryUsage.heapUsed);
            this.setGauge('system_memory_heap_total_bytes', memoryUsage.heapTotal);
            this.setGauge('system_memory_external_bytes', memoryUsage.external);

            // CPU metrics
            const cpuUsage = process.cpuUsage();
            this.setGauge('system_cpu_user_microseconds', cpuUsage.user);
            this.setGauge('system_cpu_system_microseconds', cpuUsage.system);

            // Event loop lag
            const start = process.hrtime.bigint();
            setImmediate(() => {
                const lag = Number(process.hrtime.bigint() - start) / 1e6; // Convert to milliseconds
                this.setGauge('system_event_loop_lag_ms', lag);
            });

            // Process uptime
            this.setGauge('system_process_uptime_seconds', process.uptime());

            // Active handles and requests
            this.setGauge('system_active_handles', process._getActiveHandles().length);
            this.setGauge('system_active_requests', process._getActiveRequests().length);

        } catch (error) {
            // Silently ignore system metrics collection errors
        }
    }

    /**
     * Get all metrics
     */
    getAllMetrics() {
        return {
            counters: this.getCounters(),
            gauges: this.getGauges(),
            histograms: this.getHistograms(),
            timers: this.getTimers(),
            customMetrics: this.getCustomMetrics(),
            systemMetrics: this.getSystemMetrics()
        };
    }

    /**
     * Get counters
     */
    getCounters() {
        const counters = {};
        for (const [key, value] of this.counters.entries()) {
            const parsed = this.parseMetricKey(key);
            counters[parsed.name] = counters[parsed.name] || [];
            counters[parsed.name].push({
                labels: parsed.labels,
                value
            });
        }
        return counters;
    }

    /**
     * Get gauges
     */
    getGauges() {
        const gauges = {};
        for (const [key, value] of this.gauges.entries()) {
            const parsed = this.parseMetricKey(key);
            gauges[parsed.name] = gauges[parsed.name] || [];
            gauges[parsed.name].push({
                labels: parsed.labels,
                value
            });
        }
        return gauges;
    }

    /**
     * Get histograms
     */
    getHistograms() {
        const histograms = {};
        for (const [key, histogram] of this.histograms.entries()) {
            const parsed = this.parseMetricKey(key);
            const percentiles = this.calculatePercentiles(histogram.values);

            histograms[parsed.name] = histograms[parsed.name] || [];
            histograms[parsed.name].push({
                labels: parsed.labels,
                count: histogram.count,
                sum: histogram.sum,
                avg: histogram.count > 0 ? histogram.sum / histogram.count : 0,
                min: histogram.min === Infinity ? 0 : histogram.min,
                max: histogram.max === -Infinity ? 0 : histogram.max,
                percentiles,
                buckets: histogram.buckets
            });
        }
        return histograms;
    }

    /**
     * Get timers
     */
    getTimers() {
        const timers = {};
        for (const [key, timer] of this.timers.entries()) {
            const parsed = this.parseMetricKey(key);
            timers[parsed.name] = timers[parsed.name] || [];
            timers[parsed.name].push({
                labels: parsed.labels,
                ...timer
            });
        }
        return timers;
    }

    /**
     * Get custom metrics
     */
    getCustomMetrics() {
        const metrics = {};
        for (const [key, metric] of this.customMetrics.entries()) {
            metrics[metric.name] = metrics[metric.name] || [];
            metrics[metric.name].push({
                labels: metric.labels,
                value: metric.value,
                type: metric.type,
                timestamp: metric.timestamp
            });
        }
        return metrics;
    }

    /**
     * Get system metrics summary
     */
    getSystemMetrics() {
        const systemMetrics = {};
        for (const [key, value] of this.gauges.entries()) {
            if (key.startsWith('system_')) {
                const parsed = this.parseMetricKey(key);
                systemMetrics[parsed.name] = value;
            }
        }
        return systemMetrics;
    }

    /**
     * Get Prometheus format output
     */
    getPrometheusMetrics() {
        let output = '';

        // Counters
        const counters = this.getCounters();
        for (const [name, entries] of Object.entries(counters)) {
            output += `# HELP ${name} Total number of ${name}\n`;
            output += `# TYPE ${name} counter\n`;
            for (const entry of entries) {
                const labels = this.formatPrometheusLabels(entry.labels);
                output += `${name}${labels} ${entry.value}\n`;
            }
            output += '\n';
        }

        // Gauges
        const gauges = this.getGauges();
        for (const [name, entries] of Object.entries(gauges)) {
            output += `# HELP ${name} Current value of ${name}\n`;
            output += `# TYPE ${name} gauge\n`;
            for (const entry of entries) {
                const labels = this.formatPrometheusLabels(entry.labels);
                output += `${name}${labels} ${entry.value}\n`;
            }
            output += '\n';
        }

        // Histograms
        const histograms = this.getHistograms();
        for (const [name, entries] of Object.entries(histograms)) {
            output += `# HELP ${name} Distribution of ${name}\n`;
            output += `# TYPE ${name} histogram\n`;
            for (const entry of entries) {
                const labels = this.formatPrometheusLabels(entry.labels);

                // Bucket metrics
                for (const bucket of entry.buckets) {
                    const bucketLabels = this.formatPrometheusLabels({
                        ...entry.labels,
                        le: bucket.upperBound.toString()
                    });
                    output += `${name}_bucket${bucketLabels} ${bucket.count}\n`;
                }

                // Summary metrics
                output += `${name}_count${labels} ${entry.count}\n`;
                output += `${name}_sum${labels} ${entry.sum}\n`;
            }
            output += '\n';
        }

        return output;
    }

    /**
     * Utility methods
     */
    getMetricKey(name, labels) {
        const labelStr = Object.keys(labels).length > 0
            ? JSON.stringify(labels)
            : '';
        return `${name}:${labelStr}`;
    }

    parseMetricKey(key) {
        const [name, labelStr] = key.split(':');
        const labels = labelStr ? JSON.parse(labelStr) : {};
        return { name, labels };
    }

    generateTimerId(name, labels) {
        return `timer_${name}_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }

    createHistogramBuckets() {
        const buckets = [
            { upperBound: 1, count: 0 },
            { upperBound: 5, count: 0 },
            { upperBound: 10, count: 0 },
            { upperBound: 50, count: 0 },
            { upperBound: 100, count: 0 },
            { upperBound: 500, count: 0 },
            { upperBound: 1000, count: 0 },
            { upperBound: 5000, count: 0 },
            { upperBound: 10000, count: 0 },
            { upperBound: Infinity, count: 0 }
        ];
        return buckets;
    }

    calculatePercentiles(values) {
        if (values.length === 0) return {};

        const sorted = [...values].sort((a, b) => a - b);
        const percentiles = [50, 90, 95, 99];
        const result = {};

        for (const p of percentiles) {
            const index = Math.ceil((p / 100) * sorted.length) - 1;
            result[`p${p}`] = sorted[Math.max(0, index)];
        }

        return result;
    }

    formatPrometheusLabels(labels) {
        if (Object.keys(labels).length === 0) return '';

        const labelPairs = Object.entries(labels)
            .map(([key, value]) => `${key}="${value}"`)
            .join(',');

        return `{${labelPairs}}`;
    }

    recordTimeSeries(type, name, value, labels) {
        const timestamp = Date.now();
        const key = this.getMetricKey(name, labels);

        let series = this.timeSeriesData.get(key);
        if (!series) {
            series = {
                type,
                name,
                labels,
                points: []
            };
            this.timeSeriesData.set(key, series);
        }

        series.points.push({ timestamp, value });

        // Limit history size
        if (series.points.length > this.options.maxHistorySize) {
            series.points.shift();
        }
    }

    aggregateMetrics() {
        // This method can be used for periodic aggregation
        // Currently just cleans up old time series data
        const cutoff = Date.now() - this.options.retentionPeriod;

        for (const [key, series] of this.timeSeriesData.entries()) {
            series.points = series.points.filter(point => point.timestamp > cutoff);

            if (series.points.length === 0) {
                this.timeSeriesData.delete(key);
            }
        }
    }

    cleanupOldMetrics() {
        // Clean up old histogram values
        for (const [key, histogram] of this.histograms.entries()) {
            if (histogram.values.length > this.options.maxHistorySize) {
                histogram.values = histogram.values.slice(-this.options.maxHistorySize);
            }
        }

        // Clean up old custom metrics
        const cutoff = Date.now() - this.options.retentionPeriod;
        for (const [key, metric] of this.customMetrics.entries()) {
            if (metric.timestamp < cutoff) {
                this.customMetrics.delete(key);
            }
        }
    }

    /**
     * Reset all metrics
     */
    reset() {
        this.counters.clear();
        this.gauges.clear();
        this.histograms.clear();
        this.timers.clear();
        this.customMetrics.clear();
        this.timeSeriesData.clear();
        this.activeTimers.clear();
    }

    /**
     * Health check
     */
    async healthCheck() {
        return {
            status: 'operational',
            enabled: this.options.enabled,
            activeTimers: this.activeTimers.size,
            countersCount: this.counters.size,
            gaugesCount: this.gauges.size,
            histogramsCount: this.histograms.size,
            customMetricsCount: this.customMetrics.size,
            timeSeriesCount: this.timeSeriesData.size
        };
    }
}

module.exports = MetricsCollector;