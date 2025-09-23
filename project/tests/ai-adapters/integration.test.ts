/**
 * Integration tests for AI adapter system
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  AIAdapter,
  createSimpleAdapter,
  createMultiProviderAdapter,
  AdapterOrchestrator,
  PerformanceMonitor,
  CostTracker
} from '../../src/ai-adapters/index.js';
import { AIInput, ProviderConfig } from '../../src/ai-adapters/core/types.js';

// Mock fetch for testing
global.fetch = vi.fn();

const mockSuccessResponse = {
  ok: true,
  status: 200,
  json: async () => ({
    choices: [{
      message: {
        role: 'assistant',
        content: 'Test response from API'
      },
      finish_reason: 'stop'
    }],
    usage: {
      prompt_tokens: 10,
      completion_tokens: 15,
      total_tokens: 25
    },
    model: 'gpt-3.5-turbo',
    id: 'test-request-id'
  })
};

describe('AI Adapter Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (fetch as any).mockResolvedValue(mockSuccessResponse);
  });

  describe('Simple Adapter', () => {
    it('should create and use simple OpenAI adapter', async () => {
      const adapter = createSimpleAdapter('openai', 'test-api-key', {
        model: 'gpt-3.5-turbo'
      });

      const input: AIInput = {
        prompt: 'Hello, world!',
        parameters: {
          temperature: 0.7,
          maxTokens: 100
        }
      };

      const result = await adapter.predict(input);

      expect(result.content).toBe('Test response from API');
      expect(result.usage?.totalTokens).toBe(25);
      expect(result.metadata?.provider).toBe('openai');

      // Verify fetch was called correctly
      expect(fetch).toHaveBeenCalledWith(
        'https://api.openai.com/v1/chat/completions',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-api-key',
            'Content-Type': 'application/json'
          }),
          body: expect.stringContaining('Hello, world!')
        })
      );
    });

    it('should track usage and costs', async () => {
      const adapter = createSimpleAdapter('openai', 'test-api-key');

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await adapter.predict(input);

      const usage = adapter.getUsage();
      expect(usage.totalRequests).toBe(1);
      expect(usage.totalTokens).toBe(25);
      expect(usage.averageResponseTime).toBeGreaterThan(0);

      const costTracker = adapter.getCostTracking();
      expect(costTracker).toBeDefined();
    });

    it('should monitor performance', async () => {
      const adapter = createSimpleAdapter('openai', 'test-api-key');

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await adapter.predict(input);

      const monitor = adapter.getPerformanceMonitor();
      expect(monitor).toBeDefined();

      const metrics = monitor?.getMetrics('openai');
      expect(metrics).toBeDefined();
      if (metrics && !Array.isArray(metrics)) {
        expect(metrics.reliability.totalRequests).toBe(1);
        expect(metrics.reliability.successRate).toBe(100);
      }
    });
  });

  describe('Multi-Provider Adapter', () => {
    it('should create adapter with multiple providers', async () => {
      const adapter = createMultiProviderAdapter([
        {
          provider: 'openai',
          apiKey: 'openai-key',
          model: 'gpt-3.5-turbo'
        },
        {
          provider: 'anthropic',
          apiKey: 'anthropic-key',
          model: 'claude-3-sonnet-20240229'
        }
      ], {
        fallbackEnabled: true,
        loadBalancing: { type: 'round_robin' }
      });

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      const result = await adapter.predict(input);

      expect(result.content).toBe('Test response from API');
      expect(['openai', 'anthropic']).toContain(result.metadata?.provider);
    });

    it('should use fallback on primary failure', async () => {
      // Mock first call to fail, second to succeed
      (fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockSuccessResponse);

      const adapter = createMultiProviderAdapter([
        {
          provider: 'openai',
          apiKey: 'openai-key'
        },
        {
          provider: 'anthropic',
          apiKey: 'anthropic-key'
        }
      ], {
        fallbackEnabled: true
      });

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      const result = await adapter.predict(input);

      expect(result.content).toBe('Test response from API');
      expect(fetch).toHaveBeenCalledTimes(2); // First failed, second succeeded
    });
  });

  describe('Orchestrator', () => {
    it('should orchestrate multiple adapters', async () => {
      // Create mock adapters
      const mockAdapter1 = {
        name: 'mock1',
        config: { name: 'mock1', baseUrl: '', apiKey: '' },
        predict: vi.fn().mockResolvedValue({
          content: 'Response from adapter 1',
          metadata: { provider: 'mock1' }
        }),
        healthCheck: vi.fn().mockResolvedValue({
          healthy: true,
          responseTime: 100,
          lastCheck: new Date()
        }),
        getUsage: vi.fn().mockReturnValue({
          totalRequests: 0,
          totalTokens: 0,
          totalCost: 0,
          requestsPerMinute: 0,
          averageResponseTime: 100,
          errorRate: 0,
          lastReset: new Date()
        }),
        getRateLimit: vi.fn().mockReturnValue({
          requestsPerMinute: 60,
          tokensPerMinute: 90000,
          currentUsage: { requests: 0, tokens: 0 },
          resetTime: new Date()
        }),
        resetUsage: vi.fn(),
        validateConfig: vi.fn().mockResolvedValue(true)
      };

      const mockAdapter2 = {
        ...mockAdapter1,
        name: 'mock2',
        predict: vi.fn().mockResolvedValue({
          content: 'Response from adapter 2',
          metadata: { provider: 'mock2' }
        })
      };

      const orchestrator = new AdapterOrchestrator({
        adapters: new Map([
          ['mock1', mockAdapter1 as any],
          ['mock2', mockAdapter2 as any]
        ]),
        loadBalancing: { type: 'round_robin' }
      });

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      // First request should go to first adapter
      const result1 = await orchestrator.predict(input);
      expect(result1.metadata?.provider).toBe('mock1');

      // Second request should go to second adapter (round robin)
      const result2 = await orchestrator.predict(input);
      expect(result2.metadata?.provider).toBe('mock2');
    });

    it('should handle health checking', async () => {
      const mockAdapter = {
        name: 'mock',
        config: { name: 'mock', baseUrl: '', apiKey: '' },
        predict: vi.fn(),
        healthCheck: vi.fn().mockResolvedValue({
          healthy: true,
          responseTime: 150,
          lastCheck: new Date()
        }),
        getUsage: vi.fn().mockReturnValue({
          totalRequests: 5,
          totalTokens: 100,
          totalCost: 0.001,
          requestsPerMinute: 1,
          averageResponseTime: 150,
          errorRate: 0,
          lastReset: new Date()
        }),
        getRateLimit: vi.fn().mockReturnValue({
          requestsPerMinute: 60,
          tokensPerMinute: 90000,
          currentUsage: { requests: 5, tokens: 100 },
          resetTime: new Date()
        }),
        resetUsage: vi.fn(),
        validateConfig: vi.fn().mockResolvedValue(true)
      };

      const orchestrator = new AdapterOrchestrator({
        adapters: new Map([['mock', mockAdapter as any]])
      });

      const health = await orchestrator.healthCheck();

      expect(health.healthy).toBe(true);
      expect(health.details).toHaveProperty('healthyAdapters', 1);
      expect(health.details).toHaveProperty('totalAdapters', 1);
    });
  });

  describe('Performance Monitoring', () => {
    it('should collect and analyze performance metrics', async () => {
      const monitor = new PerformanceMonitor();

      // Record some test metrics
      monitor.recordRequest('openai', 150, true, { input: 10, output: 15, total: 25 }, 0.001);
      monitor.recordRequest('openai', 200, true, { input: 20, output: 30, total: 50 }, 0.002);
      monitor.recordRequest('openai', 300, false, { input: 15, output: 0, total: 15 }, 0.0015, {
        type: 'timeout',
        message: 'Request timeout'
      });

      const metrics = monitor.getMetrics('openai');

      if (metrics && !Array.isArray(metrics)) {
        expect(metrics.reliability.totalRequests).toBe(3);
        expect(metrics.reliability.successfulRequests).toBe(2);
        expect(metrics.reliability.successRate).toBeCloseTo(66.67, 1);
        expect(metrics.timing.averageResponseTime).toBeCloseTo(216.67, 1);
        expect(metrics.usage.totalTokens).toBe(90);
        expect(metrics.usage.totalCost).toBeCloseTo(0.0045, 4);
        expect(metrics.errors).toHaveProperty('timeout', 1);
      }
    });

    it('should generate performance reports', async () => {
      const monitor = new PerformanceMonitor();

      monitor.recordRequest('openai', 150, true, { input: 10, output: 15, total: 25 }, 0.001);
      monitor.recordRequest('anthropic', 200, true, { input: 12, output: 18, total: 30 }, 0.0015);

      const report = monitor.generateReport(undefined, undefined, 'text');

      expect(report).toContain('AI Adapter Performance Report');
      expect(report).toContain('openai');
      expect(report).toContain('anthropic');
      expect(report).toContain('150ms');
      expect(report).toContain('200ms');
    });
  });

  describe('Cost Tracking', () => {
    it('should track costs across providers', async () => {
      const costTracker = new CostTracker({
        monthlyBudget: 100,
        dailyBudget: 10,
        alertThresholds: [50, 75, 90]
      });

      // Record some costs
      costTracker.recordCost('openai', 'gpt-3.5-turbo', {
        content: 'test',
        usage: { promptTokens: 10, completionTokens: 15, totalTokens: 25 }
      } as any, 0.001);

      costTracker.recordCost('anthropic', 'claude-3-sonnet', {
        content: 'test',
        usage: { promptTokens: 12, completionTokens: 18, totalTokens: 30 }
      } as any, 0.0015);

      const totalCosts = costTracker.getTotalCosts();
      expect(totalCosts).toBeCloseTo(0.0025, 4);

      const costsByProvider = costTracker.getCostsByProvider();
      expect(costsByProvider.openai).toBeCloseTo(0.001, 4);
      expect(costsByProvider.anthropic).toBeCloseTo(0.0015, 4);

      const budgetStatus = costTracker.getBudgetStatus();
      expect(budgetStatus.monthly.budget).toBe(100);
      expect(budgetStatus.daily.budget).toBe(10);
      expect(budgetStatus.monthly.spent).toBeCloseTo(0.0025, 4);
    });

    it('should export and import cost data', async () => {
      const costTracker = new CostTracker();

      costTracker.recordCost('openai', 'gpt-4', {
        content: 'test',
        usage: { promptTokens: 10, completionTokens: 15, totalTokens: 25 }
      } as any, 0.005);

      const exportedJson = costTracker.exportCosts('json');
      expect(exportedJson).toContain('openai');
      expect(exportedJson).toContain('gpt-4');
      expect(exportedJson).toContain('0.005');

      const exportedCsv = costTracker.exportCosts('csv');
      expect(exportedCsv).toContain('timestamp,provider,model');
      expect(exportedCsv).toContain('openai,gpt-4');

      // Test import
      const newTracker = new CostTracker();
      const importedCount = newTracker.importCosts(exportedJson, 'json');
      expect(importedCount).toBe(1);

      const importedCosts = newTracker.getTotalCosts();
      expect(importedCosts).toBeCloseTo(0.005, 4);
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors gracefully', async () => {
      (fetch as any).mockRejectedValue(new Error('Network error'));

      const adapter = createSimpleAdapter('openai', 'test-api-key');

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await expect(adapter.predict(input)).rejects.toThrow();

      const usage = adapter.getUsage();
      expect(usage.errorRate).toBeGreaterThan(0);
    });

    it('should handle API errors', async () => {
      (fetch as any).mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => 'Unauthorized'
      });

      const adapter = createSimpleAdapter('openai', 'invalid-key');

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await expect(adapter.predict(input)).rejects.toThrow('Unauthorized');
    });

    it('should handle rate limiting', async () => {
      (fetch as any).mockResolvedValue({
        ok: false,
        status: 429,
        text: async () => 'Rate limit exceeded'
      });

      const adapter = createSimpleAdapter('openai', 'test-api-key');

      const input: AIInput = {
        prompt: 'Test prompt'
      };

      await expect(adapter.predict(input)).rejects.toThrow('Rate limit exceeded');
    });
  });

  describe('Configuration Validation', () => {
    it('should validate adapter configuration', async () => {
      const adapter = createSimpleAdapter('openai', 'test-api-key');

      const isValid = await adapter.getOrchestrator().validateConfig();
      expect(isValid).toBe(true);
    });

    it('should detect invalid configuration', async () => {
      // Mock health check to fail
      (fetch as any).mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => 'Invalid API key'
      });

      const adapter = createSimpleAdapter('openai', 'invalid-key');

      const health = await adapter.healthCheck();
      expect(health.healthy).toBe(false);
    });
  });
});