const axios = require('axios');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

class HubIntegration {
  constructor() {
    this.hubUrl = process.env.CENTRAL_HUB_URL || 'http://localhost:8000';
    this.serviceName = 'database-service';
    this.servicePort = process.env.PORT || 8008;
    this.registrationInterval = null;
    this.heartbeatInterval = null;
  }

  async registerWithHub() {
    try {
      const registrationData = {
        name: this.serviceName,
        type: 'database',
        host: process.env.SERVICE_HOST || 'localhost',
        port: this.servicePort,
        health_endpoint: '/health',
        version: process.env.npm_package_version || '1.0.0',
        capabilities: [
          'user_authentication',
          'query_execution',
          'transaction_support',
          'schema_management'
        ],
        metadata: {
          database_type: 'postgresql',
          max_connections: process.env.DB_POOL_MAX || 20,
          supports_transactions: true,
          supports_migrations: true
        }
      };

      const response = await axios.post(
        `${this.hubUrl}/api/services/register`,
        registrationData,
        {
          timeout: 5000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Name': this.serviceName
          }
        }
      );

      logger.info('Successfully registered with Central Hub', {
        hubUrl: this.hubUrl,
        serviceId: response.data.serviceId
      });

      return response.data;

    } catch (error) {
      logger.error('Failed to register with Central Hub:', {
        error: error.message,
        hubUrl: this.hubUrl
      });
      throw error;
    }
  }

  async sendHeartbeat(healthData) {
    try {
      const heartbeatData = {
        service: this.serviceName,
        status: healthData.status,
        timestamp: new Date().toISOString(),
        metrics: {
          uptime: healthData.uptime.seconds,
          database_status: healthData.database.status,
          connection_pool: healthData.database.poolStats,
          error_rate: healthData.metrics ?
            (healthData.metrics.errorCount / Math.max(healthData.metrics.totalQueries, 1)) * 100 : 0
        }
      };

      await axios.post(
        `${this.hubUrl}/api/services/heartbeat`,
        heartbeatData,
        {
          timeout: 3000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Name': this.serviceName
          }
        }
      );

      logger.debug('Heartbeat sent to Central Hub');

    } catch (error) {
      logger.warn('Failed to send heartbeat to Central Hub:', {
        error: error.message
      });
    }
  }

  async notifyServiceEvent(event, data = {}) {
    try {
      const eventData = {
        service: this.serviceName,
        event,
        data,
        timestamp: new Date().toISOString()
      };

      await axios.post(
        `${this.hubUrl}/api/services/events`,
        eventData,
        {
          timeout: 3000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Name': this.serviceName
          }
        }
      );

      logger.info('Service event sent to Central Hub', { event, data });

    } catch (error) {
      logger.warn('Failed to send service event:', {
        event,
        error: error.message
      });
    }
  }

  async getServiceConfiguration() {
    try {
      const response = await axios.get(
        `${this.hubUrl}/api/services/${this.serviceName}/config`,
        {
          timeout: 5000,
          headers: {
            'X-Service-Name': this.serviceName
          }
        }
      );

      logger.info('Retrieved service configuration from Central Hub');
      return response.data;

    } catch (error) {
      logger.warn('Failed to get service configuration:', {
        error: error.message
      });
      return null;
    }
  }

  startHeartbeat(healthService) {
    // Send heartbeat every 30 seconds
    this.heartbeatInterval = setInterval(async () => {
      try {
        const healthData = await healthService.getDetailedHealth();
        await this.sendHeartbeat(healthData);
      } catch (error) {
        logger.error('Heartbeat failed:', error);
      }
    }, 30000);

    logger.info('Heartbeat started');
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
      logger.info('Heartbeat stopped');
    }
  }

  async deregisterFromHub() {
    try {
      await axios.delete(
        `${this.hubUrl}/api/services/${this.serviceName}`,
        {
          timeout: 5000,
          headers: {
            'X-Service-Name': this.serviceName
          }
        }
      );

      logger.info('Successfully deregistered from Central Hub');

    } catch (error) {
      logger.warn('Failed to deregister from Central Hub:', {
        error: error.message
      });
    }
  }

  async discoverServices(serviceType = null) {
    try {
      let url = `${this.hubUrl}/api/services`;
      if (serviceType) {
        url += `?type=${serviceType}`;
      }

      const response = await axios.get(url, {
        timeout: 5000,
        headers: {
          'X-Service-Name': this.serviceName
        }
      });

      return response.data.services || [];

    } catch (error) {
      logger.error('Failed to discover services:', {
        error: error.message
      });
      return [];
    }
  }
}

module.exports = HubIntegration;