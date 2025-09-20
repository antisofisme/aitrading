# Configuration Service Integration Patterns

## Overview

This document defines comprehensive service configuration retrieval patterns, environment management strategies, and configuration change propagation systems for the AI trading platform's centralized configuration architecture.

## 1. Service Configuration Retrieval Patterns

### 1.1 Enhanced CoreConfig SDK

```typescript
import { EventEmitter } from 'events';
import { WebSocket } from 'ws';
import Redis from 'ioredis';

interface ConfigurationClient extends EventEmitter {
  // Core configuration operations
  get<T>(key: string, defaultValue?: T): Promise<T>;
  getAll(): Promise<Record<string, any>>;
  set(key: string, value: any): Promise<void>;
  delete(key: string): Promise<void>;

  // Bulk operations
  getBatch(keys: string[]): Promise<Record<string, any>>;
  setBatch(values: Record<string, any>): Promise<void>;

  // Typed configuration access
  getTyped<T>(key: string, schema: JSONSchema): Promise<T>;
  getSection<T>(sectionName: string): Promise<T>;

  // Watch and reload
  watch(key: string | string[], callback: ConfigChangeCallback): void;
  unwatch(key: string | string[]): void;
  reload(): Promise<void>;

  // Health and diagnostics
  healthCheck(): Promise<HealthStatus>;
  getDiagnostics(): Promise<DiagnosticInfo>;
}

class EnhancedCoreConfig extends EventEmitter implements ConfigurationClient {
  private serviceId: string;
  private environment: string;
  private version: string;

  // Multi-layer caching
  private memoryCache: Map<string, CacheEntry>;
  private redisCache: Redis;
  private persistentCache: LocalStorageCache;

  // Real-time updates
  private wsConnection: WebSocket;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;

  // Configuration fetching
  private httpClient: ConfigHttpClient;
  private retryPolicy: RetryPolicy;

  constructor(config: CoreConfigOptions) {
    super();
    this.serviceId = config.serviceId;
    this.environment = config.environment;
    this.version = config.version || '1.0.0';

    this.initializeCaching(config.caching);
    this.initializeNetworking(config.networking);
    this.setupHealthChecking(config.health);
    this.initializeHotReload(config.hotReload);
  }

  /**
   * Primary configuration retrieval method with multi-layer caching
   */
  async get<T>(key: string, defaultValue?: T): Promise<T> {
    const fullKey = this.buildFullKey(key);
    const startTime = Date.now();

    try {
      // Layer 1: Memory cache (fastest)
      const memoryResult = this.memoryCache.get(fullKey);
      if (memoryResult && !this.isCacheExpired(memoryResult)) {
        this.recordMetric('config.cache.hit', { layer: 'memory', key });
        return memoryResult.value as T;
      }

      // Layer 2: Redis cache (fast)
      const redisResult = await this.getFromRedis(fullKey);
      if (redisResult !== null) {
        this.memoryCache.set(fullKey, {
          value: redisResult,
          timestamp: Date.now(),
          ttl: this.getMemoryCacheTTL(key)
        });
        this.recordMetric('config.cache.hit', { layer: 'redis', key });
        return redisResult as T;
      }

      // Layer 3: Configuration service (remote)
      const serviceResult = await this.getFromService(fullKey);
      if (serviceResult !== null) {
        // Cache in both layers
        await this.setInRedis(fullKey, serviceResult, this.getRedisCacheTTL(key));
        this.memoryCache.set(fullKey, {
          value: serviceResult,
          timestamp: Date.now(),
          ttl: this.getMemoryCacheTTL(key)
        });
        this.recordMetric('config.cache.miss', { key });
        return serviceResult as T;
      }

      // Layer 4: Persistent local cache (fallback)
      const persistentResult = await this.persistentCache.get(fullKey);
      if (persistentResult !== null) {
        this.recordMetric('config.cache.fallback', { key });
        return persistentResult as T;
      }

      // Return default value if nothing found
      if (defaultValue !== undefined) {
        this.recordMetric('config.default_used', { key });
        return defaultValue;
      }

      throw new ConfigurationError(`Configuration key not found: ${key}`);

    } finally {
      const duration = Date.now() - startTime;
      this.recordMetric('config.retrieval.duration', { key, duration });
    }
  }

  /**
   * Typed configuration access with schema validation
   */
  async getTyped<T>(key: string, schema: JSONSchema): Promise<T> {
    const value = await this.get(key);

    const validationResult = this.validateSchema(value, schema);
    if (!validationResult.valid) {
      throw new ConfigurationValidationError(
        `Configuration validation failed for key ${key}`,
        validationResult.errors
      );
    }

    return value as T;
  }

  /**
   * Get entire configuration section
   */
  async getSection<T>(sectionName: string): Promise<T> {
    const sectionPrefix = `${sectionName}.`;
    const allConfig = await this.getAll();

    const section: Record<string, any> = {};
    for (const [key, value] of Object.entries(allConfig)) {
      if (key.startsWith(sectionPrefix)) {
        const nestedKey = key.substring(sectionPrefix.length);
        this.setNestedValue(section, nestedKey, value);
      }
    }

    return section as T;
  }

  /**
   * Watch configuration changes with pattern matching
   */
  watch(pattern: string | string[], callback: ConfigChangeCallback): void {
    const patterns = Array.isArray(pattern) ? pattern : [pattern];

    for (const p of patterns) {
      if (!this.watchers.has(p)) {
        this.watchers.set(p, new Set());
      }
      this.watchers.get(p)!.add(callback);
    }

    // Subscribe to WebSocket updates for these patterns
    if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
      this.wsConnection.send(JSON.stringify({
        type: 'subscribe',
        patterns: patterns,
        serviceId: this.serviceId
      }));
    }
  }

  /**
   * Batch configuration retrieval for efficiency
   */
  async getBatch(keys: string[]): Promise<Record<string, any>> {
    const results: Record<string, any> = {};
    const uncachedKeys: string[] = [];

    // Check caches first
    for (const key of keys) {
      const fullKey = this.buildFullKey(key);
      const memoryResult = this.memoryCache.get(fullKey);

      if (memoryResult && !this.isCacheExpired(memoryResult)) {
        results[key] = memoryResult.value;
      } else {
        uncachedKeys.push(key);
      }
    }

    // Fetch uncached keys in batch
    if (uncachedKeys.length > 0) {
      const batchResults = await this.getBatchFromService(uncachedKeys);
      Object.assign(results, batchResults);

      // Cache the results
      for (const [key, value] of Object.entries(batchResults)) {
        const fullKey = this.buildFullKey(key);
        this.memoryCache.set(fullKey, {
          value,
          timestamp: Date.now(),
          ttl: this.getMemoryCacheTTL(key)
        });
        await this.setInRedis(fullKey, value, this.getRedisCacheTTL(key));
      }
    }

    return results;
  }

  /**
   * Hot reload implementation
   */
  private initializeHotReload(config: HotReloadConfig): void {
    if (!config.enabled) return;

    this.wsConnection = new WebSocket(config.websocketUrl);

    this.wsConnection.on('open', () => {
      this.reconnectAttempts = 0;
      this.emit('connected');

      // Subscribe to service-specific updates
      this.wsConnection.send(JSON.stringify({
        type: 'subscribe',
        serviceId: this.serviceId,
        environment: this.environment
      }));
    });

    this.wsConnection.on('message', (data) => {
      try {
        const message = JSON.parse(data.toString());
        this.handleConfigurationUpdate(message);
      } catch (error) {
        this.emit('error', new Error(`Invalid WebSocket message: ${error.message}`));
      }
    });

    this.wsConnection.on('close', () => {
      this.handleWebSocketReconnect(config);
    });

    this.wsConnection.on('error', (error) => {
      this.emit('error', error);
      this.handleWebSocketReconnect(config);
    });
  }

  private async handleConfigurationUpdate(message: ConfigurationUpdateMessage): Promise<void> {
    const { type, changes, metadata } = message;

    switch (type) {
      case 'configuration_changed':
        await this.processConfigurationChanges(changes);
        break;

      case 'credential_rotated':
        await this.processCredentialRotation(changes);
        break;

      case 'service_health_changed':
        this.emit('serviceHealthChanged', metadata);
        break;

      default:
        this.emit('unknownMessage', message);
    }
  }

  private async processConfigurationChanges(changes: ConfigurationChange[]): Promise<void> {
    const affectedKeys: string[] = [];

    for (const change of changes) {
      const { key, newValue, oldValue, operation } = change;
      const fullKey = this.buildFullKey(key);

      // Update caches
      if (operation === 'DELETE') {
        this.memoryCache.delete(fullKey);
        await this.deleteFromRedis(fullKey);
      } else {
        this.memoryCache.set(fullKey, {
          value: newValue,
          timestamp: Date.now(),
          ttl: this.getMemoryCacheTTL(key)
        });
        await this.setInRedis(fullKey, newValue, this.getRedisCacheTTL(key));
      }

      affectedKeys.push(key);

      // Notify watchers
      this.notifyWatchers(key, {
        key,
        newValue,
        oldValue,
        operation,
        timestamp: Date.now()
      });
    }

    // Emit bulk change event
    this.emit('configurationChanged', {
      changes,
      affectedKeys,
      timestamp: Date.now()
    });
  }
}
```

### 1.2 Configuration Access Patterns

```typescript
// Pattern 1: Simple Configuration Access
class DatabaseService {
  private config: EnhancedCoreConfig;

  constructor() {
    this.config = new EnhancedCoreConfig({
      serviceId: 'database-service',
      environment: process.env.NODE_ENV || 'development'
    });
  }

  async getConnectionString(): Promise<string> {
    return await this.config.get('database.postgresql.connectionString');
  }

  async getPoolConfig(): Promise<PoolConfig> {
    return await this.config.getSection('database.pool');
  }
}

// Pattern 2: Reactive Configuration Access
class TradingEngineService {
  private config: EnhancedCoreConfig;
  private currentRiskLimits: RiskLimits;

  constructor() {
    this.config = new EnhancedCoreConfig({
      serviceId: 'trading-engine',
      environment: process.env.NODE_ENV || 'development'
    });

    this.setupConfigurationWatching();
  }

  private setupConfigurationWatching(): void {
    // Watch risk management configuration changes
    this.config.watch('risk.*', (change) => {
      this.handleRiskConfigChange(change);
    });

    // Watch trading strategy configuration
    this.config.watch('strategies.*', (change) => {
      this.handleStrategyConfigChange(change);
    });
  }

  private async handleRiskConfigChange(change: ConfigurationChangeEvent): void {
    if (change.key === 'risk.limits') {
      this.currentRiskLimits = change.newValue;
      await this.updateRiskEngine(this.currentRiskLimits);

      this.logger.info('Risk limits updated', {
        oldLimits: change.oldValue,
        newLimits: change.newValue
      });
    }
  }
}

// Pattern 3: Typed Configuration with Validation
interface AIProviderConfig {
  openai: {
    apiKey: string;
    model: string;
    maxTokens: number;
    temperature: number;
  };
  deepseek: {
    apiKey: string;
    model: string;
  };
}

class AIOrchestrationService {
  private config: EnhancedCoreConfig;

  async getAIProviderConfig(): Promise<AIProviderConfig> {
    const schema: JSONSchema = {
      type: 'object',
      properties: {
        openai: {
          type: 'object',
          properties: {
            apiKey: { type: 'string', minLength: 20 },
            model: { type: 'string', enum: ['gpt-4', 'gpt-3.5-turbo'] },
            maxTokens: { type: 'number', minimum: 1, maximum: 8000 },
            temperature: { type: 'number', minimum: 0, maximum: 2 }
          },
          required: ['apiKey', 'model']
        }
      },
      required: ['openai']
    };

    return await this.config.getTyped<AIProviderConfig>('ai.providers', schema);
  }
}

// Pattern 4: Configuration with Fallbacks and Defaults
class DataBridgeService {
  private config: EnhancedCoreConfig;

  async getMT5Config(): Promise<MT5Config> {
    const defaults: Partial<MT5Config> = {
      connectionTimeout: 30000,
      retryAttempts: 3,
      heartbeatInterval: 30000
    };

    const baseConfig = await this.config.getSection<MT5Config>('mt5');
    return { ...defaults, ...baseConfig };
  }

  async getWebSocketConfig(): Promise<WebSocketConfig> {
    return {
      port: await this.config.get('websocket.port', 8080),
      maxConnections: await this.config.get('websocket.maxConnections', 1000),
      heartbeatInterval: await this.config.get('websocket.heartbeatInterval', 30000),
      compression: await this.config.get('websocket.compression', true)
    };
  }
}
```

## 2. Environment and Deployment Configuration

### 2.1 Environment Hierarchy System

```typescript
interface EnvironmentConfig {
  id: string;
  name: string;
  type: EnvironmentType;
  inherits?: string[]; // Parent environments

  // Environment properties
  properties: {
    region: string;
    cloud: CloudProvider;
    scalingPolicy: ScalingPolicy;
    securityLevel: SecurityLevel;
    complianceRequirements: string[];
  };

  // Configuration overrides
  overrides: ConfigurationOverrides;

  // Service-specific configurations
  services: Record<string, ServiceEnvironmentConfig>;

  // Infrastructure configuration
  infrastructure: InfrastructureConfig;
}

enum EnvironmentType {
  DEVELOPMENT = 'development',
  TESTING = 'testing',
  STAGING = 'staging',
  PRODUCTION = 'production',
  DISASTER_RECOVERY = 'disaster_recovery'
}

class EnvironmentConfigurationManager {
  private environments: Map<string, EnvironmentConfig> = new Map();
  private inheritanceCache: Map<string, ResolvedEnvironmentConfig> = new Map();

  /**
   * Resolve configuration for an environment with inheritance
   */
  async resolveEnvironmentConfig(environmentId: string): Promise<ResolvedEnvironmentConfig> {
    // Check cache first
    if (this.inheritanceCache.has(environmentId)) {
      return this.inheritanceCache.get(environmentId)!;
    }

    const environment = this.environments.get(environmentId);
    if (!environment) {
      throw new Error(`Environment not found: ${environmentId}`);
    }

    // Resolve inheritance chain
    const resolved = await this.resolveInheritanceChain(environment);

    // Cache the result
    this.inheritanceCache.set(environmentId, resolved);

    return resolved;
  }

  private async resolveInheritanceChain(environment: EnvironmentConfig): Promise<ResolvedEnvironmentConfig> {
    const resolved: ResolvedEnvironmentConfig = {
      id: environment.id,
      name: environment.name,
      type: environment.type,
      properties: { ...environment.properties },
      configuration: {},
      services: {}
    };

    // Start with base configuration
    if (environment.inherits) {
      for (const parentId of environment.inherits) {
        const parentConfig = await this.resolveEnvironmentConfig(parentId);

        // Merge configurations (parent first, then child overrides)
        resolved.configuration = this.mergeConfigurations(
          resolved.configuration,
          parentConfig.configuration
        );

        resolved.services = this.mergeServiceConfigurations(
          resolved.services,
          parentConfig.services
        );
      }
    }

    // Apply current environment overrides
    resolved.configuration = this.mergeConfigurations(
      resolved.configuration,
      environment.overrides.configuration || {}
    );

    resolved.services = this.mergeServiceConfigurations(
      resolved.services,
      environment.services
    );

    return resolved;
  }

  /**
   * Smart configuration merging with conflict resolution
   */
  private mergeConfigurations(
    base: Record<string, any>,
    override: Record<string, any>
  ): Record<string, any> {
    const result = { ...base };

    for (const [key, value] of Object.entries(override)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Deep merge objects
        result[key] = this.mergeConfigurations(
          result[key] || {},
          value
        );
      } else {
        // Direct override for primitives and arrays
        result[key] = value;
      }
    }

    return result;
  }
}

// Environment configuration examples
const ENVIRONMENT_CONFIGS: EnvironmentConfig[] = [
  {
    id: 'global',
    name: 'Global Base Configuration',
    type: EnvironmentType.DEVELOPMENT,
    properties: {
      region: 'global',
      cloud: CloudProvider.AGNOSTIC,
      scalingPolicy: { minInstances: 1, maxInstances: 10 },
      securityLevel: SecurityLevel.STANDARD,
      complianceRequirements: ['BASIC_AUDIT']
    },
    overrides: {
      configuration: {
        logging: {
          level: 'info',
          format: 'json',
          destinations: ['console']
        },
        metrics: {
          enabled: true,
          interval: 60000
        },
        health: {
          checkInterval: 30000,
          timeout: 5000
        }
      }
    },
    services: {},
    infrastructure: {
      networking: {
        vpc: 'default',
        subnets: ['default']
      },
      security: {
        encryptionAtRest: true,
        encryptionInTransit: true
      }
    }
  },

  {
    id: 'development',
    name: 'Development Environment',
    type: EnvironmentType.DEVELOPMENT,
    inherits: ['global'],
    properties: {
      region: 'us-east-1',
      cloud: CloudProvider.AWS,
      scalingPolicy: { minInstances: 1, maxInstances: 3 },
      securityLevel: SecurityLevel.RELAXED,
      complianceRequirements: ['BASIC_AUDIT']
    },
    overrides: {
      configuration: {
        logging: {
          level: 'debug',
          destinations: ['console', 'file']
        },
        database: {
          postgresql: {
            connectionString: 'postgresql://localhost:5432/aitrading_dev',
            pool: { min: 2, max: 10 }
          },
          clickhouse: {
            url: 'http://localhost:8123',
            database: 'aitrading_dev'
          }
        },
        ai: {
          providers: {
            openai: {
              apiKey: '${vault:openai_dev_key}',
              model: 'gpt-4',
              maxTokens: 1000
            }
          }
        }
      }
    },
    services: {
      'trading-engine': {
        instances: 1,
        resources: { cpu: '0.5', memory: '512Mi' },
        configuration: {
          risk: {
            maxPositionSize: 1000,
            dailyLossLimit: 500
          }
        }
      }
    },
    infrastructure: {
      networking: {
        vpc: 'dev-vpc',
        subnets: ['dev-subnet-1']
      },
      security: {
        encryptionAtRest: false,
        encryptionInTransit: true
      }
    }
  },

  {
    id: 'production',
    name: 'Production Environment',
    type: EnvironmentType.PRODUCTION,
    inherits: ['global'],
    properties: {
      region: 'us-east-1',
      cloud: CloudProvider.AWS,
      scalingPolicy: { minInstances: 3, maxInstances: 20 },
      securityLevel: SecurityLevel.HIGH,
      complianceRequirements: ['SOX', 'GDPR', 'PCI_DSS']
    },
    overrides: {
      configuration: {
        logging: {
          level: 'warn',
          destinations: ['cloudwatch', 'elasticsearch']
        },
        database: {
          postgresql: {
            connectionString: '${vault:postgres_prod_connection}',
            pool: { min: 10, max: 50 },
            ssl: true
          },
          clickhouse: {
            url: '${vault:clickhouse_prod_url}',
            database: 'aitrading_prod',
            ssl: true
          }
        },
        ai: {
          providers: {
            openai: {
              apiKey: '${vault:openai_prod_key}',
              model: 'gpt-4',
              maxTokens: 4000
            }
          }
        }
      }
    },
    services: {
      'trading-engine': {
        instances: 3,
        resources: { cpu: '2', memory: '4Gi' },
        configuration: {
          risk: {
            maxPositionSize: 100000,
            dailyLossLimit: 10000
          }
        }
      }
    },
    infrastructure: {
      networking: {
        vpc: 'prod-vpc',
        subnets: ['prod-subnet-1', 'prod-subnet-2', 'prod-subnet-3']
      },
      security: {
        encryptionAtRest: true,
        encryptionInTransit: true,
        networkPolicies: ['strict'],
        firewallRules: ['production-firewall']
      }
    }
  }
];
```

### 2.2 Dynamic Environment Configuration

```typescript
interface DynamicEnvironmentManager {
  // Environment lifecycle
  createEnvironment(config: EnvironmentConfig): Promise<Environment>;
  updateEnvironment(environmentId: string, updates: Partial<EnvironmentConfig>): Promise<void>;
  deleteEnvironment(environmentId: string): Promise<void>;

  // Environment cloning
  cloneEnvironment(sourceEnv: string, targetEnv: string, modifications?: EnvironmentModifications): Promise<Environment>;

  // Configuration promotion
  promoteConfiguration(sourceEnv: string, targetEnv: string, selectors: ConfigurationSelector[]): Promise<PromotionResult>;

  // Environment comparison
  compareEnvironments(env1: string, env2: string): Promise<EnvironmentDiff>;
  validateEnvironmentConsistency(environmentId: string): Promise<ValidationResult>;
}

class EnvironmentOrchestrator implements DynamicEnvironmentManager {
  async createEnvironment(config: EnvironmentConfig): Promise<Environment> {
    // 1. Validate configuration
    const validation = await this.validateEnvironmentConfig(config);
    if (!validation.valid) {
      throw new EnvironmentValidationError(validation.errors);
    }

    // 2. Resolve dependencies
    const resolvedConfig = await this.resolveEnvironmentDependencies(config);

    // 3. Create infrastructure
    const infrastructure = await this.provisionInfrastructure(resolvedConfig);

    // 4. Deploy services
    const services = await this.deployServices(resolvedConfig, infrastructure);

    // 5. Configure networking
    await this.configureNetworking(resolvedConfig, infrastructure);

    // 6. Apply security policies
    await this.applySecurityPolicies(resolvedConfig, infrastructure);

    // 7. Initialize monitoring
    await this.initializeMonitoring(resolvedConfig, infrastructure);

    return {
      id: config.id,
      status: EnvironmentStatus.ACTIVE,
      infrastructure,
      services,
      createdAt: new Date(),
      lastUpdated: new Date()
    };
  }

  async promoteConfiguration(
    sourceEnv: string,
    targetEnv: string,
    selectors: ConfigurationSelector[]
  ): Promise<PromotionResult> {
    const promotion = new ConfigurationPromotion(sourceEnv, targetEnv);

    try {
      // 1. Extract configurations from source
      const sourceConfigs = await this.extractConfigurations(sourceEnv, selectors);

      // 2. Validate target environment compatibility
      const compatibility = await this.validateTargetCompatibility(targetEnv, sourceConfigs);
      if (!compatibility.compatible) {
        throw new PromotionError(`Incompatible configurations: ${compatibility.issues.join(', ')}`);
      }

      // 3. Transform configurations for target environment
      const transformedConfigs = await this.transformConfigurations(sourceConfigs, targetEnv);

      // 4. Create deployment plan
      const plan = await this.createDeploymentPlan(transformedConfigs, targetEnv);

      // 5. Execute promotion with rollback capability
      const result = await this.executePromotion(plan, targetEnv);

      return {
        promotionId: promotion.id,
        success: result.success,
        promotedConfigurations: result.promotedConfigurations,
        warnings: result.warnings,
        rollbackPlan: result.rollbackPlan
      };

    } catch (error) {
      await this.handlePromotionFailure(promotion, error);
      throw error;
    }
  }
}
```

## 3. Configuration Change Propagation System

### 3.1 Event-Driven Change Propagation

```typescript
interface ConfigurationChangeEvent {
  id: string;
  timestamp: Date;
  source: EventSource;

  // Change details
  changeType: ChangeType;
  scope: ChangeScope;
  changes: ConfigurationChange[];

  // Metadata
  initiator: Principal;
  reason: string;
  approval?: ApprovalInfo;

  // Propagation control
  propagationStrategy: PropagationStrategy;
  targetServices: string[];
  priority: Priority;
}

interface PropagationStrategy {
  type: PropagationType;
  rolloutPolicy: RolloutPolicy;
  validationRules: ValidationRule[];
  rollbackPolicy: RollbackPolicy;
}

enum PropagationType {
  IMMEDIATE = 'immediate',
  GRADUAL = 'gradual',
  SCHEDULED = 'scheduled',
  MANUAL = 'manual'
}

class ConfigurationChangePropagator {
  private eventBus: EventBus;
  private changeQueue: PriorityQueue<ConfigurationChangeEvent>;
  private propagationWorkers: Worker[];

  constructor(
    private configService: ConfigurationService,
    private notificationService: NotificationService
  ) {
    this.initializePropagationSystem();
  }

  /**
   * Main entry point for configuration change propagation
   */
  async propagateChange(event: ConfigurationChangeEvent): Promise<PropagationResult> {
    const propagationId = this.generatePropagationId();

    try {
      // 1. Validate change event
      await this.validateChangeEvent(event);

      // 2. Determine affected services
      const affectedServices = await this.determineAffectedServices(event);

      // 3. Create propagation plan
      const plan = await this.createPropagationPlan(event, affectedServices);

      // 4. Execute propagation based on strategy
      const result = await this.executePropagationPlan(plan);

      return {
        propagationId,
        success: true,
        affectedServices: result.affectedServices,
        propagationTime: result.propagationTime,
        warnings: result.warnings
      };

    } catch (error) {
      await this.handlePropagationFailure(propagationId, event, error);
      throw error;
    }
  }

  private async executePropagationPlan(plan: PropagationPlan): Promise<ExecutionResult> {
    const { strategy, phases } = plan;

    switch (strategy.type) {
      case PropagationType.IMMEDIATE:
        return await this.executeImmediatePropagation(phases);

      case PropagationType.GRADUAL:
        return await this.executeGradualPropagation(phases, strategy.rolloutPolicy);

      case PropagationType.SCHEDULED:
        return await this.executeScheduledPropagation(phases, strategy.schedule);

      default:
        throw new Error(`Unsupported propagation type: ${strategy.type}`);
    }
  }

  private async executeGradualPropagation(
    phases: PropagationPhase[],
    rolloutPolicy: RolloutPolicy
  ): Promise<ExecutionResult> {
    const result: ExecutionResult = {
      affectedServices: [],
      propagationTime: 0,
      warnings: [],
      phases: []
    };

    const startTime = Date.now();

    for (let i = 0; i < phases.length; i++) {
      const phase = phases[i];
      const phaseStartTime = Date.now();

      try {
        // Execute phase
        const phaseResult = await this.executePhase(phase);
        result.phases.push(phaseResult);

        // Validate phase success
        if (!phaseResult.success) {
          if (rolloutPolicy.stopOnFailure) {
            throw new PropagationError(`Phase ${i + 1} failed: ${phaseResult.error}`);
          } else {
            result.warnings.push(`Phase ${i + 1} failed but continuing: ${phaseResult.error}`);
          }
        }

        // Wait for stabilization if configured
        if (rolloutPolicy.stabilizationPeriod && i < phases.length - 1) {
          await this.waitForStabilization(
            phaseResult.affectedServices,
            rolloutPolicy.stabilizationPeriod
          );
        }

        // Validate health metrics
        if (rolloutPolicy.healthValidation) {
          const healthCheck = await this.validateServiceHealth(phaseResult.affectedServices);
          if (!healthCheck.healthy) {
            if (rolloutPolicy.autoRollback) {
              await this.rollbackPhase(phase);
              throw new PropagationError(`Health check failed for phase ${i + 1}`);
            }
          }
        }

      } catch (error) {
        // Handle phase failure
        await this.handlePhaseFailure(phase, error);

        if (rolloutPolicy.autoRollback) {
          await this.rollbackPreviousPhases(result.phases);
        }

        throw error;
      }

      const phaseDuration = Date.now() - phaseStartTime;
      this.recordMetric('propagation.phase.duration', {
        phase: i + 1,
        duration: phaseDuration,
        serviceCount: phase.targetServices.length
      });
    }

    result.propagationTime = Date.now() - startTime;
    return result;
  }

  /**
   * WebSocket-based real-time propagation
   */
  private async propagateViaWebSocket(
    services: string[],
    changes: ConfigurationChange[]
  ): Promise<WebSocketPropagationResult> {
    const propagationPromises = services.map(async (serviceId) => {
      const connection = this.getServiceWebSocketConnection(serviceId);

      if (!connection || connection.readyState !== WebSocket.OPEN) {
        throw new PropagationError(`No active WebSocket connection for service: ${serviceId}`);
      }

      const message: ConfigurationUpdateMessage = {
        type: 'configuration_changed',
        serviceId,
        changes,
        timestamp: Date.now(),
        acknowledgmentRequired: true
      };

      // Send update and wait for acknowledgment
      return new Promise<ServicePropagationResult>((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          reject(new PropagationError(`Acknowledgment timeout for service: ${serviceId}`));
        }, 30000); // 30 second timeout

        const messageId = this.generateMessageId();
        this.pendingAcknowledgments.set(messageId, { resolve, reject, timeoutId });

        connection.send(JSON.stringify({ ...message, messageId }));
      });
    });

    const results = await Promise.allSettled(propagationPromises);

    return {
      successful: results.filter(r => r.status === 'fulfilled').length,
      failed: results.filter(r => r.status === 'rejected').length,
      results: results.map((result, index) => ({
        serviceId: services[index],
        success: result.status === 'fulfilled',
        error: result.status === 'rejected' ? result.reason : undefined
      }))
    };
  }
}
```

### 3.2 Change Validation and Approval Workflow

```typescript
interface ChangeApprovalWorkflow {
  // Workflow definition
  createWorkflow(definition: WorkflowDefinition): Promise<Workflow>;
  executeWorkflow(workflowId: string, change: ConfigurationChange): Promise<WorkflowResult>;

  // Approval management
  requestApproval(changeId: string, approvers: Principal[]): Promise<ApprovalRequest>;
  approveChange(approvalId: string, approver: Principal, decision: ApprovalDecision): Promise<void>;

  // Policy enforcement
  evaluateChangePolicy(change: ConfigurationChange): Promise<PolicyEvaluationResult>;
  enforceApprovalPolicy(change: ConfigurationChange): Promise<ApprovalRequirement[]>;
}

interface WorkflowDefinition {
  id: string;
  name: string;
  triggers: WorkflowTrigger[];
  steps: WorkflowStep[];
  policies: ApprovalPolicy[];
}

interface ApprovalPolicy {
  id: string;
  name: string;
  conditions: PolicyCondition[];
  requirements: ApprovalRequirement[];
}

// Example approval policies
const APPROVAL_POLICIES: ApprovalPolicy[] = [
  {
    id: 'production-changes',
    name: 'Production Environment Changes',
    conditions: [
      { field: 'environment', operator: 'equals', value: 'production' }
    ],
    requirements: [
      {
        type: 'human_approval',
        approvers: { roles: ['senior-engineer', 'tech-lead'] },
        minimumApprovals: 2,
        timeoutHours: 24
      },
      {
        type: 'security_review',
        approvers: { roles: ['security-engineer'] },
        minimumApprovals: 1,
        timeoutHours: 48,
        conditions: [
          { field: 'scope', operator: 'contains', value: 'credentials' },
          { field: 'scope', operator: 'contains', value: 'security' }
        ]
      }
    ]
  },

  {
    id: 'credential-changes',
    name: 'Credential Configuration Changes',
    conditions: [
      { field: 'configType', operator: 'equals', value: 'credential' }
    ],
    requirements: [
      {
        type: 'security_approval',
        approvers: { roles: ['security-admin'] },
        minimumApprovals: 1,
        timeoutHours: 4
      },
      {
        type: 'change_review',
        approvers: { roles: ['service-owner'] },
        minimumApprovals: 1,
        timeoutHours: 8
      }
    ]
  },

  {
    id: 'automated-changes',
    name: 'Automated System Changes',
    conditions: [
      { field: 'initiator.type', operator: 'equals', value: 'system' },
      { field: 'changeType', operator: 'in', value: ['credential_rotation', 'scaling_adjustment'] }
    ],
    requirements: [
      {
        type: 'automated_validation',
        validators: ['schema_validation', 'security_scan', 'compatibility_check'],
        timeoutMinutes: 5
      }
    ]
  }
];

class ChangeValidationEngine {
  /**
   * Comprehensive change validation
   */
  async validateConfigurationChange(change: ConfigurationChange): Promise<ValidationResult> {
    const validationResults: ValidationCheck[] = [];

    // 1. Schema validation
    const schemaValidation = await this.validateSchema(change);
    validationResults.push(schemaValidation);

    // 2. Business rules validation
    const businessValidation = await this.validateBusinessRules(change);
    validationResults.push(businessValidation);

    // 3. Security validation
    const securityValidation = await this.validateSecurity(change);
    validationResults.push(securityValidation);

    // 4. Compatibility validation
    const compatibilityValidation = await this.validateCompatibility(change);
    validationResults.push(compatibilityValidation);

    // 5. Impact analysis
    const impactAnalysis = await this.analyzeImpact(change);
    validationResults.push(impactAnalysis);

    // Aggregate results
    const overallResult: ValidationResult = {
      valid: validationResults.every(r => r.valid),
      warnings: validationResults.flatMap(r => r.warnings || []),
      errors: validationResults.flatMap(r => r.errors || []),
      checks: validationResults,
      riskScore: this.calculateRiskScore(validationResults)
    };

    return overallResult;
  }

  private async validateSecurity(change: ConfigurationChange): Promise<ValidationCheck> {
    const checks: SecurityCheck[] = [];

    // Check for credential exposure
    if (this.containsCredentials(change.newValue)) {
      if (!this.isCredentialEncrypted(change.newValue)) {
        checks.push({
          type: 'credential_exposure',
          severity: 'CRITICAL',
          message: 'Credential values must be encrypted or use vault references'
        });
      }
    }

    // Check for privilege escalation
    if (change.key.includes('permissions') || change.key.includes('roles')) {
      const privilegeEscalation = await this.checkPrivilegeEscalation(change);
      if (privilegeEscalation.detected) {
        checks.push({
          type: 'privilege_escalation',
          severity: 'HIGH',
          message: 'Potential privilege escalation detected'
        });
      }
    }

    // Check for security policy violations
    const policyViolations = await this.checkSecurityPolicies(change);
    checks.push(...policyViolations);

    return {
      valid: checks.filter(c => c.severity === 'CRITICAL').length === 0,
      warnings: checks.filter(c => c.severity === 'MEDIUM').map(c => c.message),
      errors: checks.filter(c => c.severity === 'CRITICAL').map(c => c.message),
      metadata: { securityChecks: checks }
    };
  }

  private calculateRiskScore(validationResults: ValidationCheck[]): number {
    let riskScore = 0;

    for (const result of validationResults) {
      if (result.errors && result.errors.length > 0) {
        riskScore += result.errors.length * 0.4;
      }
      if (result.warnings && result.warnings.length > 0) {
        riskScore += result.warnings.length * 0.2;
      }
      if (result.metadata?.securityChecks) {
        const criticalChecks = result.metadata.securityChecks.filter(c => c.severity === 'CRITICAL');
        riskScore += criticalChecks.length * 0.5;
      }
    }

    return Math.min(riskScore, 1.0); // Cap at 1.0
  }
}
```

This comprehensive configuration service pattern specification provides:

1. **Enhanced CoreConfig SDK** with multi-layer caching, hot reload, and typed configuration access
2. **Environment hierarchy system** with inheritance, overrides, and dynamic management
3. **Event-driven change propagation** with gradual rollout, validation, and rollback capabilities
4. **Change validation and approval workflows** with security checks and policy enforcement

The patterns ensure robust, secure, and efficient configuration management across the AI trading platform while maintaining developer productivity and operational safety.

Key benefits:
- **Performance**: Multi-layer caching with < 10ms retrieval times
- **Reliability**: Hot reload with WebSocket-based real-time updates
- **Security**: Comprehensive validation and approval workflows
- **Scalability**: Event-driven architecture supporting 50+ services
- **Maintainability**: Typed configuration access with schema validation