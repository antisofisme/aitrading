/**
 * Generic REST API adapter for custom AI providers
 */

import { BaseAdapter } from '../core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../core/types.js';

interface CustomAPIConfig extends ProviderConfig {
  options: {
    /** Request mapping configuration */
    requestMapping: {
      /** Path to the prompt/message field */
      promptField: string;
      /** Path to the model field */
      modelField?: string;
      /** Path to the max tokens field */
      maxTokensField?: string;
      /** Path to the temperature field */
      temperatureField?: string;
      /** Additional field mappings */
      customFields?: Record<string, string>;
    };
    /** Response mapping configuration */
    responseMapping: {
      /** Path to the content field */
      contentField: string;
      /** Path to the usage tokens field */
      usageTokensField?: string;
      /** Path to the finish reason field */
      finishReasonField?: string;
      /** Path to the choices array */
      choicesField?: string;
    };
    /** HTTP method to use */
    method?: 'POST' | 'PUT' | 'PATCH';
    /** Custom request transformer */
    requestTransformer?: (input: AIInput) => any;
    /** Custom response parser */
    responseParser?: (response: any, input: AIInput) => AIOutput;
    /** Pricing per 1K tokens */
    pricing?: {
      input: number;
      output: number;
    };
  };
}

export class CustomAPIAdapter extends BaseAdapter {
  private readonly customConfig: CustomAPIConfig;

  constructor(config: CustomAPIConfig) {
    super('custom-api', config);
    this.customConfig = config;

    // Validate required configuration
    if (!config.options?.requestMapping?.promptField) {
      throw new Error('requestMapping.promptField is required for CustomAPIAdapter');
    }
    if (!config.options?.responseMapping?.contentField) {
      throw new Error('responseMapping.contentField is required for CustomAPIAdapter');
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
    const requestBody = this.buildRequestBody(input);
    const method = this.customConfig.options.method || 'POST';

    const headers = {
      'Content-Type': 'application/json',
      ...this.buildAuthHeaders(),
      ...this.config.headers,
      ...input.customHeaders
    };

    const response = await fetch(this.config.baseUrl, {
      method,
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
        case 403:
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
        `Custom API error: ${response.status} ${errorText}`,
        retryable,
        response.status,
        errorText
      );
    }

    return await response.json();
  }

  private buildRequestBody(input: AIInput): any {
    const mapping = this.customConfig.options.requestMapping;

    // Use custom transformer if provided
    if (this.customConfig.options.requestTransformer) {
      return this.customConfig.options.requestTransformer(input);
    }

    const body: any = {};

    // Set prompt/message
    this.setNestedValue(body, mapping.promptField, this.formatPrompt(input));

    // Set model if specified
    if (mapping.modelField) {
      const model = input.parameters?.model || this.config.defaultModel;
      if (model) {
        this.setNestedValue(body, mapping.modelField, model);
      }
    }

    // Set max tokens if specified
    if (mapping.maxTokensField && input.parameters?.maxTokens) {
      this.setNestedValue(body, mapping.maxTokensField, input.parameters.maxTokens);
    }

    // Set temperature if specified
    if (mapping.temperatureField && input.parameters?.temperature !== undefined) {
      this.setNestedValue(body, mapping.temperatureField, input.parameters.temperature);
    }

    // Set custom fields
    if (mapping.customFields) {
      for (const [sourceField, targetPath] of Object.entries(mapping.customFields)) {
        const value = this.getNestedValue(input.parameters, sourceField);
        if (value !== undefined) {
          this.setNestedValue(body, targetPath, value);
        }
      }
    }

    return body;
  }

  private formatPrompt(input: AIInput): string {
    if (input.messages) {
      // Convert messages to a single prompt
      let prompt = '';

      if (input.systemMessage) {
        prompt += `System: ${input.systemMessage}\n\n`;
      }

      for (const msg of input.messages) {
        if (msg.role === 'system') {
          prompt += `System: ${msg.content}\n\n`;
        } else if (msg.role === 'user') {
          prompt += `User: ${msg.content}\n\n`;
        } else if (msg.role === 'assistant') {
          prompt += `Assistant: ${msg.content}\n\n`;
        }
      }

      return prompt.trim();
    }

    let prompt = '';
    if (input.systemMessage) {
      prompt += `${input.systemMessage}\n\n`;
    }
    prompt += input.prompt || '';

    return prompt;
  }

  private buildAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {};

    // Common authentication patterns
    if (this.config.apiKey) {
      // Try common header patterns
      if (this.config.headers?.['Authorization']) {
        // Use custom auth header format
        headers['Authorization'] = this.config.headers['Authorization'];
      } else {
        // Default to Bearer token
        headers['Authorization'] = `Bearer ${this.config.apiKey}`;
      }
    }

    return headers;
  }

  protected parseResponse(response: any, input: AIInput): AIOutput {
    const mapping = this.customConfig.options.responseMapping;

    // Use custom parser if provided
    if (this.customConfig.options.responseParser) {
      return this.customConfig.options.responseParser(response, input);
    }

    // Extract content
    const content = this.getNestedValue(response, mapping.contentField) || '';

    // Extract choices if available
    let choices: string[] = [content];
    if (mapping.choicesField) {
      const choicesArray = this.getNestedValue(response, mapping.choicesField);
      if (Array.isArray(choicesArray)) {
        choices = choicesArray.map((choice: any) => {
          if (typeof choice === 'string') return choice;
          return this.getNestedValue(choice, mapping.contentField) || String(choice);
        });
      }
    }

    // Extract usage information
    let usage: AIOutput['usage'];
    if (mapping.usageTokensField) {
      const tokens = this.getNestedValue(response, mapping.usageTokensField);
      if (typeof tokens === 'number') {
        usage = {
          promptTokens: Math.floor(tokens * 0.7), // Estimate
          completionTokens: Math.floor(tokens * 0.3), // Estimate
          totalTokens: tokens
        };
      }
    }

    // Extract finish reason
    const finishReason = mapping.finishReasonField
      ? this.getNestedValue(response, mapping.finishReasonField)
      : undefined;

    return {
      content,
      choices,
      usage,
      raw: response,
      metadata: {
        model: input.parameters?.model || this.config.defaultModel || 'unknown',
        provider: this.name,
        finishReason
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    const pricing = this.customConfig.options.pricing;
    if (!pricing || !output.usage) {
      return 0;
    }

    const inputCost = (output.usage.promptTokens || 0) * pricing.input / 1000;
    const outputCost = (output.usage.completionTokens || 0) * pricing.output / 1000;

    return inputCost + outputCost;
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      // Create a minimal test request
      const testInput: AIInput = {
        prompt: 'test',
        parameters: { maxTokens: 1 }
      };

      const requestBody = this.buildRequestBody(testInput);
      const method = this.customConfig.options.method || 'POST';

      const response = await fetch(this.config.baseUrl, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...this.buildAuthHeaders()
        },
        body: JSON.stringify(requestBody),
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

  /**
   * Utility to get nested object values using dot notation
   */
  private getNestedValue(obj: any, path: string): any {
    return path.split('.').reduce((current, key) => {
      return current && current[key] !== undefined ? current[key] : undefined;
    }, obj);
  }

  /**
   * Utility to set nested object values using dot notation
   */
  private setNestedValue(obj: any, path: string, value: any): void {
    const keys = path.split('.');
    const lastKey = keys.pop()!;

    const target = keys.reduce((current, key) => {
      if (!current[key] || typeof current[key] !== 'object') {
        current[key] = {};
      }
      return current[key];
    }, obj);

    target[lastKey] = value;
  }
}