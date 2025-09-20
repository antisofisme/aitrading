# Configuration Management Migration Strategy

## Overview

This document outlines a comprehensive migration strategy to transition the AI trading platform from its current distributed configuration approach to the new centralized configuration management system. The strategy emphasizes minimal risk, zero downtime, and gradual adoption.

## Current State Assessment

### Existing Configuration Landscape

```typescript
// Current per-service configuration pattern
class CurrentCoreConfig {
  constructor(serviceName: string) {
    this.serviceName = serviceName;
    this.environment = process.env.NODE_ENV || 'development';
    this.loadEnvironmentVariables();
  }

  private loadEnvironmentVariables(): void {
    // Direct environment variable access
    this.config = {
      database: {
        postgresql: process.env.POSTGRES_CONNECTION_STRING,
        clickhouse: process.env.CLICKHOUSE_URL
      },
      ai: {
        openai: {
          apiKey: process.env.OPENAI_API_KEY,
          model: process.env.OPENAI_MODEL || 'gpt-4'
        }
      },
      service: {
        port: parseInt(process.env.SERVICE_PORT || '8000'),
        host: process.env.SERVICE_HOST || '0.0.0.0'
      }
    };
  }

  get(key: string, defaultValue?: any): any {
    return this.getNestedValue(this.config, key) || defaultValue;
  }
}
```

### Current Pain Points

1. **Configuration Sprawl**: 11 services each managing configuration independently
2. **Environment Variable Explosion**: 100+ environment variables across services
3. **Security Vulnerabilities**: Credentials stored in plain text
4. **Inconsistent Patterns**: Different configuration access patterns per service
5. **Deployment Complexity**: Docker Compose files with extensive environment sections
6. **Change Management**: No centralized way to update configurations
7. **Audit Gaps**: Limited visibility into configuration changes

### Current Service Configuration Inventory

```yaml
services:
  api-gateway:
    environment_variables: 15
    configuration_files: 2
    credential_count: 5
    migration_complexity: LOW

  data-bridge:
    environment_variables: 22
    configuration_files: 3
    credential_count: 8
    migration_complexity: HIGH  # Real-time WebSocket dependencies

  ai-orchestration:
    environment_variables: 18
    configuration_files: 4
    credential_count: 12
    migration_complexity: MEDIUM

  trading-engine:
    environment_variables: 25
    configuration_files: 5
    credential_count: 15
    migration_complexity: CRITICAL  # Core business logic

  database-service:
    environment_variables: 20
    configuration_files: 6
    credential_count: 20
    migration_complexity: HIGH  # Foundation service

  # ... other services
```

## Migration Strategy Overview

### Phased Migration Approach

```
Phase 1: Foundation (Weeks 1-2)
├── Deploy Configuration Management Service
├── Set up credential vault
├── Create migration tooling
└── Validate in development environment

Phase 2: Pilot Services (Weeks 3-4)
├── Migrate database-service (foundation)
├── Migrate api-gateway (entry point)
├── Validate dual-mode operation
└── Performance testing

Phase 3: Core Services (Weeks 5-8)
├── Migrate ai-orchestration
├── Migrate user-service
├── Migrate performance-analytics
└── Monitor and optimize

Phase 4: Critical Services (Weeks 9-12)
├── Migrate trading-engine (highest risk)
├── Migrate data-bridge (real-time)
├── Complete remaining services
└── Legacy cleanup

Phase 5: Optimization (Weeks 13-16)
├── Remove legacy configuration patterns
├── Optimize performance
├── Enhanced security features
└── Documentation and training
```

## Phase 1: Foundation Setup

### 1.1 Configuration Management Service Deployment

```dockerfile
# Dockerfile for Configuration Management Service
FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8011/health || exit 1

EXPOSE 8011

CMD ["npm", "start"]
```

```yaml
# docker-compose.yml addition
services:
  config-service:
    build:
      context: ./config-management-service
      dockerfile: Dockerfile
    ports:
      - "8011:8011"
    environment:
      - NODE_ENV=${NODE_ENV:-development}
      - DATABASE_URL=${CONFIG_DB_URL}
      - REDIS_URL=${CONFIG_REDIS_URL}
      - VAULT_URL=${VAULT_URL}
    volumes:
      - config-data:/app/data
    depends_on:
      - postgres
      - redis
    networks:
      - aitrading-network
    restart: unless-stopped

volumes:
  config-data:
```

### 1.2 Backwards Compatible Configuration SDK

```typescript
class MigrationCompatibleConfig extends EnhancedCoreConfig {
  private legacyConfig: CurrentCoreConfig;
  private migrationMode: MigrationMode;
  private migrationFlags: MigrationFlags;

  constructor(serviceId: string, options: MigrationConfigOptions = {}) {
    super(serviceId, options.environment || 'development');

    // Initialize legacy configuration for fallback
    this.legacyConfig = new CurrentCoreConfig(serviceId);

    // Determine migration mode
    this.migrationMode = this.determineMigrationMode(options);
    this.migrationFlags = this.loadMigrationFlags();

    this.setupMigrationLogging();
  }

  /**
   * Backwards compatible get method with automatic fallback
   */
  async get<T>(key: string, defaultValue?: T): Promise<T> {
    const migrationKey = `${this.serviceId}.${key}`;

    try {
      // Check if this key is migrated
      if (this.migrationFlags.isKeyMigrated(migrationKey)) {
        // Use new configuration system
        return await super.get(key, defaultValue);
      }

      // Check migration mode
      switch (this.migrationMode) {
        case MigrationMode.NEW_ONLY:
          return await super.get(key, defaultValue);

        case MigrationMode.LEGACY_ONLY:
          return this.legacyConfig.get(key, defaultValue);

        case MigrationMode.NEW_WITH_FALLBACK:
          try {
            const newValue = await super.get(key);
            this.recordMigrationMetric('config.new_system.success', { key });
            return newValue;
          } catch (error) {
            this.recordMigrationMetric('config.new_system.fallback', { key, error: error.message });
            return this.legacyConfig.get(key, defaultValue);
          }

        case MigrationMode.LEGACY_WITH_VALIDATION:
          const legacyValue = this.legacyConfig.get(key, defaultValue);

          try {
            const newValue = await super.get(key);

            // Compare values and log discrepancies
            if (!this.valuesEqual(legacyValue, newValue)) {
              this.recordMigrationMetric('config.value_discrepancy', {
                key,
                legacyValue: this.sanitizeForLogging(legacyValue),
                newValue: this.sanitizeForLogging(newValue)
              });
            }
          } catch (error) {
            this.recordMigrationMetric('config.validation_error', { key, error: error.message });
          }

          return legacyValue;

        default:
          throw new Error(`Unknown migration mode: ${this.migrationMode}`);
      }

    } catch (error) {
      this.recordMigrationMetric('config.migration_error', {
        key,
        mode: this.migrationMode,
        error: error.message
      });

      // Always fall back to legacy in case of unexpected errors
      return this.legacyConfig.get(key, defaultValue);
    }
  }

  /**
   * Migration-aware batch operations
   */
  async getBatch(keys: string[]): Promise<Record<string, any>> {
    const results: Record<string, any> = {};
    const migratedKeys: string[] = [];
    const legacyKeys: string[] = [];

    // Categorize keys based on migration status
    for (const key of keys) {
      const migrationKey = `${this.serviceId}.${key}`;
      if (this.migrationFlags.isKeyMigrated(migrationKey)) {
        migratedKeys.push(key);
      } else {
        legacyKeys.push(key);
      }
    }

    // Fetch from new system
    if (migratedKeys.length > 0) {
      try {
        const newResults = await super.getBatch(migratedKeys);
        Object.assign(results, newResults);
      } catch (error) {
        this.recordMigrationMetric('config.batch_new_system.error', {
          keyCount: migratedKeys.length,
          error: error.message
        });

        // Fall back to legacy for failed keys
        for (const key of migratedKeys) {
          results[key] = this.legacyConfig.get(key);
        }
      }
    }

    // Fetch from legacy system
    for (const key of legacyKeys) {
      results[key] = this.legacyConfig.get(key);
    }

    return results;
  }

  /**
   * Migration control methods
   */
  async enableNewSystemForKey(key: string): Promise<void> {
    const migrationKey = `${this.serviceId}.${key}`;
    await this.migrationFlags.markKeyAsMigrated(migrationKey);

    this.recordMigrationMetric('config.key_migrated', {
      key: migrationKey,
      timestamp: new Date().toISOString()
    });
  }

  async rollbackKeyToLegacy(key: string): Promise<void> {
    const migrationKey = `${this.serviceId}.${key}`;
    await this.migrationFlags.markKeyAsLegacy(migrationKey);

    this.recordMigrationMetric('config.key_rolled_back', {
      key: migrationKey,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Migration validation
   */
  async validateMigration(): Promise<MigrationValidationResult> {
    const allKeys = this.getAllConfigurationKeys();
    const validationResults: KeyValidationResult[] = [];

    for (const key of allKeys) {
      try {
        const legacyValue = this.legacyConfig.get(key);
        const newValue = await super.get(key);

        const isEqual = this.valuesEqual(legacyValue, newValue);
        validationResults.push({
          key,
          legacyValue: this.sanitizeForLogging(legacyValue),
          newValue: this.sanitizeForLogging(newValue),
          isEqual,
          status: isEqual ? 'MATCH' : 'MISMATCH'
        });

      } catch (error) {
        validationResults.push({
          key,
          status: 'ERROR',
          error: error.message
        });
      }
    }

    return {
      serviceId: this.serviceId,
      totalKeys: allKeys.length,
      matches: validationResults.filter(r => r.status === 'MATCH').length,
      mismatches: validationResults.filter(r => r.status === 'MISMATCH').length,
      errors: validationResults.filter(r => r.status === 'ERROR').length,
      details: validationResults
    };
  }
}

enum MigrationMode {
  LEGACY_ONLY = 'legacy_only',
  NEW_ONLY = 'new_only',
  NEW_WITH_FALLBACK = 'new_with_fallback',
  LEGACY_WITH_VALIDATION = 'legacy_with_validation'
}
```

### 1.3 Migration Tooling

```typescript
class ConfigurationMigrationTool {
  private sourceConfig: CurrentCoreConfig;
  private targetConfig: EnhancedCoreConfig;
  private migrationRules: MigrationRule[];

  /**
   * Automated configuration extraction and migration
   */
  async migrateServiceConfiguration(serviceId: string): Promise<MigrationResult> {
    const migration = new ServiceMigration(serviceId);

    try {
      // 1. Extract current configuration
      const currentConfig = await this.extractCurrentConfiguration(serviceId);

      // 2. Transform configuration for new system
      const transformedConfig = await this.transformConfiguration(currentConfig, serviceId);

      // 3. Validate transformed configuration
      const validation = await this.validateTransformedConfiguration(transformedConfig);
      if (!validation.valid) {
        throw new MigrationError(`Configuration validation failed: ${validation.errors.join(', ')}`);
      }

      // 4. Create migration plan
      const plan = await this.createMigrationPlan(serviceId, transformedConfig);

      // 5. Execute migration with rollback capability
      const result = await this.executeMigrationPlan(plan);

      return {
        migrationId: migration.id,
        serviceId,
        success: true,
        migratedKeys: result.migratedKeys,
        warnings: result.warnings,
        rollbackPlan: result.rollbackPlan
      };

    } catch (error) {
      await this.handleMigrationFailure(migration, error);
      throw error;
    }
  }

  private async extractCurrentConfiguration(serviceId: string): Promise<ExtractedConfiguration> {
    const extraction: ExtractedConfiguration = {
      serviceId,
      environmentVariables: new Map(),
      configurationFiles: new Map(),
      hardcodedValues: new Map(),
      credentials: new Map()
    };

    // Extract environment variables
    const envVars = await this.getServiceEnvironmentVariables(serviceId);
    for (const [key, value] of envVars) {
      if (this.isCredential(key, value)) {
        extraction.credentials.set(key, value);
      } else {
        extraction.environmentVariables.set(key, value);
      }
    }

    // Extract configuration files
    const configFiles = await this.getServiceConfigurationFiles(serviceId);
    for (const [file, content] of configFiles) {
      extraction.configurationFiles.set(file, this.parseConfigurationFile(content));
    }

    // Scan for hardcoded values
    const hardcodedValues = await this.scanForHardcodedConfiguration(serviceId);
    for (const [key, value] of hardcodedValues) {
      extraction.hardcodedValues.set(key, value);
    }

    return extraction;
  }

  private async transformConfiguration(
    extracted: ExtractedConfiguration,
    serviceId: string
  ): Promise<TransformedConfiguration> {
    const transformed: TransformedConfiguration = {
      serviceId,
      configuration: {},
      credentials: {},
      migrations: []
    };

    // Apply transformation rules
    for (const rule of this.migrationRules) {
      if (rule.appliesToService(serviceId)) {
        const ruleResult = await rule.transform(extracted);
        this.mergeTransformationResults(transformed, ruleResult);
      }
    }

    // Handle environment-specific transformations
    const environmentTransforms = await this.getEnvironmentTransforms(serviceId);
    for (const [env, transform] of environmentTransforms) {
      const envResult = await transform.apply(extracted);
      transformed.configuration[env] = envResult.configuration;
    }

    return transformed;
  }
}

// Migration rules for different configuration patterns
const MIGRATION_RULES: MigrationRule[] = [
  {
    name: 'Database Configuration Migration',
    description: 'Migrate database connection strings and pool settings',
    appliesToService: (serviceId) => ['database-service', 'trading-engine', 'ai-orchestration'].includes(serviceId),
    transform: async (extracted) => {
      const result: TransformationResult = {
        configuration: {},
        credentials: {},
        migrations: []
      };

      // Transform PostgreSQL configuration
      const pgConnectionString = extracted.environmentVariables.get('POSTGRES_CONNECTION_STRING');
      if (pgConnectionString) {
        result.credentials['database.postgresql.connectionString'] = pgConnectionString;
        result.migrations.push({
          from: 'POSTGRES_CONNECTION_STRING',
          to: 'database.postgresql.connectionString',
          type: 'credential'
        });
      }

      // Transform pool settings
      const poolMin = extracted.environmentVariables.get('POSTGRES_POOL_MIN');
      const poolMax = extracted.environmentVariables.get('POSTGRES_POOL_MAX');
      if (poolMin || poolMax) {
        result.configuration['database.pool'] = {
          min: poolMin ? parseInt(poolMin) : 5,
          max: poolMax ? parseInt(poolMax) : 20
        };
      }

      return result;
    }
  },

  {
    name: 'AI Provider Configuration Migration',
    description: 'Migrate AI provider API keys and model configurations',
    appliesToService: (serviceId) => ['ai-orchestration', 'ai-provider'].includes(serviceId),
    transform: async (extracted) => {
      const result: TransformationResult = {
        configuration: {},
        credentials: {},
        migrations: []
      };

      // OpenAI configuration
      const openaiKey = extracted.environmentVariables.get('OPENAI_API_KEY');
      if (openaiKey) {
        result.credentials['ai.providers.openai.apiKey'] = openaiKey;
        result.migrations.push({
          from: 'OPENAI_API_KEY',
          to: 'ai.providers.openai.apiKey',
          type: 'credential'
        });
      }

      const openaiModel = extracted.environmentVariables.get('OPENAI_MODEL');
      if (openaiModel) {
        result.configuration['ai.providers.openai.model'] = openaiModel;
      }

      // DeepSeek configuration
      const deepseekKey = extracted.environmentVariables.get('DEEPSEEK_API_KEY');
      if (deepseekKey) {
        result.credentials['ai.providers.deepseek.apiKey'] = deepseekKey;
      }

      return result;
    }
  },

  {
    name: 'Service Port Configuration Migration',
    description: 'Migrate service port and networking configurations',
    appliesToService: () => true, // Applies to all services
    transform: async (extracted) => {
      const result: TransformationResult = {
        configuration: {},
        credentials: {},
        migrations: []
      };

      const servicePort = extracted.environmentVariables.get('SERVICE_PORT');
      if (servicePort) {
        result.configuration['service.port'] = parseInt(servicePort);
        result.migrations.push({
          from: 'SERVICE_PORT',
          to: 'service.port',
          type: 'configuration'
        });
      }

      const serviceHost = extracted.environmentVariables.get('SERVICE_HOST');
      if (serviceHost) {
        result.configuration['service.host'] = serviceHost;
      }

      return result;
    }
  }
];
```

## Phase 2: Pilot Service Migration

### 2.1 Database Service Migration (Foundation Service)

```typescript
// Before: Legacy configuration
class DatabaseService {
  private config: CurrentCoreConfig;

  constructor() {
    this.config = new CurrentCoreConfig('database-service');
  }

  async getPostgreSQLConnection(): Promise<Pool> {
    const connectionString = this.config.get('database.postgresql.connectionString');
    const poolConfig = {
      min: this.config.get('database.pool.min', 5),
      max: this.config.get('database.pool.max', 20)
    };

    return new Pool({
      connectionString,
      ...poolConfig
    });
  }
}

// After: Migrated configuration with backwards compatibility
class DatabaseService {
  private config: MigrationCompatibleConfig;

  constructor() {
    this.config = new MigrationCompatibleConfig('database-service', {
      environment: process.env.NODE_ENV,
      migrationMode: process.env.CONFIG_MIGRATION_MODE as MigrationMode || MigrationMode.NEW_WITH_FALLBACK
    });
  }

  async getPostgreSQLConnection(): Promise<Pool> {
    // New configuration system with automatic fallback
    const connectionString = await this.config.get('database.postgresql.connectionString');
    const poolConfig = await this.config.getSection<PoolConfig>('database.pool');

    return new Pool({
      connectionString,
      ...poolConfig
    });
  }

  // Migration validation endpoint
  async validateMigration(): Promise<MigrationValidationResult> {
    return await this.config.validateMigration();
  }

  // Progressive migration control
  async enableNewConfigurationForKeys(keys: string[]): Promise<void> {
    for (const key of keys) {
      await this.config.enableNewSystemForKey(key);
    }
  }
}
```

### 2.2 Gradual Key Migration Strategy

```typescript
class GradualMigrationController {
  private readonly services: MigrationCompatibleConfig[] = [];
  private readonly migrationSchedule: MigrationSchedule;

  /**
   * Progressive key migration with monitoring
   */
  async migrateKeysGradually(serviceId: string, keys: string[]): Promise<void> {
    const service = this.getServiceConfig(serviceId);

    for (const key of keys) {
      try {
        // 1. Validate key works in new system
        await this.validateKeyInNewSystem(service, key);

        // 2. Enable canary mode (small percentage of requests)
        await this.enableCanaryMode(service, key, 0.1); // 10% of requests

        // 3. Monitor for issues
        await this.monitorCanaryDeployment(service, key, 300000); // 5 minutes

        // 4. Gradually increase percentage
        for (const percentage of [0.25, 0.5, 0.75, 1.0]) {
          await this.enableCanaryMode(service, key, percentage);
          await this.monitorCanaryDeployment(service, key, 180000); // 3 minutes
        }

        // 5. Full migration
        await service.enableNewSystemForKey(key);

        this.recordMigrationSuccess(serviceId, key);

      } catch (error) {
        await this.handleKeyMigrationFailure(service, key, error);
      }
    }
  }

  private async validateKeyInNewSystem(service: MigrationCompatibleConfig, key: string): Promise<void> {
    // Compare values between old and new systems
    const legacyValue = service['legacyConfig'].get(key);
    const newValue = await service['super'].get(key);

    if (!this.valuesAreEquivalent(legacyValue, newValue)) {
      throw new MigrationValidationError(
        `Value mismatch for key ${key}: legacy=${legacyValue}, new=${newValue}`
      );
    }

    // Validate new value meets schema requirements
    const schema = await this.getKeySchema(service.serviceId, key);
    const validation = this.validateSchema(newValue, schema);
    if (!validation.valid) {
      throw new MigrationValidationError(`Schema validation failed for ${key}: ${validation.errors.join(', ')}`);
    }
  }

  private async monitorCanaryDeployment(
    service: MigrationCompatibleConfig,
    key: string,
    durationMs: number
  ): Promise<void> {
    const startTime = Date.now();
    const endTime = startTime + durationMs;

    while (Date.now() < endTime) {
      // Check error rates
      const errorRate = await this.getErrorRateForKey(service.serviceId, key);
      if (errorRate > 0.01) { // 1% error threshold
        throw new MigrationError(`High error rate detected for key ${key}: ${errorRate * 100}%`);
      }

      // Check performance impact
      const latencyIncrease = await this.getLatencyIncreaseForKey(service.serviceId, key);
      if (latencyIncrease > 0.2) { // 20% latency increase threshold
        throw new MigrationError(`High latency increase detected for key ${key}: ${latencyIncrease * 100}%`);
      }

      // Wait before next check
      await this.sleep(30000); // 30 seconds
    }
  }
}
```

### 2.3 Migration Monitoring and Rollback

```typescript
interface MigrationMonitor {
  // Real-time monitoring
  startMonitoring(migration: Migration): Promise<void>;
  stopMonitoring(migrationId: string): Promise<void>;

  // Health checks
  checkMigrationHealth(migrationId: string): Promise<MigrationHealthStatus>;
  detectMigrationIssues(migrationId: string): Promise<MigrationIssue[]>;

  // Rollback management
  createRollbackPlan(migration: Migration): Promise<RollbackPlan>;
  executeRollback(rollbackPlan: RollbackPlan): Promise<RollbackResult>;
}

class AutomatedMigrationMonitor implements MigrationMonitor {
  private readonly alerting: AlertingService;
  private readonly metrics: MetricsService;

  async checkMigrationHealth(migrationId: string): Promise<MigrationHealthStatus> {
    const migration = await this.getMigration(migrationId);
    const healthChecks: HealthCheck[] = [];

    // Check service health
    for (const serviceId of migration.affectedServices) {
      const serviceHealth = await this.checkServiceHealth(serviceId);
      healthChecks.push({
        type: 'service_health',
        serviceId,
        status: serviceHealth.healthy ? 'HEALTHY' : 'UNHEALTHY',
        details: serviceHealth.details
      });
    }

    // Check configuration access patterns
    const configHealth = await this.checkConfigurationHealth(migration);
    healthChecks.push(configHealth);

    // Check error rates
    const errorHealth = await this.checkErrorRates(migration);
    healthChecks.push(errorHealth);

    // Check performance impact
    const performanceHealth = await this.checkPerformanceImpact(migration);
    healthChecks.push(performanceHealth);

    const overallHealth = healthChecks.every(check => check.status === 'HEALTHY');

    return {
      migrationId,
      healthy: overallHealth,
      checks: healthChecks,
      lastChecked: new Date()
    };
  }

  async detectMigrationIssues(migrationId: string): Promise<MigrationIssue[]> {
    const issues: MigrationIssue[] = [];

    // Detect configuration access failures
    const accessFailures = await this.detectConfigurationAccessFailures(migrationId);
    issues.push(...accessFailures);

    // Detect value inconsistencies
    const valueIssues = await this.detectValueInconsistencies(migrationId);
    issues.push(...valueIssues);

    // Detect performance degradation
    const performanceIssues = await this.detectPerformanceDegradation(migrationId);
    issues.push(...performanceIssues);

    // Detect security issues
    const securityIssues = await this.detectSecurityIssues(migrationId);
    issues.push(...securityIssues);

    return issues;
  }

  async executeRollback(rollbackPlan: RollbackPlan): Promise<RollbackResult> {
    const rollback = new MigrationRollback(rollbackPlan);

    try {
      // 1. Validate rollback preconditions
      await this.validateRollbackPreconditions(rollbackPlan);

      // 2. Create rollback checkpoint
      const checkpoint = await this.createRollbackCheckpoint(rollbackPlan);

      // 3. Execute rollback steps
      const stepResults: RollbackStepResult[] = [];
      for (const step of rollbackPlan.steps) {
        const stepResult = await this.executeRollbackStep(step);
        stepResults.push(stepResult);

        if (!stepResult.success && step.critical) {
          throw new RollbackError(`Critical rollback step failed: ${step.description}`);
        }
      }

      // 4. Validate rollback success
      await this.validateRollbackSuccess(rollbackPlan);

      return {
        rollbackId: rollback.id,
        success: true,
        stepResults,
        duration: Date.now() - rollback.startTime
      };

    } catch (error) {
      await this.handleRollbackFailure(rollback, error);
      throw error;
    }
  }

  private async executeRollbackStep(step: RollbackStep): Promise<RollbackStepResult> {
    const startTime = Date.now();

    try {
      switch (step.type) {
        case 'REVERT_CONFIGURATION':
          await this.revertConfiguration(step.details);
          break;

        case 'RESTART_SERVICE':
          await this.restartService(step.details.serviceId);
          break;

        case 'SWITCH_TO_LEGACY':
          await this.switchToLegacyConfiguration(step.details.serviceId, step.details.keys);
          break;

        case 'CLEAR_CACHE':
          await this.clearConfigurationCache(step.details.serviceId);
          break;

        default:
          throw new Error(`Unknown rollback step type: ${step.type}`);
      }

      return {
        stepId: step.id,
        success: true,
        duration: Date.now() - startTime
      };

    } catch (error) {
      return {
        stepId: step.id,
        success: false,
        error: error.message,
        duration: Date.now() - startTime
      };
    }
  }
}
```

## Phase 3-4: Service-by-Service Migration

### 3.1 Service Migration Priority Matrix

```typescript
interface ServiceMigrationProfile {
  serviceId: string;
  complexity: MigrationComplexity;
  risk: RiskLevel;
  dependencies: string[];
  configurationCount: number;
  credentialCount: number;
  businessCriticality: BusinessCriticality;
  migrationStrategy: ServiceMigrationStrategy;
}

enum MigrationComplexity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

const SERVICE_MIGRATION_PROFILES: ServiceMigrationProfile[] = [
  {
    serviceId: 'database-service',
    complexity: MigrationComplexity.HIGH,
    risk: RiskLevel.HIGH,
    dependencies: [], // Foundation service
    configurationCount: 25,
    credentialCount: 8,
    businessCriticality: BusinessCriticality.CRITICAL,
    migrationStrategy: ServiceMigrationStrategy.GRADUAL_WITH_VALIDATION
  },

  {
    serviceId: 'api-gateway',
    complexity: MigrationComplexity.MEDIUM,
    risk: RiskLevel.MEDIUM,
    dependencies: ['database-service'],
    configurationCount: 18,
    credentialCount: 5,
    businessCriticality: BusinessCriticality.HIGH,
    migrationStrategy: ServiceMigrationStrategy.CANARY_DEPLOYMENT
  },

  {
    serviceId: 'user-service',
    complexity: MigrationComplexity.MEDIUM,
    risk: RiskLevel.MEDIUM,
    dependencies: ['database-service', 'api-gateway'],
    configurationCount: 20,
    credentialCount: 12,
    businessCriticality: BusinessCriticality.HIGH,
    migrationStrategy: ServiceMigrationStrategy.BLUE_GREEN
  },

  {
    serviceId: 'trading-engine',
    complexity: MigrationComplexity.CRITICAL,
    risk: RiskLevel.CRITICAL,
    dependencies: ['database-service', 'user-service', 'data-bridge'],
    configurationCount: 45,
    credentialCount: 15,
    businessCriticality: BusinessCriticality.CRITICAL,
    migrationStrategy: ServiceMigrationStrategy.STAGED_ROLLOUT
  },

  {
    serviceId: 'data-bridge',
    complexity: MigrationComplexity.HIGH,
    risk: RiskLevel.HIGH,
    dependencies: ['database-service'],
    configurationCount: 35,
    credentialCount: 8,
    businessCriticality: BusinessCriticality.CRITICAL,
    migrationStrategy: ServiceMigrationStrategy.GRADUAL_WITH_MONITORING
  }
];
```

### 3.2 Service-Specific Migration Plans

#### Trading Engine Migration (Critical Service)

```typescript
class TradingEngineMigrationPlan {
  async executeMigration(): Promise<MigrationResult> {
    // Phase 1: Non-critical configuration migration
    await this.migrateNonCriticalConfiguration([
      'logging.level',
      'metrics.enabled',
      'health.checkInterval'
    ]);

    // Phase 2: Database configuration migration
    await this.migrateDatabaseConfiguration();

    // Phase 3: Risk management configuration (most critical)
    await this.migrateRiskConfiguration();

    // Phase 4: Trading strategy configuration
    await this.migrateTradingStrategies();

    // Phase 5: External API configurations
    await this.migrateExternalAPIConfiguration();
  }

  private async migrateRiskConfiguration(): Promise<void> {
    const riskKeys = [
      'risk.maxPositionSize',
      'risk.dailyLossLimit',
      'risk.stopLossPercentage',
      'risk.marginRequirements'
    ];

    // Extra validation for risk configuration
    for (const key of riskKeys) {
      // Validate in staging environment first
      await this.validateInStaging(key);

      // Enable with 1% traffic
      await this.enableCanaryMode(key, 0.01);

      // Monitor for 10 minutes
      await this.monitorForDuration(key, 600000);

      // Gradually increase
      for (const percentage of [0.05, 0.1, 0.25, 0.5, 1.0]) {
        await this.enableCanaryMode(key, percentage);
        await this.monitorForDuration(key, 300000); // 5 minutes each step
      }

      // Full migration
      await this.enableNewSystemForKey(key);
    }
  }

  private async validateInStaging(key: string): Promise<void> {
    // Create staging validation request
    const validation = await this.stagingValidator.validateConfigurationKey(
      'trading-engine',
      key,
      await this.getNewConfigurationValue(key)
    );

    if (!validation.success) {
      throw new MigrationError(`Staging validation failed for ${key}: ${validation.errors.join(', ')}`);
    }

    // Run automated trading simulation
    const simulationResult = await this.runTradingSimulation(key, validation.value);
    if (simulationResult.riskScore > 0.8) {
      throw new MigrationError(`Trading simulation shows high risk for ${key}`);
    }
  }
}
```

#### Data Bridge Migration (Real-Time Service)

```typescript
class DataBridgeMigrationPlan {
  async executeMigration(): Promise<MigrationResult> {
    // Special handling for real-time service
    // Must maintain WebSocket connections during migration

    // Phase 1: Connection pool configuration
    await this.migrateConnectionPoolConfiguration();

    // Phase 2: MT5 configuration (most sensitive)
    await this.migrateMT5Configuration();

    // Phase 3: WebSocket configuration
    await this.migrateWebSocketConfiguration();

    // Phase 4: Data processing configuration
    await this.migrateDataProcessingConfiguration();
  }

  private async migrateMT5Configuration(): Promise<void> {
    // MT5 credentials are extremely sensitive
    // Use zero-downtime migration strategy

    // 1. Pre-warm new configuration system
    await this.preWarmMT5Configuration();

    // 2. Create dual-connection setup
    await this.createDualConnectionSetup();

    // 3. Switch traffic gradually
    await this.gradualTrafficSwitch();

    // 4. Validate data consistency
    await this.validateDataConsistency();

    // 5. Remove old connection
    await this.cleanupOldConnection();
  }

  private async createDualConnectionSetup(): Promise<void> {
    // Create two MT5 connections using old and new config
    const legacyConfig = await this.getLegacyMT5Config();
    const newConfig = await this.getNewMT5Config();

    this.legacyConnection = await this.createMT5Connection(legacyConfig);
    this.newConnection = await this.createMT5Connection(newConfig);

    // Validate both connections work
    await this.validateConnection(this.legacyConnection);
    await this.validateConnection(this.newConnection);

    // Compare data feeds
    await this.compareFeedConsistency(this.legacyConnection, this.newConnection);
  }
}
```

## Phase 5: Optimization and Cleanup

### 5.1 Legacy System Cleanup

```typescript
class LegacyCleanupManager {
  async cleanupLegacyConfiguration(): Promise<CleanupResult> {
    const cleanup = new LegacyCleanup();

    // 1. Identify unused environment variables
    const unusedEnvVars = await this.identifyUnusedEnvironmentVariables();

    // 2. Remove legacy configuration files
    const legacyFiles = await this.identifyLegacyConfigurationFiles();

    // 3. Update Docker Compose files
    await this.updateDockerComposeFiles();

    // 4. Remove legacy configuration classes
    await this.removeLegacyConfigurationCode();

    // 5. Update documentation
    await this.updateConfigurationDocumentation();

    return {
      cleanupId: cleanup.id,
      removedEnvironmentVariables: unusedEnvVars.length,
      removedFiles: legacyFiles.length,
      updatedDockerFiles: await this.getUpdatedDockerFiles(),
      cleanupTime: Date.now() - cleanup.startTime
    };
  }

  private async updateDockerComposeFiles(): Promise<void> {
    const dockerComposeFiles = await this.getDockerComposeFiles();

    for (const file of dockerComposeFiles) {
      const content = await this.readFile(file);
      const parsed = yaml.parse(content);

      // Remove environment variables that are now in config service
      for (const [serviceName, serviceConfig] of Object.entries(parsed.services)) {
        if (serviceConfig.environment) {
          serviceConfig.environment = this.filterEnvironmentVariables(
            serviceConfig.environment,
            serviceName
          );
        }

        // Add config service dependency
        if (!serviceConfig.depends_on) {
          serviceConfig.depends_on = [];
        }
        if (!serviceConfig.depends_on.includes('config-service')) {
          serviceConfig.depends_on.push('config-service');
        }
      }

      const newContent = yaml.stringify(parsed);
      await this.writeFile(file, newContent);
    }
  }
}
```

### 5.2 Performance Optimization

```typescript
class ConfigurationPerformanceOptimizer {
  async optimizeConfigurationSystem(): Promise<OptimizationResult> {
    const optimizations: OptimizationStep[] = [];

    // 1. Cache optimization
    const cacheOptimization = await this.optimizeCaching();
    optimizations.push(cacheOptimization);

    // 2. Network optimization
    const networkOptimization = await this.optimizeNetworking();
    optimizations.push(networkOptimization);

    // 3. Database optimization
    const dbOptimization = await this.optimizeDatabase();
    optimizations.push(dbOptimization);

    // 4. WebSocket optimization
    const wsOptimization = await this.optimizeWebSocket();
    optimizations.push(wsOptimization);

    return {
      totalOptimizations: optimizations.length,
      performanceImprovement: await this.measurePerformanceImprovement(),
      optimizations
    };
  }

  private async optimizeCaching(): Promise<OptimizationStep> {
    // Implement intelligent cache warming
    await this.implementCacheWarming();

    // Optimize cache TTL based on usage patterns
    await this.optimizeCacheTTL();

    // Implement cache compression
    await this.implementCacheCompression();

    // Add cache invalidation optimization
    await this.optimizeCacheInvalidation();

    return {
      name: 'Cache Optimization',
      improvementPercentage: 35,
      details: 'Implemented cache warming, TTL optimization, and compression'
    };
  }

  private async optimizeNetworking(): Promise<OptimizationStep> {
    // Implement connection pooling for config service
    await this.implementConnectionPooling();

    // Add request batching
    await this.implementRequestBatching();

    // Optimize WebSocket message format
    await this.optimizeWebSocketMessages();

    return {
      name: 'Network Optimization',
      improvementPercentage: 25,
      details: 'Added connection pooling, request batching, and message optimization'
    };
  }
}
```

## Risk Mitigation and Contingency Plans

### Risk Assessment Matrix

```typescript
interface MigrationRisk {
  id: string;
  description: string;
  probability: RiskProbability;
  impact: RiskImpact;
  severity: RiskSeverity;
  mitigation: MitigationStrategy;
  contingency: ContingencyPlan;
}

const MIGRATION_RISKS: MigrationRisk[] = [
  {
    id: 'TRADING_ENGINE_DOWNTIME',
    description: 'Trading engine experiences downtime during configuration migration',
    probability: RiskProbability.LOW,
    impact: RiskImpact.CRITICAL,
    severity: RiskSeverity.HIGH,
    mitigation: {
      strategy: 'Staged rollout with real-time monitoring',
      steps: [
        'Migrate during low-volume hours',
        'Use canary deployment with 1% traffic',
        'Maintain dual-mode operation',
        'Real-time health monitoring'
      ]
    },
    contingency: {
      triggerConditions: ['Error rate > 0.1%', 'Latency increase > 20%'],
      actions: [
        'Immediate rollback to legacy configuration',
        'Restart trading engine service',
        'Notify trading desk and management',
        'Investigate and fix issues before retry'
      ]
    }
  },

  {
    id: 'CREDENTIAL_EXPOSURE',
    description: 'Credentials accidentally exposed during migration process',
    probability: RiskProbability.MEDIUM,
    impact: RiskImpact.CRITICAL,
    severity: RiskSeverity.CRITICAL,
    mitigation: {
      strategy: 'Encrypt all credentials immediately and use vault references',
      steps: [
        'Encrypt credentials before migration',
        'Use vault references in all configurations',
        'Validate no plaintext credentials in logs',
        'Automated security scanning'
      ]
    },
    contingency: {
      triggerConditions: ['Plaintext credential detected', 'Security scan failure'],
      actions: [
        'Immediately rotate all affected credentials',
        'Pause migration process',
        'Security team incident response',
        'Audit all related systems'
      ]
    }
  },

  {
    id: 'DATA_INCONSISTENCY',
    description: 'Configuration values inconsistent between old and new systems',
    probability: RiskProbability.MEDIUM,
    impact: RiskImpact.HIGH,
    severity: RiskSeverity.MEDIUM,
    mitigation: {
      strategy: 'Continuous validation and monitoring',
      steps: [
        'Automated value comparison',
        'Schema validation',
        'Business rule validation',
        'Real-time monitoring'
      ]
    },
    contingency: {
      triggerConditions: ['Value mismatch detected', 'Validation failure'],
      actions: [
        'Switch to legacy configuration for affected keys',
        'Investigate root cause',
        'Fix data inconsistency',
        'Re-validate before retry'
      ]
    }
  }
];
```

## Success Metrics and Validation

### Migration Success Criteria

```typescript
interface MigrationSuccessCriteria {
  // Performance metrics
  configurationRetrievalLatency: { max: 10, unit: 'milliseconds' };
  cacheHitRate: { min: 95, unit: 'percentage' };
  systemUptime: { min: 99.9, unit: 'percentage' };

  // Security metrics
  credentialEncryptionRate: { min: 100, unit: 'percentage' };
  unauthorizedAccessAttempts: { max: 0, unit: 'count' };
  securityAuditCompliance: { min: 100, unit: 'percentage' };

  // Operational metrics
  configurationChangeTime: { max: 60, unit: 'seconds' };
  rollbackTime: { max: 30, unit: 'seconds' };
  migrationCompletionRate: { min: 100, unit: 'percentage' };

  // Business metrics
  tradingSystemAvailability: { min: 99.99, unit: 'percentage' };
  configurationIncidents: { max: 0, unit: 'count' };
  developerProductivity: { increase: 20, unit: 'percentage' };
}

class MigrationValidator {
  async validateMigrationSuccess(): Promise<ValidationReport> {
    const report = new ValidationReport();

    // Validate all services migrated
    const serviceStatus = await this.validateAllServicesMigrated();
    report.addSection('Service Migration Status', serviceStatus);

    // Validate performance criteria
    const performanceStatus = await this.validatePerformanceCriteria();
    report.addSection('Performance Validation', performanceStatus);

    // Validate security requirements
    const securityStatus = await this.validateSecurityRequirements();
    report.addSection('Security Validation', securityStatus);

    // Validate business continuity
    const businessStatus = await this.validateBusinessContinuity();
    report.addSection('Business Continuity', businessStatus);

    return report;
  }
}
```

This comprehensive migration strategy ensures a safe, gradual transition from the current distributed configuration approach to the new centralized system while maintaining system availability, security, and performance throughout the process.

Key migration benefits:
- **Zero downtime** through careful phasing and fallback mechanisms
- **Risk mitigation** through gradual rollout and continuous monitoring
- **Performance improvement** through optimized caching and networking
- **Security enhancement** through credential vault and encryption
- **Operational excellence** through automated monitoring and rollback capabilities