/**
 * BaseProvider - Abstract base class for all AI model providers
 * Defines the standard interface and common functionality
 */

class BaseProvider {
    constructor(config) {
        this.config = config;
        this.name = config.name;
        this.baseUrl = config.baseUrl;
        this.apiKey = config.apiKey;
        this.rateLimiter = null;
        this.healthChecker = null;
        this.costTracker = null;
        this.metrics = {
            requests: 0,
            tokens: 0,
            errors: 0,
            latency: [],
            cost: 0
        };
    }

    /**
     * Abstract method - must be implemented by provider subclasses
     */
    async generateCompletion(request) {
        throw new Error('generateCompletion must be implemented by provider subclass');
    }

    /**
     * Abstract method - must be implemented by provider subclasses
     */
    async generateChatCompletion(messages, options = {}) {
        throw new Error('generateChatCompletion must be implemented by provider subclass');
    }

    /**
     * Abstract method - must be implemented by provider subclasses
     */
    async generateEmbedding(text, options = {}) {
        throw new Error('generateEmbedding must be implemented by provider subclass');
    }

    /**
     * Health check method - can be overridden by providers
     */
    async healthCheck() {
        try {
            const startTime = Date.now();
            await this.ping();
            const latency = Date.now() - startTime;
            return {
                healthy: true,
                latency,
                provider: this.name,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                healthy: false,
                error: error.message,
                provider: this.name,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Provider-specific ping method - should be overridden
     */
    async ping() {
        // Default implementation - providers should override
        const response = await fetch(`${this.baseUrl}/health`, {
            method: 'GET',
            headers: this.getHeaders()
        });

        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }

        return response.json();
    }

    /**
     * Get standard headers for API requests
     */
    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.apiKey}`,
            'User-Agent': 'AI-Orchestration-Framework/1.0.0'
        };
    }

    /**
     * Record metrics for a request
     */
    recordMetrics(type, tokens, cost, latency, error = null) {
        this.metrics.requests++;
        this.metrics.tokens += tokens || 0;
        this.metrics.cost += cost || 0;
        this.metrics.latency.push(latency);

        if (error) {
            this.metrics.errors++;
        }

        // Keep only last 100 latency measurements
        if (this.metrics.latency.length > 100) {
            this.metrics.latency = this.metrics.latency.slice(-100);
        }
    }

    /**
     * Get provider metrics
     */
    getMetrics() {
        const avgLatency = this.metrics.latency.length > 0
            ? this.metrics.latency.reduce((a, b) => a + b, 0) / this.metrics.latency.length
            : 0;

        return {
            ...this.metrics,
            avgLatency,
            uptime: this.getUptime(),
            provider: this.name
        };
    }

    /**
     * Calculate provider uptime
     */
    getUptime() {
        if (!this.startTime) {
            this.startTime = Date.now();
        }
        return Date.now() - this.startTime;
    }

    /**
     * Validate request before processing
     */
    validateRequest(request) {
        if (!request) {
            throw new Error('Request is required');
        }

        if (typeof request !== 'object') {
            throw new Error('Request must be an object');
        }

        return true;
    }

    /**
     * Handle provider-specific errors
     */
    handleError(error, context = {}) {
        const enhancedError = new Error(`[${this.name}] ${error.message}`);
        enhancedError.provider = this.name;
        enhancedError.context = context;
        enhancedError.originalError = error;

        this.recordMetrics('error', 0, 0, 0, enhancedError);

        return enhancedError;
    }

    /**
     * Execute request with retry logic
     */
    async executeWithRetry(fn, maxRetries = 3, delay = 1000) {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await fn();
            } catch (error) {
                lastError = error;

                if (attempt === maxRetries) {
                    break;
                }

                // Exponential backoff
                const waitTime = delay * Math.pow(2, attempt - 1);
                await new Promise(resolve => setTimeout(resolve, waitTime));
            }
        }

        throw this.handleError(lastError, { attempts: maxRetries });
    }

    /**
     * Get provider capabilities
     */
    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: false,
            supportsStreaming: false,
            supportsFunctionCalling: false,
            maxTokens: 4096,
            models: []
        };
    }

    /**
     * Set rate limiter
     */
    setRateLimiter(rateLimiter) {
        this.rateLimiter = rateLimiter;
    }

    /**
     * Set health checker
     */
    setHealthChecker(healthChecker) {
        this.healthChecker = healthChecker;
    }

    /**
     * Set cost tracker
     */
    setCostTracker(costTracker) {
        this.costTracker = costTracker;
    }
}

module.exports = BaseProvider;