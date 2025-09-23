/**
 * GoogleAIProvider - Google AI (Gemini) API integration
 */

const BaseProvider = require('../core/BaseProvider');

class GoogleAIProvider extends BaseProvider {
    constructor(config) {
        super({
            name: config.name || 'google',
            baseUrl: config.baseUrl || 'https://generativelanguage.googleapis.com/v1beta',
            apiKey: config.apiKey,
            ...config
        });

        this.defaultModel = config.defaultModel || 'gemini-pro';
        this.maxTokens = config.maxTokens || 4096;
    }

    async generateChatCompletion(messages, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ messages });

            const model = options.model || this.defaultModel;
            const geminiMessages = this.convertMessages(messages);

            const request = {
                contents: geminiMessages,
                generationConfig: {
                    maxOutputTokens: options.maxTokens || this.maxTokens,
                    temperature: options.temperature || 0.7,
                    topP: options.topP || 1,
                    topK: options.topK || 40,
                    ...options.additionalParams
                }
            };

            const response = await fetch(
                `${this.baseUrl}/models/${model}:generateContent?key=${this.apiKey}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'AI-Orchestration-Framework/1.0.0'
                    },
                    body: JSON.stringify(request)
                }
            );

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Google AI API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            // Extract content and calculate metrics
            const content = result.candidates?.[0]?.content?.parts?.[0]?.text;
            const usage = this.extractUsage(result);
            const tokens = usage.totalTokens;
            const cost = this.calculateCost(model, usage);

            this.recordMetrics('chat_completion', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: model,
                content: content,
                usage: {
                    prompt_tokens: usage.promptTokens,
                    completion_tokens: usage.completionTokens,
                    total_tokens: usage.totalTokens
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
        // Convert to chat completion format
        const messages = [{ role: 'user', content: prompt }];
        return this.generateChatCompletion(messages, options);
    }

    async generateEmbedding(text, options = {}) {
        const startTime = Date.now();

        try {
            this.validateRequest({ text });

            const model = options.model || 'embedding-001';

            const request = {
                model: `models/${model}`,
                content: {
                    parts: [{ text: text }]
                }
            };

            const response = await fetch(
                `${this.baseUrl}/models/${model}:embedContent?key=${this.apiKey}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'AI-Orchestration-Framework/1.0.0'
                    },
                    body: JSON.stringify(request)
                }
            );

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`Google AI API error: ${response.status} - ${error}`);
            }

            const result = await response.json();
            const latency = Date.now() - startTime;

            const tokens = text.split(' ').length; // Rough estimate
            const cost = this.calculateCost(model, { totalTokens: tokens });

            this.recordMetrics('embedding', tokens, cost, latency);

            return {
                success: true,
                provider: this.name,
                model: model,
                embedding: result.embedding?.values,
                usage: {
                    prompt_tokens: tokens,
                    completion_tokens: 0,
                    total_tokens: tokens
                },
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
            const response = await fetch(
                `${this.baseUrl}/models?key=${this.apiKey}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'User-Agent': 'AI-Orchestration-Framework/1.0.0'
                    }
                }
            );

            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }

            const result = await response.json();
            return {
                status: 'healthy',
                models: result.models?.length || 0
            };
        } catch (error) {
            throw new Error(`Google AI health check failed: ${error.message}`);
        }
    }

    convertMessages(messages) {
        const geminiMessages = [];

        for (const message of messages) {
            if (message.role === 'system') {
                // Gemini doesn't have system messages, prepend to first user message
                continue;
            }

            const role = message.role === 'assistant' ? 'model' : 'user';

            geminiMessages.push({
                role: role,
                parts: [{ text: message.content }]
            });
        }

        // Add system message to first user message if present
        const systemMessage = messages.find(m => m.role === 'system');
        if (systemMessage && geminiMessages.length > 0 && geminiMessages[0].role === 'user') {
            geminiMessages[0].parts[0].text =
                `${systemMessage.content}\n\n${geminiMessages[0].parts[0].text}`;
        }

        return geminiMessages;
    }

    extractUsage(result) {
        const metadata = result.usageMetadata || {};
        return {
            promptTokens: metadata.promptTokenCount || 0,
            completionTokens: metadata.candidatesTokenCount || 0,
            totalTokens: metadata.totalTokenCount || 0
        };
    }

    calculateCost(model, usage) {
        if (!usage) return 0;

        // Google AI pricing (as of 2024 - should be configurable)
        const pricing = {
            'gemini-pro': { input: 0.0005, output: 0.0015 },
            'gemini-pro-vision': { input: 0.0005, output: 0.0015 },
            'gemini-ultra': { input: 0.005, output: 0.015 },
            'embedding-001': { input: 0.0001, output: 0 }
        };

        const modelPricing = pricing[model] || pricing['gemini-pro'];

        const inputCost = (usage.promptTokens || usage.totalTokens || 0) / 1000 * modelPricing.input;
        const outputCost = (usage.completionTokens || 0) / 1000 * modelPricing.output;

        return inputCost + outputCost;
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: true,
            supportsStreaming: false,
            supportsFunctionCalling: false,
            maxTokens: this.maxTokens,
            models: [
                'gemini-pro',
                'gemini-pro-vision',
                'gemini-ultra',
                'embedding-001'
            ]
        };
    }
}

module.exports = GoogleAIProvider;