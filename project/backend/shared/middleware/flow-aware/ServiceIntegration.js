/**
 * @fileoverview Service Integration utilities for automatic middleware registration
 * @version 1.0.0
 * @author AI Trading Platform Team
 *
 * Provides automatic integration of flow-aware middleware across all microservices
 * with service discovery, configuration management, and deployment automation.
 */

const fs = require('fs').promises;
const path = require('path');
const { FlowTracker } = require('./FlowTracker');
const { ChainContextManager } = require('./ChainContextManager');
const { FlowMetricsCollector } = require('./FlowMetricsCollector');
const { ChainEventPublisher } = require('./ChainEventPublisher');

// =============================================================================
// INTEGRATION CONSTANTS
// =============================================================================

const SERVICE_REGISTRY_PATH = '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/config/service-registry.json';
const SHARED_CONFIG_PATH = '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/shared/config';

const MIDDLEWARE_CONFIG = {
  flowTracker: {
    enabled: true,
    performanceThreshold: 1, // 1ms
    enableDependencyTracking: true,
    enablePerformanceTracking: true
  },
  chainContext: {
    enabled: true,
    enablePersistence: false,
    maxContexts: 10000,
    cleanupInterval: 60000
  },
  metricsCollector: {
    enabled: true,
    enableRealTimeMetrics: true,
    collectionInterval: 1000,
    retentionPeriod: 3600000 // 1 hour
  },
  eventPublisher: {
    enabled: true,
    enableBuffering: true,
    enableRetries: true,
    flushInterval: 5000
  }
};

// =============================================================================
// SERVICE INTEGRATION CLASS
// =============================================================================

class ServiceIntegration {
  constructor(options = {}) {
    this.logger = options.logger || console;
    this.configPath = options.configPath || SHARED_CONFIG_PATH;
    this.serviceRegistryPath = options.serviceRegistryPath || SERVICE_REGISTRY_PATH;
    this.middlewareConfig = { ...MIDDLEWARE_CONFIG, ...options.middlewareConfig };

    // Service registry
    this.serviceRegistry = null;
    this.services = new Map();

    // Middleware instances
    this.flowTracker = null;
    this.chainContextManager = null;
    this.metricsCollector = null;
    this.eventPublisher = null;
  }

  /**
   * Initialize service integration
   */
  async initialize() {
    try {
      // Load service registry
      await this.loadServiceRegistry();

      // Initialize middleware components
      await this.initializeMiddleware();

      // Setup integration hooks
      this.setupIntegrationHooks();

      this.logger.info('Service integration initialized successfully', {
        serviceCount: this.services.size,
        middlewareEnabled: Object.keys(this.middlewareConfig)
          .filter(key => this.middlewareConfig[key].enabled)
      });

    } catch (error) {
      this.logger.error('Failed to initialize service integration', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  /**
   * Load service registry
   */
  async loadServiceRegistry() {
    try {
      const registryData = await fs.readFile(this.serviceRegistryPath, 'utf8');
      this.serviceRegistry = JSON.parse(registryData);

      // Process services
      for (const [serviceName, serviceConfig] of Object.entries(this.serviceRegistry.services)) {
        this.services.set(serviceName, {
          name: serviceName,
          port: serviceConfig.port,
          protocol: serviceConfig.protocol,
          description: serviceConfig.description,
          critical: serviceConfig.critical,
          health: serviceConfig.health,
          configFile: serviceConfig.configFile,
          status: 'unknown'
        });
      }

      this.logger.info('Service registry loaded', {
        serviceCount: this.services.size,
        criticalServices: this.serviceRegistry.criticalServices?.length || 0
      });

    } catch (error) {
      this.logger.error('Failed to load service registry', {
        registryPath: this.serviceRegistryPath,
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Initialize middleware components
   */
  async initializeMiddleware() {
    const serviceName = process.env.SERVICE_NAME || 'unknown-service';

    // Initialize metrics collector
    if (this.middlewareConfig.metricsCollector.enabled) {
      this.metricsCollector = new FlowMetricsCollector({
        serviceName,
        logger: this.logger,
        ...this.middlewareConfig.metricsCollector
      });
    }

    // Initialize event publisher
    if (this.middlewareConfig.eventPublisher.enabled) {
      this.eventPublisher = new ChainEventPublisher({
        serviceName,
        logger: this.logger,
        metricsCollector: this.metricsCollector,
        ...this.middlewareConfig.eventPublisher
      });
    }

    // Initialize flow tracker
    if (this.middlewareConfig.flowTracker.enabled) {
      this.flowTracker = new FlowTracker({
        serviceName,
        logger: this.logger,
        metricsCollector: this.metricsCollector,
        eventPublisher: this.eventPublisher,
        ...this.middlewareConfig.flowTracker
      });
    }

    // Initialize chain context manager
    if (this.middlewareConfig.chainContext.enabled) {
      this.chainContextManager = new ChainContextManager({
        serviceName,
        logger: this.logger,
        ...this.middlewareConfig.chainContext
      });
    }

    this.logger.info('Middleware components initialized', {
      serviceName,
      components: {
        flowTracker: !!this.flowTracker,
        chainContextManager: !!this.chainContextManager,
        metricsCollector: !!this.metricsCollector,
        eventPublisher: !!this.eventPublisher
      }
    });
  }

  /**
   * Setup integration hooks
   */
  setupIntegrationHooks() {
    if (this.eventPublisher && this.metricsCollector) {
      // Connect metrics collector to event publisher
      this.metricsCollector.on('metricsCollected', (data) => {
        this.eventPublisher.publish('metrics.collected', data, {
          priority: 1 // Low priority
        });
      });

      this.metricsCollector.on('realTimeMetrics', (metrics) => {
        this.eventPublisher.publish('metrics.realtime', metrics, {
          priority: 1 // Low priority
        });
      });
    }

    if (this.chainContextManager && this.eventPublisher) {
      // Connect context manager to event publisher
      this.chainContextManager.on('contextCreated', (context) => {
        this.eventPublisher.publishFlowStart(context);
      });

      this.chainContextManager.on('contextCompleted', (context) => {
        this.eventPublisher.publishFlowComplete(context);
      });

      this.chainContextManager.on('errorAdded', (context, error) => {
        this.eventPublisher.publishError(context, error);
      });
    }
  }

  /**
   * Get Express.js middleware stack
   */
  getMiddlewareStack() {
    const middlewareStack = [];

    // Add flow tracker middleware
    if (this.flowTracker) {
      middlewareStack.push(this.flowTracker.middleware);
    }

    // Add chain context middleware
    if (this.chainContextManager) {
      middlewareStack.push(this.chainContextManager.middleware);
    }

    return middlewareStack;
  }

  /**
   * Create service-specific configuration
   */
  createServiceConfig(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      throw new Error(`Service ${serviceName} not found in registry`);
    }

    return {
      serviceName,
      port: service.port,
      protocol: service.protocol,
      critical: service.critical,
      middleware: {
        flowTracker: this.flowTracker,
        chainContextManager: this.chainContextManager,
        metricsCollector: this.metricsCollector,
        eventPublisher: this.eventPublisher
      },
      integration: {
        getOutgoingHeaders: (req, targetService) => {
          const headers = {};

          if (this.flowTracker) {
            Object.assign(headers, this.flowTracker.createOutgoingHeaders(req, targetService));
          }

          if (this.chainContextManager) {
            Object.assign(headers, this.chainContextManager.getOutgoingHeaders(req, targetService));
          }

          return headers;
        },
        trackDependency: (targetService, type = 'http') => {
          if (this.flowTracker) {
            return this.flowTracker.trackDependency(targetService, type);
          }
          return (req, res, next) => next && next();
        },
        addError: (req, error, operation = null) => {
          if (this.flowTracker) {
            this.flowTracker.addError(req, error);
          }
          if (this.chainContextManager) {
            this.chainContextManager.addError(req, error, operation);
          }
        },
        getFlowContext: (req) => {
          return this.flowTracker ? this.flowTracker.getFlowContext(req) : null;
        },
        getChainContext: (req) => {
          return this.chainContextManager ? this.chainContextManager.getContext(req) : null;
        }
      }
    };
  }

  /**
   * Generate integration code for service
   */
  generateIntegrationCode(serviceName) {
    const service = this.services.get(serviceName);
    if (!service) {
      throw new Error(`Service ${serviceName} not found in registry`);
    }

    return `
// Flow-aware middleware integration for ${serviceName}
// Auto-generated by ServiceIntegration

const { ServiceIntegration } = require('../../shared/middleware/flow-aware');

// Initialize service integration
const serviceIntegration = new ServiceIntegration({
  logger: require('../utils/logger'), // Use existing logger
  middlewareConfig: {
    flowTracker: {
      enabled: true,
      performanceThreshold: 1,
      enableDependencyTracking: true
    },
    chainContext: {
      enabled: true,
      enablePersistence: ${service.critical}
    },
    metricsCollector: {
      enabled: true,
      enableRealTimeMetrics: true
    },
    eventPublisher: {
      enabled: true,
      enableBuffering: true
    }
  }
});

// Initialize integration
serviceIntegration.initialize().catch(console.error);

// Get service configuration
const serviceConfig = serviceIntegration.createServiceConfig('${serviceName}');

// Export middleware stack
module.exports = {
  middlewareStack: serviceIntegration.getMiddlewareStack(),
  serviceConfig,
  integration: serviceConfig.integration,

  // Helper functions
  getFlowContext: serviceConfig.integration.getFlowContext,
  getChainContext: serviceConfig.integration.getChainContext,
  trackDependency: serviceConfig.integration.trackDependency,
  addError: serviceConfig.integration.addError,
  getOutgoingHeaders: serviceConfig.integration.getOutgoingHeaders
};
`;
  }

  /**
   * Deploy integration to service
   */
  async deployToService(serviceName) {
    try {
      const service = this.services.get(serviceName);
      if (!service) {
        throw new Error(`Service ${serviceName} not found in registry`);
      }

      // Generate integration code
      const integrationCode = this.generateIntegrationCode(serviceName);

      // Create integration file path
      const servicePath = path.join(
        path.dirname(this.serviceRegistryPath),
        serviceName,
        'middleware',
        'flow-aware-integration.js'
      );

      // Ensure directory exists
      await fs.mkdir(path.dirname(servicePath), { recursive: true });

      // Write integration file
      await fs.writeFile(servicePath, integrationCode, 'utf8');

      this.logger.info('Integration deployed to service', {
        serviceName,
        integrationPath: servicePath
      });

      // Update service status
      service.status = 'integrated';

      return {
        serviceName,
        integrationPath: servicePath,
        success: true
      };

    } catch (error) {
      this.logger.error('Failed to deploy integration to service', {
        serviceName,
        error: error.message
      });

      const service = this.services.get(serviceName);
      if (service) {
        service.status = 'error';
      }

      return {
        serviceName,
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Deploy integration to all services
   */
  async deployToAllServices() {
    const results = [];

    for (const serviceName of this.services.keys()) {
      const result = await this.deployToService(serviceName);
      results.push(result);
    }

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    this.logger.info('Integration deployment completed', {
      total: results.length,
      successful: successful.length,
      failed: failed.length,
      failedServices: failed.map(r => r.serviceName)
    });

    return {
      total: results.length,
      successful: successful.length,
      failed: failed.length,
      results
    };
  }

  /**
   * Create HTTP client with flow tracking
   */
  createHttpClient(serviceName) {
    const axios = require('axios');
    const service = this.services.get(serviceName);

    if (!service) {
      throw new Error(`Service ${serviceName} not found in registry`);
    }

    // Create axios instance
    const client = axios.create({
      baseURL: `${service.protocol}://localhost:${service.port}`,
      timeout: 30000,
      headers: {
        'User-Agent': `${process.env.SERVICE_NAME || 'unknown'}-client/1.0`
      }
    });

    // Add request interceptor for flow tracking
    client.interceptors.request.use((config) => {
      // Add flow headers if available in current context
      const req = this.getCurrentRequest();
      if (req) {
        const outgoingHeaders = this.createServiceConfig(process.env.SERVICE_NAME || 'unknown')
          .integration.getOutgoingHeaders(req, serviceName);

        Object.assign(config.headers, outgoingHeaders);
      }

      return config;
    });

    // Add response interceptor for error tracking
    client.interceptors.response.use(
      (response) => response,
      (error) => {
        const req = this.getCurrentRequest();
        if (req) {
          this.createServiceConfig(process.env.SERVICE_NAME || 'unknown')
            .integration.addError(req, error, `http-client-${serviceName}`);
        }

        return Promise.reject(error);
      }
    );

    return client;
  }

  /**
   * Get current request context (simplified implementation)
   */
  getCurrentRequest() {
    // In a real implementation, this would use async local storage
    // or similar mechanism to get the current request context
    return null;
  }

  /**
   * Generate deployment script
   */
  generateDeploymentScript() {
    return `#!/bin/bash
# Flow-aware middleware deployment script
# Auto-generated by ServiceIntegration

echo "Deploying flow-aware middleware to all services..."

# Services to deploy
SERVICES=(${Array.from(this.services.keys()).map(s => `"${s}"`).join(' ')})

# Deploy to each service
for service in "\${SERVICES[@]}"; do
    echo "Deploying to \$service..."

    # Check if service is running
    if curl -f -s "http://localhost:\$(cat config/service-registry.json | jq -r ".services.\$service.port")/health" > /dev/null; then
        echo "✓ \$service is running"
    else
        echo "⚠ \$service is not running - deployment will be applied on next start"
    fi
done

echo "Deployment completed!"
`;
  }

  /**
   * Get integration status
   */
  getIntegrationStatus() {
    const status = {
      initialized: true,
      serviceCount: this.services.size,
      services: {},
      middleware: {
        flowTracker: !!this.flowTracker,
        chainContextManager: !!this.chainContextManager,
        metricsCollector: !!this.metricsCollector,
        eventPublisher: !!this.eventPublisher
      },
      metrics: {
        eventsPublished: this.eventPublisher?.getStats().eventsPublished || 0,
        metricsCollected: this.metricsCollector?.getAllMetrics() || {},
        activeFlows: 0
      }
    };

    // Service statuses
    for (const [name, service] of this.services.entries()) {
      status.services[name] = {
        name: service.name,
        port: service.port,
        critical: service.critical,
        status: service.status
      };
    }

    return status;
  }

  /**
   * Stop integration and cleanup
   */
  async stop() {
    if (this.metricsCollector) {
      this.metricsCollector.stop();
    }

    if (this.eventPublisher) {
      await this.eventPublisher.stop();
    }

    if (this.chainContextManager) {
      this.chainContextManager.stop();
    }

    this.services.clear();
    this.serviceRegistry = null;

    this.logger.info('Service integration stopped');
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Create ServiceIntegration instance
 */
function createServiceIntegration(options = {}) {
  return new ServiceIntegration(options);
}

/**
 * Quick setup function for Express.js applications
 */
function setupFlowAwareMiddleware(app, options = {}) {
  const integration = new ServiceIntegration(options);

  return integration.initialize().then(() => {
    const middlewareStack = integration.getMiddlewareStack();
    middlewareStack.forEach(middleware => app.use(middleware));

    return integration;
  });
}

// =============================================================================
// EXPORTS
// =============================================================================

module.exports = {
  ServiceIntegration,
  createServiceIntegration,
  setupFlowAwareMiddleware,
  MIDDLEWARE_CONFIG
};