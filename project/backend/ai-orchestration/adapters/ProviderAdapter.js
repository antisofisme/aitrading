/**
 * ProviderAdapter - Request/Response adapter for different AI provider formats
 */

class ProviderAdapter {
    constructor(options = {}) {
        this.adapters = new Map();
        this.setupDefaultAdapters();
    }

    /**
     * Setup default adapters for common providers
     */
    setupDefaultAdapters() {
        // OpenAI format adapter
        this.registerAdapter('openai', {
            adaptRequest: this.adaptOpenAIRequest.bind(this),
            adaptResponse: this.adaptOpenAIResponse.bind(this)
        });

        // Anthropic format adapter
        this.registerAdapter('anthropic', {
            adaptRequest: this.adaptAnthropicRequest.bind(this),
            adaptResponse: this.adaptAnthropicResponse.bind(this)
        });

        // Google AI format adapter
        this.registerAdapter('google', {
            adaptRequest: this.adaptGoogleRequest.bind(this),
            adaptResponse: this.adaptGoogleResponse.bind(this)
        });

        // Local model adapter (Ollama style)
        this.registerAdapter('ollama', {
            adaptRequest: this.adaptOllamaRequest.bind(this),
            adaptResponse: this.adaptOllamaResponse.bind(this)
        });

        // LM Studio adapter (OpenAI compatible)
        this.registerAdapter('lmstudio', {
            adaptRequest: this.adaptOpenAIRequest.bind(this),
            adaptResponse: this.adaptOpenAIResponse.bind(this)
        });

        // Generic adapter for unknown formats
        this.registerAdapter('generic', {
            adaptRequest: this.adaptGenericRequest.bind(this),
            adaptResponse: this.adaptGenericResponse.bind(this)
        });
    }

    /**
     * Register a custom adapter
     */
    registerAdapter(name, adapter) {
        this.adapters.set(name, adapter);
    }

    /**
     * Adapt request to provider format
     */
    async adaptRequest(providerType, request, options = {}) {
        const adapter = this.adapters.get(providerType) || this.adapters.get('generic');
        return adapter.adaptRequest(request, options);
    }

    /**
     * Adapt response from provider format
     */
    async adaptResponse(providerType, response, options = {}) {
        const adapter = this.adapters.get(providerType) || this.adapters.get('generic');
        return adapter.adaptResponse(response, options);
    }

    /**
     * OpenAI request adapter
     */
    adaptOpenAIRequest(request, options = {}) {
        const { type, messages, prompt, text, model, ...params } = request;

        switch (type) {
            case 'chat':
                return {
                    model: model || 'gpt-3.5-turbo',
                    messages: messages,
                    max_tokens: params.maxTokens || 4096,
                    temperature: params.temperature || 0.7,
                    top_p: params.topP || 1,
                    frequency_penalty: params.frequencyPenalty || 0,
                    presence_penalty: params.presencePenalty || 0,
                    stream: params.stream || false,
                    ...params.additionalParams
                };

            case 'completion':
                return {
                    model: model || 'text-davinci-003',
                    prompt: prompt,
                    max_tokens: params.maxTokens || 4096,
                    temperature: params.temperature || 0.7,
                    top_p: params.topP || 1,
                    frequency_penalty: params.frequencyPenalty || 0,
                    presence_penalty: params.presencePenalty || 0,
                    stream: params.stream || false,
                    ...params.additionalParams
                };

            case 'embedding':
                return {
                    model: model || 'text-embedding-ada-002',
                    input: text,
                    ...params.additionalParams
                };

            default:
                throw new Error(`Unsupported request type: ${type}`);
        }
    }

    /**
     * OpenAI response adapter
     */
    adaptOpenAIResponse(response, options = {}) {
        const { type } = options;

        switch (type) {
            case 'chat':
                return {
                    content: response.choices?.[0]?.message?.content || '',
                    functionCall: response.choices?.[0]?.message?.function_call,
                    finishReason: response.choices?.[0]?.finish_reason,
                    usage: response.usage,
                    model: response.model
                };

            case 'completion':
                return {
                    content: response.choices?.[0]?.text || '',
                    finishReason: response.choices?.[0]?.finish_reason,
                    usage: response.usage,
                    model: response.model
                };

            case 'embedding':
                return {
                    embedding: response.data?.[0]?.embedding || [],
                    usage: response.usage,
                    model: response.model
                };

            default:
                return response;
        }
    }

    /**
     * Anthropic request adapter
     */
    adaptAnthropicRequest(request, options = {}) {
        const { type, messages, prompt, model, ...params } = request;

        if (type === 'chat' || type === 'completion') {
            const { system, anthropicMessages } = this.convertToAnthropicMessages(
                type === 'chat' ? messages : [{ role: 'user', content: prompt }]
            );

            const adaptedRequest = {
                model: model || 'claude-3-sonnet-20240229',
                messages: anthropicMessages,
                max_tokens: params.maxTokens || 4096,
                temperature: params.temperature || 0.7,
                top_p: params.topP || 1,
                stream: params.stream || false,
                ...params.additionalParams
            };

            if (system) {
                adaptedRequest.system = system;
            }

            return adaptedRequest;
        }

        if (type === 'embedding') {
            throw new Error('Anthropic does not support embeddings');
        }

        throw new Error(`Unsupported request type: ${type}`);
    }

    /**
     * Anthropic response adapter
     */
    adaptAnthropicResponse(response, options = {}) {
        return {
            content: response.content?.[0]?.text || '',
            finishReason: response.stop_reason,
            usage: {
                prompt_tokens: response.usage?.input_tokens || 0,
                completion_tokens: response.usage?.output_tokens || 0,
                total_tokens: (response.usage?.input_tokens || 0) + (response.usage?.output_tokens || 0)
            },
            model: response.model
        };
    }

    /**
     * Google AI request adapter
     */
    adaptGoogleRequest(request, options = {}) {
        const { type, messages, prompt, text, model, ...params } = request;

        if (type === 'chat' || type === 'completion') {
            const geminiMessages = this.convertToGeminiMessages(
                type === 'chat' ? messages : [{ role: 'user', content: prompt }]
            );

            return {
                contents: geminiMessages,
                generationConfig: {
                    maxOutputTokens: params.maxTokens || 4096,
                    temperature: params.temperature || 0.7,
                    topP: params.topP || 1,
                    topK: params.topK || 40,
                    ...params.additionalParams
                }
            };
        }

        if (type === 'embedding') {
            return {
                model: `models/${model || 'embedding-001'}`,
                content: {
                    parts: [{ text: text }]
                }
            };
        }

        throw new Error(`Unsupported request type: ${type}`);
    }

    /**
     * Google AI response adapter
     */
    adaptGoogleResponse(response, options = {}) {
        const { type } = options;

        if (type === 'embedding') {
            return {
                embedding: response.embedding?.values || [],
                usage: {
                    prompt_tokens: 0, // Google doesn't provide token counts for embeddings
                    completion_tokens: 0,
                    total_tokens: 0
                },
                model: 'embedding-001'
            };
        }

        // Chat/completion response
        const content = response.candidates?.[0]?.content?.parts?.[0]?.text || '';
        const usage = this.extractGoogleUsage(response);

        return {
            content: content,
            finishReason: response.candidates?.[0]?.finishReason,
            usage: {
                prompt_tokens: usage.promptTokens,
                completion_tokens: usage.completionTokens,
                total_tokens: usage.totalTokens
            },
            model: 'gemini-pro'
        };
    }

    /**
     * Ollama request adapter
     */
    adaptOllamaRequest(request, options = {}) {
        const { type, messages, prompt, text, model, ...params } = request;

        if (type === 'chat') {
            return {
                model: model || 'llama2',
                messages: messages,
                stream: false,
                options: {
                    temperature: params.temperature || 0.7,
                    top_p: params.topP || 1,
                    num_predict: params.maxTokens || 4096
                }
            };
        }

        if (type === 'completion') {
            return {
                model: model || 'llama2',
                prompt: prompt,
                stream: false,
                options: {
                    temperature: params.temperature || 0.7,
                    top_p: params.topP || 1,
                    num_predict: params.maxTokens || 4096
                }
            };
        }

        if (type === 'embedding') {
            return {
                model: model || 'nomic-embed-text',
                prompt: text
            };
        }

        throw new Error(`Unsupported request type: ${type}`);
    }

    /**
     * Ollama response adapter
     */
    adaptOllamaResponse(response, options = {}) {
        const { type } = options;

        if (type === 'embedding') {
            return {
                embedding: response.embedding || [],
                usage: {
                    prompt_tokens: 0,
                    completion_tokens: 0,
                    total_tokens: 0
                },
                model: response.model
            };
        }

        // Chat/completion response
        const content = response.message?.content || response.response || '';

        return {
            content: content,
            finishReason: response.done ? 'stop' : 'length',
            usage: {
                prompt_tokens: 0, // Ollama doesn't provide token counts
                completion_tokens: 0,
                total_tokens: 0
            },
            model: response.model
        };
    }

    /**
     * Generic request adapter (pass-through)
     */
    adaptGenericRequest(request, options = {}) {
        return request;
    }

    /**
     * Generic response adapter (pass-through)
     */
    adaptGenericResponse(response, options = {}) {
        return response;
    }

    /**
     * Convert messages to Anthropic format
     */
    convertToAnthropicMessages(messages) {
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

    /**
     * Convert messages to Google Gemini format
     */
    convertToGeminiMessages(messages) {
        const geminiMessages = [];
        let systemContent = '';

        for (const message of messages) {
            if (message.role === 'system') {
                systemContent += (systemContent ? '\n\n' : '') + message.content;
                continue;
            }

            const role = message.role === 'assistant' ? 'model' : 'user';

            geminiMessages.push({
                role: role,
                parts: [{ text: message.content }]
            });
        }

        // Prepend system message to first user message if present
        if (systemContent && geminiMessages.length > 0 && geminiMessages[0].role === 'user') {
            geminiMessages[0].parts[0].text = `${systemContent}\n\n${geminiMessages[0].parts[0].text}`;
        }

        return geminiMessages;
    }

    /**
     * Extract usage information from Google AI response
     */
    extractGoogleUsage(response) {
        const metadata = response.usageMetadata || {};
        return {
            promptTokens: metadata.promptTokenCount || 0,
            completionTokens: metadata.candidatesTokenCount || 0,
            totalTokens: metadata.totalTokenCount || 0
        };
    }

    /**
     * Create custom adapter
     */
    createCustomAdapter(name, config) {
        const adapter = {
            adaptRequest: (request, options) => {
                return this.transformRequest(request, config.requestTransform, options);
            },
            adaptResponse: (response, options) => {
                return this.transformResponse(response, config.responseTransform, options);
            }
        };

        this.registerAdapter(name, adapter);
        return adapter;
    }

    /**
     * Transform request using custom configuration
     */
    transformRequest(request, transform, options) {
        if (typeof transform === 'function') {
            return transform(request, options);
        }

        if (typeof transform === 'object') {
            const result = {};

            for (const [targetKey, mapping] of Object.entries(transform)) {
                if (typeof mapping === 'string') {
                    // Simple field mapping
                    result[targetKey] = request[mapping];
                } else if (typeof mapping === 'object') {
                    // Complex mapping
                    if (mapping.source) {
                        result[targetKey] = this.getNestedValue(request, mapping.source);
                    }
                    if (mapping.default && result[targetKey] === undefined) {
                        result[targetKey] = mapping.default;
                    }
                    if (mapping.transform && typeof mapping.transform === 'function') {
                        result[targetKey] = mapping.transform(result[targetKey]);
                    }
                }
            }

            return result;
        }

        return request;
    }

    /**
     * Transform response using custom configuration
     */
    transformResponse(response, transform, options) {
        if (typeof transform === 'function') {
            return transform(response, options);
        }

        if (typeof transform === 'object') {
            const result = {};

            for (const [targetKey, mapping] of Object.entries(transform)) {
                if (typeof mapping === 'string') {
                    // Simple field mapping
                    result[targetKey] = this.getNestedValue(response, mapping);
                } else if (typeof mapping === 'object') {
                    // Complex mapping
                    if (mapping.source) {
                        result[targetKey] = this.getNestedValue(response, mapping.source);
                    }
                    if (mapping.default && result[targetKey] === undefined) {
                        result[targetKey] = mapping.default;
                    }
                    if (mapping.transform && typeof mapping.transform === 'function') {
                        result[targetKey] = mapping.transform(result[targetKey]);
                    }
                }
            }

            return result;
        }

        return response;
    }

    /**
     * Get nested value from object using dot notation
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : undefined;
        }, obj);
    }

    /**
     * Get available adapters
     */
    getAvailableAdapters() {
        return Array.from(this.adapters.keys());
    }

    /**
     * Test adapter with sample data
     */
    async testAdapter(adapterName, sampleRequest, sampleResponse) {
        const adapter = this.adapters.get(adapterName);
        if (!adapter) {
            throw new Error(`Adapter ${adapterName} not found`);
        }

        try {
            const adaptedRequest = await adapter.adaptRequest(sampleRequest);
            const adaptedResponse = await adapter.adaptResponse(sampleResponse);

            return {
                success: true,
                adaptedRequest,
                adaptedResponse
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Validate adapter configuration
     */
    validateAdapter(config) {
        const errors = [];

        if (!config.requestTransform && !config.responseTransform) {
            errors.push('At least one of requestTransform or responseTransform is required');
        }

        if (config.requestTransform && typeof config.requestTransform !== 'function' && typeof config.requestTransform !== 'object') {
            errors.push('requestTransform must be a function or object');
        }

        if (config.responseTransform && typeof config.responseTransform !== 'function' && typeof config.responseTransform !== 'object') {
            errors.push('responseTransform must be a function or object');
        }

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

module.exports = ProviderAdapter;