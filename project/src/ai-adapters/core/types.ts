/**
 * Core types and interfaces for AI model adapters
 */

export interface AIInput {
  /** The main prompt or input text */
  prompt: string;
  /** Optional system message */
  systemMessage?: string;
  /** Model-specific parameters */
  parameters?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    topK?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
    stop?: string[];
    [key: string]: any;
  };
  /** Conversation history for chat models */
  messages?: ChatMessage[];
  /** Stream response if supported */
  stream?: boolean;
  /** Custom headers for the request */
  customHeaders?: Record<string, string>;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  name?: string;
}

export interface AIOutput {
  /** Generated text response */
  content: string;
  /** Alternative completions if available */
  choices?: string[];
  /** Usage statistics */
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  /** Raw response from the provider */
  raw?: any;
  /** Response metadata */
  metadata?: {
    model: string;
    provider: string;
    requestId?: string;
    finishReason?: string;
    [key: string]: any;
  };
}

export interface UsageMetrics {
  /** Total requests made */
  totalRequests: number;
  /** Total tokens consumed */
  totalTokens: number;
  /** Total cost in USD */
  totalCost: number;
  /** Requests per time period */
  requestsPerMinute: number;
  /** Average response time in ms */
  averageResponseTime: number;
  /** Error rate percentage */
  errorRate: number;
  /** Last reset timestamp */
  lastReset: Date;
}

export interface HealthStatus {
  /** Overall health status */
  healthy: boolean;
  /** Response time in ms */
  responseTime: number;
  /** Last check timestamp */
  lastCheck: Date;
  /** Error message if unhealthy */
  error?: string;
  /** Additional health details */
  details?: Record<string, any>;
}

export interface RateLimitInfo {
  /** Requests per minute limit */
  requestsPerMinute: number;
  /** Tokens per minute limit */
  tokensPerMinute: number;
  /** Current usage */
  currentUsage: {
    requests: number;
    tokens: number;
  };
  /** Reset time for limits */
  resetTime: Date;
}

export interface ProviderConfig {
  /** Provider identifier */
  name: string;
  /** API endpoint URL */
  baseUrl: string;
  /** Authentication token */
  apiKey: string;
  /** Default model to use */
  defaultModel?: string;
  /** Request timeout in ms */
  timeout?: number;
  /** Rate limits */
  rateLimits?: {
    requestsPerMinute?: number;
    tokensPerMinute?: number;
  };
  /** Retry configuration */
  retry?: {
    attempts: number;
    backoffMs: number;
    exponential: boolean;
  };
  /** Custom headers */
  headers?: Record<string, string>;
  /** Provider-specific options */
  options?: Record<string, any>;
}

export interface AIProvider {
  /** Provider name */
  readonly name: string;

  /** Provider configuration */
  readonly config: ProviderConfig;

  /** Make a prediction request */
  predict(input: AIInput): Promise<AIOutput>;

  /** Stream a prediction response */
  predictStream?(input: AIInput): AsyncIterable<Partial<AIOutput>>;

  /** Check provider health */
  healthCheck(): Promise<HealthStatus>;

  /** Get usage metrics */
  getUsage(): UsageMetrics;

  /** Get rate limit information */
  getRateLimit(): RateLimitInfo;

  /** Reset usage statistics */
  resetUsage(): void;

  /** Validate configuration */
  validateConfig(): Promise<boolean>;

  /** Get available models */
  getAvailableModels?(): Promise<string[]>;
}

export interface AdapterError extends Error {
  provider: string;
  type: 'network' | 'auth' | 'rate_limit' | 'timeout' | 'validation' | 'unknown';
  retryable: boolean;
  statusCode?: number;
  originalError?: any;
}

export interface FallbackConfig {
  /** Enable fallback mechanism */
  enabled: boolean;
  /** Fallback providers in order of preference */
  providers: string[];
  /** Conditions that trigger fallback */
  triggers: ('error' | 'timeout' | 'rate_limit')[];
  /** Maximum fallback attempts */
  maxAttempts: number;
}

export interface AdapterOptions {
  /** Primary provider configuration */
  primary: ProviderConfig;
  /** Fallback configuration */
  fallback?: FallbackConfig;
  /** Global timeout for requests */
  timeout?: number;
  /** Enable debug logging */
  debug?: boolean;
  /** Custom error handler */
  errorHandler?: (error: AdapterError) => void;
}