/**
 * AI Orchestration API Routes
 * RESTful API endpoints for provider management
 */

const express = require('express');
const { AIOrchestrator } = require('../index');

class AIOrchestrationAPI {
    constructor(orchestrator) {
        this.orchestrator = orchestrator;
        this.router = express.Router();
        this.setupRoutes();
    }

    setupRoutes() {
        // Provider management
        this.router.post('/providers', this.createProvider.bind(this));
        this.router.get('/providers', this.listProviders.bind(this));
        this.router.get('/providers/:name', this.getProvider.bind(this));
        this.router.put('/providers/:name', this.updateProvider.bind(this));
        this.router.delete('/providers/:name', this.removeProvider.bind(this));
        this.router.post('/providers/:name/test', this.testProvider.bind(this));

        // AI generation endpoints
        this.router.post('/chat/completions', this.chatCompletion.bind(this));
        this.router.post('/completions', this.completion.bind(this));
        this.router.post('/embeddings', this.embedding.bind(this));

        // Monitoring endpoints
        this.router.get('/health', this.getHealth.bind(this));
        this.router.get('/health/:name', this.getProviderHealth.bind(this));
        this.router.get('/metrics', this.getMetrics.bind(this));
        this.router.get('/statistics', this.getStatistics.bind(this));

        // Cost management
        this.router.get('/costs', this.getCosts.bind(this));
        this.router.get('/costs/analytics', this.getCostAnalytics.bind(this));
        this.router.post('/budgets', this.setBudget.bind(this));
        this.router.get('/budgets/:tenant', this.getBudget.bind(this));

        // Rate limiting
        this.router.get('/rate-limits', this.getRateLimits.bind(this));
        this.router.post('/rate-limits', this.setRateLimit.bind(this));
        this.router.delete('/rate-limits/:provider/:tenant', this.resetRateLimit.bind(this));

        // Configuration management
        this.router.get('/config', this.getConfiguration.bind(this));
        this.router.post('/config/templates/:template', this.createFromTemplate.bind(this));
        this.router.get('/config/export', this.exportConfig.bind(this));
        this.router.post('/config/import', this.importConfig.bind(this));

        // Tenant management
        this.router.get('/tenants', this.getTenants.bind(this));
        this.router.get('/tenants/:tenant/providers', this.getTenantProviders.bind(this));
    }

    // Middleware for extracting tenant from request
    getTenantFromRequest(req) {
        return req.headers['x-tenant-id'] || req.query.tenant || 'default';
    }

    // Provider Management Endpoints

    async createProvider(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const config = { ...req.body, tenant };

            const provider = await this.orchestrator.createProvider(config);

            res.status(201).json({
                success: true,
                message: 'Provider created successfully',
                provider: {
                    name: provider.name,
                    type: provider.constructor.name,
                    tenant,
                    capabilities: provider.getCapabilities()
                }
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async listProviders(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const providers = this.orchestrator.listProviders(tenant);

            res.json({
                success: true,
                providers: providers.map(p => ({
                    name: p.name,
                    type: p.type,
                    tenant,
                    health: p.health,
                    metrics: p.metrics,
                    capabilities: p.provider?.getCapabilities()
                }))
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getProvider(req, res) {
        try {
            const { name } = req.params;
            const tenant = this.getTenantFromRequest(req);

            const provider = this.orchestrator.getProvider(name, tenant);
            if (!provider) {
                return res.status(404).json({
                    success: false,
                    error: `Provider ${name} not found`
                });
            }

            const health = this.orchestrator.getProviderHealth(name, tenant);
            const metrics = provider.getMetrics();

            res.json({
                success: true,
                provider: {
                    name: provider.name,
                    type: provider.constructor.name,
                    tenant,
                    health,
                    metrics,
                    capabilities: provider.getCapabilities()
                }
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async updateProvider(req, res) {
        try {
            const { name } = req.params;
            const tenant = this.getTenantFromRequest(req);

            const provider = await this.orchestrator.updateProvider(name, tenant, req.body);

            res.json({
                success: true,
                message: 'Provider updated successfully',
                provider: {
                    name: provider.name,
                    type: provider.constructor.name,
                    tenant,
                    capabilities: provider.getCapabilities()
                }
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async removeProvider(req, res) {
        try {
            const { name } = req.params;
            const tenant = this.getTenantFromRequest(req);

            await this.orchestrator.removeProvider(name, tenant);

            res.json({
                success: true,
                message: 'Provider removed successfully'
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async testProvider(req, res) {
        try {
            const { name } = req.params;
            const tenant = this.getTenantFromRequest(req);

            const result = await this.orchestrator.testProvider(name, tenant);

            res.json({
                success: result.success,
                result
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    // AI Generation Endpoints

    async chatCompletion(req, res) {
        try {
            const { messages, ...options } = req.body;
            const tenant = this.getTenantFromRequest(req);

            const result = await this.orchestrator.generateChatCompletion(messages, {
                ...options,
                tenant
            });

            res.json({
                success: true,
                ...result
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async completion(req, res) {
        try {
            const { prompt, ...options } = req.body;
            const tenant = this.getTenantFromRequest(req);

            const result = await this.orchestrator.generateCompletion(prompt, {
                ...options,
                tenant
            });

            res.json({
                success: true,
                ...result
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async embedding(req, res) {
        try {
            const { text, ...options } = req.body;
            const tenant = this.getTenantFromRequest(req);

            const result = await this.orchestrator.generateEmbedding(text, {
                ...options,
                tenant
            });

            res.json({
                success: true,
                ...result
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    // Monitoring Endpoints

    async getHealth(req, res) {
        try {
            const summary = this.orchestrator.getHealthSummary();

            res.json({
                success: true,
                health: summary
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getProviderHealth(req, res) {
        try {
            const { name } = req.params;
            const tenant = this.getTenantFromRequest(req);

            const health = this.orchestrator.getProviderHealth(name, tenant);

            res.json({
                success: true,
                health
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getMetrics(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const providers = this.orchestrator.listProviders(tenant);

            const metrics = providers.map(p => ({
                name: p.name,
                metrics: p.metrics
            }));

            res.json({
                success: true,
                metrics
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getStatistics(req, res) {
        try {
            const statistics = this.orchestrator.getStatistics();

            res.json({
                success: true,
                statistics
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    // Cost Management Endpoints

    async getCosts(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const costs = this.orchestrator.getCostSummary(tenant);

            res.json({
                success: true,
                costs
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getCostAnalytics(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const { timeRange = '7d' } = req.query;

            const analytics = this.orchestrator.getAnalytics(timeRange, tenant !== 'default' ? tenant : null);

            res.json({
                success: true,
                analytics
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async setBudget(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const budget = req.body;

            this.orchestrator.setBudget(tenant, budget);

            res.json({
                success: true,
                message: 'Budget set successfully'
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async getBudget(req, res) {
        try {
            const { tenant } = req.params;
            const budget = this.orchestrator.costTracker.getBudget(tenant);

            res.json({
                success: true,
                budget
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    // Rate Limiting Endpoints

    async getRateLimits(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const { provider } = req.query;

            const rateLimits = this.orchestrator.getRateLimitStatus(provider, tenant);

            res.json({
                success: true,
                rateLimits
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async setRateLimit(req, res) {
        try {
            const { target, limits, type = 'provider' } = req.body;

            this.orchestrator.setRateLimit(target, limits, type);

            res.json({
                success: true,
                message: 'Rate limits updated successfully'
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async resetRateLimit(req, res) {
        try {
            const { provider, tenant } = req.params;

            this.orchestrator.rateLimiter.resetLimits(provider, tenant);

            res.json({
                success: true,
                message: 'Rate limits reset successfully'
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    // Configuration Management Endpoints

    async getConfiguration(req, res) {
        try {
            const tenant = this.getTenantFromRequest(req);
            const configs = this.orchestrator.configManager.listConfigs(tenant);

            res.json({
                success: true,
                configurations: configs
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async createFromTemplate(req, res) {
        try {
            const { template } = req.params;
            const { name, variables = {} } = req.body;
            const tenant = this.getTenantFromRequest(req);

            const provider = await this.orchestrator.createProviderFromTemplate(
                template,
                name,
                tenant,
                variables
            );

            res.status(201).json({
                success: true,
                message: 'Provider created from template successfully',
                provider: {
                    name: provider.name,
                    type: provider.constructor.name,
                    tenant,
                    capabilities: provider.getCapabilities()
                }
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    async exportConfig(req, res) {
        try {
            const { includeSecrets = false, includeHistory = true } = req.query;

            const exportData = await this.orchestrator.exportData({
                includeSecrets: includeSecrets === 'true',
                includeHistory: includeHistory === 'true'
            });

            res.setHeader('Content-Disposition', `attachment; filename=ai-orchestrator-export-${Date.now()}.json`);
            res.setHeader('Content-Type', 'application/json');
            res.json(exportData);
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async importConfig(req, res) {
        try {
            const importData = req.body;

            await this.orchestrator.importData(importData);

            res.json({
                success: true,
                message: 'Configuration imported successfully'
            });
        } catch (error) {
            res.status(400).json({
                success: false,
                error: error.message
            });
        }
    }

    // Tenant Management Endpoints

    async getTenants(req, res) {
        try {
            const tenants = this.orchestrator.configManager.getTenants();

            res.json({
                success: true,
                tenants
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    async getTenantProviders(req, res) {
        try {
            const { tenant } = req.params;
            const providers = this.orchestrator.listProviders(tenant);

            res.json({
                success: true,
                tenant,
                providers: providers.map(p => ({
                    name: p.name,
                    type: p.type,
                    health: p.health,
                    metrics: p.metrics
                }))
            });
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message
            });
        }
    }

    // Error handling middleware
    errorHandler(err, req, res, next) {
        console.error('API Error:', err);

        res.status(err.status || 500).json({
            success: false,
            error: err.message || 'Internal server error',
            ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
        });
    }

    // Get Express router
    getRouter() {
        return this.router;
    }
}

// Factory function to create API with orchestrator
function createAPI(orchestrator) {
    return new AIOrchestrationAPI(orchestrator);
}

module.exports = {
    AIOrchestrationAPI,
    createAPI
};