/**
 * Flow Registry API Routes
 *
 * RESTful API endpoints for flow management, dependency tracking,
 * and execution orchestration. Integrates with existing Configuration Service.
 */

const express = require('express');
const router = express.Router();
const { FlowRegistry, FlowType, FlowStatus, ExecutionStatus } = require('../services/FlowRegistry');
const Joi = require('joi');
const winston = require('winston');

// Initialize logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/flow-api.log' })
  ]
});

// Flow Registry instance will be injected via middleware
let flowRegistry = null;

// Middleware to inject FlowRegistry instance
const injectFlowRegistry = (req, res, next) => {
  if (!flowRegistry) {
    return res.status(503).json({
      error: 'Flow Registry service not available',
      message: 'Flow Registry is not initialized'
    });
  }
  req.flowRegistry = flowRegistry;
  next();
};

// Initialize FlowRegistry with database configuration
const initializeFlowRegistry = (dbConfig) => {
  flowRegistry = new FlowRegistry(dbConfig, logger);
  return flowRegistry.initializeDatabase();
};

// Validation schemas for request bodies
const flowRegistrationSchema = Joi.object({
  id: Joi.string().pattern(/^[a-zA-Z0-9_-]+$/).required(),
  name: Joi.string().min(1).max(255).required(),
  type: Joi.string().valid(...Object.values(FlowType)).required(),
  version: Joi.string().pattern(/^\d+\.\d+\.\d+$/).required(),
  description: Joi.string().max(1000).optional(),
  nodes: Joi.array().items(Joi.object()).required(),
  edges: Joi.array().items(Joi.object()).required(),
  dependencies: Joi.array().items(Joi.object()).optional(),
  parameters: Joi.array().items(Joi.object()).optional(),
  credentials: Joi.array().items(Joi.object()).optional(),
  environment: Joi.object().optional(),
  triggers: Joi.array().items(Joi.object()).optional(),
  schedule: Joi.string().optional(),
  retryPolicy: Joi.object().optional(),
  tags: Joi.array().items(Joi.string()).optional(),
  metadata: Joi.object().optional(),
  createdBy: Joi.string().required()
});

const flowExecutionSchema = Joi.object({
  parameters: Joi.object().optional(),
  environment: Joi.string().optional(),
  triggeredBy: Joi.string().optional(),
  executionContext: Joi.object().optional()
});

const flowDependencySchema = Joi.object({
  dependsOnFlowId: Joi.string().required(),
  dependencyType: Joi.string().valid('prerequisite', 'parallel', 'conditional').required(),
  condition: Joi.string().optional(),
  timeout: Joi.number().optional()
});

// Error handling middleware
const handleError = (error, req, res, next) => {
  logger.error('Flow API error', {
    error: error.message,
    stack: error.stack,
    path: req.path,
    method: req.method,
    body: req.body
  });

  if (error.message.includes('validation failed')) {
    return res.status(400).json({
      error: 'Validation Error',
      message: error.message,
      details: error.details || null
    });
  }

  if (error.message.includes('not found')) {
    return res.status(404).json({
      error: 'Not Found',
      message: error.message
    });
  }

  if (error.message.includes('already exists')) {
    return res.status(409).json({
      error: 'Conflict',
      message: error.message
    });
  }

  res.status(500).json({
    error: 'Internal Server Error',
    message: 'An unexpected error occurred',
    requestId: req.headers['x-request-id'] || 'unknown'
  });
};

// Validation middleware
const validateRequest = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({
        error: 'Validation Error',
        message: error.details.map(detail => detail.message).join(', '),
        details: error.details
      });
    }
    req.validatedBody = value;
    next();
  };
};

// Query parameter validation
const validateQueryParams = (req, res, next) => {
  const schema = Joi.object({
    type: Joi.string().valid(...Object.values(FlowType)).optional(),
    status: Joi.string().valid(...Object.values(FlowStatus)).optional(),
    createdBy: Joi.string().optional(),
    tags: Joi.alternatives().try(
      Joi.string(),
      Joi.array().items(Joi.string())
    ).optional(),
    page: Joi.number().integer().min(1).default(1),
    limit: Joi.number().integer().min(1).max(100).default(20),
    sortBy: Joi.string().valid('created_at', 'updated_at', 'name', 'type').default('created_at'),
    sortOrder: Joi.string().valid('ASC', 'DESC').default('DESC'),
    includeArchived: Joi.boolean().default(false)
  });

  const { error, value } = schema.validate(req.query);
  if (error) {
    return res.status(400).json({
      error: 'Invalid query parameters',
      message: error.details.map(detail => detail.message).join(', ')
    });
  }

  // Convert tags to array if string
  if (value.tags && typeof value.tags === 'string') {
    value.tags = value.tags.split(',').map(tag => tag.trim()).filter(Boolean);
  }

  req.validatedQuery = value;
  next();
};

// ============================================================================
// FLOW DEFINITION ENDPOINTS
// ============================================================================

/**
 * POST /api/v1/flows
 * Register a new flow definition
 */
router.post('/', injectFlowRegistry, validateRequest(flowRegistrationSchema), async (req, res, next) => {
  try {
    const flow = await req.flowRegistry.registerFlow(req.validatedBody);

    logger.info('Flow registered successfully', {
      flowId: flow.id,
      name: flow.name,
      type: flow.type,
      createdBy: flow.createdBy
    });

    res.status(201).json({
      success: true,
      message: 'Flow registered successfully',
      data: flow
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/v1/flows
 * List flows with filtering and pagination
 */
router.get('/', injectFlowRegistry, validateQueryParams, async (req, res, next) => {
  try {
    const options = { ...req.validatedQuery };

    // Filter out archived flows unless explicitly requested
    if (!options.includeArchived) {
      options.status = options.status || 'active';
    }

    const result = await req.flowRegistry.listFlows(options);

    res.json({
      success: true,
      message: 'Flows retrieved successfully',
      data: result.flows,
      pagination: result.pagination
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/v1/flows/:flowId
 * Get specific flow definition with full details
 */
router.get('/:flowId', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const flow = await req.flowRegistry.getFlow(flowId);

    if (!flow) {
      return res.status(404).json({
        error: 'Not Found',
        message: `Flow with ID '${flowId}' not found`
      });
    }

    res.json({
      success: true,
      message: 'Flow retrieved successfully',
      data: flow
    });
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/v1/flows/:flowId
 * Update flow definition
 */
router.put('/:flowId', injectFlowRegistry, validateRequest(flowRegistrationSchema.fork(['id'], (schema) => schema.optional())), async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const updatedFlow = await req.flowRegistry.updateFlow(flowId, req.validatedBody);

    logger.info('Flow updated successfully', {
      flowId: updatedFlow.id,
      name: updatedFlow.name
    });

    res.json({
      success: true,
      message: 'Flow updated successfully',
      data: updatedFlow
    });
  } catch (error) {
    next(error);
  }
});

/**
 * DELETE /api/v1/flows/:flowId
 * Archive flow definition (soft delete)
 */
router.delete('/:flowId', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    await req.flowRegistry.archiveFlow(flowId);

    logger.info('Flow archived successfully', { flowId });

    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

// ============================================================================
// FLOW EXECUTION ENDPOINTS
// ============================================================================

/**
 * POST /api/v1/flows/:flowId/execute
 * Execute flow with parameters
 */
router.post('/:flowId/execute', injectFlowRegistry, validateRequest(flowExecutionSchema), async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const { parameters, triggeredBy, executionContext } = req.validatedBody;

    // Check if flow exists and is active
    const flow = await req.flowRegistry.getFlow(flowId);
    if (!flow) {
      return res.status(404).json({
        error: 'Not Found',
        message: `Flow with ID '${flowId}' not found`
      });
    }

    if (flow.status !== FlowStatus.ACTIVE) {
      return res.status(400).json({
        error: 'Invalid Flow Status',
        message: `Flow '${flowId}' is not active (current status: ${flow.status})`
      });
    }

    // Generate unique execution ID
    const executionId = `exec_${flowId}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Track execution start
    const execution = await req.flowRegistry.trackExecution(flowId, executionId, {
      parameters: parameters || {},
      triggeredBy: triggeredBy || 'api',
      executionContext: executionContext || {}
    });

    logger.info('Flow execution started', {
      flowId,
      executionId,
      triggeredBy: triggeredBy || 'api'
    });

    res.status(202).json({
      success: true,
      message: 'Flow execution started',
      data: {
        executionId,
        flowId,
        status: ExecutionStatus.RUNNING,
        startedAt: execution.startedAt,
        parameters: execution.parameters
      }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/v1/flows/:flowId/executions
 * Get flow execution history
 */
router.get('/:flowId/executions', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const { status, limit = 50, offset = 0, sortOrder = 'DESC' } = req.query;

    const executions = await req.flowRegistry.getExecutionHistory(flowId, {
      status,
      limit: parseInt(limit),
      offset: parseInt(offset),
      sortOrder
    });

    res.json({
      success: true,
      message: 'Execution history retrieved successfully',
      data: executions
    });
  } catch (error) {
    next(error);
  }
});

/**
 * PUT /api/v1/executions/:executionId/status
 * Update execution status
 */
router.put('/executions/:executionId/status', injectFlowRegistry, async (req, res, next) => {
  try {
    const { executionId } = req.params;
    const { status, result, errorMessage } = req.body;

    // Validate status
    if (!Object.values(ExecutionStatus).includes(status)) {
      return res.status(400).json({
        error: 'Invalid Status',
        message: `Status must be one of: ${Object.values(ExecutionStatus).join(', ')}`
      });
    }

    const execution = await req.flowRegistry.updateExecutionStatus(
      executionId,
      status,
      result,
      errorMessage
    );

    logger.info('Execution status updated', {
      executionId,
      status,
      hasError: !!errorMessage
    });

    res.json({
      success: true,
      message: 'Execution status updated successfully',
      data: execution
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================================
// FLOW DEPENDENCY ENDPOINTS
// ============================================================================

/**
 * GET /api/v1/flows/:flowId/dependencies
 * Get flow dependency graph
 */
router.get('/:flowId/dependencies', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const { recursive = false } = req.query;

    const dependencyGraph = await req.flowRegistry.getDependencyGraph(
      flowId,
      recursive === 'true'
    );

    res.json({
      success: true,
      message: 'Dependency graph retrieved successfully',
      data: dependencyGraph
    });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/v1/flows/:flowId/dependencies
 * Add flow dependency
 */
router.post('/:flowId/dependencies', injectFlowRegistry, validateRequest(flowDependencySchema), async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const { dependsOnFlowId, dependencyType, condition, timeout } = req.validatedBody;

    // Verify both flows exist
    const flow = await req.flowRegistry.getFlow(flowId);
    const dependentFlow = await req.flowRegistry.getFlow(dependsOnFlowId);

    if (!flow) {
      return res.status(404).json({
        error: 'Not Found',
        message: `Flow with ID '${flowId}' not found`
      });
    }

    if (!dependentFlow) {
      return res.status(404).json({
        error: 'Not Found',
        message: `Dependent flow with ID '${dependsOnFlowId}' not found`
      });
    }

    // Add dependency by updating the flow
    const updatedDependencies = [...(flow.dependencies || []), {
      flowId: dependsOnFlowId,
      type: dependencyType,
      condition,
      timeout
    }];

    await req.flowRegistry.updateFlow(flowId, {
      dependencies: updatedDependencies
    });

    logger.info('Flow dependency added', {
      flowId,
      dependsOnFlowId,
      dependencyType
    });

    res.status(201).json({
      success: true,
      message: 'Flow dependency added successfully',
      data: {
        flowId,
        dependsOnFlowId,
        dependencyType,
        condition,
        timeout
      }
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================================
// FLOW VALIDATION ENDPOINTS
// ============================================================================

/**
 * POST /api/v1/flows/:flowId/validate
 * Validate flow definition and dependencies
 */
router.post('/:flowId/validate', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const validation = await req.flowRegistry.validateFlow(flowId);

    res.json({
      success: true,
      message: 'Flow validation completed',
      data: validation
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================================
// FLOW STATISTICS AND MONITORING ENDPOINTS
// ============================================================================

/**
 * GET /api/v1/flows/:flowId/statistics
 * Get flow statistics and performance metrics
 */
router.get('/:flowId/statistics', injectFlowRegistry, async (req, res, next) => {
  try {
    const { flowId } = req.params;
    const stats = await req.flowRegistry.getFlowStatistics(flowId);

    res.json({
      success: true,
      message: 'Flow statistics retrieved successfully',
      data: stats
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/v1/flows/statistics/global
 * Get global flow statistics
 */
router.get('/statistics/global', injectFlowRegistry, async (req, res, next) => {
  try {
    const stats = await req.flowRegistry.getFlowStatistics();

    res.json({
      success: true,
      message: 'Global flow statistics retrieved successfully',
      data: stats
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================================
// HEALTH CHECK AND METADATA ENDPOINTS
// ============================================================================

/**
 * GET /api/v1/flows/health
 * Health check for Flow Registry service
 */
router.get('/health', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'FlowRegistry',
      version: '1.0.0',
      uptime: process.uptime(),
      checks: {
        database: 'unknown',
        flowRegistry: flowRegistry ? 'healthy' : 'unavailable'
      }
    };

    // Test database connection if FlowRegistry is available
    if (flowRegistry) {
      try {
        await flowRegistry.getFlowStatistics();
        health.checks.database = 'healthy';
      } catch (error) {
        health.checks.database = 'unhealthy';
        health.status = 'degraded';
      }
    } else {
      health.status = 'unhealthy';
    }

    const statusCode = health.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(health);
  } catch (error) {
    logger.error('Health check failed', { error: error.message });
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    });
  }
});

/**
 * GET /api/v1/flows/types
 * Get available flow types and their definitions
 */
router.get('/types', (req, res) => {
  res.json({
    success: true,
    message: 'Flow types retrieved successfully',
    data: {
      types: Object.values(FlowType),
      statuses: Object.values(FlowStatus),
      executionStatuses: Object.values(ExecutionStatus),
      definitions: {
        [FlowType.LANGGRAPH_WORKFLOW]: {
          name: 'LangGraph Workflow',
          description: 'AI orchestration workflows using LangGraph framework',
          requiredFields: ['nodes', 'edges'],
          optionalFields: ['parameters', 'credentials', 'schedule']
        },
        [FlowType.AI_BRAIN_VALIDATION]: {
          name: 'AI Brain Validation',
          description: 'Architecture validation flows for AI brain systems',
          requiredFields: ['nodes', 'edges'],
          optionalFields: ['parameters']
        },
        [FlowType.CHAIN_MAPPING]: {
          name: 'Chain Mapping',
          description: 'Blockchain and system integration chain mappings',
          requiredFields: ['nodes', 'edges', 'dependencies'],
          optionalFields: ['parameters', 'credentials']
        },
        [FlowType.CUSTOM]: {
          name: 'Custom Flow',
          description: 'User-defined custom flows',
          requiredFields: ['nodes', 'edges'],
          optionalFields: ['parameters', 'credentials', 'dependencies']
        }
      }
    }
  });
});

// Apply error handling middleware
router.use(handleError);

module.exports = {
  router,
  initializeFlowRegistry,
  FlowType,
  FlowStatus,
  ExecutionStatus
};