/**
 * Coordination System Index - Main entry point for parallel agent coordination
 * Exports all coordination components following CLAUDE.md protocols
 */

const BatchCoordinator = require('./BatchCoordinator');
const AgentOrchestrator = require('./AgentOrchestrator');
const CrossAgentCommunication = require('./CrossAgentCommunication');
const MemoryCoordination = require('./MemoryCoordination');
const ResultAggregation = require('./ResultAggregation');
const ConflictResolution = require('./ConflictResolution');
const AgentLifecycleManager = require('./AgentLifecycleManager');
const MemoryPersistence = require('./MemoryPersistence');
const StatusMonitoring = require('./StatusMonitoring');
const ProtocolHandlers = require('./ProtocolHandlers');

/**
 * Complete coordination system factory
 * Creates and initializes all coordination components
 */
class CoordinationSystem {
  constructor(config = {}) {
    this.config = {
      enablePersistence: config.enablePersistence !== false,
      enableMonitoring: config.enableMonitoring !== false,
      persistencePath: config.persistencePath || './.swarm/coordination',
      monitoringInterval: config.monitoringInterval || 15000,
      autoSaveInterval: config.autoSaveInterval || 300000,
      ...config
    };

    this.components = {};
    this.isInitialized = false;
  }

  /**
   * Initialize complete coordination system
   */
  async initialize() {
    if (this.isInitialized) return this.components;

    try {
      // Initialize core components
      await this.initializeCoreComponents();

      // Initialize optional components
      await this.initializeOptionalComponents();

      // Setup inter-component connections
      await this.setupComponentConnections();

      this.isInitialized = true;

      console.log('Coordination system fully initialized');
      return this.components;

    } catch (error) {
      console.error('Failed to initialize coordination system:', error);
      throw error;
    }
  }

  /**
   * Initialize core coordination components
   */
  async initializeCoreComponents() {
    // Memory coordination (foundation)
    this.components.memoryCoordination = new MemoryCoordination();
    await this.components.memoryCoordination.initializeBatchMemory(['system']);

    // Cross-agent communication
    this.components.communication = new CrossAgentCommunication(this.components.memoryCoordination);
    await this.components.communication.initializeBatchCommunication(['system']);

    // Agent orchestrator
    this.components.orchestrator = new AgentOrchestrator();

    // Result aggregation
    this.components.resultAggregation = new ResultAggregation(this.components.memoryCoordination);

    // Conflict resolution
    this.components.conflictResolution = new ConflictResolution(
      this.components.memoryCoordination,
      this.components.communication
    );

    // Agent lifecycle manager
    this.components.lifecycleManager = new AgentLifecycleManager(
      this.components.memoryCoordination,
      this.components.communication
    );
    await this.components.lifecycleManager.initialize();

    // Protocol handlers
    this.components.protocolHandlers = new ProtocolHandlers(
      this.components.memoryCoordination,
      this.components.communication
    );
    await this.components.protocolHandlers.initialize();

    // Main batch coordinator
    this.components.batchCoordinator = new BatchCoordinator();
    await this.components.batchCoordinator.initialize();
  }

  /**
   * Initialize optional components
   */
  async initializeOptionalComponents() {
    // Memory persistence (optional)
    if (this.config.enablePersistence) {
      this.components.memoryPersistence = new MemoryPersistence(this.components.memoryCoordination);
      await this.components.memoryPersistence.initialize();
    }

    // Status monitoring (optional)
    if (this.config.enableMonitoring) {
      this.components.statusMonitoring = new StatusMonitoring(
        this.components.memoryCoordination,
        this.components.communication,
        this.components.lifecycleManager
      );
      await this.components.statusMonitoring.initialize();
    }
  }

  /**
   * Setup connections between components
   */
  async setupComponentConnections() {
    // Connect orchestrator to lifecycle manager
    this.components.orchestrator.setLifecycleManager(this.components.lifecycleManager);

    // Connect batch coordinator to all components
    this.components.batchCoordinator.memoryCoordination = this.components.memoryCoordination;
    this.components.batchCoordinator.communicationSystem = this.components.communication;
    this.components.batchCoordinator.agentOrchestrator = this.components.orchestrator;
    this.components.batchCoordinator.resultAggregation = this.components.resultAggregation;
    this.components.batchCoordinator.conflictResolution = this.components.conflictResolution;

    // Setup protocol message routing
    this.components.communication.setProtocolHandler(this.components.protocolHandlers);
  }

  /**
   * Execute parallel agent batch with full coordination
   */
  async executeBatch(batchConfig) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return await this.components.batchCoordinator.executeBatch(batchConfig);
  }

  /**
   * Get system status
   */
  getSystemStatus() {
    return {
      initialized: this.isInitialized,
      components: Object.keys(this.components),
      config: this.config,
      memory: this.components.memoryCoordination?.getMemoryStatistics(),
      communication: this.components.communication?.getCommunicationStats(),
      lifecycle: this.components.lifecycleManager?.getLifecycleStatistics(),
      monitoring: this.components.statusMonitoring?.getMonitoringStatus(),
      protocols: this.components.protocolHandlers?.getProtocolStatistics()
    };
  }

  /**
   * Cleanup coordination system
   */
  async cleanup() {
    if (!this.isInitialized) return;

    // Cleanup all components
    const cleanupPromises = Object.values(this.components).map(component => {
      if (component && typeof component.cleanup === 'function') {
        return component.cleanup();
      }
    }).filter(Boolean);

    await Promise.all(cleanupPromises);

    this.components = {};
    this.isInitialized = false;

    console.log('Coordination system cleaned up');
  }
}

/**
 * Factory function for creating coordination system
 */
function createCoordinationSystem(config = {}) {
  return new CoordinationSystem(config);
}

/**
 * Quick setup function for basic coordination
 */
async function setupBasicCoordination(agentConfigs, taskConfigs, options = {}) {
  const system = createCoordinationSystem(options);
  await system.initialize();

  const batchConfig = {
    agents: agentConfigs,
    tasks: taskConfigs,
    aggregationStrategy: options.aggregationStrategy || 'merge',
    conflictResolver: options.conflictResolver || 'merge'
  };

  return await system.executeBatch(batchConfig);
}

/**
 * Utility function to create CLAUDE.md compliant agent hooks
 */
function createClaudeFlowHooks(agentId, batchId) {
  return {
    preTask: async (task) => {
      // Execute pre-task hook as per CLAUDE.md
      console.log(`npx claude-flow@alpha hooks pre-task --description "${task.description}"`);
    },

    postEdit: async (file, memoryKey) => {
      // Execute post-edit hook with memory coordination
      console.log(`npx claude-flow@alpha hooks post-edit --file "${file}" --memory-key "${memoryKey}"`);
    },

    postTask: async (taskId) => {
      // Execute post-task hook
      console.log(`npx claude-flow@alpha hooks post-task --task-id "${taskId}"`);
    }
  };
}

/**
 * Example usage function demonstrating CLAUDE.md protocols
 */
async function demonstrateCoordination() {
  console.log('Demonstrating parallel coordination system...');

  // Create coordination system
  const system = createCoordinationSystem({
    enablePersistence: true,
    enableMonitoring: true
  });

  try {
    // Initialize system
    await system.initialize();

    // Define agent configuration following CLAUDE.md single-message principle
    const agentConfigs = [
      {
        id: 'researcher_001',
        type: 'researcher',
        capabilities: ['research', 'analysis', 'documentation'],
        pool: 'researcher'
      },
      {
        id: 'coder_001',
        type: 'coder',
        capabilities: ['coding', 'implementation', 'testing'],
        pool: 'coder'
      },
      {
        id: 'reviewer_001',
        type: 'reviewer',
        capabilities: ['review', 'quality_assurance', 'optimization'],
        pool: 'reviewer'
      }
    ];

    // Define task configuration
    const taskConfigs = [
      {
        id: 'research_task',
        description: 'Research best practices for parallel coordination',
        requiredType: 'researcher',
        priority: 'high'
      },
      {
        id: 'implementation_task',
        description: 'Implement coordination features',
        requiredType: 'coder',
        priority: 'high',
        dependencies: ['research_task']
      },
      {
        id: 'review_task',
        description: 'Review implementation quality',
        requiredType: 'reviewer',
        priority: 'medium',
        dependencies: ['implementation_task']
      }
    ];

    // Execute batch with full coordination
    const result = await system.executeBatch({
      agents: agentConfigs,
      tasks: taskConfigs,
      aggregationStrategy: 'merge',
      conflictResolver: 'negotiation'
    });

    console.log('Coordination demonstration completed:', result);

    // Get system status
    const status = system.getSystemStatus();
    console.log('System status:', status);

    return result;

  } finally {
    // Cleanup
    await system.cleanup();
  }
}

// Export all components and utilities
module.exports = {
  // Main classes
  CoordinationSystem,
  BatchCoordinator,
  AgentOrchestrator,
  CrossAgentCommunication,
  MemoryCoordination,
  ResultAggregation,
  ConflictResolution,
  AgentLifecycleManager,
  MemoryPersistence,
  StatusMonitoring,
  ProtocolHandlers,

  // Factory functions
  createCoordinationSystem,
  setupBasicCoordination,
  createClaudeFlowHooks,

  // Demonstration
  demonstrateCoordination
};