/**
 * Local model adapter for self-hosted AI models
 */

import { BaseAdapter } from '../core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../core/types.js';

interface LocalModelConfig extends ProviderConfig {
  options: {
    /** Model format/type */
    modelType: 'ollama' | 'llamacpp' | 'vllm' | 'tgi' | 'custom';
    /** Model name/identifier */
    modelName: string;
    /** Generation parameters */
    generation?: {
      /** Context window size */
      contextLength?: number;
      /** Batch size for processing */
      batchSize?: number;
      /** Number of threads for CPU inference */
      threads?: number;
      /** GPU layers (for GGML models) */
      gpuLayers?: number;
    };
    /** Custom endpoints for different operations */
    endpoints?: {
      generate?: string;
      chat?: string;
      health?: string;
      models?: string;
    };
    /** Authentication method for local models */
    auth?: {
      type: 'none' | 'basic' | 'bearer' | 'api_key';
      credentials?: {
        username?: string;
        password?: string;
        token?: string;
      };
    };
  };
}

interface OllamaRequest {
  model: string;
  prompt?: string;
  messages?: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  options?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    num_predict?: number;
    stop?: string[];
  };
  stream?: boolean;
}

interface OllamaResponse {
  model: string;
  created_at: string;
  response?: string;
  message?: {
    role: string;
    content: string;
  };
  done: boolean;
  context?: number[];
  total_duration?: number;
  load_duration?: number;
  prompt_eval_count?: number;
  prompt_eval_duration?: number;
  eval_count?: number;
  eval_duration?: number;
}

export class LocalModelAdapter extends BaseAdapter {
  private readonly localConfig: LocalModelConfig;

  constructor(config: LocalModelConfig) {
    super('local-model', config);
    this.localConfig = config;

    // Validate required configuration
    if (!config.options?.modelName) {
      throw new Error('options.modelName is required for LocalModelAdapter');
    }
  }

  async predict(input: AIInput): Promise<AIOutput> {
    this.validateInput(input);
    await this.checkRateLimit(input);

    const startTime = Date.now();

    try {
      const response = await this.withRetry(() => this.makeRequest(input));
      const output = this.parseResponse(response, input);

      this.updateUsage(output, Date.now() - startTime);
      return output;
    } catch (error) {
      this.recordError();
      throw error;
    }
  }

  protected async makeRequest(input: AIInput): Promise<any> {
    const modelType = this.localConfig.options.modelType;

    switch (modelType) {
      case 'ollama':
        return this.makeOllamaRequest(input);
      case 'llamacpp':
        return this.makeLlamaCppRequest(input);
      case 'vllm':
        return this.makeVLLMRequest(input);
      case 'tgi':
        return this.makeTGIRequest(input);
      default:
        return this.makeCustomRequest(input);
    }
  }

  private async makeOllamaRequest(input: AIInput): Promise<OllamaResponse> {
    const endpoint = this.localConfig.options.endpoints?.generate || '/api/generate';
    const chatEndpoint = this.localConfig.options.endpoints?.chat || '/api/chat';

    // Use chat endpoint if messages are provided
    const isChat = input.messages && input.messages.length > 0;
    const url = `${this.config.baseUrl}${isChat ? chatEndpoint : endpoint}`;

    const requestBody: OllamaRequest = {
      model: this.localConfig.options.modelName,
      options: {
        temperature: input.parameters?.temperature,
        top_p: input.parameters?.topP,
        top_k: input.parameters?.topK,
        num_predict: input.parameters?.maxTokens,
        stop: input.parameters?.stop
      },
      stream: false
    };

    if (isChat) {
      requestBody.messages = input.messages!.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Add system message if provided
      if (input.systemMessage) {
        requestBody.messages.unshift({
          role: 'system',
          content: input.systemMessage
        });
      }
    } else {
      let prompt = '';
      if (input.systemMessage) {
        prompt += `${input.systemMessage}\n\n`;
      }
      prompt += input.prompt || '';
      requestBody.prompt = prompt;
    }

    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw this.createError(
        'network',
        `Ollama error: ${response.status} ${await response.text()}`,
        response.status >= 500,
        response.status
      );
    }

    return await response.json();
  }

  private async makeLlamaCppRequest(input: AIInput): Promise<any> {
    const endpoint = this.localConfig.options.endpoints?.generate || '/completion';
    const url = `${this.config.baseUrl}${endpoint}`;

    let prompt = '';
    if (input.systemMessage) {
      prompt += `${input.systemMessage}\n\n`;
    }
    if (input.messages) {
      prompt += input.messages.map(m => `${m.role}: ${m.content}`).join('\n');
    } else {
      prompt += input.prompt || '';
    }

    const requestBody = {
      prompt,
      n_predict: input.parameters?.maxTokens || -1,
      temperature: input.parameters?.temperature || 0.7,
      top_p: input.parameters?.topP || 0.9,
      top_k: input.parameters?.topK || 40,
      stop: input.parameters?.stop || [],
      stream: false
    };

    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw this.createError(
        'network',
        `llama.cpp error: ${response.status} ${await response.text()}`,
        response.status >= 500,
        response.status
      );
    }

    return await response.json();
  }

  private async makeVLLMRequest(input: AIInput): Promise<any> {
    const endpoint = this.localConfig.options.endpoints?.generate || '/v1/completions';
    const url = `${this.config.baseUrl}${endpoint}`;

    const requestBody = {
      model: this.localConfig.options.modelName,
      prompt: this.formatPromptForVLLM(input),
      max_tokens: input.parameters?.maxTokens,
      temperature: input.parameters?.temperature,
      top_p: input.parameters?.topP,
      stop: input.parameters?.stop,
      stream: false
    };

    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw this.createError(
        'network',
        `vLLM error: ${response.status} ${await response.text()}`,
        response.status >= 500,
        response.status
      );
    }

    return await response.json();
  }

  private async makeTGIRequest(input: AIInput): Promise<any> {
    const endpoint = this.localConfig.options.endpoints?.generate || '/generate';
    const url = `${this.config.baseUrl}${endpoint}`;

    const requestBody = {
      inputs: this.formatPromptForTGI(input),
      parameters: {
        max_new_tokens: input.parameters?.maxTokens,
        temperature: input.parameters?.temperature,
        top_p: input.parameters?.topP,
        top_k: input.parameters?.topK,
        stop: input.parameters?.stop,
        do_sample: true
      }
    };

    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw this.createError(
        'network',
        `TGI error: ${response.status} ${await response.text()}`,
        response.status >= 500,
        response.status
      );
    }

    return await response.json();
  }

  private async makeCustomRequest(input: AIInput): Promise<any> {
    // Basic custom request - override this method for specific custom implementations
    const url = this.config.baseUrl;

    const requestBody = {
      model: this.localConfig.options.modelName,
      prompt: input.prompt,
      max_tokens: input.parameters?.maxTokens,
      temperature: input.parameters?.temperature
    };

    const response = await this.fetchWithAuth(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw this.createError(
        'network',
        `Custom model error: ${response.status} ${await response.text()}`,
        response.status >= 500,
        response.status
      );
    }

    return await response.json();
  }

  private async fetchWithAuth(url: string, options: RequestInit): Promise<Response> {
    const auth = this.localConfig.options.auth;
    const headers = { ...options.headers };

    if (auth && auth.type !== 'none') {
      switch (auth.type) {
        case 'basic':
          if (auth.credentials?.username && auth.credentials?.password) {
            const credentials = btoa(`${auth.credentials.username}:${auth.credentials.password}`);
            headers['Authorization'] = `Basic ${credentials}`;
          }
          break;
        case 'bearer':
          if (auth.credentials?.token) {
            headers['Authorization'] = `Bearer ${auth.credentials.token}`;
          }
          break;
        case 'api_key':
          if (this.config.apiKey) {
            headers['X-API-Key'] = this.config.apiKey;
          }
          break;
      }
    }

    return fetch(url, {
      ...options,
      headers,
      signal: AbortSignal.timeout(this.config.timeout || 60000)
    });
  }

  private formatPromptForVLLM(input: AIInput): string {
    let prompt = '';
    if (input.systemMessage) {
      prompt += `System: ${input.systemMessage}\n\n`;
    }
    if (input.messages) {
      prompt += input.messages.map(m => `${m.role}: ${m.content}`).join('\n') + '\nAssistant:';
    } else {
      prompt += input.prompt || '';
    }
    return prompt;
  }

  private formatPromptForTGI(input: AIInput): string {
    let prompt = '';
    if (input.systemMessage) {
      prompt += `${input.systemMessage}\n\n`;
    }
    if (input.messages) {
      prompt += input.messages.map(m => `${m.role}: ${m.content}`).join('\n');
    } else {
      prompt += input.prompt || '';
    }
    return prompt;
  }

  protected parseResponse(response: any, input: AIInput): AIOutput {
    const modelType = this.localConfig.options.modelType;

    switch (modelType) {
      case 'ollama':
        return this.parseOllamaResponse(response, input);
      case 'llamacpp':
        return this.parseLlamaCppResponse(response, input);
      case 'vllm':
        return this.parseVLLMResponse(response, input);
      case 'tgi':
        return this.parseTGIResponse(response, input);
      default:
        return this.parseCustomResponse(response, input);
    }
  }

  private parseOllamaResponse(response: OllamaResponse, input: AIInput): AIOutput {
    const content = response.message?.content || response.response || '';

    // Estimate token usage from timing information
    let usage: AIOutput['usage'] | undefined;
    if (response.prompt_eval_count && response.eval_count) {
      usage = {
        promptTokens: response.prompt_eval_count,
        completionTokens: response.eval_count,
        totalTokens: response.prompt_eval_count + response.eval_count
      };
    }

    return {
      content,
      choices: [content],
      usage,
      raw: response,
      metadata: {
        model: response.model,
        provider: this.name,
        totalDuration: response.total_duration,
        loadDuration: response.load_duration,
        promptEvalDuration: response.prompt_eval_duration,
        evalDuration: response.eval_duration
      }
    };
  }

  private parseLlamaCppResponse(response: any, input: AIInput): AIOutput {
    const content = response.content || '';

    return {
      content,
      choices: [content],
      usage: response.usage ? {
        promptTokens: response.usage.prompt_tokens || 0,
        completionTokens: response.usage.completion_tokens || 0,
        totalTokens: response.usage.total_tokens || 0
      } : undefined,
      raw: response,
      metadata: {
        model: this.localConfig.options.modelName,
        provider: this.name,
        finishReason: response.stop ? 'stop' : 'length'
      }
    };
  }

  private parseVLLMResponse(response: any, input: AIInput): AIOutput {
    const choice = response.choices?.[0];
    const content = choice?.text || '';

    return {
      content,
      choices: response.choices?.map((c: any) => c.text) || [content],
      usage: response.usage ? {
        promptTokens: response.usage.prompt_tokens,
        completionTokens: response.usage.completion_tokens,
        totalTokens: response.usage.total_tokens
      } : undefined,
      raw: response,
      metadata: {
        model: response.model || this.localConfig.options.modelName,
        provider: this.name,
        finishReason: choice?.finish_reason
      }
    };
  }

  private parseTGIResponse(response: any, input: AIInput): AIOutput {
    const content = response.generated_text || '';

    return {
      content,
      choices: [content],
      usage: response.details ? {
        promptTokens: response.details.prefill?.length || 0,
        completionTokens: response.details.tokens?.length || 0,
        totalTokens: (response.details.prefill?.length || 0) + (response.details.tokens?.length || 0)
      } : undefined,
      raw: response,
      metadata: {
        model: this.localConfig.options.modelName,
        provider: this.name,
        finishReason: response.details?.finish_reason
      }
    };
  }

  private parseCustomResponse(response: any, input: AIInput): AIOutput {
    // Basic parsing - override for specific implementations
    const content = response.text || response.content || response.output || '';

    return {
      content,
      choices: [content],
      raw: response,
      metadata: {
        model: this.localConfig.options.modelName,
        provider: this.name
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    // Local models typically don't have per-token costs
    return 0;
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      const healthEndpoint = this.localConfig.options.endpoints?.health;

      if (healthEndpoint) {
        // Use dedicated health endpoint
        const response = await this.fetchWithAuth(`${this.config.baseUrl}${healthEndpoint}`, {
          method: 'GET'
        });

        const responseTime = Date.now() - startTime;

        return {
          healthy: response.ok,
          responseTime,
          lastCheck: new Date(),
          error: response.ok ? undefined : `Health check failed: ${response.status}`,
          details: {
            status: response.status,
            provider: this.name,
            modelType: this.localConfig.options.modelType
          }
        };
      } else {
        // Make a minimal generation request
        const testInput: AIInput = {
          prompt: 'test',
          parameters: { maxTokens: 1 }
        };

        await this.makeRequest(testInput);
        const responseTime = Date.now() - startTime;

        return {
          healthy: true,
          responseTime,
          lastCheck: new Date(),
          details: {
            provider: this.name,
            modelType: this.localConfig.options.modelType
          }
        };
      }
    } catch (error) {
      return {
        healthy: false,
        responseTime: Date.now() - startTime,
        lastCheck: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error',
        details: {
          provider: this.name,
          modelType: this.localConfig.options.modelType,
          error: error
        }
      };
    }
  }

  async getAvailableModels(): Promise<string[]> {
    try {
      const modelsEndpoint = this.localConfig.options.endpoints?.models;

      if (modelsEndpoint) {
        const response = await this.fetchWithAuth(`${this.config.baseUrl}${modelsEndpoint}`, {
          method: 'GET'
        });

        if (response.ok) {
          const data = await response.json();

          // Handle different response formats
          if (Array.isArray(data)) {
            return data.map(model => typeof model === 'string' ? model : model.name || model.id);
          } else if (data.models && Array.isArray(data.models)) {
            return data.models.map((model: any) => model.name || model.id);
          }
        }
      }

      // Return configured model as fallback
      return [this.localConfig.options.modelName];
    } catch (error) {
      return [this.localConfig.options.modelName];
    }
  }
}