const axios = require('axios');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class CentralHubClient {
  constructor() {
    this.hubUrl = process.env.CENTRAL_HUB_URL || 'http://localhost:8000';
    this.serviceId = null;
    this.heartbeatInterval = null;
    this.heartbeatFrequency = parseInt(process.env.HEARTBEAT_FREQUENCY) || 30000; // 30 seconds
    this.retryAttempts = 3;
    this.retryDelay = 5000; // 5 seconds
  }

  async registerService(serviceInfo) {
    try {
      const registrationData = {
        name: serviceInfo.name,
        type: 'database-service',
        port: serviceInfo.port,
        healthEndpoint: serviceInfo.health,
        endpoints: serviceInfo.endpoints,
        capabilities: [
          'user_management',
          'query_interface',
          'migrations',
          'health_monitoring'
        ],
        metadata: {
          database: 'PostgreSQL',
          version: '1.0.0',
          environment: process.env.NODE_ENV || 'development'
        },
        timestamp: new Date().toISOString()
      };

      const response = await this.makeRequest('post', '/api/services/register', registrationData);

      if (response.data && response.data.serviceId) {
        this.serviceId = response.data.serviceId;
        logger.info(`Registered with Central Hub, Service ID: ${this.serviceId}`);

        // Start heartbeat
        this.startHeartbeat();

        return response.data;
      } else {
        throw new Error('Invalid registration response');
      }
    } catch (error) {
      logger.error('Service registration failed:', error.message);
      throw error;
    }
  }

  async updateServiceStatus(status) {
    if (!this.serviceId) {
      logger.warn('Cannot update status: Service not registered');
      return;
    }

    try {
      const statusData = {
        serviceId: this.serviceId,
        status: status,
        timestamp: new Date().toISOString()
      };

      await this.makeRequest('put', `/api/services/${this.serviceId}/status`, statusData);
      logger.debug(`Status updated: ${status}`);
    } catch (error) {
      logger.error('Status update failed:', error.message);
    }
  }

  async sendHeartbeat() {
    if (!this.serviceId) {
      return;
    }

    try {
      const heartbeatData = {
        serviceId: this.serviceId,
        timestamp: new Date().toISOString(),
        metrics: await this.getServiceMetrics()
      };

      await this.makeRequest('post', `/api/services/${this.serviceId}/heartbeat`, heartbeatData);
      logger.debug('Heartbeat sent successfully');
    } catch (error) {
      logger.error('Heartbeat failed:', error.message);
    }
  }

  async getServiceMetrics() {
    try {
      const process = require('process');
      return {
        memory: {
          used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100,
          total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024 * 100) / 100
        },
        uptime: Math.round(process.uptime()),
        pid: process.pid,
        nodeVersion: process.version
      };
    } catch (error) {
      logger.error('Failed to get service metrics:', error);
      return {};
    }
  }

  async discoverServices(serviceType = null) {
    try {
      const params = serviceType ? { type: serviceType } : {};
      const response = await this.makeRequest('get', '/api/services/discover', null, { params });

      return response.data.services || [];
    } catch (error) {
      logger.error('Service discovery failed:', error.message);
      return [];
    }
  }

  async getServiceHealth(serviceId) {
    try {
      const response = await this.makeRequest('get', `/api/services/${serviceId}/health`);
      return response.data;
    } catch (error) {
      logger.error(`Failed to get health for service ${serviceId}:`, error.message);
      return null;
    }
  }

  async unregisterService() {
    if (!this.serviceId) {
      return;
    }

    try {
      await this.makeRequest('delete', `/api/services/${this.serviceId}`);
      logger.info('Service unregistered successfully');

      // Stop heartbeat
      this.stopHeartbeat();

      this.serviceId = null;
    } catch (error) {
      logger.error('Service unregistration failed:', error.message);
    }
  }

  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, this.heartbeatFrequency);

    logger.info(`Heartbeat started with frequency: ${this.heartbeatFrequency}ms`);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
      logger.info('Heartbeat stopped');
    }
  }

  async makeRequest(method, endpoint, data = null, config = {}) {
    let lastError;

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const requestConfig = {
          method,
          url: `${this.hubUrl}${endpoint}`,
          timeout: 10000,
          ...config
        };

        if (data) {
          requestConfig.data = data;
        }

        const response = await axios(requestConfig);
        return response;
      } catch (error) {
        lastError = error;

        if (attempt < this.retryAttempts) {
          logger.warn(`Request failed (attempt ${attempt}/${this.retryAttempts}), retrying in ${this.retryDelay}ms...`);
          await this.sleep(this.retryDelay);
        }
      }
    }

    throw lastError;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Graceful shutdown
  async shutdown() {
    logger.info('Shutting down Central Hub client...');
    this.stopHeartbeat();
    await this.unregisterService();
  }
}

module.exports = CentralHubClient;