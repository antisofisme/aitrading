#!/usr/bin/env node
/**
 * Component Manager Service - Standalone Hot Reload Service
 * Watches Central Hub shared components and distributes updates via NATS
 */

const { ComponentManager } = require('./ComponentManager');
const nats = require('nats');
const path = require('path');

class ComponentManagerService {
    constructor() {
        this.component_manager = null;
        this.nats_client = null;
        this.is_running = false;

        this.config = {
            service_name: 'component-manager',
            port: parseInt(process.env.PORT) || 7001,
            nats_url: process.env.NATS_URL || 'nats://suho-nats-server:4222',
            shared_root: process.env.SHARED_ROOT || '/app/shared',
            watch_enabled: process.env.WATCH_ENABLED !== 'false',
            debounce_ms: parseInt(process.env.DEBOUNCE_MS) || 500,
            log_level: process.env.LOG_LEVEL || 'info'
        };

        this.logger = {
            debug: (msg, extra) => this.log('DEBUG', msg, extra),
            info: (msg, extra) => this.log('INFO', msg, extra),
            warn: (msg, extra) => this.log('WARN', msg, extra),
            error: (msg, extra) => this.log('ERROR', msg, extra)
        };
    }

    log(level, message, extra = {}) {
        const timestamp = new Date().toISOString();
        const log_entry = {
            timestamp,
            level,
            service: this.config.service_name,
            message,
            ...extra
        };
        console.log(JSON.stringify(log_entry));
    }

    async initialize() {
        this.logger.info('🔄 Initializing Component Manager Service...');

        try {
            // Connect to NATS
            await this.connectNATS();

            // Initialize ComponentManager
            await this.setupComponentManager();

            // Setup signal handlers
            this.setupSignalHandlers();

            this.is_running = true;
            this.logger.info('✅ Component Manager Service ready', {
                shared_root: this.config.shared_root,
                nats_url: this.config.nats_url,
                watch_enabled: this.config.watch_enabled
            });

        } catch (error) {
            this.logger.error('❌ Service initialization failed', { error: error.message });
            throw error;
        }
    }

    async connectNATS() {
        try {
            this.nats_client = await nats.connect({
                servers: this.config.nats_url,
                reconnect: true,
                maxReconnectAttempts: 10,
                reconnectTimeWait: 2000,
                timeout: 10000
            });

            this.logger.info('✅ Connected to NATS', { url: this.config.nats_url });

            // Handle NATS events
            this.nats_client.closed().then(() => {
                this.logger.warn('🔌 NATS connection closed');
            });

        } catch (error) {
            this.logger.error('❌ NATS connection failed', {
                error: error.message,
                url: this.config.nats_url
            });
            throw error;
        }
    }

    async setupComponentManager() {
        try {
            this.component_manager = new ComponentManager({
                shared_root: this.config.shared_root,
                nats_client: this.nats_client,
                watch_patterns: ['**/*.js', '!**/node_modules/**', '!**/test-*.js'],
                debounce_ms: this.config.debounce_ms,
                enable_compression: true,
                logger: this.logger
            });

            await this.component_manager.initialize();

            // Setup component update handlers
            this.component_manager.on('component_updated', (component) => {
                this.logger.info('📝 Component updated', {
                    path: component.path,
                    version: component.version,
                    size: component.size
                });
            });

            this.logger.info('✅ ComponentManager initialized');

        } catch (error) {
            this.logger.error('❌ ComponentManager setup failed', { error: error.message });
            throw error;
        }
    }

    setupSignalHandlers() {
        process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
        process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));

        process.on('uncaughtException', (error) => {
            this.logger.error('💥 Uncaught Exception', { error: error.message, stack: error.stack });
            this.gracefulShutdown('uncaughtException');
        });

        process.on('unhandledRejection', (reason, promise) => {
            this.logger.error('💥 Unhandled Rejection', { reason: reason.toString() });
            this.gracefulShutdown('unhandledRejection');
        });
    }

    async gracefulShutdown(signal) {
        this.logger.info(`🛑 Received ${signal}, shutting down gracefully...`);
        this.is_running = false;

        try {
            // Shutdown ComponentManager
            if (this.component_manager) {
                await this.component_manager.shutdown();
                this.logger.info('✅ ComponentManager shutdown complete');
            }

            // Close NATS connection
            if (this.nats_client && !this.nats_client.isClosed()) {
                await this.nats_client.close();
                this.logger.info('✅ NATS connection closed');
            }

            this.logger.info('✅ Component Manager Service shutdown complete');
            process.exit(0);

        } catch (error) {
            this.logger.error('❌ Shutdown error', { error: error.message });
            process.exit(1);
        }
    }

    async healthCheck() {
        try {
            const health = {
                service: 'component-manager',
                status: 'healthy',
                timestamp: new Date().toISOString(),
                nats_connected: this.nats_client && !this.nats_client.isClosed(),
                component_manager_running: this.component_manager && this.is_running,
                config: {
                    shared_root: this.config.shared_root,
                    watch_enabled: this.config.watch_enabled,
                    nats_url: this.config.nats_url
                }
            };

            if (this.component_manager) {
                const components = this.component_manager.getAllComponents();
                const versions = this.component_manager.getVersions();

                health.metrics = {
                    total_components: components.length,
                    component_versions_count: Object.keys(versions).length,
                    last_scan: components.length > 0 ? components[0].modified : null
                };
            }

            return health;

        } catch (error) {
            return {
                service: 'component-manager',
                status: 'unhealthy',
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // API endpoints jika diperlukan
    getComponentInfo(component_path) {
        return this.component_manager ? this.component_manager.getComponentInfo(component_path) : null;
    }

    getAllComponents() {
        return this.component_manager ? this.component_manager.getAllComponents() : [];
    }

    getVersions() {
        return this.component_manager ? this.component_manager.getVersions() : {};
    }

    async rescanComponents() {
        if (this.component_manager) {
            await this.component_manager.scanComponents();
            return { success: true, message: 'Component rescan completed' };
        }
        return { success: false, message: 'ComponentManager not initialized' };
    }
}

// Main execution
async function main() {
    const service = new ComponentManagerService();

    try {
        await service.initialize();

        // Keep process alive
        process.stdin.resume();

    } catch (error) {
        console.error('❌ Failed to start Component Manager Service:', error.message);
        process.exit(1);
    }
}

// Export for testing
module.exports = { ComponentManagerService };

// Run if this is the main module
if (require.main === module) {
    main().catch((error) => {
        console.error('❌ Service startup failed:', error.message);
        process.exit(1);
    });
}