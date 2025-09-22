/**
 * AI Trading Platform - Comprehensive Monitoring System
 *
 * This module provides a complete monitoring solution with:
 * - Real-time health monitoring
 * - Advanced metrics collection
 * - Intelligent alerting system
 * - Interactive dashboards
 * - Multi-channel notifications
 * - Log aggregation and analysis
 * - Configuration management
 *
 * @author AI Trading Platform Team
 * @version 1.0.0
 */

const MonitoringOrchestrator = require('./MonitoringOrchestrator');
const HealthMonitor = require('./health/HealthMonitor');
const MetricsCollector = require('./metrics/MetricsCollector');
const AlertManager = require('./alerts/AlertManager');
const DashboardServer = require('./dashboards/DashboardServer');
const NotificationService = require('./notifications/NotificationService');
const LogAggregator = require('./logs/LogAggregator');
const MonitoringConfig = require('./config/MonitoringConfig');

/**
 * Main Monitoring System Factory
 * Creates and configures the complete monitoring infrastructure
 */
class MonitoringSystem {
    constructor(environment = 'development', customConfig = {}) {
        this.environment = environment;
        this.config = new MonitoringConfig(environment);

        // Apply custom configuration overrides
        if (Object.keys(customConfig).length > 0) {
            this.config.updateConfig(customConfig);
        }

        // Validate configuration
        const validation = this.config.validateConfig();
        if (!validation.isValid) {
            throw new Error(`Invalid monitoring configuration: ${validation.errors.join(', ')}`);
        }

        this.orchestrator = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the complete monitoring system
     */
    async initialize() {
        if (this.isInitialized) {
            console.log('⚠️ Monitoring system already initialized');
            return this.orchestrator;
        }

        console.log('🚀 Initializing AI Trading Platform Monitoring System...');
        console.log(`📊 Environment: ${this.environment}`);

        try {
            // Create orchestrator with validated configuration
            this.orchestrator = new MonitoringOrchestrator(this.config.getConfig());

            // Setup global error handlers
            this.setupGlobalErrorHandlers();

            // Setup graceful shutdown
            this.setupGracefulShutdown();

            this.isInitialized = true;
            console.log('✅ Monitoring system initialized successfully');

            return this.orchestrator;
        } catch (error) {
            console.error('❌ Failed to initialize monitoring system:', error);
            throw error;
        }
    }

    /**
     * Start the monitoring system
     */
    async start() {
        if (!this.isInitialized) {
            await this.initialize();
        }

        try {
            await this.orchestrator.start();
            this.logSystemInfo();
            return this.orchestrator;
        } catch (error) {
            console.error('❌ Failed to start monitoring system:', error);
            throw error;
        }
    }

    /**
     * Stop the monitoring system
     */
    async stop() {
        if (!this.orchestrator) {
            console.log('⚠️ Monitoring system not running');
            return;
        }

        try {
            await this.orchestrator.stop();
            console.log('✅ Monitoring system stopped gracefully');
        } catch (error) {
            console.error('❌ Error stopping monitoring system:', error);
            throw error;
        }
    }

    /**
     * Get monitoring system status
     */
    getStatus() {
        if (!this.orchestrator) {
            return {
                initialized: this.isInitialized,
                running: false,
                environment: this.environment
            };
        }

        return {
            initialized: this.isInitialized,
            environment: this.environment,
            config: this.config.getConfig(),
            ...this.orchestrator.getStatus()
        };
    }

    /**
     * Get configuration
     */
    getConfig() {
        return this.config.getConfig();
    }

    /**
     * Update configuration
     */
    updateConfig(updates) {
        return this.config.updateConfig(updates);
    }

    /**
     * Setup global error handlers
     */
    setupGlobalErrorHandlers() {
        process.on('uncaughtException', (error) => {
            console.error('🚨 Uncaught Exception:', error);
            if (this.orchestrator) {
                this.orchestrator.createAlert({
                    severity: 'critical',
                    component: 'system.global',
                    message: `Uncaught exception: ${error.message}`,
                    source: 'global_error_handler',
                    metadata: { stack: error.stack }
                });
            }
        });

        process.on('unhandledRejection', (reason, promise) => {
            console.error('🚨 Unhandled Promise Rejection:', reason);
            if (this.orchestrator) {
                this.orchestrator.createAlert({
                    severity: 'critical',
                    component: 'system.global',
                    message: `Unhandled promise rejection: ${reason}`,
                    source: 'global_error_handler',
                    metadata: { promise: promise.toString() }
                });
            }
        });
    }

    /**
     * Setup graceful shutdown handlers
     */
    setupGracefulShutdown() {
        const gracefulShutdown = async (signal) => {
            console.log(`\n🛑 Received ${signal}, initiating graceful shutdown...`);

            try {
                await this.stop();
                process.exit(0);
            } catch (error) {
                console.error('❌ Error during graceful shutdown:', error);
                process.exit(1);
            }
        };

        process.on('SIGINT', () => gracefulShutdown('SIGINT'));
        process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
    }

    /**
     * Log system information
     */
    logSystemInfo() {
        const status = this.getStatus();
        const dashboardUrl = status.components?.dashboard?.url;

        console.log('\n📊 AI Trading Platform Monitoring System');
        console.log('==========================================');
        console.log(`🌍 Environment: ${this.environment}`);
        console.log(`⚡ Status: ${status.running ? 'RUNNING' : 'STOPPED'}`);
        console.log(`🕐 Started: ${status.startTime?.toISOString() || 'N/A'}`);

        if (dashboardUrl) {
            console.log(`🖥️ Dashboard: ${dashboardUrl}`);
        }

        console.log('\n📋 Components Status:');
        if (status.components) {
            console.log(`  🏥 Health Monitor: ${status.components.health?.running ? '✅ RUNNING' : '❌ STOPPED'}`);
            console.log(`  📊 Metrics Collector: ${status.components.metrics?.collecting ? '✅ COLLECTING' : '❌ STOPPED'}`);
            console.log(`  🚨 Alert Manager: ${status.components.alerts?.active !== undefined ? `✅ ACTIVE (${status.components.alerts.active} alerts)` : '❌ STOPPED'}`);
            console.log(`  🖥️ Dashboard Server: ${status.components.dashboard?.running ? '✅ RUNNING' : '❌ STOPPED'}`);
        }

        console.log('\n🔧 Key Features:');
        console.log('  • Real-time health monitoring');
        console.log('  • Advanced metrics collection');
        console.log('  • Intelligent alerting system');
        console.log('  • Interactive web dashboard');
        console.log('  • Multi-channel notifications');
        console.log('  • Log aggregation & analysis');
        console.log('  • Configuration management');
        console.log('  • Claude Flow coordination');
        console.log('==========================================\n');
    }
}

/**
 * Factory function to create monitoring system
 */
function createMonitoringSystem(environment = 'development', config = {}) {
    return new MonitoringSystem(environment, config);
}

/**
 * Quick start function for common use cases
 */
async function quickStart(options = {}) {
    const {
        environment = 'development',
        autoStart = true,
        dashboardPort = 3001,
        enableAlerts = true,
        alertChannels = ['console'],
        config = {}
    } = options;

    const quickConfig = {
        dashboard: { port: dashboardPort },
        alerts: {
            channels: enableAlerts ? alertChannels : [],
            enabled: enableAlerts
        },
        ...config
    };

    const monitoringSystem = createMonitoringSystem(environment, quickConfig);

    if (autoStart) {
        await monitoringSystem.start();
    }

    return monitoringSystem;
}

/**
 * Utility function to validate monitoring configuration
 */
function validateConfig(config, environment = 'development') {
    const configManager = new MonitoringConfig(environment);
    if (config) {
        configManager.updateConfig(config);
    }
    return configManager.validateConfig();
}

// Export all components for individual use
module.exports = {
    // Main system
    MonitoringSystem,
    createMonitoringSystem,
    quickStart,
    validateConfig,

    // Core orchestrator
    MonitoringOrchestrator,

    // Individual components
    HealthMonitor,
    MetricsCollector,
    AlertManager,
    DashboardServer,
    NotificationService,
    LogAggregator,

    // Configuration
    MonitoringConfig,

    // Utility constants
    SEVERITY_LEVELS: ['info', 'warning', 'critical'],
    ENVIRONMENTS: ['development', 'testing', 'staging', 'production'],

    // Default configurations for quick setup
    DEFAULT_CONFIGS: {
        development: {
            health: { checkInterval: 10000 },
            dashboard: { enableAuth: false },
            alerts: { channels: ['console'] }
        },
        production: {
            health: { checkInterval: 5000 },
            dashboard: { enableAuth: true },
            alerts: { channels: ['console', 'email', 'slack'] }
        }
    }
};

// CLI support for standalone execution
if (require.main === module) {
    const args = process.argv.slice(2);
    const environment = args[0] || 'development';
    const port = parseInt(args[1]) || 3001;

    console.log('🚀 Starting AI Trading Platform Monitoring System...');
    console.log(`📊 Environment: ${environment}`);
    console.log(`🖥️ Dashboard Port: ${port}`);

    quickStart({
        environment,
        dashboardPort: port,
        enableAlerts: true,
        alertChannels: ['console']
    }).then((system) => {
        console.log('✅ Monitoring system started successfully');
        console.log(`🌍 Access dashboard at: http://localhost:${port}`);
    }).catch((error) => {
        console.error('❌ Failed to start monitoring system:', error);
        process.exit(1);
    });
}