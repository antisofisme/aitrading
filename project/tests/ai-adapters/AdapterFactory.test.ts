/**
 * Tests for AdapterFactory
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  AdapterFactory,
  createOpenAIAdapter,
  createAnthropicAdapter,
  createGoogleAIAdapter,
  createAdapterFromUrl,
  createLocalAdapter,
  SupportedProvider
} from '../../src/ai-adapters/core/AdapterFactory.js';
import { ProviderConfig } from '../../src/ai-adapters/core/types.js';

describe('AdapterFactory', () => {
  let factory: AdapterFactory;

  beforeEach(() => {
    factory = AdapterFactory.getInstance();
    factory.clearCache(); // Start with clean cache
  });

  afterEach(() => {
    factory.clearCache();
  });

  describe('getInstance', () => {
    it('should return singleton instance', () => {
      const instance1 = AdapterFactory.getInstance();
      const instance2 = AdapterFactory.getInstance();

      expect(instance1).toBe(instance2);
    });
  });

  describe('createAdapter', () => {
    it('should create OpenAI adapter', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key'
      };

      const adapter = factory.createAdapter('openai', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('openai');
    });

    it('should create Anthropic adapter', () => {
      const config: ProviderConfig = {
        name: 'anthropic',
        baseUrl: 'https://api.anthropic.com/v1',
        apiKey: 'test-key'
      };

      const adapter = factory.createAdapter('anthropic', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('anthropic');
    });

    it('should create Google AI adapter', () => {
      const config: ProviderConfig = {
        name: 'google',
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
        apiKey: 'test-key'
      };

      const adapter = factory.createAdapter('google', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('google');
    });

    it('should create custom adapter', () => {
      const config: any = {
        name: 'custom',
        baseUrl: 'https://api.example.com',
        apiKey: 'test-key',
        options: {
          requestMapping: {
            promptField: 'prompt'
          },
          responseMapping: {
            contentField: 'response'
          }
        }
      };

      const adapter = factory.createAdapter('custom', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('custom-api');
    });

    it('should create local adapter', () => {
      const config: any = {
        name: 'local',
        baseUrl: 'http://localhost:11434',
        apiKey: '',
        options: {
          modelName: 'llama2',
          modelType: 'ollama'
        }
      };

      const adapter = factory.createAdapter('local', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('local-model');
    });

    it('should throw error for unsupported provider', () => {
      const config: ProviderConfig = {
        name: 'unsupported',
        baseUrl: 'https://api.example.com',
        apiKey: 'test-key'
      };

      expect(() => {
        factory.createAdapter('unsupported' as SupportedProvider, config);
      }).toThrow('Unsupported provider: unsupported');
    });

    it('should validate required configuration', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: '',
        apiKey: 'test-key'
      };

      expect(() => {
        factory.createAdapter('openai', config);
      }).toThrow('baseUrl is required');
    });

    it('should validate API key requirement', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: ''
      };

      expect(() => {
        factory.createAdapter('openai', config);
      }).toThrow('apiKey is required');
    });

    it('should not require API key for local adapters', () => {
      const config: any = {
        name: 'local',
        baseUrl: 'http://localhost:11434',
        apiKey: '',
        options: {
          modelName: 'llama2',
          modelType: 'ollama'
        }
      };

      expect(() => {
        factory.createAdapter('local', config);
      }).not.toThrow();
    });
  });

  describe('getAdapter', () => {
    it('should return cached adapter', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key'
      };

      const adapter1 = factory.getAdapter('openai', config);
      const adapter2 = factory.getAdapter('openai', config);

      expect(adapter1).toBe(adapter2);
    });

    it('should create new adapter if not cached', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key'
      };

      const adapter = factory.getAdapter('openai', config);

      expect(adapter).toBeDefined();
      expect(adapter.name).toBe('openai');
    });
  });

  describe('createFromUrl', () => {
    it('should detect OpenAI from URL', () => {
      const adapter = factory.createFromUrl('https://api.openai.com/v1/chat/completions', 'test-key');

      expect(adapter.name).toBe('openai');
    });

    it('should detect Anthropic from URL', () => {
      const adapter = factory.createFromUrl('https://api.anthropic.com/v1/messages', 'test-key');

      expect(adapter.name).toBe('anthropic');
    });

    it('should detect Google from URL', () => {
      const adapter = factory.createFromUrl('https://generativelanguage.googleapis.com/v1beta/models', 'test-key');

      expect(adapter.name).toBe('google');
    });

    it('should use custom for unknown URLs', () => {
      const adapter = factory.createFromUrl('https://api.example.com/v1/generate', 'test-key');

      expect(adapter.name).toBe('custom-api');
    });

    it('should detect local from localhost URL', () => {
      const adapter = factory.createFromUrl('http://localhost:11434/api/generate', 'test-key');

      expect(adapter.name).toBe('local-model');
    });
  });

  describe('createFallbackChain', () => {
    it('should create multiple adapters', () => {
      const configs = [
        {
          provider: 'openai' as SupportedProvider,
          config: {
            name: 'openai',
            baseUrl: 'https://api.openai.com/v1',
            apiKey: 'test-key-1'
          }
        },
        {
          provider: 'anthropic' as SupportedProvider,
          config: {
            name: 'anthropic',
            baseUrl: 'https://api.anthropic.com/v1',
            apiKey: 'test-key-2'
          }
        }
      ];

      const adapters = factory.createFallbackChain(configs);

      expect(adapters).toHaveLength(2);
      expect(adapters[0].name).toBe('openai');
      expect(adapters[1].name).toBe('anthropic');
    });
  });

  describe('registerAdapter', () => {
    it('should register custom adapter class', () => {
      class CustomTestAdapter {
        public readonly name = 'test';
        public readonly config: any;

        constructor(config: any) {
          this.config = config;
        }

        async predict() {
          return { content: 'test' };
        }

        async healthCheck() {
          return { healthy: true, responseTime: 100, lastCheck: new Date() };
        }

        getUsage() {
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

        getRateLimit() {
          return {
            requestsPerMinute: Infinity,
            tokensPerMinute: Infinity,
            currentUsage: { requests: 0, tokens: 0 },
            resetTime: new Date()
          };
        }

        resetUsage() {}

        async validateConfig() {
          return true;
        }
      }

      factory.registerAdapter('test', CustomTestAdapter);

      const config: ProviderConfig = {
        name: 'test',
        baseUrl: 'https://api.test.com',
        apiKey: 'test-key'
      };

      const adapter = factory.createAdapter('test', config);

      expect(adapter.name).toBe('test');
    });
  });

  describe('cache management', () => {
    it('should list cached adapters', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key'
      };

      factory.createAdapter('openai', config);

      const adapters = factory.listAdapters();

      expect(adapters).toHaveLength(1);
      expect(adapters[0].key).toBe('openai-default');
      expect(adapters[0].adapter.name).toBe('openai');
    });

    it('should remove specific adapter from cache', () => {
      const config: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key'
      };

      factory.createAdapter('openai', config);

      let adapters = factory.listAdapters();
      expect(adapters).toHaveLength(1);

      const removed = factory.removeAdapter('openai');
      expect(removed).toBe(true);

      adapters = factory.listAdapters();
      expect(adapters).toHaveLength(0);
    });

    it('should clear all adapters from cache', () => {
      const config1: ProviderConfig = {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'test-key-1'
      };

      const config2: ProviderConfig = {
        name: 'anthropic',
        baseUrl: 'https://api.anthropic.com/v1',
        apiKey: 'test-key-2'
      };

      factory.createAdapter('openai', config1);
      factory.createAdapter('anthropic', config2);

      let adapters = factory.listAdapters();
      expect(adapters).toHaveLength(2);

      factory.clearCache();

      adapters = factory.listAdapters();
      expect(adapters).toHaveLength(0);
    });
  });

  describe('getAvailableProviders', () => {
    it('should return list of available provider types', () => {
      const providers = factory.getAvailableProviders();

      expect(providers).toContain('openai');
      expect(providers).toContain('anthropic');
      expect(providers).toContain('google');
      expect(providers).toContain('custom');
      expect(providers).toContain('local');
    });
  });
});

describe('Convenience functions', () => {
  describe('createOpenAIAdapter', () => {
    it('should create OpenAI adapter with defaults', () => {
      const adapter = createOpenAIAdapter('test-key');

      expect(adapter.name).toBe('openai');
      expect(adapter.config.baseUrl).toBe('https://api.openai.com/v1');
      expect(adapter.config.defaultModel).toBe('gpt-3.5-turbo');
    });

    it('should override defaults with options', () => {
      const adapter = createOpenAIAdapter('test-key', {
        defaultModel: 'gpt-4',
        timeout: 60000
      });

      expect(adapter.config.defaultModel).toBe('gpt-4');
      expect(adapter.config.timeout).toBe(60000);
    });
  });

  describe('createAnthropicAdapter', () => {
    it('should create Anthropic adapter with defaults', () => {
      const adapter = createAnthropicAdapter('test-key');

      expect(adapter.name).toBe('anthropic');
      expect(adapter.config.baseUrl).toBe('https://api.anthropic.com/v1');
      expect(adapter.config.defaultModel).toBe('claude-3-sonnet-20240229');
    });
  });

  describe('createGoogleAIAdapter', () => {
    it('should create Google AI adapter with defaults', () => {
      const adapter = createGoogleAIAdapter('test-key');

      expect(adapter.name).toBe('google');
      expect(adapter.config.baseUrl).toBe('https://generativelanguage.googleapis.com/v1beta');
      expect(adapter.config.defaultModel).toBe('gemini-pro');
    });
  });

  describe('createLocalAdapter', () => {
    it('should create local adapter', () => {
      const adapter = createLocalAdapter('http://localhost:11434', 'llama2', 'ollama');

      expect(adapter.name).toBe('local-model');
      expect(adapter.config.baseUrl).toBe('http://localhost:11434');
    });
  });

  describe('createAdapterFromUrl', () => {
    it('should create adapter from URL and token', () => {
      const adapter = createAdapterFromUrl('https://api.openai.com/v1', 'test-key');

      expect(adapter.name).toBe('openai');
      expect(adapter.config.apiKey).toBe('test-key');
    });
  });
});