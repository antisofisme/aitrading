/**
 * Hot Reload Loader - Replaces static central-hub-shared directory
 * Dynamically loads components from Central Hub via ComponentSubscriber
 */

// ComponentSubscriber will be loaded dynamically to avoid circular dependency
let ComponentSubscriber = null;
const nats = require('nats');
const path = require('path');

class HotReloadLoader {
    constructor(options = {}) {
        this.config = {
            service_name: 'api-gateway',
            central_hub_url: options.central_hub_url || 'http://suho-central-hub:7000',
            nats_url: options.nats_url || process.env.NATS_URL || 'nats://suho-nats-server:4222',
            cache_dir: options.cache_dir || path.join(__dirname, '.hot_cache'),
            fallback_dir: options.fallback_dir || path.join(__dirname, '../central-hub/shared/components'),
            enable_fallback: options.enable_fallback !== false, // Default true for safety
            ...options
        };

        this.nats_client = null;
        this.component_subscriber = null;
        this.loaded_modules = new Map(); // path -> module
        this.is_initialized = false;

        this.logger = options.logger || console;
    }

    async initialize() {
        this.logger.info('🔄 Initializing Hot Reload Loader...');

        try {
            // Connect to NATS
            this.nats_client = await nats.connect({
                servers: this.config.nats_url,
                reconnect: true,
                maxReconnectAttempts: 10,
                reconnectTimeWait: 2000
            });

            this.logger.info(`✅ Connected to NATS: ${this.config.nats_url}`);

            // Load ComponentSubscriber dynamically
            if (!ComponentSubscriber) {
                ComponentSubscriber = require('../central-hub/shared/components/js/utils/ComponentSubscriber').ComponentSubscriber;
            }

            // Initialize ComponentSubscriber
            this.component_subscriber = new ComponentSubscriber({
                service_name: this.config.service_name,
                nats_client: this.nats_client,
                component_cache_dir: this.config.cache_dir,
                central_hub_url: this.config.central_hub_url,
                logger: this.logger
            });

            await this.component_subscriber.initialize();

            // Setup component update handlers
            this.setupUpdateHandlers();

            this.is_initialized = true;
            this.logger.info('✅ Hot Reload Loader initialized');

        } catch (error) {
            this.logger.error(`❌ Hot Reload Loader initialization failed: ${error.message}`);
            throw error;
        }
    }

    setupUpdateHandlers() {
        // Handle component updates
        this.component_subscriber.on('component_updated', (event) => {
            this.logger.info(`🔄 Component updated: ${event.path} (v${event.version})`);
        });

        // Handle component reloads
        this.component_subscriber.on('component_reloaded', (event) => {
            this.logger.info(`🔃 Component reloaded: ${event.path}`);

            // Update our loaded modules cache
            this.loaded_modules.set(event.path, event.module);

            // Emit reload event for application to handle
            this.emit('component_reloaded', event);
        });

        // Handle reload failures
        this.component_subscriber.on('component_reload_failed', (event) => {
            this.logger.error(`❌ Component reload failed: ${event.path} - ${event.error}`);

            // Emit failure event
            this.emit('component_reload_failed', event);
        });

        // Handle component deletions
        this.component_subscriber.on('component_deleted', (event) => {
            this.logger.info(`🗑️ Component deleted: ${event.path}`);

            // Remove from loaded modules
            this.loaded_modules.delete(event.path);

            // Emit deletion event
            this.emit('component_deleted', event);
        });
    }

    /**
     * Load a shared component with hot reload capability
     * @param {string} component_path - Relative path to component (e.g., 'js/utils/BaseService')
     * @returns {Object} - Loaded module
     */
    async loadComponent(component_path) {
        if (!this.is_initialized) {
            throw new Error('Hot Reload Loader not initialized');
        }

        try {
            // Normalize path
            const normalized_path = component_path.replace(/^\.\//, '').replace(/\.js$/, '') + '.js';

            // Check if already loaded and cached
            if (this.loaded_modules.has(normalized_path)) {
                this.logger.debug(`📦 Using cached component: ${normalized_path}`);
                return this.loaded_modules.get(normalized_path);
            }

            // Determine fallback path
            const fallback_path = this.config.enable_fallback ?
                path.join(this.config.fallback_dir, normalized_path) : null;

            // Load component via subscriber
            const module_obj = await this.component_subscriber.loadComponent(
                normalized_path,
                fallback_path
            );

            // Cache the loaded module
            this.loaded_modules.set(normalized_path, module_obj);

            this.logger.info(`📦 Loaded component: ${normalized_path}`);

            return module_obj;

        } catch (error) {
            this.logger.error(`❌ Failed to load component ${component_path}: ${error.message}`);
            throw error;
        }
    }

    /**
     * Create a require-like function for hot reload components
     * @param {string} base_path - Base path for relative requires
     * @returns {function} - Hot reload require function
     */
    createHotRequire(base_path = '') {
        return (module_path) => {
            // Handle relative paths
            const resolved_path = path.posix.join(base_path, module_path);

            // Return promise-based loader
            return this.loadComponent(resolved_path);
        };
    }

    /**
     * Pre-load essential components
     * @param {string[]} component_paths - Array of component paths to pre-load
     */
    async preloadComponents(component_paths) {
        this.logger.info(`🔄 Pre-loading ${component_paths.length} components...`);

        const load_promises = component_paths.map(async (component_path) => {
            try {
                await this.loadComponent(component_path);
            } catch (error) {
                this.logger.error(`❌ Failed to pre-load ${component_path}: ${error.message}`);
            }
        });

        await Promise.allSettled(load_promises);
        this.logger.info('✅ Component pre-loading complete');
    }

    /**
     * Get component version information
     */
    getComponentVersions() {
        if (!this.component_subscriber) {
            return {};
        }
        return this.component_subscriber.getComponentVersions();
    }

    /**
     * Get list of loaded components
     */
    getLoadedComponents() {
        return Array.from(this.loaded_modules.keys());
    }

    /**
     * Check if hot reload is working
     */
    async healthCheck() {
        try {
            const versions = this.getComponentVersions();
            const loaded_count = this.loaded_modules.size;
            const is_connected = this.nats_client && !this.nats_client.isClosed();

            return {
                status: 'healthy',
                hot_reload_enabled: this.is_initialized,
                nats_connected: is_connected,
                loaded_components: loaded_count,
                component_versions_count: Object.keys(versions).length,
                cache_dir: this.config.cache_dir
            };

        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message
            };
        }
    }

    /**
     * Cleanup and shutdown
     */
    async shutdown() {
        this.logger.info('🛑 Shutting down Hot Reload Loader...');

        try {
            if (this.component_subscriber) {
                await this.component_subscriber.shutdown();
            }

            if (this.nats_client && !this.nats_client.isClosed()) {
                await this.nats_client.close();
            }

            this.loaded_modules.clear();
            this.is_initialized = false;

            this.logger.info('✅ Hot Reload Loader shutdown complete');

        } catch (error) {
            this.logger.error(`❌ Hot Reload Loader shutdown error: ${error.message}`);
        }
    }
}

// Export both the class and a singleton instance
const hotReloadLoader = new HotReloadLoader();

module.exports = {
    HotReloadLoader,
    hotReloadLoader
};