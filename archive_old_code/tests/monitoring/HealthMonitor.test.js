const HealthMonitor = require('../../src/monitoring/health/HealthMonitor');
const EventEmitter = require('events');

describe('HealthMonitor', () => {
    let healthMonitor;
    let mockConfig;

    beforeEach(() => {
        mockConfig = {
            checkInterval: 1000,
            thresholds: {
                cpu: { warning: 70, critical: 85 },
                memory: { warning: 80, critical: 90 },
                disk: { warning: 85, critical: 95 },
                latency: { warning: 100, critical: 500 },
                errorRate: { warning: 5, critical: 10 }
            },
            retentionPeriod: 3600000
        };

        healthMonitor = new HealthMonitor(mockConfig);
    });

    afterEach(async () => {
        if (healthMonitor && healthMonitor.isMonitoring) {
            healthMonitor.stop();
        }
    });

    describe('Initialization', () => {
        it('should initialize with default configuration', () => {
            const monitor = new HealthMonitor();
            expect(monitor).toBeDefined();
            expect(monitor.isMonitoring).toBe(false);
            expect(monitor.healthChecks.size).toBeGreaterThan(0);
        });

        it('should initialize with custom configuration', () => {
            expect(healthMonitor.config.checkInterval).toBe(1000);
            expect(healthMonitor.config.thresholds.cpu.warning).toBe(70);
        });

        it('should register default health checks', () => {
            expect(healthMonitor.healthChecks.has('system.cpu')).toBe(true);
            expect(healthMonitor.healthChecks.has('system.memory')).toBe(true);
            expect(healthMonitor.healthChecks.has('app.database')).toBe(true);
            expect(healthMonitor.healthChecks.has('performance.latency')).toBe(true);
        });
    });

    describe('Health Check Registration', () => {
        it('should register custom health check', () => {
            const customCheck = jest.fn().mockResolvedValue({
                status: 'healthy',
                value: 50,
                timestamp: new Date()
            });

            healthMonitor.registerHealthCheck('custom.test', customCheck);
            expect(healthMonitor.healthChecks.has('custom.test')).toBe(true);
        });

        it('should enable/disable health checks', () => {
            healthMonitor.healthChecks.get('system.cpu').enabled = false;
            expect(healthMonitor.healthChecks.get('system.cpu').enabled).toBe(false);
        });
    });

    describe('Health Check Execution', () => {
        it('should run health checks and generate report', async () => {
            const reportPromise = new Promise((resolve) => {
                healthMonitor.once('health.check.completed', resolve);
            });

            await healthMonitor.runHealthChecks();
            const report = await reportPromise;

            expect(report).toBeDefined();
            expect(report.timestamp).toBeInstanceOf(Date);
            expect(report.overallHealth).toBeDefined();
            expect(report.results).toBeDefined();
            expect(typeof report.duration).toBe('number');
        });

        it('should handle health check failures gracefully', async () => {
            const failingCheck = jest.fn().mockRejectedValue(new Error('Check failed'));
            healthMonitor.registerHealthCheck('failing.test', failingCheck);

            const reportPromise = new Promise((resolve) => {
                healthMonitor.once('health.check.completed', resolve);
            });

            await healthMonitor.runHealthChecks();
            const report = await reportPromise;

            expect(report.results['failing.test']).toBeDefined();
            expect(report.results['failing.test'].status).toBe('error');
        });

        it('should calculate overall health correctly', async () => {
            // Mock checks to return specific statuses
            const healthyCheck = jest.fn().mockResolvedValue({ status: 'healthy' });
            const warningCheck = jest.fn().mockResolvedValue({ status: 'warning' });
            const criticalCheck = jest.fn().mockResolvedValue({ status: 'critical' });

            healthMonitor.registerHealthCheck('test.healthy', healthyCheck);
            healthMonitor.registerHealthCheck('test.warning', warningCheck);

            let report = await healthMonitor.runHealthChecks();
            expect(['healthy', 'warning']).toContain(report.overallHealth);

            healthMonitor.registerHealthCheck('test.critical', criticalCheck);
            report = await healthMonitor.runHealthChecks();
            expect(report.overallHealth).toBe('critical');
        });
    });

    describe('Alert Generation', () => {
        it('should generate alerts for threshold violations', async () => {
            const alertsPromise = new Promise((resolve) => {
                healthMonitor.once('health.alerts', resolve);
            });

            // Mock a check that returns critical status
            const criticalCheck = jest.fn().mockResolvedValue({
                status: 'critical',
                value: 95,
                unit: '%',
                timestamp: new Date()
            });

            healthMonitor.registerHealthCheck('test.critical', criticalCheck);
            await healthMonitor.runHealthChecks();

            const alerts = await alertsPromise;
            expect(Array.isArray(alerts)).toBe(true);
            expect(alerts.length).toBeGreaterThan(0);
        });

        it('should not generate alerts for healthy checks', async () => {
            let alertsEmitted = false;
            healthMonitor.once('health.alerts', () => {
                alertsEmitted = true;
            });

            const healthyCheck = jest.fn().mockResolvedValue({
                status: 'healthy',
                value: 30,
                timestamp: new Date()
            });

            healthMonitor.registerHealthCheck('test.healthy', healthyCheck);
            await healthMonitor.runHealthChecks();

            // Wait a bit to ensure no alerts are emitted
            await new Promise(resolve => setTimeout(resolve, 100));
            expect(alertsEmitted).toBe(false);
        });
    });

    describe('Monitoring Lifecycle', () => {
        it('should start monitoring', () => {
            const startSpy = jest.spyOn(healthMonitor, 'emit');
            healthMonitor.start();

            expect(healthMonitor.isMonitoring).toBe(true);
            expect(healthMonitor.monitoringInterval).toBeDefined();
            expect(startSpy).toHaveBeenCalledWith('monitoring.started');
        });

        it('should stop monitoring', () => {
            healthMonitor.start();
            const stopSpy = jest.spyOn(healthMonitor, 'emit');

            healthMonitor.stop();

            expect(healthMonitor.isMonitoring).toBe(false);
            expect(healthMonitor.monitoringInterval).toBeUndefined();
            expect(stopSpy).toHaveBeenCalledWith('monitoring.stopped');
        });

        it('should not start monitoring if already running', () => {
            healthMonitor.start();
            const initialInterval = healthMonitor.monitoringInterval;

            healthMonitor.start(); // Try to start again

            expect(healthMonitor.monitoringInterval).toBe(initialInterval);
        });
    });

    describe('Metrics Storage', () => {
        it('should store health check results', async () => {
            await healthMonitor.runHealthChecks();

            const metrics = healthMonitor.getAllMetrics();
            expect(Object.keys(metrics).length).toBeGreaterThan(0);
        });

        it('should clean up old metrics', async () => {
            // Set very short retention period
            healthMonitor.config.retentionPeriod = 100;

            await healthMonitor.runHealthChecks();

            // Wait for retention period to pass
            await new Promise(resolve => setTimeout(resolve, 150));

            healthMonitor.cleanupHistory();

            // Should have minimal or no old data
            expect(healthMonitor.checkHistory.length).toBe(0);
        });

        it('should retrieve metrics for specific component', async () => {
            await healthMonitor.runHealthChecks();

            const cpuMetrics = healthMonitor.getMetrics('system.cpu');
            expect(Array.isArray(cpuMetrics)).toBe(true);
        });
    });

    describe('System Health Checks', () => {
        it('should check CPU usage', async () => {
            const result = await healthMonitor.checkCpuUsage();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('%');
            expect(result.timestamp).toBeInstanceOf(Date);
        });

        it('should check memory usage', async () => {
            const result = await healthMonitor.checkMemoryUsage();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('%');
            expect(typeof result.used).toBe('number');
            expect(typeof result.total).toBe('number');
        });

        it('should check uptime', async () => {
            const result = await healthMonitor.checkUptime();

            expect(result).toBeDefined();
            expect(result.status).toBe('healthy');
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('seconds');
        });
    });

    describe('Application Health Checks', () => {
        it('should check database connection', async () => {
            const result = await healthMonitor.checkDatabaseConnection();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(result.timestamp).toBeInstanceOf(Date);
        });

        it('should check trading engine', async () => {
            const result = await healthMonitor.checkTradingEngine();

            expect(result).toBeDefined();
            expect(result.status).toBe('healthy');
            expect(typeof result.activeOrders).toBe('number');
        });

        it('should check market data feed', async () => {
            const result = await healthMonitor.checkMarketDataFeed();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(typeof result.latency).toBe('number');
        });
    });

    describe('Performance Health Checks', () => {
        it('should check latency', async () => {
            const result = await healthMonitor.checkLatency();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('ms');
        });

        it('should check throughput', async () => {
            const result = await healthMonitor.checkThroughput();

            expect(result).toBeDefined();
            expect(result.status).toBe('healthy');
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('requests/sec');
        });

        it('should check error rate', async () => {
            const result = await healthMonitor.checkErrorRate();

            expect(result).toBeDefined();
            expect(result.status).toBeDefined();
            expect(typeof result.value).toBe('number');
            expect(result.unit).toBe('%');
        });
    });

    describe('Status and Information', () => {
        it('should return current health status', () => {
            const status = healthMonitor.getHealthStatus();

            expect(status).toBeDefined();
            expect(typeof status.isMonitoring).toBe('boolean');
            expect(typeof status.checkCount).toBe('number');
            expect(Array.isArray(status.registeredChecks)).toBe(true);
        });

        it('should return metrics for time range', async () => {
            await healthMonitor.runHealthChecks();

            const timeRange = 3600000; // 1 hour
            const metrics = healthMonitor.getMetrics('system.cpu', timeRange);

            expect(Array.isArray(metrics)).toBe(true);
        });
    });
});