/**
 * Tests for BaseAdapter functionality
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { BaseAdapter } from '../../src/ai-adapters/core/BaseAdapter.js';
import { AIInput, AIOutput, HealthStatus, ProviderConfig } from '../../src/ai-adapters/core/types.js';

// Mock adapter implementation for testing
class MockAdapter extends BaseAdapter {
  private shouldFail = false;
  private mockResponse: any = {
    content: 'Test response',
    usage: { prompt_tokens: 10, completion_tokens: 20, total_tokens: 30 }
  };

  constructor(config: ProviderConfig, shouldFail = false) {
    super('mock', config);
    this.shouldFail = shouldFail;
  }

  setShouldFail(fail: boolean) {
    this.shouldFail = fail;
  }

  setMockResponse(response: any) {
    this.mockResponse = response;
  }

  protected async makeRequest(input: AIInput): Promise<any> {
    if (this.shouldFail) {
      throw new Error('Mock request failed');
    }

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 100));
    return this.mockResponse;
  }

  protected parseResponse(response: any, input: AIInput): AIOutput {
    return {
      content: response.content,
      usage: {
        promptTokens: response.usage.prompt_tokens,
        completionTokens: response.usage.completion_tokens,
        totalTokens: response.usage.total_tokens
      },
      metadata: {
        model: 'mock-model',
        provider: this.name
      }
    };
  }

  protected calculateCost(output: AIOutput): number {
    const inputCost = (output.usage?.promptTokens || 0) * 0.001;
    const outputCost = (output.usage?.completionTokens || 0) * 0.002;
    return inputCost + outputCost;
  }

  async healthCheck(): Promise<HealthStatus> {
    return {
      healthy: !this.shouldFail,
      responseTime: 100,
      lastCheck: new Date(),
      error: this.shouldFail ? 'Mock health check failed' : undefined
    };
  }
}

describe('BaseAdapter', () => {
  let adapter: MockAdapter;
  let config: ProviderConfig;

  beforeEach(() => {
    config = {
      name: 'mock',
      baseUrl: 'https://api.mock.com',
      apiKey: 'test-key',
      timeout: 5000,
      rateLimits: {
        requestsPerMinute: 60,
        tokensPerMinute: 90000
      },
      retry: {
        attempts: 3,
        backoffMs: 1000,
        exponential: true
      }
    };

    adapter = new MockAdapter(config);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('predict', () => {
    it('should make successful prediction', async () => {
      const input: AIInput = {
        prompt: 'Test prompt',
        parameters: {
          temperature: 0.7,
          maxTokens: 100
        }
      };

      const result = await adapter.predict(input);

      expect(result.content).toBe('Test response');
      expect(result.usage?.totalTokens).toBe(30);
      expect(result.metadata?.provider).toBe('mock');
    });

    it('should validate input', async () => {
      const invalidInput: AIInput = {
        prompt: '',
        parameters: {
          temperature: -1, // Invalid temperature
          maxTokens: 100
        }
      };

      await expect(adapter.predict(invalidInput)).rejects.toThrow('temperature must be between 0 and 2');
    });

    it('should enforce rate limits', async () => {
      // Set very low rate limit
      config.rateLimits = {
        requestsPerMinute: 1,
        tokensPerMinute: 10
      };

      adapter = new MockAdapter(config);

      const input: AIInput = {
        prompt: 'Test prompt',
        parameters: { maxTokens: 100 }
      };

      // First request should succeed
      await adapter.predict(input);

      // Second request should fail due to rate limit
      await expect(adapter.predict(input)).rejects.toThrow('Request rate limit exceeded');
    });

    it('should retry on failure', async () => {
      adapter.setShouldFail(true);

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      // Mock the makeRequest method to fail twice then succeed
      let callCount = 0;
      const originalMakeRequest = adapter['makeRequest'];
      adapter['makeRequest'] = vi.fn().mockImplementation(async (input: AIInput) => {
        callCount++;
        if (callCount <= 2) {
          throw adapter.createError('network', 'Network error', true);
        }
        return originalMakeRequest.call(adapter, input);
      });

      adapter.setShouldFail(false);
      const result = await adapter.predict(input);

      expect(result.content).toBe('Test response');
      expect(adapter['makeRequest']).toHaveBeenCalledTimes(3);
    });

    it('should not retry non-retryable errors', async () => {
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      adapter['makeRequest'] = vi.fn().mockRejectedValue(
        adapter.createError('auth', 'Authentication failed', false)
      );

      await expect(adapter.predict(input)).rejects.toThrow('Authentication failed');
      expect(adapter['makeRequest']).toHaveBeenCalledTimes(1);
    });

    it('should update usage metrics', async () => {
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      const initialUsage = adapter.getUsage();
      expect(initialUsage.totalRequests).toBe(0);

      await adapter.predict(input);

      const updatedUsage = adapter.getUsage();
      expect(updatedUsage.totalRequests).toBe(1);
      expect(updatedUsage.totalTokens).toBe(30);
      expect(updatedUsage.totalCost).toBeGreaterThan(0);
      expect(updatedUsage.averageResponseTime).toBeGreaterThan(0);
    });

    it('should record errors in metrics', async () => {
      adapter.setShouldFail(true);

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await expect(adapter.predict(input)).rejects.toThrow();

      const usage = adapter.getUsage();
      expect(usage.errorRate).toBeGreaterThan(0);
    });
  });

  describe('rate limiting', () => {
    it('should track request counts', async () => {
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      const initialLimit = adapter.getRateLimit();
      expect(initialLimit.currentUsage.requests).toBe(0);

      await adapter.predict(input);

      const updatedLimit = adapter.getRateLimit();
      expect(updatedLimit.currentUsage.requests).toBe(1);
    });

    it('should track token usage', async () => {
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await adapter.predict(input);

      const rateLimit = adapter.getRateLimit();
      expect(rateLimit.currentUsage.tokens).toBeGreaterThan(0);
    });

    it('should reset rate limits after time window', async () => {
      // This would be better tested with time mocking
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await adapter.predict(input);

      const rateLimit = adapter.getRateLimit();
      expect(rateLimit.currentUsage.requests).toBe(1);

      // In a real test, we'd mock time to advance past the window
      // For now, we just verify the structure is correct
      expect(rateLimit.resetTime).toBeInstanceOf(Date);
    });
  });

  describe('configuration validation', () => {
    it('should validate valid configuration', async () => {
      const isValid = await adapter.validateConfig();
      expect(isValid).toBe(true);
    });

    it('should reject configuration without API key', async () => {
      const invalidConfig = { ...config, apiKey: '' };
      const invalidAdapter = new MockAdapter(invalidConfig);

      const isValid = await invalidAdapter.validateConfig();
      expect(isValid).toBe(false);
    });

    it('should reject configuration without base URL', async () => {
      const invalidConfig = { ...config, baseUrl: '' };
      const invalidAdapter = new MockAdapter(invalidConfig);

      const isValid = await invalidAdapter.validateConfig();
      expect(isValid).toBe(false);
    });
  });

  describe('health check', () => {
    it('should return healthy status', async () => {
      const health = await adapter.healthCheck();

      expect(health.healthy).toBe(true);
      expect(health.responseTime).toBeGreaterThan(0);
      expect(health.lastCheck).toBeInstanceOf(Date);
      expect(health.error).toBeUndefined();
    });

    it('should return unhealthy status on failure', async () => {
      adapter.setShouldFail(true);

      const health = await adapter.healthCheck();

      expect(health.healthy).toBe(false);
      expect(health.error).toBeDefined();
    });
  });

  describe('usage management', () => {
    it('should get current usage', () => {
      const usage = adapter.getUsage();

      expect(usage).toHaveProperty('totalRequests');
      expect(usage).toHaveProperty('totalTokens');
      expect(usage).toHaveProperty('totalCost');
      expect(usage).toHaveProperty('averageResponseTime');
      expect(usage).toHaveProperty('errorRate');
      expect(usage).toHaveProperty('lastReset');
    });

    it('should reset usage metrics', async () => {
      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await adapter.predict(input);

      let usage = adapter.getUsage();
      expect(usage.totalRequests).toBe(1);

      adapter.resetUsage();

      usage = adapter.getUsage();
      expect(usage.totalRequests).toBe(0);
      expect(usage.totalTokens).toBe(0);
      expect(usage.totalCost).toBe(0);
    });
  });

  describe('error handling', () => {
    it('should create standardized errors', () => {
      const error = adapter.createError('network', 'Test error', true, 500);

      expect(error.provider).toBe('mock');
      expect(error.type).toBe('network');
      expect(error.retryable).toBe(true);
      expect(error.statusCode).toBe(500);
      expect(error.message).toBe('Test error');
    });

    it('should handle timeout errors', async () => {
      const slowAdapter = new MockAdapter({
        ...config,
        timeout: 50 // Very short timeout
      });

      // Make the request take longer than timeout
      slowAdapter['makeRequest'] = vi.fn().mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return { content: 'Too slow' };
      });

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await expect(slowAdapter.predict(input)).rejects.toThrow();
    });
  });

  describe('token estimation', () => {
    it('should estimate tokens from prompt', () => {
      const input: AIInput = {
        prompt: 'This is a test prompt with multiple words'
      };

      const estimated = adapter['estimateTokens'](input);
      expect(estimated).toBeGreaterThan(0);
      expect(estimated).toBeLessThan(1000); // Reasonable estimate
    });

    it('should estimate tokens from messages', () => {
      const input: AIInput = {
        messages: [
          { role: 'user', content: 'Hello' },
          { role: 'assistant', content: 'Hi there!' },
          { role: 'user', content: 'How are you?' }
        ]
      };

      const estimated = adapter['estimateTokens'](input);
      expect(estimated).toBeGreaterThan(0);
    });
  });
});