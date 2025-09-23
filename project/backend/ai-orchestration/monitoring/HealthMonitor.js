/**
 * HealthMonitor - Provider health monitoring and status tracking
 */

class HealthMonitor {
    constructor(options = {}) {
        this.providers = new Map();
        this.healthHistory = new Map();
        this.checkInterval = options.checkInterval || 60000; // 1 minute
        this.maxHistorySize = options.maxHistorySize || 100;
        this.healthThresholds = {
            errorRate: options.errorRateThreshold || 0.1, // 10%
            latency: options.latencyThreshold || 10000, // 10 seconds
            consecutiveFailures: options.consecutiveFailuresThreshold || 3
        };
        this.intervalId = null;
        this.isRunning = false;
    }

    /**
     * Add a provider to monitoring
     */
    addProvider(key, provider) {
        this.providers.set(key, {
            provider,
            status: 'unknown',
            lastCheck: null,
            consecutiveFailures: 0,
            errors: [],
            latencies: []
        });

        if (!this.healthHistory.has(key)) {
            this.healthHistory.set(key, []);
        }

        // Start monitoring if this is the first provider
        if (this.providers.size === 1 && !this.isRunning) {
            this.start();
        }
    }

    /**
     * Remove a provider from monitoring
     */
    removeProvider(key) {
        this.providers.delete(key);
        this.healthHistory.delete(key);

        // Stop monitoring if no providers left
        if (this.providers.size === 0 && this.isRunning) {
            this.stop();
        }
    }

    /**
     * Start health monitoring
     */
    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.intervalId = setInterval(() => {
            this.checkAllProviders();
        }, this.checkInterval);

        console.log('Health monitoring started');
    }

    /**
     * Stop health monitoring
     */
    stop() {
        if (!this.isRunning) return;

        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        console.log('Health monitoring stopped');
    }

    /**
     * Check health of all providers
     */
    async checkAllProviders() {
        const checks = Array.from(this.providers.keys()).map(key =>
            this.checkProvider(key).catch(error => ({
                key,
                error: error.message
            }))
        );

        await Promise.all(checks);
    }

    /**
     * Check health of a specific provider
     */
    async checkProvider(key) {
        const providerData = this.providers.get(key);
        if (!providerData) return;

        const { provider } = providerData;
        const startTime = Date.now();

        try {
            const result = await provider.healthCheck();
            const latency = Date.now() - startTime;

            // Update provider status
            providerData.status = result.healthy ? 'healthy' : 'unhealthy';
            providerData.lastCheck = new Date().toISOString();
            providerData.consecutiveFailures = result.healthy ? 0 : providerData.consecutiveFailures + 1;

            // Record latency
            providerData.latencies.push(latency);
            if (providerData.latencies.length > 50) {
                providerData.latencies = providerData.latencies.slice(-50);
            }

            // Create health record
            const healthRecord = {
                timestamp: new Date().toISOString(),
                healthy: result.healthy,
                latency,
                error: result.error || null,
                details: result
            };

            // Add to history
            this.addToHistory(key, healthRecord);

            // Check if provider should be marked as unhealthy
            this.evaluateProviderHealth(key);

            return healthRecord;

        } catch (error) {
            const latency = Date.now() - startTime;

            providerData.status = 'error';
            providerData.lastCheck = new Date().toISOString();
            providerData.consecutiveFailures++;

            // Record error
            this.recordError(key, error);

            const healthRecord = {
                timestamp: new Date().toISOString(),
                healthy: false,
                latency,
                error: error.message,
                details: null
            };

            this.addToHistory(key, healthRecord);
            this.evaluateProviderHealth(key);

            return healthRecord;
        }
    }

    /**
     * Record an error for a provider
     */
    recordError(key, error) {
        const providerData = this.providers.get(key);
        if (!providerData) return;

        providerData.errors.push({
            timestamp: new Date().toISOString(),
            error: error.message || error,
            stack: error.stack
        });

        // Keep only recent errors
        if (providerData.errors.length > 20) {
            providerData.errors = providerData.errors.slice(-20);
        }
    }

    /**
     * Add health record to history
     */
    addToHistory(key, record) {
        const history = this.healthHistory.get(key) || [];
        history.push(record);

        if (history.length > this.maxHistorySize) {
            this.healthHistory.set(key, history.slice(-this.maxHistorySize));
        } else {
            this.healthHistory.set(key, history);
        }
    }

    /**
     * Evaluate provider health based on thresholds
     */
    evaluateProviderHealth(key) {
        const providerData = this.providers.get(key);
        if (!providerData) return;

        const history = this.healthHistory.get(key) || [];
        const recentHistory = history.slice(-10); // Last 10 checks

        // Check error rate
        const errorCount = recentHistory.filter(h => !h.healthy).length;
        const errorRate = errorCount / recentHistory.length;

        // Check average latency
        const latencies = recentHistory.map(h => h.latency).filter(l => l > 0);
        const avgLatency = latencies.length > 0
            ? latencies.reduce((a, b) => a + b, 0) / latencies.length
            : 0;

        // Determine overall health status
        let status = 'healthy';

        if (providerData.consecutiveFailures >= this.healthThresholds.consecutiveFailures) {
            status = 'critical';
        } else if (errorRate > this.healthThresholds.errorRate) {
            status = 'degraded';
        } else if (avgLatency > this.healthThresholds.latency) {
            status = 'slow';
        }

        providerData.status = status;
    }

    /**
     * Get provider health status
     */
    getProviderHealth(key) {
        const providerData = this.providers.get(key);
        if (!providerData) {
            return { healthy: false, error: 'Provider not found' };
        }

        const history = this.healthHistory.get(key) || [];
        const recentHistory = history.slice(-10);

        const errorCount = recentHistory.filter(h => !h.healthy).length;
        const errorRate = errorCount / Math.max(recentHistory.length, 1);

        const latencies = recentHistory.map(h => h.latency).filter(l => l > 0);
        const avgLatency = latencies.length > 0
            ? latencies.reduce((a, b) => a + b, 0) / latencies.length
            : 0;

        const uptime = this.calculateUptime(key);

        return {
            healthy: providerData.status === 'healthy',
            status: providerData.status,
            lastCheck: providerData.lastCheck,
            consecutiveFailures: providerData.consecutiveFailures,
            errorRate,
            avgLatency,
            uptime,
            recentErrors: providerData.errors.slice(-5)
        };
    }

    /**
     * Calculate provider uptime percentage
     */
    calculateUptime(key) {
        const history = this.healthHistory.get(key) || [];
        if (history.length === 0) return 0;

        const healthyCount = history.filter(h => h.healthy).length;
        return (healthyCount / history.length) * 100;
    }

    /**
     * Get overall health summary
     */
    getHealthSummary() {
        const summary = {
            totalProviders: this.providers.size,
            healthy: 0,
            degraded: 0,
            critical: 0,
            unknown: 0,
            providers: {}
        };

        for (const [key, providerData] of this.providers) {
            const health = this.getProviderHealth(key);

            summary.providers[key] = health;

            switch (providerData.status) {
                case 'healthy':
                    summary.healthy++;
                    break;
                case 'degraded':
                case 'slow':
                    summary.degraded++;
                    break;
                case 'critical':
                case 'error':
                    summary.critical++;
                    break;
                default:
                    summary.unknown++;
            }
        }

        return summary;
    }

    /**
     * Get health trends for analytics
     */
    getHealthTrends(key, timeRange = '1h') {
        const history = this.healthHistory.get(key) || [];
        const now = Date.now();
        const ranges = {
            '1h': 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '24h': 24 * 60 * 60 * 1000,
            '7d': 7 * 24 * 60 * 60 * 1000
        };

        const cutoff = now - (ranges[timeRange] || ranges['1h']);

        const recentHistory = history.filter(h =>
            new Date(h.timestamp).getTime() > cutoff
        );

        return {
            timeRange,
            totalChecks: recentHistory.length,
            healthyChecks: recentHistory.filter(h => h.healthy).length,
            errorRate: recentHistory.length > 0
                ? recentHistory.filter(h => !h.healthy).length / recentHistory.length
                : 0,
            avgLatency: recentHistory.length > 0
                ? recentHistory.reduce((sum, h) => sum + h.latency, 0) / recentHistory.length
                : 0,
            data: recentHistory
        };
    }

    /**
     * Reset provider health data
     */
    resetProviderHealth(key) {
        const providerData = this.providers.get(key);
        if (providerData) {
            providerData.consecutiveFailures = 0;
            providerData.errors = [];
            providerData.latencies = [];
            providerData.status = 'unknown';
        }

        this.healthHistory.set(key, []);
    }

    /**
     * Get configuration
     */
    getConfiguration() {
        return {
            checkInterval: this.checkInterval,
            maxHistorySize: this.maxHistorySize,
            healthThresholds: this.healthThresholds,
            isRunning: this.isRunning,
            providerCount: this.providers.size
        };
    }

    /**
     * Update configuration
     */
    updateConfiguration(config) {
        if (config.checkInterval) {
            this.checkInterval = config.checkInterval;
            if (this.isRunning) {
                this.stop();
                this.start();
            }
        }

        if (config.maxHistorySize) {
            this.maxHistorySize = config.maxHistorySize;
        }

        if (config.healthThresholds) {
            this.healthThresholds = { ...this.healthThresholds, ...config.healthThresholds };
        }
    }
}

module.exports = HealthMonitor;