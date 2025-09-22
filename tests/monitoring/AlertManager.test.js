const AlertManager = require('../../src/monitoring/alerts/AlertManager');

// Mock external dependencies
jest.mock('nodemailer');
jest.mock('axios');

const nodemailer = require('nodemailer');
const axios = require('axios');

describe('AlertManager', () => {
    let alertManager;
    let mockConfig;
    let mockTransporter;

    beforeEach(() => {
        // Mock nodemailer
        mockTransporter = {
            sendMail: jest.fn().mockResolvedValue({ messageId: 'test-message-id' })
        };
        nodemailer.createTransporter = jest.fn().mockReturnValue(mockTransporter);

        // Mock axios
        axios.post = jest.fn().mockResolvedValue({ status: 200 });

        mockConfig = {
            channels: ['console', 'email', 'slack'],
            escalationDelays: [1000, 2000], // Short delays for testing
            retryAttempts: 2,
            retryDelay: 100,
            deduplicationWindow: 1000,
            maxAlertsPerHour: 10,
            email: {
                smtp: {
                    host: 'smtp.test.com',
                    port: 587,
                    auth: { user: 'test', pass: 'test' }
                },
                from: 'alerts@test.com',
                to: 'admin@test.com'
            },
            slack: {
                webhookUrl: 'https://hooks.slack.com/test'
            }
        };

        alertManager = new AlertManager(mockConfig);
    });

    afterEach(() => {
        // Clear all timers
        jest.clearAllTimers();
        jest.useRealTimers();
    });

    describe('Initialization', () => {
        it('should initialize with default configuration', () => {
            const manager = new AlertManager();
            expect(manager).toBeDefined();
            expect(manager.notificationChannels.has('console')).toBe(true);
        });

        it('should initialize notification channels', () => {
            expect(alertManager.notificationChannels.has('console')).toBe(true);
            expect(alertManager.notificationChannels.has('email')).toBe(true);
            expect(alertManager.notificationChannels.has('slack')).toBe(true);
        });

        it('should not initialize channels without configuration', () => {
            const manager = new AlertManager({});
            expect(manager.notificationChannels.has('email')).toBe(false);
            expect(manager.notificationChannels.has('slack')).toBe(false);
        });
    });

    describe('Alert Creation', () => {
        it('should create alert with required fields', async () => {
            const alertData = {
                severity: 'critical',
                component: 'trading.engine',
                message: 'Trading engine is down',
                source: 'health_monitor'
            };

            const alert = await alertManager.createAlert(alertData);

            expect(alert).toBeDefined();
            expect(alert.id).toBeDefined();
            expect(alert.severity).toBe('critical');
            expect(alert.component).toBe('trading.engine');
            expect(alert.status).toBe('active');
            expect(alert.timestamp).toBeInstanceOf(Date);
        });

        it('should validate severity levels', async () => {
            const alertData = {
                severity: 'invalid',
                component: 'test',
                message: 'Test alert'
            };

            await expect(alertManager.createAlert(alertData)).rejects.toThrow('Invalid severity: invalid');
        });

        it('should set default values for missing fields', async () => {
            const alertData = {
                message: 'Test alert'
            };

            const alert = await alertManager.createAlert(alertData);

            expect(alert.severity).toBe('warning');
            expect(alert.component).toBe('unknown');
            expect(alert.source).toBe('system');
        });

        it('should emit alert.created event', async () => {
            const emitSpy = jest.spyOn(alertManager, 'emit');
            const alertData = {
                severity: 'warning',
                component: 'test',
                message: 'Test alert'
            };

            await alertManager.createAlert(alertData);

            expect(emitSpy).toHaveBeenCalledWith('alert.created', expect.objectContaining({
                severity: 'warning',
                component: 'test'
            }));
        });
    });

    describe('Rate Limiting', () => {
        it('should rate limit alerts', async () => {
            // Set low rate limit
            alertManager.config.maxAlertsPerHour = 2;

            const alertData = {
                component: 'test.rate',
                message: 'Rate limit test'
            };

            // Create alerts up to limit
            await alertManager.createAlert(alertData);
            await alertManager.createAlert(alertData);

            // This should be rate limited
            const rateLimitedAlert = await alertManager.createAlert(alertData);
            expect(rateLimitedAlert).toBeNull();
        });
    });

    describe('Deduplication', () => {
        it('should deduplicate identical alerts', async () => {
            const alertData = {
                severity: 'warning',
                component: 'test.dedup',
                message: 'Duplicate test'
            };

            const alert1 = await alertManager.createAlert(alertData);
            const alert2 = await alertManager.createAlert(alertData);

            expect(alert1).toBeDefined();
            expect(alert2).toBeDefined();
            expect(alert1.id).not.toBe(alert2.id); // Different objects
            expect(alert2.count).toBe(2); // Second alert should update count
        });

        it('should not deduplicate different alerts', async () => {
            const alert1Data = { component: 'test.1', message: 'Test 1' };
            const alert2Data = { component: 'test.2', message: 'Test 2' };

            const alert1 = await alertManager.createAlert(alert1Data);
            const alert2 = await alertManager.createAlert(alert2Data);

            expect(alert1.component).toBe('test.1');
            expect(alert2.component).toBe('test.2');
            expect(alertManager.activeAlerts.size).toBe(2);
        });
    });

    describe('Notification Channels', () => {
        it('should send console alert', async () => {
            const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

            const alert = {
                severity: 'warning',
                component: 'test',
                message: 'Console test',
                timestamp: new Date()
            };

            const channel = alertManager.notificationChannels.get('console');
            const result = await channel.send(alert);

            expect(result.deliveryId).toBeDefined();
            expect(consoleSpy).toHaveBeenCalled();

            consoleSpy.mockRestore();
        });

        it('should send email alert', async () => {
            const alert = {
                severity: 'critical',
                component: 'test.email',
                message: 'Email test',
                timestamp: new Date()
            };

            const channel = alertManager.notificationChannels.get('email');
            const result = await channel.send(alert);

            expect(mockTransporter.sendMail).toHaveBeenCalled();
            expect(result.messageId).toBe('test-message-id');
        });

        it('should send Slack alert', async () => {
            const alert = {
                severity: 'warning',
                component: 'test.slack',
                message: 'Slack test',
                timestamp: new Date()
            };

            const channel = alertManager.notificationChannels.get('slack');
            const result = await channel.send(alert);

            expect(axios.post).toHaveBeenCalledWith(
                'https://hooks.slack.com/test',
                expect.objectContaining({
                    text: expect.stringContaining('Trading Platform Alert')
                })
            );
            expect(result.statusCode).toBe(200);
        });
    });

    describe('Alert Processing', () => {
        it('should process alert through appropriate channels', async () => {
            const alertData = {
                severity: 'critical',
                component: 'test.process',
                message: 'Process test'
            };

            const alert = await alertManager.createAlert(alertData);

            expect(alert.notifications).toBeDefined();
            expect(Array.isArray(alert.notifications)).toBe(true);

            // Critical alerts should go to multiple channels
            const channelNames = alert.notifications.map(n => n.channel);
            expect(channelNames).toContain('console');
            expect(channelNames).toContain('email');
            expect(channelNames).toContain('slack');
        });

        it('should handle notification failures gracefully', async () => {
            // Make email fail
            mockTransporter.sendMail.mockRejectedValue(new Error('SMTP Error'));

            const alertData = {
                severity: 'critical',
                component: 'test.failure',
                message: 'Failure test'
            };

            const alert = await alertManager.createAlert(alertData);

            const emailNotification = alert.notifications.find(n => n.channel === 'email');
            expect(emailNotification.status).toBe('failed');
            expect(emailNotification.error).toBe('SMTP Error');
        });
    });

    describe('Alert Escalation', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        it('should setup escalation for critical alerts', async () => {
            const emitSpy = jest.spyOn(alertManager, 'emit');

            const alertData = {
                severity: 'critical',
                component: 'test.escalation',
                message: 'Escalation test'
            };

            await alertManager.createAlert(alertData);

            // Fast-forward through escalation delays
            jest.advanceTimersByTime(1000);

            expect(emitSpy).toHaveBeenCalledWith('alert.escalated', expect.objectContaining({
                escalationLevel: 1
            }));
        });

        it('should not escalate resolved alerts', async () => {
            const alertData = {
                severity: 'critical',
                component: 'test.resolved',
                message: 'Resolved test'
            };

            const alert = await alertManager.createAlert(alertData);

            // Resolve the alert
            alertManager.resolveAlert(alert.id);

            const emitSpy = jest.spyOn(alertManager, 'emit');

            // Fast-forward through escalation delay
            jest.advanceTimersByTime(1000);

            // Should not emit escalation for resolved alert
            expect(emitSpy).not.toHaveBeenCalledWith('alert.escalated', expect.anything());
        });
    });

    describe('Alert Resolution', () => {
        it('should resolve active alert', async () => {
            const alertData = {
                component: 'test.resolve',
                message: 'Resolve test'
            };

            const alert = await alertManager.createAlert(alertData);
            expect(alertManager.activeAlerts.has(alert.id)).toBe(true);

            const emitSpy = jest.spyOn(alertManager, 'emit');
            const resolved = alertManager.resolveAlert(alert.id, 'admin');

            expect(resolved).toBe(true);
            expect(alertManager.activeAlerts.has(alert.id)).toBe(false);
            expect(alert.status).toBe('resolved');
            expect(alert.resolvedBy).toBe('admin');
            expect(alert.resolvedAt).toBeInstanceOf(Date);
            expect(emitSpy).toHaveBeenCalledWith('alert.resolved', alert);
        });

        it('should not resolve non-existent alert', () => {
            const resolved = alertManager.resolveAlert('non-existent');
            expect(resolved).toBe(false);
        });
    });

    describe('Alert Suppression', () => {
        beforeEach(() => {
            jest.useFakeTimers();
        });

        it('should suppress alerts for component', () => {
            const emitSpy = jest.spyOn(alertManager, 'emit');

            alertManager.suppressAlerts('test.suppress', 1000);

            expect(alertManager.suppressedAlerts.has('test.suppress')).toBe(true);
            expect(emitSpy).toHaveBeenCalledWith('alert.suppressed', {
                component: 'test.suppress',
                duration: 1000
            });
        });

        it('should automatically unsuppress after duration', () => {
            const emitSpy = jest.spyOn(alertManager, 'emit');

            alertManager.suppressAlerts('test.auto', 1000);

            jest.advanceTimersByTime(1000);

            expect(alertManager.suppressedAlerts.has('test.auto')).toBe(false);
            expect(emitSpy).toHaveBeenCalledWith('alert.suppression.expired', 'test.auto');
        });
    });

    describe('Channel Selection', () => {
        it('should select correct channels for info severity', () => {
            const channels = alertManager.getChannelsForSeverity('info');
            expect(channels).toEqual(['console']);
        });

        it('should select correct channels for warning severity', () => {
            const channels = alertManager.getChannelsForSeverity('warning');
            expect(channels).toEqual(['console', 'slack', 'webhook']);
        });

        it('should select correct channels for critical severity', () => {
            const channels = alertManager.getChannelsForSeverity('critical');
            expect(channels).toEqual(['console', 'email', 'slack', 'webhook', 'sms']);
        });
    });

    describe('Statistics and Information', () => {
        it('should return alert statistics', async () => {
            // Create some test alerts
            await alertManager.createAlert({
                severity: 'critical',
                component: 'test.stats.1',
                message: 'Stats test 1'
            });

            await alertManager.createAlert({
                severity: 'warning',
                component: 'test.stats.2',
                message: 'Stats test 2'
            });

            const stats = alertManager.getStatistics();

            expect(stats).toBeDefined();
            expect(typeof stats.active).toBe('number');
            expect(typeof stats.total).toBe('number');
            expect(stats.bySeverity).toBeDefined();
            expect(Array.isArray(stats.channels)).toBe(true);
        });

        it('should return active alerts', async () => {
            await alertManager.createAlert({
                component: 'test.active',
                message: 'Active test'
            });

            const activeAlerts = alertManager.getActiveAlerts();

            expect(Array.isArray(activeAlerts)).toBe(true);
            expect(activeAlerts.length).toBeGreaterThan(0);
            expect(activeAlerts[0].component).toBe('test.active');
        });

        it('should return alert history', async () => {
            await alertManager.createAlert({
                component: 'test.history',
                message: 'History test'
            });

            const history = alertManager.getAlertHistory(10);

            expect(Array.isArray(history)).toBe(true);
            expect(history.length).toBeGreaterThan(0);
        });
    });

    describe('Utility Functions', () => {
        it('should get severity emoji', () => {
            expect(alertManager.getSeverityEmoji('info')).toBe('ℹ️');
            expect(alertManager.getSeverityEmoji('warning')).toBe('⚠️');
            expect(alertManager.getSeverityEmoji('critical')).toBe('🚨');
        });

        it('should get severity color', () => {
            expect(alertManager.getSeverityColor('info')).toBe('#36a64f');
            expect(alertManager.getSeverityColor('warning')).toBe('#ff9500');
            expect(alertManager.getSeverityColor('critical')).toBe('#ff0000');
        });

        it('should get recommended actions', () => {
            const alert = { component: 'system.cpu' };
            const actions = alertManager.getRecommendedActions(alert);

            expect(Array.isArray(actions)).toBe(true);
            expect(actions.length).toBeGreaterThan(0);
            expect(actions).toContain('Check for runaway processes');
        });

        it('should generate unique alert IDs', () => {
            const id1 = alertManager.generateAlertId();
            const id2 = alertManager.generateAlertId();

            expect(id1).not.toBe(id2);
            expect(id1).toMatch(/^alert_\d+_[a-z0-9]+$/);
        });
    });

    describe('Cleanup', () => {
        it('should clean up old data', () => {
            // Add some old data
            const oldTimestamp = new Date(Date.now() - 25 * 60 * 60 * 1000); // 25 hours ago
            alertManager.alertHistory.push({
                id: 'old-alert',
                timestamp: oldTimestamp
            });

            const oldHour = Math.floor((Date.now() - 25 * 60 * 60 * 1000) / 3600000);
            alertManager.alertCounts.set(`test_${oldHour}`, 5);

            alertManager.cleanupOldData();

            // Old data should be removed
            expect(alertManager.alertHistory.find(a => a.id === 'old-alert')).toBeUndefined();
            expect(alertManager.alertCounts.has(`test_${oldHour}`)).toBe(false);
        });
    });
});