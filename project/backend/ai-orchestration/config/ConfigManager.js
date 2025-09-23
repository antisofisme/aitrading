/**
 * ConfigManager - Configuration management for AI providers with multi-tenant support
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

class ConfigManager {
    constructor(options = {}) {
        this.configDir = options.configDir || './config';
        this.encryptionKey = options.encryptionKey || this.generateKey();
        this.configs = new Map(); // tenant -> provider configs
        this.defaultConfigs = new Map(); // default provider configurations
        this.templates = new Map(); // configuration templates
        this.watchers = new Map(); // file watchers
        this.validators = new Map(); // custom validators
        this.hooks = new Map(); // configuration change hooks

        this.init();
    }

    /**
     * Initialize configuration manager
     */
    async init() {
        try {
            await fs.mkdir(this.configDir, { recursive: true });
            await this.loadDefaultConfigs();
            await this.loadTenantConfigs();
            this.setupDefaultTemplates();
        } catch (error) {
            console.error('Failed to initialize ConfigManager:', error);
        }
    }

    /**
     * Load default provider configurations
     */
    async loadDefaultConfigs() {
        const defaultConfigPath = path.join(this.configDir, 'defaults.json');

        try {
            const data = await fs.readFile(defaultConfigPath, 'utf8');
            const configs = JSON.parse(data);

            for (const [provider, config] of Object.entries(configs)) {
                this.defaultConfigs.set(provider, config);
            }
        } catch (error) {
            // Create default configuration if it doesn't exist
            await this.createDefaultConfigs();
        }
    }

    /**
     * Load tenant-specific configurations
     */
    async loadTenantConfigs() {
        try {
            const files = await fs.readdir(this.configDir);
            const tenantFiles = files.filter(f => f.startsWith('tenant-') && f.endsWith('.json'));

            for (const file of tenantFiles) {
                const tenant = file.replace('tenant-', '').replace('.json', '');
                await this.loadTenantConfig(tenant);
            }
        } catch (error) {
            console.error('Failed to load tenant configs:', error);
        }
    }

    /**
     * Load configuration for a specific tenant
     */
    async loadTenantConfig(tenant) {
        const configPath = path.join(this.configDir, `tenant-${tenant}.json`);

        try {
            const data = await fs.readFile(configPath, 'utf8');
            const encryptedConfig = JSON.parse(data);
            const decryptedConfig = this.decryptConfig(encryptedConfig);

            this.configs.set(tenant, decryptedConfig);

            // Setup file watcher
            this.setupFileWatcher(tenant, configPath);

        } catch (error) {
            console.error(`Failed to load config for tenant ${tenant}:`, error);
        }
    }

    /**
     * Get configuration for a provider/tenant combination
     */
    getConfig(provider, tenant = 'default') {
        const tenantConfigs = this.configs.get(tenant) || {};
        const providerConfig = tenantConfigs[provider];

        if (providerConfig) {
            // Merge with default config
            const defaultConfig = this.defaultConfigs.get(provider) || {};
            return { ...defaultConfig, ...providerConfig };
        }

        // Return default config if no tenant-specific config exists
        return this.defaultConfigs.get(provider) || null;
    }

    /**
     * Set configuration for a provider/tenant combination
     */
    async setConfig(provider, tenant, config) {
        // Validate configuration
        const isValid = await this.validateConfig(provider, config);
        if (!isValid.valid) {
            throw new Error(`Invalid configuration: ${isValid.errors.join(', ')}`);
        }

        // Get or create tenant config
        let tenantConfigs = this.configs.get(tenant) || {};
        tenantConfigs[provider] = config;

        this.configs.set(tenant, tenantConfigs);

        // Save to file
        await this.saveTenantConfig(tenant);

        // Trigger hooks
        await this.triggerHooks('config.updated', { provider, tenant, config });

        return true;
    }

    /**
     * Remove configuration for a provider/tenant combination
     */
    async removeConfig(provider, tenant) {
        const tenantConfigs = this.configs.get(tenant);
        if (!tenantConfigs || !tenantConfigs[provider]) {
            return false;
        }

        delete tenantConfigs[provider];
        this.configs.set(tenant, tenantConfigs);

        await this.saveTenantConfig(tenant);
        await this.triggerHooks('config.removed', { provider, tenant });

        return true;
    }

    /**
     * List all configurations for a tenant
     */
    listConfigs(tenant = 'default') {
        const tenantConfigs = this.configs.get(tenant) || {};
        const result = {};

        // Add tenant-specific configs
        for (const [provider, config] of Object.entries(tenantConfigs)) {
            result[provider] = {
                ...config,
                source: 'tenant',
                tenant
            };
        }

        // Add default configs for providers not overridden
        for (const [provider, config] of this.defaultConfigs) {
            if (!result[provider]) {
                result[provider] = {
                    ...config,
                    source: 'default',
                    tenant: 'default'
                };
            }
        }

        return result;
    }

    /**
     * Get all tenants
     */
    getTenants() {
        return Array.from(this.configs.keys());
    }

    /**
     * Create provider configuration from template
     */
    async createFromTemplate(templateName, provider, tenant, variables = {}) {
        const template = this.templates.get(templateName);
        if (!template) {
            throw new Error(`Template ${templateName} not found`);
        }

        // Replace variables in template
        let configStr = JSON.stringify(template);
        for (const [key, value] of Object.entries(variables)) {
            configStr = configStr.replace(new RegExp(`{{${key}}}`, 'g'), value);
        }

        const config = JSON.parse(configStr);
        return await this.setConfig(provider, tenant, config);
    }

    /**
     * Register configuration template
     */
    registerTemplate(name, template) {
        this.templates.set(name, template);
    }

    /**
     * Register custom validator
     */
    registerValidator(provider, validator) {
        this.validators.set(provider, validator);
    }

    /**
     * Register configuration change hook
     */
    registerHook(event, handler) {
        if (!this.hooks.has(event)) {
            this.hooks.set(event, []);
        }
        this.hooks.get(event).push(handler);
    }

    /**
     * Validate configuration
     */
    async validateConfig(provider, config) {
        const errors = [];

        // Basic validation
        if (!config.baseUrl) {
            errors.push('baseUrl is required');
        }

        if (!config.apiKey && provider !== 'local') {
            errors.push('apiKey is required for non-local providers');
        }

        // Provider-specific validation
        const customValidator = this.validators.get(provider);
        if (customValidator) {
            try {
                const customResult = await customValidator(config);
                if (!customResult.valid) {
                    errors.push(...customResult.errors);
                }
            } catch (error) {
                errors.push(`Custom validation failed: ${error.message}`);
            }
        }

        // Provider-specific validation rules
        switch (provider) {
            case 'openai':
                if (config.baseUrl && !config.baseUrl.includes('openai.com') && !config.baseUrl.includes('localhost')) {
                    // Allow custom OpenAI-compatible endpoints
                }
                break;

            case 'anthropic':
                if (config.baseUrl && !config.baseUrl.includes('anthropic.com') && !config.baseUrl.includes('localhost')) {
                    // Allow custom Anthropic-compatible endpoints
                }
                if (config.anthropicVersion && !/^\d{4}-\d{2}-\d{2}$/.test(config.anthropicVersion)) {
                    errors.push('anthropicVersion must be in YYYY-MM-DD format');
                }
                break;

            case 'local':
                if (config.serverType && !['ollama', 'lmstudio', 'vllm'].includes(config.serverType)) {
                    errors.push('serverType must be one of: ollama, lmstudio, vllm');
                }
                break;

            case 'custom':
                if (!config.requestFormat) {
                    errors.push('requestFormat is required for custom providers');
                }
                if (!config.responseFormat) {
                    errors.push('responseFormat is required for custom providers');
                }
                break;
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }

    /**
     * Save tenant configuration to file
     */
    async saveTenantConfig(tenant) {
        const configPath = path.join(this.configDir, `tenant-${tenant}.json`);
        const tenantConfigs = this.configs.get(tenant) || {};

        // Encrypt sensitive data
        const encryptedConfig = this.encryptConfig(tenantConfigs);

        await fs.writeFile(configPath, JSON.stringify(encryptedConfig, null, 2));
    }

    /**
     * Encrypt configuration
     */
    encryptConfig(config) {
        const encryptedConfig = {};

        for (const [provider, providerConfig] of Object.entries(config)) {
            encryptedConfig[provider] = {};

            for (const [key, value] of Object.entries(providerConfig)) {
                if (this.isSensitiveField(key)) {
                    encryptedConfig[provider][key] = this.encrypt(value);
                } else {
                    encryptedConfig[provider][key] = value;
                }
            }
        }

        return encryptedConfig;
    }

    /**
     * Decrypt configuration
     */
    decryptConfig(encryptedConfig) {
        const config = {};

        for (const [provider, providerConfig] of Object.entries(encryptedConfig)) {
            config[provider] = {};

            for (const [key, value] of Object.entries(providerConfig)) {
                if (this.isSensitiveField(key) && typeof value === 'string' && value.startsWith('encrypted:')) {
                    config[provider][key] = this.decrypt(value);
                } else {
                    config[provider][key] = value;
                }
            }
        }

        return config;
    }

    /**
     * Check if field contains sensitive data
     */
    isSensitiveField(fieldName) {
        const sensitiveFields = ['apiKey', 'apiSecret', 'token', 'password', 'key'];
        return sensitiveFields.some(field => fieldName.toLowerCase().includes(field.toLowerCase()));
    }

    /**
     * Encrypt sensitive value
     */
    encrypt(value) {
        if (!value) return value;

        const cipher = crypto.createCipher('aes-256-cbc', this.encryptionKey);
        let encrypted = cipher.update(value, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        return `encrypted:${encrypted}`;
    }

    /**
     * Decrypt sensitive value
     */
    decrypt(encryptedValue) {
        if (!encryptedValue || !encryptedValue.startsWith('encrypted:')) {
            return encryptedValue;
        }

        const encrypted = encryptedValue.replace('encrypted:', '');
        const decipher = crypto.createDecipher('aes-256-cbc', this.encryptionKey);
        let decrypted = decipher.update(encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        return decrypted;
    }

    /**
     * Generate encryption key
     */
    generateKey() {
        return crypto.randomBytes(32).toString('hex');
    }

    /**
     * Setup file watcher for configuration changes
     */
    setupFileWatcher(tenant, configPath) {
        if (this.watchers.has(tenant)) {
            this.watchers.get(tenant).close();
        }

        try {
            const watcher = fs.watch(configPath, async (eventType) => {
                if (eventType === 'change') {
                    await this.loadTenantConfig(tenant);
                    await this.triggerHooks('config.reloaded', { tenant });
                }
            });

            this.watchers.set(tenant, watcher);
        } catch (error) {
            console.error(`Failed to setup file watcher for tenant ${tenant}:`, error);
        }
    }

    /**
     * Trigger configuration hooks
     */
    async triggerHooks(event, data) {
        const handlers = this.hooks.get(event) || [];

        for (const handler of handlers) {
            try {
                await handler(data);
            } catch (error) {
                console.error(`Hook handler failed for event ${event}:`, error);
            }
        }
    }

    /**
     * Setup default configuration templates
     */
    setupDefaultTemplates() {
        // OpenAI template
        this.registerTemplate('openai', {
            baseUrl: 'https://api.openai.com/v1',
            apiKey: '{{OPENAI_API_KEY}}',
            defaultModel: 'gpt-3.5-turbo',
            maxTokens: 4096,
            organization: '{{OPENAI_ORG_ID}}'
        });

        // Anthropic template
        this.registerTemplate('anthropic', {
            baseUrl: 'https://api.anthropic.com/v1',
            apiKey: '{{ANTHROPIC_API_KEY}}',
            defaultModel: 'claude-3-sonnet-20240229',
            maxTokens: 4096,
            anthropicVersion: '2023-06-01'
        });

        // Google AI template
        this.registerTemplate('google', {
            baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
            apiKey: '{{GOOGLE_API_KEY}}',
            defaultModel: 'gemini-pro',
            maxTokens: 4096
        });

        // Local model template
        this.registerTemplate('local', {
            baseUrl: '{{LOCAL_MODEL_URL}}',
            apiKey: 'not-required',
            defaultModel: '{{LOCAL_MODEL_NAME}}',
            maxTokens: 4096,
            serverType: 'ollama'
        });

        // Custom API template
        this.registerTemplate('custom', {
            baseUrl: '{{CUSTOM_API_URL}}',
            apiKey: '{{CUSTOM_API_KEY}}',
            defaultModel: 'default',
            maxTokens: 4096,
            requestFormat: 'openai',
            responseFormat: 'openai',
            authMethod: 'bearer'
        });
    }

    /**
     * Create default configurations
     */
    async createDefaultConfigs() {
        const defaultConfigs = {
            openai: {
                baseUrl: 'https://api.openai.com/v1',
                defaultModel: 'gpt-3.5-turbo',
                maxTokens: 4096
            },
            anthropic: {
                baseUrl: 'https://api.anthropic.com/v1',
                defaultModel: 'claude-3-sonnet-20240229',
                maxTokens: 4096,
                anthropicVersion: '2023-06-01'
            },
            google: {
                baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
                defaultModel: 'gemini-pro',
                maxTokens: 4096
            },
            local: {
                baseUrl: 'http://localhost:11434',
                defaultModel: 'llama2',
                maxTokens: 4096,
                serverType: 'ollama'
            }
        };

        for (const [provider, config] of Object.entries(defaultConfigs)) {
            this.defaultConfigs.set(provider, config);
        }

        const defaultConfigPath = path.join(this.configDir, 'defaults.json');
        await fs.writeFile(defaultConfigPath, JSON.stringify(defaultConfigs, null, 2));
    }

    /**
     * Export configurations
     */
    async exportConfigs(includeSensitive = false) {
        const exported = {
            defaults: Object.fromEntries(this.defaultConfigs),
            tenants: {},
            exportDate: new Date().toISOString(),
            includeSensitive
        };

        for (const [tenant, configs] of this.configs) {
            exported.tenants[tenant] = {};

            for (const [provider, config] of Object.entries(configs)) {
                if (includeSensitive) {
                    exported.tenants[tenant][provider] = config;
                } else {
                    // Remove sensitive fields
                    const sanitized = {};
                    for (const [key, value] of Object.entries(config)) {
                        if (!this.isSensitiveField(key)) {
                            sanitized[key] = value;
                        }
                    }
                    exported.tenants[tenant][provider] = sanitized;
                }
            }
        }

        return exported;
    }

    /**
     * Get configuration statistics
     */
    getStatistics() {
        const stats = {
            totalTenants: this.configs.size,
            totalProviders: new Set(),
            defaultConfigs: this.defaultConfigs.size,
            templates: this.templates.size,
            watchers: this.watchers.size,
            hooks: this.hooks.size,
            tenantBreakdown: {}
        };

        for (const [tenant, configs] of this.configs) {
            stats.tenantBreakdown[tenant] = {
                providers: Object.keys(configs).length,
                providerList: Object.keys(configs)
            };

            Object.keys(configs).forEach(provider => {
                stats.totalProviders.add(provider);
            });
        }

        stats.totalProviders = stats.totalProviders.size;

        return stats;
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        // Close file watchers
        for (const watcher of this.watchers.values()) {
            watcher.close();
        }
        this.watchers.clear();

        // Clear hooks
        this.hooks.clear();
    }
}

module.exports = ConfigManager;