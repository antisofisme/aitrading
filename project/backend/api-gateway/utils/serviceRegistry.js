const axios = require('axios');
const config = require('../config/config');
const logger = require('./logger');

/**
 * Service Registry client for API Gateway
 * Handles registration with Central Hub and service discovery
 */
class ServiceRegistry {
  constructor() {
    this.registrationData = null;
    this.heartbeatInterval = null;
    this.registryUrl = config.registry.hubUrl;
  }

  /**
   * Register this API Gateway with the Central Hub
   */
  async register(serviceInfo) {
    try {
      const registrationPayload = {
        ...serviceInfo,
        type: 'api-gateway',
        version: '1.0.0',
        phase: 'phase-1',
        registeredAt: new Date().toISOString(),
        metadata: {
          environment: config.environment,
          capabilities: [
            'routing',
            'authentication',
            'rate-limiting',
            'cors',
            'health-checks'
          ],
          endpoints: {
            health: '/health',
            ready: '/health/ready',
            live: '/health/live',
            metrics: '/health/metrics'
          }
        }
      };

      const response = await axios.post(
        `${this.registryUrl}${config.registry.registrationPath}`,
        registrationPayload,
        {
          timeout: 10000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Type': 'api-gateway'
          }
        }
      );

      if (response.data && response.data.success) {
        this.registrationData = {
          ...registrationPayload,
          registrationId: response.data.registrationId,
          registeredAt: response.data.registeredAt
        };

        logger.info('Successfully registered with Central Hub', {
          registrationId: response.data.registrationId,
          hubUrl: this.registryUrl
        });

        // Start heartbeat
        this.startHeartbeat();

        return true;
      } else {
        throw new Error('Registration failed: Invalid response from hub');
      }
    } catch (error) {
      logger.error('Failed to register with Central Hub:', {
        error: error.message,
        hubUrl: this.registryUrl,
        stack: error.stack
      });

      // In Phase 1, we can continue without registration but log the issue
      logger.warn('Continuing without Central Hub registration - operating in standalone mode');
      return false;
    }
  }

  /**
   * Start sending heartbeat signals to Central Hub
   */
  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }

    this.heartbeatInterval = setInterval(async () => {
      try {
        await this.sendHeartbeat();
      } catch (error) {
        logger.warn('Heartbeat failed:', error.message);
      }
    }, config.registry.heartbeatInterval);

    logger.info('Heartbeat started', {
      interval: config.registry.heartbeatInterval
    });
  }

  /**
   * Send heartbeat to Central Hub
   */
  async sendHeartbeat() {
    if (!this.registrationData) {
      return;
    }

    try {
      const heartbeatData = {
        registrationId: this.registrationData.registrationId,
        timestamp: new Date().toISOString(),
        status: 'healthy',
        metrics: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          cpu: process.cpuUsage()
        }
      };

      const response = await axios.post(
        `${this.registryUrl}/api/registry/heartbeat`,
        heartbeatData,
        {
          timeout: 5000,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Type': 'api-gateway'
          }
        }
      );

      logger.debug('Heartbeat sent successfully');
    } catch (error) {
      logger.warn('Heartbeat failed:', error.message);
      // Consider implementing retry logic or re-registration here
    }
  }

  /**
   * Discover available services from Central Hub
   */
  async discoverServices() {
    try {
      const response = await axios.get(
        `${this.registryUrl}/api/registry/services`,
        {
          timeout: 5000,
          headers: {
            'X-Service-Type': 'api-gateway'
          }
        }
      );

      if (response.data && response.data.services) {
        logger.info('Discovered services:', {
          count: response.data.services.length,
          services: response.data.services.map(s => s.name)
        });

        return response.data.services;
      }

      return [];
    } catch (error) {
      logger.warn('Service discovery failed:', error.message);
      return [];
    }
  }

  /**
   * Unregister from Central Hub (called during shutdown)
   */
  async unregister() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }

    if (!this.registrationData) {
      return;
    }

    try {
      await axios.delete(
        `${this.registryUrl}/api/registry/services/${this.registrationData.registrationId}`,
        {
          timeout: 5000,
          headers: {
            'X-Service-Type': 'api-gateway'
          }
        }
      );

      logger.info('Successfully unregistered from Central Hub');
    } catch (error) {
      logger.warn('Failed to unregister from Central Hub:', error.message);
    }
  }

  /**
   * Get current registration status
   */
  getRegistrationStatus() {
    return {
      registered: !!this.registrationData,
      registrationData: this.registrationData,
      heartbeatActive: !!this.heartbeatInterval
    };
  }
}

module.exports = new ServiceRegistry();