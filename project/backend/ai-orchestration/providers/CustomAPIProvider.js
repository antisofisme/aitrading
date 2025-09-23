/**
 * CustomAPIProvider - Generic provider for custom API endpoints
 */

const BaseProvider = require('../core/BaseProvider');

class CustomAPIProvider extends BaseProvider {
    constructor(config) {
        super({
            name: config.name || 'custom',
            baseUrl: config.baseUrl,
            apiKey: config.apiKey,
            ...config
        });

        this.defaultModel = config.defaultModel || 'default';
        this.maxTokens = config.maxTokens || 4096;

        // Custom API configuration
        this.endpoints = config.endpoints || {};
        this.authMethod = config.authMethod || 'bearer'; // bearer, api-key, basic, custom
        this.requestFormat = config.requestFormat || 'openai'; // openai, anthropic, custom
        this.responseFormat = config.responseFormat || 'openai'; // openai, anthropic, custom
        this.customHeaders = config.customHeaders || {};
        this.transformRequest = config.transformRequest;
        this.transformResponse = config.transformResponse;
    }

    async generateChatCompletion(messages, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ messages });

            const endpoint = this.endpoints.chatCompletion || '/v1/chat/completions';
            let request = this.buildRequest(messages, options, 'chat');

            // Apply custom request transformation
            if (this.transformRequest) {
                request = this.transformRequest(request, 'chat');
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Custom API error: ${response.status} - ${error}`);
            }

            let result = await response.json();

            // Apply custom response transformation
            if (this.transformResponse) {
                result = this.transformResponse(result, 'chat');
            }

            const latency = Date.now() - startTime;
            const content = this.extractContent(result);
            const usage = this.extractUsage(result);
            const tokens = usage.total_tokens;
            const cost = this.calculateCost(options.model || this.defaultModel, usage);

            this.recordMetrics('chat_completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || this.defaultModel,
                content: content,
                usage: usage,
                cost,
                latency,
                raw: result
            };

        } catch (error) {
            const latency = Date.now() - startTime;
            this.recordMetrics('chat_completion', 0, 0, latency, error);
            throw this.handleError(error, { method: 'generateChatCompletion', options });
        }
    }

    async generateCompletion(prompt, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ prompt });

            const endpoint = this.endpoints.completion || '/v1/completions';
            let request = this.buildCompletionRequest(prompt, options);

            if (this.transformRequest) {
                request = this.transformRequest(request, 'completion');
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Custom API error: ${response.status} - ${error}`);
            }

            let result = await response.json();

            if (this.transformResponse) {
                result = this.transformResponse(result, 'completion');
            }

            const latency = Date.now() - startTime;
            const content = this.extractContent(result);
            const usage = this.extractUsage(result);
            const tokens = usage.total_tokens;
            const cost = this.calculateCost(options.model || this.defaultModel, usage);

            this.recordMetrics('completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || this.defaultModel,
                content: content,
                usage: usage,
                cost,
                latency,
                raw: result
            };

        } catch (error) {
            const latency = Date.now() - startTime;
            this.recordMetrics('completion', 0, 0, latency, error);
            throw this.handleError(error, { method: 'generateCompletion', options });
        }
    }

    async generateEmbedding(text, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ text });

            const endpoint = this.endpoints.embedding || '/v1/embeddings';
            let request = this.buildEmbeddingRequest(text, options);

            if (this.transformRequest) {
                request = this.transformRequest(request, 'embedding');
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Custom API error: ${response.status} - ${error}`);
            }

            let result = await response.json();

            if (this.transformResponse) {
                result = this.transformResponse(result, 'embedding');
            }

            const latency = Date.now() - startTime;
            const embedding = this.extractEmbedding(result);
            const usage = this.extractUsage(result);
            const tokens = usage.total_tokens;
            const cost = this.calculateCost(options.model || this.defaultModel, usage);

            this.recordMetrics('embedding', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || this.defaultModel,
                embedding: embedding,
                usage: usage,
                cost,
                latency,
                raw: result
            };

        } catch (error) {
            const latency = Date.now() - startTime;
            this.recordMetrics('embedding', 0, 0, latency, error);
            throw this.handleError(error, { method: 'generateEmbedding', options });
        }
    }

    async ping() {
        try {
            const endpoint = this.endpoints.health || this.endpoints.models || '/v1/models';

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }

            const result = await response.json();
            return {
                status: 'healthy',
                endpoint: endpoint,
                data: result
            };
        } catch (error) {
            throw new Error(`Custom API health check failed: ${error.message}`);
        }
    }

    buildRequest(messages, options, type) {
        switch (this.requestFormat) {
            case 'openai':
                return {
                    model: options.model || this.defaultModel,
                    messages: messages,
                    max_tokens: options.maxTokens || this.maxTokens,
                    temperature: options.temperature || 0.7,
                    top_p: options.topP || 1,
                    stream: options.stream || false,
                    ...options.additionalParams
                };

            case 'anthropic':
                const { system, anthropicMessages } = this.convertToAnthropicFormat(messages);
                const request = {
                    model: options.model || this.defaultModel,
                    messages: anthropicMessages,
                    max_tokens: options.maxTokens || this.maxTokens,
                    temperature: options.temperature || 0.7,
                    stream: options.stream || false,
                    ...options.additionalParams
                };
                if (system) request.system = system;
                return request;

            case 'custom':
                // Return as-is for custom handling
                return {
                    messages: messages,
                    options: options
                };

            default:
                throw new Error(`Unknown request format: ${this.requestFormat}`);
        }
    }

    buildCompletionRequest(prompt, options) {
        return {
            model: options.model || this.defaultModel,
            prompt: prompt,
            max_tokens: options.maxTokens || this.maxTokens,
            temperature: options.temperature || 0.7,
            top_p: options.topP || 1,
            stream: options.stream || false,
            ...options.additionalParams
        };
    }

    buildEmbeddingRequest(text, options) {
        return {
            model: options.model || 'embedding-model',
            input: text,
            ...options.additionalParams
        };
    }

    extractContent(result) {
        // Try different response formats
        if (result.choices?.[0]?.message?.content) return result.choices[0].message.content;
        if (result.choices?.[0]?.text) return result.choices[0].text;
        if (result.content?.[0]?.text) return result.content[0].text;
        if (result.message?.content) return result.message.content;
        if (result.response) return result.response;
        if (result.text) return result.text;
        if (result.output) return result.output;

        return '';
    }

    extractEmbedding(result) {
        if (result.data?.[0]?.embedding) return result.data[0].embedding;
        if (result.embedding?.values) return result.embedding.values;
        if (result.embedding) return result.embedding;
        if (result.vector) return result.vector;

        return null;
    }

    extractUsage(result) {
        // Try different usage formats
        if (result.usage) {
            return {
                prompt_tokens: result.usage.prompt_tokens || result.usage.input_tokens || 0,
                completion_tokens: result.usage.completion_tokens || result.usage.output_tokens || 0,
                total_tokens: result.usage.total_tokens || 0
            };
        }

        // Estimate if no usage provided
        return {
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0
        };
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Orchestration-Framework/1.0.0',
            ...this.customHeaders
        };

        // Add authentication based on method
        switch (this.authMethod) {
            case 'bearer':
                if (this.apiKey) {
                    headers['Authorization'] = `Bearer ${this.apiKey}`;
                }
                break;

            case 'api-key':
                if (this.apiKey) {
                    headers['X-API-Key'] = this.apiKey;
                }
                break;

            case 'basic':
                if (this.apiKey) {
                    headers['Authorization'] = `Basic ${Buffer.from(this.apiKey).toString('base64')}`;
                }
                break;

            case 'custom':
                // Custom headers should be provided in customHeaders
                break;
        }

        return headers;
    }

    convertToAnthropicFormat(messages) {
        let system = '';
        const anthropicMessages = [];

        for (const message of messages) {
            if (message.role === 'system') {
                system += (system ? '\n\n' : '') + message.content;
            } else {
                anthropicMessages.push({
                    role: message.role === 'assistant' ? 'assistant' : 'user',
                    content: message.content
                });
            }
        }

        return { system, anthropicMessages };
    }

    calculateCost(model, usage) {
        // Default to zero unless custom pricing is provided
        if (this.pricing && this.pricing[model]) {
            const modelPricing = this.pricing[model];
            const inputCost = (usage.prompt_tokens || 0) / 1000 * modelPricing.input;
            const outputCost = (usage.completion_tokens || 0) / 1000 * modelPricing.output;
            return inputCost + outputCost;
        }

        return 0;
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: !!this.endpoints.chatCompletion,
            supportsCompletion: !!this.endpoints.completion,
            supportsEmbedding: !!this.endpoints.embedding,
            supportsStreaming: false,
            supportsFunctionCalling: false,
            maxTokens: this.maxTokens,
            requestFormat: this.requestFormat,
            responseFormat: this.responseFormat,
            authMethod: this.authMethod,
            models: []
        };
    }
}

module.exports = CustomAPIProvider;