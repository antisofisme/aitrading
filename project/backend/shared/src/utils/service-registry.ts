/**
 * @fileoverview Service Discovery and Registry utility using Consul
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

import Consul from 'consul';
import { ServiceConfig, HealthStatus, HealthDependency } from '../types';
import { Logger } from './logger';

// =============================================================================
// SERVICE REGISTRY CONFIGURATION
// =============================================================================

export interface ServiceRegistryConfig {
  consul: {
    host: string;
    port: number;
    token?: string;
    datacenter?: string;
  };
  service: {
    id: string;
    name: string;
    tags: string[];
    address: string;
    port: number;
    meta?: Record<string, string>;
  };
  health: {
    checkUrl: string;
    interval: string;
    timeout: string;
    deregisterAfter?: string;
  };
  logger: Logger;
}

// =============================================================================
// SERVICE REGISTRY CLASS
// =============================================================================

export class ServiceRegistry {
  private consul: Consul.Consul;
  private config: ServiceRegistryConfig;
  private logger: Logger;
  private isRegistered: boolean = false;
  private healthCheckInterval?: NodeJS.Timeout;

  constructor(config: ServiceRegistryConfig) {
    this.config = config;
    this.logger = config.logger;

    this.consul = new Consul({
      host: config.consul.host,
      port: config.consul.port,
      secure: false,
      defaults: {
        token: config.consul.token
      }
    });
  }

  /**
   * Register service with Consul
   */
  async register(): Promise<void> {
    try {
      const serviceDefinition: Consul.Agent.Service.RegisterOptions = {
        id: this.config.service.id,
        name: this.config.service.name,
        tags: this.config.service.tags,
        address: this.config.service.address,
        port: this.config.service.port,
        meta: this.config.service.meta,
        check: {
          http: this.config.health.checkUrl,
          interval: this.config.health.interval,
          timeout: this.config.health.timeout,
          deregistercriticalserviceafter: this.config.health.deregisterAfter || '10m'
        }
      };

      await this.consul.agent.service.register(serviceDefinition);
      this.isRegistered = true;

      this.logger.info('Service registered with Consul', {
        serviceId: this.config.service.id,
        serviceName: this.config.service.name,
        address: this.config.service.address,
        port: this.config.service.port
      });

      // Start periodic health reporting
      this.startHealthReporting();

    } catch (error) {
      this.logger.error('Failed to register service with Consul', { error });
      throw error;
    }
  }

  /**
   * Deregister service from Consul
   */
  async deregister(): Promise<void> {
    try {
      if (this.healthCheckInterval) {
        clearInterval(this.healthCheckInterval);
      }

      await this.consul.agent.service.deregister(this.config.service.id);
      this.isRegistered = false;

      this.logger.info('Service deregistered from Consul', {
        serviceId: this.config.service.id
      });

    } catch (error) {
      this.logger.error('Failed to deregister service from Consul', { error });
      throw error;
    }
  }

  /**
   * Discover services by name
   */
  async discoverServices(serviceName: string): Promise<ServiceInstance[]> {
    try {
      const result = await this.consul.health.service({
        service: serviceName,
        passing: true
      });

      const services: ServiceInstance[] = result.map((entry: any) => ({
        id: entry.Service.ID,
        name: entry.Service.Service,
        address: entry.Service.Address,
        port: entry.Service.Port,
        tags: entry.Service.Tags,
        meta: entry.Service.Meta,
        health: this.mapHealthStatus(entry.Checks)
      }));

      this.logger.debug('Discovered services', {
        serviceName,
        count: services.length,
        services: services.map(s => ({ id: s.id, address: s.address, port: s.port }))
      });

      return services;

    } catch (error) {
      this.logger.error('Failed to discover services', { serviceName, error });
      throw error;
    }
  }

  /**
   * Get service instance by ID
   */
  async getService(serviceId: string): Promise<ServiceInstance | null> {
    try {
      const services = await this.consul.agent.service.list();
      const service = services[serviceId];

      if (!service) {
        return null;
      }

      return {
        id: service.ID,
        name: service.Service,
        address: service.Address,
        port: service.Port,
        tags: service.Tags,
        meta: service.Meta,
        health: 'unknown'
      };

    } catch (error) {
      this.logger.error('Failed to get service', { serviceId, error });
      throw error;
    }
  }

  /**
   * Get all healthy instances of a service
   */
  async getHealthyInstances(serviceName: string): Promise<ServiceInstance[]> {
    const services = await this.discoverServices(serviceName);
    return services.filter(service => service.health === 'healthy');
  }

  /**
   * Get load-balanced service instance
   */
  async getBalancedInstance(serviceName: string): Promise<ServiceInstance | null> {
    const instances = await this.getHealthyInstances(serviceName);

    if (instances.length === 0) {
      return null;
    }

    // Simple round-robin load balancing
    const index = Math.floor(Math.random() * instances.length);
    return instances[index];
  }

  /**
   * Set key-value pair in Consul KV store
   */
  async setConfig(key: string, value: any): Promise<void> {
    try {
      await this.consul.kv.set(key, JSON.stringify(value));
      this.logger.debug('Configuration set in Consul KV', { key });
    } catch (error) {
      this.logger.error('Failed to set configuration in Consul KV', { key, error });
      throw error;
    }
  }

  /**
   * Get value from Consul KV store
   */
  async getConfig<T = any>(key: string): Promise<T | null> {
    try {
      const result = await this.consul.kv.get(key);

      if (!result || !result.Value) {
        return null;
      }

      return JSON.parse(result.Value) as T;
    } catch (error) {
      this.logger.error('Failed to get configuration from Consul KV', { key, error });
      throw error;
    }
  }

  /**
   * Watch for service changes
   */
  watchServices(serviceName: string, callback: (services: ServiceInstance[]) => void): () => void {
    const watcher = this.consul.watch({
      method: this.consul.health.service,
      options: {
        service: serviceName,
        passing: true
      }
    });

    watcher.on('change', (data: any) => {
      const services: ServiceInstance[] = data.map((entry: any) => ({
        id: entry.Service.ID,
        name: entry.Service.Service,
        address: entry.Service.Address,
        port: entry.Service.Port,
        tags: entry.Service.Tags,
        meta: entry.Service.Meta,
        health: this.mapHealthStatus(entry.Checks)
      }));

      callback(services);
    });

    watcher.on('error', (error: Error) => {
      this.logger.error('Service watch error', { serviceName, error });
    });

    // Return cleanup function
    return () => {
      watcher.end();
    };
  }

  /**
   * Start periodic health reporting
   */
  private startHealthReporting(): void {
    this.healthCheckInterval = setInterval(async () => {
      try {
        // Report health status to Consul
        await this.consul.agent.check.pass(`service:${this.config.service.id}`);
      } catch (error) {
        this.logger.warn('Failed to report health status', { error });
      }
    }, 30000); // Report every 30 seconds
  }

  /**
   * Map Consul health checks to simple status
   */
  private mapHealthStatus(checks: any[]): 'healthy' | 'unhealthy' | 'unknown' {
    if (!checks || checks.length === 0) {
      return 'unknown';
    }

    const hasFailure = checks.some(check => check.Status !== 'passing');
    return hasFailure ? 'unhealthy' : 'healthy';
  }

  /**
   * Check if service is registered
   */
  isServiceRegistered(): boolean {
    return this.isRegistered;
  }

  /**
   * Get Consul client for advanced operations
   */
  getConsulClient(): Consul.Consul {
    return this.consul;
  }
}

// =============================================================================
// SERVICE INSTANCE INTERFACE
// =============================================================================

export interface ServiceInstance {
  id: string;
  name: string;
  address: string;
  port: number;
  tags: string[];
  meta?: Record<string, string>;
  health: 'healthy' | 'unhealthy' | 'unknown';
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create service registry instance
 */
export function createServiceRegistry(config: ServiceRegistryConfig): ServiceRegistry {
  return new ServiceRegistry(config);
}

/**
 * Create service registry from service config
 */
export function createServiceRegistryFromConfig(
  serviceConfig: ServiceConfig,
  logger: Logger
): ServiceRegistry {
  const registryConfig: ServiceRegistryConfig = {
    consul: {
      host: serviceConfig.consul.host,
      port: serviceConfig.consul.port,
      token: serviceConfig.consul.token,
      datacenter: serviceConfig.consul.datacenter
    },
    service: {
      id: `${serviceConfig.name}-${serviceConfig.version}-${process.pid}`,
      name: serviceConfig.name,
      tags: [serviceConfig.environment, `version-${serviceConfig.version}`],
      address: serviceConfig.host,
      port: serviceConfig.port,
      meta: {
        version: serviceConfig.version,
        environment: serviceConfig.environment,
        adminPort: serviceConfig.adminPort?.toString() || ''
      }
    },
    health: {
      checkUrl: `http://${serviceConfig.host}:${serviceConfig.adminPort || serviceConfig.port}/health`,
      interval: '30s',
      timeout: '10s',
      deregisterAfter: '10m'
    },
    logger
  };

  return new ServiceRegistry(registryConfig);
}

/**
 * Simple service discovery helper
 */
export class ServiceDiscovery {
  private registry: ServiceRegistry;
  private serviceCache: Map<string, ServiceInstance[]> = new Map();
  private cacheTimeout: number = 30000; // 30 seconds

  constructor(registry: ServiceRegistry) {
    this.registry = registry;
  }

  /**
   * Get service with caching
   */
  async getService(serviceName: string): Promise<ServiceInstance | null> {
    const instances = await this.getServices(serviceName);
    return instances.length > 0 ? instances[0] : null;
  }

  /**
   * Get all services with caching
   */
  async getServices(serviceName: string): Promise<ServiceInstance[]> {
    const cached = this.serviceCache.get(serviceName);

    if (cached) {
      return cached;
    }

    const services = await this.registry.discoverServices(serviceName);
    this.serviceCache.set(serviceName, services);

    // Clear cache after timeout
    setTimeout(() => {
      this.serviceCache.delete(serviceName);
    }, this.cacheTimeout);

    return services;
  }

  /**
   * Clear service cache
   */
  clearCache(serviceName?: string): void {
    if (serviceName) {
      this.serviceCache.delete(serviceName);
    } else {
      this.serviceCache.clear();
    }
  }
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default ServiceRegistry;