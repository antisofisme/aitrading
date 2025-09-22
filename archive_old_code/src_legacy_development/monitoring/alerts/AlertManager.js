const EventEmitter = require('events');
const nodemailer = require('nodemailer');
const axios = require('axios');

/**
 * Comprehensive Alert Management System
 * Handles alert generation, routing, escalation, and notification delivery
 */
class AlertManager extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            channels: config.channels || ['console', 'email', 'webhook'],
            escalationDelays: config.escalationDelays || [300000, 900000, 3600000], // 5min, 15min, 1hr
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 5000,
            deduplicationWindow: config.deduplicationWindow || 300000, // 5 minutes
            maxAlertsPerHour: config.maxAlertsPerHour || 100,
            ...config
        };

        this.alerts = new Map();
        this.activeAlerts = new Map();
        this.alertHistory = [];
        this.suppressedAlerts = new Set();
        this.notificationChannels = new Map();
        this.escalationTimers = new Map();
        this.alertCounts = new Map();

        this.initializeChannels();
        this.startCleanupTimer();
    }

    /**
     * Initialize notification channels
     */
    initializeChannels() {
        // Console channel (always available)
        this.notificationChannels.set('console', {
            name: 'console',
            enabled: true,
            send: this.sendConsoleAlert.bind(this)
        });

        // Email channel
        if (this.config.email) {
            this.notificationChannels.set('email', {
                name: 'email',
                enabled: true,
                transporter: nodemailer.createTransporter(this.config.email.smtp),
                send: this.sendEmailAlert.bind(this)
            });
        }

        // Slack channel
        if (this.config.slack) {
            this.notificationChannels.set('slack', {
                name: 'slack',
                enabled: true,
                webhookUrl: this.config.slack.webhookUrl,
                send: this.sendSlackAlert.bind(this)
            });
        }

        // Webhook channel
        if (this.config.webhook) {
            this.notificationChannels.set('webhook', {
                name: 'webhook',
                enabled: true,
                url: this.config.webhook.url,
                headers: this.config.webhook.headers || {},
                send: this.sendWebhookAlert.bind(this)
            });
        }

        // SMS channel (placeholder)
        if (this.config.sms) {
            this.notificationChannels.set('sms', {
                name: 'sms',
                enabled: true,
                send: this.sendSmsAlert.bind(this)
            });
        }
    }

    /**
     * Create and process an alert
     */
    async createAlert(alertData) {
        const alert = {
            id: this.generateAlertId(),
            timestamp: new Date(),
            status: 'active',
            ...alertData,
            // Required fields validation
            severity: alertData.severity || 'warning',
            component: alertData.component || 'unknown',
            message: alertData.message || 'Alert triggered',
            source: alertData.source || 'system'
        };

        // Validate severity
        if (!['info', 'warning', 'critical'].includes(alert.severity)) {
            throw new Error(`Invalid severity: ${alert.severity}`);
        }

        // Check rate limiting
        if (this.isRateLimited(alert)) {
            console.warn(`⚠️ Alert rate limited: ${alert.component}`);
            return null;
        }

        // Check deduplication
        if (this.isDuplicate(alert)) {
            console.log(`🔄 Alert deduplicated: ${alert.component}`);
            return this.updateExistingAlert(alert);
        }

        // Store alert
        this.alerts.set(alert.id, alert);
        this.activeAlerts.set(alert.id, alert);
        this.alertHistory.push(alert);

        // Process alert
        await this.processAlert(alert);

        this.emit('alert.created', alert);
        return alert;
    }

    /**
     * Process alert through notification channels
     */
    async processAlert(alert) {
        const channels = this.getChannelsForSeverity(alert.severity);
        const notifications = [];

        for (const channelName of channels) {
            const channel = this.notificationChannels.get(channelName);
            if (!channel || !channel.enabled) continue;

            try {
                const notification = await this.sendNotification(channel, alert);
                notifications.push({
                    channel: channelName,
                    status: 'sent',
                    timestamp: new Date(),
                    ...notification
                });
            } catch (error) {
                notifications.push({
                    channel: channelName,
                    status: 'failed',
                    error: error.message,
                    timestamp: new Date()
                });

                await this.retryNotification(channel, alert);
            }
        }

        alert.notifications = notifications;

        // Setup escalation if critical
        if (alert.severity === 'critical') {
            this.setupEscalation(alert);
        }

        this.emit('alert.processed', alert);
    }

    /**
     * Send notification through specified channel
     */
    async sendNotification(channel, alert, retry = 0) {
        try {
            const result = await channel.send(alert, retry);
            this.emit('notification.sent', { channel: channel.name, alert, result });
            return result;
        } catch (error) {
            this.emit('notification.failed', { channel: channel.name, alert, error, retry });
            throw error;
        }
    }

    /**
     * Retry failed notification
     */
    async retryNotification(channel, alert) {
        for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
            await new Promise(resolve => setTimeout(resolve, this.config.retryDelay * attempt));

            try {
                await this.sendNotification(channel, alert, attempt);
                break;
            } catch (error) {
                if (attempt === this.config.retryAttempts) {
                    console.error(`❌ Failed to send alert after ${attempt} attempts:`, error.message);
                }
            }
        }
    }

    /**
     * Console notification channel
     */
    async sendConsoleAlert(alert) {
        const emoji = this.getSeverityEmoji(alert.severity);
        const timestamp = alert.timestamp.toISOString();

        console.log(`${emoji} [${alert.severity.toUpperCase()}] ${timestamp}`);
        console.log(`   Component: ${alert.component}`);
        console.log(`   Message: ${alert.message}`);

        if (alert.value !== undefined) {
            console.log(`   Value: ${alert.value}${alert.unit || ''}`);
        }

        if (alert.threshold !== undefined) {
            console.log(`   Threshold: ${alert.threshold}`);
        }

        console.log('');

        return { deliveryId: `console_${Date.now()}` };
    }

    /**
     * Email notification channel
     */
    async sendEmailAlert(alert) {
        const channel = this.notificationChannels.get('email');
        const subject = `[${alert.severity.toUpperCase()}] Trading Platform Alert: ${alert.component}`;

        const html = `
            <h2>Trading Platform Alert</h2>
            <table style="border-collapse: collapse; width: 100%;">
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Severity:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: ${this.getSeverityColor(alert.severity)};">
                        ${alert.severity.toUpperCase()}
                    </td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Component:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${alert.component}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Message:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${alert.message}</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">${alert.timestamp.toISOString()}</td></tr>
                ${alert.value !== undefined ?
                    `<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Value:</strong></td>
                         <td style="padding: 8px; border: 1px solid #ddd;">${alert.value}${alert.unit || ''}</td></tr>` : ''
                }
                ${alert.threshold !== undefined ?
                    `<tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Threshold:</strong></td>
                         <td style="padding: 8px; border: 1px solid #ddd;">${alert.threshold}</td></tr>` : ''
                }
            </table>

            <h3>Recommended Actions:</h3>
            <ul>
                ${this.getRecommendedActions(alert).map(action => `<li>${action}</li>`).join('')}
            </ul>
        `;

        const mailOptions = {
            from: this.config.email.from,
            to: this.config.email.to,
            subject,
            html
        };

        const result = await channel.transporter.sendMail(mailOptions);
        return { messageId: result.messageId };
    }

    /**
     * Slack notification channel
     */
    async sendSlackAlert(alert) {
        const channel = this.notificationChannels.get('slack');
        const color = this.getSeverityColor(alert.severity);
        const emoji = this.getSeverityEmoji(alert.severity);

        const payload = {
            text: `${emoji} Trading Platform Alert`,
            attachments: [{
                color,
                title: `${alert.severity.toUpperCase()}: ${alert.component}`,
                text: alert.message,
                fields: [
                    {
                        title: 'Component',
                        value: alert.component,
                        short: true
                    },
                    {
                        title: 'Severity',
                        value: alert.severity.toUpperCase(),
                        short: true
                    },
                    {
                        title: 'Time',
                        value: alert.timestamp.toISOString(),
                        short: false
                    }
                ],
                footer: 'AI Trading Platform',
                ts: Math.floor(alert.timestamp.getTime() / 1000)
            }]
        };

        if (alert.value !== undefined) {
            payload.attachments[0].fields.push({
                title: 'Value',
                value: `${alert.value}${alert.unit || ''}`,
                short: true
            });
        }

        if (alert.threshold !== undefined) {
            payload.attachments[0].fields.push({
                title: 'Threshold',
                value: alert.threshold,
                short: true
            });
        }

        const response = await axios.post(channel.webhookUrl, payload);
        return { statusCode: response.status };
    }

    /**
     * Webhook notification channel
     */
    async sendWebhookAlert(alert) {
        const channel = this.notificationChannels.get('webhook');

        const payload = {
            alert,
            timestamp: new Date(),
            source: 'ai-trading-platform'
        };

        const response = await axios.post(channel.url, payload, {
            headers: channel.headers
        });

        return { statusCode: response.status };
    }

    /**
     * SMS notification channel (placeholder)
     */
    async sendSmsAlert(alert) {
        // Placeholder for SMS implementation
        console.log(`📱 SMS Alert: ${alert.message}`);
        return { deliveryId: `sms_${Date.now()}` };
    }

    /**
     * Check if alert is rate limited
     */
    isRateLimited(alert) {
        const hour = Math.floor(Date.now() / 3600000);
        const key = `${alert.component}_${hour}`;

        const count = this.alertCounts.get(key) || 0;
        if (count >= this.config.maxAlertsPerHour) {
            return true;
        }

        this.alertCounts.set(key, count + 1);
        return false;
    }

    /**
     * Check if alert is duplicate
     */
    isDuplicate(alert) {
        const cutoff = new Date(Date.now() - this.config.deduplicationWindow);

        for (const existingAlert of this.activeAlerts.values()) {
            if (existingAlert.timestamp > cutoff &&
                existingAlert.component === alert.component &&
                existingAlert.severity === alert.severity &&
                existingAlert.message === alert.message) {
                return true;
            }
        }

        return false;
    }

    /**
     * Update existing alert
     */
    updateExistingAlert(alert) {
        for (const existingAlert of this.activeAlerts.values()) {
            if (existingAlert.component === alert.component &&
                existingAlert.severity === alert.severity) {
                existingAlert.lastSeen = new Date();
                existingAlert.count = (existingAlert.count || 1) + 1;
                return existingAlert;
            }
        }
        return null;
    }

    /**
     * Setup escalation for critical alerts
     */
    setupEscalation(alert) {
        if (alert.severity !== 'critical') return;

        this.config.escalationDelays.forEach((delay, index) => {
            const timerId = setTimeout(() => {
                this.escalateAlert(alert, index + 1);
            }, delay);

            const escalationKey = `${alert.id}_${index}`;
            this.escalationTimers.set(escalationKey, timerId);
        });
    }

    /**
     * Escalate alert
     */
    async escalateAlert(alert, level) {
        if (!this.activeAlerts.has(alert.id)) return; // Alert resolved

        const escalatedAlert = {
            ...alert,
            escalationLevel: level,
            escalatedAt: new Date(),
            message: `[ESCALATION LEVEL ${level}] ${alert.message}`
        };

        await this.processAlert(escalatedAlert);
        this.emit('alert.escalated', escalatedAlert);
    }

    /**
     * Resolve alert
     */
    resolveAlert(alertId, resolvedBy = 'system') {
        const alert = this.activeAlerts.get(alertId);
        if (!alert) return false;

        alert.status = 'resolved';
        alert.resolvedAt = new Date();
        alert.resolvedBy = resolvedBy;

        this.activeAlerts.delete(alertId);

        // Cancel escalation timers
        this.config.escalationDelays.forEach((_, index) => {
            const escalationKey = `${alertId}_${index}`;
            const timer = this.escalationTimers.get(escalationKey);
            if (timer) {
                clearTimeout(timer);
                this.escalationTimers.delete(escalationKey);
            }
        });

        this.emit('alert.resolved', alert);
        return true;
    }

    /**
     * Suppress alerts for component
     */
    suppressAlerts(component, duration = 3600000) { // 1 hour default
        this.suppressedAlerts.add(component);

        setTimeout(() => {
            this.suppressedAlerts.delete(component);
            this.emit('alert.suppression.expired', component);
        }, duration);

        this.emit('alert.suppressed', { component, duration });
    }

    /**
     * Get channels for severity level
     */
    getChannelsForSeverity(severity) {
        switch (severity) {
            case 'info':
                return ['console'];
            case 'warning':
                return ['console', 'slack', 'webhook'];
            case 'critical':
                return ['console', 'email', 'slack', 'webhook', 'sms'];
            default:
                return ['console'];
        }
    }

    /**
     * Get severity emoji
     */
    getSeverityEmoji(severity) {
        switch (severity) {
            case 'info': return 'ℹ️';
            case 'warning': return '⚠️';
            case 'critical': return '🚨';
            default: return '🔔';
        }
    }

    /**
     * Get severity color
     */
    getSeverityColor(severity) {
        switch (severity) {
            case 'info': return '#36a64f';
            case 'warning': return '#ff9500';
            case 'critical': return '#ff0000';
            default: return '#cccccc';
        }
    }

    /**
     * Get recommended actions
     */
    getRecommendedActions(alert) {
        const actions = [];

        switch (alert.component) {
            case 'system.cpu':
                actions.push('Check for runaway processes');
                actions.push('Consider scaling resources');
                break;
            case 'system.memory':
                actions.push('Investigate memory leaks');
                actions.push('Restart affected services');
                break;
            case 'trading.risk':
                actions.push('Review open positions');
                actions.push('Consider reducing exposure');
                break;
            case 'market_data':
                actions.push('Check data feed connectivity');
                actions.push('Verify market hours');
                break;
            default:
                actions.push('Investigate the issue');
                actions.push('Check system logs');
        }

        return actions;
    }

    /**
     * Generate unique alert ID
     */
    generateAlertId() {
        return `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Start cleanup timer
     */
    startCleanupTimer() {
        setInterval(() => {
            this.cleanupOldData();
        }, 3600000); // 1 hour
    }

    /**
     * Clean up old data
     */
    cleanupOldData() {
        const cutoff = new Date(Date.now() - 86400000); // 24 hours

        // Clean alert history
        this.alertHistory = this.alertHistory.filter(alert =>
            alert.timestamp > cutoff
        );

        // Clean alert counts
        const currentHour = Math.floor(Date.now() / 3600000);
        for (const [key] of this.alertCounts) {
            const hour = parseInt(key.split('_').pop());
            if (currentHour - hour > 24) {
                this.alertCounts.delete(key);
            }
        }
    }

    /**
     * Get alert statistics
     */
    getStatistics() {
        const now = new Date();
        const last24h = new Date(now.getTime() - 86400000);
        const lastHour = new Date(now.getTime() - 3600000);

        const recent24h = this.alertHistory.filter(a => a.timestamp > last24h);
        const recentHour = this.alertHistory.filter(a => a.timestamp > lastHour);

        return {
            active: this.activeAlerts.size,
            total: this.alerts.size,
            last24h: recent24h.length,
            lastHour: recentHour.length,
            bySeverity: {
                critical: recent24h.filter(a => a.severity === 'critical').length,
                warning: recent24h.filter(a => a.severity === 'warning').length,
                info: recent24h.filter(a => a.severity === 'info').length
            },
            channels: Array.from(this.notificationChannels.keys()),
            suppressed: this.suppressedAlerts.size
        };
    }

    /**
     * Get active alerts
     */
    getActiveAlerts() {
        return Array.from(this.activeAlerts.values());
    }

    /**
     * Get alert history
     */
    getAlertHistory(limit = 100) {
        return this.alertHistory
            .slice(-limit)
            .sort((a, b) => b.timestamp - a.timestamp);
    }
}

module.exports = AlertManager;