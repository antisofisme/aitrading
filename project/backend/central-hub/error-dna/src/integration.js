const axios = require('axios');

class SystemIntegration {
  constructor(config = {}) {
    this.config = {
      centralHub: {
        baseUrl: 'http://localhost:3001',
        apiKey: null,
        timeout: 10000,
        ...config.centralHub
      },
      importManager: {
        baseUrl: 'http://localhost:3003',
        apiKey: null,
        timeout: 10000,
        ...config.importManager
      },
      ...config
    };

    this.integrationStats = {
      centralHub: { requests: 0, errors: 0, lastContact: null },
      importManager: { requests: 0, errors: 0, lastContact: null }
    };
  }

  /**
   * Register ErrorDNA with Central Hub
   * @returns {Promise<Object>} - Registration result
   */
  async registerWithCentralHub() {
    try {
      const registrationData = {
        serviceName: 'ErrorDNA',
        version: '1.0.0',
        capabilities: [
          'error_categorization',
          'pattern_detection',
          'error_recovery',
          'notification_management'
        ],
        endpoints: {
          health: '/health',
          errors: '/api/errors',
          patterns: '/api/patterns',
          metrics: '/api/metrics'
        },
        integrationVersion: '1.0'
      };

      const response = await this._makeRequest('centralHub', 'POST', '/api/services/register', registrationData);

      return {
        success: true,
        serviceId: response.data.serviceId,
        registrationTime: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to register with Central Hub:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Send error data to Central Hub
   * @param {Object} errorData - Error data to send
   * @returns {Promise<Object>} - Send result
   */
  async sendErrorToCentralHub(errorData) {
    try {
      const payload = {
        source: 'ErrorDNA',
        timestamp: new Date().toISOString(),
        error: {
          id: errorData.id,
          category: errorData.categorization?.category,
          subcategory: errorData.categorization?.subcategory,
          severity: errorData.categorization?.severity,
          message: errorData.originalError?.message,
          stack: errorData.originalError?.stack,
          code: errorData.originalError?.code
        },
        patterns: errorData.patterns?.map(p => ({
          id: p.id,
          description: p.description,
          occurrences: p.occurrences
        })) || [],
        recovery: errorData.recovery || null,
        metadata: {
          confidence: errorData.categorization?.confidence,
          tags: errorData.categorization?.tags,
          processed: true
        }
      };

      const response = await this._makeRequest('centralHub', 'POST', '/api/errors', payload);

      return {
        success: true,
        centralHubId: response.data.id,
        acknowledgment: response.data.acknowledgment
      };
    } catch (error) {
      console.error('Failed to send error to Central Hub:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get system configuration from Central Hub
   * @returns {Promise<Object>} - Configuration data
   */
  async getSystemConfiguration() {
    try {
      const response = await this._makeRequest('centralHub', 'GET', '/api/configuration/error-dna');

      return {
        success: true,
        configuration: response.data
      };
    } catch (error) {
      console.error('Failed to get configuration from Central Hub:', error.message);
      return {
        success: false,
        error: error.message,
        fallbackConfig: this._getFallbackConfiguration()
      };
    }
  }

  /**
   * Send health status to Central Hub
   * @param {Object} healthData - Health status data
   * @returns {Promise<Object>} - Send result
   */
  async sendHealthStatus(healthData) {
    try {
      const payload = {
        service: 'ErrorDNA',
        timestamp: new Date().toISOString(),
        status: healthData.status,
        metrics: {
          errorsProcessed: healthData.errorsProcessed || 0,
          patternsDetected: healthData.patternsDetected || 0,
          recoveriesAttempted: healthData.recoveriesAttempted || 0,
          uptime: healthData.uptime || 0
        },
        resources: {
          memory: healthData.memory || {},
          storage: healthData.storage || {},
          queues: healthData.queues || {}
        }
      };

      const response = await this._makeRequest('centralHub', 'POST', '/api/health', payload);

      return {
        success: true,
        acknowledgment: response.data.acknowledgment
      };
    } catch (error) {
      console.error('Failed to send health status to Central Hub:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Register ErrorDNA with Import Manager
   * @returns {Promise<Object>} - Registration result
   */
  async registerWithImportManager() {
    try {
      const registrationData = {
        serviceName: 'ErrorDNA',
        version: '1.0.0',
        errorHandling: {
          capabilities: [
            'data_import_errors',
            'validation_errors',
            'processing_errors',
            'transformation_errors'
          ],
          endpoints: {
            report: '/api/import-errors',
            patterns: '/api/import-patterns'
          }
        },
        integrationVersion: '1.0'
      };

      const response = await this._makeRequest('importManager', 'POST', '/api/services/register', registrationData);

      return {
        success: true,
        serviceId: response.data.serviceId,
        registrationTime: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to register with Import Manager:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Handle import error from Import Manager
   * @param {Object} importError - Import error data
   * @returns {Promise<Object>} - Handling result
   */
  async handleImportError(importError) {
    try {
      // Transform import error to standard error format
      const standardError = {
        id: importError.id || this._generateId(),
        originalError: {
          message: importError.message,
          code: importError.code,
          type: 'ImportError',
          source: importError.source,
          timestamp: importError.timestamp
        },
        context: {
          operation: 'data_import',
          file: importError.file,
          lineNumber: importError.lineNumber,
          column: importError.column,
          dataType: importError.dataType,
          retryable: importError.retryable !== false
        },
        metadata: {
          importId: importError.importId,
          batchId: importError.batchId,
          processor: importError.processor
        }
      };

      // Send acknowledgment back to Import Manager
      const ackPayload = {
        errorId: importError.id,
        received: true,
        timestamp: new Date().toISOString(),
        processedBy: 'ErrorDNA'
      };

      const response = await this._makeRequest('importManager', 'POST', '/api/errors/acknowledge', ackPayload);

      return {
        success: true,
        standardError,
        acknowledgment: response.data
      };
    } catch (error) {
      console.error('Failed to handle import error:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Send import error patterns to Import Manager
   * @param {Array} patterns - Array of import-related patterns
   * @returns {Promise<Object>} - Send result
   */
  async sendImportPatterns(patterns) {
    try {
      const importPatterns = patterns.filter(pattern =>
        pattern.category === 'API' || pattern.category === 'SYSTEM' ||
        (pattern.commonTags && pattern.commonTags.some(tag => tag.includes('import')))
      );

      if (importPatterns.length === 0) {
        return { success: true, sent: 0, reason: 'No import-related patterns found' };
      }

      const payload = {
        source: 'ErrorDNA',
        timestamp: new Date().toISOString(),
        patterns: importPatterns.map(pattern => ({
          id: pattern.id,
          signature: pattern.signature,
          description: pattern.description,
          occurrences: pattern.occurrences,
          severity: pattern.severity,
          riskLevel: pattern.riskLevel,
          recommendations: this._generateImportRecommendations(pattern)
        }))
      };

      const response = await this._makeRequest('importManager', 'POST', '/api/patterns', payload);

      return {
        success: true,
        sent: importPatterns.length,
        acknowledgment: response.data.acknowledgment
      };
    } catch (error) {
      console.error('Failed to send import patterns:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Get import configuration from Import Manager
   * @returns {Promise<Object>} - Configuration data
   */
  async getImportConfiguration() {
    try {
      const response = await this._makeRequest('importManager', 'GET', '/api/configuration/error-handling');

      return {
        success: true,
        configuration: response.data
      };
    } catch (error) {
      console.error('Failed to get import configuration:', error.message);
      return {
        success: false,
        error: error.message,
        fallbackConfig: this._getImportFallbackConfiguration()
      };
    }
  }

  /**
   * Send recovery suggestion to services
   * @param {string} service - Target service (centralHub or importManager)
   * @param {Object} errorData - Error data
   * @param {Object} recovery - Recovery suggestion
   * @returns {Promise<Object>} - Send result
   */
  async sendRecoverySuggestion(service, errorData, recovery) {
    try {
      const payload = {
        errorId: errorData.id,
        source: 'ErrorDNA',
        timestamp: new Date().toISOString(),
        recovery: {
          strategy: recovery.strategy,
          confidence: recovery.confidence || 0.8,
          actions: recovery.actions || [],
          fallback: recovery.fallback || null,
          metadata: recovery.metadata || {}
        }
      };

      const response = await this._makeRequest(service, 'POST', '/api/recovery-suggestions', payload);

      return {
        success: true,
        acknowledgment: response.data.acknowledgment
      };
    } catch (error) {
      console.error(`Failed to send recovery suggestion to ${service}:`, error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check integration health
   * @returns {Promise<Object>} - Health status for all integrations
   */
  async checkIntegrationHealth() {
    const results = {};

    // Check Central Hub
    try {
      const response = await this._makeRequest('centralHub', 'GET', '/api/health', null, { timeout: 5000 });
      results.centralHub = {
        status: 'healthy',
        latency: response.latency,
        lastContact: new Date().toISOString()
      };
    } catch (error) {
      results.centralHub = {
        status: 'unhealthy',
        error: error.message,
        lastAttempt: new Date().toISOString()
      };
    }

    // Check Import Manager
    try {
      const response = await this._makeRequest('importManager', 'GET', '/api/health', null, { timeout: 5000 });
      results.importManager = {
        status: 'healthy',
        latency: response.latency,
        lastContact: new Date().toISOString()
      };
    } catch (error) {
      results.importManager = {
        status: 'unhealthy',
        error: error.message,
        lastAttempt: new Date().toISOString()
      };
    }

    return results;
  }

  // Private methods

  /**
   * Make HTTP request to service
   * @private
   */
  async _makeRequest(service, method, endpoint, data = null, options = {}) {
    const config = this.config[service];
    const startTime = Date.now();

    if (!config) {
      throw new Error(`Unknown service: ${service}`);
    }

    const requestConfig = {
      method,
      url: `${config.baseUrl}${endpoint}`,
      timeout: options.timeout || config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'ErrorDNA/1.0'
      }
    };

    if (config.apiKey) {
      requestConfig.headers['Authorization'] = `Bearer ${config.apiKey}`;
    }

    if (data) {
      requestConfig.data = data;
    }

    try {
      this.integrationStats[service].requests++;

      const response = await axios(requestConfig);
      const latency = Date.now() - startTime;

      this.integrationStats[service].lastContact = new Date().toISOString();

      return {
        data: response.data,
        status: response.status,
        latency
      };
    } catch (error) {
      this.integrationStats[service].errors++;

      if (error.response) {
        throw new Error(`HTTP ${error.response.status}: ${error.response.data?.message || error.message}`);
      } else if (error.code === 'ECONNREFUSED') {
        throw new Error(`Connection refused to ${service}`);
      } else if (error.code === 'ETIMEDOUT') {
        throw new Error(`Request timeout to ${service}`);
      } else {
        throw error;
      }
    }
  }

  /**
   * Generate import-specific recommendations
   * @private
   */
  _generateImportRecommendations(pattern) {
    const recommendations = [];

    if (pattern.category === 'API' && pattern.subcategory === 'VALIDATION') {
      recommendations.push({
        action: 'enhance_validation',
        description: 'Improve data validation rules for import files',
        priority: 'medium'
      });
    }

    if (pattern.category === 'SYSTEM' && pattern.subcategory === 'MEMORY') {
      recommendations.push({
        action: 'optimize_batch_size',
        description: 'Reduce import batch size to prevent memory issues',
        priority: 'high'
      });
    }

    if (pattern.riskLevel === 'HIGH') {
      recommendations.push({
        action: 'implement_circuit_breaker',
        description: 'Add circuit breaker to prevent cascade failures',
        priority: 'high'
      });
    }

    return recommendations;
  }

  /**
   * Get fallback configuration
   * @private
   */
  _getFallbackConfiguration() {
    return {
      errorRetention: 30,
      patternDetection: true,
      notificationThresholds: {
        critical: 1,
        high: 3,
        medium: 10
      },
      recoveryStrategies: ['retry', 'fallback']
    };
  }

  /**
   * Get import fallback configuration
   * @private
   */
  _getImportFallbackConfiguration() {
    return {
      maxRetries: 3,
      batchSize: 1000,
      timeoutMs: 30000,
      errorThreshold: 0.05,
      recoveryStrategies: ['retry', 'skip', 'manual_review']
    };
  }

  /**
   * Generate unique ID
   * @private
   */
  _generateId() {
    return `int_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get integration statistics
   */
  getIntegrationStats() {
    return this.integrationStats;
  }

  /**
   * Reset integration statistics
   */
  resetStats() {
    this.integrationStats = {
      centralHub: { requests: 0, errors: 0, lastContact: null },
      importManager: { requests: 0, errors: 0, lastContact: null }
    };
  }
}

module.exports = SystemIntegration;