const EventEmitter = require('events');
const nodemailer = require('nodemailer');
const axios = require('axios');
const twilio = require('twilio');

/**
 * Advanced Notification Service
 * Handles multiple notification channels with retry logic and templates
 */
class NotificationService extends EventEmitter {
    constructor(config = {}) {
        super();
        this.config = {
            channels: {
                email: config.email || null,
                slack: config.slack || null,
                sms: config.sms || null,
                webhook: config.webhook || null,
                discord: config.discord || null,
                teams: config.teams || null
            },
            retryAttempts: config.retryAttempts || 3,
            retryDelay: config.retryDelay || 5000,
            rateLimit: config.rateLimit || {
                maxPerMinute: 60,
                maxPerHour: 500
            },
            templates: config.templates || {},
            ...config
        };

        this.transports = new Map();
        this.messageQueue = [];
        this.rateLimiter = new Map();
        this.isProcessing = false;

        this.initializeTransports();
        this.startQueueProcessor();
    }

    /**
     * Initialize notification transports
     */
    initializeTransports() {
        console.log('📧 Initializing notification transports...');

        // Email transport
        if (this.config.channels.email) {
            try {
                const transporter = nodemailer.createTransporter(this.config.channels.email.smtp);
                this.transports.set('email', {
                    type: 'email',
                    transporter,
                    config: this.config.channels.email,
                    send: this.sendEmail.bind(this)
                });
                console.log('✅ Email transport initialized');
            } catch (error) {
                console.error('❌ Failed to initialize email transport:', error.message);
            }
        }

        // Slack transport
        if (this.config.channels.slack) {
            this.transports.set('slack', {
                type: 'slack',
                config: this.config.channels.slack,
                send: this.sendSlack.bind(this)
            });
            console.log('✅ Slack transport initialized');
        }

        // SMS transport (Twilio)
        if (this.config.channels.sms) {
            try {
                const client = twilio(
                    this.config.channels.sms.accountSid,
                    this.config.channels.sms.authToken
                );
                this.transports.set('sms', {
                    type: 'sms',
                    client,
                    config: this.config.channels.sms,
                    send: this.sendSMS.bind(this)
                });
                console.log('✅ SMS transport initialized');
            } catch (error) {
                console.error('❌ Failed to initialize SMS transport:', error.message);
            }
        }

        // Webhook transport
        if (this.config.channels.webhook) {
            this.transports.set('webhook', {
                type: 'webhook',
                config: this.config.channels.webhook,
                send: this.sendWebhook.bind(this)
            });
            console.log('✅ Webhook transport initialized');
        }

        // Discord transport
        if (this.config.channels.discord) {
            this.transports.set('discord', {
                type: 'discord',
                config: this.config.channels.discord,
                send: this.sendDiscord.bind(this)
            });
            console.log('✅ Discord transport initialized');
        }

        // Microsoft Teams transport
        if (this.config.channels.teams) {
            this.transports.set('teams', {
                type: 'teams',
                config: this.config.channels.teams,
                send: this.sendTeams.bind(this)
            });
            console.log('✅ Teams transport initialized');
        }
    }

    /**
     * Send notification through specified channels
     */
    async sendNotification(message, channels = null, priority = 'normal') {
        const notification = {
            id: this.generateId(),
            message,
            channels: channels || this.getDefaultChannelsForPriority(priority),
            priority,
            timestamp: new Date(),
            attempts: 0,
            status: 'pending'
        };

        // Add to queue
        this.messageQueue.push(notification);
        this.emit('notification.queued', notification);

        return notification.id;
    }

    /**
     * Process message queue
     */
    startQueueProcessor() {
        setInterval(async () => {
            if (this.isProcessing || this.messageQueue.length === 0) return;

            this.isProcessing = true;
            const notification = this.messageQueue.shift();

            try {
                await this.processNotification(notification);
            } catch (error) {
                console.error('❌ Failed to process notification:', error);
            } finally {
                this.isProcessing = false;
            }
        }, 1000);
    }

    /**
     * Process individual notification
     */
    async processNotification(notification) {
        notification.attempts++;

        // Check rate limiting
        if (this.isRateLimited(notification)) {
            // Re-queue for later
            this.messageQueue.push(notification);
            return;
        }

        const results = [];

        for (const channel of notification.channels) {
            const transport = this.transports.get(channel);
            if (!transport) {
                results.push({
                    channel,
                    status: 'failed',
                    error: 'Transport not available'
                });
                continue;
            }

            try {
                const result = await this.sendToChannel(transport, notification);
                results.push({
                    channel,
                    status: 'sent',
                    result,
                    timestamp: new Date()
                });

                this.updateRateLimit(channel);
            } catch (error) {
                results.push({
                    channel,
                    status: 'failed',
                    error: error.message,
                    timestamp: new Date()
                });

                // Retry logic
                if (notification.attempts < this.config.retryAttempts) {
                    setTimeout(() => {
                        this.messageQueue.push(notification);
                    }, this.config.retryDelay * notification.attempts);
                }
            }
        }

        notification.results = results;
        notification.status = results.every(r => r.status === 'sent') ? 'sent' : 'partial';

        this.emit('notification.processed', notification);
    }

    /**
     * Send to specific channel
     */
    async sendToChannel(transport, notification) {
        const formattedMessage = this.formatMessage(notification.message, transport.type);
        return await transport.send(formattedMessage, notification);
    }

    /**
     * Email sending implementation
     */
    async sendEmail(message, notification) {
        const transport = this.transports.get('email');
        const template = this.getTemplate('email', notification.message.type);

        const mailOptions = {
            from: transport.config.from,
            to: notification.message.recipients || transport.config.to,
            subject: this.renderTemplate(template.subject, notification.message),
            html: this.renderTemplate(template.html, notification.message),
            text: this.renderTemplate(template.text, notification.message)
        };

        const result = await transport.transporter.sendMail(mailOptions);
        return { messageId: result.messageId };
    }

    /**
     * Slack sending implementation
     */
    async sendSlack(message, notification) {
        const transport = this.transports.get('slack');
        const template = this.getTemplate('slack', notification.message.type);

        const payload = {
            text: this.renderTemplate(template.text, notification.message),
            blocks: this.buildSlackBlocks(notification.message),
            channel: notification.message.channel || transport.config.channel
        };

        const response = await axios.post(transport.config.webhookUrl, payload);
        return { statusCode: response.status };
    }

    /**
     * SMS sending implementation
     */
    async sendSMS(message, notification) {
        const transport = this.transports.get('sms');
        const template = this.getTemplate('sms', notification.message.type);

        const messageText = this.renderTemplate(template.text, notification.message);

        const result = await transport.client.messages.create({
            body: messageText,
            from: transport.config.from,
            to: notification.message.recipient || transport.config.to
        });

        return { sid: result.sid };
    }

    /**
     * Webhook sending implementation
     */
    async sendWebhook(message, notification) {
        const transport = this.transports.get('webhook');

        const payload = {
            notification,
            message,
            timestamp: new Date(),
            source: 'ai-trading-platform'
        };

        const response = await axios.post(transport.config.url, payload, {
            headers: transport.config.headers || {}
        });

        return { statusCode: response.status };
    }

    /**
     * Discord sending implementation
     */
    async sendDiscord(message, notification) {
        const transport = this.transports.get('discord');
        const template = this.getTemplate('discord', notification.message.type);

        const payload = {
            content: this.renderTemplate(template.text, notification.message),
            embeds: this.buildDiscordEmbeds(notification.message)
        };

        const response = await axios.post(transport.config.webhookUrl, payload);
        return { statusCode: response.status };
    }

    /**
     * Microsoft Teams sending implementation
     */
    async sendTeams(message, notification) {
        const transport = this.transports.get('teams');
        const template = this.getTemplate('teams', notification.message.type);

        const payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": this.getColorForSeverity(notification.message.severity),
            "summary": notification.message.title,
            "sections": [{
                "activityTitle": notification.message.title,
                "activitySubtitle": this.renderTemplate(template.text, notification.message),
                "facts": this.buildTeamsFacts(notification.message)
            }]
        };

        const response = await axios.post(transport.config.webhookUrl, payload);
        return { statusCode: response.status };
    }

    /**
     * Format message for specific channel
     */
    formatMessage(message, channelType) {
        switch (channelType) {
            case 'email':
                return {
                    ...message,
                    html: message.html || this.convertToHtml(message.text || message.content)
                };
            case 'sms':
                return {
                    ...message,
                    text: this.truncateForSMS(message.text || message.content)
                };
            default:
                return message;
        }
    }

    /**
     * Get template for channel and message type
     */
    getTemplate(channel, messageType) {
        const templates = {
            email: {
                alert: {
                    subject: '[{{severity}}] Trading Platform Alert: {{title}}',
                    html: `
                        <h2>Trading Platform Alert</h2>
                        <table style="border-collapse: collapse; width: 100%;">
                            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Severity:</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd; color: {{severityColor}};">{{severity}}</td></tr>
                            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Component:</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{{component}}</td></tr>
                            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Message:</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{{message}}</td></tr>
                            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td>
                                <td style="padding: 8px; border: 1px solid #ddd;">{{timestamp}}</td></tr>
                        </table>
                    `,
                    text: '[{{severity}}] {{component}}: {{message}} at {{timestamp}}'
                }
            },
            slack: {
                alert: {
                    text: ':warning: Trading Platform Alert: {{title}}'
                }
            },
            sms: {
                alert: {
                    text: '[{{severity}}] {{component}}: {{message}}'
                }
            },
            discord: {
                alert: {
                    text: '🚨 Trading Platform Alert: {{title}}'
                }
            },
            teams: {
                alert: {
                    text: '{{message}}'
                }
            }
        };

        return templates[channel]?.[messageType] || templates[channel]?.default || {
            subject: '{{title}}',
            text: '{{message}}',
            html: '{{message}}'
        };
    }

    /**
     * Render template with data
     */
    renderTemplate(template, data) {
        if (!template) return '';

        return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] || match;
        });
    }

    /**
     * Build Slack blocks
     */
    buildSlackBlocks(message) {
        return [
            {
                type: 'section',
                text: {
                    type: 'mrkdwn',
                    text: `*${message.title}*\n${message.content || message.message}`
                }
            },
            {
                type: 'section',
                fields: [
                    {
                        type: 'mrkdwn',
                        text: `*Severity:*\n${message.severity}`
                    },
                    {
                        type: 'mrkdwn',
                        text: `*Component:*\n${message.component}`
                    },
                    {
                        type: 'mrkdwn',
                        text: `*Time:*\n${message.timestamp}`
                    }
                ]
            }
        ];
    }

    /**
     * Build Discord embeds
     */
    buildDiscordEmbeds(message) {
        return [{
            title: message.title,
            description: message.content || message.message,
            color: this.getColorCodeForSeverity(message.severity),
            fields: [
                {
                    name: 'Severity',
                    value: message.severity,
                    inline: true
                },
                {
                    name: 'Component',
                    value: message.component,
                    inline: true
                },
                {
                    name: 'Time',
                    value: message.timestamp,
                    inline: false
                }
            ],
            timestamp: new Date().toISOString()
        }];
    }

    /**
     * Build Teams facts
     */
    buildTeamsFacts(message) {
        return [
            {
                name: 'Severity',
                value: message.severity
            },
            {
                name: 'Component',
                value: message.component
            },
            {
                name: 'Time',
                value: message.timestamp
            }
        ];
    }

    /**
     * Get default channels for priority
     */
    getDefaultChannelsForPriority(priority) {
        switch (priority) {
            case 'low':
                return ['slack'];
            case 'normal':
                return ['slack', 'email'];
            case 'high':
                return ['slack', 'email', 'webhook'];
            case 'critical':
                return ['slack', 'email', 'sms', 'webhook', 'teams'];
            default:
                return ['slack'];
        }
    }

    /**
     * Rate limiting
     */
    isRateLimited(notification) {
        for (const channel of notification.channels) {
            const key = `${channel}_${Math.floor(Date.now() / 60000)}`; // per minute
            const count = this.rateLimiter.get(key) || 0;

            if (count >= this.config.rateLimit.maxPerMinute) {
                return true;
            }
        }
        return false;
    }

    updateRateLimit(channel) {
        const key = `${channel}_${Math.floor(Date.now() / 60000)}`;
        const count = this.rateLimiter.get(key) || 0;
        this.rateLimiter.set(key, count + 1);
    }

    /**
     * Utility methods
     */
    generateId() {
        return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    convertToHtml(text) {
        return text.replace(/\n/g, '<br>');
    }

    truncateForSMS(text, maxLength = 160) {
        return text.length > maxLength ? text.substring(0, maxLength - 3) + '...' : text;
    }

    getColorForSeverity(severity) {
        const colors = {
            info: '#36a64f',
            warning: '#ff9500',
            critical: '#ff0000',
            low: '#36a64f',
            normal: '#ff9500',
            high: '#ff6600',
            critical: '#ff0000'
        };
        return colors[severity] || '#cccccc';
    }

    getColorCodeForSeverity(severity) {
        const colors = {
            info: 0x36a64f,
            warning: 0xff9500,
            critical: 0xff0000,
            low: 0x36a64f,
            normal: 0xff9500,
            high: 0xff6600,
            critical: 0xff0000
        };
        return colors[severity] || 0xcccccc;
    }

    /**
     * Get service status
     */
    getStatus() {
        return {
            transports: Array.from(this.transports.keys()),
            queueLength: this.messageQueue.length,
            isProcessing: this.isProcessing,
            rateLimits: Object.fromEntries(this.rateLimiter)
        };
    }

    /**
     * Send test notification
     */
    async sendTestNotification(channel) {
        const testMessage = {
            type: 'test',
            title: 'Test Notification',
            content: 'This is a test notification from the AI Trading Platform monitoring system.',
            severity: 'info',
            component: 'notification_service',
            timestamp: new Date().toISOString()
        };

        return await this.sendNotification(testMessage, [channel], 'low');
    }

    /**
     * Clean up old rate limit data
     */
    cleanupRateLimits() {
        const currentMinute = Math.floor(Date.now() / 60000);
        for (const [key] of this.rateLimiter) {
            const keyMinute = parseInt(key.split('_').pop());
            if (currentMinute - keyMinute > 60) { // Keep last hour
                this.rateLimiter.delete(key);
            }
        }
    }
}

module.exports = NotificationService;