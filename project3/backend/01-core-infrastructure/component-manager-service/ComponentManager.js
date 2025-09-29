/**
 * Component Manager - Event-Driven Hot Reload System
 * Manages shared component versioning and distribution via NATS/EventStream
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const EventEmitter = require('events');
const chokidar = require('chokidar');

// Component versioning and distribution
class ComponentManager extends EventEmitter {
    constructor(options = {}) {
        super();

        this.config = {
            shared_root: options.shared_root || path.join(__dirname, '../../'),
            nats_client: options.nats_client || null,
            version_file: options.version_file || 'component_versions.json',
            watch_patterns: options.watch_patterns || ['**/*.js', '!**/node_modules/**', '!**/test-*.js'],
            debounce_ms: options.debounce_ms || 500,
            enable_compression: options.enable_compression || true,
            ...options
        };

        // Component registry
        this.components = new Map();
        this.versions = new Map();
        this.file_watcher = null;
        this.subscribers = new Set();

        // Debounce mechanism for file changes
        this.change_timers = new Map();

        this.logger = options.logger || console;
    }

    async initialize() {
        this.logger.info('🔄 Initializing Component Manager for hot reload...');

        try {
            // Load existing component versions
            await this.loadVersions();

            // Scan all shared components
            await this.scanComponents();

            // Setup file system watcher
            await this.setupFileWatcher();

            // Setup NATS publisher
            if (this.config.nats_client) {
                await this.setupNATSPublisher();
            }

            this.logger.info(`✅ Component Manager initialized with ${this.components.size} components`);

        } catch (error) {
            this.logger.error(`❌ Component Manager initialization failed: ${error.message}`);
            throw error;
        }
    }

    async scanComponents() {
        const component_root = this.config.shared_root;

        try {
            const files = await this.getAllJSFiles(component_root);

            for (const file_path of files) {
                await this.processComponent(file_path);
            }

            this.logger.info(`📦 Scanned ${files.length} component files`);

        } catch (error) {
            this.logger.error(`❌ Component scan failed: ${error.message}`);
            throw error;
        }
    }

    async processComponent(file_path) {
        try {
            const relative_path = path.relative(this.config.shared_root, file_path);
            const content = await fs.readFile(file_path, 'utf8');
            const hash = this.generateHash(content);
            const stats = await fs.stat(file_path);

            const component = {
                path: relative_path,
                absolute_path: file_path,
                hash: hash,
                content: content,
                size: stats.size,
                modified: stats.mtime.toISOString(),
                version: this.generateVersion(relative_path, hash)
            };

            // Check if component changed
            const existing = this.components.get(relative_path);
            const has_changed = !existing || existing.hash !== hash;

            this.components.set(relative_path, component);
            this.versions.set(relative_path, component.version);

            if (has_changed) {
                this.logger.info(`🔄 Component updated: ${relative_path} (v${component.version})`);
                await this.publishComponentUpdate(component);
            }

            return component;

        } catch (error) {
            this.logger.error(`❌ Failed to process component ${file_path}: ${error.message}`);
            throw error;
        }
    }

    async setupFileWatcher() {
        const watch_root = this.config.shared_root;
        const patterns = this.config.watch_patterns.map(pattern => path.join(watch_root, pattern));

        this.file_watcher = chokidar.watch(patterns, {
            ignored: ['**/node_modules/**', '**/.git/**', '**/test-*.js'],
            persistent: true,
            ignoreInitial: true,
            usePolling: true,
            interval: 1000,
            binaryInterval: 3000
        });

        this.file_watcher.on('change', (file_path) => {
            const relative_path = path.relative(watch_root, file_path);
            this.debounceChange(relative_path, 'change');
        });

        this.file_watcher.on('add', (file_path) => {
            const relative_path = path.relative(watch_root, file_path);
            this.debounceChange(relative_path, 'add');
        });

        this.file_watcher.on('unlink', (file_path) => {
            const relative_path = path.relative(watch_root, file_path);
            this.debounceChange(relative_path, 'delete');
        });

        this.logger.info(`👁️ File watcher setup for ${watch_root}`);
    }

    debounceChange(relative_path, change_type) {
        const key = `${relative_path}:${change_type}`;

        // Clear existing timer
        if (this.change_timers.has(key)) {
            clearTimeout(this.change_timers.get(key));
        }

        // Set debounced handler
        const timer = setTimeout(async () => {
            try {
                this.change_timers.delete(key);
                await this.handleFileChange(relative_path, change_type);
            } catch (error) {
                this.logger.error(`❌ File change handler failed: ${error.message}`);
            }
        }, this.config.debounce_ms);

        this.change_timers.set(key, timer);
    }

    async handleFileChange(relative_path, change_type) {
        const absolute_path = path.join(this.config.shared_root, relative_path);

        this.logger.info(`📝 File ${change_type}: ${relative_path}`);

        try {
            if (change_type === 'delete') {
                await this.handleComponentDelete(relative_path);
            } else {
                await this.processComponent(absolute_path);
            }

            // Save updated versions
            await this.saveVersions();

        } catch (error) {
            this.logger.error(`❌ Failed to handle file change ${relative_path}: ${error.message}`);
        }
    }

    async handleComponentDelete(relative_path) {
        if (this.components.has(relative_path)) {
            this.components.delete(relative_path);
            this.versions.delete(relative_path);

            const delete_event = {
                type: 'component_deleted',
                path: relative_path,
                timestamp: new Date().toISOString()
            };

            await this.publishComponentUpdate(delete_event);
            this.logger.info(`🗑️ Component deleted: ${relative_path}`);
        }
    }

    async setupNATSPublisher() {
        if (!this.config.nats_client) {
            throw new Error('NATS client required for component publishing');
        }

        this.logger.info('📡 Setting up NATS publisher for component updates...');

        // Subscribe to component requests
        const subscription = await this.config.nats_client.subscribe('suho.components.request.*');

        for await (const msg of subscription) {
            try {
                await this.handleComponentRequest(msg);
            } catch (error) {
                this.logger.error(`❌ Failed to handle component request: ${error.message}`);
            }
        }
    }

    async publishComponentUpdate(component) {
        // Emit local event
        this.emit('component_updated', component);

        // Publish via NATS if available
        if (this.config.nats_client) {
            try {
                const update_event = {
                    type: 'component_updated',
                    component: {
                        path: component.path,
                        hash: component.hash,
                        version: component.version,
                        size: component.size,
                        modified: component.modified
                    },
                    content: this.config.enable_compression ?
                        this.compressContent(component.content) : component.content,
                    timestamp: new Date().toISOString(),
                    source: 'central-hub'
                };

                await this.config.nats_client.publish(
                    `suho.components.update.${component.path.replace(/\//g, '.')}`,
                    JSON.stringify(update_event)
                );

                this.logger.info(`📡 Published component update: ${component.path} (v${component.version})`);

            } catch (error) {
                this.logger.error(`❌ Failed to publish component update: ${error.message}`);
            }
        }
    }

    async handleComponentRequest(msg) {
        const subject_parts = msg.subject.split('.');
        const requested_path = subject_parts.slice(3).join('/'); // Remove 'suho.components.request'

        if (this.components.has(requested_path)) {
            const component = this.components.get(requested_path);

            const response = {
                found: true,
                component: {
                    path: component.path,
                    hash: component.hash,
                    version: component.version,
                    size: component.size,
                    modified: component.modified,
                    content: component.content
                },
                timestamp: new Date().toISOString()
            };

            msg.respond(JSON.stringify(response));
            this.logger.info(`📤 Served component request: ${requested_path}`);

        } else {
            msg.respond(JSON.stringify({
                found: false,
                path: requested_path,
                error: 'Component not found'
            }));
        }
    }

    async getAllJSFiles(root_dir) {
        const files = [];

        async function scanDirectory(dir) {
            const entries = await fs.readdir(dir, { withFileTypes: true });

            for (const entry of entries) {
                const entry_path = path.join(dir, entry.name);

                if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
                    await scanDirectory(entry_path);
                } else if (entry.isFile() && entry.name.endsWith('.js') && !entry.name.startsWith('test-')) {
                    files.push(entry_path);
                }
            }
        }

        await scanDirectory(root_dir);
        return files;
    }

    generateHash(content) {
        return crypto.createHash('sha256').update(content).digest('hex').substring(0, 16);
    }

    generateVersion(file_path, hash) {
        // Use timestamp + hash for version
        const timestamp = Math.floor(Date.now() / 1000);
        return `${timestamp}.${hash.substring(0, 8)}`;
    }

    compressContent(content) {
        // Simple base64 encoding for now - could use gzip
        return Buffer.from(content).toString('base64');
    }

    async loadVersions() {
        const version_file = path.join(this.config.shared_root, this.config.version_file);

        try {
            const content = await fs.readFile(version_file, 'utf8');
            const data = JSON.parse(content);

            for (const [path, version] of Object.entries(data.versions || {})) {
                this.versions.set(path, version);
            }

            this.logger.info(`📄 Loaded ${this.versions.size} component versions`);

        } catch (error) {
            this.logger.info('📄 No existing version file found, starting fresh');
        }
    }

    async saveVersions() {
        const version_file = path.join(this.config.shared_root, this.config.version_file);

        const data = {
            last_updated: new Date().toISOString(),
            component_count: this.components.size,
            versions: Object.fromEntries(this.versions)
        };

        try {
            await fs.writeFile(version_file, JSON.stringify(data, null, 2));
            this.logger.debug(`💾 Saved component versions to ${version_file}`);
        } catch (error) {
            this.logger.error(`❌ Failed to save versions: ${error.message}`);
        }
    }

    // Public API for services
    getComponentInfo(component_path) {
        return this.components.get(component_path) || null;
    }

    getAllComponents() {
        return Array.from(this.components.values());
    }

    getVersions() {
        return Object.fromEntries(this.versions);
    }

    // Cleanup
    async shutdown() {
        this.logger.info('🛑 Shutting down Component Manager...');

        // Clear all timers
        for (const timer of this.change_timers.values()) {
            clearTimeout(timer);
        }
        this.change_timers.clear();

        // Close file watcher
        if (this.file_watcher) {
            await this.file_watcher.close();
        }

        // Save final versions
        await this.saveVersions();

        this.removeAllListeners();
        this.logger.info('✅ Component Manager shutdown complete');
    }
}

module.exports = {
    ComponentManager
};