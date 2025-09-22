const EventEmitter = require('events');
const os = require('os');
const process = require('process');
const { performance } = require('perf_hooks');

/**
 * Comprehensive Health Monitoring System
 * Tracks system health, trading performance, and resource utilization
 */
class HealthMonitor extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            checkInterval: config.checkInterval || 5000, // 5 seconds
            thresholds: config.thresholds || {
                cpu: { warning: 70, critical: 85 },
                memory: { warning: 80, critical: 90 },
                disk: { warning: 85, critical: 95 },
                latency: { warning: 100, critical: 500 },
                errorRate: { warning: 5, critical: 10 }
            },
            retentionPeriod: config.retentionPeriod || 86400000, // 24 hours
            ...config
        };

        this.metrics = new Map();
        this.healthChecks = new Map();
        this.isMonitoring = false;
        this.lastCheck = null;
        this.checkHistory = [];

        this.initializeHealthChecks();
    }

    /**
     * Initialize default health checks
     */
    initializeHealthChecks() {
        // System health checks
        this.registerHealthCheck('system.cpu', this.checkCpuUsage.bind(this));
        this.registerHealthCheck('system.memory', this.checkMemoryUsage.bind(this));
        this.registerHealthCheck('system.disk', this.checkDiskSpace.bind(this));
        this.registerHealthCheck('system.uptime', this.checkUptime.bind(this));

        // Application health checks
        this.registerHealthCheck('app.database', this.checkDatabaseConnection.bind(this));
        this.registerHealthCheck('app.trading_engine', this.checkTradingEngine.bind(this));
        this.registerHealthCheck('app.market_data', this.checkMarketDataFeed.bind(this));
        this.registerHealthCheck('app.risk_manager', this.checkRiskManager.bind(this));

        // Performance checks
        this.registerHealthCheck('performance.latency', this.checkLatency.bind(this));
        this.registerHealthCheck('performance.throughput', this.checkThroughput.bind(this));
        this.registerHealthCheck('performance.error_rate', this.checkErrorRate.bind(this));
    }

    /**
     * Register a custom health check
     */
    registerHealthCheck(name, checkFunction) {
        this.healthChecks.set(name, {
            name,
            check: checkFunction,
            lastRun: null,
            lastResult: null,
            enabled: true
        });
    }

    /**
     * Start monitoring
     */
    start() {
        if (this.isMonitoring) return;

        this.isMonitoring = true;
        this.monitoringInterval = setInterval(() => {
            this.runHealthChecks();
        }, this.config.checkInterval);

        this.emit('monitoring.started');
        console.log('✅ Health monitoring started');
    }

    /**
     * Stop monitoring
     */
    stop() {
        if (!this.isMonitoring) return;

        this.isMonitoring = false;
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
        }

        this.emit('monitoring.stopped');
        console.log('🛑 Health monitoring stopped');
    }

    /**
     * Run all health checks
     */
    async runHealthChecks() {
        const startTime = performance.now();
        const results = {};
        const alerts = [];

        for (const [name, healthCheck] of this.healthChecks) {
            if (!healthCheck.enabled) continue;

            try {
                const result = await healthCheck.check();
                healthCheck.lastRun = new Date();
                healthCheck.lastResult = result;
                results[name] = result;

                // Check thresholds and generate alerts
                const alert = this.evaluateThreshold(name, result);
                if (alert) {
                    alerts.push(alert);
                }

            } catch (error) {
                const errorResult = {
                    status: 'error',
                    message: error.message,
                    timestamp: new Date()
                };
                healthCheck.lastResult = errorResult;
                results[name] = errorResult;

                alerts.push({
                    type: 'critical',
                    component: name,
                    message: `Health check failed: ${error.message}`,
                    timestamp: new Date()
                });
            }
        }

        const checkDuration = performance.now() - startTime;
        const overallHealth = this.calculateOverallHealth(results);

        const healthReport = {
            timestamp: new Date(),
            duration: checkDuration,
            overallHealth,
            results,
            alerts
        };

        this.lastCheck = healthReport;
        this.checkHistory.push(healthReport);
        this.cleanupHistory();

        // Emit events
        this.emit('health.check.completed', healthReport);

        if (alerts.length > 0) {
            this.emit('health.alerts', alerts);
        }

        // Store metrics
        this.updateMetrics(results);
    }

    /**
     * System health checks
     */
    async checkCpuUsage() {
        return new Promise((resolve) => {
            const startUsage = process.cpuUsage();
            setTimeout(() => {
                const endUsage = process.cpuUsage(startUsage);
                const totalUsage = (endUsage.user + endUsage.system) / 1000000; // Convert to seconds
                const cpuPercent = (totalUsage / 0.1) * 100; // 100ms measurement period

                resolve({
                    status: cpuPercent < this.config.thresholds.cpu.warning ? 'healthy' :
                           cpuPercent < this.config.thresholds.cpu.critical ? 'warning' : 'critical',
                    value: cpuPercent,
                    unit: '%',
                    timestamp: new Date()
                });
            }, 100);
        });
    }

    async checkMemoryUsage() {
        const totalMemory = os.totalmem();
        const freeMemory = os.freemem();
        const usedMemory = totalMemory - freeMemory;
        const memoryPercent = (usedMemory / totalMemory) * 100;

        return {
            status: memoryPercent < this.config.thresholds.memory.warning ? 'healthy' :
                   memoryPercent < this.config.thresholds.memory.critical ? 'warning' : 'critical',
            value: memoryPercent,
            used: usedMemory,
            total: totalMemory,
            unit: '%',
            timestamp: new Date()
        };
    }

    async checkDiskSpace() {
        // Simplified disk check - in production, use actual disk monitoring
        const usage = Math.random() * 100; // Placeholder

        return {
            status: usage < this.config.thresholds.disk.warning ? 'healthy' :
                   usage < this.config.thresholds.disk.critical ? 'warning' : 'critical',
            value: usage,
            unit: '%',
            timestamp: new Date()
        };
    }

    async checkUptime() {
        const uptime = process.uptime();

        return {
            status: 'healthy',
            value: uptime,
            unit: 'seconds',
            timestamp: new Date()
        };
    }

    /**
     * Application health checks
     */
    async checkDatabaseConnection() {
        try {
            // Placeholder for actual database check
            return {
                status: 'healthy',
                latency: Math.random() * 50,
                timestamp: new Date()
            };
        } catch (error) {
            return {
                status: 'critical',
                error: error.message,
                timestamp: new Date()
            };
        }
    }

    async checkTradingEngine() {
        // Placeholder for trading engine health check
        return {
            status: 'healthy',
            activeOrders: Math.floor(Math.random() * 100),
            lastTrade: new Date(Date.now() - Math.random() * 60000),
            timestamp: new Date()
        };
    }

    async checkMarketDataFeed() {
        // Placeholder for market data feed check
        const latency = Math.random() * 200;
        return {
            status: latency < 100 ? 'healthy' : latency < 500 ? 'warning' : 'critical',
            latency,
            lastUpdate: new Date(),
            timestamp: new Date()
        };
    }

    async checkRiskManager() {
        // Placeholder for risk manager check
        return {
            status: 'healthy',
            exposureRatio: Math.random() * 0.8,
            timestamp: new Date()
        };
    }

    /**
     * Performance health checks
     */
    async checkLatency() {
        const latency = Math.random() * 1000; // Placeholder

        return {
            status: latency < this.config.thresholds.latency.warning ? 'healthy' :
                   latency < this.config.thresholds.latency.critical ? 'warning' : 'critical',
            value: latency,
            unit: 'ms',
            timestamp: new Date()
        };
    }

    async checkThroughput() {
        const throughput = Math.random() * 1000; // Placeholder

        return {
            status: 'healthy',
            value: throughput,
            unit: 'requests/sec',
            timestamp: new Date()
        };
    }

    async checkErrorRate() {
        const errorRate = Math.random() * 15; // Placeholder

        return {
            status: errorRate < this.config.thresholds.errorRate.warning ? 'healthy' :
                   errorRate < this.config.thresholds.errorRate.critical ? 'warning' : 'critical',
            value: errorRate,
            unit: '%',
            timestamp: new Date()
        };
    }

    /**
     * Evaluate thresholds and generate alerts
     */
    evaluateThreshold(component, result) {
        if (!result || result.status === 'healthy') return null;

        return {
            type: result.status, // warning or critical
            component,
            message: `${component} health check ${result.status}: ${result.value}${result.unit || ''}`,
            value: result.value,
            threshold: this.getThreshold(component, result.status),
            timestamp: new Date()
        };
    }

    getThreshold(component, level) {
        const parts = component.split('.');
        const metric = parts[parts.length - 1];
        return this.config.thresholds[metric]?.[level] || null;
    }

    /**
     * Calculate overall health status
     */
    calculateOverallHealth(results) {
        const statuses = Object.values(results).map(r => r.status);

        if (statuses.includes('critical')) return 'critical';
        if (statuses.includes('warning')) return 'warning';
        if (statuses.includes('error')) return 'critical';
        return 'healthy';
    }

    /**
     * Update metrics storage
     */
    updateMetrics(results) {
        const timestamp = new Date();

        for (const [component, result] of Object.entries(results)) {
            if (!this.metrics.has(component)) {
                this.metrics.set(component, []);
            }

            const componentMetrics = this.metrics.get(component);
            componentMetrics.push({
                timestamp,
                ...result
            });

            // Keep only recent metrics
            const cutoff = timestamp.getTime() - this.config.retentionPeriod;
            this.metrics.set(component, componentMetrics.filter(m =>
                m.timestamp.getTime() > cutoff
            ));
        }
    }

    /**
     * Clean up old history
     */
    cleanupHistory() {
        const cutoff = new Date(Date.now() - this.config.retentionPeriod);
        this.checkHistory = this.checkHistory.filter(check =>
            check.timestamp > cutoff
        );
    }

    /**
     * Get current health status
     */
    getHealthStatus() {
        return {
            isMonitoring: this.isMonitoring,
            lastCheck: this.lastCheck,
            overallHealth: this.lastCheck?.overallHealth || 'unknown',
            checkCount: this.checkHistory.length,
            registeredChecks: Array.from(this.healthChecks.keys())
        };
    }

    /**
     * Get metrics for a specific component
     */
    getMetrics(component, timeRange = null) {
        const metrics = this.metrics.get(component) || [];

        if (!timeRange) return metrics;

        const cutoff = new Date(Date.now() - timeRange);
        return metrics.filter(m => m.timestamp > cutoff);
    }

    /**
     * Get all metrics
     */
    getAllMetrics() {
        const result = {};
        for (const [component, metrics] of this.metrics) {
            result[component] = metrics;
        }
        return result;
    }
}

module.exports = HealthMonitor;