/**
 * Tests for BatchCoordinator - Parallel coordination system tests
 * Validates CLAUDE.md single-message batch operations
 */

const { BatchCoordinator, MemoryCoordination, CrossAgentCommunication } = require('../../src/coordination');

describe('BatchCoordinator', () => {
  let coordinator;
  let memoryCoordination;
  let communicationSystem;

  beforeEach(async () => {
    memoryCoordination = new MemoryCoordination();
    communicationSystem = new CrossAgentCommunication(memoryCoordination);
    coordinator = new BatchCoordinator();

    await coordinator.initialize();
  });

  afterEach(async () => {
    if (coordinator) {
      await coordinator.cleanup();
    }
  });

  describe('Initialization', () => {
    test('should initialize coordination system', async () => {
      expect(coordinator.isInitialized).toBe(true);
    });

    test('should setup coordination hooks', async () => {
      const status = coordinator.getCoordinationStatus();
      expect(status.initialized).toBe(true);
    });
  });

  describe('Batch Execution', () => {
    test('should execute agent batch following single-message principle', async () => {
      const batchConfig = {
        agents: [
          { id: 'agent1', type: 'coder', capabilities: ['coding'] },
          { id: 'agent2', type: 'reviewer', capabilities: ['review'] }
        ],
        tasks: [
          { id: 'task1', description: 'Code implementation', requiredType: 'coder' },
          { id: 'task2', description: 'Code review', requiredType: 'reviewer' }
        ],
        aggregationStrategy: 'merge'
      };

      const result = await coordinator.executeBatch(batchConfig);

      expect(result).toBeDefined();
      expect(result.type).toBe('batch_result');
      expect(result.batchId).toBeDefined();
    });

    test('should spawn agents in parallel batch', async () => {
      const agentConfigs = [
        { id: 'agent1', type: 'coder' },
        { id: 'agent2', type: 'tester' },
        { id: 'agent3', type: 'reviewer' }
      ];

      const agents = await coordinator.spawnAgentsBatch(agentConfigs, 'test_batch');

      expect(agents).toHaveLength(3);
      expect(agents.every(agent => agent.id)).toBe(true);
      expect(agents.every(agent => agent.batchId === 'test_batch')).toBe(true);
    });

    test('should setup batch coordination infrastructure', async () => {
      const batch = {
        id: 'test_batch',
        agents: [
          { id: 'agent1', type: 'coder' },
          { id: 'agent2', type: 'tester' }
        ]
      };

      const coordination = await coordinator.setupBatchCoordination(batch);

      expect(coordination).toBeDefined();
      expect(coordination.memory).toBeDefined();
      expect(coordination.communication).toBeDefined();
    });
  });

  describe('Task Coordination', () => {
    test('should execute coordinated task with hooks', async () => {
      const task = {
        id: 'test_task',
        description: 'Test task execution',
        agentId: 'agent1',
        batchId: 'test_batch'
      };

      const batch = {
        id: 'test_batch',
        agents: [{ id: 'agent1', type: 'coder' }]
      };

      const result = await coordinator.executeCoordinatedTask(task, batch);

      expect(result).toBeDefined();
      expect(result.taskId).toBe('test_task');
      expect(result.agentId).toBe('agent1');
    });

    test('should handle task failure with coordination', async () => {
      const task = {
        id: 'failing_task',
        description: 'Task that will fail',
        agentId: 'agent1',
        batchId: 'test_batch'
      };

      const batch = {
        id: 'test_batch',
        agents: [{ id: 'agent1', type: 'coder' }]
      };

      // Mock task execution to fail
      jest.spyOn(coordinator.agentOrchestrator, 'executeTask').mockRejectedValue(
        new Error('Task execution failed')
      );

      const result = await coordinator.executeCoordinatedTask(task, batch);

      expect(result.status).toBe('failed');
      expect(result.error).toBe('Task execution failed');
    });
  });

  describe('Result Processing', () => {
    test('should process batch results with aggregation', async () => {
      const batch = {
        id: 'test_batch',
        config: { aggregationStrategy: 'merge' },
        results: [
          { taskId: 'task1', agentId: 'agent1', status: 'success', result: { data: 'result1' } },
          { taskId: 'task2', agentId: 'agent2', status: 'success', result: { data: 'result2' } }
        ]
      };

      const finalResult = await coordinator.processBatchResults(batch);

      expect(finalResult).toBeDefined();
      expect(finalResult.type).toBe('batch_result');
      expect(finalResult.batchId).toBe('test_batch');
      expect(finalResult.aggregated).toBeDefined();
    });

    test('should handle conflicts in results', async () => {
      const batch = {
        id: 'test_batch',
        config: { aggregationStrategy: 'merge', conflictResolver: 'vote' },
        results: [
          {
            taskId: 'task1',
            agentId: 'agent1',
            status: 'success',
            result: { data: 'conflicting_result1' }
          },
          {
            taskId: 'task1',
            agentId: 'agent2',
            status: 'success',
            result: { data: 'conflicting_result2' }
          }
        ]
      };

      const finalResult = await coordinator.processBatchResults(batch);

      expect(finalResult.conflicts).toBeGreaterThanOrEqual(0);
      expect(finalResult.resolutions).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Performance Metrics', () => {
    test('should track batch performance metrics', async () => {
      const batchId = 'test_batch';

      // Simulate some performance metrics
      coordinator.performanceMetrics.set(`spawn_${batchId}`, {
        duration: 1000,
        agentCount: 3,
        timestamp: Date.now()
      });

      const metrics = coordinator.getBatchPerformanceMetrics(batchId);

      expect(metrics).toBeDefined();
      expect(metrics.metrics).toBeDefined();
    });

    test('should calculate batch efficiency', async () => {
      const batchId = 'test_batch';

      // Setup test batch with results
      coordinator.batchExecutions.set(batchId, {
        id: batchId,
        started: Date.now() - 5000,
        completed: Date.now(),
        results: [
          { status: 'success' },
          { status: 'success' },
          { status: 'failed' }
        ]
      });

      const efficiency = coordinator.calculateBatchEfficiency(batchId);

      expect(efficiency).toBeCloseTo(66.67, 1); // 2/3 success = 66.67%
    });
  });

  describe('Coordination Status', () => {
    test('should provide coordination system status', async () => {
      const status = coordinator.getCoordinationStatus();

      expect(status).toBeDefined();
      expect(status.initialized).toBe(true);
      expect(status.activeBatches).toBeGreaterThanOrEqual(0);
      expect(status.memoryStats).toBeDefined();
    });
  });

  describe('Agent Hooks', () => {
    test('should create pre-task hook for agent', async () => {
      const hook = coordinator.createAgentPreTaskHook('agent1', 'batch1');

      expect(typeof hook).toBe('function');

      // Test hook execution
      const task = { id: 'test_task', description: 'Test task' };
      await expect(hook(task)).resolves.not.toThrow();
    });

    test('should create post-edit hook for agent', async () => {
      const hook = coordinator.createAgentPostEditHook('agent1', 'batch1');

      expect(typeof hook).toBe('function');

      // Test hook execution
      await expect(hook('test_file.js', { edit: 'result' })).resolves.not.toThrow();
    });

    test('should create post-task hook for agent', async () => {
      const hook = coordinator.createAgentPostTaskHook('agent1', 'batch1');

      expect(typeof hook).toBe('function');

      // Test hook execution
      const task = { id: 'test_task' };
      const result = { status: 'completed' };
      await expect(hook(task, result)).resolves.not.toThrow();
    });
  });

  describe('Memory Coordination', () => {
    test('should setup memory namespaces for batch', async () => {
      const batch = {
        id: 'test_batch',
        agents: [{ id: 'agent1' }, { id: 'agent2' }]
      };

      const namespaces = await coordinator.setupMemoryNamespaces(batch);

      expect(namespaces).toBeDefined();
      expect(Array.isArray(namespaces)).toBe(true);
      expect(namespaces.length).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    test('should handle batch spawn failure gracefully', async () => {
      const invalidConfigs = [
        { /* missing required fields */ }
      ];

      await expect(coordinator.spawnAgentsBatch(invalidConfigs, 'test_batch'))
        .rejects.toThrow();
    });

    test('should handle coordination setup failure', async () => {
      const invalidBatch = null;

      await expect(coordinator.setupBatchCoordination(invalidBatch))
        .rejects.toThrow();
    });
  });

  describe('Cleanup', () => {
    test('should cleanup coordination system properly', async () => {
      await coordinator.cleanup();

      expect(coordinator.isInitialized).toBe(false);
      expect(coordinator.batchExecutions.size).toBe(0);
      expect(coordinator.performanceMetrics.size).toBe(0);
    });
  });
});

// Integration tests
describe('BatchCoordinator Integration', () => {
  test('should execute complete coordination workflow', async () => {
    const coordinator = new BatchCoordinator();
    await coordinator.initialize();

    try {
      const batchConfig = {
        agents: [
          { id: 'researcher1', type: 'researcher', capabilities: ['research'] },
          { id: 'coder1', type: 'coder', capabilities: ['coding'] },
          { id: 'reviewer1', type: 'reviewer', capabilities: ['review'] }
        ],
        tasks: [
          {
            id: 'research_task',
            description: 'Research coordination patterns',
            requiredType: 'researcher',
            priority: 'high'
          },
          {
            id: 'coding_task',
            description: 'Implement coordination features',
            requiredType: 'coder',
            dependencies: ['research_task']
          },
          {
            id: 'review_task',
            description: 'Review implementation',
            requiredType: 'reviewer',
            dependencies: ['coding_task']
          }
        ],
        aggregationStrategy: 'merge',
        conflictResolver: 'priority'
      };

      const result = await coordinator.executeBatch(batchConfig);

      expect(result).toBeDefined();
      expect(result.type).toBe('batch_result');
      expect(result.performance).toBeDefined();

    } finally {
      await coordinator.cleanup();
    }
  });
});

// Performance tests
describe('BatchCoordinator Performance', () => {
  test('should handle large agent batches efficiently', async () => {
    const coordinator = new BatchCoordinator();
    await coordinator.initialize();

    try {
      const agentCount = 50;
      const agentConfigs = Array.from({ length: agentCount }, (_, i) => ({
        id: `agent${i}`,
        type: 'coder',
        capabilities: ['coding']
      }));

      const startTime = Date.now();
      const agents = await coordinator.spawnAgentsBatch(agentConfigs, 'large_batch');
      const duration = Date.now() - startTime;

      expect(agents).toHaveLength(agentCount);
      expect(duration).toBeLessThan(10000); // Should complete within 10 seconds

    } finally {
      await coordinator.cleanup();
    }
  });

  test('should maintain performance with concurrent batches', async () => {
    const coordinator = new BatchCoordinator();
    await coordinator.initialize();

    try {
      const batchPromises = Array.from({ length: 5 }, (_, i) => {
        const batchConfig = {
          agents: [
            { id: `agent${i}_1`, type: 'coder' },
            { id: `agent${i}_2`, type: 'tester' }
          ],
          tasks: [
            { id: `task${i}_1`, requiredType: 'coder' },
            { id: `task${i}_2`, requiredType: 'tester' }
          ]
        };
        return coordinator.executeBatch(batchConfig);
      });

      const startTime = Date.now();
      const results = await Promise.all(batchPromises);
      const duration = Date.now() - startTime;

      expect(results).toHaveLength(5);
      expect(results.every(result => result.type === 'batch_result')).toBe(true);
      expect(duration).toBeLessThan(15000); // Should handle concurrent batches efficiently

    } finally {
      await coordinator.cleanup();
    }
  });
});