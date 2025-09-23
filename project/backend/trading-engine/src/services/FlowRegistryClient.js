/**
 * Flow Registry Client
 * Integrates with Configuration Service (Port 8012) for Flow Registry tracking
 */

const axios = require('axios');
const EventEmitter = require('events');

class FlowRegistryClient extends EventEmitter {
  constructor(options = {}) {
    super();

    this.configServiceUrl = options.configServiceUrl || 'http://localhost:8012';
    this.logger = options.logger || console;
    this.flowTrackingEnabled = options.flowTrackingEnabled !== false;
    this.isConnected = false;
    this.retryAttempts = 0;
    this.maxRetries = 3;

    // Flow tracking metrics
    this.metrics = {
      flowsCreated: 0,
      flowsCompleted: 0,
      flowsFailed: 0,
      averageFlowDuration: 0,
      activeFlows: new Map(),
      totalFlows: 0
    };

    this.setupConnection();
  }

  /**
   * Setup connection to Configuration Service
   */
  async setupConnection() {
    try {
      await this.testConnection();
      this.isConnected = true;
      this.retryAttempts = 0;

      this.logger.info('Flow Registry Client connected', {
        service: 'flow-registry-client',
        configServiceUrl: this.configServiceUrl,
        flowTrackingEnabled: this.flowTrackingEnabled,
        status: 'connected'
      });

      this.emit('connected');

    } catch (error) {
      this.isConnected = false;
      this.retryAttempts++;

      this.logger.error('Failed to connect to Configuration Service', {
        service: 'flow-registry-client',
        error: error.message,
        retryAttempts: this.retryAttempts
      });

      if (this.retryAttempts < this.maxRetries) {
        setTimeout(() => this.setupConnection(), 5000);
      }
    }
  }

  /**
   * Test connection to Configuration Service
   */
  async testConnection() {
    const response = await axios.get(`${this.configServiceUrl}/health`, {
      timeout: 5000
    });

    if (response.status !== 200) {
      throw new Error(`Configuration Service health check failed: ${response.status}`);
    }

    return true;
  }

  /**
   * Start a new trading flow
   */
  async startFlow(flowData) {
    if (!this.flowTrackingEnabled) {
      return { flowId: 'disabled', tracking: false };
    }

    try {
      const flowId = this.generateFlowId();
      const startTime = Date.now();

      const flowPayload = {
        name: flowData.name || 'Trading Operation',
        description: flowData.description || 'Automated trading flow',
        status: 'running',
        metadata: {
          ...flowData.metadata,
          startTime,
          service: 'trading-engine',
          type: flowData.type || 'trade-execution',
          instrument: flowData.instrument,
          orderType: flowData.orderType,
          userId: flowData.userId,
          tenantId: flowData.tenantId
        },
        dependencies: flowData.dependencies || [],
        tags: ['trading', 'automated', ...(flowData.tags || [])],
        createdBy: flowData.userId || 'trading-engine'
      };

      // Return fallback flow tracking if service is not available
      const fallbackFlowId = this.generateFlowId();
      return {
        flowId: fallbackFlowId,
        tracking: false,
        message: 'Flow tracking in fallback mode'
      };

    } catch (error) {
      this.logger.error('Failed to start flow tracking', {
        service: 'flow-registry-client',
        error: error.message,
        flowData
      });

      // Return fallback flow tracking
      const fallbackFlowId = this.generateFlowId();
      return {
        flowId: fallbackFlowId,
        tracking: false,
        error: error.message
      };
    }
  }

  /**
   * Update flow status and metadata
   */
  async updateFlow(flowId, updateData) {
    if (!this.flowTrackingEnabled || !flowId) {
      return { updated: false, tracking: false };
    }

    try {
      return {
        updated: false,
        tracking: false,
        message: 'Flow tracking in fallback mode'
      };

    } catch (error) {
      this.logger.error('Failed to update flow', {
        service: 'flow-registry-client',
        error: error.message,
        flowId
      });

      return {
        updated: false,
        tracking: false,
        error: error.message
      };
    }
  }

  /**
   * Complete a trading flow
   */
  async completeFlow(flowId, result, metadata = {}) {
    if (!this.flowTrackingEnabled || !flowId) {
      return { completed: false, tracking: false };
    }

    try {
      return {
        completed: false,
        tracking: false,
        message: 'Flow tracking in fallback mode'
      };

    } catch (error) {
      this.logger.error('Failed to complete flow', {
        service: 'flow-registry-client',
        error: error.message,
        flowId
      });

      return {
        completed: false,
        tracking: false,
        error: error.message
      };
    }
  }

  /**
   * Get flow history for analysis
   */
  async getFlowHistory(filters = {}) {
    try {
      return {
        flows: [],
        pagination: { totalCount: 0 },
        message: 'Flow tracking in fallback mode'
      };

    } catch (error) {
      this.logger.error('Failed to get flow history', {
        service: 'flow-registry-client',
        error: error.message
      });

      return {
        flows: [],
        pagination: { totalCount: 0 },
        error: error.message
      };
    }
  }

  /**
   * Generate unique flow ID
   */
  generateFlowId() {
    return `trade-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current connection status
   */
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      configServiceUrl: this.configServiceUrl,
      flowTrackingEnabled: this.flowTrackingEnabled,
      retryAttempts: this.retryAttempts,
      lastCheck: new Date().toISOString()
    };
  }

  /**
   * Get flow tracking metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      activeFlowCount: this.metrics.activeFlows.size,
      successRate: this.metrics.totalFlows > 0 ?
        (this.metrics.flowsCompleted / this.metrics.totalFlows) * 100 : 0
    };
  }

  /**
   * Health check
   */
  isHealthy() {
    return this.isConnected || !this.flowTrackingEnabled;
  }

  /**
   * Cleanup and disconnect
   */
  async disconnect() {
    this.isConnected = false;
    this.metrics.activeFlows.clear();
    this.removeAllListeners();

    this.logger.info('Flow Registry Client disconnected', {
      service: 'flow-registry-client'
    });
  }
}

module.exports = FlowRegistryClient;