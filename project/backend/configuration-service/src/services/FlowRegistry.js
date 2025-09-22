/**
 * FlowRegistry Service - Core component for flow-aware debugging
 *
 * Provides centralized flow definition management, dependency tracking,
 * and execution orchestration for:
 * - LangGraph workflows (ai-orchestration service)
 * - AI Brain Flow Validator (shared service)
 * - Chain Mapping specifications (30 distinct chain mappings)
 * - Custom flows
 */

const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');

// Flow Type enumeration
const FlowType = {
  LANGGRAPH_WORKFLOW: 'langgraph_workflow',
  AI_BRAIN_VALIDATION: 'ai_brain_validation',
  CHAIN_MAPPING: 'chain_mapping',
  CUSTOM: 'custom'
};

// Flow Status enumeration
const FlowStatus = {
  DRAFT: 'draft',
  ACTIVE: 'active',
  DEPRECATED: 'deprecated',
  ARCHIVED: 'archived'
};

// Dependency Type enumeration
const DependencyType = {
  PREREQUISITE: 'prerequisite',
  PARALLEL: 'parallel',
  CONDITIONAL: 'conditional'
};

// Execution Status enumeration
const ExecutionStatus = {
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
};

class FlowRegistry {
  constructor(dbConfig, logger = null) {
    this.pool = new Pool(dbConfig);
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({
          filename: 'logs/flow-registry.log',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        })
      ]
    });

    this.initializeValidationSchemas();
  }

  /**
   * Initialize Joi validation schemas for flow definitions
   */
  initializeValidationSchemas() {
    // Flow Node schema
    this.flowNodeSchema = Joi.object({
      id: Joi.string().required(),
      name: Joi.string().required(),
      type: Joi.string().required(),
      config: Joi.object().default({}),
      position: Joi.object({
        x: Joi.number().required(),
        y: Joi.number().required()
      }).optional()
    });

    // Flow Edge schema
    this.flowEdgeSchema = Joi.object({
      id: Joi.string().required(),
      source: Joi.string().required(),
      target: Joi.string().required(),
      condition: Joi.string().optional(),
      config: Joi.object().default({})
    });

    // Flow Parameter schema
    this.flowParameterSchema = Joi.object({
      name: Joi.string().required(),
      type: Joi.string().valid('string', 'number', 'boolean', 'object', 'array').required(),
      required: Joi.boolean().default(false),
      default: Joi.any().optional(),
      description: Joi.string().optional(),
      validation: Joi.object().optional()
    });

    // Credential Reference schema
    this.credentialRefSchema = Joi.object({
      key: Joi.string().required(),
      type: Joi.string().valid('api_key', 'token', 'secret', 'oauth').required(),
      required: Joi.boolean().default(true),
      scope: Joi.string().optional()
    });

    // Flow Dependency schema
    this.flowDependencySchema = Joi.object({
      flowId: Joi.string().required(),
      type: Joi.string().valid(...Object.values(DependencyType)).required(),
      condition: Joi.string().optional(),
      timeout: Joi.number().optional()
    });

    // Flow Trigger schema
    this.flowTriggerSchema = Joi.object({
      type: Joi.string().valid('manual', 'schedule', 'event', 'webhook').required(),
      config: Joi.object().required(),
      enabled: Joi.boolean().default(true)
    });

    // Retry Policy schema
    this.retryPolicySchema = Joi.object({
      maxAttempts: Joi.number().min(1).max(10).default(3),
      backoffStrategy: Joi.string().valid('linear', 'exponential', 'fixed').default('exponential'),
      baseDelay: Joi.number().min(1000).default(1000),
      maxDelay: Joi.number().min(1000).default(30000)
    });

    // Main Flow Definition schema
    this.flowDefinitionSchema = Joi.object({
      id: Joi.string().pattern(/^[a-zA-Z0-9_-]+$/).required(),
      name: Joi.string().min(1).max(255).required(),
      type: Joi.string().valid(...Object.values(FlowType)).required(),
      version: Joi.string().pattern(/^\d+\.\d+\.\d+$/).required(),
      description: Joi.string().max(1000).optional(),

      // Flow Structure
      nodes: Joi.array().items(this.flowNodeSchema).required(),
      edges: Joi.array().items(this.flowEdgeSchema).required(),
      dependencies: Joi.array().items(this.flowDependencySchema).optional(),

      // Configuration
      parameters: Joi.array().items(this.flowParameterSchema).optional(),
      credentials: Joi.array().items(this.credentialRefSchema).optional(),
      environment: Joi.object().optional(),

      // Execution
      triggers: Joi.array().items(this.flowTriggerSchema).optional(),
      schedule: Joi.string().optional(), // Cron expression
      retryPolicy: this.retryPolicySchema.optional(),

      // Metadata
      tags: Joi.array().items(Joi.string()).optional(),
      metadata: Joi.object().optional(),
      createdBy: Joi.string().required(),
      status: Joi.string().valid(...Object.values(FlowStatus)).default(FlowStatus.DRAFT)
    });
  }

  /**
   * Initialize database tables if they don't exist
   */
  async initializeDatabase() {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      // Create flow definitions table
      await client.query(`
        CREATE TABLE IF NOT EXISTS flow_definitions (
          id VARCHAR(50) PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          type VARCHAR(50) NOT NULL,
          version VARCHAR(20) NOT NULL,
          description TEXT,
          definition_json JSONB NOT NULL,
          parameters_json JSONB DEFAULT '{}',
          status VARCHAR(20) DEFAULT 'draft',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by VARCHAR(100),
          tags TEXT[],
          metadata_json JSONB DEFAULT '{}',
          UNIQUE(name, version)
        );
      `);

      // Create flow dependencies table
      await client.query(`
        CREATE TABLE IF NOT EXISTS flow_dependencies (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
          depends_on_flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
          dependency_type VARCHAR(50) NOT NULL,
          condition_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(flow_id, depends_on_flow_id)
        );
      `);

      // Create flow executions table
      await client.query(`
        CREATE TABLE IF NOT EXISTS flow_executions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
          execution_id VARCHAR(100) NOT NULL,
          status VARCHAR(20) NOT NULL,
          parameters_json JSONB DEFAULT '{}',
          started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          completed_at TIMESTAMP,
          result_json JSONB,
          error_message TEXT,
          triggered_by VARCHAR(100),
          execution_context JSONB DEFAULT '{}',
          UNIQUE(execution_id)
        );
      `);

      // Create flow credentials table
      await client.query(`
        CREATE TABLE IF NOT EXISTS flow_credentials (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
          credential_key VARCHAR(100) NOT NULL,
          credential_type VARCHAR(50) NOT NULL,
          is_required BOOLEAN DEFAULT true,
          scope VARCHAR(100),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(flow_id, credential_key)
        );
      `);

      // Create indexes for performance
      await client.query(`
        CREATE INDEX IF NOT EXISTS idx_flow_definitions_type ON flow_definitions(type);
        CREATE INDEX IF NOT EXISTS idx_flow_definitions_status ON flow_definitions(status);
        CREATE INDEX IF NOT EXISTS idx_flow_definitions_created_by ON flow_definitions(created_by);
        CREATE INDEX IF NOT EXISTS idx_flow_definitions_tags ON flow_definitions USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_flow_executions_flow_id ON flow_executions(flow_id);
        CREATE INDEX IF NOT EXISTS idx_flow_executions_status ON flow_executions(status);
        CREATE INDEX IF NOT EXISTS idx_flow_executions_started_at ON flow_executions(started_at);
        CREATE INDEX IF NOT EXISTS idx_flow_dependencies_flow_id ON flow_dependencies(flow_id);
        CREATE INDEX IF NOT EXISTS idx_flow_dependencies_depends_on ON flow_dependencies(depends_on_flow_id);
        CREATE INDEX IF NOT EXISTS idx_flow_credentials_flow_id ON flow_credentials(flow_id);
      `);

      await client.query('COMMIT');
      this.logger.info('FlowRegistry database tables initialized successfully');
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Failed to initialize FlowRegistry database tables', { error: error.message });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Register a new flow definition
   * @param {Object} flowDefinition - The flow definition object
   * @returns {Promise<Object>} The registered flow with ID
   */
  async registerFlow(flowDefinition) {
    try {
      // Validate flow definition
      const { error, value } = this.flowDefinitionSchema.validate(flowDefinition);
      if (error) {
        throw new Error(`Flow validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedFlow = value;

      // Check if flow with same name and version exists
      const existingFlow = await this.getFlowByNameAndVersion(validatedFlow.name, validatedFlow.version);
      if (existingFlow) {
        throw new Error(`Flow with name '${validatedFlow.name}' and version '${validatedFlow.version}' already exists`);
      }

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Insert flow definition
        const flowResult = await client.query(
          `INSERT INTO flow_definitions
           (id, name, type, version, description, definition_json, parameters_json, status, created_by, tags, metadata_json)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
           RETURNING *`,
          [
            validatedFlow.id,
            validatedFlow.name,
            validatedFlow.type,
            validatedFlow.version,
            validatedFlow.description || null,
            JSON.stringify({
              nodes: validatedFlow.nodes,
              edges: validatedFlow.edges,
              environment: validatedFlow.environment || {},
              triggers: validatedFlow.triggers || [],
              schedule: validatedFlow.schedule || null,
              retryPolicy: validatedFlow.retryPolicy || {}
            }),
            JSON.stringify(validatedFlow.parameters || []),
            validatedFlow.status,
            validatedFlow.createdBy,
            validatedFlow.tags || [],
            JSON.stringify(validatedFlow.metadata || {})
          ]
        );

        // Insert flow credentials
        if (validatedFlow.credentials && validatedFlow.credentials.length > 0) {
          for (const credential of validatedFlow.credentials) {
            await client.query(
              `INSERT INTO flow_credentials (flow_id, credential_key, credential_type, is_required, scope)
               VALUES ($1, $2, $3, $4, $5)`,
              [
                validatedFlow.id,
                credential.key,
                credential.type,
                credential.required,
                credential.scope || null
              ]
            );
          }
        }

        // Insert flow dependencies
        if (validatedFlow.dependencies && validatedFlow.dependencies.length > 0) {
          for (const dependency of validatedFlow.dependencies) {
            await client.query(
              `INSERT INTO flow_dependencies (flow_id, depends_on_flow_id, dependency_type, condition_json)
               VALUES ($1, $2, $3, $4)`,
              [
                validatedFlow.id,
                dependency.flowId,
                dependency.type,
                JSON.stringify({
                  condition: dependency.condition || null,
                  timeout: dependency.timeout || null
                })
              ]
            );
          }
        }

        await client.query('COMMIT');

        const registeredFlow = flowResult.rows[0];
        this.logger.info('Flow registered successfully', {
          flowId: registeredFlow.id,
          name: registeredFlow.name,
          type: registeredFlow.type
        });

        return this.formatFlowResponse(registeredFlow);
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to register flow', {
        error: error.message,
        flowId: flowDefinition.id
      });
      throw error;
    }
  }

  /**
   * Get flow by ID with full details
   * @param {string} flowId - The flow ID
   * @returns {Promise<Object|null>} The flow definition or null if not found
   */
  async getFlow(flowId) {
    try {
      const client = await this.pool.connect();
      try {
        // Get flow definition
        const flowResult = await client.query(
          'SELECT * FROM flow_definitions WHERE id = $1',
          [flowId]
        );

        if (flowResult.rows.length === 0) {
          return null;
        }

        const flow = flowResult.rows[0];

        // Get flow credentials
        const credentialsResult = await client.query(
          'SELECT * FROM flow_credentials WHERE flow_id = $1',
          [flowId]
        );

        // Get flow dependencies
        const dependenciesResult = await client.query(
          `SELECT fd.*, f.name as depends_on_name
           FROM flow_dependencies fd
           LEFT JOIN flow_definitions f ON fd.depends_on_flow_id = f.id
           WHERE fd.flow_id = $1`,
          [flowId]
        );

        return this.formatFlowResponse(flow, credentialsResult.rows, dependenciesResult.rows);
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to get flow', { error: error.message, flowId });
      throw error;
    }
  }

  /**
   * Get flow by name and version
   * @param {string} name - Flow name
   * @param {string} version - Flow version
   * @returns {Promise<Object|null>} The flow definition or null if not found
   */
  async getFlowByNameAndVersion(name, version) {
    try {
      const result = await this.pool.query(
        'SELECT * FROM flow_definitions WHERE name = $1 AND version = $2',
        [name, version]
      );

      return result.rows.length > 0 ? this.formatFlowResponse(result.rows[0]) : null;
    } catch (error) {
      this.logger.error('Failed to get flow by name and version', {
        error: error.message,
        name,
        version
      });
      throw error;
    }
  }

  /**
   * List flows with filtering and pagination
   * @param {Object} options - Filter options
   * @returns {Promise<Object>} Paginated list of flows
   */
  async listFlows(options = {}) {
    try {
      const {
        type,
        status,
        createdBy,
        tags,
        page = 1,
        limit = 20,
        sortBy = 'created_at',
        sortOrder = 'DESC'
      } = options;

      let whereClause = '';
      const params = [];
      let paramCount = 0;

      // Build WHERE clause
      const conditions = [];

      if (type) {
        conditions.push(`type = $${++paramCount}`);
        params.push(type);
      }

      if (status) {
        conditions.push(`status = $${++paramCount}`);
        params.push(status);
      }

      if (createdBy) {
        conditions.push(`created_by = $${++paramCount}`);
        params.push(createdBy);
      }

      if (tags && tags.length > 0) {
        conditions.push(`tags && $${++paramCount}`);
        params.push(tags);
      }

      if (conditions.length > 0) {
        whereClause = 'WHERE ' + conditions.join(' AND ');
      }

      // Calculate offset
      const offset = (page - 1) * limit;

      // Get total count
      const countResult = await this.pool.query(
        `SELECT COUNT(*) FROM flow_definitions ${whereClause}`,
        params
      );
      const totalCount = parseInt(countResult.rows[0].count);

      // Get flows
      const flowsResult = await this.pool.query(
        `SELECT * FROM flow_definitions ${whereClause}
         ORDER BY ${sortBy} ${sortOrder}
         LIMIT $${++paramCount} OFFSET $${++paramCount}`,
        [...params, limit, offset]
      );

      const flows = flowsResult.rows.map(flow => this.formatFlowResponse(flow));

      return {
        flows,
        pagination: {
          page,
          limit,
          totalCount,
          totalPages: Math.ceil(totalCount / limit),
          hasNext: page < Math.ceil(totalCount / limit),
          hasPrev: page > 1
        }
      };
    } catch (error) {
      this.logger.error('Failed to list flows', { error: error.message, options });
      throw error;
    }
  }

  /**
   * Update flow definition
   * @param {string} flowId - The flow ID
   * @param {Object} updates - The updates to apply
   * @returns {Promise<Object>} The updated flow
   */
  async updateFlow(flowId, updates) {
    try {
      // Get existing flow
      const existingFlow = await this.getFlow(flowId);
      if (!existingFlow) {
        throw new Error(`Flow with ID '${flowId}' not found`);
      }

      // Merge updates with existing flow
      const updatedFlow = { ...existingFlow, ...updates };
      updatedFlow.id = flowId; // Ensure ID doesn't change

      // Validate updated flow
      const { error, value } = this.flowDefinitionSchema.validate(updatedFlow);
      if (error) {
        throw new Error(`Flow validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Update flow definition
        const result = await client.query(
          `UPDATE flow_definitions
           SET name = $2, type = $3, version = $4, description = $5,
               definition_json = $6, parameters_json = $7, status = $8,
               tags = $9, metadata_json = $10, updated_at = CURRENT_TIMESTAMP
           WHERE id = $1
           RETURNING *`,
          [
            flowId,
            value.name,
            value.type,
            value.version,
            value.description,
            JSON.stringify({
              nodes: value.nodes,
              edges: value.edges,
              environment: value.environment || {},
              triggers: value.triggers || [],
              schedule: value.schedule || null,
              retryPolicy: value.retryPolicy || {}
            }),
            JSON.stringify(value.parameters || []),
            value.status,
            value.tags || [],
            JSON.stringify(value.metadata || {})
          ]
        );

        // Update credentials if provided
        if (updates.credentials) {
          // Delete existing credentials
          await client.query('DELETE FROM flow_credentials WHERE flow_id = $1', [flowId]);

          // Insert new credentials
          for (const credential of updates.credentials) {
            await client.query(
              `INSERT INTO flow_credentials (flow_id, credential_key, credential_type, is_required, scope)
               VALUES ($1, $2, $3, $4, $5)`,
              [flowId, credential.key, credential.type, credential.required, credential.scope]
            );
          }
        }

        // Update dependencies if provided
        if (updates.dependencies) {
          // Delete existing dependencies
          await client.query('DELETE FROM flow_dependencies WHERE flow_id = $1', [flowId]);

          // Insert new dependencies
          for (const dependency of updates.dependencies) {
            await client.query(
              `INSERT INTO flow_dependencies (flow_id, depends_on_flow_id, dependency_type, condition_json)
               VALUES ($1, $2, $3, $4)`,
              [flowId, dependency.flowId, dependency.type, JSON.stringify({
                condition: dependency.condition || null,
                timeout: dependency.timeout || null
              })]
            );
          }
        }

        await client.query('COMMIT');

        this.logger.info('Flow updated successfully', { flowId });
        return this.formatFlowResponse(result.rows[0]);
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to update flow', { error: error.message, flowId });
      throw error;
    }
  }

  /**
   * Archive flow (soft delete)
   * @param {string} flowId - The flow ID
   * @returns {Promise<boolean>} Success status
   */
  async archiveFlow(flowId) {
    try {
      const result = await this.pool.query(
        'UPDATE flow_definitions SET status = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2',
        [FlowStatus.ARCHIVED, flowId]
      );

      if (result.rowCount === 0) {
        throw new Error(`Flow with ID '${flowId}' not found`);
      }

      this.logger.info('Flow archived successfully', { flowId });
      return true;
    } catch (error) {
      this.logger.error('Failed to archive flow', { error: error.message, flowId });
      throw error;
    }
  }

  /**
   * Track flow execution
   * @param {string} flowId - The flow ID
   * @param {string} executionId - Unique execution identifier
   * @param {Object} options - Execution options
   * @returns {Promise<Object>} Execution record
   */
  async trackExecution(flowId, executionId, options = {}) {
    try {
      const {
        parameters = {},
        triggeredBy = 'system',
        executionContext = {}
      } = options;

      const result = await this.pool.query(
        `INSERT INTO flow_executions
         (flow_id, execution_id, status, parameters_json, triggered_by, execution_context)
         VALUES ($1, $2, $3, $4, $5, $6)
         RETURNING *`,
        [
          flowId,
          executionId,
          ExecutionStatus.RUNNING,
          JSON.stringify(parameters),
          triggeredBy,
          JSON.stringify(executionContext)
        ]
      );

      const execution = result.rows[0];
      this.logger.info('Flow execution tracked', {
        flowId,
        executionId,
        triggeredBy
      });

      return this.formatExecutionResponse(execution);
    } catch (error) {
      this.logger.error('Failed to track flow execution', {
        error: error.message,
        flowId,
        executionId
      });
      throw error;
    }
  }

  /**
   * Update execution status
   * @param {string} executionId - The execution ID
   * @param {string} status - New status
   * @param {Object} result - Execution result
   * @param {string} errorMessage - Error message if failed
   * @returns {Promise<Object>} Updated execution record
   */
  async updateExecutionStatus(executionId, status, result = null, errorMessage = null) {
    try {
      const completedAt = [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED]
        .includes(status) ? 'CURRENT_TIMESTAMP' : null;

      const query = `
        UPDATE flow_executions
        SET status = $1, result_json = $2, error_message = $3
        ${completedAt ? ', completed_at = CURRENT_TIMESTAMP' : ''}
        WHERE execution_id = $4
        RETURNING *
      `;

      const queryResult = await this.pool.query(query, [
        status,
        result ? JSON.stringify(result) : null,
        errorMessage,
        executionId
      ]);

      if (queryResult.rowCount === 0) {
        throw new Error(`Execution with ID '${executionId}' not found`);
      }

      const execution = queryResult.rows[0];
      this.logger.info('Flow execution status updated', {
        executionId,
        status,
        hasError: !!errorMessage
      });

      return this.formatExecutionResponse(execution);
    } catch (error) {
      this.logger.error('Failed to update execution status', {
        error: error.message,
        executionId,
        status
      });
      throw error;
    }
  }

  /**
   * Get flow execution history
   * @param {string} flowId - The flow ID
   * @param {Object} options - Query options
   * @returns {Promise<Array>} List of executions
   */
  async getExecutionHistory(flowId, options = {}) {
    try {
      const {
        status,
        limit = 50,
        offset = 0,
        sortOrder = 'DESC'
      } = options;

      let whereClause = 'WHERE flow_id = $1';
      const params = [flowId];

      if (status) {
        whereClause += ' AND status = $2';
        params.push(status);
      }

      const result = await this.pool.query(
        `SELECT * FROM flow_executions ${whereClause}
         ORDER BY started_at ${sortOrder}
         LIMIT ${limit} OFFSET ${offset}`,
        params
      );

      return result.rows.map(execution => this.formatExecutionResponse(execution));
    } catch (error) {
      this.logger.error('Failed to get execution history', {
        error: error.message,
        flowId
      });
      throw error;
    }
  }

  /**
   * Get flow dependency graph
   * @param {string} flowId - The flow ID
   * @param {boolean} recursive - Include recursive dependencies
   * @returns {Promise<Object>} Dependency graph
   */
  async getDependencyGraph(flowId, recursive = false) {
    try {
      const visited = new Set();
      const graph = {
        flow: await this.getFlow(flowId),
        dependencies: [],
        dependents: []
      };

      if (!graph.flow) {
        throw new Error(`Flow with ID '${flowId}' not found`);
      }

      // Get direct dependencies (flows this flow depends on)
      const dependenciesResult = await this.pool.query(
        `SELECT fd.*, f.name, f.type, f.status
         FROM flow_dependencies fd
         JOIN flow_definitions f ON fd.depends_on_flow_id = f.id
         WHERE fd.flow_id = $1`,
        [flowId]
      );

      graph.dependencies = dependenciesResult.rows.map(dep => ({
        flowId: dep.depends_on_flow_id,
        name: dep.name,
        type: dep.type,
        status: dep.status,
        dependencyType: dep.dependency_type,
        condition: dep.condition_json
      }));

      // Get direct dependents (flows that depend on this flow)
      const dependentsResult = await this.pool.query(
        `SELECT fd.*, f.name, f.type, f.status
         FROM flow_dependencies fd
         JOIN flow_definitions f ON fd.flow_id = f.id
         WHERE fd.depends_on_flow_id = $1`,
        [flowId]
      );

      graph.dependents = dependentsResult.rows.map(dep => ({
        flowId: dep.flow_id,
        name: dep.name,
        type: dep.type,
        status: dep.status,
        dependencyType: dep.dependency_type,
        condition: dep.condition_json
      }));

      // If recursive, get full dependency tree
      if (recursive) {
        visited.add(flowId);

        for (const dep of graph.dependencies) {
          if (!visited.has(dep.flowId)) {
            dep.subDependencies = await this._getRecursiveDependencies(dep.flowId, visited);
          }
        }

        for (const dep of graph.dependents) {
          if (!visited.has(dep.flowId)) {
            dep.subDependents = await this._getRecursiveDependents(dep.flowId, visited);
          }
        }
      }

      return graph;
    } catch (error) {
      this.logger.error('Failed to get dependency graph', {
        error: error.message,
        flowId
      });
      throw error;
    }
  }

  /**
   * Validate flow definition and dependencies
   * @param {string} flowId - The flow ID
   * @returns {Promise<Object>} Validation result
   */
  async validateFlow(flowId) {
    try {
      const flow = await this.getFlow(flowId);
      if (!flow) {
        throw new Error(`Flow with ID '${flowId}' not found`);
      }

      const validation = {
        flowId,
        isValid: true,
        errors: [],
        warnings: [],
        details: {
          nodesValidation: [],
          edgesValidation: [],
          dependenciesValidation: [],
          credentialsValidation: []
        }
      };

      // Validate nodes
      const nodeIds = new Set();
      for (const node of flow.nodes) {
        if (nodeIds.has(node.id)) {
          validation.errors.push(`Duplicate node ID: ${node.id}`);
        }
        nodeIds.add(node.id);

        validation.details.nodesValidation.push({
          nodeId: node.id,
          isValid: true,
          issues: []
        });
      }

      // Validate edges
      for (const edge of flow.edges) {
        const edgeValidation = {
          edgeId: edge.id,
          isValid: true,
          issues: []
        };

        if (!nodeIds.has(edge.source)) {
          edgeValidation.issues.push(`Source node '${edge.source}' not found`);
          edgeValidation.isValid = false;
        }

        if (!nodeIds.has(edge.target)) {
          edgeValidation.issues.push(`Target node '${edge.target}' not found`);
          edgeValidation.isValid = false;
        }

        validation.details.edgesValidation.push(edgeValidation);
      }

      // Validate dependencies (check for cycles)
      const dependencyGraph = await this.getDependencyGraph(flowId, true);
      const cycles = this._detectCycles(flowId, dependencyGraph);

      if (cycles.length > 0) {
        validation.errors.push(`Circular dependencies detected: ${cycles.join(', ')}`);
        validation.details.dependenciesValidation.push({
          issue: 'circular_dependencies',
          cycles
        });
      }

      // Validate credentials exist
      for (const credential of flow.credentials || []) {
        // This would integrate with the existing credential service
        validation.details.credentialsValidation.push({
          credentialKey: credential.key,
          type: credential.type,
          isRequired: credential.required,
          isValid: true // Would check actual credential existence
        });
      }

      // Set overall validation status
      validation.isValid = validation.errors.length === 0;

      return validation;
    } catch (error) {
      this.logger.error('Failed to validate flow', {
        error: error.message,
        flowId
      });
      throw error;
    }
  }

  /**
   * Get flow statistics and metrics
   * @param {string} flowId - The flow ID (optional)
   * @returns {Promise<Object>} Flow statistics
   */
  async getFlowStatistics(flowId = null) {
    try {
      const stats = {};

      if (flowId) {
        // Statistics for specific flow
        const flowResult = await this.pool.query(
          'SELECT * FROM flow_definitions WHERE id = $1',
          [flowId]
        );

        if (flowResult.rows.length === 0) {
          throw new Error(`Flow with ID '${flowId}' not found`);
        }

        const executionStats = await this.pool.query(
          `SELECT
             COUNT(*) as total_executions,
             COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
             COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
             COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions,
             AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
           FROM flow_executions
           WHERE flow_id = $1`,
          [flowId]
        );

        stats.flow = this.formatFlowResponse(flowResult.rows[0]);
        stats.executions = executionStats.rows[0];
        stats.successRate = stats.executions.total_executions > 0
          ? (stats.executions.successful_executions / stats.executions.total_executions * 100).toFixed(2) + '%'
          : '0%';
      } else {
        // Global statistics
        const globalStats = await this.pool.query(`
          SELECT
            COUNT(*) as total_flows,
            COUNT(CASE WHEN type = 'langgraph_workflow' THEN 1 END) as langgraph_flows,
            COUNT(CASE WHEN type = 'ai_brain_validation' THEN 1 END) as ai_brain_flows,
            COUNT(CASE WHEN type = 'chain_mapping' THEN 1 END) as chain_mapping_flows,
            COUNT(CASE WHEN type = 'custom' THEN 1 END) as custom_flows,
            COUNT(CASE WHEN status = 'active' THEN 1 END) as active_flows,
            COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_flows
          FROM flow_definitions
        `);

        const executionStats = await this.pool.query(`
          SELECT
            COUNT(*) as total_executions,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as successful_executions,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_executions,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running_executions
          FROM flow_executions
        `);

        stats.flows = globalStats.rows[0];
        stats.executions = executionStats.rows[0];
        stats.overallSuccessRate = stats.executions.total_executions > 0
          ? (stats.executions.successful_executions / stats.executions.total_executions * 100).toFixed(2) + '%'
          : '0%';
      }

      return stats;
    } catch (error) {
      this.logger.error('Failed to get flow statistics', {
        error: error.message,
        flowId
      });
      throw error;
    }
  }

  /**
   * Format flow response for API
   * @private
   */
  formatFlowResponse(flow, credentials = [], dependencies = []) {
    const definitionJson = typeof flow.definition_json === 'string'
      ? JSON.parse(flow.definition_json)
      : flow.definition_json;

    const parametersJson = typeof flow.parameters_json === 'string'
      ? JSON.parse(flow.parameters_json)
      : flow.parameters_json;

    const metadataJson = typeof flow.metadata_json === 'string'
      ? JSON.parse(flow.metadata_json)
      : flow.metadata_json;

    return {
      id: flow.id,
      name: flow.name,
      type: flow.type,
      version: flow.version,
      description: flow.description,
      status: flow.status,
      createdBy: flow.created_by,
      createdAt: flow.created_at,
      updatedAt: flow.updated_at,
      tags: flow.tags || [],
      metadata: metadataJson || {},

      // Flow structure
      nodes: definitionJson.nodes || [],
      edges: definitionJson.edges || [],
      environment: definitionJson.environment || {},

      // Configuration
      parameters: parametersJson || [],
      credentials: credentials.map(cred => ({
        key: cred.credential_key,
        type: cred.credential_type,
        required: cred.is_required,
        scope: cred.scope
      })),

      // Execution
      triggers: definitionJson.triggers || [],
      schedule: definitionJson.schedule,
      retryPolicy: definitionJson.retryPolicy || {},

      // Dependencies
      dependencies: dependencies.map(dep => ({
        flowId: dep.depends_on_flow_id,
        name: dep.depends_on_name,
        type: dep.dependency_type,
        condition: typeof dep.condition_json === 'string'
          ? JSON.parse(dep.condition_json)
          : dep.condition_json
      }))
    };
  }

  /**
   * Format execution response for API
   * @private
   */
  formatExecutionResponse(execution) {
    return {
      id: execution.id,
      flowId: execution.flow_id,
      executionId: execution.execution_id,
      status: execution.status,
      parameters: typeof execution.parameters_json === 'string'
        ? JSON.parse(execution.parameters_json)
        : execution.parameters_json,
      startedAt: execution.started_at,
      completedAt: execution.completed_at,
      result: execution.result_json ?
        (typeof execution.result_json === 'string'
          ? JSON.parse(execution.result_json)
          : execution.result_json) : null,
      errorMessage: execution.error_message,
      triggeredBy: execution.triggered_by,
      executionContext: typeof execution.execution_context === 'string'
        ? JSON.parse(execution.execution_context)
        : execution.execution_context,
      duration: execution.completed_at && execution.started_at
        ? Math.round((new Date(execution.completed_at) - new Date(execution.started_at)) / 1000)
        : null
    };
  }

  /**
   * Get recursive dependencies
   * @private
   */
  async _getRecursiveDependencies(flowId, visited) {
    if (visited.has(flowId)) return [];

    visited.add(flowId);

    const result = await this.pool.query(
      `SELECT fd.*, f.name, f.type, f.status
       FROM flow_dependencies fd
       JOIN flow_definitions f ON fd.depends_on_flow_id = f.id
       WHERE fd.flow_id = $1`,
      [flowId]
    );

    const dependencies = [];
    for (const dep of result.rows) {
      const subDep = {
        flowId: dep.depends_on_flow_id,
        name: dep.name,
        type: dep.type,
        status: dep.status,
        dependencyType: dep.dependency_type,
        condition: dep.condition_json
      };

      if (!visited.has(dep.depends_on_flow_id)) {
        subDep.subDependencies = await this._getRecursiveDependencies(dep.depends_on_flow_id, visited);
      }

      dependencies.push(subDep);
    }

    return dependencies;
  }

  /**
   * Get recursive dependents
   * @private
   */
  async _getRecursiveDependents(flowId, visited) {
    if (visited.has(flowId)) return [];

    visited.add(flowId);

    const result = await this.pool.query(
      `SELECT fd.*, f.name, f.type, f.status
       FROM flow_dependencies fd
       JOIN flow_definitions f ON fd.flow_id = f.id
       WHERE fd.depends_on_flow_id = $1`,
      [flowId]
    );

    const dependents = [];
    for (const dep of result.rows) {
      const subDep = {
        flowId: dep.flow_id,
        name: dep.name,
        type: dep.type,
        status: dep.status,
        dependencyType: dep.dependency_type,
        condition: dep.condition_json
      };

      if (!visited.has(dep.flow_id)) {
        subDep.subDependents = await this._getRecursiveDependents(dep.flow_id, visited);
      }

      dependents.push(subDep);
    }

    return dependents;
  }

  /**
   * Detect cycles in dependency graph
   * @private
   */
  _detectCycles(startFlowId, dependencyGraph, visited = new Set(), recursionStack = new Set()) {
    const cycles = [];

    if (recursionStack.has(startFlowId)) {
      return [Array.from(recursionStack).join(' -> ') + ' -> ' + startFlowId];
    }

    if (visited.has(startFlowId)) {
      return cycles;
    }

    visited.add(startFlowId);
    recursionStack.add(startFlowId);

    for (const dependency of dependencyGraph.dependencies || []) {
      const subCycles = this._detectCycles(dependency.flowId, dependency, visited, recursionStack);
      cycles.push(...subCycles);
    }

    recursionStack.delete(startFlowId);
    return cycles;
  }

  /**
   * Close database connection
   */
  async close() {
    await this.pool.end();
    this.logger.info('FlowRegistry database connection closed');
  }
}

// Export enums and class
module.exports = {
  FlowRegistry,
  FlowType,
  FlowStatus,
  DependencyType,
  ExecutionStatus
};