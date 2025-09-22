/**
 * LangGraph Workflow Integration
 *
 * Integration layer for LangGraph workflows with FlowRegistry.
 * Provides seamless workflow registration and execution tracking.
 */

const FlowRegistryClient = require('../FlowRegistryClient');

class LangGraphIntegration {
  constructor(options = {}) {
    this.flowRegistry = new FlowRegistryClient(options);
    this.workflowCache = new Map();
    this.executionCallbacks = new Map();

    // Event listeners for workflow lifecycle
    this.flowRegistry.on('response', (data) => {
      if (data.data?.executionId) {
        this.handleExecutionResponse(data.data);
      }
    });
  }

  /**
   * Register LangGraph workflow with FlowRegistry
   */
  async registerWorkflow(workflowDefinition) {
    try {
      // Validate LangGraph workflow structure
      this.validateLangGraphWorkflow(workflowDefinition);

      // Transform LangGraph format to FlowRegistry format
      const flowDefinition = this.transformLangGraphToFlow(workflowDefinition);

      // Register with FlowRegistry
      const result = await this.flowRegistry.registerLangGraphWorkflow(flowDefinition);

      // Cache workflow for future use
      this.workflowCache.set(workflowDefinition.name, {
        flowId: result.data.id,
        definition: workflowDefinition,
        registered: new Date()
      });

      return result;
    } catch (error) {
      throw new Error(`Failed to register LangGraph workflow: ${error.message}`);
    }
  }

  /**
   * Execute LangGraph workflow with centralized tracking
   */
  async executeWorkflow(workflowName, parameters = {}, options = {}) {
    try {
      // Get workflow from cache or registry
      let workflow = this.workflowCache.get(workflowName);
      if (!workflow) {
        const flows = await this.flowRegistry.listFlows({
          type: 'langgraph_workflow',
          name: workflowName
        });

        if (flows.data.flows.length === 0) {
          throw new Error(`Workflow '${workflowName}' not found`);
        }

        workflow = {
          flowId: flows.data.flows[0].id,
          definition: flows.data.flows[0]
        };
        this.workflowCache.set(workflowName, workflow);
      }

      // Execute workflow
      const execution = await this.flowRegistry.executeFlow(workflow.flowId, {
        parameters,
        triggeredBy: options.triggeredBy || 'langgraph_integration',
        executionContext: {
          workflowName,
          integrationVersion: '1.0.0',
          ...options.context
        }
      });

      // Setup execution tracking if callback provided
      if (options.onComplete || options.onError) {
        this.executionCallbacks.set(execution.executionId, {
          onComplete: options.onComplete,
          onError: options.onError,
          startTime: Date.now()
        });
      }

      return execution;
    } catch (error) {
      throw new Error(`Failed to execute LangGraph workflow: ${error.message}`);
    }
  }

  /**
   * Get workflow execution history
   */
  async getWorkflowHistory(workflowName, options = {}) {
    try {
      const workflow = this.workflowCache.get(workflowName);
      if (!workflow) {
        throw new Error(`Workflow '${workflowName}' not found in cache`);
      }

      const history = await this.flowRegistry.getExecutionHistory(workflow.flowId, options);
      return history;
    } catch (error) {
      throw new Error(`Failed to get workflow history: ${error.message}`);
    }
  }

  /**
   * Update workflow execution status
   */
  async updateExecutionStatus(executionId, status, result = null, errorMessage = null) {
    try {
      const updated = await this.flowRegistry.updateExecutionStatus(
        executionId,
        status,
        result,
        errorMessage
      );

      // Trigger callbacks if registered
      const callbacks = this.executionCallbacks.get(executionId);
      if (callbacks) {
        const duration = Date.now() - callbacks.startTime;

        if (status === 'completed' && callbacks.onComplete) {
          callbacks.onComplete({
            executionId,
            result,
            duration,
            status: updated
          });
        } else if (status === 'failed' && callbacks.onError) {
          callbacks.onError({
            executionId,
            error: errorMessage,
            duration,
            status: updated
          });
        }

        // Cleanup callbacks
        this.executionCallbacks.delete(executionId);
      }

      return updated;
    } catch (error) {
      throw new Error(`Failed to update execution status: ${error.message}`);
    }
  }

  /**
   * Validate LangGraph workflow structure
   */
  validateLangGraphWorkflow(workflow) {
    const required = ['name', 'nodes', 'edges'];
    for (const field of required) {
      if (!workflow[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    // Validate nodes structure
    if (!Array.isArray(workflow.nodes) || workflow.nodes.length === 0) {
      throw new Error('Workflow must have at least one node');
    }

    // Validate edges structure
    if (!Array.isArray(workflow.edges)) {
      throw new Error('Workflow edges must be an array');
    }

    // Validate node IDs are unique
    const nodeIds = new Set();
    for (const node of workflow.nodes) {
      if (!node.id) {
        throw new Error('All nodes must have an ID');
      }
      if (nodeIds.has(node.id)) {
        throw new Error(`Duplicate node ID: ${node.id}`);
      }
      nodeIds.add(node.id);
    }

    // Validate edge references
    for (const edge of workflow.edges) {
      if (!edge.source || !edge.target) {
        throw new Error('All edges must have source and target');
      }
      if (!nodeIds.has(edge.source)) {
        throw new Error(`Edge references unknown source node: ${edge.source}`);
      }
      if (!nodeIds.has(edge.target)) {
        throw new Error(`Edge references unknown target node: ${edge.target}`);
      }
    }
  }

  /**
   * Transform LangGraph workflow to FlowRegistry format
   */
  transformLangGraphToFlow(workflow) {
    return {
      name: workflow.name,
      description: workflow.description || `LangGraph workflow: ${workflow.name}`,
      version: workflow.version || '1.0.0',
      nodes: workflow.nodes.map(node => ({
        id: node.id,
        name: node.name || node.id,
        type: node.type || 'langgraph_node',
        config: {
          langGraphConfig: node.config || {},
          functionName: node.function,
          inputs: node.inputs || [],
          outputs: node.outputs || []
        },
        position: node.position || { x: 0, y: 0 }
      })),
      edges: workflow.edges.map(edge => ({
        id: edge.id || `${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        condition: edge.condition,
        config: {
          langGraphConfig: edge.config || {},
          weight: edge.weight || 1
        }
      })),
      parameters: this.extractParameters(workflow),
      credentials: workflow.required_credentials || [],
      environment: {
        langGraphVersion: workflow.langGraphVersion || '0.1.0',
        pythonVersion: workflow.pythonVersion || '3.11',
        dependencies: workflow.dependencies || []
      },
      triggers: workflow.triggers || [],
      schedule: workflow.schedule,
      retryPolicy: workflow.retryPolicy || {
        maxAttempts: 3,
        backoffStrategy: 'exponential',
        baseDelay: 1000
      },
      tags: ['langgraph', 'workflow', ...(workflow.tags || [])],
      metadata: {
        langGraphWorkflow: true,
        originalDefinition: workflow,
        integrationVersion: '1.0.0'
      }
    };
  }

  /**
   * Extract parameters from LangGraph workflow
   */
  extractParameters(workflow) {
    const parameters = [];

    // Extract from node configurations
    for (const node of workflow.nodes) {
      if (node.config?.parameters) {
        for (const [name, config] of Object.entries(node.config.parameters)) {
          parameters.push({
            name: `${node.id}.${name}`,
            type: config.type || 'string',
            required: config.required || false,
            default: config.default,
            description: config.description || `Parameter for node ${node.id}`,
            validation: config.validation
          });
        }
      }
    }

    // Add global workflow parameters
    if (workflow.parameters) {
      for (const [name, config] of Object.entries(workflow.parameters)) {
        parameters.push({
          name,
          type: config.type || 'string',
          required: config.required || false,
          default: config.default,
          description: config.description || `Global workflow parameter`,
          validation: config.validation
        });
      }
    }

    return parameters;
  }

  /**
   * Handle execution response events
   */
  handleExecutionResponse(data) {
    // Log execution events for monitoring
    console.log('LangGraph execution event:', {
      executionId: data.executionId,
      status: data.status,
      timestamp: new Date()
    });
  }

  /**
   * Get workflow statistics
   */
  async getWorkflowStatistics(workflowName) {
    try {
      const workflow = this.workflowCache.get(workflowName);
      if (!workflow) {
        throw new Error(`Workflow '${workflowName}' not found`);
      }

      const stats = await this.flowRegistry.getFlowStatistics(workflow.flowId);
      return {
        ...stats,
        workflowName,
        integrationStats: {
          cacheHits: this.workflowCache.has(workflowName),
          activeCallbacks: this.executionCallbacks.size
        }
      };
    } catch (error) {
      throw new Error(`Failed to get workflow statistics: ${error.message}`);
    }
  }

  /**
   * List all registered LangGraph workflows
   */
  async listWorkflows(options = {}) {
    try {
      const result = await this.flowRegistry.listFlows({
        type: 'langgraph_workflow',
        ...options
      });

      return {
        ...result,
        data: {
          ...result.data,
          workflows: result.data.flows.map(flow => ({
            name: flow.name,
            id: flow.id,
            version: flow.version,
            description: flow.description,
            status: flow.status,
            cached: this.workflowCache.has(flow.name),
            lastExecution: flow.lastExecution,
            executionCount: flow.executionCount || 0
          }))
        }
      };
    } catch (error) {
      throw new Error(`Failed to list workflows: ${error.message}`);
    }
  }

  /**
   * Clear workflow cache
   */
  clearCache() {
    this.workflowCache.clear();
    this.executionCallbacks.clear();
  }

  /**
   * Close integration and cleanup
   */
  close() {
    this.clearCache();
    this.flowRegistry.close();
  }
}

module.exports = LangGraphIntegration;