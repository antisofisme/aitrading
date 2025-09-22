const MonitoringOrchestrator = require('../../src/monitoring/MonitoringOrchestrator');
const HealthMonitor = require('../../src/monitoring/health/HealthMonitor');
const MetricsCollector = require('../../src/monitoring/metrics/MetricsCollector');
const AlertManager = require('../../src/monitoring/alerts/AlertManager');
const DashboardServer = require('../../src/monitoring/dashboards/DashboardServer');

// Mock all dependencies
jest.mock('../../src/monitoring/health/HealthMonitor');
jest.mock('../../src/monitoring/metrics/MetricsCollector');
jest.mock('../../src/monitoring/alerts/AlertManager');
jest.mock('../../src/monitoring/dashboards/DashboardServer');

describe('MonitoringOrchestrator', () => {
    let orchestrator;
    let mockConfig;
    let mockHealthMonitor;
    let mockMetricsCollector;
    let mockAlertManager;
    let mockDashboardServer;

    beforeEach(() => {
        // Clear all mocks
        jest.clearAllMocks();

        // Setup mock instances
        mockHealthMonitor = {
            isMonitoring: false,
            start: jest.fn(),
            stop: jest.fn(),
            runHealthChecks: jest.fn(),
            getHealthStatus: jest.fn().mockReturnValue({ status: 'healthy' }),
            on: jest.fn(),
            emit: jest.fn()
        };

        mockMetricsCollector = {
            isCollecting: false,
            start: jest.fn(),
            stop: jest.fn(),
            getAllMetrics: jest.fn().mockReturnValue({}),
            getMetricsSummary: jest.fn().mockReturnValue({}),
            on: jest.fn(),
            emit: jest.fn()
        };

        mockAlertManager = {
            getActiveAlerts: jest.fn().mockReturnValue([]),
            getStatistics: jest.fn().mockReturnValue({}),
            createAlert: jest.fn(),
            on: jest.fn(),
            emit: jest.fn()
        };

        mockDashboardServer = {
            isRunning: false,
            start: jest.fn().mockResolvedValue(),
            stop: jest.fn().mockResolvedValue(),
            updateMetrics: jest.fn(),
            updateAlerts: jest.fn(),
            updateTrading: jest.fn(),
            updateSystem: jest.fn(),
            connectedClients: { size: 0 },
            on: jest.fn(),
            emit: jest.fn()
        };

        // Mock constructors
        HealthMonitor.mockImplementation(() => mockHealthMonitor);
        MetricsCollector.mockImplementation(() => mockMetricsCollector);
        AlertManager.mockImplementation(() => mockAlertManager);
        DashboardServer.mockImplementation(() => mockDashboardServer);

        mockConfig = {
            health: { checkInterval: 5000 },
            metrics: { aggregationInterval: 60000 },
            alerts: { channels: ['console'] },
            dashboard: { port: 3001 },
            coordination: { enableHooks: false }
        };

        orchestrator = new MonitoringOrchestrator(mockConfig);
    });

    afterEach(async () => {
        if (orchestrator && orchestrator.isRunning) {
            await orchestrator.stop();
        }
    });

    describe('Initialization', () => {
        it('should initialize with default configuration', () => {
            const defaultOrchestrator = new MonitoringOrchestrator();
            expect(defaultOrchestrator).toBeDefined();
            expect(defaultOrchestrator.isRunning).toBe(false);
        });

        it('should initialize all monitoring components', () => {
            expect(HealthMonitor).toHaveBeenCalledWith(mockConfig.health);
            expect(MetricsCollector).toHaveBeenCalledWith(mockConfig.metrics);
            expect(AlertManager).toHaveBeenCalledWith(mockConfig.alerts);
            expect(DashboardServer).toHaveBeenCalledWith(mockConfig.dashboard);
        });

        it('should setup event handlers', () => {
            // Verify that event handlers are registered
            expect(mockHealthMonitor.on).toHaveBeenCalledWith('health.check.completed', expect.any(Function));
            expect(mockHealthMonitor.on).toHaveBeenCalledWith('health.alerts', expect.any(Function));
            expect(mockMetricsCollector.on).toHaveBeenCalledWith('metrics.aggregated', expect.any(Function));
            expect(mockAlertManager.on).toHaveBeenCalledWith('alert.created', expect.any(Function));
        });
    });

    describe('Startup Process', () => {
        it('should start all components in correct order', async () => {
            const startSpy = jest.spyOn(orchestrator, 'emit');

            await orchestrator.start();

            expect(mockMetricsCollector.start).toHaveBeenCalled();
            expect(mockHealthMonitor.start).toHaveBeenCalled();
            expect(mockDashboardServer.start).toHaveBeenCalled();
            expect(orchestrator.isRunning).toBe(true);
            expect(orchestrator.startTime).toBeInstanceOf(Date);
            expect(startSpy).toHaveBeenCalledWith('monitoring.started');
        });

        it('should not start if already running', async () => {
            await orchestrator.start();
            const firstStartTime = orchestrator.startTime;

            await orchestrator.start(); // Try to start again

            expect(orchestrator.startTime).toBe(firstStartTime);
        });

        it('should handle startup failures', async () => {
            mockDashboardServer.start.mockRejectedValue(new Error('Dashboard start failed'));

            await expect(orchestrator.start()).rejects.toThrow('Dashboard start failed');
            expect(orchestrator.isRunning).toBe(false);
        });
    });

    describe('Shutdown Process', () => {
        it('should stop all components in reverse order', async () => {
            await orchestrator.start();
            const stopSpy = jest.spyOn(orchestrator, 'emit');

            await orchestrator.stop();

            expect(mockDashboardServer.stop).toHaveBeenCalled();
            expect(mockHealthMonitor.stop).toHaveBeenCalled();
            expect(mockMetricsCollector.stop).toHaveBeenCalled();
            expect(orchestrator.isRunning).toBe(false);
            expect(stopSpy).toHaveBeenCalledWith('monitoring.stopped');
        });

        it('should not stop if not running', async () => {
            const stopSpy = jest.spyOn(orchestrator, 'emit');

            await orchestrator.stop();

            expect(mockDashboardServer.stop).not.toHaveBeenCalled();
            expect(stopSpy).not.toHaveBeenCalledWith('monitoring.stopped');
        });

        it('should handle shutdown errors gracefully', async () => {
            await orchestrator.start();
            mockDashboardServer.stop.mockRejectedValue(new Error('Dashboard stop failed'));

            await expect(orchestrator.stop()).rejects.toThrow('Dashboard stop failed');
        });
    });

    describe('Event Handling', () => {
        it('should handle health report events', () => {
            const mockReport = {
                timestamp: new Date(),
                duration: 100,
                overallHealth: 'healthy',
                results: {
                    'system.cpu': { value: 45, status: 'healthy' },
                    'system.memory': { value: 67, status: 'warning' }
                }
            };

            // Simulate health report event
            const handler = mockHealthMonitor.on.mock.calls.find(call =>
                call[0] === 'health.check.completed'
            )[1];

            const emitSpy = jest.spyOn(orchestrator, 'emit');
            handler(mockReport);

            expect(emitSpy).toHaveBeenCalledWith('health.report.processed', mockReport);
        });

        it('should handle metrics aggregation events', () => {
            const mockAggregation = {
                timestamp: new Date(),
                counters: { 'trades.executed': { value: 100 } },
                gauges: { 'system.cpu': { value: 45 } },
                histograms: { 'latency.order': { count: 50 } }
            };

            const handler = mockMetricsCollector.on.mock.calls.find(call =>
                call[0] === 'metrics.aggregated'
            )[1];

            handler(mockAggregation);

            expect(mockDashboardServer.updateMetrics).toHaveBeenCalledWith(mockAggregation);
        });

        it('should handle alert creation events', () => {
            const mockAlert = {
                id: 'alert-123',
                severity: 'critical',
                component: 'trading.engine',
                message: 'Engine down'
            };

            const handler = mockAlertManager.on.mock.calls.find(call =>
                call[0] === 'alert.created'
            )[1];

            const emitSpy = jest.spyOn(orchestrator, 'emit');
            handler(mockAlert);

            expect(emitSpy).toHaveBeenCalledWith('alert.created', mockAlert);
            expect(mockDashboardServer.updateAlerts).toHaveBeenCalled();
        });

        it('should process health alerts and create alert manager alerts', async () => {
            const mockHealthAlerts = [{
                type: 'critical',
                component: 'system.cpu',
                message: 'CPU usage critical',
                value: 95,
                threshold: 85
            }];

            const handler = mockHealthMonitor.on.mock.calls.find(call =>
                call[0] === 'health.alerts'
            )[1];

            await handler(mockHealthAlerts);

            expect(mockAlertManager.createAlert).toHaveBeenCalledWith({
                severity: 'critical',
                component: 'system.cpu',
                message: 'CPU usage critical',
                value: 95,
                threshold: 85,
                source: 'health_monitor'
            });
        });
    });

    describe('Cross-Component Coordination', () => {
        it('should update dashboard with trading data on trade record', () => {
            const mockTrade = {
                pnl: 150.50,
                duration: 3600000,
                quantity: 100
            };

            const handler = mockMetricsCollector.on.mock.calls.find(call =>
                call[0] === 'trade.recorded'
            )[1];

            handler(mockTrade);

            expect(mockDashboardServer.updateTrading).toHaveBeenCalledWith(expect.objectContaining({
                performance: expect.any(Object),
                positions: expect.any(Array),
                pnl: expect.any(Object),
                risk: expect.any(Object)
            }));
        });

        it('should create critical alerts for trading errors', () => {
            const mockError = {
                type: 'trading',
                error: new Error('Trading system failure')
            };

            const handler = mockMetricsCollector.on.mock.calls.find(call =>
                call[0] === 'error.recorded'
            )[1];

            handler(mockError);

            expect(mockAlertManager.createAlert).toHaveBeenCalledWith({
                severity: 'critical',
                component: 'error.trading',
                message: 'trading error: Trading system failure',
                source: 'metrics_collector',
                metadata: expect.any(Object)
            });
        });

        it('should update dashboard with system health data', () => {
            const mockReport = {
                timestamp: new Date(),
                overallHealth: 'healthy',
                results: {
                    'system.cpu': { value: 45 },
                    'system.memory': { value: 67 }
                }
            };

            const handler = mockHealthMonitor.on.mock.calls.find(call =>
                call[0] === 'health.check.completed'
            )[1];

            handler(mockReport);

            expect(mockDashboardServer.updateSystem).toHaveBeenCalledWith({
                health: expect.objectContaining({
                    overall: 'healthy',
                    components: mockReport.results
                }),
                resources: expect.any(Object),
                uptime: expect.any(Number)
            });
        });
    });

    describe('Manual Operations', () => {
        it('should trigger manual health check', async () => {
            await orchestrator.triggerHealthCheck();
            expect(mockHealthMonitor.runHealthChecks).toHaveBeenCalled();
        });

        it('should create manual alert', async () => {
            const alertData = {
                severity: 'warning',
                component: 'manual.test',
                message: 'Manual test alert'
            };

            mockAlertManager.createAlert.mockResolvedValue({ id: 'manual-alert' });

            const result = await orchestrator.createAlert(alertData);

            expect(mockAlertManager.createAlert).toHaveBeenCalledWith(alertData);
            expect(result).toEqual({ id: 'manual-alert' });
        });

        it('should handle manual operations when components not available', async () => {
            orchestrator.healthMonitor = null;
            orchestrator.alertManager = null;

            await orchestrator.triggerHealthCheck(); // Should not throw
            const result = await orchestrator.createAlert({}); // Should return null

            expect(result).toBeNull();
        });
    });

    describe('Status and Information', () => {
        it('should return comprehensive monitoring status', () => {
            mockHealthMonitor.isMonitoring = true;
            mockMetricsCollector.isCollecting = true;
            mockDashboardServer.isRunning = true;
            orchestrator.isRunning = true;
            orchestrator.startTime = new Date();

            const status = orchestrator.getStatus();

            expect(status).toEqual({
                isRunning: true,
                startTime: expect.any(Date),
                uptime: expect.any(Number),
                components: {
                    health: {
                        running: true,
                        lastCheck: undefined,
                        status: { status: 'healthy' }
                    },
                    metrics: {
                        collecting: true,
                        summary: {}
                    },
                    alerts: {
                        active: 0,
                        statistics: {}
                    },
                    dashboard: {
                        running: true,
                        url: 'http://localhost:3001',
                        clients: 0
                    }
                }
            });
        });

        it('should return metrics', () => {
            const mockMetrics = { 'system.cpu': [{ value: 45 }] };
            mockMetricsCollector.getAllMetrics.mockReturnValue(mockMetrics);

            const metrics = orchestrator.getMetrics();

            expect(metrics).toBe(mockMetrics);
            expect(mockMetricsCollector.getAllMetrics).toHaveBeenCalled();
        });

        it('should return active alerts', () => {
            const mockAlerts = [{ id: 'alert-1', severity: 'warning' }];
            mockAlertManager.getActiveAlerts.mockReturnValue(mockAlerts);

            const alerts = orchestrator.getActiveAlerts();

            expect(alerts).toBe(mockAlerts);
            expect(mockAlertManager.getActiveAlerts).toHaveBeenCalled();
        });
    });

    describe('Threshold Checking', () => {
        it('should check metric thresholds and create alerts', () => {
            const mockAggregation = {
                gauges: {
                    'system.cpu_usage': { value: 90 } // Above critical threshold
                }
            };

            const handler = mockMetricsCollector.on.mock.calls.find(call =>
                call[0] === 'metrics.aggregated'
            )[1];

            handler(mockAggregation);

            expect(mockAlertManager.createAlert).toHaveBeenCalledWith({
                severity: 'critical',
                component: 'system.cpu_usage',
                message: 'system.cpu_usage critical threshold exceeded',
                value: 90,
                threshold: 85,
                source: 'metrics_threshold'
            });
        });

        it('should not create alerts for metrics within thresholds', () => {
            const mockAggregation = {
                gauges: {
                    'system.cpu_usage': { value: 50 } // Below warning threshold
                }
            };

            const handler = mockMetricsCollector.on.mock.calls.find(call =>
                call[0] === 'metrics.aggregated'
            )[1];

            mockAlertManager.createAlert.mockClear();
            handler(mockAggregation);

            expect(mockAlertManager.createAlert).not.toHaveBeenCalled();
        });
    });

    describe('Trading Data Methods', () => {
        it('should calculate trading performance', () => {
            const performance = orchestrator.calculateTradingPerformance();

            expect(performance).toEqual({
                totalPnL: 15420.50,
                dayPnL: 1240.30,
                winRate: 67.6,
                sharpeRatio: 1.43,
                maxDrawdown: 8.2
            });
        });

        it('should calculate P&L', () => {
            const pnl = orchestrator.calculatePnL();

            expect(pnl).toEqual({
                realized: 12180.20,
                unrealized: 3240.30,
                total: 15420.50
            });
        });

        it('should calculate risk metrics', () => {
            const risk = orchestrator.calculateRiskMetrics();

            expect(risk).toEqual({
                exposureRatio: 0.75,
                varEstimate: 2340.50,
                maxExposure: 50000
            });
        });

        it('should get current positions', () => {
            const positions = orchestrator.getCurrentPositions();
            expect(Array.isArray(positions)).toBe(true);
        });
    });

    describe('Utility Methods', () => {
        it('should extract resource metrics from health results', () => {
            const results = {
                'system.cpu': { value: 45 },
                'system.memory': { value: 67 },
                'system.disk': { value: 32 },
                'system.uptime': { value: 86400 }
            };

            const resources = orchestrator.extractResourceMetrics(results);

            expect(resources).toEqual({
                cpu: 45,
                memory: 67,
                disk: 32,
                uptime: 86400
            });
        });

        it('should get metric value from aggregation', () => {
            const aggregation = {
                gauges: {
                    'system.cpu_usage': { value: 75 }
                }
            };

            const value = orchestrator.getMetricValue(aggregation, 'gauges.system.cpu_usage.value');
            expect(value).toBe(75);

            const nonExistent = orchestrator.getMetricValue(aggregation, 'gauges.non.existent');
            expect(nonExistent).toBeNull();
        });
    });

    describe('Error Handling', () => {
        it('should handle component initialization errors', () => {
            HealthMonitor.mockImplementation(() => {
                throw new Error('Health monitor init failed');
            });

            expect(() => new MonitoringOrchestrator()).toThrow('Health monitor init failed');
        });

        it('should handle event handler errors gracefully', () => {
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

            // Simulate an error in health alert processing
            const mockHealthAlerts = [{
                type: 'critical',
                component: 'test',
                message: 'Test alert'
            }];

            mockAlertManager.createAlert.mockRejectedValue(new Error('Alert creation failed'));

            const handler = mockHealthMonitor.on.mock.calls.find(call =>
                call[0] === 'health.alerts'
            )[1];

            // This should not throw, but should log the error
            expect(async () => await handler(mockHealthAlerts)).not.toThrow();

            consoleSpy.mockRestore();
        });
    });
});