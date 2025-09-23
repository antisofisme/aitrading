/**
 * Integration Adapter - Bridges AI Provider Framework with Trading System
 * Handles request routing, response transformation, and system coordination
 */

const ProviderConfigTemplates = require('./ProviderConfigTemplates');

class IntegrationAdapter {
    constructor(options = {}) {
        this.configTemplates = new ProviderConfigTemplates();
        this.providerRegistry = options.providerRegistry;
        this.centralHub = options.centralHub;
        this.logger = options.logger || console;

        this.routingTable = new Map();
        this.requestQueue = [];
        this.responseCache = new Map();
        this.metrics = {
            totalRequests: 0,
            successfulRequests: 0,
            failedRequests: 0,
            averageLatency: 0,
            providerDistribution: {}
        };

        this.initializeRoutingTable();
    }

    /**
     * Initialize default routing table for different request types
     */
    initializeRoutingTable() {
        // Trading signal analysis
        this.addRoute('trading-signal-analysis', {
            primaryProvider: 'openai-primary',
            fallbackProvider: 'anthropic-primary',
            requestType: 'chat',
            timeout: 5000,
            retries: 2,
            systemPrompt: 'You are an expert trading analyst. Analyze the provided market data and provide actionable trading signals.'
        });

        // Market sentiment analysis
        this.addRoute('market-sentiment', {
            primaryProvider: 'anthropic-primary',
            fallbackProvider: 'google-ai-primary',
            requestType: 'chat',
            timeout: 3000,
            retries: 1,
            systemPrompt: 'Analyze market sentiment from the provided news and data. Return a structured sentiment score and reasoning.'
        });

        // Risk assessment
        this.addRoute('risk-assessment', {
            primaryProvider: 'local-llama',
            fallbackProvider: 'openai-primary',
            requestType: 'chat',
            timeout: 8000,
            retries: 2,
            systemPrompt: 'Evaluate trading risk based on portfolio composition, market conditions, and proposed trades.'
        });

        // Pattern recognition
        this.addRoute('pattern-recognition', {
            primaryProvider: 'google-ai-primary',
            fallbackProvider: 'openai-primary',
            requestType: 'vision',
            timeout: 7000,
            retries: 1,
            systemPrompt: 'Analyze the provided chart patterns and identify technical trading opportunities.'
        });

        // News analysis
        this.addRoute('news-analysis', {
            primaryProvider: 'anthropic-primary',
            fallbackProvider: 'openai-primary',
            requestType: 'chat',
            timeout: 4000,
            retries: 2,
            systemPrompt: 'Analyze financial news and extract actionable insights for trading decisions.'
        });
    }

    /**
     * Add a new routing rule
     */
    addRoute(routeName, config) {
        this.routingTable.set(routeName, {
            ...config,
            createdAt: new Date().toISOString(),
            requestCount: 0,
            successRate: 0
        });
    }

    /**
     * Process AI request with intelligent routing
     */
    async processRequest(requestType, payload, options = {}) {
        const startTime = Date.now();
        const route = this.routingTable.get(requestType);

        if (!route) {
            throw new Error(`No route configured for request type: ${requestType}`);
        }

        try {
            this.metrics.totalRequests++;
            route.requestCount++;

            // Prepare request based on route configuration
            const request = this.prepareRequest(route, payload, options);

            // Execute with provider selection and failover
            const response = await this.executeWithFailover(route, request, options);

            // Transform response
            const transformedResponse = this.transformResponse(response, requestType, options);

            // Record success metrics
            const latency = Date.now() - startTime;
            this.recordSuccess(requestType, route.primaryProvider, latency);

            // Cache response if applicable
            if (options.cache) {
                this.cacheResponse(request, transformedResponse, options.cacheTTL);
            }

            return transformedResponse;

        } catch (error) {
            const latency = Date.now() - startTime;
            this.recordFailure(requestType, error, latency);
            throw error;
        }
    }

    /**
     * Prepare request based on route configuration
     */
    prepareRequest(route, payload, options) {
        const request = {
            type: route.requestType,
            timestamp: new Date().toISOString(),
            route: route,
            payload: payload,
            options: options
        };

        // Add system prompt if configured
        if (route.systemPrompt && route.requestType === 'chat') {
            request.messages = [
                { role: 'system', content: route.systemPrompt },
                ...(payload.messages || [{ role: 'user', content: payload.content || payload }])
            ];
        } else if (route.requestType === 'completion') {
            request.prompt = payload.prompt || payload;
        } else if (route.requestType === 'embedding') {
            request.text = payload.text || payload;
        }

        // Apply request transformations
        if (options.temperature) request.temperature = options.temperature;
        if (options.maxTokens) request.maxTokens = options.maxTokens;
        if (options.model) request.model = options.model;

        return request;
    }

    /**
     * Execute request with provider failover
     */
    async executeWithFailover(route, request, options) {
        const providers = [route.primaryProvider];
        if (route.fallbackProvider) {
            providers.push(route.fallbackProvider);
        }

        let lastError;

        for (const providerName of providers) {
            try {
                const provider = this.providerRegistry.getProvider(providerName, options.tenant);
                if (!provider) {
                    throw new Error(`Provider ${providerName} not found`);
                }

                // Check provider health
                const health = await provider.healthCheck();
                if (!health.healthy) {
                    throw new Error(`Provider ${providerName} is unhealthy: ${health.error}`);
                }

                // Execute request based on type
                let response;
                switch (request.type) {
                    case 'chat':
                        response = await provider.generateChatCompletion(
                            request.messages,
                            {
                                model: request.model,
                                temperature: request.temperature,
                                maxTokens: request.maxTokens
                            }
                        );
                        break;
                    case 'completion':
                        response = await provider.generateCompletion({
                            prompt: request.prompt,
                            model: request.model,
                            temperature: request.temperature,
                            maxTokens: request.maxTokens
                        });
                        break;
                    case 'embedding':
                        response = await provider.generateEmbedding(request.text);
                        break;
                    default:
                        throw new Error(`Unsupported request type: ${request.type}`);
                }

                // Record provider success
                this.recordProviderUsage(providerName, true);
                return response;

            } catch (error) {
                lastError = error;
                this.recordProviderUsage(providerName, false);
                this.logger.warn(`Provider ${providerName} failed:`, error.message);

                // Continue to next provider if available
                continue;
            }
        }

        throw lastError || new Error('All providers failed');
    }

    /**
     * Transform response based on request type and requirements
     */
    transformResponse(response, requestType, options) {
        const transformed = {
            requestType,
            timestamp: new Date().toISOString(),
            success: true,
            data: response
        };

        // Add trading-specific transformations
        switch (requestType) {
            case 'trading-signal-analysis':
                transformed.tradingSignal = this.extractTradingSignal(response);
                break;
            case 'market-sentiment':
                transformed.sentiment = this.extractSentiment(response);
                break;
            case 'risk-assessment':
                transformed.riskScore = this.extractRiskScore(response);
                break;
            case 'pattern-recognition':
                transformed.patterns = this.extractPatterns(response);
                break;
            case 'news-analysis':
                transformed.insights = this.extractInsights(response);
                break;
        }

        // Add metadata
        transformed.metadata = {
            processingTime: Date.now() - new Date(transformed.timestamp).getTime(),
            confidence: this.calculateConfidence(response, requestType),
            source: 'ai-integration-adapter'
        };

        return transformed;
    }

    /**
     * Extract trading signal from AI response
     */
    extractTradingSignal(response) {
        const content = response.choices?.[0]?.message?.content || response.content || response;

        // Parse structured trading signal
        try {
            if (typeof content === 'string' && content.includes('{')) {
                const jsonMatch = content.match(/\{[^}]+\}/);
                if (jsonMatch) {
                    return JSON.parse(jsonMatch[0]);
                }
            }
        } catch (e) {
            // Fallback to pattern extraction
        }

        return {
            action: this.extractAction(content),
            confidence: this.extractConfidenceScore(content),
            reasoning: content,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Extract sentiment score from response
     */
    extractSentiment(response) {
        const content = response.choices?.[0]?.message?.content || response.content || response;

        return {
            score: this.extractNumericScore(content, 'sentiment'),
            label: this.extractSentimentLabel(content),
            reasoning: content
        };
    }

    /**
     * Extract risk score from response
     */
    extractRiskScore(response) {
        const content = response.choices?.[0]?.message?.content || response.content || response;

        return {
            score: this.extractNumericScore(content, 'risk'),
            level: this.extractRiskLevel(content),
            factors: this.extractRiskFactors(content),
            recommendations: this.extractRecommendations(content)
        };
    }

    /**
     * Extract patterns from chart analysis
     */
    extractPatterns(response) {
        const content = response.choices?.[0]?.message?.content || response.content || response;

        return {
            identified: this.extractPatternList(content),
            strength: this.extractNumericScore(content, 'strength'),
            direction: this.extractDirection(content),
            timeframe: this.extractTimeframe(content)
        };
    }

    /**
     * Extract insights from news analysis
     */
    extractInsights(response) {
        const content = response.choices?.[0]?.message?.content || response.content || response;

        return {
            summary: this.extractSummary(content),
            impact: this.extractImpact(content),
            assets: this.extractAffectedAssets(content),
            timeline: this.extractTimeline(content)
        };
    }

    /**
     * Helper methods for content extraction
     */
    extractAction(content) {
        const actions = ['BUY', 'SELL', 'HOLD', 'WAIT'];
        for (const action of actions) {
            if (content.toUpperCase().includes(action)) {
                return action;
            }
        }
        return 'HOLD';
    }

    extractConfidenceScore(content) {
        const matches = content.match(/confidence[:\s]+(\d+(?:\.\d+)?)/i);
        return matches ? parseFloat(matches[1]) : 0.5;
    }

    extractNumericScore(content, type) {
        const pattern = new RegExp(`${type}[:\s]+(\d+(?:\.\d+)?)`, 'i');
        const matches = content.match(pattern);
        return matches ? parseFloat(matches[1]) : 0.5;
    }

    extractSentimentLabel(content) {
        const labels = ['BULLISH', 'BEARISH', 'NEUTRAL'];
        for (const label of labels) {
            if (content.toUpperCase().includes(label)) {
                return label;
            }
        }
        return 'NEUTRAL';
    }

    extractRiskLevel(content) {
        const levels = ['HIGH', 'MEDIUM', 'LOW'];
        for (const level of levels) {
            if (content.toUpperCase().includes(level)) {
                return level;
            }
        }
        return 'MEDIUM';
    }

    /**
     * Calculate confidence based on response quality
     */
    calculateConfidence(response, requestType) {
        let confidence = 0.5;

        const content = response.choices?.[0]?.message?.content || response.content || response;

        // Length-based confidence
        if (content.length > 100) confidence += 0.1;
        if (content.length > 500) confidence += 0.1;

        // Structure-based confidence
        if (content.includes('{') || content.includes('[')) confidence += 0.1;
        if (content.includes('confidence') || content.includes('score')) confidence += 0.1;

        // Request-type specific confidence
        switch (requestType) {
            case 'trading-signal-analysis':
                if (content.match(/BUY|SELL|HOLD/i)) confidence += 0.2;
                break;
            case 'market-sentiment':
                if (content.match(/BULLISH|BEARISH|NEUTRAL/i)) confidence += 0.2;
                break;
        }

        return Math.min(confidence, 1.0);
    }

    /**
     * Cache response for future use
     */
    cacheResponse(request, response, ttl = 300000) {
        const key = this.generateCacheKey(request);
        const cacheEntry = {
            response,
            timestamp: Date.now(),
            ttl
        };

        this.responseCache.set(key, cacheEntry);

        // Cleanup expired entries
        this.cleanupCache();
    }

    /**
     * Generate cache key from request
     */
    generateCacheKey(request) {
        const keyData = {
            type: request.type,
            prompt: request.prompt || JSON.stringify(request.messages),
            model: request.model
        };

        return JSON.stringify(keyData);
    }

    /**
     * Cleanup expired cache entries
     */
    cleanupCache() {
        const now = Date.now();
        for (const [key, entry] of this.responseCache.entries()) {
            if (now - entry.timestamp > entry.ttl) {
                this.responseCache.delete(key);
            }
        }
    }

    /**
     * Record metrics
     */
    recordSuccess(requestType, provider, latency) {
        this.metrics.successfulRequests++;
        this.updateAverageLatency(latency);
        this.recordProviderUsage(provider, true);

        const route = this.routingTable.get(requestType);
        if (route) {
            route.successRate = route.successRate * 0.9 + 0.1; // Moving average
        }
    }

    recordFailure(requestType, error, latency) {
        this.metrics.failedRequests++;
        this.updateAverageLatency(latency);

        const route = this.routingTable.get(requestType);
        if (route) {
            route.successRate = route.successRate * 0.9; // Moving average
        }
    }

    recordProviderUsage(provider, success) {
        if (!this.metrics.providerDistribution[provider]) {
            this.metrics.providerDistribution[provider] = {
                requests: 0,
                successes: 0,
                failures: 0
            };
        }

        this.metrics.providerDistribution[provider].requests++;
        if (success) {
            this.metrics.providerDistribution[provider].successes++;
        } else {
            this.metrics.providerDistribution[provider].failures++;
        }
    }

    updateAverageLatency(latency) {
        const totalRequests = this.metrics.totalRequests;
        this.metrics.averageLatency =
            (this.metrics.averageLatency * (totalRequests - 1) + latency) / totalRequests;
    }

    /**
     * Get adapter metrics
     */
    getMetrics() {
        return {
            ...this.metrics,
            routingTable: Object.fromEntries(this.routingTable),
            cacheSize: this.responseCache.size,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const providerHealths = await Promise.all(
                Array.from(this.routingTable.values())
                    .map(route => route.primaryProvider)
                    .map(async provider => {
                        try {
                            const p = this.providerRegistry.getProvider(provider);
                            return p ? await p.healthCheck() : { healthy: false };
                        } catch {
                            return { healthy: false };
                        }
                    })
            );

            const healthyProviders = providerHealths.filter(h => h.healthy).length;
            const totalProviders = providerHealths.length;

            return {
                healthy: healthyProviders > 0,
                adapters: {
                    total: totalProviders,
                    healthy: healthyProviders,
                    unhealthy: totalProviders - healthyProviders
                },
                cache: {
                    size: this.responseCache.size,
                    healthy: true
                },
                metrics: this.metrics
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message
            };
        }
    }
}

module.exports = IntegrationAdapter;