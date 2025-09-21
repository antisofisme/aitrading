const axios = require('axios');
const WebSocket = require('ws');
const logger = require('./logger');
const config = require('../config/gateway.config');

class CentralHubClient {
  constructor() {
    this.connected = false;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 5000;
    this.heartbeatInterval = null;
    this.serviceId = null;
  }

  async connect() {
    try {
      const hubUrl = config.services.centralHub.url;
      logger.info(`Connecting to Central Hub at ${hubUrl}`);

      // First, register with HTTP API
      await this.registerWithHub();

      // Then establish WebSocket connection for real-time communication
      await this.connectWebSocket();

      this.connected = true;
      this.reconnectAttempts = 0;
      logger.info('Successfully connected to Central Hub');

    } catch (error) {
      logger.error('Failed to connect to Central Hub:', error);
      this.scheduleReconnect();
    }
  }

  async registerWithHub() {
    try {
      const registration = {
        name: 'api-gateway',
        type: 'gateway',
        host: config.server.host,
        port: config.server.port,
        health: `http://${config.server.host}:${config.server.port}/health`,
        status: `http://${config.server.host}:${config.server.port}/gateway/info`,
        version: '1.0.0',
        capabilities: [
          'routing',
          'authentication',
          'rate-limiting',
          'monitoring',
          'service-discovery'
        ],
        metadata: {
          environment: process.env.NODE_ENV || 'development',
          startTime: new Date().toISOString(),
          nodeVersion: process.version,
          platform: process.platform
        }
      };

      const response = await axios.post(
        `${config.services.centralHub.url}/api/services/register`,
        registration,
        {
          timeout: config.services.centralHub.timeout,
          headers: {
            'Content-Type': 'application/json',
            'X-Service-Token': process.env.SERVICE_TOKEN || 'dev-token'
          }
        }
      );

      this.serviceId = response.data.serviceId;
      logger.info(`Registered with Central Hub, service ID: ${this.serviceId}`);

      return response.data;
    } catch (error) {
      if (error.code === 'ECONNREFUSED') {
        logger.warn('Central Hub is not available, continuing without registration');
        return null;
      }
      throw error;
    }
  }

  async connectWebSocket() {
    try {
      const wsUrl = config.services.centralHub.url.replace('http', 'ws') + '/ws';

      this.ws = new WebSocket(wsUrl, {
        headers: {
          'X-Service-ID': this.serviceId,
          'X-Service-Type': 'gateway',
          'X-Service-Token': process.env.SERVICE_TOKEN || 'dev-token'
        }
      });

      this.ws.on('open', () => {
        logger.info('WebSocket connection to Central Hub established');
        this.startHeartbeat();
        this.sendStatus();
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          this.handleMessage(message);
        } catch (error) {
          logger.error('Failed to parse WebSocket message:', error);
        }
      });

      this.ws.on('close', (code, reason) => {
        logger.warn(`WebSocket connection closed: ${code} ${reason}`);
        this.connected = false;
        this.stopHeartbeat();
        this.scheduleReconnect();
      });

      this.ws.on('error', (error) => {
        logger.error('WebSocket error:', error);
        this.connected = false;
      });

    } catch (error) {
      logger.error('Failed to establish WebSocket connection:', error);
      throw error;
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case 'ping':
        this.sendMessage({ type: 'pong', timestamp: Date.now() });
        break;

      case 'service_discovery':
        this.handleServiceDiscovery(message);
        break;

      case 'configuration_update':
        this.handleConfigurationUpdate(message);
        break;

      case 'health_check_request':
        this.handleHealthCheckRequest(message);
        break;

      case 'system_alert':
        this.handleSystemAlert(message);
        break;

      default:
        logger.debug(`Received unknown message type: ${message.type}`);
    }
  }

  handleServiceDiscovery(message) {
    logger.info('Received service discovery update:', message.services);
    // Update local service registry with discovered services
    // This could trigger dynamic route updates
  }

  handleConfigurationUpdate(message) {
    logger.info('Received configuration update:', message.config);
    // Handle dynamic configuration updates
    // This could update rate limits, CORS settings, etc.
  }

  async handleHealthCheckRequest(message) {
    try {
      const health = await this.getGatewayHealth();
      this.sendMessage({
        type: 'health_check_response',
        requestId: message.requestId,
        health
      });
    } catch (error) {
      logger.error('Failed to respond to health check request:', error);
    }
  }

  handleSystemAlert(message) {
    logger.warn('System alert received:', message.alert);
    // Handle system-wide alerts (security issues, service outages, etc.)
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        ...message,
        serviceId: this.serviceId,
        timestamp: Date.now()
      }));
    }
  }

  async sendStatus() {
    try {
      const status = await this.getGatewayStatus();
      this.sendMessage({
        type: 'status_update',
        status
      });
    } catch (error) {
      logger.error('Failed to send status update:', error);
    }
  }

  async getGatewayHealth() {
    return {
      status: 'healthy',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      timestamp: new Date().toISOString()
    };
  }

  async getGatewayStatus() {
    return {
      uptime: process.uptime(),
      connections: this.getActiveConnections(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      requestsPerMinute: this.getRequestsPerMinute(),
      timestamp: new Date().toISOString()
    };
  }

  getActiveConnections() {
    // This would typically be tracked by the server
    return process._getActiveHandles().length;
  }

  getRequestsPerMinute() {
    // This would typically be tracked by metrics middleware
    return 0; // Placeholder
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.sendMessage({ type: 'heartbeat' });
      }
    }, 30000); // 30 seconds
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectInterval * this.reconnectAttempts;

      logger.info(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);

      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      logger.error('Max reconnect attempts reached, giving up on Central Hub connection');
    }
  }

  async registerService(serviceInfo) {
    try {
      if (!this.connected) {
        logger.warn('Not connected to Central Hub, cannot register service');
        return false;
      }

      this.sendMessage({
        type: 'service_registration',
        service: serviceInfo
      });

      return true;
    } catch (error) {
      logger.error('Failed to register service with Central Hub:', error);
      return false;
    }
  }

  async unregisterService(serviceName) {
    try {
      if (!this.connected) {
        logger.warn('Not connected to Central Hub, cannot unregister service');
        return false;
      }

      this.sendMessage({
        type: 'service_unregistration',
        serviceName
      });

      return true;
    } catch (error) {
      logger.error('Failed to unregister service from Central Hub:', error);
      return false;
    }
  }

  async reportMetrics(metrics) {
    try {
      if (!this.connected) return false;

      this.sendMessage({
        type: 'metrics_report',
        metrics
      });

      return true;
    } catch (error) {
      logger.error('Failed to report metrics to Central Hub:', error);
      return false;
    }
  }

  async disconnect() {
    try {
      this.connected = false;
      this.stopHeartbeat();

      if (this.ws) {
        this.ws.close(1000, 'Gateway shutdown');
        this.ws = null;
      }

      // Unregister from Central Hub
      if (this.serviceId) {
        await axios.delete(
          `${config.services.centralHub.url}/api/services/${this.serviceId}`,
          {
            timeout: 5000,
            headers: {
              'X-Service-Token': process.env.SERVICE_TOKEN || 'dev-token'
            }
          }
        );
      }

      logger.info('Disconnected from Central Hub');
    } catch (error) {
      logger.error('Error during Central Hub disconnect:', error);
    }
  }
}

module.exports = CentralHubClient;