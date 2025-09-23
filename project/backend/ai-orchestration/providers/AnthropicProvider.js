/**
 * AnthropicProvider - Anthropic Claude API integration
 */

const BaseProvider = require('../core/BaseProvider');

class AnthropicProvider extends BaseProvider {
    constructor(config) {
        super({
            name: config.name || 'anthropic',
            baseUrl: config.baseUrl || 'https://api.anthropic.com/v1',
            apiKey: config.apiKey,
            ...config
        });

        this.defaultModel = config.defaultModel || 'claude-3-sonnet-20240229';
        this.maxTokens = config.maxTokens || 4096;
        this.anthropicVersion = config.anthropicVersion || '2023-06-01';
    }

    async generateChatCompletion(messages, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ messages });

            // Convert OpenAI-style messages to Anthropic format
            const { system, anthropicMessages } = this.convertMessages(messages);

            const request = {
                model: options.model || this.defaultModel,
                messages: anthropicMessages,
                max_tokens: options.maxTokens || this.maxTokens,
                temperature: options.temperature || 0.7,
                top_p: options.topP || 1,
                stream: options.stream || false,
                ...options.additionalParams
            };

            if (system) {
                request.system = system;
            }

            const response = await fetch(`${this.baseUrl}/messages`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Anthropic API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            // Calculate cost and tokens
            const tokens = result.usage?.input_tokens + result.usage?.output_tokens || 0;
            const cost = this.calculateCost(request.model, result.usage);

            this.recordMetrics('chat_completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: request.model,
                content: result.content[0]?.text,
                usage: {
                    prompt_tokens: result.usage?.input_tokens,
                    completion_tokens: result.usage?.output_tokens,
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
        // Convert to chat completion format for Claude
        const messages = [{ role: 'user', content: prompt }];
        return this.generateChatCompletion(messages, options);
    }

    async generateEmbedding(text, options = {}) {
        // Anthropic doesn't provide embeddings, throw error or use fallback
        throw new Error('Anthropic does not support embeddings. Use a different provider.');
    }

    async ping() {
        try {
            // Use a minimal message to test the API
            const testRequest = {
                model: this.defaultModel,
                messages: [{ role: 'user', content: 'Hello' }],
                max_tokens: 1
            };

            const response = await fetch(`${this.baseUrl}/messages`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(testRequest)
            });

            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }

            return { status: 'healthy', model: this.defaultModel };
        } catch (error) {
            throw new Error(`Anthropic health check failed: ${error.message}`);
        }
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'x-api-key': this.apiKey,
            'anthropic-version': this.anthropicVersion,
            'User-Agent': 'AI-Orchestration-Framework/1.0.0'
        };
    }

    convertMessages(messages) {
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
        if (!usage) return 0;

        // Anthropic pricing (as of 2024 - should be configurable)
        const pricing = {
            'claude-3-opus-20240229': { input: 0.015, output: 0.075 },
            'claude-3-sonnet-20240229': { input: 0.003, output: 0.015 },
            'claude-3-haiku-20240307': { input: 0.00025, output: 0.00125 },
            'claude-2.1': { input: 0.008, output: 0.024 },
            'claude-2.0': { input: 0.008, output: 0.024 },
            'claude-instant-1.2': { input: 0.0008, output: 0.0024 }
        };

        const modelPricing = pricing[model] || pricing['claude-3-sonnet-20240229'];

        const inputCost = (usage.input_tokens || 0) / 1000 * modelPricing.input;
        const outputCost = (usage.output_tokens || 0) / 1000 * modelPricing.output;

        return inputCost + outputCost;
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: false,
            supportsStreaming: true,
            supportsFunctionCalling: false,
            maxTokens: this.maxTokens,
            models: [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
                'claude-2.1',
                'claude-2.0',
                'claude-instant-1.2'
            ]
        };
    }
}

module.exports = AnthropicProvider;