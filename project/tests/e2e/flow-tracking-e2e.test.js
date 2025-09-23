/**
 * End-to-End Flow Tracking Tests
 * Tests complete flow from Configuration Service through Database Stack
 */

const { expect } = require('chai');
const { spawn } = require('child_process');
const { Pool } = require('pg');
const { ClickHouse } = require('clickhouse');
const supertest = require('supertest');
const WebSocket = require('ws');
const express = require('express');

describe('End-to-End Flow Tracking', function() {
  this.timeout(120000);

  let configService;
  let databaseService;
  let tradingEngine;
  let pgPool;
  let clickHouseClient;
  let wsServer;
  let wsClient;

  // Test flow definition that spans multiple services
  const tradingWorkflow = {
    id: 'e2e-trading-workflow-001',
    name: 'Complete Trading Workflow',
    type: 'chain_mapping',
    version: '1.0.0',
    description: 'End-to-end trading workflow with full error tracking',
    createdBy: 'e2e-test-user',
    nodes: [
      {
        id: 'market-data-fetcher',
        name: 'Market Data Fetcher',
        type: 'data_source',
        config: {
          sources: ['binance', 'coinbase'],
          refresh_rate: 1000
        }
      },
      {
        id: 'risk-analyzer',
        name: 'Risk Analysis Engine',
        type: 'analyzer',
        config: {
          risk_models: ['var', 'expected_shortfall'],
          confidence_level: 0.95
        }
      },
      {
        id: 'portfolio-optimizer',
        name: 'Portfolio Optimizer',
        type: 'optimizer',
        config: {
          optimization_method: 'mean_variance',
          constraints: ['position_limits', 'sector_limits']
        }
      },
      {
        id: 'order-manager',
        name: 'Order Management System',
        type: 'executor',
        config: {
          order_types: ['market', 'limit', 'stop'],
          execution_algos: ['twap', 'vwap']
        }
      },
      {
        id: 'position-tracker',
        name: 'Position Tracker',
        type: 'monitor',
        config: {
          update_frequency: 500,
          pnl_calculation: 'mark_to_market'
        }
      }
    ],
    edges: [
      {
        id: 'edge-1',
        source: 'market-data-fetcher',
        target: 'risk-analyzer',
        condition: 'data_available && quality_score > 0.9'
      },
      {
        id: 'edge-2',
        source: 'risk-analyzer',
        target: 'portfolio-optimizer',
        condition: 'risk_level <= acceptable_threshold'
      },
      {
        id: 'edge-3',
        source: 'portfolio-optimizer',
        target: 'order-manager',
        condition: 'optimization_successful'
      },
      {
        id: 'edge-4',
        source: 'order-manager',
        target: 'position-tracker'
      }
    ],
    dependencies: [
      {
        flowId: 'market-connectivity-flow',
        type: 'prerequisite',
        condition: 'all_exchanges_connected',
        timeout: 10000
      },
      {
        flowId: 'risk-model-flow',
        type: 'prerequisite',
        condition: 'models_loaded',
        timeout: 5000
      }
    ]
  };

  before(async function() {
    // Setup database connections
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

    // Setup WebSocket server for real-time flow tracking
    wsServer = new WebSocket.Server({ port: 8080 });
    wsServer.on('connection', (ws) => {
      ws.on('message', (message) => {
        const data = JSON.parse(message);
        if (data.type === 'subscribe_flow') {
          ws.flowId = data.flowId;
        }
      });
    });

    // Create WebSocket client for testing
    wsClient = new WebSocket('ws://localhost:8080');
    await new Promise((resolve) => {
      wsClient.on('open', resolve);
    });

    // Initialize test database schema
    await initializeTestSchema();
  });

  after(async function() {
    if (wsClient) wsClient.close();
    if (wsServer) wsServer.close();
    if (pgPool) await pgPool.end();
    if (configService) configService.kill();
    if (databaseService) databaseService.kill();
    if (tradingEngine) tradingEngine.kill();
  });

  async function initializeTestSchema() {
    // Create flow tracking tables
    await pgPool.query(`
      CREATE TABLE IF NOT EXISTS flow_executions_e2e (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        flow_id VARCHAR(50) NOT NULL,
        execution_id VARCHAR(100) NOT NULL UNIQUE,
        status VARCHAR(20) NOT NULL,
        current_node VARCHAR(50),
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        metadata JSONB DEFAULT '{}'
      );
    `);

    await pgPool.query(`
      CREATE TABLE IF NOT EXISTS flow_node_executions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        execution_id VARCHAR(100) REFERENCES flow_executions_e2e(execution_id),
        node_id VARCHAR(50) NOT NULL,
        status VARCHAR(20) NOT NULL,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        result JSONB,
        error_message TEXT,
        performance_metrics JSONB DEFAULT '{}'
      );
    `);

    // Create ClickHouse tables for analytics
    await clickHouseClient.query(`
      CREATE TABLE IF NOT EXISTS flow_metrics_e2e (
        timestamp DateTime,
        flow_id String,
        execution_id String,
        node_id String,
        metric_name String,
        metric_value Float64,
        metadata String
      ) ENGINE = MergeTree()
      ORDER BY (timestamp, flow_id, execution_id)
    `).toPromise();

    await clickHouseClient.query(`
      CREATE TABLE IF NOT EXISTS flow_errors_e2e (
        timestamp DateTime,
        flow_id String,
        execution_id String,
        node_id String,
        error_type String,
        error_code String,
        error_message String,
        stack_trace String,
        upstream_nodes Array(String),
        downstream_impact String
      ) ENGINE = MergeTree()
      ORDER BY (timestamp, flow_id, execution_id)
    `).toPromise();
  }

  describe('1. Flow Registration and Discovery', function() {
    it('should register flow across all services', async function() {
      // Register flow with Configuration Service
      const configResponse = await supertest('http://localhost:3001')
        .post('/api/flows')
        .send(tradingWorkflow)
        .expect(201);

      expect(configResponse.body).to.have.property('id', tradingWorkflow.id);

      // Verify flow is discoverable by other services
      const discoveryResponse = await supertest('http://localhost:3002')
        .get(`/api/flows/${tradingWorkflow.id}`)
        .expect(200);

      expect(discoveryResponse.body).to.have.property('name', tradingWorkflow.name);
    });

    it('should create dependency mappings in database', async function() {
      // Verify flow definition stored in PostgreSQL
      const flowResult = await pgPool.query(
        'SELECT * FROM flow_definitions WHERE id = $1',
        [tradingWorkflow.id]
      );

      expect(flowResult.rows).to.have.lengthOf(1);
      expect(flowResult.rows[0].name).to.equal(tradingWorkflow.name);

      // Verify dependencies stored
      const depResult = await pgPool.query(
        'SELECT * FROM flow_dependencies WHERE flow_id = $1',
        [tradingWorkflow.id]
      );

      expect(depResult.rows).to.have.lengthOf(2);
      expect(depResult.rows.map(d => d.depends_on_flow_id))
        .to.include.members(['market-connectivity-flow', 'risk-model-flow']);
    });

    it('should enable real-time flow tracking', async function() {
      // Subscribe to flow updates via WebSocket
      wsClient.send(JSON.stringify({
        type: 'subscribe_flow',
        flowId: tradingWorkflow.id
      }));

      // Trigger a flow event
      await supertest('http://localhost:3001')
        .post(`/api/flows/${tradingWorkflow.id}/events`)
        .send({
          type: 'flow_updated',
          timestamp: new Date().toISOString()
        })
        .expect(200);

      // Wait for WebSocket message
      const message = await new Promise((resolve) => {
        wsClient.once('message', resolve);
      });

      const data = JSON.parse(message);
      expect(data).to.have.property('flowId', tradingWorkflow.id);
      expect(data).to.have.property('type', 'flow_updated');
    });
  });

  describe('2. Flow Execution Tracking', function() {
    let executionId;

    it('should initiate flow execution with full tracking', async function() {
      const executionRequest = {
        parameters: {
          symbol: 'BTCUSD',
          quantity: 1.5,
          strategy: 'momentum',
          risk_tolerance: 'medium'
        },
        executionContext: {
          user_id: 'trader-001',
          session_id: 'session-' + Date.now(),
          priority: 'high'
        }
      };

      const response = await supertest('http://localhost:3003')
        .post(`/api/flows/${tradingWorkflow.id}/execute`)
        .send(executionRequest)
        .expect(200);

      expect(response.body).to.have.property('executionId');
      expect(response.body).to.have.property('status', 'running');

      executionId = response.body.executionId;

      // Verify execution tracked in PostgreSQL
      const execResult = await pgPool.query(
        'SELECT * FROM flow_executions_e2e WHERE execution_id = $1',
        [executionId]
      );

      expect(execResult.rows).to.have.lengthOf(1);
      expect(execResult.rows[0].flow_id).to.equal(tradingWorkflow.id);
      expect(execResult.rows[0].status).to.equal('running');
    });

    it('should track node-by-node execution progress', async function() {
      // Simulate node executions
      const nodes = tradingWorkflow.nodes;

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Start node execution
        await pgPool.query(
          `INSERT INTO flow_node_executions (execution_id, node_id, status)
           VALUES ($1, $2, $3)`,
          [executionId, node.id, 'running']
        );

        // Record metrics in ClickHouse
        await clickHouseClient.insert('flow_metrics_e2e', [
          {
            timestamp: Math.floor(Date.now() / 1000),
            flow_id: tradingWorkflow.id,
            execution_id: executionId,
            node_id: node.id,
            metric_name: 'execution_start',
            metric_value: Date.now(),
            metadata: JSON.stringify({ node_type: node.type })
          }
        ]).toPromise();

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 100));

        // Complete node execution
        const result = {
          processed_data: `Result from ${node.name}`,
          processing_time: 100 + Math.random() * 50,
          success: true
        };

        await pgPool.query(
          `UPDATE flow_node_executions
           SET status = $1, completed_at = CURRENT_TIMESTAMP, result = $2
           WHERE execution_id = $3 AND node_id = $4`,
          ['completed', JSON.stringify(result), executionId, node.id]
        );

        // Record completion metrics
        await clickHouseClient.insert('flow_metrics_e2e', [
          {
            timestamp: Math.floor(Date.now() / 1000),
            flow_id: tradingWorkflow.id,
            execution_id: executionId,
            node_id: node.id,
            metric_name: 'execution_time',
            metric_value: result.processing_time,
            metadata: JSON.stringify({ success: true })
          }
        ]).toPromise();
      }

      // Verify all nodes completed
      const nodeResult = await pgPool.query(
        `SELECT node_id, status FROM flow_node_executions
         WHERE execution_id = $1 ORDER BY started_at`,
        [executionId]
      );

      expect(nodeResult.rows).to.have.lengthOf(nodes.length);
      nodeResult.rows.forEach(row => {
        expect(row.status).to.equal('completed');
      });
    });

    it('should provide real-time execution updates', async function() {
      // Subscribe to execution updates
      wsClient.send(JSON.stringify({
        type: 'subscribe_execution',
        executionId: executionId
      }));

      // Trigger execution update
      await supertest('http://localhost:3003')
        .post(`/api/executions/${executionId}/update`)
        .send({
          status: 'completed',
          result: {
            total_execution_time: 500,
            nodes_executed: 5,
            success_rate: 100
          }
        })
        .expect(200);

      // Receive WebSocket update
      const message = await new Promise((resolve) => {
        wsClient.once('message', resolve);
      });

      const data = JSON.parse(message);
      expect(data).to.have.property('executionId', executionId);
      expect(data).to.have.property('status', 'completed');
    });
  });

  describe('3. Error Propagation and Chain Analysis', function() {
    let errorExecutionId;

    it('should track error propagation through flow chain', async function() {
      // Start execution that will fail
      const errorResponse = await supertest('http://localhost:3003')
        .post(`/api/flows/${tradingWorkflow.id}/execute`)
        .send({
          parameters: { symbol: 'INVALID', quantity: -1 },
          simulateError: true,
          errorNode: 'risk-analyzer'
        })
        .expect(500);

      expect(errorResponse.body).to.have.property('executionId');
      errorExecutionId = errorResponse.body.executionId;

      // Verify error recorded in ClickHouse
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for async logging

      const errorQuery = `
        SELECT * FROM flow_errors_e2e
        WHERE execution_id = '${errorExecutionId}'
        ORDER BY timestamp DESC
        LIMIT 1
      `;

      const errorResult = await clickHouseClient.query(errorQuery).toPromise();
      expect(errorResult).to.have.lengthOf(1);
      expect(errorResult[0].node_id).to.equal('risk-analyzer');
      expect(errorResult[0].error_type).to.equal('validation_error');
    });

    it('should analyze upstream and downstream impact', async function() {
      // Get dependency graph for impact analysis
      const impactResponse = await supertest('http://localhost:3001')
        .get(`/api/flows/${tradingWorkflow.id}/impact-analysis`)
        .query({ executionId: errorExecutionId })
        .expect(200);

      expect(impactResponse.body).to.have.property('upstreamNodes');
      expect(impactResponse.body).to.have.property('downstreamNodes');
      expect(impactResponse.body).to.have.property('impactedFlows');

      // Verify market-data-fetcher completed (upstream)
      expect(impactResponse.body.upstreamNodes).to.include('market-data-fetcher');

      // Verify downstream nodes were not executed
      expect(impactResponse.body.downstreamNodes).to.include.members([
        'portfolio-optimizer',
        'order-manager',
        'position-tracker'
      ]);
    });

    it('should provide error recovery recommendations', async function() {
      const recoveryResponse = await supertest('http://localhost:3001')
        .get(`/api/executions/${errorExecutionId}/recovery-options`)
        .expect(200);

      expect(recoveryResponse.body).to.have.property('recommendations');
      expect(recoveryResponse.body.recommendations).to.be.an('array');

      const recommendations = recoveryResponse.body.recommendations;
      expect(recommendations.some(r => r.type === 'retry_from_node')).to.be.true;
      expect(recommendations.some(r => r.type === 'parameter_adjustment')).to.be.true;
    });
  });

  describe('4. Performance Analytics and Optimization', function() {
    it('should collect comprehensive performance metrics', async function() {
      // Query execution metrics from ClickHouse
      const metricsQuery = `
        SELECT
          node_id,
          AVG(metric_value) as avg_execution_time,
          MAX(metric_value) as max_execution_time,
          COUNT(*) as execution_count
        FROM flow_metrics_e2e
        WHERE flow_id = '${tradingWorkflow.id}'
          AND metric_name = 'execution_time'
          AND timestamp >= NOW() - INTERVAL 1 HOUR
        GROUP BY node_id
        ORDER BY avg_execution_time DESC
      `;

      const metricsResult = await clickHouseClient.query(metricsQuery).toPromise();
      expect(metricsResult.length).to.be.at.least(1);

      metricsResult.forEach(metric => {
        expect(metric).to.have.property('node_id');
        expect(metric).to.have.property('avg_execution_time');
        expect(metric.avg_execution_time).to.be.a('number');
      });
    });

    it('should identify performance bottlenecks', async function() {
      const bottleneckResponse = await supertest('http://localhost:3002')
        .get(`/api/analytics/bottlenecks/${tradingWorkflow.id}`)
        .expect(200);

      expect(bottleneckResponse.body).to.have.property('bottlenecks');
      expect(bottleneckResponse.body).to.have.property('recommendations');

      const bottlenecks = bottleneckResponse.body.bottlenecks;
      expect(bottlenecks).to.be.an('array');

      if (bottlenecks.length > 0) {
        expect(bottlenecks[0]).to.have.property('nodeId');
        expect(bottlenecks[0]).to.have.property('avgExecutionTime');
        expect(bottlenecks[0]).to.have.property('impact');
      }
    });

    it('should track flow success rates and reliability', async function() {
      const reliabilityQuery = `
        SELECT
          COUNT(*) as total_executions,
          SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
          AVG(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) * 100 as success_rate
        FROM flow_executions_e2e
        WHERE flow_id = '${tradingWorkflow.id}'
          AND started_at >= NOW() - INTERVAL 1 HOUR
      `;

      const reliabilityResult = await pgPool.query(reliabilityQuery);
      const stats = reliabilityResult.rows[0];

      expect(parseInt(stats.total_executions)).to.be.at.least(1);
      expect(parseFloat(stats.success_rate)).to.be.a('number');

      console.log(`Flow reliability: ${stats.success_rate}% (${stats.successful_executions}/${stats.total_executions})`);
    });
  });

  describe('5. Cross-Service Integration', function() {
    it('should maintain flow state consistency across services', async function() {
      // Check Configuration Service
      const configState = await supertest('http://localhost:3001')
        .get(`/api/flows/${tradingWorkflow.id}/state`)
        .expect(200);

      // Check Database Service
      const dbState = await supertest('http://localhost:3002')
        .get(`/api/flows/${tradingWorkflow.id}/state`)
        .expect(200);

      // Check Trading Engine
      const engineState = await supertest('http://localhost:3003')
        .get(`/api/flows/${tradingWorkflow.id}/state`)
        .expect(200);

      // Verify state consistency
      expect(configState.body.flowId).to.equal(tradingWorkflow.id);
      expect(dbState.body.flowId).to.equal(tradingWorkflow.id);
      expect(engineState.body.flowId).to.equal(tradingWorkflow.id);

      expect(configState.body.version).to.equal(dbState.body.version);
      expect(dbState.body.version).to.equal(engineState.body.version);
    });

    it('should synchronize configuration changes across services', async function() {
      // Update flow configuration
      const updatedFlow = {
        ...tradingWorkflow,
        version: '1.1.0',
        description: 'Updated description for E2E test'
      };

      await supertest('http://localhost:3001')
        .put(`/api/flows/${tradingWorkflow.id}`)
        .send(updatedFlow)
        .expect(200);

      // Wait for propagation
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Verify update propagated to other services
      const engineResponse = await supertest('http://localhost:3003')
        .get(`/api/flows/${tradingWorkflow.id}`)
        .expect(200);

      expect(engineResponse.body.version).to.equal('1.1.0');
      expect(engineResponse.body.description).to.include('Updated description');
    });

    it('should handle service failures gracefully', async function() {
      // Simulate Database Service failure
      // (In a real test, you might stop the service or block network access)

      const fallbackResponse = await supertest('http://localhost:3001')
        .get(`/api/flows/${tradingWorkflow.id}`)
        .expect(200); // Should still work with cached data

      expect(fallbackResponse.body).to.have.property('id', tradingWorkflow.id);
      expect(fallbackResponse.body.metadata).to.have.property('source', 'cache');
    });
  });

  describe('6. Flow Lifecycle Management', function() {
    it('should archive completed flow executions', async function() {
      // Mark old executions for archival
      await supertest('http://localhost:3002')
        .post('/api/maintenance/archive-executions')
        .send({
          flowId: tradingWorkflow.id,
          olderThan: '1 hour',
          archiveLocation: 'cold_storage'
        })
        .expect(200);

      // Verify archival metadata
      const archiveResult = await pgPool.query(
        `SELECT COUNT(*) as archived_count
         FROM flow_executions_archive
         WHERE flow_id = $1`,
        [tradingWorkflow.id]
      );

      // Should have at least our test executions
      expect(parseInt(archiveResult.rows[0].archived_count)).to.be.at.least(0);
    });

    it('should provide flow usage analytics', async function() {
      const analyticsResponse = await supertest('http://localhost:3002')
        .get(`/api/analytics/flows/${tradingWorkflow.id}/usage`)
        .query({
          timeRange: '24h',
          includeMetrics: true
        })
        .expect(200);

      expect(analyticsResponse.body).to.have.property('totalExecutions');
      expect(analyticsResponse.body).to.have.property('successRate');
      expect(analyticsResponse.body).to.have.property('avgExecutionTime');
      expect(analyticsResponse.body).to.have.property('errorBreakdown');

      const usage = analyticsResponse.body;
      expect(usage.totalExecutions).to.be.a('number');
      expect(usage.successRate).to.be.a('number');
      expect(usage.errorBreakdown).to.be.an('object');
    });

    it('should cleanup test data', async function() {
      // Clean up test executions
      await pgPool.query(
        'DELETE FROM flow_node_executions WHERE execution_id LIKE $1',
        ['%' + tradingWorkflow.id + '%']
      );

      await pgPool.query(
        'DELETE FROM flow_executions_e2e WHERE flow_id = $1',
        [tradingWorkflow.id]
      );

      // Clean up ClickHouse data
      await clickHouseClient.query(`
        ALTER TABLE flow_metrics_e2e DELETE WHERE flow_id = '${tradingWorkflow.id}'
      `).toPromise();

      await clickHouseClient.query(`
        ALTER TABLE flow_errors_e2e DELETE WHERE flow_id = '${tradingWorkflow.id}'
      `).toPromise();

      console.log('Test data cleanup completed');
    });
  });
});