/**
 * Google AI adapter for Gemini and PaLM models
 */

import { BaseAdapter } from '../core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../core/types.js';

interface GoogleAIContent {
  parts: Array<{
    text: string;
  }>;
  role?: 'user' | 'model';
}

interface GoogleAIRequest {
  contents: GoogleAIContent[];
  generationConfig?: {
    temperature?: number;
    topP?: number;
    topK?: number;
    maxOutputTokens?: number;
    stopSequences?: string[];
  };
  safetySettings?: Array<{
    category: string;
    threshold: string;
  }>;
}

interface GoogleAIResponse {
  candidates: Array<{
    content: {
      parts: Array<{
        text: string;
      }>;
      role: string;
    };
    finishReason: string;
    index: number;
    safetyRatings?: Array<{
      category: string;
      probability: string;
    }>;
  }>;
  usageMetadata: {
    promptTokenCount: number;
    candidatesTokenCount: number;
    totalTokenCount: number;
  };
}

export class GoogleAIAdapter extends BaseAdapter {
  private readonly modelPricing: Record<string, { input: number; output: number }> = {
    'gemini-pro': { input: 0.00025, output: 0.0005 },
    'gemini-pro-vision': { input: 0.00025, output: 0.0005 },
    'gemini-ultra': { input: 0.0025, output: 0.005 },
    'text-bison-001': { input: 0.001, output: 0.001 },
    'chat-bison-001': { input: 0.0005, output: 0.0005 },
    'code-bison-001': { input: 0.001, output: 0.001 }
  };

  constructor(config: ProviderConfig) {
    super('google', {
      ...config,
      baseUrl: config.baseUrl || 'https://generativelanguage.googleapis.com/v1beta',
      defaultModel: config.defaultModel || 'gemini-pro'
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

  protected async makeRequest(input: AIInput): Promise<GoogleAIResponse> {
    const model = input.parameters?.model || this.config.defaultModel || 'gemini-pro';

    const requestBody: GoogleAIRequest = {
      contents: this.formatContents(input),
      generationConfig: {
        temperature: input.parameters?.temperature,
        topP: input.parameters?.topP,
        topK: input.parameters?.topK,
        maxOutputTokens: input.parameters?.maxTokens,
        stopSequences: input.parameters?.stop
      }
    };

    // Add safety settings for content filtering
    requestBody.safetySettings = [
      {
        category: 'HARM_CATEGORY_HARASSMENT',
        threshold: 'BLOCK_MEDIUM_AND_ABOVE'
      },
      {
        category: 'HARM_CATEGORY_HATE_SPEECH',
        threshold: 'BLOCK_MEDIUM_AND_ABOVE'
      },
      {
        category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        threshold: 'BLOCK_MEDIUM_AND_ABOVE'
      },
      {
        category: 'HARM_CATEGORY_DANGEROUS_CONTENT',
        threshold: 'BLOCK_MEDIUM_AND_ABOVE'
      }
    ];

    const url = `${this.config.baseUrl}/models/${model}:generateContent?key=${this.config.apiKey}`;

    const headers = {
      'Content-Type': 'application/json',
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
        `Google AI API error: ${response.status} ${errorText}`,
        retryable,
        response.status,
        errorText
      );
    }

    return await response.json();
  }

  private formatContents(input: AIInput): GoogleAIContent[] {
    const contents: GoogleAIContent[] = [];

    if (input.messages) {
      // Convert chat messages
      for (const msg of input.messages) {
        if (msg.role === 'system') {
          // System messages can be added as user messages with special formatting
          contents.push({
            parts: [{ text: `System: ${msg.content}` }],
            role: 'user'
          });
        } else {
          contents.push({
            parts: [{ text: msg.content }],
            role: msg.role === 'assistant' ? 'model' : 'user'
          });
        }
      }
    } else if (input.prompt) {
      contents.push({
        parts: [{ text: input.prompt }],
        role: 'user'
      });
    }

    // Add system message if provided and no messages array
    if (input.systemMessage && !input.messages) {
      contents.unshift({
        parts: [{ text: `System: ${input.systemMessage}` }],
        role: 'user'
      });
    }

    return contents;
  }

  protected parseResponse(response: GoogleAIResponse, input: AIInput): AIOutput {
    const candidate = response.candidates[0];
    const content = candidate.content.parts.map(p => p.text).join('');

    return {
      content,
      choices: response.candidates.map(c => c.content.parts.map(p => p.text).join('')),
      usage: {
        promptTokens: response.usageMetadata.promptTokenCount,
        completionTokens: response.usageMetadata.candidatesTokenCount,
        totalTokens: response.usageMetadata.totalTokenCount
      },
      raw: response,
      metadata: {
        model: input.parameters?.model || this.config.defaultModel || 'gemini-pro',
        provider: this.name,
        finishReason: candidate.finishReason,
        safetyRatings: candidate.safetyRatings
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    const model = output.metadata?.model || this.config.defaultModel || 'gemini-pro';
    const pricing = this.modelPricing[model] || this.modelPricing['gemini-pro'];

    const inputCost = (output.usage?.promptTokens || 0) * pricing.input / 1000;
    const outputCost = (output.usage?.completionTokens || 0) * pricing.output / 1000;

    return inputCost + outputCost;
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      // Test with a minimal request
      const testRequest: GoogleAIRequest = {
        contents: [
          {
            parts: [{ text: 'Hi' }],
            role: 'user'
          }
        ],
        generationConfig: {
          maxOutputTokens: 1
        }
      };

      const model = this.config.defaultModel || 'gemini-pro';
      const url = `${this.config.baseUrl}/models/${model}:generateContent?key=${this.config.apiKey}`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
    try {
      const url = `${this.config.baseUrl}/models?key=${this.config.apiKey}`;

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.status}`);
      }

      const data = await response.json();
      return data.models
        .filter((model: any) => model.supportedGenerationMethods?.includes('generateContent'))
        .map((model: any) => model.name.replace('models/', ''));
    } catch (error) {
      // Return known models if API call fails
      return Object.keys(this.modelPricing);
    }
  }
}