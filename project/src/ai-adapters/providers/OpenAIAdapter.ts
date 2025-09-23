/**
 * OpenAI adapter for GPT models
 */

import { BaseAdapter } from '../core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../core/types.js';

interface OpenAIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  name?: string;
}

interface OpenAIRequest {
  model: string;
  messages?: OpenAIMessage[];
  prompt?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  stop?: string[];
  stream?: boolean;
}

interface OpenAIResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    message?: {
      role: string;
      content: string;
    };
    text?: string;
    index: number;
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class OpenAIAdapter extends BaseAdapter {
  private readonly modelPricing: Record<string, { input: number; output: number }> = {
    'gpt-4': { input: 0.03, output: 0.06 },
    'gpt-4-32k': { input: 0.06, output: 0.12 },
    'gpt-4-turbo': { input: 0.01, output: 0.03 },
    'gpt-3.5-turbo': { input: 0.0015, output: 0.002 },
    'gpt-3.5-turbo-16k': { input: 0.003, output: 0.004 },
    'text-davinci-003': { input: 0.02, output: 0.02 },
    'text-curie-001': { input: 0.002, output: 0.002 },
    'text-babbage-001': { input: 0.0005, output: 0.0005 },
    'text-ada-001': { input: 0.0004, output: 0.0004 }
  };

  constructor(config: ProviderConfig) {
    super('openai', {
      ...config,
      baseUrl: config.baseUrl || 'https://api.openai.com/v1',
      defaultModel: config.defaultModel || 'gpt-3.5-turbo'
    });
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

  protected async makeRequest(input: AIInput): Promise<OpenAIResponse> {
    const model = input.parameters?.model || this.config.defaultModel || 'gpt-3.5-turbo';
    const isChatModel = model.includes('gpt-4') || model.includes('gpt-3.5-turbo');

    const requestBody: OpenAIRequest = {
      model,
      max_tokens: input.parameters?.maxTokens,
      temperature: input.parameters?.temperature,
      top_p: input.parameters?.topP,
      frequency_penalty: input.parameters?.frequencyPenalty,
      presence_penalty: input.parameters?.presencePenalty,
      stop: input.parameters?.stop,
      stream: input.stream || false
    };

    if (isChatModel) {
      // Chat completions format
      requestBody.messages = [];

      if (input.systemMessage) {
        requestBody.messages.push({
          role: 'system',
          content: input.systemMessage
        });
      }

      if (input.messages) {
        requestBody.messages.push(...input.messages);
      } else if (input.prompt) {
        requestBody.messages.push({
          role: 'user',
          content: input.prompt
        });
      }
    } else {
      // Text completions format
      requestBody.prompt = input.prompt;
    }

    const endpoint = isChatModel ? '/chat/completions' : '/completions';
    const url = `${this.config.baseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.config.apiKey}`,
      ...this.config.headers,
      ...input.customHeaders
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
      signal: AbortSignal.timeout(this.config.timeout || 30000)
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorType: 'network' | 'auth' | 'rate_limit' | 'timeout' | 'validation' | 'unknown' = 'unknown';
      let retryable = false;

      switch (response.status) {
        case 401:
          errorType = 'auth';
          break;
        case 429:
          errorType = 'rate_limit';
          retryable = true;
          break;
        case 400:
          errorType = 'validation';
          break;
        case 408:
        case 504:
          errorType = 'timeout';
          retryable = true;
          break;
        case 500:
        case 502:
        case 503:
          errorType = 'network';
          retryable = true;
          break;
      }

      throw this.createError(
        errorType,
        `OpenAI API error: ${response.status} ${errorText}`,
        retryable,
        response.status,
        errorText
      );
    }

    return await response.json();
  }

  protected parseResponse(response: OpenAIResponse, input: AIInput): AIOutput {
    const choice = response.choices[0];
    const content = choice.message?.content || choice.text || '';

    return {
      content,
      choices: response.choices.map(c => c.message?.content || c.text || ''),
      usage: {
        promptTokens: response.usage.prompt_tokens,
        completionTokens: response.usage.completion_tokens,
        totalTokens: response.usage.total_tokens
      },
      raw: response,
      metadata: {
        model: response.model,
        provider: this.name,
        requestId: response.id,
        finishReason: choice.finish_reason
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    const model = output.metadata?.model || this.config.defaultModel || 'gpt-3.5-turbo';
    const pricing = this.modelPricing[model] || this.modelPricing['gpt-3.5-turbo'];

    const inputCost = (output.usage?.promptTokens || 0) * pricing.input / 1000;
    const outputCost = (output.usage?.completionTokens || 0) * pricing.output / 1000;

    return inputCost + outputCost;
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      const response = await fetch(`${this.config.baseUrl}/models`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        signal: AbortSignal.timeout(5000)
      });

      const responseTime = Date.now() - startTime;

      if (response.ok) {
        return {
          healthy: true,
          responseTime,
          lastCheck: new Date(),
          details: {
            status: response.status,
            provider: this.name
          }
        };
      } else {
        return {
          healthy: false,
          responseTime,
          lastCheck: new Date(),
          error: `HTTP ${response.status}: ${await response.text()}`,
          details: {
            status: response.status,
            provider: this.name
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
          error: error
        }
      };
    }
  }

  async getAvailableModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.config.baseUrl}/models`, {
        headers: {
          'Authorization': `Bearer ${this.config.apiKey}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status}`);
      }

      const data = await response.json();
      return data.data.map((model: any) => model.id);
    } catch (error) {
      throw this.createError('network', 'Failed to fetch available models', true, undefined, error);
    }
  }
}