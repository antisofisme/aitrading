/**
 * Orchestrator for managing multiple adapters with fallback, load balancing, and retry logic
 */

import {
  AIProvider,
  AIInput,
  AIOutput,
  AdapterError,
  FallbackConfig,
  AdapterOptions,
  HealthStatus,
  UsageMetrics
} from './types.js';

export interface LoadBalancingStrategy {
  type: 'round_robin' | 'least_latency' | 'least_usage' | 'health_based' | 'random';
  weights?: Record<string, number>; // Provider weights for weighted strategies
}

export interface OrchestratorConfig {
  /** Primary adapters */
  adapters: Map<string, AIProvider>;
  /** Fallback configuration */
  fallback?: FallbackConfig;
  /** Load balancing strategy */
  loadBalancing?: LoadBalancingStrategy;
  /** Global timeout for requests */
  timeout?: number;
  /** Circuit breaker configuration */
  circuitBreaker?: {
    enabled: boolean;
    failureThreshold: number;
    resetTimeoutMs: number;
  };
  /** Enable debug logging */
  debug?: boolean;
}

interface CircuitBreakerState {
  failures: number;
  lastFailure: Date;
  state: 'closed' | 'open' | 'half-open';
}

export class AdapterOrchestrator implements AIProvider {
  public readonly name = 'orchestrator';
  public readonly config: any = {};

  private adapters: Map<string, AIProvider>;
  private fallbackConfig?: FallbackConfig;
  private loadBalancingStrategy: LoadBalancingStrategy;
  private circuitBreakers: Map<string, CircuitBreakerState> = new Map();
  private roundRobinIndex = 0;
  private timeout: number;
  private debug: boolean;

  constructor(config: OrchestratorConfig) {
    this.adapters = config.adapters;
    this.fallbackConfig = config.fallback;
    this.loadBalancingStrategy = config.loadBalancing || { type: 'round_robin' };
    this.timeout = config.timeout || 30000;
    this.debug = config.debug || false;

    // Initialize circuit breakers
    if (config.circuitBreaker?.enabled) {
      for (const providerName of this.adapters.keys()) {
        this.circuitBreakers.set(providerName, {
          failures: 0,
          lastFailure: new Date(0),
          state: 'closed'
        });
      }
    }
  }

  async predict(input: AIInput): Promise<AIOutput> {
    const startTime = Date.now();
    let lastError: AdapterError | Error;

    // Get ordered list of adapters to try
    const adapterOrder = await this.getAdapterOrder();

    for (const providerName of adapterOrder) {
      const adapter = this.adapters.get(providerName);
      if (!adapter) continue;

      // Check circuit breaker
      if (!this.isAdapterAvailable(providerName)) {
        this.log(`Skipping ${providerName} - circuit breaker open`);
        continue;
      }

      try {
        this.log(`Attempting prediction with ${providerName}`);

        const result = await this.executeWithTimeout(
          adapter.predict(input),
          this.timeout
        );

        this.recordSuccess(providerName);
        this.log(`Prediction successful with ${providerName} in ${Date.now() - startTime}ms`);

        return result;
      } catch (error) {
        lastError = error as AdapterError;
        this.recordFailure(providerName, lastError);
        this.log(`Prediction failed with ${providerName}: ${lastError.message}`);

        // Check if we should continue trying other adapters
        if (!this.shouldRetryWithFallback(lastError)) {
          throw lastError;
        }
      }
    }

    // All adapters failed
    throw lastError! || new Error('All adapters failed');
  }

  async healthCheck(): Promise<HealthStatus> {
    const startTime = Date.now();
    const healthResults: Record<string, HealthStatus> = {};

    // Check health of all adapters
    const healthPromises = Array.from(this.adapters.entries()).map(async ([name, adapter]) => {
      try {
        const health = await adapter.healthCheck();
        healthResults[name] = health;
        return { name, healthy: health.healthy };
      } catch (error) {
        healthResults[name] = {
          healthy: false,
          responseTime: 0,
          lastCheck: new Date(),
          error: error instanceof Error ? error.message : 'Unknown error'
        };
        return { name, healthy: false };
      }
    });

    const results = await Promise.all(healthPromises);
    const healthyCount = results.filter(r => r.healthy).length;
    const totalCount = results.length;

    return {
      healthy: healthyCount > 0,
      responseTime: Date.now() - startTime,
      lastCheck: new Date(),
      details: {
        provider: this.name,
        healthyAdapters: healthyCount,
        totalAdapters: totalCount,
        adapters: healthResults,
        circuitBreakers: this.getCircuitBreakerStatus()
      }
    };
  }

  getUsage(): UsageMetrics {
    // Aggregate usage from all adapters
    let totalRequests = 0;
    let totalTokens = 0;
    let totalCost = 0;
    let totalResponseTime = 0;
    let totalErrors = 0;

    const adapters = Array.from(this.adapters.values());

    for (const adapter of adapters) {
      const usage = adapter.getUsage();
      totalRequests += usage.totalRequests;
      totalTokens += usage.totalTokens;
      totalCost += usage.totalCost;
      totalResponseTime += usage.averageResponseTime * usage.totalRequests;
      totalErrors += Math.round(usage.errorRate * usage.totalRequests / 100);
    }

    const averageResponseTime = totalRequests > 0 ? totalResponseTime / totalRequests : 0;
    const errorRate = totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0;

    return {
      totalRequests,
      totalTokens,
      totalCost,
      requestsPerMinute: 0, // Not easily aggregatable
      averageResponseTime,
      errorRate,
      lastReset: new Date()
    };
  }

  getRateLimit() {
    // Return the most restrictive rate limit among all adapters
    const rateLimits = Array.from(this.adapters.values()).map(a => a.getRateLimit());

    return rateLimits.reduce((most, current) => {
      if (current.requestsPerMinute < most.requestsPerMinute) {
        return current;
      }
      return most;
    }, rateLimits[0] || {
      requestsPerMinute: Infinity,
      tokensPerMinute: Infinity,
      currentUsage: { requests: 0, tokens: 0 },
      resetTime: new Date()
    });
  }

  resetUsage(): void {
    for (const adapter of this.adapters.values()) {
      adapter.resetUsage();
    }
  }

  async validateConfig(): Promise<boolean> {
    if (this.adapters.size === 0) {
      return false;
    }

    // Validate at least one adapter
    const validationPromises = Array.from(this.adapters.values()).map(adapter =>
      adapter.validateConfig().catch(() => false)
    );

    const results = await Promise.all(validationPromises);
    return results.some(result => result);
  }

  /**
   * Add an adapter to the orchestrator
   */
  addAdapter(name: string, adapter: AIProvider): void {
    this.adapters.set(name, adapter);

    // Initialize circuit breaker if enabled
    if (this.circuitBreakers.size > 0) {
      this.circuitBreakers.set(name, {
        failures: 0,
        lastFailure: new Date(0),
        state: 'closed'
      });
    }
  }

  /**
   * Remove an adapter from the orchestrator
   */
  removeAdapter(name: string): boolean {
    const removed = this.adapters.delete(name);
    this.circuitBreakers.delete(name);
    return removed;
  }

  /**
   * Get adapter statistics
   */
  getAdapterStats(): Record<string, {
    usage: UsageMetrics;
    health: HealthStatus;
    circuitBreaker?: CircuitBreakerState
  }> {
    const stats: Record<string, any> = {};

    for (const [name, adapter] of this.adapters.entries()) {
      stats[name] = {
        usage: adapter.getUsage(),
        circuitBreaker: this.circuitBreakers.get(name)
      };
    }

    return stats;
  }

  /**
   * Get ordered list of adapters based on load balancing strategy
   */
  private async getAdapterOrder(): Promise<string[]> {
    const availableAdapters = Array.from(this.adapters.keys()).filter(name =>
      this.isAdapterAvailable(name)
    );

    if (availableAdapters.length === 0) {
      throw new Error('No adapters available');
    }

    switch (this.loadBalancingStrategy.type) {
      case 'round_robin':
        return this.roundRobinOrder(availableAdapters);

      case 'least_latency':
        return await this.leastLatencyOrder(availableAdapters);

      case 'least_usage':
        return this.leastUsageOrder(availableAdapters);

      case 'health_based':
        return await this.healthBasedOrder(availableAdapters);

      case 'random':
        return this.randomOrder(availableAdapters);

      default:
        return availableAdapters;
    }
  }

  private roundRobinOrder(adapters: string[]): string[] {
    const index = this.roundRobinIndex % adapters.length;
    this.roundRobinIndex++;

    return [
      ...adapters.slice(index),
      ...adapters.slice(0, index)
    ];
  }

  private async leastLatencyOrder(adapters: string[]): Promise<string[]> {
    const latencies = await Promise.all(
      adapters.map(async name => {
        const adapter = this.adapters.get(name)!;
        const usage = adapter.getUsage();
        return { name, latency: usage.averageResponseTime };
      })
    );

    return latencies
      .sort((a, b) => a.latency - b.latency)
      .map(item => item.name);
  }

  private leastUsageOrder(adapters: string[]): string[] {
    const usage = adapters.map(name => {
      const adapter = this.adapters.get(name)!;
      const metrics = adapter.getUsage();
      return { name, requests: metrics.totalRequests };
    });

    return usage
      .sort((a, b) => a.requests - b.requests)
      .map(item => item.name);
  }

  private async healthBasedOrder(adapters: string[]): Promise<string[]> {
    const healthScores = await Promise.all(
      adapters.map(async name => {
        const adapter = this.adapters.get(name)!;
        try {
          const health = await adapter.healthCheck();
          const score = health.healthy ? (10000 - health.responseTime) : 0;
          return { name, score };
        } catch {
          return { name, score: 0 };
        }
      })
    );

    return healthScores
      .sort((a, b) => b.score - a.score)
      .map(item => item.name);
  }

  private randomOrder(adapters: string[]): string[] {
    return [...adapters].sort(() => Math.random() - 0.5);
  }

  /**
   * Check if adapter is available (circuit breaker)
   */
  private isAdapterAvailable(name: string): boolean {
    const breaker = this.circuitBreakers.get(name);
    if (!breaker) return true;

    const now = Date.now();
    const timeSinceLastFailure = now - breaker.lastFailure.getTime();

    switch (breaker.state) {
      case 'closed':
        return true;

      case 'open':
        // Check if we should transition to half-open
        const resetTimeout = 60000; // 1 minute default
        if (timeSinceLastFailure > resetTimeout) {
          breaker.state = 'half-open';
          return true;
        }
        return false;

      case 'half-open':
        return true;

      default:
        return true;
    }
  }

  /**
   * Record successful request
   */
  private recordSuccess(name: string): void {
    const breaker = this.circuitBreakers.get(name);
    if (breaker) {
      breaker.failures = 0;
      breaker.state = 'closed';
    }
  }

  /**
   * Record failed request
   */
  private recordFailure(name: string, error: Error): void {
    const breaker = this.circuitBreakers.get(name);
    if (!breaker) return;

    breaker.failures++;
    breaker.lastFailure = new Date();

    // Check if we should open the circuit
    const threshold = 5; // Default failure threshold
    if (breaker.failures >= threshold && breaker.state !== 'open') {
      breaker.state = 'open';
      this.log(`Circuit breaker opened for ${name} after ${breaker.failures} failures`);
    }
  }

  /**
   * Check if we should retry with fallback
   */
  private shouldRetryWithFallback(error: AdapterError | Error): boolean {
    if (!this.fallbackConfig?.enabled) {
      return false;
    }

    // Check if error type triggers fallback
    if ('type' in error) {
      return this.fallbackConfig.triggers.includes(error.type as any);
    }

    // Default to retry for non-adapter errors
    return true;
  }

  /**
   * Execute operation with timeout
   */
  private async executeWithTimeout<T>(promise: Promise<T>, timeoutMs: number): Promise<T> {
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('Request timeout')), timeoutMs);
    });

    return Promise.race([promise, timeoutPromise]);
  }

  /**
   * Get circuit breaker status
   */
  private getCircuitBreakerStatus(): Record<string, CircuitBreakerState> {
    return Object.fromEntries(this.circuitBreakers.entries());
  }

  /**
   * Debug logging
   */
  private log(message: string): void {
    if (this.debug) {
      console.log(`[AdapterOrchestrator] ${message}`);
    }
  }
}