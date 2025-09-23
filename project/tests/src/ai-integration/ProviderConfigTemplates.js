/**
 * AI Provider Configuration Templates
 * Standardized configurations for different AI providers and use cases
 */

class ProviderConfigTemplates {
    constructor() {
        this.templates = new Map();
        this.initializeDefaultTemplates();
    }

    /**
     * Initialize default provider templates
     */
    initializeDefaultTemplates() {
        // OpenAI Templates
        this.addTemplate('openai-production', {
            type: 'openai',
            name: 'openai-primary',
            baseUrl: 'https://api.openai.com/v1',
            apiKey: '${OPENAI_API_KEY}',
            models: {
                chat: 'gpt-4-turbo-preview',
                completion: 'gpt-3.5-turbo-instruct',
                embedding: 'text-embedding-3-large',
                vision: 'gpt-4-vision-preview'
            },
            rateLimits: {
                requestsPerMinute: 500,
                tokensPerMinute: 150000,
                costLimitPerHour: 100.0
            },
            features: {
                supportsFunctionCalling: true,
                supportsStreaming: true,
                supportsVision: true,
                maxTokens: 128000,
                contextWindow: 128000
            },
            retryConfig: {
                maxRetries: 3,
                backoffMultiplier: 2.0,
                initialDelay: 1000,
                maxDelay: 10000
            },
            costTracking: {
                enabled: true,
                alertThreshold: 100.0,
                dailyLimit: 1000.0
            },
            tenant: 'default',
            environment: 'production'
        });

        this.addTemplate('openai-development', {
            type: 'openai',
            name: 'openai-dev',
            baseUrl: 'https://api.openai.com/v1',
            apiKey: '${OPENAI_DEV_API_KEY}',
            models: {
                chat: 'gpt-3.5-turbo',
                completion: 'gpt-3.5-turbo-instruct',
                embedding: 'text-embedding-ada-002'
            },
            rateLimits: {
                requestsPerMinute: 100,
                tokensPerMinute: 50000,
                costLimitPerHour: 10.0
            },
            features: {
                supportsFunctionCalling: true,
                supportsStreaming: false,
                maxTokens: 4096
            },
            environment: 'development'
        });

        // Anthropic Templates
        this.addTemplate('anthropic-production', {
            type: 'anthropic',
            name: 'anthropic-primary',
            baseUrl: 'https://api.anthropic.com',
            apiKey: '${ANTHROPIC_API_KEY}',
            models: {
                chat: 'claude-3-opus-20240229',
                completion: 'claude-3-sonnet-20240229',
                fast: 'claude-3-haiku-20240307'
            },
            rateLimits: {
                requestsPerMinute: 300,
                tokensPerMinute: 100000,
                costLimitPerHour: 150.0
            },
            features: {
                supportsFunctionCalling: true,
                supportsStreaming: true,
                maxTokens: 200000,
                contextWindow: 200000,
                supportsSystemPrompts: true
            },
            retryConfig: {
                maxRetries: 3,
                backoffMultiplier: 1.5,
                initialDelay: 1500
            },
            tenant: 'default',
            environment: 'production'
        });

        // Google AI Templates
        this.addTemplate('google-ai-production', {
            type: 'google',
            name: 'google-ai-primary',
            baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
            apiKey: '${GOOGLE_AI_API_KEY}',
            models: {
                chat: 'gemini-1.5-pro',
                completion: 'gemini-1.5-flash',
                embedding: 'embedding-001'
            },
            rateLimits: {
                requestsPerMinute: 200,
                tokensPerMinute: 80000
            },
            features: {
                supportsFunctionCalling: true,
                supportsMultimodal: true,
                maxTokens: 100000,
                contextWindow: 100000
            },
            environment: 'production'
        });

        // Local Model Templates
        this.addTemplate('local-llama-production', {
            type: 'local',
            name: 'local-llama',
            baseUrl: 'http://localhost:11434',
            models: {
                chat: 'llama2:13b-chat',
                completion: 'llama2:7b',
                embedding: 'nomic-embed-text',
                code: 'codellama:13b'
            },
            rateLimits: {
                concurrentRequests: 4,
                requestsPerMinute: 60
            },
            features: {
                supportsStreaming: true,
                maxTokens: 4096,
                contextWindow: 4096,
                localDeployment: true
            },
            healthCheck: {
                endpoint: '/api/version',
                interval: 30000,
                timeout: 5000
            },
            performance: {
                timeoutMs: 30000,
                warmupRequests: 3
            },
            environment: 'production'
        });

        // Custom API Templates
        this.addTemplate('custom-api-template', {
            type: 'custom',
            name: 'custom-provider',
            baseUrl: '${CUSTOM_API_BASE_URL}',
            apiKey: '${CUSTOM_API_KEY}',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Version': '1.0'
            },
            endpoints: {
                chat: '/v1/chat/completions',
                completion: '/v1/completions',
                embedding: '/v1/embeddings'
            },
            models: {
                chat: 'custom-chat-model',
                completion: 'custom-completion-model'
            },
            rateLimits: {
                requestsPerMinute: 100,
                tokensPerMinute: 50000
            },
            features: {
                customFormat: true,
                requiresTransformation: true
            },
            transformation: {
                requestFormat: 'custom',
                responseFormat: 'openai-compatible'
            }
        });

        // Multi-Provider Load Balancing Templates
        this.addTemplate('load-balanced-chat', {
            type: 'load-balanced',
            name: 'chat-load-balancer',
            providers: [
                'openai-primary',
                'anthropic-primary',
                'google-ai-primary'
            ],
            strategy: 'round-robin',
            healthCheckInterval: 60000,
            failoverEnabled: true,
            weightedRouting: {
                'openai-primary': 0.5,
                'anthropic-primary': 0.3,
                'google-ai-primary': 0.2
            }
        });

        // Enterprise Multi-Tenant Template
        this.addTemplate('enterprise-tenant', {
            type: 'multi-tenant',
            name: 'enterprise-config',
            tenants: {
                'tenant-1': {
                    primaryProvider: 'openai-primary',
                    fallbackProvider: 'anthropic-primary',
                    quotas: {
                        dailyRequests: 10000,
                        monthlyBudget: 5000
                    }
                },
                'tenant-2': {
                    primaryProvider: 'local-llama',
                    fallbackProvider: 'openai-primary',
                    quotas: {
                        dailyRequests: 5000,
                        monthlyBudget: 1000
                    }
                }
            },
            isolation: {
                networkIsolation: true,
                dataIsolation: true,
                logIsolation: true
            }
        });
    }

    /**
     * Add a new template
     */
    addTemplate(name, config) {
        this.templates.set(name, {
            ...config,
            createdAt: new Date().toISOString(),
            version: '1.0.0'
        });
    }

    /**
     * Get a template by name
     */
    getTemplate(name) {
        return this.templates.get(name);
    }

    /**
     * List all templates
     */
    listTemplates(filter = {}) {
        const templates = Array.from(this.templates.entries()).map(([name, config]) => ({
            name,
            ...config
        }));

        if (filter.type) {
            return templates.filter(t => t.type === filter.type);
        }

        if (filter.environment) {
            return templates.filter(t => t.environment === filter.environment);
        }

        return templates;
    }

    /**
     * Generate tenant-specific configuration
     */
    generateTenantConfig(templateName, tenantId, overrides = {}) {
        const template = this.getTemplate(templateName);
        if (!template) {
            throw new Error(`Template '${templateName}' not found`);
        }

        const tenantConfig = {
            ...template,
            tenant: tenantId,
            name: `${template.name}-${tenantId}`,
            generatedAt: new Date().toISOString(),
            ...overrides
        };

        // Apply tenant-specific environment variable substitutions
        tenantConfig.apiKey = tenantConfig.apiKey.replace('${', `\${${tenantId.toUpperCase()}_`);

        return tenantConfig;
    }

    /**
     * Validate configuration
     */
    validateConfig(config) {
        const required = ['type', 'name', 'baseUrl'];
        const missing = required.filter(field => !config[field]);

        if (missing.length > 0) {
            throw new Error(`Missing required fields: ${missing.join(', ')}`);
        }

        // Type-specific validation
        switch (config.type) {
            case 'openai':
                if (!config.apiKey && !config.apiKey?.includes('${')) {
                    throw new Error('OpenAI provider requires apiKey');
                }
                break;

            case 'anthropic':
                if (!config.apiKey && !config.apiKey?.includes('${')) {
                    throw new Error('Anthropic provider requires apiKey');
                }
                break;

            case 'local':
                if (!config.healthCheck?.endpoint) {
                    throw new Error('Local provider requires healthCheck.endpoint');
                }
                break;

            case 'custom':
                if (!config.endpoints) {
                    throw new Error('Custom provider requires endpoints configuration');
                }
                break;
        }

        return true;
    }

    /**
     * Get recommended template for use case
     */
    getRecommendedTemplate(useCase, constraints = {}) {
        const recommendations = {
            'high-volume-chat': 'openai-production',
            'cost-effective': 'local-llama-production',
            'multi-modal': 'google-ai-production',
            'long-context': 'anthropic-production',
            'development': 'openai-development',
            'enterprise': 'enterprise-tenant',
            'load-balanced': 'load-balanced-chat'
        };

        const templateName = recommendations[useCase];
        if (!templateName) {
            throw new Error(`No recommendation for use case: ${useCase}`);
        }

        let template = this.getTemplate(templateName);

        // Apply constraints
        if (constraints.maxCostPerHour && template.costTracking) {
            template.costTracking.alertThreshold = Math.min(
                template.costTracking.alertThreshold,
                constraints.maxCostPerHour
            );
        }

        if (constraints.maxRequestsPerMinute && template.rateLimits) {
            template.rateLimits.requestsPerMinute = Math.min(
                template.rateLimits.requestsPerMinute,
                constraints.maxRequestsPerMinute
            );
        }

        return template;
    }

    /**
     * Export templates to JSON
     */
    exportTemplates(templateNames = null) {
        const templatesToExport = templateNames
            ? templateNames.map(name => [name, this.getTemplate(name)])
            : Array.from(this.templates.entries());

        return {
            version: '1.0.0',
            exportedAt: new Date().toISOString(),
            templates: Object.fromEntries(templatesToExport)
        };
    }

    /**
     * Import templates from JSON
     */
    importTemplates(data) {
        if (!data.templates) {
            throw new Error('Invalid template data format');
        }

        Object.entries(data.templates).forEach(([name, config]) => {
            this.addTemplate(name, config);
        });

        return Object.keys(data.templates).length;
    }
}

module.exports = ProviderConfigTemplates;