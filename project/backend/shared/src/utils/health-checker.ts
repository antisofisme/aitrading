/**
 * @fileoverview Health Check utility for monitoring service health
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

import { HealthStatus, HealthDependency, HealthMetrics } from '../types';
import { Logger } from './logger';

// =============================================================================
// HEALTH CHECK CONFIGURATION
// =============================================================================

export interface HealthCheckConfig {
  service: {
    name: string;
    version: string;
    environment: string;
  };
  dependencies: DependencyConfig[];
  metrics: {
    enabled: boolean;
    collectInterval: number;
  };
  logger: Logger;
}

export interface DependencyConfig {
  name: string;
  type: 'http' | 'database' | 'redis' | 'consul' | 'custom';
  config: {
    url?: string;
    host?: string;
    port?: number;
    timeout?: number;
    customCheck?: () => Promise<boolean>;
  };
  critical: boolean;
}

// =============================================================================
// HEALTH CHECKER CLASS
// =============================================================================

export class HealthChecker {
  private config: HealthCheckConfig;
  private logger: Logger;
  private startTime: Date;
  private lastHealthCheck?: HealthStatus;
  private metricsInterval?: NodeJS.Timeout;

  constructor(config: HealthCheckConfig) {
    this.config = config;
    this.logger = config.logger;
    this.startTime = new Date();

    if (config.metrics.enabled) {
      this.startMetricsCollection();
    }
  }

  /**
   * Perform comprehensive health check
   */
  async checkHealth(): Promise<HealthStatus> {
    const startTime = Date.now();

    try {
      const dependencies = await this.checkDependencies();
      const metrics = this.config.metrics.enabled ? await this.collectMetrics() : undefined;

      const status = this.determineOverallStatus(dependencies);

      const healthStatus: HealthStatus = {
        status,
        timestamp: new Date(),
        version: this.config.service.version,
        uptime: Date.now() - this.startTime.getTime(),
        environment: this.config.service.environment,
        dependencies,
        metrics
      };

      this.lastHealthCheck = healthStatus;

      this.logger.debug('Health check completed', {
        status,
        duration: Date.now() - startTime,
        dependencies: dependencies.length
      });

      return healthStatus;

    } catch (error) {
      this.logger.error('Health check failed', { error });

      return {
        status: 'unhealthy',
        timestamp: new Date(),
        version: this.config.service.version,
        uptime: Date.now() - this.startTime.getTime(),
        environment: this.config.service.environment,
        dependencies: []
      };
    }
  }

  /**
   * Check all configured dependencies
   */
  private async checkDependencies(): Promise<HealthDependency[]> {
    const promises = this.config.dependencies.map(dep => this.checkDependency(dep));
    return Promise.all(promises);
  }

  /**
   * Check individual dependency
   */
  private async checkDependency(config: DependencyConfig): Promise<HealthDependency> {
    const startTime = Date.now();

    try {
      let isHealthy = false;

      switch (config.type) {
        case 'http':
          isHealthy = await this.checkHttpDependency(config);
          break;
        case 'database':
          isHealthy = await this.checkDatabaseDependency(config);
          break;
        case 'redis':
          isHealthy = await this.checkRedisDependency(config);
          break;
        case 'consul':
          isHealthy = await this.checkConsulDependency(config);
          break;
        case 'custom':
          isHealthy = await this.checkCustomDependency(config);
          break;
        default:
          throw new Error(`Unknown dependency type: ${config.type}`);
      }

      const responseTime = Date.now() - startTime;

      return {
        name: config.name,
        status: isHealthy ? 'healthy' : 'unhealthy',
        responseTime,
        lastChecked: new Date()
      };

    } catch (error) {
      const responseTime = Date.now() - startTime;

      return {
        name: config.name,
        status: 'unhealthy',
        responseTime,
        lastChecked: new Date(),
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Check HTTP dependency
   */
  private async checkHttpDependency(config: DependencyConfig): Promise<boolean> {
    const axios = require('axios');
    const timeout = config.config.timeout || 5000;

    try {
      const response = await axios.get(config.config.url, {
        timeout,
        validateStatus: (status: number) => status < 400
      });

      return response.status >= 200 && response.status < 400;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check database dependency
   */
  private async checkDatabaseDependency(config: DependencyConfig): Promise<boolean> {
    // This is a simplified check - in real implementation, you'd use actual DB clients
    try {
      const { Client } = require('pg');
      const client = new Client({
        host: config.config.host,
        port: config.config.port,
        connectionTimeoutMillis: config.config.timeout || 5000
      });

      await client.connect();
      await client.query('SELECT 1');
      await client.end();

      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check Redis dependency
   */
  private async checkRedisDependency(config: DependencyConfig): Promise<boolean> {
    try {
      const Redis = require('ioredis');
      const redis = new Redis({
        host: config.config.host,
        port: config.config.port,
        connectTimeout: config.config.timeout || 5000,
        retryDelayOnFailover: 100,
        maxRetriesPerRequest: 1
      });

      const result = await redis.ping();
      redis.disconnect();

      return result === 'PONG';
    } catch (error) {
      return false;
    }
  }

  /**
   * Check Consul dependency
   */
  private async checkConsulDependency(config: DependencyConfig): Promise<boolean> {
    try {
      const Consul = require('consul');
      const consul = new Consul({
        host: config.config.host,
        port: config.config.port
      });

      await consul.status.leader();
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Check custom dependency
   */
  private async checkCustomDependency(config: DependencyConfig): Promise<boolean> {
    if (!config.config.customCheck) {
      throw new Error('Custom check function not provided');
    }

    return config.config.customCheck();
  }

  /**
   * Determine overall health status based on dependencies
   */
  private determineOverallStatus(dependencies: HealthDependency[]): 'healthy' | 'unhealthy' | 'degraded' {
    const criticalDeps = this.config.dependencies.filter(dep => dep.critical);
    const criticalResults = dependencies.filter(dep =>
      criticalDeps.some(critical => critical.name === dep.name)
    );

    // If any critical dependency is unhealthy, overall status is unhealthy
    if (criticalResults.some(dep => dep.status === 'unhealthy')) {
      return 'unhealthy';
    }

    // If any non-critical dependency is unhealthy, overall status is degraded
    if (dependencies.some(dep => dep.status === 'unhealthy')) {
      return 'degraded';
    }

    return 'healthy';
  }

  /**
   * Collect system metrics
   */
  private async collectMetrics(): Promise<HealthMetrics> {
    const process = require('process');
    const os = require('os');

    const memoryUsage = process.memoryUsage();
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;

    return {
      memoryUsage: {
        used: Math.round(memoryUsage.heapUsed / 1024 / 1024), // MB
        total: Math.round(memoryUsage.heapTotal / 1024 / 1024), // MB
        percentage: Math.round((memoryUsage.heapUsed / memoryUsage.heapTotal) * 100)
      },
      cpuUsage: Math.round(process.cpuUsage().user / 1000000), // Convert to seconds
      diskUsage: {
        used: Math.round(usedMemory / 1024 / 1024), // MB
        total: Math.round(totalMemory / 1024 / 1024), // MB
        percentage: Math.round((usedMemory / totalMemory) * 100)
      }
    };
  }

  /**
   * Start metrics collection interval
   */
  private startMetricsCollection(): void {
    this.metricsInterval = setInterval(async () => {
      try {
        const metrics = await this.collectMetrics();
        this.logger.debug('Metrics collected', { metrics });
      } catch (error) {
        this.logger.warn('Failed to collect metrics', { error });
      }
    }, this.config.metrics.collectInterval);
  }

  /**
   * Stop metrics collection
   */
  stopMetricsCollection(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = undefined;
    }
  }

  /**
   * Get last health check result
   */
  getLastHealthCheck(): HealthStatus | undefined {
    return this.lastHealthCheck;
  }

  /**
   * Add dependency configuration
   */
  addDependency(dependency: DependencyConfig): void {
    this.config.dependencies.push(dependency);
  }

  /**
   * Remove dependency configuration
   */
  removeDependency(name: string): void {
    this.config.dependencies = this.config.dependencies.filter(dep => dep.name !== name);
  }

  /**
   * Get service uptime in milliseconds
   */
  getUptime(): number {
    return Date.now() - this.startTime.getTime();
  }

  /**
   * Get service start time
   */
  getStartTime(): Date {
    return this.startTime;
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create health checker instance
 */
export function createHealthChecker(config: HealthCheckConfig): HealthChecker {
  return new HealthChecker(config);
}

/**
 * Create basic health checker with common dependencies
 */
export function createBasicHealthChecker(
  serviceName: string,
  serviceVersion: string,
  logger: Logger,
  dependencies: Partial<DependencyConfig>[] = []
): HealthChecker {
  const config: HealthCheckConfig = {
    service: {
      name: serviceName,
      version: serviceVersion,
      environment: process.env.NODE_ENV || 'development'
    },
    dependencies: dependencies.map(dep => ({
      name: dep.name || 'unknown',
      type: dep.type || 'http',
      config: dep.config || {},
      critical: dep.critical !== undefined ? dep.critical : true
    })),
    metrics: {
      enabled: true,
      collectInterval: 60000 // 1 minute
    },
    logger
  };

  return new HealthChecker(config);
}

/**
 * Express middleware for health checks
 */
export function createHealthMiddleware(healthChecker: HealthChecker) {
  return async (req: any, res: any) => {
    try {
      const health = await healthChecker.checkHealth();

      const statusCode = health.status === 'healthy' ? 200 :
                        health.status === 'degraded' ? 200 : 503;

      res.status(statusCode).json(health);
    } catch (error) {
      res.status(503).json({
        status: 'unhealthy',
        timestamp: new Date(),
        error: 'Health check failed'
      });
    }
  };
}

/**
 * Simple readiness check
 */
export function createReadinessMiddleware(healthChecker: HealthChecker) {
  return async (req: any, res: any) => {
    try {
      const health = await healthChecker.checkHealth();
      const isReady = health.status === 'healthy';

      res.status(isReady ? 200 : 503).json({
        ready: isReady,
        timestamp: new Date()
      });
    } catch (error) {
      res.status(503).json({
        ready: false,
        timestamp: new Date(),
        error: 'Readiness check failed'
      });
    }
  };
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default HealthChecker;