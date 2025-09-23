/**
 * Configuration management system for AI adapters
 */

import { ProviderConfig, AdapterOptions } from '../core/types.js';
import { SupportedProvider } from '../core/AdapterFactory.js';

export interface AIAdapterConfig {
  /** Default provider to use */
  defaultProvider: string;
  /** Provider configurations */
  providers: Record<string, ProviderConfig>;
  /** Global settings */
  global: {
    /** Global timeout for all requests */
    timeout?: number;
    /** Enable debug logging */
    debug?: boolean;
    /** Maximum concurrent requests across all providers */
    maxConcurrentRequests?: number;
    /** Default retry configuration */
    retry?: {
      attempts: number;
      backoffMs: number;
      exponential: boolean;
    };
  };
  /** Fallback configuration */
  fallback?: {
    enabled: boolean;
    providers: string[];
    triggers: ('error' | 'timeout' | 'rate_limit')[];
    maxAttempts: number;
  };
  /** Load balancing configuration */
  loadBalancing?: {
    strategy: 'round_robin' | 'least_latency' | 'least_usage' | 'health_based' | 'random';
    weights?: Record<string, number>;
  };
  /** Cost tracking configuration */
  costTracking?: {
    enabled: boolean;
    monthlyBudget?: number;
    dailyBudget?: number;
    alertThresholds?: number[];
    detailed?: boolean;
  };
  /** Performance monitoring configuration */
  monitoring?: {
    enabled: boolean;
    maxMetrics?: number;
    retentionDays?: number;
    alertRules?: Array<{
      name: string;
      condition: {
        metric: string;
        operator: '>' | '<' | '>=' | '<=' | '=' | '!=';
        value: number;
        duration?: number;
      };
      action: 'log' | 'email' | 'webhook' | 'disable_provider';
    }>;
  };
}

export interface ConfigSource {
  load(): Promise<Partial<AIAdapterConfig>>;
  save(config: Partial<AIAdapterConfig>): Promise<void>;
}

export class FileConfigSource implements ConfigSource {
  constructor(private filePath: string) {}

  async load(): Promise<Partial<AIAdapterConfig>> {
    try {
      const fs = await import('fs/promises');
      const content = await fs.readFile(this.filePath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      if ((error as any)?.code === 'ENOENT') {
        return {}; // File doesn't exist
      }
      throw error;
    }
  }

  async save(config: Partial<AIAdapterConfig>): Promise<void> {
    const fs = await import('fs/promises');
    const path = await import('path');

    // Ensure directory exists
    await fs.mkdir(path.dirname(this.filePath), { recursive: true });

    await fs.writeFile(this.filePath, JSON.stringify(config, null, 2));
  }
}

export class EnvironmentConfigSource implements ConfigSource {
  async load(): Promise<Partial<AIAdapterConfig>> {
    const config: Partial<AIAdapterConfig> = {
      providers: {},
      global: {}
    };

    // Load environment variables
    const env = process.env;

    // Global settings
    if (env.AI_ADAPTER_TIMEOUT) {
      config.global!.timeout = parseInt(env.AI_ADAPTER_TIMEOUT);
    }

    if (env.AI_ADAPTER_DEBUG) {
      config.global!.debug = env.AI_ADAPTER_DEBUG === 'true';
    }

    if (env.AI_ADAPTER_DEFAULT_PROVIDER) {
      config.defaultProvider = env.AI_ADAPTER_DEFAULT_PROVIDER;
    }

    // Provider configurations
    this.loadProviderFromEnv(config, 'openai', env);
    this.loadProviderFromEnv(config, 'anthropic', env);
    this.loadProviderFromEnv(config, 'google', env);

    return config;
  }

  async save(config: Partial<AIAdapterConfig>): Promise<void> {
    // Environment variables are read-only, so this is a no-op
    console.warn('EnvironmentConfigSource does not support saving configuration');
  }

  private loadProviderFromEnv(config: Partial<AIAdapterConfig>, provider: string, env: NodeJS.ProcessEnv): void {
    const prefix = `AI_ADAPTER_${provider.toUpperCase()}`;

    const apiKey = env[`${prefix}_API_KEY`];
    const baseUrl = env[`${prefix}_BASE_URL`];
    const model = env[`${prefix}_DEFAULT_MODEL`];

    if (apiKey || baseUrl) {
      config.providers![provider] = {
        name: provider,
        apiKey: apiKey || '',
        baseUrl: baseUrl || this.getDefaultBaseUrl(provider),
        defaultModel: model
      };
    }
  }

  private getDefaultBaseUrl(provider: string): string {
    switch (provider) {
      case 'openai': return 'https://api.openai.com/v1';
      case 'anthropic': return 'https://api.anthropic.com/v1';
      case 'google': return 'https://generativelanguage.googleapis.com/v1beta';
      default: return '';
    }
  }
}

export class ConfigManager {
  private config: AIAdapterConfig;
  private sources: ConfigSource[] = [];

  constructor(initialConfig?: Partial<AIAdapterConfig>) {
    this.config = this.getDefaultConfig();

    if (initialConfig) {
      this.mergeConfig(initialConfig);
    }
  }

  /**
   * Add a configuration source
   */
  addSource(source: ConfigSource): void {
    this.sources.push(source);
  }

  /**
   * Load configuration from all sources
   */
  async load(): Promise<void> {
    for (const source of this.sources) {
      try {
        const configPart = await source.load();
        this.mergeConfig(configPart);
      } catch (error) {
        console.warn(`Failed to load config from source: ${error}`);
      }
    }
  }

  /**
   * Save configuration to all writable sources
   */
  async save(): Promise<void> {
    const savePromises = this.sources.map(async source => {
      try {
        await source.save(this.config);
      } catch (error) {
        console.warn(`Failed to save config to source: ${error}`);
      }
    });

    await Promise.all(savePromises);
  }

  /**
   * Get the current configuration
   */
  getConfig(): AIAdapterConfig {
    return JSON.parse(JSON.stringify(this.config)); // Deep copy
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<AIAdapterConfig>): void {
    this.mergeConfig(updates);
  }

  /**
   * Get provider configuration
   */
  getProviderConfig(provider: string): ProviderConfig | undefined {
    return this.config.providers[provider];
  }

  /**
   * Add or update a provider configuration
   */
  setProviderConfig(provider: string, config: ProviderConfig): void {
    this.config.providers[provider] = config;
  }

  /**
   * Remove a provider configuration
   */
  removeProviderConfig(provider: string): boolean {
    if (this.config.providers[provider]) {
      delete this.config.providers[provider];
      return true;
    }
    return false;
  }

  /**
   * Get list of configured providers
   */
  getConfiguredProviders(): string[] {
    return Object.keys(this.config.providers);
  }

  /**
   * Validate configuration
   */
  validate(): {
    valid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check if default provider exists
    if (this.config.defaultProvider && !this.config.providers[this.config.defaultProvider]) {
      errors.push(`Default provider '${this.config.defaultProvider}' is not configured`);
    }

    // Validate each provider
    for (const [name, provider] of Object.entries(this.config.providers)) {
      if (!provider.baseUrl) {
        errors.push(`Provider '${name}' is missing baseUrl`);
      }

      if (!provider.apiKey && name !== 'local') {
        warnings.push(`Provider '${name}' is missing apiKey`);
      }

      // Validate retry configuration
      if (provider.retry) {
        if (provider.retry.attempts < 1) {
          errors.push(`Provider '${name}' retry attempts must be at least 1`);
        }
        if (provider.retry.backoffMs < 0) {
          errors.push(`Provider '${name}' retry backoff must be non-negative`);
        }
      }

      // Validate rate limits
      if (provider.rateLimits) {
        if (provider.rateLimits.requestsPerMinute && provider.rateLimits.requestsPerMinute < 1) {
          errors.push(`Provider '${name}' requests per minute must be at least 1`);
        }
        if (provider.rateLimits.tokensPerMinute && provider.rateLimits.tokensPerMinute < 1) {
          errors.push(`Provider '${name}' tokens per minute must be at least 1`);
        }
      }
    }

    // Validate fallback configuration
    if (this.config.fallback?.enabled) {
      if (!this.config.fallback.providers || this.config.fallback.providers.length === 0) {
        errors.push('Fallback is enabled but no fallback providers are configured');
      }

      for (const provider of this.config.fallback.providers || []) {
        if (!this.config.providers[provider]) {
          errors.push(`Fallback provider '${provider}' is not configured`);
        }
      }
    }

    // Validate cost tracking
    if (this.config.costTracking?.enabled) {
      if (this.config.costTracking.monthlyBudget && this.config.costTracking.monthlyBudget <= 0) {
        errors.push('Monthly budget must be positive');
      }
      if (this.config.costTracking.dailyBudget && this.config.costTracking.dailyBudget <= 0) {
        errors.push('Daily budget must be positive');
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Export configuration
   */
  export(format: 'json' | 'yaml' | 'env' = 'json'): string {
    switch (format) {
      case 'json':
        return JSON.stringify(this.config, null, 2);

      case 'yaml':
        // Simple YAML export - in production, use a proper YAML library
        return this.toYaml(this.config);

      case 'env':
        return this.toEnvironmentVariables(this.config);

      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Import configuration
   */
  import(data: string, format: 'json' | 'yaml' | 'env' = 'json'): void {
    let importedConfig: Partial<AIAdapterConfig>;

    switch (format) {
      case 'json':
        importedConfig = JSON.parse(data);
        break;

      case 'yaml':
        // Simple YAML import - in production, use a proper YAML library
        importedConfig = this.fromYaml(data);
        break;

      case 'env':
        importedConfig = this.fromEnvironmentVariables(data);
        break;

      default:
        throw new Error(`Unsupported import format: ${format}`);
    }

    this.mergeConfig(importedConfig);
  }

  /**
   * Get configuration template for a provider
   */
  getProviderTemplate(provider: SupportedProvider): ProviderConfig {
    const templates: Record<SupportedProvider, ProviderConfig> = {
      openai: {
        name: 'openai',
        baseUrl: 'https://api.openai.com/v1',
        apiKey: 'your-openai-api-key',
        defaultModel: 'gpt-3.5-turbo',
        timeout: 30000,
        rateLimits: {
          requestsPerMinute: 60,
          tokensPerMinute: 90000
        },
        retry: {
          attempts: 3,
          backoffMs: 1000,
          exponential: true
        }
      },
      anthropic: {
        name: 'anthropic',
        baseUrl: 'https://api.anthropic.com/v1',
        apiKey: 'your-anthropic-api-key',
        defaultModel: 'claude-3-sonnet-20240229',
        timeout: 30000,
        rateLimits: {
          requestsPerMinute: 50,
          tokensPerMinute: 50000
        },
        retry: {
          attempts: 3,
          backoffMs: 1000,
          exponential: true
        }
      },
      google: {
        name: 'google',
        baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
        apiKey: 'your-google-api-key',
        defaultModel: 'gemini-pro',
        timeout: 30000,
        rateLimits: {
          requestsPerMinute: 60,
          tokensPerMinute: 32000
        },
        retry: {
          attempts: 3,
          backoffMs: 1000,
          exponential: true
        }
      },
      custom: {
        name: 'custom',
        baseUrl: 'https://your-api-endpoint.com',
        apiKey: 'your-api-key',
        timeout: 30000,
        options: {
          requestMapping: {
            promptField: 'prompt',
            modelField: 'model',
            maxTokensField: 'max_tokens',
            temperatureField: 'temperature'
          },
          responseMapping: {
            contentField: 'response',
            usageTokensField: 'usage.total_tokens',
            finishReasonField: 'finish_reason'
          }
        }
      },
      local: {
        name: 'local',
        baseUrl: 'http://localhost:11434',
        apiKey: '', // Not required for local models
        timeout: 60000,
        options: {
          modelType: 'ollama',
          modelName: 'llama2',
          auth: {
            type: 'none'
          }
        }
      }
    };

    return templates[provider];
  }

  /**
   * Get default configuration
   */
  private getDefaultConfig(): AIAdapterConfig {
    return {
      defaultProvider: 'openai',
      providers: {},
      global: {
        timeout: 30000,
        debug: false,
        maxConcurrentRequests: 10,
        retry: {
          attempts: 3,
          backoffMs: 1000,
          exponential: true
        }
      },
      fallback: {
        enabled: false,
        providers: [],
        triggers: ['error', 'timeout', 'rate_limit'],
        maxAttempts: 3
      },
      loadBalancing: {
        strategy: 'round_robin'
      },
      costTracking: {
        enabled: true,
        detailed: true,
        alertThresholds: [50, 75, 90, 95]
      },
      monitoring: {
        enabled: true,
        maxMetrics: 10000,
        retentionDays: 30,
        alertRules: []
      }
    };
  }

  /**
   * Merge configuration objects
   */
  private mergeConfig(updates: Partial<AIAdapterConfig>): void {
    // Simple deep merge - in production, use a proper deep merge utility
    this.config = this.deepMerge(this.config, updates);
  }

  private deepMerge(target: any, source: any): any {
    const result = { ...target };

    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(target[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }

    return result;
  }

  private toYaml(obj: any, indent: number = 0): string {
    const spaces = ' '.repeat(indent);
    let yaml = '';

    for (const [key, value] of Object.entries(obj)) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        yaml += `${spaces}${key}:\n${this.toYaml(value, indent + 2)}`;
      } else if (Array.isArray(value)) {
        yaml += `${spaces}${key}:\n`;
        for (const item of value) {
          yaml += `${spaces}  - ${item}\n`;
        }
      } else {
        yaml += `${spaces}${key}: ${value}\n`;
      }
    }

    return yaml;
  }

  private fromYaml(yaml: string): any {
    // Very basic YAML parser - use a proper library in production
    const lines = yaml.split('\n').filter(line => line.trim());
    const result: any = {};

    // This is a simplified implementation
    // In production, use a proper YAML parsing library
    for (const line of lines) {
      if (line.includes(':')) {
        const [key, value] = line.split(':').map(s => s.trim());
        if (value) {
          result[key] = value;
        }
      }
    }

    return result;
  }

  private toEnvironmentVariables(config: AIAdapterConfig): string {
    let env = '';

    // Global settings
    if (config.global.timeout) {
      env += `AI_ADAPTER_TIMEOUT=${config.global.timeout}\n`;
    }
    if (config.global.debug !== undefined) {
      env += `AI_ADAPTER_DEBUG=${config.global.debug}\n`;
    }
    if (config.defaultProvider) {
      env += `AI_ADAPTER_DEFAULT_PROVIDER=${config.defaultProvider}\n`;
    }

    // Provider configurations
    for (const [name, provider] of Object.entries(config.providers)) {
      const prefix = `AI_ADAPTER_${name.toUpperCase()}`;

      if (provider.apiKey) {
        env += `${prefix}_API_KEY=${provider.apiKey}\n`;
      }
      if (provider.baseUrl) {
        env += `${prefix}_BASE_URL=${provider.baseUrl}\n`;
      }
      if (provider.defaultModel) {
        env += `${prefix}_DEFAULT_MODEL=${provider.defaultModel}\n`;
      }
    }

    return env;
  }

  private fromEnvironmentVariables(envString: string): Partial<AIAdapterConfig> {
    const config: Partial<AIAdapterConfig> = {
      providers: {},
      global: {}
    };

    const lines = envString.split('\n').filter(line => line.trim());

    for (const line of lines) {
      if (line.includes('=')) {
        const [key, value] = line.split('=');

        if (key === 'AI_ADAPTER_TIMEOUT') {
          config.global!.timeout = parseInt(value);
        } else if (key === 'AI_ADAPTER_DEBUG') {
          config.global!.debug = value === 'true';
        } else if (key === 'AI_ADAPTER_DEFAULT_PROVIDER') {
          config.defaultProvider = value;
        } else if (key.startsWith('AI_ADAPTER_') && key.includes('_API_KEY')) {
          const provider = key.split('_')[2].toLowerCase();
          if (!config.providers![provider]) {
            config.providers![provider] = {
              name: provider,
              baseUrl: '',
              apiKey: value
            };
          } else {
            config.providers![provider].apiKey = value;
          }
        }
      }
    }

    return config;
  }
}