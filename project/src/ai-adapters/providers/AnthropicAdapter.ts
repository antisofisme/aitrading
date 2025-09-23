/**
 * Anthropic adapter for Claude models
 */

import { BaseAdapter } from '../core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../core/types.js';

interface AnthropicMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface AnthropicRequest {
  model: string;
  messages: AnthropicMessage[];
  system?: string;
  max_tokens: number;
  temperature?: number;
  top_p?: number;
  top_k?: number;
  stop_sequences?: string[];
  stream?: boolean;
}

interface AnthropicResponse {
  id: string;
  type: 'message';
  role: 'assistant';
  content: Array<{
    type: 'text';
    text: string;
  }>;
  model: string;
  stop_reason: string;
  stop_sequence?: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

export class AnthropicAdapter extends BaseAdapter {
  private readonly modelPricing: Record<string, { input: number; output: number }> = {
    'claude-3-opus-20240229': { input: 0.015, output: 0.075 },
    'claude-3-sonnet-20240229': { input: 0.003, output: 0.015 },
    'claude-3-haiku-20240307': { input: 0.00025, output: 0.00125 },
    'claude-2.1': { input: 0.008, output: 0.024 },
    'claude-2.0': { input: 0.008, output: 0.024 },
    'claude-instant-1.2': { input: 0.0008, output: 0.0024 }
  };

  constructor(config: ProviderConfig) {
    super('anthropic', {
      ...config,
      baseUrl: config.baseUrl || 'https://api.anthropic.com/v1',
      defaultModel: config.defaultModel || 'claude-3-sonnet-20240229'
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

  protected async makeRequest(input: AIInput): Promise<AnthropicResponse> {
    const model = input.parameters?.model || this.config.defaultModel || 'claude-3-sonnet-20240229';

    const requestBody: AnthropicRequest = {
      model,
      messages: this.formatMessages(input),
      max_tokens: input.parameters?.maxTokens || 1000,
      temperature: input.parameters?.temperature,
      top_p: input.parameters?.topP,
      top_k: input.parameters?.topK,
      stop_sequences: input.parameters?.stop,
      stream: input.stream || false
    };

    if (input.systemMessage) {
      requestBody.system = input.systemMessage;
    }

    const url = `${this.config.baseUrl}/messages`;

    const headers = {
      'Content-Type': 'application/json',
      'x-api-key': this.config.apiKey,
      'anthropic-version': '2023-06-01',
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
        `Anthropic API error: ${response.status} ${errorText}`,
        retryable,
        response.status,
        errorText
      );
    }

    return await response.json();
  }

  private formatMessages(input: AIInput): AnthropicMessage[] {
    const messages: AnthropicMessage[] = [];

    if (input.messages) {
      // Convert chat messages, filtering out system messages (handled separately)
      for (const msg of input.messages) {
        if (msg.role !== 'system') {
          messages.push({
            role: msg.role as 'user' | 'assistant',
            content: msg.content
          });
        }
      }
    } else if (input.prompt) {
      messages.push({
        role: 'user',
        content: input.prompt
      });
    }

    // Ensure we have at least one message and it starts with user
    if (messages.length === 0 || messages[0].role !== 'user') {
      messages.unshift({
        role: 'user',
        content: input.prompt || 'Hello'
      });
    }

    return messages;
  }

  protected parseResponse(response: AnthropicResponse, input: AIInput): AIOutput {
    const content = response.content.map(c => c.text).join('');

    return {
      content,
      choices: [content], // Anthropic typically returns single response
      usage: {
        promptTokens: response.usage.input_tokens,
        completionTokens: response.usage.output_tokens,
        totalTokens: response.usage.input_tokens + response.usage.output_tokens
      },
      raw: response,
      metadata: {
        model: response.model,
        provider: this.name,
        requestId: response.id,
        finishReason: response.stop_reason
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    const model = output.metadata?.model || this.config.defaultModel || 'claude-3-sonnet-20240229';
    const pricing = this.modelPricing[model] || this.modelPricing['claude-3-sonnet-20240229'];

    const inputCost = (output.usage?.promptTokens || 0) * pricing.input / 1000;
    const outputCost = (output.usage?.completionTokens || 0) * pricing.output / 1000;

    return inputCost + outputCost;
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      // Test with a minimal request
      const testRequest: AnthropicRequest = {
        model: this.config.defaultModel || 'claude-3-sonnet-20240229',
        messages: [{ role: 'user', content: 'Hi' }],
        max_tokens: 1
      };

      const response = await fetch(`${this.config.baseUrl}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.config.apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify(testRequest),
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
    // Anthropic doesn't provide a models endpoint, return known models
    return Object.keys(this.modelPricing);
  }
}