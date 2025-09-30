/**
 * Component Subscriber - Client-side Hot Reload System
 * Subscribes to component updates and reloads modules automatically
 */

const fs = require('fs').promises;
const path = require('path');
const EventEmitter = require('events');

class ComponentSubscriber extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            service_name: options.service_name || 'unknown-service',
            nats_client: options.nats_client || null,
            component_cache_dir: options.component_cache_dir || path.join(process.cwd(), '.component_cache'),
            central_hub_url: options.central_hub_url || 'http://suho-central-hub:7000',
            auto_reload: options.auto_reload !== false, // Default true
            version_check_interval: options.version_check_interval || 30000, // 30s
            retry_attempts: options.retry_attempts || 3,
            retry_delay: options.retry_delay || 5000,
            ...options
        };

        // Component management
        this.loaded_components = new Map(); // path -> module
        this.component_versions = new Map(); // path -> version
        this.subscriptions = new Set();
        this.version_check_timer = null;
        this.is_shutting_down = false;

        this.logger = options.logger || console;
    }

    async initialize() {
        this.logger.info(`🔄 Initializing Component Subscriber for ${this.config.service_name}...`);

        try {
            // Ensure cache directory exists
            await this.ensureCacheDirectory();

            // Load existing component versions
            await this.loadLocalVersions();

            // Setup NATS subscriber
            if (this.config.nats_client) {
                await this.setupNATSSubscriber();
            }

            // Start version check timer
            if (this.config.version_check_interval > 0) {
                this.startVersionChecker();
            }

            this.logger.info(`✅ Component Subscriber initialized for ${this.config.service_name}`);

        } catch (error) {
            this.logger.error(`❌ Component Subscriber initialization failed: ${error.message}`);
            throw error;
        }
    }

    async ensureCacheDirectory() {
        try {
            await fs.mkdir(this.config.component_cache_dir, { recursive: true });
            this.logger.debug(`📁 Component cache directory: ${this.config.component_cache_dir}`);
        } catch (error) {
            this.logger.error(`❌ Failed to create cache directory: ${error.message}`);
            throw error;
        }
    }

    async setupNATSSubscriber() {
        if (!this.config.nats_client) {
            throw new Error('NATS client required for component subscription');
        }

        this.logger.info('📡 Setting up NATS subscriber for component updates...');

        try {
            // Subscribe to all component updates
            const subscription = await this.config.nats_client.subscribe('suho.components.update.*');
            this.subscriptions.add(subscription);

            // Process updates
            (async () => {
                for await (const msg of subscription) {
                    if (this.is_shutting_down) break;

                    try {
                        await this.handleComponentUpdate(msg);
                    } catch (error) {
                        this.logger.error(`❌ Failed to handle component update: ${error.message}`);
                    }
                }
            })();

            this.logger.info('📡 NATS component subscriber active');

        } catch (error) {
            this.logger.error(`❌ Failed to setup NATS subscriber: ${error.message}`);
            throw error;
        }
    }

    async handleComponentUpdate(msg) {
        try {
            const update = JSON.parse(msg.data);
            const component_path = update.component?.path;

            if (!component_path) {
                this.logger.warn('⚠️ Received component update without path');
                return;
            }

            this.logger.info(`📥 Received component update: ${component_path} (v${update.component.version})`);

            // Check if we need this component
            const current_version = this.component_versions.get(component_path);
            const new_version = update.component.version;

            if (current_version === new_version) {
                this.logger.debug(`⏭️ Component ${component_path} already up to date`);
                return;
            }

            // Handle component deletion
            if (update.type === 'component_deleted') {
                await this.handleComponentDeletion(component_path);
                return;
            }

            // Update component
            await this.updateComponent(component_path, update);

        } catch (error) {
            this.logger.error(`❌ Failed to process component update: ${error.message}`);
        }
    }

    async updateComponent(component_path, update) {
        try {
            const component = update.component;
            const content = update.content;

            // Decompress content if needed
            const actual_content = typeof content === 'string' && update.compressed ?
                Buffer.from(content, 'base64').toString('utf8') : content;

            // Save to cache
            const cache_file = path.join(this.config.component_cache_dir, component_path);
            const cache_dir = path.dirname(cache_file);

            await fs.mkdir(cache_dir, { recursive: true });
            await fs.writeFile(cache_file, actual_content);

            // Update version tracking
            this.component_versions.set(component_path, component.version);

            // Reload module if auto-reload enabled
            if (this.config.auto_reload && this.loaded_components.has(component_path)) {
                await this.reloadComponent(component_path, cache_file);
            }

            this.logger.info(`🔄 Component updated: ${component_path} (v${component.version})`);

            // Emit update event
            this.emit('component_updated', {
                path: component_path,
                version: component.version,
                cache_file: cache_file
            });

        } catch (error) {
            this.logger.error(`❌ Failed to update component ${component_path}: ${error.message}`);
            throw error;
        }
    }

    async reloadComponent(component_path, cache_file) {
        try {
            // Clear module from require cache
            const absolute_cache_file = path.resolve(cache_file);
            delete require.cache[absolute_cache_file];

            // Reload module
            const new_module = require(absolute_cache_file);
            this.loaded_components.set(component_path, new_module);

            this.logger.info(`🔃 Module reloaded: ${component_path}`);

            // Emit reload event
            this.emit('component_reloaded', {
                path: component_path,
                module: new_module,
                cache_file: cache_file
            });

        } catch (error) {
            this.logger.error(`❌ Failed to reload component ${component_path}: ${error.message}`);

            // Keep old version on reload failure
            this.emit('component_reload_failed', {
                path: component_path,
                error: error.message
            });
        }
    }

    async handleComponentDeletion(component_path) {
        try {
            // Remove from cache
            const cache_file = path.join(this.config.component_cache_dir, component_path);
            try {
                await fs.unlink(cache_file);
            } catch (error) {
                // File might not exist
            }

            // Remove from tracking
            this.component_versions.delete(component_path);
            this.loaded_components.delete(component_path);

            // Clear from require cache
            const absolute_cache_file = path.resolve(cache_file);
            delete require.cache[absolute_cache_file];

            this.logger.info(`🗑️ Component deleted: ${component_path}`);

            // Emit deletion event
            this.emit('component_deleted', { path: component_path });

        } catch (error) {
            this.logger.error(`❌ Failed to handle component deletion ${component_path}: ${error.message}`);
        }
    }

    async loadComponent(component_path, fallback_path = null) {
        try {
            // Check if component is in cache
            const cache_file = path.join(this.config.component_cache_dir, component_path);
            const cache_exists = await this.fileExists(cache_file);

            let module_to_load;

            if (cache_exists) {
                // Load from cache
                module_to_load = require(path.resolve(cache_file));
                this.logger.debug(`📦 Loaded component from cache: ${component_path}`);
            } else if (fallback_path && await this.fileExists(fallback_path)) {
                // Load from fallback (static copy)
                module_to_load = require(path.resolve(fallback_path));
                this.logger.debug(`📦 Loaded component from fallback: ${component_path}`);

                // Request fresh component from Central Hub
                await this.requestComponent(component_path);
            } else {
                // Request component from Central Hub
                module_to_load = await this.requestComponent(component_path);
            }

            // Track loaded component
            this.loaded_components.set(component_path, module_to_load);

            return module_to_load;

        } catch (error) {
            this.logger.error(`❌ Failed to load component ${component_path}: ${error.message}`);

            // Try fallback if available
            if (fallback_path) {
                try {
                    const fallback_module = require(path.resolve(fallback_path));
                    this.logger.warn(`⚠️ Using fallback for ${component_path}`);
                    return fallback_module;
                } catch (fallback_error) {
                    this.logger.error(`❌ Fallback also failed: ${fallback_error.message}`);
                }
            }

            throw error;
        }
    }

    async requestComponent(component_path) {
        if (!this.config.nats_client) {
            throw new Error('NATS client required for component requests');
        }

        try {
            const request_subject = `suho.components.request.${component_path.replace(/\//g, '.')}`;
            const response = await this.config.nats_client.request(request_subject, '', { timeout: 10000 });

            const data = JSON.parse(response.data);

            if (!data.found) {
                throw new Error(`Component not found: ${component_path}`);
            }

            // Save to cache
            const cache_file = path.join(this.config.component_cache_dir, component_path);
            const cache_dir = path.dirname(cache_file);

            await fs.mkdir(cache_dir, { recursive: true });
            await fs.writeFile(cache_file, data.component.content);

            // Update version tracking
            this.component_versions.set(component_path, data.component.version);

            // Load module
            const module_obj = require(path.resolve(cache_file));

            this.logger.info(`📥 Retrieved component: ${component_path} (v${data.component.version})`);

            return module_obj;

        } catch (error) {
            this.logger.error(`❌ Failed to request component ${component_path}: ${error.message}`);
            throw error;
        }
    }

    startVersionChecker() {
        if (this.version_check_timer) {
            clearInterval(this.version_check_timer);
        }

        this.version_check_timer = setInterval(async () => {
            if (this.is_shutting_down) return;

            try {
                await this.checkComponentVersions();
            } catch (error) {
                this.logger.error(`❌ Version check failed: ${error.message}`);
            }
        }, this.config.version_check_interval);

        this.logger.info(`⏰ Version checker started (${this.config.version_check_interval}ms interval)`);
    }

    async checkComponentVersions() {
        // This could poll Central Hub for version manifest
        // For now, rely on NATS push notifications
        this.logger.debug('🔍 Checking component versions...');
    }

    async loadLocalVersions() {
        // Load any cached version information
        try {
            const version_file = path.join(this.config.component_cache_dir, 'versions.json');
            const content = await fs.readFile(version_file, 'utf8');
            const data = JSON.parse(content);

            for (const [path, version] of Object.entries(data.versions || {})) {
                this.component_versions.set(path, version);
            }

            this.logger.info(`📄 Loaded ${this.component_versions.size} cached component versions`);

        } catch (error) {
            this.logger.debug('📄 No cached versions found');
        }
    }

    async saveLocalVersions() {
        try {
            const version_file = path.join(this.config.component_cache_dir, 'versions.json');
            const data = {
                service: this.config.service_name,
                last_updated: new Date().toISOString(),
                versions: Object.fromEntries(this.component_versions)
            };

            await fs.writeFile(version_file, JSON.stringify(data, null, 2));
            this.logger.debug('💾 Saved local component versions');

        } catch (error) {
            this.logger.error(`❌ Failed to save local versions: ${error.message}`);
        }
    }

    async fileExists(file_path) {
        try {
            await fs.access(file_path);
            return true;
        } catch {
            return false;
        }
    }

    // Public API
    getLoadedComponents() {
        return Array.from(this.loaded_components.keys());
    }

    getComponentVersions() {
        return Object.fromEntries(this.component_versions);
    }

    isComponentLoaded(component_path) {
        return this.loaded_components.has(component_path);
    }

    // Cleanup
    async shutdown() {
        this.logger.info('🛑 Shutting down Component Subscriber...');
        this.is_shutting_down = true;

        // Stop version checker
        if (this.version_check_timer) {
            clearInterval(this.version_check_timer);
        }

        // Close NATS subscriptions
        for (const subscription of this.subscriptions) {
            try {
                subscription.unsubscribe();
            } catch (error) {
                this.logger.error(`❌ Failed to unsubscribe: ${error.message}`);
            }
        }

        // Save local versions
        await this.saveLocalVersions();

        this.removeAllListeners();
        this.logger.info('✅ Component Subscriber shutdown complete');
    }
}

module.exports = {
    ComponentSubscriber
};