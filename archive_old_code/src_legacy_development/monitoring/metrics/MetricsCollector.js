const EventEmitter = require('events');
const { performance } = require('perf_hooks');

/**
 * Advanced Metrics Collection System
 * Collects, aggregates, and analyzes trading and system metrics
 */
class MetricsCollector extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            aggregationInterval: config.aggregationInterval || 60000, // 1 minute
            retentionPeriod: config.retentionPeriod || 604800000, // 7 days
            batchSize: config.batchSize || 1000,
            enableRealTime: config.enableRealTime !== false,
            ...config
        };

        this.metrics = new Map();
        this.counters = new Map();
        this.histograms = new Map();
        this.gauges = new Map();
        this.timers = new Map();

        this.isCollecting = false;
        this.aggregationTimer = null;

        this.initializeDefaultMetrics();
    }

    /**
     * Initialize default trading metrics
     */
    initializeDefaultMetrics() {
        // Trading Performance Metrics
        this.createCounter('trades.executed');
        this.createCounter('trades.profitable');
        this.createCounter('trades.losses');
        this.createCounter('orders.placed');
        this.createCounter('orders.filled');
        this.createCounter('orders.cancelled');
        this.createCounter('errors.trading');
        this.createCounter('errors.market_data');
        this.createCounter('errors.risk');

        // System Performance Metrics
        this.createGauge('system.cpu_usage');
        this.createGauge('system.memory_usage');
        this.createGauge('system.active_connections');
        this.createGauge('trading.active_positions');
        this.createGauge('trading.portfolio_value');
        this.createGauge('trading.unrealized_pnl');
        this.createGauge('trading.realized_pnl');
        this.createGauge('risk.exposure_ratio');
        this.createGauge('risk.var_estimate');

        // Latency Histograms
        this.createHistogram('latency.order_execution');
        this.createHistogram('latency.market_data');
        this.createHistogram('latency.risk_calculation');
        this.createHistogram('latency.strategy_decision');
        this.createHistogram('latency.database_query');

        // Trading Histograms
        this.createHistogram('trading.trade_duration');
        this.createHistogram('trading.trade_pnl');
        this.createHistogram('trading.position_size');
        this.createHistogram('trading.slippage');
    }

    /**
     * Start metrics collection
     */
    start() {
        if (this.isCollecting) return;

        this.isCollecting = true;

        if (this.config.aggregationInterval > 0) {
            this.aggregationTimer = setInterval(() => {
                this.aggregateMetrics();
            }, this.config.aggregationInterval);
        }

        this.emit('collection.started');
        console.log('📊 Metrics collection started');
    }

    /**
     * Stop metrics collection
     */
    stop() {
        if (!this.isCollecting) return;

        this.isCollecting = false;

        if (this.aggregationTimer) {
            clearInterval(this.aggregationTimer);
            this.aggregationTimer = null;
        }

        this.emit('collection.stopped');
        console.log('📊 Metrics collection stopped');
    }

    /**
     * Create a counter metric
     */
    createCounter(name, labels = {}) {
        if (!this.counters.has(name)) {
            this.counters.set(name, {
                name,
                type: 'counter',
                value: 0,
                labels,
                history: [],
                created: new Date()
            });
        }
        return this.counters.get(name);
    }

    /**
     * Increment a counter
     */
    incrementCounter(name, value = 1, labels = {}) {
        const counter = this.counters.get(name);
        if (!counter) {
            throw new Error(`Counter ${name} not found`);
        }

        counter.value += value;
        counter.history.push({
            timestamp: new Date(),
            value: counter.value,
            increment: value,
            labels
        });

        this.emit('metric.updated', {
            type: 'counter',
            name,
            value: counter.value,
            increment: value,
            labels
        });

        if (this.config.enableRealTime) {
            this.emit('metric.realtime', {
                type: 'counter',
                name,
                value: counter.value,
                labels
            });
        }
    }

    /**
     * Create a gauge metric
     */
    createGauge(name, labels = {}) {
        if (!this.gauges.has(name)) {
            this.gauges.set(name, {
                name,
                type: 'gauge',
                value: 0,
                labels,
                history: [],
                created: new Date()
            });
        }
        return this.gauges.get(name);
    }

    /**
     * Set gauge value
     */
    setGauge(name, value, labels = {}) {
        const gauge = this.gauges.get(name);
        if (!gauge) {
            throw new Error(`Gauge ${name} not found`);
        }

        const previousValue = gauge.value;
        gauge.value = value;
        gauge.history.push({
            timestamp: new Date(),
            value,
            previousValue,
            labels
        });

        this.emit('metric.updated', {
            type: 'gauge',
            name,
            value,
            previousValue,
            labels
        });

        if (this.config.enableRealTime) {
            this.emit('metric.realtime', {
                type: 'gauge',
                name,
                value,
                labels
            });
        }
    }

    /**
     * Create a histogram metric
     */
    createHistogram(name, buckets = null, labels = {}) {
        if (!buckets) {
            buckets = [0.1, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
        }

        if (!this.histograms.has(name)) {
            this.histograms.set(name, {
                name,
                type: 'histogram',
                buckets: buckets.map(b => ({ le: b, count: 0 })),
                count: 0,
                sum: 0,
                labels,
                observations: [],
                created: new Date()
            });
        }
        return this.histograms.get(name);
    }

    /**
     * Observe a value in histogram
     */
    observeHistogram(name, value, labels = {}) {
        const histogram = this.histograms.get(name);
        if (!histogram) {
            throw new Error(`Histogram ${name} not found`);
        }

        histogram.count++;
        histogram.sum += value;

        // Update buckets
        for (const bucket of histogram.buckets) {
            if (value <= bucket.le) {
                bucket.count++;
            }
        }

        histogram.observations.push({
            timestamp: new Date(),
            value,
            labels
        });

        // Calculate percentiles
        const percentiles = this.calculatePercentiles(histogram);

        this.emit('metric.updated', {
            type: 'histogram',
            name,
            value,
            count: histogram.count,
            sum: histogram.sum,
            mean: histogram.sum / histogram.count,
            percentiles,
            labels
        });

        if (this.config.enableRealTime) {
            this.emit('metric.realtime', {
                type: 'histogram',
                name,
                value,
                percentiles,
                labels
            });
        }
    }

    /**
     * Start a timer
     */
    startTimer(name, labels = {}) {
        const timerId = `${name}_${Date.now()}_${Math.random()}`;
        this.timers.set(timerId, {
            name,
            startTime: performance.now(),
            labels
        });
        return timerId;
    }

    /**
     * End a timer and record the duration
     */
    endTimer(timerId) {
        const timer = this.timers.get(timerId);
        if (!timer) {
            throw new Error(`Timer ${timerId} not found`);
        }

        const duration = performance.now() - timer.startTime;
        this.timers.delete(timerId);

        // Record in histogram if it exists
        if (this.histograms.has(timer.name)) {
            this.observeHistogram(timer.name, duration, timer.labels);
        }

        return duration;
    }

    /**
     * Record trading metrics
     */
    recordTrade(trade) {
        this.incrementCounter('trades.executed');

        if (trade.pnl > 0) {
            this.incrementCounter('trades.profitable');
        } else {
            this.incrementCounter('trades.losses');
        }

        this.observeHistogram('trading.trade_pnl', trade.pnl);
        this.observeHistogram('trading.trade_duration', trade.duration);
        this.observeHistogram('trading.position_size', Math.abs(trade.quantity));

        if (trade.slippage !== undefined) {
            this.observeHistogram('trading.slippage', trade.slippage);
        }

        this.emit('trade.recorded', trade);
    }

    /**
     * Record order metrics
     */
    recordOrder(order) {
        this.incrementCounter('orders.placed');

        if (order.status === 'filled') {
            this.incrementCounter('orders.filled');
        } else if (order.status === 'cancelled') {
            this.incrementCounter('orders.cancelled');
        }

        if (order.executionTime) {
            this.observeHistogram('latency.order_execution', order.executionTime);
        }

        this.emit('order.recorded', order);
    }

    /**
     * Record error metrics
     */
    recordError(type, error) {
        this.incrementCounter(`errors.${type}`, 1, {
            error_type: error.name || 'unknown',
            error_message: error.message
        });

        this.emit('error.recorded', { type, error });
    }

    /**
     * Update portfolio metrics
     */
    updatePortfolioMetrics(portfolio) {
        this.setGauge('trading.portfolio_value', portfolio.totalValue);
        this.setGauge('trading.unrealized_pnl', portfolio.unrealizedPnl);
        this.setGauge('trading.realized_pnl', portfolio.realizedPnl);
        this.setGauge('trading.active_positions', portfolio.positionCount);

        this.emit('portfolio.updated', portfolio);
    }

    /**
     * Update risk metrics
     */
    updateRiskMetrics(risk) {
        this.setGauge('risk.exposure_ratio', risk.exposureRatio);
        this.setGauge('risk.var_estimate', risk.varEstimate);

        this.emit('risk.updated', risk);
    }

    /**
     * Calculate percentiles for histogram
     */
    calculatePercentiles(histogram) {
        if (histogram.observations.length === 0) return {};

        const values = histogram.observations
            .slice(-1000) // Use last 1000 observations
            .map(obs => obs.value)
            .sort((a, b) => a - b);

        const percentiles = {};
        const targets = [50, 75, 90, 95, 99];

        for (const p of targets) {
            const index = Math.ceil((p / 100) * values.length) - 1;
            percentiles[`p${p}`] = values[Math.max(0, index)];
        }

        return percentiles;
    }

    /**
     * Aggregate metrics
     */
    aggregateMetrics() {
        const timestamp = new Date();
        const aggregation = {
            timestamp,
            counters: this.getCounterSummary(),
            gauges: this.getGaugeSummary(),
            histograms: this.getHistogramSummary()
        };

        this.emit('metrics.aggregated', aggregation);
        this.cleanupOldData();
    }

    /**
     * Get counter summary
     */
    getCounterSummary() {
        const summary = {};
        for (const [name, counter] of this.counters) {
            summary[name] = {
                value: counter.value,
                rate: this.calculateRate(counter)
            };
        }
        return summary;
    }

    /**
     * Get gauge summary
     */
    getGaugeSummary() {
        const summary = {};
        for (const [name, gauge] of this.gauges) {
            summary[name] = {
                value: gauge.value,
                change: this.calculateChange(gauge)
            };
        }
        return summary;
    }

    /**
     * Get histogram summary
     */
    getHistogramSummary() {
        const summary = {};
        for (const [name, histogram] of this.histograms) {
            summary[name] = {
                count: histogram.count,
                sum: histogram.sum,
                mean: histogram.count > 0 ? histogram.sum / histogram.count : 0,
                percentiles: this.calculatePercentiles(histogram)
            };
        }
        return summary;
    }

    /**
     * Calculate rate for counter
     */
    calculateRate(counter) {
        if (counter.history.length < 2) return 0;

        const recent = counter.history.slice(-10);
        const timeSpan = recent[recent.length - 1].timestamp - recent[0].timestamp;
        const valueChange = recent[recent.length - 1].value - recent[0].value;

        return timeSpan > 0 ? (valueChange / timeSpan) * 1000 : 0; // per second
    }

    /**
     * Calculate change for gauge
     */
    calculateChange(gauge) {
        if (gauge.history.length < 2) return 0;

        const current = gauge.history[gauge.history.length - 1].value;
        const previous = gauge.history[gauge.history.length - 2].value;

        return current - previous;
    }

    /**
     * Clean up old data
     */
    cleanupOldData() {
        const cutoff = new Date(Date.now() - this.config.retentionPeriod);

        // Clean counters
        for (const counter of this.counters.values()) {
            counter.history = counter.history.filter(h => h.timestamp > cutoff);
        }

        // Clean gauges
        for (const gauge of this.gauges.values()) {
            gauge.history = gauge.history.filter(h => h.timestamp > cutoff);
        }

        // Clean histograms
        for (const histogram of this.histograms.values()) {
            histogram.observations = histogram.observations.filter(obs => obs.timestamp > cutoff);
        }
    }

    /**
     * Get all metrics summary
     */
    getMetricsSummary() {
        return {
            counters: Object.fromEntries(this.counters),
            gauges: Object.fromEntries(this.gauges),
            histograms: Object.fromEntries(this.histograms),
            isCollecting: this.isCollecting
        };
    }

    /**
     * Export metrics in Prometheus format
     */
    exportPrometheusMetrics() {
        let output = '';

        // Export counters
        for (const [name, counter] of this.counters) {
            output += `# HELP ${name} ${counter.type} metric\n`;
            output += `# TYPE ${name} counter\n`;
            output += `${name} ${counter.value}\n\n`;
        }

        // Export gauges
        for (const [name, gauge] of this.gauges) {
            output += `# HELP ${name} ${gauge.type} metric\n`;
            output += `# TYPE ${name} gauge\n`;
            output += `${name} ${gauge.value}\n\n`;
        }

        // Export histograms
        for (const [name, histogram] of this.histograms) {
            output += `# HELP ${name} ${histogram.type} metric\n`;
            output += `# TYPE ${name} histogram\n`;

            for (const bucket of histogram.buckets) {
                output += `${name}_bucket{le="${bucket.le}"} ${bucket.count}\n`;
            }

            output += `${name}_count ${histogram.count}\n`;
            output += `${name}_sum ${histogram.sum}\n\n`;
        }

        return output;
    }
}

module.exports = MetricsCollector;