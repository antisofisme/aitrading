/**
 * Centralized Monitoring Configuration
 * Manages all monitoring system configurations with environment-based overrides
 */
class MonitoringConfig {
    constructor(environment = 'development') {
        this.environment = environment;
        this.config = this.buildConfig();
    }

    /**
     * Build complete monitoring configuration
     */
    buildConfig() {
        const baseConfig = this.getBaseConfig();
        const envConfig = this.getEnvironmentConfig(this.environment);

        return this.mergeConfigurations(baseConfig, envConfig);
    }

    /**
     * Base monitoring configuration
     */
    getBaseConfig() {
        return {
            // Health Monitor Configuration
            health: {
                checkInterval: 5000, // 5 seconds
                retentionPeriod: 86400000, // 24 hours
                thresholds: {
                    cpu: { warning: 70, critical: 85 },
                    memory: { warning: 80, critical: 90 },
                    disk: { warning: 85, critical: 95 },
                    latency: { warning: 100, critical: 500 },
                    errorRate: { warning: 5, critical: 10 },
                    responseTime: { warning: 200, critical: 1000 }
                },
                components: {
                    'system.cpu': { enabled: true, timeout: 5000 },
                    'system.memory': { enabled: true, timeout: 5000 },
                    'system.disk': { enabled: true, timeout: 5000 },
                    'system.uptime': { enabled: true, timeout: 1000 },
                    'app.database': { enabled: true, timeout: 10000 },
                    'app.trading_engine': { enabled: true, timeout: 5000 },
                    'app.market_data': { enabled: true, timeout: 3000 },
                    'app.risk_manager': { enabled: true, timeout: 5000 },
                    'performance.latency': { enabled: true, timeout: 5000 },
                    'performance.throughput': { enabled: true, timeout: 5000 },
                    'performance.error_rate': { enabled: true, timeout: 5000 }
                }
            },

            // Metrics Collector Configuration
            metrics: {
                aggregationInterval: 60000, // 1 minute
                retentionPeriod: 604800000, // 7 days
                batchSize: 1000,
                enableRealTime: true,
                exportFormats: ['prometheus', 'json'],
                storage: {
                    type: 'memory', // memory, redis, influxdb
                    config: {}
                },
                customMetrics: {
                    trading: {
                        'trades.executed': { type: 'counter', description: 'Total trades executed' },
                        'trades.profitable': { type: 'counter', description: 'Profitable trades' },
                        'trades.losses': { type: 'counter', description: 'Loss-making trades' },
                        'orders.placed': { type: 'counter', description: 'Orders placed' },
                        'orders.filled': { type: 'counter', description: 'Orders filled' },
                        'orders.cancelled': { type: 'counter', description: 'Orders cancelled' },
                        'trading.portfolio_value': { type: 'gauge', description: 'Current portfolio value' },
                        'trading.unrealized_pnl': { type: 'gauge', description: 'Unrealized P&L' },
                        'trading.realized_pnl': { type: 'gauge', description: 'Realized P&L' },
                        'trading.active_positions': { type: 'gauge', description: 'Active positions count' }
                    },
                    system: {
                        'system.cpu_usage': { type: 'gauge', description: 'CPU usage percentage' },
                        'system.memory_usage': { type: 'gauge', description: 'Memory usage percentage' },
                        'system.active_connections': { type: 'gauge', description: 'Active connections' }
                    },
                    risk: {
                        'risk.exposure_ratio': { type: 'gauge', description: 'Risk exposure ratio' },
                        'risk.var_estimate': { type: 'gauge', description: 'Value at Risk estimate' }
                    }
                }
            },

            // Alert Manager Configuration
            alerts: {
                channels: ['console', 'email', 'slack'],
                escalationDelays: [300000, 900000, 3600000], // 5min, 15min, 1hr
                retryAttempts: 3,
                retryDelay: 5000,
                deduplicationWindow: 300000, // 5 minutes
                maxAlertsPerHour: 100,
                severityChannels: {
                    info: ['console'],
                    warning: ['console', 'slack'],
                    critical: ['console', 'email', 'slack', 'sms']
                },
                templates: {
                    email: {
                        subject: '[{{severity}}] AI Trading Platform Alert: {{component}}',
                        html: this.getEmailTemplate(),
                        text: '[{{severity}}] {{component}}: {{message}} at {{timestamp}}'
                    },
                    slack: {
                        text: ':warning: AI Trading Platform Alert',
                        blocks: []
                    }
                }
            },

            // Dashboard Configuration
            dashboard: {
                port: 3001,
                host: 'localhost',
                enableAuth: false,
                refreshInterval: 5000,
                maxDataPoints: 1000,
                themes: ['dark', 'light'],
                layout: {
                    grid: { columns: 12, rows: 'auto' },
                    widgets: [
                        {
                            id: 'system-health',
                            type: 'status',
                            position: { x: 0, y: 0, w: 6, h: 4 },
                            config: { component: 'system' }
                        },
                        {
                            id: 'trading-performance',
                            type: 'chart',
                            position: { x: 6, y: 0, w: 6, h: 4 },
                            config: { metric: 'trading.pnl', timeRange: '24h' }
                        },
                        {
                            id: 'alerts-summary',
                            type: 'alerts',
                            position: { x: 0, y: 4, w: 4, h: 4 },
                            config: { showActive: true, limit: 10 }
                        },
                        {
                            id: 'metrics-overview',
                            type: 'metrics',
                            position: { x: 4, y: 4, w: 8, h: 4 },
                            config: { categories: ['trading', 'system', 'risk'] }
                        }
                    ]
                }
            },

            // Notification Service Configuration
            notifications: {
                channels: {
                    email: null, // Set in environment config
                    slack: null, // Set in environment config
                    sms: null,   // Set in environment config
                    webhook: null, // Set in environment config
                    discord: null, // Set in environment config
                    teams: null    // Set in environment config
                },
                retryAttempts: 3,
                retryDelay: 5000,
                rateLimit: {
                    maxPerMinute: 60,
                    maxPerHour: 500
                },
                templates: {
                    trading: {
                        tradeExecuted: {
                            title: 'Trade Executed',
                            priority: 'normal'
                        },
                        riskAlert: {
                            title: 'Risk Alert',
                            priority: 'high'
                        },
                        systemError: {
                            title: 'System Error',
                            priority: 'critical'
                        }
                    }
                }
            },

            // Log Aggregator Configuration
            logs: {
                logDirectory: './logs',
                retentionDays: 30,
                maxFileSize: 100 * 1024 * 1024, // 100MB
                compressionEnabled: true,
                realTimeAnalysis: true,
                alertThresholds: {
                    errorRate: 10, // errors per minute
                    warningRate: 50, // warnings per minute
                    diskUsage: 85 // percentage
                },
                sources: [
                    { name: 'application', path: './logs/app.log', type: 'file' },
                    { name: 'error', path: './logs/error.log', type: 'file' },
                    { name: 'access', path: './logs/access.log', type: 'file' }
                ],
                patterns: {
                    error: [/ERROR/i, /FATAL/i, /EXCEPTION/i, /CRITICAL/i, /FAILED/i],
                    warning: [/WARN/i, /WARNING/i, /DEPRECATED/i, /TIMEOUT/i],
                    security: [/UNAUTHORIZED/i, /FORBIDDEN/i, /AUTHENTICATION/i, /SECURITY/i],
                    performance: [/SLOW/i, /LATENCY/i, /PERFORMANCE/i, /BOTTLENECK/i]
                }
            },

            // Coordination Configuration
            coordination: {
                enableHooks: true,
                memoryNamespace: 'aitrading-monitoring',
                sessionId: `monitoring-${Date.now()}`,
                hooks: {
                    preTask: true,
                    postTask: true,
                    sessionRestore: true,
                    sessionEnd: true,
                    notify: true
                }
            }
        };
    }

    /**
     * Environment-specific configurations
     */
    getEnvironmentConfig(environment) {
        const environments = {
            development: {
                health: {
                    checkInterval: 10000, // Slower in dev
                    thresholds: {
                        cpu: { warning: 80, critical: 95 }, // More lenient in dev
                        memory: { warning: 90, critical: 95 }
                    }
                },
                dashboard: {
                    enableAuth: false,
                    host: 'localhost'
                },
                logs: {
                    realTimeAnalysis: true,
                    alertThresholds: {
                        errorRate: 20, // More lenient in dev
                        warningRate: 100
                    }
                }
            },

            testing: {
                health: {
                    checkInterval: 1000, // Fast for tests
                    retentionPeriod: 300000 // 5 minutes
                },
                metrics: {
                    aggregationInterval: 5000, // 5 seconds
                    retentionPeriod: 300000 // 5 minutes
                },
                alerts: {
                    channels: ['console'], // Only console in tests
                    maxAlertsPerHour: 1000
                },
                dashboard: {
                    port: 3002, // Different port for tests
                    enableAuth: false
                },
                logs: {
                    retentionDays: 1,
                    realTimeAnalysis: false
                }
            },

            staging: {
                health: {
                    thresholds: {
                        cpu: { warning: 75, critical: 90 },
                        memory: { warning: 85, critical: 95 }
                    }
                },
                alerts: {
                    channels: ['console', 'slack'],
                    escalationDelays: [600000, 1800000] // 10min, 30min
                },
                dashboard: {
                    enableAuth: true,
                    host: '0.0.0.0'
                },
                notifications: {
                    channels: {
                        slack: {
                            webhookUrl: process.env.SLACK_WEBHOOK_URL_STAGING
                        }
                    }
                }
            },

            production: {
                health: {
                    checkInterval: 5000,
                    thresholds: {
                        cpu: { warning: 70, critical: 85 },
                        memory: { warning: 80, critical: 90 },
                        disk: { warning: 85, critical: 95 },
                        latency: { warning: 100, critical: 500 },
                        errorRate: { warning: 5, critical: 10 }
                    }
                },
                metrics: {
                    retentionPeriod: 2592000000, // 30 days
                    storage: {
                        type: 'influxdb',
                        config: {
                            url: process.env.INFLUXDB_URL,
                            token: process.env.INFLUXDB_TOKEN,
                            org: process.env.INFLUXDB_ORG,
                            bucket: 'trading-metrics'
                        }
                    }
                },
                alerts: {
                    channels: ['console', 'email', 'slack', 'webhook'],
                    maxAlertsPerHour: 50 // Stricter in production
                },
                dashboard: {
                    enableAuth: true,
                    host: '0.0.0.0',
                    auth: {
                        username: process.env.DASHBOARD_USERNAME,
                        password: process.env.DASHBOARD_PASSWORD
                    }
                },
                notifications: {
                    channels: {
                        email: {
                            smtp: {
                                host: process.env.SMTP_HOST,
                                port: parseInt(process.env.SMTP_PORT) || 587,
                                secure: false,
                                auth: {
                                    user: process.env.SMTP_USER,
                                    pass: process.env.SMTP_PASS
                                }
                            },
                            from: process.env.EMAIL_FROM,
                            to: process.env.EMAIL_TO
                        },
                        slack: {
                            webhookUrl: process.env.SLACK_WEBHOOK_URL
                        },
                        sms: {
                            accountSid: process.env.TWILIO_ACCOUNT_SID,
                            authToken: process.env.TWILIO_AUTH_TOKEN,
                            from: process.env.TWILIO_FROM,
                            to: process.env.TWILIO_TO
                        },
                        webhook: {
                            url: process.env.WEBHOOK_URL,
                            headers: {
                                'Authorization': `Bearer ${process.env.WEBHOOK_TOKEN}`
                            }
                        }
                    },
                    rateLimit: {
                        maxPerMinute: 30,
                        maxPerHour: 200
                    }
                },
                logs: {
                    retentionDays: 90,
                    maxFileSize: 500 * 1024 * 1024, // 500MB
                    compressionEnabled: true,
                    alertThresholds: {
                        errorRate: 5,
                        warningRate: 25,
                        diskUsage: 85
                    }
                }
            }
        };

        return environments[environment] || {};
    }

    /**
     * Merge configurations with deep merge
     */
    mergeConfigurations(base, override) {
        const result = JSON.parse(JSON.stringify(base));

        for (const key in override) {
            if (override.hasOwnProperty(key)) {
                if (typeof override[key] === 'object' && override[key] !== null && !Array.isArray(override[key])) {
                    result[key] = this.mergeConfigurations(result[key] || {}, override[key]);
                } else {
                    result[key] = override[key];
                }
            }
        }

        return result;
    }

    /**
     * Get email template
     */
    getEmailTemplate() {
        return `
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; color: #333; }
                    .header { background-color: #f8f9fa; padding: 20px; text-align: center; }
                    .content { padding: 20px; }
                    .alert-critical { border-left: 5px solid #dc3545; }
                    .alert-warning { border-left: 5px solid #ffc107; }
                    .alert-info { border-left: 5px solid #17a2b8; }
                    .details-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                    .details-table th, .details-table td { padding: 10px; text-align: left; border-bottom: 1px solid #dee2e6; }
                    .details-table th { background-color: #f8f9fa; }
                    .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🤖 AI Trading Platform Alert</h2>
                </div>
                <div class="content alert-{{severity}}">
                    <h3>{{title}}</h3>
                    <p><strong>Component:</strong> {{component}}</p>
                    <p><strong>Severity:</strong> {{severity}}</p>
                    <p><strong>Message:</strong> {{message}}</p>

                    <table class="details-table">
                        <tr><th>Timestamp</th><td>{{timestamp}}</td></tr>
                        {{#if value}}<tr><th>Current Value</th><td>{{value}}{{#if unit}} {{unit}}{{/if}}</td></tr>{{/if}}
                        {{#if threshold}}<tr><th>Threshold</th><td>{{threshold}}</td></tr>{{/if}}
                        {{#if source}}<tr><th>Source</th><td>{{source}}</td></tr>{{/if}}
                    </table>

                    {{#if recommendations}}
                    <h4>Recommended Actions:</h4>
                    <ul>
                        {{#each recommendations}}
                        <li>{{this}}</li>
                        {{/each}}
                    </ul>
                    {{/if}}
                </div>
                <div class="footer">
                    <p>AI Trading Platform Monitoring System | Generated at {{timestamp}}</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </body>
            </html>
        `;
    }

    /**
     * Get configuration for specific component
     */
    getComponentConfig(component) {
        return this.config[component] || {};
    }

    /**
     * Get complete configuration
     */
    getConfig() {
        return this.config;
    }

    /**
     * Update configuration
     */
    updateConfig(updates) {
        this.config = this.mergeConfigurations(this.config, updates);
        return this.config;
    }

    /**
     * Get threshold configuration for specific metric
     */
    getThreshold(metric) {
        const parts = metric.split('.');
        let current = this.config.health?.thresholds;

        for (const part of parts) {
            if (current && current[part]) {
                current = current[part];
            } else {
                return null;
            }
        }

        return current;
    }

    /**
     * Validate configuration
     */
    validateConfig() {
        const errors = [];

        // Validate required fields
        if (!this.config.health) {
            errors.push('Health monitor configuration is required');
        }

        if (!this.config.metrics) {
            errors.push('Metrics collector configuration is required');
        }

        if (!this.config.alerts) {
            errors.push('Alert manager configuration is required');
        }

        // Validate thresholds
        if (this.config.health?.thresholds) {
            for (const [metric, threshold] of Object.entries(this.config.health.thresholds)) {
                if (threshold.warning >= threshold.critical) {
                    errors.push(`Invalid threshold for ${metric}: warning must be less than critical`);
                }
            }
        }

        // Validate intervals
        if (this.config.health?.checkInterval < 1000) {
            errors.push('Health check interval must be at least 1000ms');
        }

        if (this.config.metrics?.aggregationInterval < 5000) {
            errors.push('Metrics aggregation interval must be at least 5000ms');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    /**
     * Export configuration to JSON
     */
    exportConfig() {
        return JSON.stringify(this.config, null, 2);
    }

    /**
     * Import configuration from JSON
     */
    importConfig(configJson) {
        try {
            const importedConfig = JSON.parse(configJson);
            this.config = this.mergeConfigurations(this.config, importedConfig);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}

module.exports = MonitoringConfig;