/**
 * ProviderRegistry - Factory and registry for AI providers
 * Manages provider instances, configurations, and lifecycle
 */

const BaseProvider = require('./BaseProvider');
const OpenAIProvider = require('../providers/OpenAIProvider');
const AnthropicProvider = require('../providers/AnthropicProvider');
const GoogleAIProvider = require('../providers/GoogleAIProvider');
const LocalModelProvider = require('../providers/LocalModelProvider');
const CustomAPIProvider = require('../providers/CustomAPIProvider');
const HealthMonitor = require('../monitoring/HealthMonitor');
const CostTracker = require('../monitoring/CostTracker');
const RateLimiter = require('../monitoring/RateLimiter');

class ProviderRegistry {
    constructor() {
        this.providers = new Map();
        this.providerClasses = new Map();
        this.configurations = new Map();
        this.healthMonitor = new HealthMonitor();
        this.costTracker = new CostTracker();
        this.rateLimiter = new RateLimiter();

        // Register built-in provider classes
        this.registerProviderClass('openai', OpenAIProvider);
        this.registerProviderClass('anthropic', AnthropicProvider);
        this.registerProviderClass('google', GoogleAIProvider);
        this.registerProviderClass('local', LocalModelProvider);
        this.registerProviderClass('custom', CustomAPIProvider);
    }

    /**
     * Register a provider class
     */
    registerProviderClass(type, providerClass) {
        if (!(providerClass.prototype instanceof BaseProvider)) {
            throw new Error(`Provider class must extend BaseProvider`);
        }

        this.providerClasses.set(type, providerClass);
    }

    /**
     * Create and register a provider instance
     */
    async createProvider(config) {
        const { type, name, tenant, ...providerConfig } = config;

        if (!this.providerClasses.has(type)) {
            throw new Error(`Unknown provider type: ${type}`);
        }

        const providerKey = this.getProviderKey(name, tenant);

        if (this.providers.has(providerKey)) {
            throw new Error(`Provider ${providerKey} already exists`);
        }

        const ProviderClass = this.providerClasses.get(type);
        const provider = new ProviderClass(providerConfig);

        // Set up monitoring and rate limiting
        provider.setHealthChecker(this.healthMonitor);
        provider.setCostTracker(this.costTracker);
        provider.setRateLimiter(this.rateLimiter);

        // Store configuration
        this.configurations.set(providerKey, config);

        // Register provider
        this.providers.set(providerKey, provider);

        // Start health monitoring
        this.healthMonitor.addProvider(providerKey, provider);

        return provider;
    }

    /**
     * Get a provider instance
     */
    getProvider(name, tenant = 'default') {
        const providerKey = this.getProviderKey(name, tenant);
        return this.providers.get(providerKey);
    }

    /**
     * List all providers for a tenant
     */
    listProviders(tenant = 'default') {
        const tenantProviders = [];

        for (const [key, provider] of this.providers) {
            if (key.startsWith(`${tenant}:`)) {
                tenantProviders.push({
                    key,
                    name: provider.name,
                    type: provider.constructor.name,
                    config: this.configurations.get(key),
                    metrics: provider.getMetrics(),
                    health: this.healthMonitor.getProviderHealth(key)
                });
            }
        }

        return tenantProviders;
    }

    /**
     * Remove a provider
     */
    async removeProvider(name, tenant = 'default') {
        const providerKey = this.getProviderKey(name, tenant);

        if (!this.providers.has(providerKey)) {
            throw new Error(`Provider ${providerKey} not found`);
        }

        // Stop health monitoring
        this.healthMonitor.removeProvider(providerKey);

        // Remove from registry
        this.providers.delete(providerKey);
        this.configurations.delete(providerKey);

        return true;
    }

    /**
     * Update provider configuration
     */
    async updateProvider(name, tenant, updates) {
        const providerKey = this.getProviderKey(name, tenant);
        const provider = this.providers.get(providerKey);

        if (!provider) {
            throw new Error(`Provider ${providerKey} not found`);
        }

        const currentConfig = this.configurations.get(providerKey);
        const newConfig = { ...currentConfig, ...updates };

        // Recreate provider with new configuration
        await this.removeProvider(name, tenant);
        return await this.createProvider(newConfig);
    }

    /**
     * Get best available provider for a request
     */
    getBestProvider(criteria = {}, tenant = 'default') {
        const tenantProviders = this.listProviders(tenant);

        if (tenantProviders.length === 0) {
            throw new Error(`No providers available for tenant: ${tenant}`);
        }

        // Filter by criteria
        let candidates = tenantProviders.filter(p => {
            const health = p.health;
            const capabilities = p.provider?.getCapabilities() || {};

            // Must be healthy
            if (!health.healthy) return false;

            // Check model requirements
            if (criteria.model && capabilities.models) {
                if (!capabilities.models.includes(criteria.model)) return false;
            }

            // Check capability requirements
            if (criteria.supportsFunctionCalling && !capabilities.supportsFunctionCalling) {
                return false;
            }

            if (criteria.supportsStreaming && !capabilities.supportsStreaming) {
                return false;
            }

            return true;
        });

        if (candidates.length === 0) {
            throw new Error('No providers meet the specified criteria');
        }

        // Sort by performance and availability
        candidates.sort((a, b) => {
            const aMetrics = a.metrics;
            const bMetrics = b.metrics;

            // Prefer lower error rate
            const aErrorRate = aMetrics.errors / Math.max(aMetrics.requests, 1);
            const bErrorRate = bMetrics.errors / Math.max(bMetrics.requests, 1);

            if (aErrorRate !== bErrorRate) {
                return aErrorRate - bErrorRate;
            }

            // Prefer lower latency
            return aMetrics.avgLatency - bMetrics.avgLatency;
        });

        return this.getProvider(candidates[0].name, tenant);
    }

    /**
     * Get load balanced provider
     */
    getLoadBalancedProvider(tenant = 'default') {
        const providers = this.listProviders(tenant);
        const healthyProviders = providers.filter(p => p.health.healthy);

        if (healthyProviders.length === 0) {
            throw new Error('No healthy providers available');
        }

        // Simple round-robin based on request count
        const sortedByLoad = healthyProviders.sort((a, b) =>
            a.metrics.requests - b.metrics.requests
        );

        return this.getProvider(sortedByLoad[0].name, tenant);
    }

    /**
     * Execute request with failover
     */
    async executeWithFailover(requestFn, criteria = {}, tenant = 'default', maxAttempts = 3) {
        const providers = this.listProviders(tenant)
            .filter(p => p.health.healthy)
            .sort((a, b) => a.metrics.errors - b.metrics.errors);

        if (providers.length === 0) {
            throw new Error('No healthy providers available');
        }

        let lastError;

        for (let i = 0; i < Math.min(maxAttempts, providers.length); i++) {
            const provider = this.getProvider(providers[i].name, tenant);

            try {
                return await requestFn(provider);
            } catch (error) {
                lastError = error;

                // Mark provider as potentially unhealthy
                this.healthMonitor.recordError(
                    this.getProviderKey(provider.name, tenant),
                    error
                );

                // Continue to next provider
                continue;
            }
        }

        throw lastError;
    }

    /**
     * Get registry statistics
     */
    getStatistics() {
        const stats = {
            totalProviders: this.providers.size,
            providerTypes: {},
            tenants: new Set(),
            healthyProviders: 0,
            totalRequests: 0,
            totalCost: 0,
            totalTokens: 0
        };

        for (const [key, provider] of this.providers) {
            const [tenant, name] = key.split(':');
            stats.tenants.add(tenant);

            const type = provider.constructor.name;
            stats.providerTypes[type] = (stats.providerTypes[type] || 0) + 1;

            const health = this.healthMonitor.getProviderHealth(key);
            if (health.healthy) {
                stats.healthyProviders++;
            }

            const metrics = provider.getMetrics();
            stats.totalRequests += metrics.requests;
            stats.totalCost += metrics.cost;
            stats.totalTokens += metrics.tokens;
        }

        stats.tenants = Array.from(stats.tenants);

        return stats;
    }

    /**
     * Generate provider key
     */
    getProviderKey(name, tenant = 'default') {
        return `${tenant}:${name}`;
    }

    /**
     * Cleanup resources
     */
    async cleanup() {
        this.healthMonitor.stop();
        this.providers.clear();
        this.configurations.clear();
    }
}

module.exports = ProviderRegistry;