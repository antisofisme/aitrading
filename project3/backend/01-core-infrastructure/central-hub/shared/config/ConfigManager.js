/**
 * Config Manager - Centralized Configuration Management
 *
 * Environment-aware configuration management for all services:
 * - Environment variable loading
 * - Configuration validation
 * - Dynamic configuration updates
 * - Secret management
 * - Configuration caching
 */

const fs = require('fs');
const path = require('path');

class ConfigManager {
    constructor(serviceName, options = {}) {
        this.serviceName = serviceName;
        this.environment = process.env.NODE_ENV || 'development';
        this.configPath = options.configPath || path.join(process.cwd(), 'config');
        this.secretsPath = options.secretsPath || path.join(process.cwd(), 'secrets');

        // Configuration cache
        this.configCache = new Map();
        this.watchers = new Map();

        // Configuration schema for validation
        this.schema = new Map();

        // Default configuration
        this.defaults = new Map();

        // Initialize default schemas
        this.initializeDefaultSchemas();

        // Load initial configuration
        this.loadConfiguration();
    }

    /**
     * Initialize default configuration schemas
     */
    initializeDefaultSchemas() {
        // Service configuration schema
        this.addSchema('service', {
            name: { type: 'string', required: true },
            version: { type: 'string', required: true },
            port: { type: 'number', required: true, min: 1, max: 65535 },
            environment: { type: 'string', enum: ['development', 'staging', 'production'] },
            debug: { type: 'boolean', default: false },
            log_level: { type: 'string', enum: ['error', 'warn', 'info', 'debug'], default: 'info' }
        });

        // Database configuration schema
        this.addSchema('database', {
            host: { type: 'string', required: true },
            port: { type: 'number', required: true, min: 1, max: 65535 },
            database: { type: 'string', required: true },
            username: { type: 'string', required: true },
            password: { type: 'string', required: true, secret: true },
            ssl: { type: 'boolean', default: false },
            pool_size: { type: 'number', default: 10, min: 1, max: 100 },
            timeout: { type: 'number', default: 30000, min: 1000 }
        });

        // Cache configuration schema
        this.addSchema('cache', {
            type: { type: 'string', enum: ['memory', 'redis', 'memcached'], default: 'memory' },
            host: { type: 'string' },
            port: { type: 'number' },
            ttl: { type: 'number', default: 300000, min: 1000 },
            max_keys: { type: 'number', default: 1000, min: 100 }
        });

        // Transfer configuration schema
        this.addSchema('transfer', {
            nats_url: { type: 'string', default: 'nats://localhost:4222' },
            kafka_brokers: { type: 'string', default: 'localhost:9092' },
            grpc_port: { type: 'number', default: 50051, min: 1, max: 65535 },
            timeout: { type: 'number', default: 30000, min: 1000 },
            retry_attempts: { type: 'number', default: 3, min: 1, max: 10 }
        });

        // Security configuration schema
        this.addSchema('security', {
            jwt_secret: { type: 'string', required: true, secret: true },
            jwt_expires_in: { type: 'string', default: '24h' },
            bcrypt_rounds: { type: 'number', default: 12, min: 8, max: 15 },
            rate_limit: { type: 'number', default: 100, min: 1 },
            cors_origins: { type: 'array', default: ['*'] }
        });

        // Monitoring configuration schema
        this.addSchema('monitoring', {
            enabled: { type: 'boolean', default: true },
            metrics_interval: { type: 'number', default: 60000, min: 1000 },
            health_check_interval: { type: 'number', default: 30000, min: 1000 },
            error_threshold: { type: 'number', default: 0.1, min: 0, max: 1 }
        });
    }

    /**
     * Add configuration schema
     */
    addSchema(section, schema) {
        this.schema.set(section, schema);
    }

    /**
     * Set default configuration
     */
    setDefaults(section, defaults) {
        this.defaults.set(section, defaults);
    }

    /**
     * Load configuration from multiple sources
     */
    loadConfiguration() {
        try {
            // 1. Load default configuration
            this.loadDefaults();

            // 2. Load configuration files
            this.loadConfigFiles();

            // 3. Load environment variables
            this.loadEnvironmentVariables();

            // 4. Load secrets
            this.loadSecrets();

            // 5. Validate configuration
            this.validateConfiguration();

        } catch (error) {
            throw new Error(`Failed to load configuration: ${error.message}`);
        }
    }

    /**
     * Load default configuration
     */
    loadDefaults() {
        for (const [section, schema] of this.schema.entries()) {
            const sectionConfig = {};

            for (const [key, definition] of Object.entries(schema)) {
                if (definition.default !== undefined) {
                    sectionConfig[key] = definition.default;
                }
            }

            if (Object.keys(sectionConfig).length > 0) {
                this.configCache.set(section, sectionConfig);
            }
        }

        // Apply custom defaults
        for (const [section, defaults] of this.defaults.entries()) {
            const existing = this.configCache.get(section) || {};
            this.configCache.set(section, { ...existing, ...defaults });
        }
    }

    /**
     * Load configuration from files
     */
    loadConfigFiles() {
        if (!fs.existsSync(this.configPath)) {
            return;
        }

        // Load base configuration
        const baseConfigFile = path.join(this.configPath, 'config.json');
        if (fs.existsSync(baseConfigFile)) {
            const baseConfig = this.loadJsonFile(baseConfigFile);
            this.mergeConfiguration(baseConfig);
        }

        // Load environment-specific configuration
        const envConfigFile = path.join(this.configPath, `${this.environment}.json`);
        if (fs.existsSync(envConfigFile)) {
            const envConfig = this.loadJsonFile(envConfigFile);
            this.mergeConfiguration(envConfig);
        }

        // Load service-specific configuration
        const serviceConfigFile = path.join(this.configPath, `${this.serviceName}.json`);
        if (fs.existsSync(serviceConfigFile)) {
            const serviceConfig = this.loadJsonFile(serviceConfigFile);
            this.mergeConfiguration(serviceConfig);
        }
    }

    /**
     * Load environment variables
     */
    loadEnvironmentVariables() {
        // Service configuration from environment
        const serviceConfig = {
            name: process.env.SERVICE_NAME || this.serviceName,
            version: process.env.SERVICE_VERSION || '1.0.0',
            port: this.parseEnvInt('PORT', 3000),
            environment: process.env.NODE_ENV || 'development',
            debug: this.parseEnvBool('DEBUG', false),
            log_level: process.env.LOG_LEVEL || 'info'
        };

        // Database configuration from environment
        const databaseConfig = {
            host: process.env.DB_HOST,
            port: this.parseEnvInt('DB_PORT'),
            database: process.env.DB_NAME,
            username: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            ssl: this.parseEnvBool('DB_SSL'),
            pool_size: this.parseEnvInt('DB_POOL_SIZE'),
            timeout: this.parseEnvInt('DB_TIMEOUT')
        };

        // Cache configuration from environment
        const cacheConfig = {
            type: process.env.CACHE_TYPE,
            host: process.env.CACHE_HOST,
            port: this.parseEnvInt('CACHE_PORT'),
            ttl: this.parseEnvInt('CACHE_TTL'),
            max_keys: this.parseEnvInt('CACHE_MAX_KEYS')
        };

        // Transfer configuration from environment
        const transferConfig = {
            nats_url: process.env.NATS_URL,
            kafka_brokers: process.env.KAFKA_BROKERS,
            grpc_port: this.parseEnvInt('GRPC_PORT'),
            timeout: this.parseEnvInt('TRANSFER_TIMEOUT'),
            retry_attempts: this.parseEnvInt('TRANSFER_RETRY_ATTEMPTS')
        };

        // Security configuration from environment
        const securityConfig = {
            jwt_secret: process.env.JWT_SECRET,
            jwt_expires_in: process.env.JWT_EXPIRES_IN,
            bcrypt_rounds: this.parseEnvInt('BCRYPT_ROUNDS'),
            rate_limit: this.parseEnvInt('RATE_LIMIT'),
            cors_origins: this.parseEnvArray('CORS_ORIGINS')
        };

        // Monitoring configuration from environment
        const monitoringConfig = {
            enabled: this.parseEnvBool('MONITORING_ENABLED'),
            metrics_interval: this.parseEnvInt('METRICS_INTERVAL'),
            health_check_interval: this.parseEnvInt('HEALTH_CHECK_INTERVAL'),
            error_threshold: this.parseEnvFloat('ERROR_THRESHOLD')
        };

        // Merge configurations (only if values are defined)
        this.mergeConfigurationSection('service', serviceConfig);
        this.mergeConfigurationSection('database', databaseConfig);
        this.mergeConfigurationSection('cache', cacheConfig);
        this.mergeConfigurationSection('transfer', transferConfig);
        this.mergeConfigurationSection('security', securityConfig);
        this.mergeConfigurationSection('monitoring', monitoringConfig);
    }

    /**
     * Load secrets from files
     */
    loadSecrets() {
        if (!fs.existsSync(this.secretsPath)) {
            return;
        }

        // Load secrets from individual files
        const secretFiles = fs.readdirSync(this.secretsPath);

        for (const file of secretFiles) {
            if (file.endsWith('.secret')) {
                const secretName = file.replace('.secret', '');
                const secretValue = fs.readFileSync(path.join(this.secretsPath, file), 'utf8').trim();

                // Apply secret to configuration
                this.applySecret(secretName, secretValue);
            }
        }
    }

    /**
     * Apply secret to configuration
     */
    applySecret(secretName, secretValue) {
        // Map common secret names to configuration paths
        const secretMapping = {
            'jwt_secret': ['security', 'jwt_secret'],
            'db_password': ['database', 'password'],
            'cache_password': ['cache', 'password'],
            'api_key': ['security', 'api_key']
        };

        const mapping = secretMapping[secretName];
        if (mapping) {
            const [section, key] = mapping;
            const sectionConfig = this.configCache.get(section) || {};
            sectionConfig[key] = secretValue;
            this.configCache.set(section, sectionConfig);
        }
    }

    /**
     * Validate configuration against schemas
     */
    validateConfiguration() {
        for (const [section, schema] of this.schema.entries()) {
            const config = this.configCache.get(section) || {};
            this.validateSection(section, config, schema);
        }
    }

    /**
     * Validate configuration section
     */
    validateSection(section, config, schema) {
        for (const [key, definition] of Object.entries(schema)) {
            const value = config[key];

            // Check required fields
            if (definition.required && (value === undefined || value === null)) {
                throw new Error(`Required configuration missing: ${section}.${key}`);
            }

            // Skip validation if value is undefined and not required
            if (value === undefined) {
                continue;
            }

            // Validate type
            if (definition.type && !this.validateType(value, definition.type)) {
                throw new Error(`Invalid type for ${section}.${key}: expected ${definition.type}, got ${typeof value}`);
            }

            // Validate enum values
            if (definition.enum && !definition.enum.includes(value)) {
                throw new Error(`Invalid value for ${section}.${key}: ${value} not in [${definition.enum.join(', ')}]`);
            }

            // Validate min/max for numbers
            if (definition.type === 'number') {
                if (definition.min !== undefined && value < definition.min) {
                    throw new Error(`Value too small for ${section}.${key}: ${value} < ${definition.min}`);
                }
                if (definition.max !== undefined && value > definition.max) {
                    throw new Error(`Value too large for ${section}.${key}: ${value} > ${definition.max}`);
                }
            }
        }
    }

    /**
     * Validate value type
     */
    validateType(value, expectedType) {
        switch (expectedType) {
            case 'string':
                return typeof value === 'string';
            case 'number':
                return typeof value === 'number' && !isNaN(value);
            case 'boolean':
                return typeof value === 'boolean';
            case 'array':
                return Array.isArray(value);
            case 'object':
                return typeof value === 'object' && value !== null && !Array.isArray(value);
            default:
                return true;
        }
    }

    /**
     * Get configuration value
     */
    get(section, key = null) {
        if (key === null) {
            return this.configCache.get(section) || {};
        }

        const sectionConfig = this.configCache.get(section) || {};
        return sectionConfig[key];
    }

    /**
     * Set configuration value
     */
    set(section, key, value) {
        const sectionConfig = this.configCache.get(section) || {};
        sectionConfig[key] = value;
        this.configCache.set(section, sectionConfig);
    }

    /**
     * Get all configuration
     */
    getAll() {
        const config = {};
        for (const [section, sectionConfig] of this.configCache.entries()) {
            config[section] = { ...sectionConfig };
        }
        return config;
    }

    /**
     * Get configuration with secrets masked
     */
    getAllSafe() {
        const config = this.getAll();

        // Mask secrets
        for (const [section, schema] of this.schema.entries()) {
            const sectionConfig = config[section];
            if (!sectionConfig) continue;

            for (const [key, definition] of Object.entries(schema)) {
                if (definition.secret && sectionConfig[key]) {
                    sectionConfig[key] = '***masked***';
                }
            }
        }

        return config;
    }

    /**
     * Watch configuration file for changes
     */
    watchConfigFile(filePath, callback) {
        if (this.watchers.has(filePath)) {
            return;
        }

        if (!fs.existsSync(filePath)) {
            return;
        }

        const watcher = fs.watchFile(filePath, { interval: 1000 }, (current, previous) => {
            if (current.mtime > previous.mtime) {
                try {
                    this.loadConfiguration();
                    callback(null, this.getAll());
                } catch (error) {
                    callback(error, null);
                }
            }
        });

        this.watchers.set(filePath, watcher);
    }

    /**
     * Stop watching configuration files
     */
    stopWatching() {
        for (const [filePath, watcher] of this.watchers.entries()) {
            fs.unwatchFile(filePath);
        }
        this.watchers.clear();
    }

    /**
     * Utility methods
     */
    loadJsonFile(filePath) {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            return JSON.parse(content);
        } catch (error) {
            throw new Error(`Failed to load JSON file ${filePath}: ${error.message}`);
        }
    }

    mergeConfiguration(config) {
        for (const [section, sectionConfig] of Object.entries(config)) {
            const existing = this.configCache.get(section) || {};
            this.configCache.set(section, { ...existing, ...sectionConfig });
        }
    }

    mergeConfigurationSection(section, config) {
        const filtered = {};
        for (const [key, value] of Object.entries(config)) {
            if (value !== undefined && value !== null) {
                filtered[key] = value;
            }
        }

        if (Object.keys(filtered).length > 0) {
            const existing = this.configCache.get(section) || {};
            this.configCache.set(section, { ...existing, ...filtered });
        }
    }

    parseEnvInt(envVar, defaultValue = undefined) {
        const value = process.env[envVar];
        if (value === undefined) return defaultValue;
        const parsed = parseInt(value, 10);
        return isNaN(parsed) ? defaultValue : parsed;
    }

    parseEnvFloat(envVar, defaultValue = undefined) {
        const value = process.env[envVar];
        if (value === undefined) return defaultValue;
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    }

    parseEnvBool(envVar, defaultValue = undefined) {
        const value = process.env[envVar];
        if (value === undefined) return defaultValue;
        return value.toLowerCase() === 'true' || value === '1';
    }

    parseEnvArray(envVar, defaultValue = undefined) {
        const value = process.env[envVar];
        if (value === undefined) return defaultValue;
        return value.split(',').map(item => item.trim());
    }

    /**
     * Health check
     */
    async healthCheck() {
        return {
            status: 'operational',
            sectionsLoaded: this.configCache.size,
            schemasLoaded: this.schema.size,
            environment: this.environment,
            watchersActive: this.watchers.size
        };
    }
}

module.exports = ConfigManager;