/**
 * Base adapter class with common functionality
 */

import {
  AIProvider,
  ProviderConfig,
  AIInput,
  AIOutput,
  UsageMetrics,
  HealthStatus,
  RateLimitInfo,
  AdapterError
} from './types.js';

export abstract class BaseAdapter implements AIProvider {
  protected usage: UsageMetrics;
  protected rateLimit: RateLimitInfo;
  private requestQueue: Map<string, Date> = new Map();
  private tokenQueue: Map<string, number> = new Map();

  constructor(
    public readonly name: string,
    public readonly config: ProviderConfig
  ) {
    this.usage = this.initializeUsage();
    this.rateLimit = this.initializeRateLimit();
  }

  abstract predict(input: AIInput): Promise<AIOutput>;
  abstract healthCheck(): Promise<HealthStatus>;

  protected abstract makeRequest(input: AIInput): Promise<any>;
  protected abstract parseResponse(response: any, input: AIInput): AIOutput;

  /**
   * Validate input before processing
   */
  protected validateInput(input: AIInput): void {
    if (!input.prompt && (!input.messages || input.messages.length === 0)) {
      throw this.createError('Validation', 'Either prompt or messages must be provided', false);
    }

    if (input.parameters?.maxTokens && input.parameters.maxTokens <= 0) {
      throw this.createError('Validation', 'maxTokens must be positive', false);
    }

    if (input.parameters?.temperature && (input.parameters.temperature < 0 || input.parameters.temperature > 2)) {
      throw this.createError('Validation', 'temperature must be between 0 and 2', false);
    }
  }

  /**
   * Check rate limits before making request
   */
  protected async checkRateLimit(input: AIInput): Promise<void> {
    const now = new Date();
    const estimatedTokens = this.estimateTokens(input);

    // Clean old entries
    this.cleanupRateLimit(now);

    // Check request rate limit
    if (this.config.rateLimits?.requestsPerMinute) {
      if (this.rateLimit.currentUsage.requests >= this.config.rateLimits.requestsPerMinute) {
        throw this.createError('Rate Limit', 'Request rate limit exceeded', true);
      }
    }

    // Check token rate limit
    if (this.config.rateLimits?.tokensPerMinute) {
      if (this.rateLimit.currentUsage.tokens + estimatedTokens > this.config.rateLimits.tokensPerMinute) {
        throw this.createError('Rate Limit', 'Token rate limit exceeded', true);
      }
    }

    // Record this request
    const requestId = `${now.getTime()}-${Math.random()}`;
    this.requestQueue.set(requestId, now);
    this.tokenQueue.set(requestId, estimatedTokens);

    this.rateLimit.currentUsage.requests++;
    this.rateLimit.currentUsage.tokens += estimatedTokens;
  }

  /**
   * Update usage metrics after request
   */
  protected updateUsage(output: AIOutput, responseTime: number): void {
    this.usage.totalRequests++;
    this.usage.totalTokens += output.usage?.totalTokens || 0;
    this.usage.totalCost += this.calculateCost(output);

    // Update average response time
    const totalTime = this.usage.averageResponseTime * (this.usage.totalRequests - 1) + responseTime;
    this.usage.averageResponseTime = totalTime / this.usage.totalRequests;
  }

  /**
   * Record error for metrics
   */
  protected recordError(): void {
    const totalRequests = this.usage.totalRequests || 1;
    const errors = Math.round(this.usage.errorRate * totalRequests / 100) + 1;
    this.usage.errorRate = (errors / (totalRequests + 1)) * 100;
  }

  /**
   * Estimate token count for rate limiting
   */
  protected estimateTokens(input: AIInput): number {
    const text = input.prompt || input.messages?.map(m => m.content).join(' ') || '';
    // Rough estimation: ~4 characters per token for English text
    return Math.ceil(text.length / 4) + (input.parameters?.maxTokens || 100);
  }

  /**
   * Calculate cost based on usage
   */
  protected abstract calculateCost(output: AIOutput): number;

  /**
   * Create standardized error
   */
  protected createError(
    type: AdapterError['type'],
    message: string,
    retryable: boolean,
    statusCode?: number,
    originalError?: any
  ): AdapterError {
    const error = new Error(message) as AdapterError;
    error.provider = this.name;
    error.type = type;
    error.retryable = retryable;
    error.statusCode = statusCode;
    error.originalError = originalError;
    return error;
  }

  /**
   * Retry mechanism with exponential backoff
   */
  protected async withRetry<T>(
    operation: () => Promise<T>,
    maxAttempts: number = this.config.retry?.attempts || 3
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        // Don't retry non-retryable errors
        if (error instanceof Error && 'retryable' in error && !error.retryable) {
          throw error;
        }

        // Don't retry on last attempt
        if (attempt === maxAttempts) {
          break;
        }

        // Calculate backoff delay
        const baseDelay = this.config.retry?.backoffMs || 1000;
        const delay = this.config.retry?.exponential
          ? baseDelay * Math.pow(2, attempt - 1)
          : baseDelay;

        await this.sleep(delay);
      }
    }

    throw lastError!;
  }

  /**
   * Sleep utility
   */
  protected sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clean up old rate limit entries
   */
  private cleanupRateLimit(now: Date): void {
    const oneMinuteAgo = new Date(now.getTime() - 60000);

    for (const [id, timestamp] of this.requestQueue.entries()) {
      if (timestamp < oneMinuteAgo) {
        this.requestQueue.delete(id);
        const tokens = this.tokenQueue.get(id) || 0;
        this.tokenQueue.delete(id);

        this.rateLimit.currentUsage.requests = Math.max(0, this.rateLimit.currentUsage.requests - 1);
        this.rateLimit.currentUsage.tokens = Math.max(0, this.rateLimit.currentUsage.tokens - tokens);
      }
    }

    // Update reset time
    this.rateLimit.resetTime = new Date(now.getTime() + 60000);
  }

  /**
   * Initialize usage metrics
   */
  private initializeUsage(): UsageMetrics {
    return {
      totalRequests: 0,
      totalTokens: 0,
      totalCost: 0,
      requestsPerMinute: 0,
      averageResponseTime: 0,
      errorRate: 0,
      lastReset: new Date()
    };
  }

  /**
   * Initialize rate limit info
   */
  private initializeRateLimit(): RateLimitInfo {
    return {
      requestsPerMinute: this.config.rateLimits?.requestsPerMinute || Infinity,
      tokensPerMinute: this.config.rateLimits?.tokensPerMinute || Infinity,
      currentUsage: {
        requests: 0,
        tokens: 0
      },
      resetTime: new Date(Date.now() + 60000)
    };
  }

  // Public interface methods
  getUsage(): UsageMetrics {
    return { ...this.usage };
  }

  getRateLimit(): RateLimitInfo {
    return { ...this.rateLimit };
  }

  resetUsage(): void {
    this.usage = this.initializeUsage();
  }

  async validateConfig(): Promise<boolean> {
    try {
      if (!this.config.apiKey) {
        throw new Error('API key is required');
      }
      if (!this.config.baseUrl) {
        throw new Error('Base URL is required');
      }

      const health = await this.healthCheck();
      return health.healthy;
    } catch (error) {
      return false;
    }
  }
}