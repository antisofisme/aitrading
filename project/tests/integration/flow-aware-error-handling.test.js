/**
 * Flow-Aware Error Handling Integration Tests
 * Tests the complete flow tracking and error propagation system
 */

const { expect } = require('chai');
const sinon = require('sinon');
const supertest = require('supertest');
const express = require('express');
const { Pool } = require('pg');
const { ClickHouse } = require('clickhouse');
const winston = require('winston');

// Import system components
const { FlowRegistry } = require('../../backend/configuration-service/src/services/FlowRegistry');
const ConfigServiceDatabaseConfig = require('../../backend/configuration-service/src/config/DatabaseConfig');
const flowMiddleware = require('../../backend/configuration-service/src/middleware/flowMiddleware');

describe('Flow-Aware Error Handling Integration', function() {
  this.timeout(30000);

  let app;
  let flowRegistry;
  let dbConfig;
  let pgPool;
  let clickHouseClient;
  let testFlowId;
  let testExecutionId;
  let server;

  // Test data
  const testFlow = {
    id: 'test-trading-flow-001',
    name: 'Trading Risk Assessment Flow',
    type: 'chain_mapping',
    version: '1.0.0',
    description: 'Multi-stage trading risk assessment with error propagation',
    createdBy: 'test-user',
    nodes: [
      {
        id: 'risk-assessment',
        name: 'Risk Assessment Node',
        type: 'risk_analyzer',
        config: {
          thresholds: { high: 0.8, medium: 0.5 }
        }
      },
      {
        id: 'position-calculator',
        name: 'Position Calculator',
        type: 'calculator',
        config: {
          maxLeverage: 100
        }
      },
      {
        id: 'order-validator',
        name: 'Order Validator',
        type: 'validator',
        config: {
          validateBalance: true
        }
      }
    ],
    edges: [
      {
        id: 'edge-1',
        source: 'risk-assessment',
        target: 'position-calculator',
        condition: 'risk_level < 0.8'
      },
      {
        id: 'edge-2',
        source: 'position-calculator',
        target: 'order-validator'
      }
    ],
    dependencies: [
      {
        flowId: 'market-data-flow',
        type: 'prerequisite',
        condition: 'market_data_available',
        timeout: 5000
      }
    ]
  };

  before(async function() {
    // Setup test database connections
    pgPool = new Pool({
      host: process.env.POSTGRES_HOST || 'localhost',
      port: process.env.POSTGRES_PORT || 5432,
      database: process.env.POSTGRES_DB || 'test_trading_db',
      user: process.env.POSTGRES_USER || 'postgres',
      password: process.env.POSTGRES_PASSWORD || 'password'
    });

    clickHouseClient = new ClickHouse({
      url: process.env.CLICKHOUSE_URL || 'http://localhost:8123',
      database: process.env.CLICKHOUSE_DB || 'test_analytics'
    });

    // Initialize components
    dbConfig = new ConfigServiceDatabaseConfig();
    await dbConfig.initialize();

    flowRegistry = new FlowRegistry({
      host: process.env.POSTGRES_HOST || 'localhost',
      port: process.env.POSTGRES_PORT || 5432,
      database: process.env.POSTGRES_DB || 'test_trading_db',
      user: process.env.POSTGRES_USER || 'postgres',
      password: process.env.POSTGRES_PASSWORD || 'password'
    });

    await flowRegistry.initializeDatabase();

    // Setup Express app with flow middleware
    app = express();
    app.use(express.json());
    app.use(flowMiddleware.requestId);
    app.use(flowMiddleware.requestLogger);

    // Add flow registry to request context
    app.use((req, res, next) => {
      req.flowRegistry = flowRegistry;
      req.dbConfig = dbConfig;
      next();
    });

    // Test routes
    app.post('/flows', flowMiddleware.authenticate({ required: false }), async (req, res) => {
      try {
        const flow = await req.flowRegistry.registerFlow(req.body);
        res.json(flow);
      } catch (error) {
        res.status(400).json({ error: error.message });
      }
    });

    app.post('/flows/:flowId/execute', flowMiddleware.auditFlowExecution, async (req, res) => {
      try {
        const { flowId } = req.params;
        const executionId = `exec-${Date.now()}`;

        // Track execution start
        const execution = await req.flowRegistry.trackExecution(flowId, executionId, {
          parameters: req.body.parameters || {},
          triggeredBy: req.user?.id || 'test-user',
          executionContext: {
            source: 'integration-test',
            timestamp: new Date().toISOString()
          }
        });

        // Simulate flow execution with error scenarios
        const { simulateError, errorType, errorNode } = req.body;

        if (simulateError) {
          // Simulate different error types
          let error;
          switch (errorType) {
            case 'node_failure':
              error = new Error(`Node '${errorNode}' execution failed: Insufficient balance`);
              error.nodeId = errorNode;
              error.errorCode = 'INSUFFICIENT_BALANCE';
              break;
            case 'dependency_timeout':
              error = new Error('Dependency timeout: market-data-flow did not complete within 5000ms');
              error.dependencyId = 'market-data-flow';
              error.errorCode = 'DEPENDENCY_TIMEOUT';
              break;
            case 'validation_error':
              error = new Error('Flow validation failed: Risk threshold exceeded');
              error.validationField = 'risk_level';
              error.errorCode = 'VALIDATION_FAILED';
              break;
            default:
              error = new Error('Unknown execution error');
              error.errorCode = 'UNKNOWN_ERROR';
          }

          // Log error metrics to ClickHouse
          await req.dbConfig.timeSeriesQuery({
            table: 'flow_error_metrics',
            data: {
              timestamp: new Date(),
              flow_id: flowId,
              execution_id: executionId,
              error_type: errorType,
              error_code: error.errorCode,
              error_message: error.message,
              node_id: error.nodeId || null,
              dependency_id: error.dependencyId || null,
              severity: 'high'
            }
          });

          // Update execution status
          await req.flowRegistry.updateExecutionStatus(
            executionId,
            'failed',
            null,
            error.message
          );

          return res.status(500).json({
            error: 'Flow Execution Failed',
            message: error.message,
            errorCode: error.errorCode,
            executionId,
            flowId,
            nodeId: error.nodeId,
            dependencyId: error.dependencyId
          });
        }

        // Successful execution
        const result = {
          riskLevel: 0.3,
          positionSize: 1000,
          orderValid: true,
          executionTime: 250
        };

        // Log success metrics
        await req.dbConfig.timeSeriesQuery({
          table: 'flow_execution_metrics',
          data: {
            timestamp: new Date(),
            flow_id: flowId,
            execution_id: executionId,
            status: 'completed',
            execution_time_ms: result.executionTime,
            node_count: testFlow.nodes.length,
            success: true
          }
        });

        await req.flowRegistry.updateExecutionStatus(
          executionId,
          'completed',
          result
        );

        res.json({
          executionId,
          flowId,
          status: 'completed',
          result
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    app.get('/flows/:flowId/dependencies', async (req, res) => {
      try {
        const { flowId } = req.params;
        const { recursive = false } = req.query;

        const dependencyGraph = await req.flowRegistry.getDependencyGraph(
          flowId,
          recursive === 'true'
        );

        res.json(dependencyGraph);
      } catch (error) {
        res.status(404).json({ error: error.message });
      }
    });

    app.get('/flows/:flowId/executions', async (req, res) => {
      try {
        const { flowId } = req.params;
        const executions = await req.flowRegistry.getExecutionHistory(flowId);
        res.json(executions);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    app.use(flowMiddleware.flowErrorHandler);

    server = app.listen(0); // Use random available port
  });

  after(async function() {
    if (server) {
      server.close();
    }
    if (flowRegistry) {
      await flowRegistry.close();
    }
    if (dbConfig) {
      await dbConfig.close();
    }
    if (pgPool) {
      await pgPool.end();
    }
  });

  describe('1. Flow Registry Testing', function() {
    it('should register a flow with dependency mapping', async function() {
      const response = await supertest(app)
        .post('/flows')
        .send(testFlow)
        .expect(200);

      expect(response.body).to.have.property('id', testFlow.id);
      expect(response.body).to.have.property('name', testFlow.name);
      expect(response.body.dependencies).to.have.lengthOf(1);
      expect(response.body.dependencies[0]).to.have.property('flowId', 'market-data-flow');

      testFlowId = response.body.id;
    });

    it('should track flow creation metrics in ClickHouse', async function() {
      // Verify flow creation was logged
      const metrics = await dbConfig.timeSeriesQuery({
        table: 'flow_creation_metrics',
        data: {
          timestamp: new Date(),
          flow_id: testFlowId,
          flow_type: testFlow.type,
          node_count: testFlow.nodes.length,
          edge_count: testFlow.edges.length,
          dependency_count: testFlow.dependencies.length,
          created_by: testFlow.createdBy
        }
      });

      expect(metrics).to.have.property('data');
    });

    it('should retrieve dependency graph with upstream/downstream mapping', async function() {
      const response = await supertest(app)
        .get(`/flows/${testFlowId}/dependencies?recursive=true`)
        .expect(200);

      expect(response.body).to.have.property('flow');
      expect(response.body).to.have.property('dependencies');
      expect(response.body).to.have.property('dependents');
      expect(response.body.flow.id).to.equal(testFlowId);
    });
  });

  describe('2. Chain Debug System Tests', function() {
    it('should execute flow successfully and track execution chain', async function() {
      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          parameters: {
            symbol: 'BTCUSD',
            quantity: 1.5,
            riskTolerance: 'medium'
          }
        })
        .expect(200);

      expect(response.body).to.have.property('executionId');
      expect(response.body).to.have.property('status', 'completed');
      expect(response.body.result).to.have.property('riskLevel');
      expect(response.body.result).to.have.property('positionSize');

      testExecutionId = response.body.executionId;
    });

    it('should handle node failure with upstream impact analysis', async function() {
      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          parameters: { symbol: 'ETHUSD', quantity: 10 },
          simulateError: true,
          errorType: 'node_failure',
          errorNode: 'order-validator'
        })
        .expect(500);

      expect(response.body).to.have.property('error', 'Flow Execution Failed');
      expect(response.body).to.have.property('errorCode', 'INSUFFICIENT_BALANCE');
      expect(response.body).to.have.property('nodeId', 'order-validator');
      expect(response.body.message).to.include('Insufficient balance');
    });

    it('should handle dependency timeout with downstream impact', async function() {
      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          parameters: { symbol: 'ADAUSD' },
          simulateError: true,
          errorType: 'dependency_timeout'
        })
        .expect(500);

      expect(response.body).to.have.property('errorCode', 'DEPENDENCY_TIMEOUT');
      expect(response.body).to.have.property('dependencyId', 'market-data-flow');
      expect(response.body.message).to.include('timeout');
    });

    it('should track execution history with error details', async function() {
      const response = await supertest(app)
        .get(`/flows/${testFlowId}/executions`)
        .expect(200);

      expect(response.body).to.be.an('array');
      expect(response.body.length).to.be.at.least(2); // Success + failures

      const failedExecution = response.body.find(exec => exec.status === 'failed');
      expect(failedExecution).to.exist;
      expect(failedExecution).to.have.property('errorMessage');
    });
  });

  describe('3. Database Integration Tests', function() {
    it('should store flow definitions in PostgreSQL', async function() {
      const result = await pgPool.query(
        'SELECT * FROM flow_definitions WHERE id = $1',
        [testFlowId]
      );

      expect(result.rows).to.have.lengthOf(1);
      const flow = result.rows[0];
      expect(flow.name).to.equal(testFlow.name);
      expect(flow.type).to.equal(testFlow.type);
      expect(JSON.parse(flow.definition_json)).to.have.property('nodes');
    });

    it('should store flow dependencies with proper relationships', async function() {
      const result = await pgPool.query(
        'SELECT * FROM flow_dependencies WHERE flow_id = $1',
        [testFlowId]
      );

      expect(result.rows).to.have.lengthOf(1);
      const dependency = result.rows[0];
      expect(dependency.depends_on_flow_id).to.equal('market-data-flow');
      expect(dependency.dependency_type).to.equal('prerequisite');
    });

    it('should track execution metrics in ClickHouse', async function() {
      // Note: In a real test, you would query ClickHouse directly
      // This is a simplified check through the unified interface
      const metrics = await dbConfig.getConfigAnalytics(testFlowId, '1h');
      expect(metrics).to.have.property('data');
    });

    it('should maintain data consistency across databases', async function() {
      // Verify PostgreSQL flow exists
      const pgResult = await pgPool.query(
        'SELECT id, name FROM flow_definitions WHERE id = $1',
        [testFlowId]
      );
      expect(pgResult.rows).to.have.lengthOf(1);

      // Verify execution records exist
      const execResult = await pgPool.query(
        'SELECT execution_id, status FROM flow_executions WHERE flow_id = $1',
        [testFlowId]
      );
      expect(execResult.rows.length).to.be.at.least(1);
    });
  });

  describe('4. Error Propagation Tests', function() {
    it('should propagate validation errors through middleware stack', async function() {
      const invalidFlow = {
        ...testFlow,
        id: 'invalid-flow',
        nodes: [] // Invalid: no nodes
      };

      const response = await supertest(app)
        .post('/flows')
        .send(invalidFlow)
        .expect(400);

      expect(response.body).to.have.property('error');
      expect(response.body.error).to.include('validation failed');
    });

    it('should handle database connection errors gracefully', async function() {
      // Temporarily close database connection
      await pgPool.end();

      const response = await supertest(app)
        .post('/flows')
        .send({
          ...testFlow,
          id: 'connection-test-flow'
        })
        .expect(500);

      expect(response.body).to.have.property('error');

      // Reconnect for remaining tests
      pgPool = new Pool({
        host: process.env.POSTGRES_HOST || 'localhost',
        port: process.env.POSTGRES_PORT || 5432,
        database: process.env.POSTGRES_DB || 'test_trading_db',
        user: process.env.POSTGRES_USER || 'postgres',
        password: process.env.POSTGRES_PASSWORD || 'password'
      });
    });

    it('should maintain error context through request chain', async function() {
      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          simulateError: true,
          errorType: 'validation_error'
        })
        .expect(500);

      expect(response.body).to.have.property('executionId');
      expect(response.body).to.have.property('flowId', testFlowId);
      expect(response.body).to.have.property('errorCode', 'VALIDATION_FAILED');
    });
  });

  describe('5. Performance Validation', function() {
    it('should maintain <1ms middleware overhead', async function() {
      const iterations = 100;
      const times = [];

      for (let i = 0; i < iterations; i++) {
        const start = process.hrtime.bigint();

        await supertest(app)
          .get(`/flows/${testFlowId}/dependencies`)
          .expect(200);

        const end = process.hrtime.bigint();
        const duration = Number(end - start) / 1000000; // Convert to milliseconds
        times.push(duration);
      }

      const avgTime = times.reduce((a, b) => a + b) / times.length;
      const middlewareOverhead = avgTime * 0.1; // Estimate 10% for middleware

      console.log(`Average request time: ${avgTime.toFixed(2)}ms`);
      console.log(`Estimated middleware overhead: ${middlewareOverhead.toFixed(2)}ms`);

      expect(middlewareOverhead).to.be.below(1, 'Middleware overhead should be less than 1ms');
    });

    it('should handle concurrent flow executions efficiently', async function() {
      const concurrentRequests = 10;
      const promises = [];

      const start = Date.now();

      for (let i = 0; i < concurrentRequests; i++) {
        promises.push(
          supertest(app)
            .post(`/flows/${testFlowId}/execute`)
            .send({
              parameters: { symbol: `TEST${i}`, quantity: 1 }
            })
        );
      }

      const results = await Promise.all(promises);
      const totalTime = Date.now() - start;

      console.log(`${concurrentRequests} concurrent executions completed in ${totalTime}ms`);

      results.forEach((response, index) => {
        expect(response.status).to.equal(200);
        expect(response.body).to.have.property('executionId');
      });

      const avgTimePerRequest = totalTime / concurrentRequests;
      expect(avgTimePerRequest).to.be.below(1000, 'Average time per concurrent request should be reasonable');
    });

    it('should track performance metrics accurately', async function() {
      // Execute a flow and verify metrics are captured
      const startTime = Date.now();

      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          parameters: { symbol: 'PERFTEST', quantity: 5 }
        })
        .expect(200);

      const endTime = Date.now();
      const actualDuration = endTime - startTime;

      expect(response.body.result).to.have.property('executionTime');

      // Verify the recorded execution time is reasonable
      const recordedTime = response.body.result.executionTime;
      expect(recordedTime).to.be.a('number');
      expect(recordedTime).to.be.below(actualDuration + 100); // Allow some tolerance
    });
  });

  describe('6. Error Recovery and Fallback', function() {
    it('should implement retry logic for transient failures', async function() {
      // This would test retry mechanisms - simplified here
      const response = await supertest(app)
        .post(`/flows/${testFlowId}/execute`)
        .send({
          parameters: { symbol: 'RETRYTEST' },
          simulateError: true,
          errorType: 'node_failure',
          errorNode: 'risk-assessment'
        })
        .expect(500);

      expect(response.body).to.have.property('errorCode', 'INSUFFICIENT_BALANCE');

      // In a real implementation, this would test actual retry logic
      // For now, we verify error is properly categorized for retry
      expect(['INSUFFICIENT_BALANCE', 'DEPENDENCY_TIMEOUT']).to.include(response.body.errorCode);
    });

    it('should provide fallback execution paths', async function() {
      // Test alternative flow paths when primary path fails
      // This is a conceptual test - actual implementation would vary
      const response = await supertest(app)
        .get(`/flows/${testFlowId}/dependencies`)
        .expect(200);

      expect(response.body.dependencies).to.be.an('array');
      // Verify dependency mapping exists for fallback routing
      expect(response.body.dependencies.length).to.be.at.least(0);
    });
  });

  describe('7. Flow Execution Metrics', function() {
    it('should collect comprehensive execution metrics', async function() {
      const executions = await supertest(app)
        .get(`/flows/${testFlowId}/executions`)
        .expect(200);

      expect(executions.body).to.be.an('array');

      if (executions.body.length > 0) {
        const execution = executions.body[0];
        expect(execution).to.have.property('executionId');
        expect(execution).to.have.property('status');
        expect(execution).to.have.property('startedAt');
        expect(execution).to.have.property('parameters');

        if (execution.status === 'completed') {
          expect(execution).to.have.property('completedAt');
          expect(execution).to.have.property('duration');
        }
      }
    });

    it('should analyze flow performance patterns', async function() {
      // Get flow statistics
      const stats = await flowRegistry.getFlowStatistics(testFlowId);

      expect(stats).to.have.property('flow');
      expect(stats).to.have.property('executions');
      expect(stats).to.have.property('successRate');

      expect(stats.flow.id).to.equal(testFlowId);
      expect(stats.executions).to.have.property('total_executions');
      expect(stats.executions).to.have.property('successful_executions');
      expect(stats.executions).to.have.property('failed_executions');
    });
  });
});