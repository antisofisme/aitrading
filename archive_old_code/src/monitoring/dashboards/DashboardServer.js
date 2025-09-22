const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const EventEmitter = require('events');

/**
 * Real-time Monitoring Dashboard Server
 * Provides web-based dashboards for visualizing system and trading metrics
 */
class DashboardServer extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            port: config.port || 3001,
            host: config.host || 'localhost',
            enableAuth: config.enableAuth || false,
            refreshInterval: config.refreshInterval || 5000,
            maxDataPoints: config.maxDataPoints || 1000,
            ...config
        };

        this.app = express();
        this.server = http.createServer(this.app);
        this.io = socketIo(this.server, {
            cors: {
                origin: "*",
                methods: ["GET", "POST"]
            }
        });

        this.connectedClients = new Set();
        this.dashboardData = new Map();
        this.isRunning = false;

        this.setupExpress();
        this.setupSocketIO();
        this.setupRoutes();
    }

    /**
     * Setup Express middleware
     */
    setupExpress() {
        this.app.use(express.json());
        this.app.use(express.static(path.join(__dirname, 'public')));

        // CORS middleware
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
            next();
        });

        // Basic authentication if enabled
        if (this.config.enableAuth) {
            this.app.use(this.basicAuth.bind(this));
        }
    }

    /**
     * Setup Socket.IO for real-time updates
     */
    setupSocketIO() {
        this.io.on('connection', (socket) => {
            console.log(`📱 Dashboard client connected: ${socket.id}`);
            this.connectedClients.add(socket.id);

            // Send initial data
            socket.emit('dashboard.initial', this.getInitialData());

            // Handle client requests
            socket.on('dashboard.subscribe', (dashboards) => {
                socket.join(dashboards);
            });

            socket.on('dashboard.unsubscribe', (dashboards) => {
                socket.leave(dashboards);
            });

            socket.on('dashboard.request', (request) => {
                this.handleDashboardRequest(socket, request);
            });

            socket.on('disconnect', () => {
                console.log(`📱 Dashboard client disconnected: ${socket.id}`);
                this.connectedClients.delete(socket.id);
            });
        });
    }

    /**
     * Setup API routes
     */
    setupRoutes() {
        // Main dashboard
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, 'public', 'index.html'));
        });

        // API endpoints
        this.app.get('/api/health', (req, res) => {
            res.json({ status: 'healthy', timestamp: new Date() });
        });

        this.app.get('/api/metrics/summary', (req, res) => {
            res.json(this.getMetricsSummary());
        });

        this.app.get('/api/alerts/active', (req, res) => {
            res.json(this.getActiveAlerts());
        });

        this.app.get('/api/trading/performance', (req, res) => {
            res.json(this.getTradingPerformance());
        });

        this.app.get('/api/system/status', (req, res) => {
            res.json(this.getSystemStatus());
        });

        // Historical data endpoints
        this.app.get('/api/metrics/:metric/history', (req, res) => {
            const { metric } = req.params;
            const { timeRange = '1h' } = req.query;
            res.json(this.getMetricHistory(metric, timeRange));
        });

        this.app.get('/api/alerts/history', (req, res) => {
            const { limit = 100 } = req.query;
            res.json(this.getAlertHistory(limit));
        });

        // Configuration endpoints
        this.app.get('/api/config/dashboards', (req, res) => {
            res.json(this.getDashboardConfigs());
        });

        this.app.post('/api/config/dashboards', (req, res) => {
            const config = req.body;
            this.updateDashboardConfig(config);
            res.json({ success: true });
        });

        // Export endpoints
        this.app.get('/api/export/metrics', (req, res) => {
            const { format = 'json' } = req.query;
            const data = this.exportMetrics(format);

            if (format === 'csv') {
                res.setHeader('Content-Type', 'text/csv');
                res.setHeader('Content-Disposition', 'attachment; filename=metrics.csv');
            }

            res.send(data);
        });
    }

    /**
     * Start dashboard server
     */
    start() {
        return new Promise((resolve, reject) => {
            if (this.isRunning) {
                resolve();
                return;
            }

            this.server.listen(this.config.port, this.config.host, (error) => {
                if (error) {
                    reject(error);
                    return;
                }

                this.isRunning = true;
                console.log(`🖥️ Dashboard server started on http://${this.config.host}:${this.config.port}`);
                this.emit('server.started');
                resolve();
            });
        });
    }

    /**
     * Stop dashboard server
     */
    stop() {
        return new Promise((resolve) => {
            if (!this.isRunning) {
                resolve();
                return;
            }

            this.server.close(() => {
                this.isRunning = false;
                console.log('🖥️ Dashboard server stopped');
                this.emit('server.stopped');
                resolve();
            });
        });
    }

    /**
     * Update dashboard with new data
     */
    updateDashboard(dashboardName, data) {
        this.dashboardData.set(dashboardName, {
            ...data,
            timestamp: new Date()
        });

        // Broadcast to connected clients
        this.io.to(dashboardName).emit('dashboard.update', {
            dashboard: dashboardName,
            data
        });
    }

    /**
     * Update metrics dashboard
     */
    updateMetrics(metrics) {
        this.updateDashboard('metrics', {
            type: 'metrics',
            metrics: this.formatMetricsForDashboard(metrics)
        });
    }

    /**
     * Update alerts dashboard
     */
    updateAlerts(alerts) {
        this.updateDashboard('alerts', {
            type: 'alerts',
            active: alerts.filter(a => a.status === 'active'),
            recent: alerts.slice(-10)
        });
    }

    /**
     * Update trading dashboard
     */
    updateTrading(tradingData) {
        this.updateDashboard('trading', {
            type: 'trading',
            performance: tradingData.performance,
            positions: tradingData.positions,
            pnl: tradingData.pnl,
            risk: tradingData.risk
        });
    }

    /**
     * Update system dashboard
     */
    updateSystem(systemData) {
        this.updateDashboard('system', {
            type: 'system',
            health: systemData.health,
            resources: systemData.resources,
            uptime: systemData.uptime
        });
    }

    /**
     * Handle dashboard request
     */
    handleDashboardRequest(socket, request) {
        switch (request.type) {
            case 'metrics.detail':
                socket.emit('metrics.detail', this.getMetricsDetail(request.metric));
                break;
            case 'alert.detail':
                socket.emit('alert.detail', this.getAlertDetail(request.alertId));
                break;
            case 'trading.positions':
                socket.emit('trading.positions', this.getTradingPositions());
                break;
            case 'system.logs':
                socket.emit('system.logs', this.getSystemLogs(request.lines));
                break;
            default:
                socket.emit('error', { message: 'Unknown request type' });
        }
    }

    /**
     * Format metrics for dashboard display
     */
    formatMetricsForDashboard(metrics) {
        const formatted = {
            timestamp: new Date(),
            counters: {},
            gauges: {},
            histograms: {}
        };

        // Format counters
        if (metrics.counters) {
            for (const [name, counter] of Object.entries(metrics.counters)) {
                formatted.counters[name] = {
                    value: counter.value,
                    rate: counter.rate || 0,
                    change: counter.change || 0
                };
            }
        }

        // Format gauges
        if (metrics.gauges) {
            for (const [name, gauge] of Object.entries(metrics.gauges)) {
                formatted.gauges[name] = {
                    value: gauge.value,
                    change: gauge.change || 0,
                    status: this.getMetricStatus(name, gauge.value)
                };
            }
        }

        // Format histograms
        if (metrics.histograms) {
            for (const [name, histogram] of Object.entries(metrics.histograms)) {
                formatted.histograms[name] = {
                    count: histogram.count,
                    mean: histogram.mean,
                    percentiles: histogram.percentiles || {}
                };
            }
        }

        return formatted;
    }

    /**
     * Get metric status (healthy/warning/critical)
     */
    getMetricStatus(metricName, value) {
        // This would typically use the same thresholds as the alert system
        const thresholds = {
            'system.cpu_usage': { warning: 70, critical: 85 },
            'system.memory_usage': { warning: 80, critical: 90 },
            'trading.drawdown': { warning: 5, critical: 10 }
        };

        const threshold = thresholds[metricName];
        if (!threshold) return 'healthy';

        if (value >= threshold.critical) return 'critical';
        if (value >= threshold.warning) return 'warning';
        return 'healthy';
    }

    /**
     * Basic authentication middleware
     */
    basicAuth(req, res, next) {
        const auth = req.headers.authorization;

        if (!auth || !auth.startsWith('Basic ')) {
            res.setHeader('WWW-Authenticate', 'Basic');
            res.status(401).send('Authentication required');
            return;
        }

        const credentials = Buffer.from(auth.slice(6), 'base64').toString().split(':');
        const [username, password] = credentials;

        if (username === this.config.auth.username && password === this.config.auth.password) {
            next();
        } else {
            res.status(401).send('Invalid credentials');
        }
    }

    /**
     * Get initial data for new connections
     */
    getInitialData() {
        const data = {};
        for (const [dashboard, content] of this.dashboardData) {
            data[dashboard] = content;
        }
        return data;
    }

    /**
     * Placeholder methods - these would be connected to actual monitoring systems
     */
    getMetricsSummary() {
        return {
            system: {
                cpu: 45.2,
                memory: 67.8,
                disk: 32.1
            },
            trading: {
                totalTrades: 1247,
                profitableTrades: 843,
                currentPnL: 15420.50
            },
            alerts: {
                active: 3,
                critical: 1,
                warning: 2
            }
        };
    }

    getActiveAlerts() {
        return [
            {
                id: 'alert_1',
                severity: 'critical',
                component: 'trading.risk',
                message: 'Risk exposure above threshold',
                timestamp: new Date()
            }
        ];
    }

    getTradingPerformance() {
        return {
            totalPnL: 15420.50,
            dayPnL: 1240.30,
            winRate: 67.6,
            sharpeRatio: 1.43,
            maxDrawdown: 8.2
        };
    }

    getSystemStatus() {
        return {
            uptime: 86400,
            cpu: 45.2,
            memory: 67.8,
            connections: this.connectedClients.size,
            status: 'healthy'
        };
    }

    getMetricHistory(metric, timeRange) {
        // Placeholder for historical data
        const points = [];
        const now = Date.now();
        const interval = 60000; // 1 minute

        for (let i = 60; i >= 0; i--) {
            points.push({
                timestamp: new Date(now - (i * interval)),
                value: Math.random() * 100
            });
        }

        return points;
    }

    getAlertHistory(limit) {
        // Placeholder for alert history
        return [];
    }

    getDashboardConfigs() {
        return {
            layouts: ['grid', 'list'],
            themes: ['light', 'dark'],
            refreshIntervals: [1000, 5000, 10000, 30000]
        };
    }

    updateDashboardConfig(config) {
        // Placeholder for config updates
        this.emit('config.updated', config);
    }

    exportMetrics(format) {
        const metrics = this.getMetricsSummary();

        if (format === 'csv') {
            // Convert to CSV format
            let csv = 'metric,value,timestamp\\n';
            for (const [category, values] of Object.entries(metrics)) {
                for (const [key, value] of Object.entries(values)) {
                    csv += `${category}.${key},${value},${new Date().toISOString()}\\n`;
                }
            }
            return csv;
        }

        return JSON.stringify(metrics, null, 2);
    }

    getMetricsDetail(metric) {
        // Placeholder for detailed metrics
        return { metric, details: 'Detailed information' };
    }

    getAlertDetail(alertId) {
        // Placeholder for alert details
        return { alertId, details: 'Alert details' };
    }

    getTradingPositions() {
        // Placeholder for trading positions
        return [];
    }

    getSystemLogs(lines = 100) {
        // Placeholder for system logs
        return [];
    }

    /**
     * Get server status
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            port: this.config.port,
            host: this.config.host,
            connectedClients: this.connectedClients.size,
            dashboards: Array.from(this.dashboardData.keys())
        };
    }
}

module.exports = DashboardServer;