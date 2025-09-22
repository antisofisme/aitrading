/**
 * FlowRegistry Client Library
 *
 * Easy-to-use client for integrating with the FlowRegistry service.
 * Supports LangGraph workflows, AI Brain validation flows, and Chain mappings.
 */

const axios = require('axios');
const EventEmitter = require('events');

class FlowRegistryClient extends EventEmitter {
  constructor(options = {}) {
    super();

    this.baseURL = options.baseURL || 'http://localhost:8012';
    this.apiVersion = options.apiVersion || 'v1';
    this.timeout = options.timeout || 30000;
    this.retryAttempts = options.retryAttempts || 3;
    this.retryDelay = options.retryDelay || 1000;

    // Authentication options
    this.token = options.token || null;
    this.apiKey = options.apiKey || null;

    // Request interceptors
    this.client = axios.create({
      baseURL: `${this.baseURL}/api/${this.apiVersion}`,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'FlowRegistryClient/1.0.0'
      }
    });

    this.setupInterceptors();
  }

  /**
   * Setup request and response interceptors
   */
  setupInterceptors() {
    // Request interceptor for authentication
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        } else if (this.apiKey) {
          config.headers['X-API-Key'] = this.apiKey;
        }

        // Add request ID for tracing
        config.headers['x-request-id'] = this.generateRequestId();

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

    // Response interceptor for error handling and retries
    this.client.interceptors.response.use(
      (response) => {
        this.emit('response', {
          status: response.status,
          data: response.data,
          headers: response.headers
        });
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle retries for 5xx errors
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

          // Exponential backoff
          const delay = this.retryDelay * Math.pow(2, originalRequest._retryCount - 1);
          await this.sleep(delay);

          return this.client(originalRequest);
        }

        this.emit('error', error);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Set authentication token
   */
  setToken(token) {
    this.token = token;
    return this;
  }

  /**
   * Set API key
   */
  setApiKey(apiKey) {
    this.apiKey = apiKey;
    return this;
  }

  // ============================================================================
  // FLOW DEFINITION METHODS
  // ============================================================================

  /**
   * Register a new flow definition
   */
  async registerFlow(flowDefinition) {
    try {
      const response = await this.client.post('/flows', flowDefinition);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'registerFlow');
    }
  }

  /**
   * Register LangGraph workflow
   */
  async registerLangGraphWorkflow(workflowDefinition) {
    const flowDef = {
      id: `langgraph_${workflowDefinition.name}`,
      name: workflowDefinition.name,
      type: 'langgraph_workflow',
      version: workflowDefinition.version || '1.0.0',
      description: workflowDefinition.description || '',
      nodes: workflowDefinition.nodes || [],
      edges: workflowDefinition.edges || [],
      parameters: workflowDefinition.parameters || [],
      credentials: workflowDefinition.required_credentials || [],
      createdBy: workflowDefinition.createdBy || 'system',
      ...workflowDefinition
    };

    return this.registerFlow(flowDef);
  }

  /**
   * Register AI Brain validation flow
   */
  async registerAIBrainValidationFlow(validationDefinition) {
    const flowDef = {
      id: `ai_brain_validation_${validationDefinition.name}`,
      name: `AI Brain Validation: ${validationDefinition.name}`,
      type: 'ai_brain_validation',
      version: validationDefinition.version || '1.0.0',
      description: validationDefinition.description || '',
      nodes: validationDefinition.validation_rules || [],
      edges: [],
      parameters: validationDefinition.parameters || [],
      credentials: [],
      createdBy: validationDefinition.createdBy || 'system',
      ...validationDefinition
    };

    return this.registerFlow(flowDef);
  }

  /**
   * Register chain mapping flow
   */
  async registerChainMappingFlow(chainDefinition) {
    const flowDef = {
      id: `chain_mapping_${chainDefinition.id}`,
      name: `Chain Mapping: ${chainDefinition.name}`,
      type: 'chain_mapping',
      version: chainDefinition.version || '1.0.0',
      description: chainDefinition.description || '',
      nodes: chainDefinition.nodes || [],
      edges: chainDefinition.edges || [],
      dependencies: chainDefinition.dependencies || [],
      parameters: chainDefinition.parameters || [],
      credentials: chainDefinition.credentials || [],
      createdBy: chainDefinition.createdBy || 'system',
      ...chainDefinition
    };

    return this.registerFlow(flowDef);
  }

  /**
   * Get flow by ID
   */
  async getFlow(flowId) {
    try {
      const response = await this.client.get(`/flows/${flowId}`);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'getFlow');
    }
  }

  /**
   * List flows with filtering
   */
  async listFlows(options = {}) {
    try {
      const params = new URLSearchParams(options);
      const response = await this.client.get(`/flows?${params}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'listFlows');
    }
  }

  /**
   * Update flow definition
   */
  async updateFlow(flowId, updates) {
    try {
      const response = await this.client.put(`/flows/${flowId}`, updates);
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'updateFlow');
    }
  }

  /**
   * Archive flow
   */
  async archiveFlow(flowId) {
    try {
      await this.client.delete(`/flows/${flowId}`);
      return true;
    } catch (error) {
      throw this.handleError(error, 'archiveFlow');
    }
  }

  // ============================================================================
  // FLOW EXECUTION METHODS
  // ============================================================================

  /**
   * Execute flow
   */
  async executeFlow(flowId, options = {}) {
    try {
      const response = await this.client.post(`/flows/${flowId}/execute`, options);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'executeFlow');
    }
  }

  /**
   * Get execution history
   */
  async getExecutionHistory(flowId, options = {}) {
    try {
      const params = new URLSearchParams(options);
      const response = await this.client.get(`/flows/${flowId}/executions?${params}`);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'getExecutionHistory');
    }
  }

  /**
   * Update execution status
   */
  async updateExecutionStatus(executionId, status, result = null, errorMessage = null) {
    try {
      const response = await this.client.put(`/executions/${executionId}/status`, {
        status,
        result,
        errorMessage
      });
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'updateExecutionStatus');
    }
  }

  // ============================================================================
  // FLOW DEPENDENCY METHODS
  // ============================================================================

  /**
   * Get dependency graph
   */
  async getDependencyGraph(flowId, recursive = false) {
    try {
      const response = await this.client.get(
        `/flows/${flowId}/dependencies?recursive=${recursive}`
      );
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'getDependencyGraph');
    }
  }

  /**
   * Add flow dependency
   */
  async addFlowDependency(flowId, dependencyConfig) {
    try {
      const response = await this.client.post(`/flows/${flowId}/dependencies`, dependencyConfig);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'addFlowDependency');
    }
  }

  // ============================================================================
  // FLOW VALIDATION METHODS
  // ============================================================================

  /**
   * Validate flow
   */
  async validateFlow(flowId) {
    try {
      const response = await this.client.post(`/flows/${flowId}/validate`);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'validateFlow');
    }
  }

  // ============================================================================
  // MONITORING AND STATISTICS METHODS
  // ============================================================================

  /**
   * Get flow statistics
   */
  async getFlowStatistics(flowId = null) {
    try {
      const url = flowId ? `/flows/${flowId}/statistics` : '/flows/statistics/global';
      const response = await this.client.get(url);
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'getFlowStatistics');
    }
  }

  /**
   * Get flow types and definitions
   */
  async getFlowTypes() {
    try {
      const response = await this.client.get('/flows/types');
      return response.data.data;
    } catch (error) {
      throw this.handleError(error, 'getFlowTypes');
    }
  }

  /**
   * Health check
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/flows/health');
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'healthCheck');
    }
  }

  // ============================================================================
  // UTILITY METHODS
  // ============================================================================

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Sleep for specified milliseconds
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Handle and format errors
   */
  handleError(error, method) {
    const errorInfo = {
      method,
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      requestId: error.config?.headers?.['x-request-id']
    };

    this.emit('error', errorInfo);

    // Create custom error with additional context
    const customError = new Error(
      error.response?.data?.message || error.message || 'Unknown error'
    );
    customError.method = method;
    customError.status = error.response?.status;
    customError.requestId = errorInfo.requestId;
    customError.originalError = error;

    return customError;
  }

  /**
   * Close client and cleanup
   */
  close() {
    this.removeAllListeners();
  }
}

module.exports = FlowRegistryClient;