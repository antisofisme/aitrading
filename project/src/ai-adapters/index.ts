/**
 * AI Model Adapter System - Main Entry Point
 *
 * A standardized interface for seamless AI provider integration with
 * simple URL + token configuration, automatic fallback, and comprehensive monitoring.
 */

// Core types and interfaces
export type {
  AIInput,
  AIOutput,
  AIProvider,
  ProviderConfig,
  AdapterOptions,
  AdapterError,
  UsageMetrics,
  HealthStatus,
  RateLimitInfo,
  FallbackConfig,
  ChatMessage
} from './core/types.js';

// Base adapter class
export { BaseAdapter } from './core/BaseAdapter.js';

// Provider adapters
export { OpenAIAdapter } from './providers/OpenAIAdapter.js';
export { AnthropicAdapter } from './providers/AnthropicAdapter.js';
export { GoogleAIAdapter } from './providers/GoogleAIAdapter.js';
export { CustomAPIAdapter } from './providers/CustomAPIAdapter.js';
export { LocalModelAdapter } from './providers/LocalModelAdapter.js';

// Factory and orchestration
export {
  AdapterFactory,
  createOpenAIAdapter,
  createAnthropicAdapter,
  createGoogleAIAdapter,
  createAdapterFromUrl,
  createLocalAdapter,
  type SupportedProvider
} from './core/AdapterFactory.js';

export {
  AdapterOrchestrator,
  type LoadBalancingStrategy,
  type OrchestratorConfig
} from './core/AdapterOrchestrator.js';

// Utilities
export {
  CostTracker,
  type CostBreakdown,
  type BudgetAlert,
  type CostTrackerConfig
} from './utils/CostTracker.js';

export {
  RateLimiter,
  type RateLimitConfig,
  type QuotaConfig
} from './utils/RateLimiter.js';

export {
  PerformanceMonitor,
  type PerformanceMetrics,
  type RequestMetric,
  type AlertRule,
  type PerformanceAlert
} from './utils/PerformanceMonitor.js';

// Configuration management
export {
  ConfigManager,
  FileConfigSource,
  EnvironmentConfigSource,
  type AIAdapterConfig,
  type ConfigSource
} from './config/ConfigManager.js';

/**
 * Main AIAdapter class - simplified interface for common use cases
 */
export class AIAdapter {
  private orchestrator: AdapterOrchestrator;
  private costTracker?: CostTracker;
  private performanceMonitor?: PerformanceMonitor;

  constructor(
    providers: Map<string, AIProvider> | Record<string, AIProvider>,
    options: {
      fallback?: FallbackConfig;
      loadBalancing?: LoadBalancingStrategy;
      costTracking?: boolean;
      monitoring?: boolean;
      timeout?: number;
      debug?: boolean;
    } = {}
  ) {
    const providerMap = providers instanceof Map ? providers : new Map(Object.entries(providers));

    this.orchestrator = new AdapterOrchestrator({
      adapters: providerMap,
      fallback: options.fallback,
      loadBalancing: options.loadBalancing,
      timeout: options.timeout,
      debug: options.debug
    });

    if (options.costTracking) {
      this.costTracker = new CostTracker();
    }

    if (options.monitoring) {
      this.performanceMonitor = new PerformanceMonitor();
    }
  }

  /**
   * Make a prediction request
   */
  async predict(input: AIInput): Promise<AIOutput> {
    const startTime = Date.now();

    try {
      const result = await this.orchestrator.predict(input);

      // Record metrics
      if (this.costTracker) {
        this.costTracker.recordCost(
          result.metadata?.provider || 'unknown',
          result.metadata?.model || 'unknown',
          result,
          0, // Cost calculation would be provider-specific
          result.metadata?.requestId
        );
      }

      if (this.performanceMonitor) {
        this.performanceMonitor.recordRequest(
          result.metadata?.provider || 'unknown',
          Date.now() - startTime,
          true,
          {
            input: result.usage?.promptTokens || 0,
            output: result.usage?.completionTokens || 0,
            total: result.usage?.totalTokens || 0
          },
          0 // Cost would be calculated separately
        );
      }

      return result;
    } catch (error) {
      // Record error metrics
      if (this.performanceMonitor) {
        this.performanceMonitor.recordRequest(
          'unknown',
          Date.now() - startTime,
          false,
          { input: 0, output: 0, total: 0 },
          0,
          {
            type: error instanceof Error && 'type' in error ? (error as any).type : 'unknown',
            message: error instanceof Error ? error.message : 'Unknown error'
          }
        );
      }

      throw error;
    }
  }

  /**
   * Check health of all adapters
   */
  async healthCheck(): Promise<HealthStatus> {
    return this.orchestrator.healthCheck();
  }

  /**
   * Get usage metrics
   */
  getUsage(): UsageMetrics {
    return this.orchestrator.getUsage();
  }

  /**
   * Get cost tracking information
   */
  getCostTracking() {
    return this.costTracker;
  }

  /**
   * Get performance monitoring information
   */
  getPerformanceMonitor() {
    return this.performanceMonitor;
  }

  /**
   * Get adapter orchestrator
   */
  getOrchestrator() {
    return this.orchestrator;
  }
}

/**
 * Quick setup functions for common configurations
 */

/**
 * Create a simple AI adapter with a single provider
 */
export function createSimpleAdapter(
  provider: SupportedProvider,
  apiKey: string,
  options?: {
    baseUrl?: string;
    model?: string;
    timeout?: number;
  }
): AIAdapter {
  const factory = AdapterFactory.getInstance();

  const config: ProviderConfig = {
    name: provider,
    baseUrl: options?.baseUrl || getDefaultBaseUrl(provider),
    apiKey,
    defaultModel: options?.model,
    timeout: options?.timeout
  };

  const adapter = factory.createAdapter(provider, config);
  const providers = new Map([[provider, adapter]]);

  return new AIAdapter(providers, {
    costTracking: true,
    monitoring: true
  });
}

/**
 * Create a multi-provider adapter with fallback
 */
export function createMultiProviderAdapter(
  configs: Array<{
    provider: SupportedProvider;
    apiKey: string;
    baseUrl?: string;
    model?: string;
  }>,
  options?: {
    fallbackEnabled?: boolean;
    loadBalancing?: LoadBalancingStrategy;
    costTracking?: boolean;
    monitoring?: boolean;
  }
): AIAdapter {
  const factory = AdapterFactory.getInstance();
  const providers = new Map<string, AIProvider>();

  for (const config of configs) {
    const providerConfig: ProviderConfig = {
      name: config.provider,
      baseUrl: config.baseUrl || getDefaultBaseUrl(config.provider),
      apiKey: config.apiKey,
      defaultModel: config.model
    };

    const adapter = factory.createAdapter(config.provider, providerConfig);
    providers.set(config.provider, adapter);
  }

  return new AIAdapter(providers, {
    fallback: options?.fallbackEnabled ? {
      enabled: true,
      providers: Array.from(providers.keys()),
      triggers: ['error', 'timeout', 'rate_limit'],
      maxAttempts: 3
    } : undefined,
    loadBalancing: options?.loadBalancing,
    costTracking: options?.costTracking ?? true,
    monitoring: options?.monitoring ?? true
  });
}

/**
 * Create adapter from configuration file
 */
export async function createAdapterFromConfig(
  configPath: string,
  options?: {
    costTracking?: boolean;
    monitoring?: boolean;
  }
): Promise<AIAdapter> {
  const configManager = new ConfigManager();
  configManager.addSource(new FileConfigSource(configPath));

  await configManager.load();
  const config = configManager.getConfig();

  const factory = AdapterFactory.getInstance();
  const providers = new Map<string, AIProvider>();

  for (const [name, providerConfig] of Object.entries(config.providers)) {
    const adapter = factory.createAdapter(name as SupportedProvider, providerConfig);
    providers.set(name, adapter);
  }

  return new AIAdapter(providers, {
    fallback: config.fallback,
    loadBalancing: config.loadBalancing,
    costTracking: options?.costTracking ?? config.costTracking?.enabled ?? true,
    monitoring: options?.monitoring ?? config.monitoring?.enabled ?? true
  });
}

/**
 * Get default base URL for a provider
 */
function getDefaultBaseUrl(provider: SupportedProvider): string {
  const urls: Record<SupportedProvider, string> = {
    openai: 'https://api.openai.com/v1',
    anthropic: 'https://api.anthropic.com/v1',
    google: 'https://generativelanguage.googleapis.com/v1beta',
    custom: '',
    local: 'http://localhost:11434'
  };

  return urls[provider];
}

/**
 * Export default instance for convenience
 */
export default AIAdapter;