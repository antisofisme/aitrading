/**
 * AI Orchestration Framework - Main Entry Point
 * A flexible AI model provider framework supporting multiple AI services
 */

const ProviderRegistry = require('./core/ProviderRegistry');
const ConfigManager = require('./config/ConfigManager');
const ProviderAdapter = require('./adapters/ProviderAdapter');
const HealthMonitor = require('./monitoring/HealthMonitor');
const CostTracker = require('./monitoring/CostTracker');
const RateLimiter = require('./monitoring/RateLimiter');

class AIOrchestrator {
    constructor(options = {}) {
        this.options = options;

        // Initialize core components
        this.configManager = new ConfigManager(options.config);
        this.providerRegistry = new ProviderRegistry();
        this.adapter = new ProviderAdapter(options.adapter);
        this.healthMonitor = new HealthMonitor(options.health);
        this.costTracker = new CostTracker(options.cost);
        this.rateLimiter = new RateLimiter(options.rateLimit);

        this.isInitialized = false;
    }

    /**
     * Initialize the orchestrator
     */
    async initialize() {
        if (this.isInitialized) return;

        try {
            // Initialize configuration manager
            await this.configManager.init();

            // Setup configuration change hooks
            this.configManager.registerHook('config.updated', this.handleConfigUpdate.bind(this));
            this.configManager.registerHook('config.removed', this.handleConfigRemoval.bind(this));

            // Load existing provider configurations
            await this.loadProviderConfigurations();

            this.isInitialized = true;
            console.log('AI Orchestrator initialized successfully');

        } catch (error) {
            console.error('Failed to initialize AI Orchestrator:', error);
            throw error;
        }
    }

    /**
     * Create a new AI provider
     */
    async createProvider(config) {
        if (!this.isInitialized) {
            await this.initialize();
        }

        const { name, tenant = 'default', type, ...providerConfig } = config;

        // Validate configuration
        const validation = await this.configManager.validateConfig(type, providerConfig);
        if (!validation.valid) {
            throw new Error(`Invalid provider configuration: ${validation.errors.join(', ')}`);
        }

        // Store configuration
        await this.configManager.setConfig(type, tenant, { name, ...providerConfig });

        // Create provider instance
        const provider = await this.providerRegistry.createProvider({
            name,
            tenant,
            type,
            ...providerConfig
        });

        return provider;
    }

    /**
     * Get a provider instance
     */
    getProvider(name, tenant = 'default') {
        return this.providerRegistry.getProvider(name, tenant);
    }

    /**
     * Generate chat completion using best available provider
     */
    async generateChatCompletion(messages, options = {}) {
        const { tenant = 'default', provider: preferredProvider, ...requestOptions } = options;

        try {
            let provider;

            if (preferredProvider) {
                provider = this.getProvider(preferredProvider, tenant);
                if (!provider) {
                    throw new Error(`Provider ${preferredProvider} not found for tenant ${tenant}`);
                }
            } else {
                provider = this.providerRegistry.getBestProvider(requestOptions, tenant);
            }

            // Check rate limits
            const rateLimitResult = await this.rateLimiter.checkLimit(
                provider.name,
                tenant,
                this.estimateTokens(messages),
                'request'
            );

            if (!rateLimitResult.allowed) {
                throw new Error(`Rate limit exceeded: ${rateLimitResult.reason}. Retry after ${rateLimitResult.retryAfter} seconds`);
            }

            // Execute request with failover
            const result = await this.providerRegistry.executeWithFailover(
                async (p) => await p.generateChatCompletion(messages, requestOptions),
                requestOptions,
                tenant
            );

            // Record cost
            this.costTracker.recordCost(
                provider.name,
                tenant,
                result.model,
                result.cost,
                result.usage?.total_tokens || 0,
                'chat_completion'
            );

            // Release rate limit
            this.rateLimiter.releaseRequest(provider.name, tenant);

            return result;

        } catch (error) {
            throw new Error(`Chat completion failed: ${error.message}`);
        }
    }

    /**
     * Generate text completion using best available provider
     */
    async generateCompletion(prompt, options = {}) {
        const { tenant = 'default', provider: preferredProvider, ...requestOptions } = options;

        try {
            let provider;

            if (preferredProvider) {
                provider = this.getProvider(preferredProvider, tenant);
                if (!provider) {
                    throw new Error(`Provider ${preferredProvider} not found for tenant ${tenant}`);
                }
            } else {
                provider = this.providerRegistry.getBestProvider(requestOptions, tenant);
            }

            // Check rate limits
            const estimatedTokens = Math.ceil(prompt.length / 4);
            const rateLimitResult = await this.rateLimiter.checkLimit(
                provider.name,
                tenant,
                estimatedTokens,
                'request'
            );

            if (!rateLimitResult.allowed) {
                throw new Error(`Rate limit exceeded: ${rateLimitResult.reason}. Retry after ${rateLimitResult.retryAfter} seconds`);
            }

            // Execute request with failover
            const result = await this.providerRegistry.executeWithFailover(
                async (p) => await p.generateCompletion(prompt, requestOptions),
                requestOptions,
                tenant
            );

            // Record cost
            this.costTracker.recordCost(
                provider.name,
                tenant,
                result.model,
                result.cost,
                result.usage?.total_tokens || 0,
                'completion'
            );

            // Release rate limit
            this.rateLimiter.releaseRequest(provider.name, tenant);

            return result;

        } catch (error) {
            throw new Error(`Completion failed: ${error.message}`);
        }
    }

    /**
     * Generate embedding using best available provider
     */
    async generateEmbedding(text, options = {}) {
        const { tenant = 'default', provider: preferredProvider, ...requestOptions } = options;

        try {
            // Filter providers that support embeddings
            const criteria = { ...requestOptions, supportsEmbedding: true };

            let provider;

            if (preferredProvider) {
                provider = this.getProvider(preferredProvider, tenant);
                if (!provider) {
                    throw new Error(`Provider ${preferredProvider} not found for tenant ${tenant}`);
                }

                const capabilities = provider.getCapabilities();
                if (!capabilities.supportsEmbedding) {
                    throw new Error(`Provider ${preferredProvider} does not support embeddings`);
                }
            } else {
                provider = this.providerRegistry.getBestProvider(criteria, tenant);
            }

            // Check rate limits
            const estimatedTokens = Math.ceil(text.length / 4);
            const rateLimitResult = await this.rateLimiter.checkLimit(
                provider.name,
                tenant,
                estimatedTokens,
                'request'
            );

            if (!rateLimitResult.allowed) {
                throw new Error(`Rate limit exceeded: ${rateLimitResult.reason}. Retry after ${rateLimitResult.retryAfter} seconds`);
            }

            // Execute request with failover
            const result = await this.providerRegistry.executeWithFailover(
                async (p) => await p.generateEmbedding(text, requestOptions),
                criteria,
                tenant
            );

            // Record cost
            this.costTracker.recordCost(
                provider.name,
                tenant,
                result.model,
                result.cost,
                result.usage?.total_tokens || 0,
                'embedding'
            );

            // Release rate limit
            this.rateLimiter.releaseRequest(provider.name, tenant);

            return result;

        } catch (error) {
            throw new Error(`Embedding generation failed: ${error.message}`);
        }
    }

    /**
     * List available providers for a tenant
     */
    listProviders(tenant = 'default') {
        return this.providerRegistry.listProviders(tenant);
    }

    /**
     * Get provider health status
     */
    getProviderHealth(name, tenant = 'default') {
        const providerKey = this.providerRegistry.getProviderKey(name, tenant);
        return this.healthMonitor.getProviderHealth(providerKey);
    }

    /**
     * Get overall health summary
     */
    getHealthSummary() {
        return this.healthMonitor.getHealthSummary();
    }

    /**
     * Get cost summary for a tenant
     */
    getCostSummary(tenant = 'default') {
        if (tenant === 'all') {
            return this.costTracker.getCostSummary();
        }
        return this.costTracker.getTenantCosts(tenant);
    }

    /**
     * Get rate limit status
     */
    getRateLimitStatus(name = null, tenant = 'default') {
        if (name) {
            return this.rateLimiter.getStatus(name, tenant);
        }
        return this.rateLimiter.getAllStatuses();
    }

    /**
     * Set budget for a tenant
     */
    setBudget(tenant, budget) {
        return this.costTracker.setBudget(tenant, budget);
    }

    /**
     * Set rate limits for a provider or tenant
     */
    setRateLimit(target, limits, type = 'provider') {
        if (type === 'provider') {
            return this.rateLimiter.setProviderLimits(target, limits);
        } else {
            return this.rateLimiter.setTenantLimits(target, limits);
        }
    }

    /**
     * Get analytics for cost and usage
     */
    getAnalytics(timeRange = '7d', tenant = null) {
        return this.costTracker.getCostAnalytics(timeRange, tenant);
    }

    /**
     * Remove a provider
     */
    async removeProvider(name, tenant = 'default') {
        await this.providerRegistry.removeProvider(name, tenant);
        await this.configManager.removeConfig(name, tenant);
        return true;
    }

    /**
     * Update provider configuration
     */
    async updateProvider(name, tenant, updates) {
        const provider = await this.providerRegistry.updateProvider(name, tenant, updates);
        await this.configManager.setConfig(updates.type || 'custom', tenant, {
            name,
            ...updates
        });
        return provider;
    }

    /**
     * Create provider from template
     */
    async createProviderFromTemplate(templateName, name, tenant, variables = {}) {
        await this.configManager.createFromTemplate(templateName, name, tenant, variables);

        // Get the created configuration
        const config = this.configManager.getConfig(name, tenant);

        // Create provider instance
        return await this.providerRegistry.createProvider({
            name,
            tenant,
            type: templateName,
            ...config
        });
    }

    /**
     * Test provider connectivity
     */
    async testProvider(name, tenant = 'default') {
        const provider = this.getProvider(name, tenant);
        if (!provider) {
            throw new Error(`Provider ${name} not found for tenant ${tenant}`);
        }

        try {
            const healthResult = await provider.healthCheck();
            return {
                success: healthResult.healthy,
                provider: name,
                tenant,
                result: healthResult
            };
        } catch (error) {
            return {
                success: false,
                provider: name,
                tenant,
                error: error.message
            };
        }
    }

    /**
     * Get system statistics
     */
    getStatistics() {
        return {
            providers: this.providerRegistry.getStatistics(),
            health: this.healthMonitor.getHealthSummary(),
            costs: this.costTracker.getCostSummary(),
            rateLimits: this.rateLimiter.getStatistics(),
            configuration: this.configManager.getStatistics()
        };
    }

    /**
     * Export configuration and data
     */
    async exportData(options = {}) {
        const { includeSecrets = false, includeHistory = true } = options;

        const exportData = {
            timestamp: new Date().toISOString(),
            version: '1.0.0',
            configuration: await this.configManager.exportConfigs(includeSecrets),
            statistics: this.getStatistics()
        };

        if (includeHistory) {
            exportData.costHistory = this.costTracker.exportData();
        }

        return exportData;
    }

    /**
     * Import configuration and data
     */
    async importData(data) {
        if (data.configuration) {
            // Import configurations
            if (data.configuration.defaults) {
                for (const [provider, config] of Object.entries(data.configuration.defaults)) {
                    this.configManager.defaultConfigs.set(provider, config);
                }
            }

            if (data.configuration.tenants) {
                for (const [tenant, configs] of Object.entries(data.configuration.tenants)) {
                    for (const [provider, config] of Object.entries(configs)) {
                        await this.configManager.setConfig(provider, tenant, config);
                    }
                }
            }
        }

        if (data.costHistory) {
            this.costTracker.importData(JSON.parse(data.costHistory));
        }

        // Reload providers
        await this.loadProviderConfigurations();
    }

    /**
     * Handle configuration updates
     */
    async handleConfigUpdate({ provider, tenant, config }) {
        try {
            // Recreate provider with new configuration
            await this.providerRegistry.removeProvider(provider, tenant);
            await this.providerRegistry.createProvider({
                name: config.name,
                tenant,
                type: provider,
                ...config
            });

            console.log(`Provider ${provider} updated for tenant ${tenant}`);
        } catch (error) {
            console.error(`Failed to update provider ${provider} for tenant ${tenant}:`, error);
        }
    }

    /**
     * Handle configuration removal
     */
    async handleConfigRemoval({ provider, tenant }) {
        try {
            await this.providerRegistry.removeProvider(provider, tenant);
            console.log(`Provider ${provider} removed for tenant ${tenant}`);
        } catch (error) {
            console.error(`Failed to remove provider ${provider} for tenant ${tenant}:`, error);
        }
    }

    /**
     * Load provider configurations from config manager
     */
    async loadProviderConfigurations() {
        const tenants = this.configManager.getTenants();

        for (const tenant of tenants) {
            const configs = this.configManager.listConfigs(tenant);

            for (const [providerName, config] of Object.entries(configs)) {
                if (config.source === 'tenant' && config.apiKey) {
                    try {
                        await this.providerRegistry.createProvider({
                            name: config.name || providerName,
                            tenant,
                            type: providerName,
                            ...config
                        });
                    } catch (error) {
                        console.error(`Failed to load provider ${providerName} for tenant ${tenant}:`, error);
                    }
                }
            }
        }
    }

    /**
     * Estimate token count for messages
     */
    estimateTokens(messages) {
        if (Array.isArray(messages)) {
            const text = messages.map(m => m.content || '').join(' ');
            return Math.ceil(text.length / 4);
        }
        return Math.ceil((messages || '').length / 4);
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        await this.providerRegistry.cleanup();
        this.healthMonitor.stop();
        this.rateLimiter.stopCleanup();
        await this.configManager.cleanup();
    }
}

// Export individual components for advanced usage
module.exports = {
    AIOrchestrator,
    ProviderRegistry,
    ConfigManager,
    ProviderAdapter,
    HealthMonitor,
    CostTracker,
    RateLimiter
};