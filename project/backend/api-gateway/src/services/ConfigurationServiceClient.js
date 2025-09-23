/**
 * Configuration Service Client
 *
 * Client for interacting with the Configuration Service and Flow Registry
 */

const axios = require('axios');
const EventEmitter = require('events');
const winston = require('winston');

class ConfigurationServiceClient extends EventEmitter {
  constructor(options = {}) {
    super();

    this.baseURL = options.baseURL || process.env.FLOW_REGISTRY_URL || 'http://configuration-service:8012';
    this.timeout = options.timeout || 30000;
    this.retryAttempts = options.retryAttempts || 3;
    this.retryDelay = options.retryDelay || 1000;

    this.logger = options.logger || winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'logs/config-service-client.log' })
      ]
    });

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'APIGateway-ConfigServiceClient/1.0.0'
      }
    });

    this.setupInterceptors();
    this.isConnected = false;
    this.lastHealthCheck = null;
  }

  /**
   * Setup request and response interceptors
   */
  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        config.headers['x-request-id'] = this.generateRequestId();
        config.headers['x-service'] = 'api-gateway';

        this.emit('request', {
          method: config.method,
          url: config.url,
          headers: config.headers
        });

        return config;
      },
      (error) => {
        this.emit('error', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => {
        this.isConnected = true;
        this.emit('response', {
          status: response.status,
          data: response.data
        });
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (
          error.response?.status >= 500 &&
          originalRequest._retryCount < this.retryAttempts
        ) {
          originalRequest._retryCount = (originalRequest._retryCount || 0) + 1;

          this.emit('retry', {
            attempt: originalRequest._retryCount,
            maxAttempts: this.retryAttempts,
            error: error.message
          });

          const delay = this.retryDelay * Math.pow(2, originalRequest._retryCount - 1);
          await this.sleep(delay);

          return this.client(originalRequest);
        }

        if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
          this.isConnected = false;
        }

        this.emit('error', error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Initialize connection to Configuration Service
   */
  async initialize() {
    try {
      await this.healthCheck();
      this.logger.info('Configuration Service client initialized', {
        baseURL: this.baseURL,
        isConnected: this.isConnected
      });
      return true;
    } catch (error) {
      this.logger.error('Failed to initialize Configuration Service client', {
        error: error.message,
        baseURL: this.baseURL
      });
      return false;
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/health');
      this.isConnected = true;
      this.lastHealthCheck = new Date();

      this.logger.debug('Configuration Service health check successful', {
        status: response.data
      });

      return response.data;
    } catch (error) {
      this.isConnected = false;
      this.logger.warn('Configuration Service health check failed', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Register API Gateway service with Configuration Service
   */
  async registerService() {
    try {
      const serviceInfo = {
        name: 'api-gateway',
        version: '1.0.0',
        host: process.env.SERVICE_HOST || 'api-gateway',
        port: process.env.PORT || 3001,
        protocol: 'http',
        healthEndpoint: '/health',
        capabilities: [
          'authentication',
          'rate_limiting',
          'request_routing',
          'error_handling',
          'flow_integration'
        ],
        metadata: {
          registeredAt: new Date(),
          environment: process.env.NODE_ENV || 'development'
        }
      };

      const response = await this.client.post('/api/v1/services/register', serviceInfo);

      this.logger.info('API Gateway registered with Configuration Service', {
        serviceId: response.data.data?.id
      });

      return response.data;
    } catch (error) {
      this.logger.error('Failed to register API Gateway with Configuration Service', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Get configuration value
   */
  async getConfiguration(key, options = {}) {
    try {
      const params = new URLSearchParams({
        key,
        environment: options.environment || process.env.NODE_ENV || 'development',
        ...(options.tenantId && { tenantId: options.tenantId }),
        ...(options.userId && { userId: options.userId })
      });

      const response = await this.client.get(`/api/v1/config?${params}`);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to get configuration', {
        error: error.message,
        key,
        options
      });
      throw error;
    }
  }

  /**
   * Set configuration value
   */
  async setConfiguration(configData) {
    try {
      const response = await this.client.post('/api/v1/config', configData);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to set configuration', {
        error: error.message,
        configData
      });
      throw error;
    }
  }

  /**
   * Discover service
   */
  async discoverService(serviceName) {
    try {
      const response = await this.client.get(`/api/v1/services/discover/${serviceName}`);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to discover service', {
        error: error.message,
        serviceName
      });
      throw error;
    }
  }

  /**
   * List available services
   */
  async listServices() {
    try {
      const response = await this.client.get('/api/v1/services');
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to list services', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Register flow with Flow Registry
   */
  async registerFlow(flowDefinition) {
    try {
      const response = await this.client.post('/api/v1/flows', flowDefinition);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to register flow', {
        error: error.message,
        flowName: flowDefinition.name
      });
      throw error;
    }
  }

  /**
   * Get flow by ID
   */
  async getFlow(flowId) {
    try {
      const response = await this.client.get(`/api/v1/flows/${flowId}`);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to get flow', {
        error: error.message,
        flowId
      });
      throw error;
    }
  }

  /**
   * Execute flow
   */
  async executeFlow(flowId, parameters = {}) {
    try {
      const response = await this.client.post(`/api/v1/flows/${flowId}/execute`, {
        parameters
      });
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to execute flow', {
        error: error.message,
        flowId,
        parameters
      });
      throw error;
    }
  }

  /**
   * Get tenant configuration
   */
  async getTenantConfig(tenantId) {
    try {
      const response = await this.client.get(`/api/v1/tenants/${tenantId}/config`);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to get tenant configuration', {
        error: error.message,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Update tenant configuration
   */
  async updateTenantConfig(tenantId, configData) {
    try {
      const response = await this.client.put(`/api/v1/tenants/${tenantId}/config`, configData);
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to update tenant configuration', {
        error: error.message,
        tenantId,
        configData
      });
      throw error;
    }
  }

  /**
   * Get service statistics
   */
  async getServiceStatistics() {
    try {
      const response = await this.client.get('/api/v1/services/statistics');
      return response.data.data;
    } catch (error) {
      this.logger.error('Failed to get service statistics', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Get connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      baseURL: this.baseURL,
      lastHealthCheck: this.lastHealthCheck,
      timestamp: new Date()
    };
  }

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `api-gw_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Close client and cleanup
   */
  close() {
    this.removeAllListeners();
    this.logger.info('Configuration Service client closed');
  }
}

module.exports = ConfigurationServiceClient;