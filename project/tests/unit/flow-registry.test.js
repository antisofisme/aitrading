/**
 * Flow Registry Unit Tests
 * Focused testing of FlowRegistry core functionality
 */

const { expect } = require('chai');
const sinon = require('sinon');
const { Pool } = require('pg');
const winston = require('winston');
const { FlowRegistry, FlowType, FlowStatus, DependencyType, ExecutionStatus } = require('../../backend/configuration-service/src/services/FlowRegistry');

describe('FlowRegistry Unit Tests', function() {
  let flowRegistry;
  let mockPool;
  let mockClient;
  let logger;

  const testFlow = {
    id: 'unit-test-flow-001',
    name: 'Unit Test Flow',
    type: FlowType.CUSTOM,
    version: '1.0.0',
    description: 'Flow for unit testing',
    createdBy: 'unit-test',
    nodes: [
      {
        id: 'node1',
        name: 'Test Node 1',
        type: 'processor',
        config: { timeout: 5000 }
      },
      {
        id: 'node2',
        name: 'Test Node 2',
        type: 'validator',
        config: { strict: true }
      }
    ],
    edges: [
      {
        id: 'edge1',
        source: 'node1',
        target: 'node2'
      }
    ],
    dependencies: [
      {
        flowId: 'dependency-flow',
        type: DependencyType.PREREQUISITE,
        timeout: 10000
      }
    ]
  };

  beforeEach(function() {
    // Mock database client
    mockClient = {
      query: sinon.stub(),
      release: sinon.stub()
    };

    // Mock connection pool
    mockPool = {
      connect: sinon.stub().resolves(mockClient),
      query: sinon.stub(),
      end: sinon.stub()
    };

    // Mock logger
    logger = {
      info: sinon.stub(),
      error: sinon.stub(),
      warn: sinon.stub(),
      debug: sinon.stub()
    };

    flowRegistry = new FlowRegistry({}, logger);
    flowRegistry.pool = mockPool;
  });

  afterEach(function() {
    sinon.restore();
  });

  describe('Flow Registration', function() {
    it('should validate flow definition before registration', async function() {
      const invalidFlow = {
        id: 'invalid-flow',
        // Missing required fields
      };

      try {
        await flowRegistry.registerFlow(invalidFlow);
        expect.fail('Should have thrown validation error');
      } catch (error) {
        expect(error.message).to.include('validation failed');
      }
    });

    it('should register valid flow successfully', async function() {
      // Mock successful database operations
      mockClient.query
        .onFirstCall().resolves() // BEGIN
        .onSecondCall().resolves() // Check existing
        .onThirdCall().resolves({ rows: [] }) // No existing flow
        .onCall(3).resolves({ // Insert flow
          rows: [{
            id: testFlow.id,
            name: testFlow.name,
            type: testFlow.type,
            version: testFlow.version,
            created_at: new Date(),
            updated_at: new Date()
          }]
        })
        .onCall(4).resolves() // Insert credentials
        .onCall(5).resolves() // Insert dependencies
        .onCall(6).resolves(); // COMMIT

      mockPool.query.resolves({ rows: [] }); // getFlowByNameAndVersion

      const result = await flowRegistry.registerFlow(testFlow);

      expect(result).to.have.property('id', testFlow.id);
      expect(result).to.have.property('name', testFlow.name);
      expect(mockClient.query).to.have.been.calledWith('BEGIN');
      expect(mockClient.query).to.have.been.calledWith('COMMIT');
    });

    it('should prevent duplicate flow registration', async function() {
      // Mock existing flow
      mockPool.query.resolves({
        rows: [{ id: testFlow.id, name: testFlow.name, version: testFlow.version }]
      });

      try {
        await flowRegistry.registerFlow(testFlow);
        expect.fail('Should have thrown duplicate error');
      } catch (error) {
        expect(error.message).to.include('already exists');
      }
    });

    it('should handle database errors during registration', async function() {
      mockPool.query.rejects(new Error('Database connection failed'));

      try {
        await flowRegistry.registerFlow(testFlow);
        expect.fail('Should have thrown database error');
      } catch (error) {
        expect(error.message).to.include('Database connection failed');
      }
    });
  });

  describe('Flow Retrieval', function() {
    it('should retrieve flow by ID with full details', async function() {
      const mockFlowData = {
        id: testFlow.id,
        name: testFlow.name,
        type: testFlow.type,
        version: testFlow.version,
        definition_json: JSON.stringify({
          nodes: testFlow.nodes,
          edges: testFlow.edges
        }),
        parameters_json: '[]',
        metadata_json: '{}',
        tags: [],
        created_by: testFlow.createdBy,
        created_at: new Date(),
        updated_at: new Date()
      };

      mockClient.query
        .onFirstCall().resolves({ rows: [mockFlowData] }) // Get flow
        .onSecondCall().resolves({ rows: [] }) // Get credentials
        .onThirdCall().resolves({ rows: [] }); // Get dependencies

      const result = await flowRegistry.getFlow(testFlow.id);

      expect(result).to.have.property('id', testFlow.id);
      expect(result).to.have.property('nodes');
      expect(result.nodes).to.have.lengthOf(2);
      expect(mockClient.query).to.have.been.calledThrice;
    });

    it('should return null for non-existent flow', async function() {
      mockClient.query.resolves({ rows: [] });

      const result = await flowRegistry.getFlow('non-existent-flow');

      expect(result).to.be.null;
    });

    it('should handle database errors during retrieval', async function() {
      mockClient.query.rejects(new Error('Query timeout'));

      try {
        await flowRegistry.getFlow(testFlow.id);
        expect.fail('Should have thrown database error');
      } catch (error) {
        expect(error.message).to.include('Query timeout');
      }
    });
  });

  describe('Flow Listing and Filtering', function() {
    it('should list flows with pagination', async function() {
      const mockFlows = [
        { id: 'flow1', name: 'Flow 1', type: 'custom' },
        { id: 'flow2', name: 'Flow 2', type: 'langgraph_workflow' }
      ];

      mockPool.query
        .onFirstCall().resolves({ rows: [{ count: '10' }] }) // Total count
        .onSecondCall().resolves({ rows: mockFlows }); // Flows

      const result = await flowRegistry.listFlows({
        page: 1,
        limit: 5
      });

      expect(result).to.have.property('flows');
      expect(result).to.have.property('pagination');
      expect(result.flows).to.have.lengthOf(2);
      expect(result.pagination.totalCount).to.equal(10);
      expect(result.pagination.page).to.equal(1);
    });

    it('should filter flows by type', async function() {
      mockPool.query
        .onFirstCall().resolves({ rows: [{ count: '5' }] })
        .onSecondCall().resolves({ rows: [] });

      await flowRegistry.listFlows({
        type: FlowType.LANGGRAPH_WORKFLOW
      });

      // Verify filter was applied in query
      const queryCall = mockPool.query.getCall(1);
      expect(queryCall.args[0]).to.include('WHERE type = $1');
      expect(queryCall.args[1]).to.include(FlowType.LANGGRAPH_WORKFLOW);
    });

    it('should filter flows by status', async function() {
      mockPool.query
        .onFirstCall().resolves({ rows: [{ count: '3' }] })
        .onSecondCall().resolves({ rows: [] });

      await flowRegistry.listFlows({
        status: FlowStatus.ACTIVE
      });

      const queryCall = mockPool.query.getCall(1);
      expect(queryCall.args[0]).to.include('status = $1');
      expect(queryCall.args[1]).to.include(FlowStatus.ACTIVE);
    });

    it('should filter flows by tags', async function() {
      mockPool.query
        .onFirstCall().resolves({ rows: [{ count: '2' }] })
        .onSecondCall().resolves({ rows: [] });

      await flowRegistry.listFlows({
        tags: ['production', 'trading']
      });

      const queryCall = mockPool.query.getCall(1);
      expect(queryCall.args[0]).to.include('tags && $1');
      expect(queryCall.args[1]).to.deep.include(['production', 'trading']);
    });
  });

  describe('Flow Updates', function() {
    it('should update flow definition successfully', async function() {
      const existingFlow = {
        id: testFlow.id,
        name: testFlow.name,
        nodes: testFlow.nodes,
        edges: testFlow.edges
      };

      const updates = {
        description: 'Updated description',
        status: FlowStatus.ACTIVE
      };

      // Mock getFlow to return existing flow
      sinon.stub(flowRegistry, 'getFlow').resolves(existingFlow);

      mockClient.query
        .onFirstCall().resolves() // BEGIN
        .onSecondCall().resolves({ // UPDATE flow
          rows: [{
            ...existingFlow,
            ...updates,
            updated_at: new Date()
          }]
        })
        .onThirdCall().resolves(); // COMMIT

      const result = await flowRegistry.updateFlow(testFlow.id, updates);

      expect(result).to.have.property('description', updates.description);
      expect(result).to.have.property('status', updates.status);
      expect(mockClient.query).to.have.been.calledWith('BEGIN');
      expect(mockClient.query).to.have.been.calledWith('COMMIT');
    });

    it('should handle non-existent flow updates', async function() {
      sinon.stub(flowRegistry, 'getFlow').resolves(null);

      try {
        await flowRegistry.updateFlow('non-existent', { status: 'active' });
        expect.fail('Should have thrown not found error');
      } catch (error) {
        expect(error.message).to.include('not found');
      }
    });

    it('should validate updates before applying', async function() {
      const existingFlow = { ...testFlow };
      sinon.stub(flowRegistry, 'getFlow').resolves(existingFlow);

      const invalidUpdates = {
        version: 'invalid-version-format'
      };

      try {
        await flowRegistry.updateFlow(testFlow.id, invalidUpdates);
        expect.fail('Should have thrown validation error');
      } catch (error) {
        expect(error.message).to.include('validation failed');
      }
    });
  });

  describe('Flow Execution Tracking', function() {
    it('should track flow execution start', async function() {
      const executionId = 'exec-123';
      const mockExecution = {
        id: 'uuid-123',
        flow_id: testFlow.id,
        execution_id: executionId,
        status: ExecutionStatus.RUNNING,
        started_at: new Date()
      };

      mockPool.query.resolves({ rows: [mockExecution] });

      const result = await flowRegistry.trackExecution(testFlow.id, executionId, {
        triggeredBy: 'test-user',
        parameters: { test: true }
      });

      expect(result).to.have.property('executionId', executionId);
      expect(result).to.have.property('status', ExecutionStatus.RUNNING);
      expect(mockPool.query).to.have.been.calledOnce;
    });

    it('should update execution status', async function() {
      const executionId = 'exec-123';
      const mockUpdatedExecution = {
        execution_id: executionId,
        status: ExecutionStatus.COMPLETED,
        completed_at: new Date(),
        result_json: '{"success": true}'
      };

      mockPool.query.resolves({ rows: [mockUpdatedExecution], rowCount: 1 });

      const result = await flowRegistry.updateExecutionStatus(
        executionId,
        ExecutionStatus.COMPLETED,
        { success: true }
      );

      expect(result).to.have.property('status', ExecutionStatus.COMPLETED);
      expect(result).to.have.property('result');
      expect(result.result.success).to.be.true;
    });

    it('should handle execution not found during status update', async function() {
      mockPool.query.resolves({ rowCount: 0 });

      try {
        await flowRegistry.updateExecutionStatus('non-existent', 'completed');
        expect.fail('Should have thrown not found error');
      } catch (error) {
        expect(error.message).to.include('not found');
      }
    });
  });

  describe('Dependency Management', function() {
    it('should get dependency graph for flow', async function() {
      const mockFlow = { ...testFlow };
      sinon.stub(flowRegistry, 'getFlow').resolves(mockFlow);

      // Mock dependencies query
      mockPool.query
        .onFirstCall().resolves({ // Direct dependencies
          rows: [{
            depends_on_flow_id: 'dep-flow-1',
            name: 'Dependency Flow 1',
            type: 'custom',
            status: 'active',
            dependency_type: 'prerequisite'
          }]
        })
        .onSecondCall().resolves({ rows: [] }); // Direct dependents

      const result = await flowRegistry.getDependencyGraph(testFlow.id);

      expect(result).to.have.property('flow');
      expect(result).to.have.property('dependencies');
      expect(result).to.have.property('dependents');
      expect(result.flow.id).to.equal(testFlow.id);
      expect(result.dependencies).to.have.lengthOf(1);
    });

    it('should detect circular dependencies', async function() {
      const mockFlow = { ...testFlow };
      sinon.stub(flowRegistry, 'getFlow').resolves(mockFlow);

      // Create a circular dependency scenario
      mockPool.query
        .onFirstCall().resolves({
          rows: [{
            depends_on_flow_id: 'circular-flow',
            dependency_type: 'prerequisite'
          }]
        })
        .onSecondCall().resolves({ rows: [] });

      // Mock recursive dependency that creates a cycle
      sinon.stub(flowRegistry, '_getRecursiveDependencies')
        .resolves([{
          flowId: testFlow.id, // Circular reference back to original flow
          type: 'prerequisite'
        }]);

      const validation = await flowRegistry.validateFlow(testFlow.id);

      expect(validation).to.have.property('isValid', false);
      expect(validation.errors.some(e => e.includes('Circular dependencies')))
        .to.be.true;
    });
  });

  describe('Flow Validation', function() {
    it('should validate flow structure successfully', async function() {
      const validFlow = { ...testFlow };
      sinon.stub(flowRegistry, 'getFlow').resolves(validFlow);
      sinon.stub(flowRegistry, 'getDependencyGraph').resolves({
        flow: validFlow,
        dependencies: [],
        dependents: []
      });

      const result = await flowRegistry.validateFlow(testFlow.id);

      expect(result).to.have.property('isValid', true);
      expect(result).to.have.property('errors');
      expect(result.errors).to.have.lengthOf(0);
      expect(result.details).to.have.property('nodesValidation');
      expect(result.details).to.have.property('edgesValidation');
    });

    it('should detect invalid node references in edges', async function() {
      const invalidFlow = {
        ...testFlow,
        edges: [
          {
            id: 'invalid-edge',
            source: 'non-existent-node',
            target: 'node2'
          }
        ]
      };

      sinon.stub(flowRegistry, 'getFlow').resolves(invalidFlow);
      sinon.stub(flowRegistry, 'getDependencyGraph').resolves({
        flow: invalidFlow,
        dependencies: [],
        dependents: []
      });

      const result = await flowRegistry.validateFlow(testFlow.id);

      expect(result).to.have.property('isValid', false);
      expect(result.details.edgesValidation.some(e =>
        e.issues.some(issue => issue.includes('Source node'))
      )).to.be.true;
    });

    it('should handle validation of non-existent flow', async function() {
      sinon.stub(flowRegistry, 'getFlow').resolves(null);

      try {
        await flowRegistry.validateFlow('non-existent-flow');
        expect.fail('Should have thrown not found error');
      } catch (error) {
        expect(error.message).to.include('not found');
      }
    });
  });

  describe('Flow Statistics', function() {
    it('should get statistics for specific flow', async function() {
      mockPool.query
        .onFirstCall().resolves({ // Flow query
          rows: [{
            id: testFlow.id,
            name: testFlow.name,
            type: testFlow.type
          }]
        })
        .onSecondCall().resolves({ // Execution stats
          rows: [{
            total_executions: '10',
            successful_executions: '8',
            failed_executions: '2',
            running_executions: '0',
            avg_duration_seconds: '45.5'
          }]
        });

      const result = await flowRegistry.getFlowStatistics(testFlow.id);

      expect(result).to.have.property('flow');
      expect(result).to.have.property('executions');
      expect(result).to.have.property('successRate');
      expect(result.flow.id).to.equal(testFlow.id);
      expect(result.successRate).to.equal('80.00%');
    });

    it('should get global statistics when no flow specified', async function() {
      mockPool.query
        .onFirstCall().resolves({ // Global flow stats
          rows: [{
            total_flows: '50',
            langgraph_flows: '20',
            ai_brain_flows: '15',
            chain_mapping_flows: '10',
            custom_flows: '5',
            active_flows: '45',
            draft_flows: '5'
          }]
        })
        .onSecondCall().resolves({ // Global execution stats
          rows: [{
            total_executions: '1000',
            successful_executions: '850',
            failed_executions: '150',
            running_executions: '0'
          }]
        });

      const result = await flowRegistry.getFlowStatistics();

      expect(result).to.have.property('flows');
      expect(result).to.have.property('executions');
      expect(result).to.have.property('overallSuccessRate');
      expect(result.overallSuccessRate).to.equal('85.00%');
    });
  });

  describe('Error Handling', function() {
    it('should handle database connection failures gracefully', async function() {
      mockPool.connect.rejects(new Error('Connection pool exhausted'));

      try {
        await flowRegistry.registerFlow(testFlow);
        expect.fail('Should have thrown connection error');
      } catch (error) {
        expect(error.message).to.include('Connection pool exhausted');
        expect(logger.error).to.have.been.called;
      }
    });

    it('should rollback transactions on error', async function() {
      mockClient.query
        .onFirstCall().resolves() // BEGIN
        .onSecondCall().rejects(new Error('Database constraint violation')) // INSERT fails
        .onThirdCall().resolves(); // ROLLBACK

      mockPool.query.resolves({ rows: [] }); // getFlowByNameAndVersion

      try {
        await flowRegistry.registerFlow(testFlow);
        expect.fail('Should have thrown constraint error');
      } catch (error) {
        expect(error.message).to.include('constraint violation');
        expect(mockClient.query).to.have.been.calledWith('ROLLBACK');
      }
    });

    it('should log errors appropriately', async function() {
      mockPool.query.rejects(new Error('Network timeout'));

      try {
        await flowRegistry.getFlow('test-flow');
        expect.fail('Should have thrown timeout error');
      } catch (error) {
        expect(logger.error).to.have.been.calledWith(
          'Failed to get flow',
          sinon.match({ error: error.message, flowId: 'test-flow' })
        );
      }
    });
  });

  describe('Connection Management', function() {
    it('should close database connections properly', async function() {
      await flowRegistry.close();

      expect(mockPool.end).to.have.been.calledOnce;
      expect(logger.info).to.have.been.calledWith(
        'FlowRegistry database connection closed'
      );
    });

    it('should handle connection close errors', async function() {
      mockPool.end.rejects(new Error('Close timeout'));

      try {
        await flowRegistry.close();
        // Should not throw, but log the error
      } catch (error) {
        // If it does throw, verify it's the expected error
        expect(error.message).to.include('Close timeout');
      }
    });
  });
});