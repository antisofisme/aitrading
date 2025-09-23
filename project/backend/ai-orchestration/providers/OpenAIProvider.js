/**
 * OpenAIProvider - OpenAI API integration
 */

const BaseProvider = require('../core/BaseProvider');

class OpenAIProvider extends BaseProvider {
    constructor(config) {
        super({
            name: config.name || 'openai',
            baseUrl: config.baseUrl || 'https://api.openai.com/v1',
            apiKey: config.apiKey,
            ...config
        });

        this.organization = config.organization;
        this.defaultModel = config.defaultModel || 'gpt-3.5-turbo';
        this.maxTokens = config.maxTokens || 4096;
    }

    async generateChatCompletion(messages, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ messages });

            const request = {
                model: options.model || this.defaultModel,
                messages: messages,
                max_tokens: options.maxTokens || this.maxTokens,
                temperature: options.temperature || 0.7,
                top_p: options.topP || 1,
                frequency_penalty: options.frequencyPenalty || 0,
                presence_penalty: options.presencePenalty || 0,
                stream: options.stream || false,
                ...options.additionalParams
            };

            if (options.functions) {
                request.functions = options.functions;
            }

            if (options.functionCall) {
                request.function_call = options.functionCall;
            }

            const response = await fetch(`${this.baseUrl}/chat/completions`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`OpenAI API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            // Calculate cost and tokens
            const tokens = result.usage?.total_tokens || 0;
            const cost = this.calculateCost(request.model, result.usage);

            this.recordMetrics('chat_completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: request.model,
                content: result.choices[0]?.message?.content,
                functionCall: result.choices[0]?.message?.function_call,
                usage: result.usage,
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

            const request = {
                model: options.model || 'text-davinci-003',
                prompt: prompt,
                max_tokens: options.maxTokens || this.maxTokens,
                temperature: options.temperature || 0.7,
                top_p: options.topP || 1,
                frequency_penalty: options.frequencyPenalty || 0,
                presence_penalty: options.presencePenalty || 0,
                stream: options.stream || false,
                ...options.additionalParams
            };

            const response = await fetch(`${this.baseUrl}/completions`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`OpenAI API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const tokens = result.usage?.total_tokens || 0;
            const cost = this.calculateCost(request.model, result.usage);

            this.recordMetrics('completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: request.model,
                content: result.choices[0]?.text,
                usage: result.usage,
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

            const request = {
                model: options.model || 'text-embedding-ada-002',
                input: text,
                ...options.additionalParams
            };

            const response = await fetch(`${this.baseUrl}/embeddings`, {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`OpenAI API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const tokens = result.usage?.total_tokens || 0;
            const cost = this.calculateCost(request.model, result.usage);

            this.recordMetrics('embedding', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: request.model,
                embedding: result.data[0]?.embedding,
                usage: result.usage,
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
            const response = await fetch(`${this.baseUrl}/models`, {
                method: 'GET',
                headers: this.getHeaders()
            });

            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }

            return { status: 'healthy', models: (await response.json()).data.length };
        } catch (error) {
            throw new Error(`OpenAI health check failed: ${error.message}`);
        }
    }

    getHeaders() {
        const headers = super.getHeaders();

        if (this.organization) {
            headers['OpenAI-Organization'] = this.organization;
        }

        return headers;
    }

    calculateCost(model, usage) {
        if (!usage) return 0;

        // OpenAI pricing (as of 2024 - should be configurable)
        const pricing = {
            'gpt-4': { input: 0.03, output: 0.06 },
            'gpt-4-32k': { input: 0.06, output: 0.12 },
            'gpt-3.5-turbo': { input: 0.001, output: 0.002 },
            'gpt-3.5-turbo-16k': { input: 0.003, output: 0.004 },
            'text-davinci-003': { input: 0.02, output: 0.02 },
            'text-embedding-ada-002': { input: 0.0001, output: 0 }
        };

        const modelPricing = pricing[model] || pricing['gpt-3.5-turbo'];

        const inputCost = (usage.prompt_tokens || 0) / 1000 * modelPricing.input;
        const outputCost = (usage.completion_tokens || 0) / 1000 * modelPricing.output;

        return inputCost + outputCost;
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: true,
            supportsStreaming: true,
            supportsFunctionCalling: true,
            maxTokens: this.maxTokens,
            models: [
                'gpt-4',
                'gpt-4-32k',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
                'text-davinci-003',
                'text-embedding-ada-002'
            ]
        };
    }
}

module.exports = OpenAIProvider;