/**
 * LocalModelProvider - Local model server integration (Ollama, LM Studio, etc.)
 */

const BaseProvider = require('../core/BaseProvider');

class LocalModelProvider extends BaseProvider {
    constructor(config) {
        super({
            name: config.name || 'local',
            baseUrl: config.baseUrl || 'http://localhost:11434',
            apiKey: config.apiKey || 'not-required',
            ...config
        });

        this.defaultModel = config.defaultModel || 'llama2';
        this.maxTokens = config.maxTokens || 4096;
        this.serverType = config.serverType || 'ollama'; // ollama, lmstudio, vllm, etc.
    }

    async generateChatCompletion(messages, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ messages });

            let request, endpoint;

            switch (this.serverType) {
                case 'ollama':
                    ({ request, endpoint } = this.prepareOllamaRequest(messages, options));
                    break;
                case 'lmstudio':
                    ({ request, endpoint } = this.prepareLMStudioRequest(messages, options));
                    break;
                case 'vllm':
                    ({ request, endpoint } = this.prepareVLLMRequest(messages, options));
                    break;
                default:
                    ({ request, endpoint } = this.prepareOllamaRequest(messages, options));
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Local model API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const content = this.extractContent(result);
            const tokens = this.estimateTokens(messages, content);
            const cost = 0; // Local models are free

            this.recordMetrics('chat_completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || this.defaultModel,
                content: content,
                usage: {
                    prompt_tokens: this.estimateTokens(messages),
                    completion_tokens: this.estimateTokens([{ content }]),
                    total_tokens: tokens
                },
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

            let request, endpoint;

            switch (this.serverType) {
                case 'ollama':
                    request = {
                        model: options.model || this.defaultModel,
                        prompt: prompt,
                        stream: false,
                        options: {
                            temperature: options.temperature || 0.7,
                            top_p: options.topP || 1,
                            num_predict: options.maxTokens || this.maxTokens
                        }
                    };
                    endpoint = '/api/generate';
                    break;
                default:
                    // Fallback to chat completion
                    return this.generateChatCompletion([{ role: 'user', content: prompt }], options);
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Local model API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const content = result.response || result.text || '';
            const tokens = this.estimateTokens([{ content: prompt + content }]);

            this.recordMetrics('completion', tokens, 0, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || this.defaultModel,
                content: content,
                usage: {
                    prompt_tokens: this.estimateTokens([{ content: prompt }]),
                    completion_tokens: this.estimateTokens([{ content }]),
                    total_tokens: tokens
                },
                cost: 0,
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

            let request, endpoint;

            switch (this.serverType) {
                case 'ollama':
                    request = {
                        model: options.model || 'nomic-embed-text',
                        prompt: text
                    };
                    endpoint = '/api/embeddings';
                    break;
                default:
                    throw new Error(`Embedding not supported for server type: ${this.serverType}`);
            }

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Local model API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const tokens = this.estimateTokens([{ content: text }]);

            this.recordMetrics('embedding', tokens, 0, latency);

            return {
                success: true,
                provider: this.name,
                model: options.model || 'nomic-embed-text',
                embedding: result.embedding,
                usage: {
                    prompt_tokens: tokens,
                    completion_tokens: 0,
                    total_tokens: tokens
                },
                cost: 0,
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
            let endpoint;

            switch (this.serverType) {
                case 'ollama':
                    endpoint = '/api/tags';
                    break;
                case 'lmstudio':
                    endpoint = '/v1/models';
                    break;
                case 'vllm':
                    endpoint = '/v1/models';
                    break;
                default:
                    endpoint = '/api/tags';
            }

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
                serverType: this.serverType,
                models: result.models?.length || result.data?.length || 0
            };
        } catch (error) {
            throw new Error(`Local model health check failed: ${error.message}`);
        }
    }

    prepareOllamaRequest(messages, options) {
        const request = {
            model: options.model || this.defaultModel,
            messages: messages,
            stream: false,
            options: {
                temperature: options.temperature || 0.7,
                top_p: options.topP || 1,
                num_predict: options.maxTokens || this.maxTokens
            }
        };

        return { request, endpoint: '/api/chat' };
    }

    prepareLMStudioRequest(messages, options) {
        const request = {
            model: options.model || this.defaultModel,
            messages: messages,
            temperature: options.temperature || 0.7,
            top_p: options.topP || 1,
            max_tokens: options.maxTokens || this.maxTokens,
            stream: false
        };

        return { request, endpoint: '/v1/chat/completions' };
    }

    prepareVLLMRequest(messages, options) {
        const request = {
            model: options.model || this.defaultModel,
            messages: messages,
            temperature: options.temperature || 0.7,
            top_p: options.topP || 1,
            max_tokens: options.maxTokens || this.maxTokens,
            stream: false
        };

        return { request, endpoint: '/v1/chat/completions' };
    }

    extractContent(result) {
        // Handle different response formats
        if (result.message?.content) return result.message.content;
        if (result.choices?.[0]?.message?.content) return result.choices[0].message.content;
        if (result.response) return result.response;
        if (result.text) return result.text;

        return '';
    }

    estimateTokens(messages, additionalContent = '') {
        // Simple token estimation (4 characters ≈ 1 token)
        const text = messages.map(m => m.content || '').join(' ') + additionalContent;
        return Math.ceil(text.length / 4);
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'AI-Orchestration-Framework/1.0.0'
        };

        // Some local servers might still expect auth headers
        if (this.apiKey && this.apiKey !== 'not-required') {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }

        return headers;
    }

    calculateCost(model, usage) {
        return 0; // Local models are free
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: this.serverType === 'ollama',
            supportsStreaming: true,
            supportsFunctionCalling: false,
            maxTokens: this.maxTokens,
            serverType: this.serverType,
            models: [] // Would be populated from actual server
        };
    }
}

module.exports = LocalModelProvider;