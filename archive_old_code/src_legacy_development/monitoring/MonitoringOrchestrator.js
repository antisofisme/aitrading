const EventEmitter = require('events');
const HealthMonitor = require('./health/HealthMonitor');
const MetricsCollector = require('./metrics/MetricsCollector');
const AlertManager = require('./alerts/AlertManager');
const DashboardServer = require('./dashboards/DashboardServer');

/**
 * Central Monitoring Orchestrator
 * Coordinates all monitoring components and manages their interactions
 */
class MonitoringOrchestrator extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            health: config.health || {},
            metrics: config.metrics || {},
            alerts: config.alerts || {},
            dashboard: config.dashboard || {},
            coordination: config.coordination || {
                enableHooks: true,
                memoryNamespace: 'aitrading-monitoring'
            },
            ...config
        };

        this.healthMonitor = null;
        this.metricsCollector = null;
        this.alertManager = null;
        this.dashboardServer = null;

        this.isRunning = false;
        this.startTime = null;

        this.initializeComponents();
        this.setupEventHandlers();
    }

    /**
     * Initialize all monitoring components
     */
    initializeComponents() {
        console.log('🔧 Initializing monitoring components...');

        // Initialize health monitor
        this.healthMonitor = new HealthMonitor(this.config.health);

        // Initialize metrics collector
        this.metricsCollector = new MetricsCollector(this.config.metrics);

        // Initialize alert manager
        this.alertManager = new AlertManager(this.config.alerts);

        // Initialize dashboard server
        this.dashboardServer = new DashboardServer(this.config.dashboard);

        console.log('✅ All monitoring components initialized');
    }

    /**
     * Setup event handlers between components
     */
    setupEventHandlers() {
        console.log('🔗 Setting up component event handlers...');

        // Health Monitor Events
        this.healthMonitor.on('health.check.completed', (report) => {
            this.handleHealthReport(report);
        });

        this.healthMonitor.on('health.alerts', (alerts) => {
            this.processHealthAlerts(alerts);
        });

        // Metrics Collector Events
        this.metricsCollector.on('metrics.aggregated', (aggregation) => {
            this.handleMetricsAggregation(aggregation);
        });

        this.metricsCollector.on('metric.updated', (metric) => {
            this.handleMetricUpdate(metric);
        });

        this.metricsCollector.on('trade.recorded', (trade) => {
            this.handleTradeRecord(trade);
        });

        this.metricsCollector.on('error.recorded', (error) => {
            this.handleErrorRecord(error);
        });

        // Alert Manager Events
        this.alertManager.on('alert.created', (alert) => {
            this.handleAlertCreated(alert);
        });

        this.alertManager.on('alert.escalated', (alert) => {
            this.handleAlertEscalated(alert);
        });

        this.alertManager.on('notification.sent', (notification) => {
            this.handleNotificationSent(notification);
        });

        // Dashboard Server Events
        this.dashboardServer.on('server.started', () => {
            console.log('📊 Dashboard server is running');
        });

        // Cross-component coordination
        this.setupCrossComponentEvents();

        console.log('✅ Event handlers configured');
    }

    /**
     * Setup cross-component event coordination
     */
    setupCrossComponentEvents() {
        // Health monitor triggers alerts
        this.healthMonitor.on('health.alerts', async (alerts) => {
            for (const alert of alerts) {
                await this.alertManager.createAlert({
                    severity: alert.type,
                    component: alert.component,
                    message: alert.message,
                    value: alert.value,
                    threshold: alert.threshold,
                    source: 'health_monitor'
                });
            }
        });

        // Metrics collector updates dashboard
        this.metricsCollector.on('metrics.aggregated', (aggregation) => {
            this.dashboardServer.updateMetrics(aggregation);
        });

        // Alert manager updates dashboard
        this.alertManager.on('alert.created', (alert) => {
            const activeAlerts = this.alertManager.getActiveAlerts();
            this.dashboardServer.updateAlerts(activeAlerts);
        });

        this.alertManager.on('alert.resolved', () => {
            const activeAlerts = this.alertManager.getActiveAlerts();
            this.dashboardServer.updateAlerts(activeAlerts);
        });

        // Health monitor updates dashboard
        this.healthMonitor.on('health.check.completed', (report) => {
            this.dashboardServer.updateSystem({
                health: {
                    overall: report.overallHealth,
                    components: report.results,
                    timestamp: report.timestamp
                },
                resources: this.extractResourceMetrics(report.results),
                uptime: process.uptime()
            });
        });
    }

    /**
     * Start all monitoring components
     */
    async start() {
        if (this.isRunning) {
            console.log('⚠️ Monitoring system already running');
            return;
        }

        console.log('🚀 Starting comprehensive monitoring system...');
        this.startTime = new Date();

        try {
            // Execute coordination hooks
            if (this.config.coordination.enableHooks) {
                await this.executePreStartHooks();
            }

            // Start components in order
            console.log('📊 Starting metrics collector...');
            this.metricsCollector.start();

            console.log('🏥 Starting health monitor...');
            this.healthMonitor.start();

            console.log('🚨 Starting alert manager...');
            // Alert manager doesn't need explicit start

            console.log('🖥️ Starting dashboard server...');
            await this.dashboardServer.start();

            this.isRunning = true;

            // Store configuration in memory for coordination
            if (this.config.coordination.enableHooks) {
                await this.storeConfigurationInMemory();
            }

            console.log('✅ Monitoring system fully operational');
            console.log(`📊 Dashboard: http://${this.config.dashboard.host || 'localhost'}:${this.config.dashboard.port || 3001}`);

            this.emit('monitoring.started');

            // Execute post-start hooks
            if (this.config.coordination.enableHooks) {
                await this.executePostStartHooks();
            }

        } catch (error) {
            console.error('❌ Failed to start monitoring system:', error);
            await this.stop();
            throw error;
        }
    }

    /**
     * Stop all monitoring components
     */
    async stop() {
        if (!this.isRunning) {
            console.log('⚠️ Monitoring system not running');
            return;
        }

        console.log('🛑 Stopping monitoring system...');

        try {
            // Execute pre-stop hooks
            if (this.config.coordination.enableHooks) {
                await this.executePreStopHooks();
            }

            // Stop components in reverse order
            if (this.dashboardServer) {
                await this.dashboardServer.stop();
            }

            if (this.healthMonitor) {
                this.healthMonitor.stop();
            }

            if (this.metricsCollector) {
                this.metricsCollector.stop();
            }

            this.isRunning = false;
            console.log('✅ Monitoring system stopped');

            this.emit('monitoring.stopped');

            // Execute post-stop hooks
            if (this.config.coordination.enableHooks) {
                await this.executePostStopHooks();
            }

        } catch (error) {
            console.error('❌ Error stopping monitoring system:', error);
            throw error;
        }
    }

    /**
     * Handle health report
     */
    handleHealthReport(report) {
        // Update metrics based on health status
        for (const [component, result] of Object.entries(report.results)) {
            if (result.value !== undefined) {
                const metricName = `health.${component.replace(/\./g, '_')}`;
                this.metricsCollector.setGauge(metricName, result.value);
            }
        }

        // Record health check duration
        this.metricsCollector.observeHistogram('health.check_duration', report.duration);

        this.emit('health.report.processed', report);
    }

    /**
     * Process health alerts
     */
    async processHealthAlerts(alerts) {
        for (const alert of alerts) {
            try {
                await this.alertManager.createAlert({
                    severity: alert.type,
                    component: alert.component,
                    message: alert.message,
                    value: alert.value,
                    threshold: alert.threshold,
                    source: 'health_monitor',
                    metadata: {
                        healthCheck: true,
                        timestamp: alert.timestamp
                    }
                });
            } catch (error) {
                console.error('❌ Failed to create health alert:', error);
            }
        }
    }

    /**
     * Handle metrics aggregation
     */
    handleMetricsAggregation(aggregation) {
        // Store aggregated metrics for dashboard
        this.emit('metrics.aggregated', aggregation);

        // Check for metric-based alerts
        this.checkMetricThresholds(aggregation);
    }

    /**
     * Handle metric update
     */
    handleMetricUpdate(metric) {
        // Real-time metric processing
        this.emit('metric.updated', metric);

        // Store in coordination memory if needed
        if (this.config.coordination.enableHooks) {
            this.storeMetricInMemory(metric);
        }
    }

    /**
     * Handle trade record
     */
    handleTradeRecord(trade) {
        // Update dashboard with trading data
        this.dashboardServer.updateTrading({
            performance: this.calculateTradingPerformance(),
            positions: this.getCurrentPositions(),
            pnl: this.calculatePnL(),
            risk: this.calculateRiskMetrics()
        });

        this.emit('trade.recorded', trade);
    }

    /**
     * Handle error record
     */
    handleErrorRecord(errorRecord) {
        // Create alert for errors based on severity
        if (errorRecord.type === 'trading' || errorRecord.type === 'risk') {
            this.alertManager.createAlert({
                severity: 'critical',
                component: `error.${errorRecord.type}`,
                message: `${errorRecord.type} error: ${errorRecord.error.message}`,
                source: 'metrics_collector',
                metadata: {
                    errorType: errorRecord.error.name,
                    stack: errorRecord.error.stack
                }
            });
        }

        this.emit('error.recorded', errorRecord);
    }

    /**
     * Handle alert created
     */
    handleAlertCreated(alert) {
        console.log(`🚨 Alert created: [${alert.severity.toUpperCase()}] ${alert.component} - ${alert.message}`);

        // Record alert metrics
        this.metricsCollector.incrementCounter(`alerts.${alert.severity}`);
        this.metricsCollector.incrementCounter('alerts.total');

        this.emit('alert.created', alert);
    }

    /**
     * Handle alert escalated
     */
    handleAlertEscalated(alert) {
        console.log(`⬆️ Alert escalated: [LEVEL ${alert.escalationLevel}] ${alert.component}`);

        // Record escalation metrics
        this.metricsCollector.incrementCounter('alerts.escalated');

        this.emit('alert.escalated', alert);
    }

    /**
     * Handle notification sent
     */
    handleNotificationSent(notification) {
        // Record notification metrics
        this.metricsCollector.incrementCounter(`notifications.${notification.channel}.sent`);

        this.emit('notification.sent', notification);
    }

    /**
     * Check metric thresholds for alerting
     */
    checkMetricThresholds(aggregation) {
        const thresholds = {
            'system.cpu_usage': { warning: 70, critical: 85 },
            'system.memory_usage': { warning: 80, critical: 90 },
            'trading.drawdown': { warning: 5, critical: 10 },
            'trading.risk_ratio': { warning: 2, critical: 3 }
        };

        for (const [metric, threshold] of Object.entries(thresholds)) {
            const value = this.getMetricValue(aggregation, metric);
            if (value === null) continue;

            if (value >= threshold.critical) {
                this.alertManager.createAlert({
                    severity: 'critical',
                    component: metric,
                    message: `${metric} critical threshold exceeded`,
                    value,
                    threshold: threshold.critical,
                    source: 'metrics_threshold'
                });
            } else if (value >= threshold.warning) {
                this.alertManager.createAlert({
                    severity: 'warning',
                    component: metric,
                    message: `${metric} warning threshold exceeded`,
                    value,
                    threshold: threshold.warning,
                    source: 'metrics_threshold'
                });
            }
        }
    }

    /**
     * Get metric value from aggregation
     */
    getMetricValue(aggregation, metricName) {
        // Navigate through aggregation structure to find metric
        const parts = metricName.split('.');
        let current = aggregation;

        for (const part of parts) {
            if (current && current[part] !== undefined) {
                current = current[part];
            } else {
                return null;
            }
        }

        return typeof current === 'object' && current.value !== undefined ? current.value : current;
    }

    /**
     * Extract resource metrics from health results
     */
    extractResourceMetrics(results) {
        return {
            cpu: results['system.cpu']?.value || 0,
            memory: results['system.memory']?.value || 0,
            disk: results['system.disk']?.value || 0,
            uptime: results['system.uptime']?.value || 0
        };
    }

    /**
     * Coordination hooks
     */
    async executePreStartHooks() {
        console.log('🪝 Executing pre-start coordination hooks...');
        // Store monitoring start event in memory for coordination
        await this.storeEventInMemory('monitoring.starting', {
            timestamp: new Date(),
            config: this.config
        });
    }

    async executePostStartHooks() {
        console.log('🪝 Executing post-start coordination hooks...');
        // Notify other systems that monitoring is ready
        await this.storeEventInMemory('monitoring.started', {
            timestamp: new Date(),
            components: {
                health: this.healthMonitor.isMonitoring,
                metrics: this.metricsCollector.isCollecting,
                dashboard: this.dashboardServer.isRunning
            }
        });
    }

    async executePreStopHooks() {
        console.log('🪝 Executing pre-stop coordination hooks...');
        await this.storeEventInMemory('monitoring.stopping', {
            timestamp: new Date(),
            uptime: Date.now() - this.startTime?.getTime()
        });
    }

    async executePostStopHooks() {
        console.log('🪝 Executing post-stop coordination hooks...');
        await this.storeEventInMemory('monitoring.stopped', {
            timestamp: new Date()
        });
    }

    /**
     * Store configuration in memory for coordination
     */
    async storeConfigurationInMemory() {
        const configData = {
            thresholds: this.config.health.thresholds,
            alertChannels: this.config.alerts.channels,
            dashboardPort: this.config.dashboard.port,
            metricsRetention: this.config.metrics.retentionPeriod,
            timestamp: new Date()
        };

        await this.storeInMemory('monitoring/config', configData);
    }

    /**
     * Store metric in memory for coordination
     */
    async storeMetricInMemory(metric) {
        const key = `monitoring/metrics/${metric.name}`;
        await this.storeInMemory(key, {
            type: metric.type,
            value: metric.value,
            timestamp: new Date()
        });
    }

    /**
     * Store event in memory for coordination
     */
    async storeEventInMemory(eventType, data) {
        const key = `monitoring/events/${eventType}`;
        await this.storeInMemory(key, data);
    }

    /**
     * Generic memory storage helper
     */
    async storeInMemory(key, data) {
        try {
            // This would integrate with the claude-flow memory system
            // For now, just log the coordination action
            console.log(`💾 Storing coordination data: ${key}`);
        } catch (error) {
            console.warn('⚠️ Failed to store coordination data:', error.message);
        }
    }

    /**
     * Placeholder methods for trading data (would be connected to actual trading system)
     */
    calculateTradingPerformance() {
        return {
            totalPnL: 15420.50,
            dayPnL: 1240.30,
            winRate: 67.6,
            sharpeRatio: 1.43,
            maxDrawdown: 8.2
        };
    }

    getCurrentPositions() {
        return []; // Placeholder
    }

    calculatePnL() {
        return {
            realized: 12180.20,
            unrealized: 3240.30,
            total: 15420.50
        };
    }

    calculateRiskMetrics() {
        return {
            exposureRatio: 0.75,
            varEstimate: 2340.50,
            maxExposure: 50000
        };
    }

    /**
     * Get comprehensive monitoring status
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            startTime: this.startTime,
            uptime: this.startTime ? Date.now() - this.startTime.getTime() : 0,
            components: {
                health: {
                    running: this.healthMonitor?.isMonitoring || false,
                    lastCheck: this.healthMonitor?.lastCheck?.timestamp,
                    status: this.healthMonitor?.getHealthStatus()
                },
                metrics: {
                    collecting: this.metricsCollector?.isCollecting || false,
                    summary: this.metricsCollector?.getMetricsSummary()
                },
                alerts: {
                    active: this.alertManager?.getActiveAlerts()?.length || 0,
                    statistics: this.alertManager?.getStatistics()
                },
                dashboard: {
                    running: this.dashboardServer?.isRunning || false,
                    url: this.dashboardServer ?
                        `http://${this.config.dashboard.host || 'localhost'}:${this.config.dashboard.port || 3001}` :
                        null,
                    clients: this.dashboardServer?.connectedClients?.size || 0
                }
            }
        };
    }

    /**
     * Get monitoring metrics
     */
    getMetrics() {
        return this.metricsCollector?.getAllMetrics() || {};
    }

    /**
     * Get active alerts
     */
    getActiveAlerts() {
        return this.alertManager?.getActiveAlerts() || [];
    }

    /**
     * Manual health check trigger
     */
    async triggerHealthCheck() {
        if (this.healthMonitor) {
            await this.healthMonitor.runHealthChecks();
        }
    }

    /**
     * Create manual alert
     */
    async createAlert(alertData) {
        if (this.alertManager) {
            return await this.alertManager.createAlert(alertData);
        }
        return null;
    }
}

module.exports = MonitoringOrchestrator;