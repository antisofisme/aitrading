/**
 * Factory for creating and managing AI adapters
 */

import { AIProvider, ProviderConfig, AdapterOptions } from './types.js';
import { OpenAIAdapter } from '../providers/OpenAIAdapter.js';
import { AnthropicAdapter } from '../providers/AnthropicAdapter.js';
import { GoogleAIAdapter } from '../providers/GoogleAIAdapter.js';
import { CustomAPIAdapter } from '../providers/CustomAPIAdapter.js';
import { LocalModelAdapter } from '../providers/LocalModelAdapter.js';

export type SupportedProvider = 'openai' | 'anthropic' | 'google' | 'custom' | 'local';

export interface AdapterRegistry {
  [key: string]: new (config: any) => AIProvider;
}

export class AdapterFactory {
  private static instance: AdapterFactory;
  private adapters: Map<string, AIProvider> = new Map();
  private registry: AdapterRegistry = {
    openai: OpenAIAdapter,
    anthropic: AnthropicAdapter,
    google: GoogleAIAdapter,
    custom: CustomAPIAdapter,
    local: LocalModelAdapter
  };

  private constructor() {}

  static getInstance(): AdapterFactory {
    if (!AdapterFactory.instance) {
      AdapterFactory.instance = new AdapterFactory();
    }
    return AdapterFactory.instance;
  }

  /**
   * Register a custom adapter type
   */
  registerAdapter(name: string, adapterClass: new (config: any) => AIProvider): void {
    this.registry[name] = adapterClass;
  }

  /**
   * Create an adapter instance
   */
  createAdapter(provider: SupportedProvider | string, config: ProviderConfig): AIProvider {
    const AdapterClass = this.registry[provider];

    if (!AdapterClass) {
      throw new Error(`Unsupported provider: ${provider}. Available providers: ${Object.keys(this.registry).join(', ')}`);
    }

    // Validate required configuration
    this.validateConfig(provider, config);

    const adapter = new AdapterClass(config);

    // Cache the adapter instance
    const cacheKey = `${provider}-${config.name || 'default'}`;
    this.adapters.set(cacheKey, adapter);

    return adapter;
  }

  /**
   * Get or create an adapter
   */
  getAdapter(provider: SupportedProvider | string, config: ProviderConfig): AIProvider {
    const cacheKey = `${provider}-${config.name || 'default'}`;

    let adapter = this.adapters.get(cacheKey);

    if (!adapter) {
      adapter = this.createAdapter(provider, config);
    }

    return adapter;
  }

  /**
   * Create adapter from URL configuration
   */
  createFromUrl(url: string, token: string, options?: Partial<ProviderConfig>): AIProvider {
    const urlObj = new URL(url);
    const provider = this.detectProviderFromUrl(url);

    const config: ProviderConfig = {
      name: provider,
      baseUrl: `${urlObj.protocol}//${urlObj.host}${urlObj.pathname}`,
      apiKey: token,
      ...options
    };

    return this.createAdapter(provider, config);
  }

  /**
   * Create multiple adapters for fallback configuration
   */
  createFallbackChain(configs: Array<{ provider: SupportedProvider | string; config: ProviderConfig }>): AIProvider[] {
    return configs.map(({ provider, config }) => this.createAdapter(provider, config));
  }

  /**
   * List all cached adapters
   */
  listAdapters(): Array<{ key: string; adapter: AIProvider }> {
    return Array.from(this.adapters.entries()).map(([key, adapter]) => ({ key, adapter }));
  }

  /**
   * Clear cached adapters
   */
  clearCache(): void {
    this.adapters.clear();
  }

  /**
   * Remove specific adapter from cache
   */
  removeAdapter(provider: SupportedProvider | string, name?: string): boolean {
    const cacheKey = `${provider}-${name || 'default'}`;
    return this.adapters.delete(cacheKey);
  }

  /**
   * Get available provider types
   */
  getAvailableProviders(): string[] {
    return Object.keys(this.registry);
  }

  /**
   * Validate adapter configuration
   */
  private validateConfig(provider: string, config: ProviderConfig): void {
    // Common validation
    if (!config.baseUrl) {
      throw new Error(`baseUrl is required for ${provider} adapter`);
    }

    if (!config.apiKey && provider !== 'local') {
      throw new Error(`apiKey is required for ${provider} adapter`);
    }

    // Provider-specific validation
    switch (provider) {
      case 'openai':
        this.validateOpenAIConfig(config);
        break;
      case 'anthropic':
        this.validateAnthropicConfig(config);
        break;
      case 'google':
        this.validateGoogleConfig(config);
        break;
      case 'custom':
        this.validateCustomConfig(config);
        break;
      case 'local':
        this.validateLocalConfig(config);
        break;
    }
  }

  private validateOpenAIConfig(config: ProviderConfig): void {
    if (!config.baseUrl.includes('openai.com') && !config.baseUrl.includes('azure.com')) {
      console.warn('OpenAI adapter is being used with a non-OpenAI URL. Ensure compatibility.');
    }
  }

  private validateAnthropicConfig(config: ProviderConfig): void {
    if (!config.baseUrl.includes('anthropic.com')) {
      console.warn('Anthropic adapter is being used with a non-Anthropic URL. Ensure compatibility.');
    }
  }

  private validateGoogleConfig(config: ProviderConfig): void {
    if (!config.baseUrl.includes('googleapis.com')) {
      console.warn('Google adapter is being used with a non-Google URL. Ensure compatibility.');
    }
  }

  private validateCustomConfig(config: ProviderConfig): void {
    const customConfig = config as any;
    if (!customConfig.options?.requestMapping?.promptField) {
      throw new Error('Custom adapter requires options.requestMapping.promptField');
    }
    if (!customConfig.options?.responseMapping?.contentField) {
      throw new Error('Custom adapter requires options.responseMapping.contentField');
    }
  }

  private validateLocalConfig(config: ProviderConfig): void {
    const localConfig = config as any;
    if (!localConfig.options?.modelName) {
      throw new Error('Local adapter requires options.modelName');
    }
    if (!localConfig.options?.modelType) {
      throw new Error('Local adapter requires options.modelType');
    }
  }

  /**
   * Detect provider type from URL
   */
  private detectProviderFromUrl(url: string): SupportedProvider {
    const urlLower = url.toLowerCase();

    if (urlLower.includes('openai.com') || urlLower.includes('azure.com/openai')) {
      return 'openai';
    }
    if (urlLower.includes('anthropic.com')) {
      return 'anthropic';
    }
    if (urlLower.includes('googleapis.com') || urlLower.includes('generativelanguage.googleapis.com')) {
      return 'google';
    }
    if (urlLower.includes('localhost') || urlLower.includes('127.0.0.1') || urlLower.includes('192.168.')) {
      return 'local';
    }

    // Default to custom for unknown URLs
    return 'custom';
  }
}

/**
 * Convenience functions
 */

/**
 * Create an OpenAI adapter
 */
export function createOpenAIAdapter(apiKey: string, options?: Partial<ProviderConfig>): AIProvider {
  const config: ProviderConfig = {
    name: 'openai',
    baseUrl: 'https://api.openai.com/v1',
    apiKey,
    defaultModel: 'gpt-3.5-turbo',
    ...options
  };

  return AdapterFactory.getInstance().createAdapter('openai', config);
}

/**
 * Create an Anthropic adapter
 */
export function createAnthropicAdapter(apiKey: string, options?: Partial<ProviderConfig>): AIProvider {
  const config: ProviderConfig = {
    name: 'anthropic',
    baseUrl: 'https://api.anthropic.com/v1',
    apiKey,
    defaultModel: 'claude-3-sonnet-20240229',
    ...options
  };

  return AdapterFactory.getInstance().createAdapter('anthropic', config);
}

/**
 * Create a Google AI adapter
 */
export function createGoogleAIAdapter(apiKey: string, options?: Partial<ProviderConfig>): AIProvider {
  const config: ProviderConfig = {
    name: 'google',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    apiKey,
    defaultModel: 'gemini-pro',
    ...options
  };

  return AdapterFactory.getInstance().createAdapter('google', config);
}

/**
 * Create adapter from simple URL + token configuration
 */
export function createAdapterFromUrl(url: string, token: string, options?: Partial<ProviderConfig>): AIProvider {
  return AdapterFactory.getInstance().createFromUrl(url, token, options);
}

/**
 * Create a local model adapter
 */
export function createLocalAdapter(
  baseUrl: string,
  modelName: string,
  modelType: 'ollama' | 'llamacpp' | 'vllm' | 'tgi' | 'custom',
  options?: Partial<ProviderConfig>
): AIProvider {
  const config = {
    name: 'local',
    baseUrl,
    apiKey: '', // Not required for local models
    options: {
      modelName,
      modelType,
      ...options?.options
    },
    ...options
  } as any;

  return AdapterFactory.getInstance().createAdapter('local', config);
}