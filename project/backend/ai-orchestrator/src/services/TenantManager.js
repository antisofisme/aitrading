/**
 * Tenant Manager - Multi-tenant isolation and management
 * Handles tenant-specific AI model deployment and performance tracking
 */

class TenantManager {
  constructor(logger) {
    this.logger = logger;
    this.tenants = new Map();
    this.tenantMetrics = new Map();
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // Initialize tenant storage
      this.initializeTenantStorage();
      
      this.isInitialized = true;
      this.logger.info('Tenant Manager initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Tenant Manager', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  initializeTenantStorage() {
    // Initialize with default tenant for development
    const defaultTenant = {
      id: 'default',
      name: 'Default Tenant',
      created: Date.now(),
      status: 'active',
      config: {
        aiModelsLimit: 10,
        concurrentInferences: 5,
        dataRetentionDays: 30
      },
      resources: {
        allocatedCPU: 2,
        allocatedMemory: '4GB',
        storageQuota: '10GB'
      }
    };

    this.tenants.set('default', defaultTenant);
    this.tenantMetrics.set('default', {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageResponseTime: 0,
      aiAccuracy: 0.7,
      activeModels: 0,
      lastActivity: Date.now()
    });
  }

  async getTenantDashboard(tenantId) {
    try {
      const tenant = this.tenants.get(tenantId);
      const metrics = this.tenantMetrics.get(tenantId);

      if (!tenant) {
        throw new Error(`Tenant ${tenantId} not found`);
      }

      const dashboard = {
        tenant: {
          id: tenant.id,
          name: tenant.name,
          status: tenant.status,
          created: tenant.created
        },
        performance: {
          totalRequests: metrics.totalRequests,
          successfulRequests: metrics.successfulRequests,
          failedRequests: metrics.failedRequests,
          successRate: metrics.totalRequests > 0 
            ? (metrics.successfulRequests / metrics.totalRequests) * 100 
            : 0,
          averageResponseTime: metrics.averageResponseTime,
          lastActivity: metrics.lastActivity
        },
        ai: {
          averageAIAccuracy: metrics.aiAccuracy,
          activeModels: metrics.activeModels,
          averageInferenceTime: metrics.averageResponseTime
        },
        resources: {
          allocatedCPU: tenant.resources.allocatedCPU,
          allocatedMemory: tenant.resources.allocatedMemory,
          storageQuota: tenant.resources.storageQuota,
          currentUsage: {
            cpu: Math.random() * tenant.resources.allocatedCPU,
            memory: `${Math.round(Math.random() * 3)}GB`,
            storage: `${Math.round(Math.random() * 8)}GB`
          }
        },
        serviceAvailability: 0.99, // Mock for now
        compliance: {
          dataEncryption: true,
          auditLogging: true,
          accessControl: true
        }
      };

      return dashboard;

    } catch (error) {
      this.logger.error('Failed to get tenant dashboard', {
        tenantId,
        error: error.message
      });
      throw error;
    }
  }

  async updateTenantMetrics(tenantId, requestData) {
    try {
      const metrics = this.tenantMetrics.get(tenantId);
      
      if (!metrics) {
        // Create new tenant metrics if doesn't exist
        this.tenantMetrics.set(tenantId, {
          totalRequests: 1,
          successfulRequests: requestData.success ? 1 : 0,
          failedRequests: requestData.success ? 0 : 1,
          averageResponseTime: requestData.responseTime || 0,
          aiAccuracy: requestData.accuracy || 0.7,
          activeModels: 1,
          lastActivity: Date.now()
        });
        return;
      }

      // Update existing metrics
      metrics.totalRequests++;
      if (requestData.success) {
        metrics.successfulRequests++;
      } else {
        metrics.failedRequests++;
      }

      // Update average response time
      if (requestData.responseTime) {
        metrics.averageResponseTime = 
          (metrics.averageResponseTime * (metrics.totalRequests - 1) + requestData.responseTime) / metrics.totalRequests;
      }

      // Update AI accuracy
      if (requestData.accuracy) {
        metrics.aiAccuracy = 
          (metrics.aiAccuracy * (metrics.totalRequests - 1) + requestData.accuracy) / metrics.totalRequests;
      }

      metrics.lastActivity = Date.now();

      this.tenantMetrics.set(tenantId, metrics);

    } catch (error) {
      this.logger.error('Failed to update tenant metrics', {
        tenantId,
        error: error.message
      });
    }
  }

  async createTenant(tenantData) {
    try {
      const tenantId = tenantData.id || this.generateTenantId();
      
      const tenant = {
        id: tenantId,
        name: tenantData.name,
        created: Date.now(),
        status: 'active',
        config: {
          aiModelsLimit: tenantData.aiModelsLimit || 5,
          concurrentInferences: tenantData.concurrentInferences || 3,
          dataRetentionDays: tenantData.dataRetentionDays || 30
        },
        resources: {
          allocatedCPU: tenantData.allocatedCPU || 1,
          allocatedMemory: tenantData.allocatedMemory || '2GB',
          storageQuota: tenantData.storageQuota || '5GB'
        }
      };

      this.tenants.set(tenantId, tenant);
      this.tenantMetrics.set(tenantId, {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTime: 0,
        aiAccuracy: 0.7,
        activeModels: 0,
        lastActivity: Date.now()
      });

      this.logger.info('Tenant created successfully', { tenantId, name: tenant.name });
      return tenant;

    } catch (error) {
      this.logger.error('Failed to create tenant', {
        error: error.message,
        tenantData
      });
      throw error;
    }
  }

  async getTenant(tenantId) {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) {
      throw new Error(`Tenant ${tenantId} not found`);
    }
    return tenant;
  }

  async listTenants() {
    return Array.from(this.tenants.values());
  }

  async validateTenantAccess(tenantId, userId) {
    // Simple validation for development
    const tenant = this.tenants.get(tenantId);
    if (!tenant) {
      return { valid: false, reason: 'Tenant not found' };
    }

    if (tenant.status !== 'active') {
      return { valid: false, reason: 'Tenant is not active' };
    }

    return { valid: true };
  }

  async checkResourceQuota(tenantId, resourceType, requestedAmount) {
    const tenant = this.tenants.get(tenantId);
    if (!tenant) {
      return { allowed: false, reason: 'Tenant not found' };
    }

    // Mock quota checking
    const quotas = {
      'ai-models': tenant.config.aiModelsLimit,
      'concurrent-inferences': tenant.config.concurrentInferences,
      'cpu': tenant.resources.allocatedCPU,
      'memory': parseInt(tenant.resources.allocatedMemory) || 2
    };

    const currentUsage = this.getCurrentResourceUsage(tenantId, resourceType);
    const quota = quotas[resourceType] || 1;

    if (currentUsage + requestedAmount > quota) {
      return {
        allowed: false,
        reason: `Resource quota exceeded. Current: ${currentUsage}, Requested: ${requestedAmount}, Limit: ${quota}`
      };
    }

    return { allowed: true };
  }

  getCurrentResourceUsage(tenantId, resourceType) {
    const metrics = this.tenantMetrics.get(tenantId);
    if (!metrics) return 0;

    // Mock current usage
    switch (resourceType) {
      case 'ai-models':
        return metrics.activeModels;
      case 'concurrent-inferences':
        return Math.floor(Math.random() * 3); // Mock concurrent usage
      case 'cpu':
        return Math.random() * 2; // Mock CPU usage
      case 'memory':
        return Math.random() * 2; // Mock memory usage
      default:
        return 0;
    }
  }

  generateTenantId() {
    return `tenant_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  isHealthy() {
    return this.isInitialized;
  }

  getMetrics() {
    const totalTenants = this.tenants.size;
    const activeTenants = Array.from(this.tenants.values())
      .filter(t => t.status === 'active').length;
    
    const totalRequests = Array.from(this.tenantMetrics.values())
      .reduce((sum, metrics) => sum + metrics.totalRequests, 0);
    
    return {
      totalTenants,
      activeTenants,
      totalRequests,
      averageAccuracy: this.calculateOverallAccuracy()
    };
  }

  calculateOverallAccuracy() {
    const metricsArray = Array.from(this.tenantMetrics.values());
    if (metricsArray.length === 0) return 0;

    const totalAccuracy = metricsArray.reduce((sum, metrics) => sum + metrics.aiAccuracy, 0);
    return totalAccuracy / metricsArray.length;
  }
}

module.exports = TenantManager;