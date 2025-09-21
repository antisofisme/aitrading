/**
 * AgentOrchestrator - Parallel coordination system for spawning multiple agents
 * Follows CLAUDE.md protocols for single-message batch operations
 */

class AgentOrchestrator {
  constructor() {
    this.activeAgents = new Map();
    this.communicationChannels = new Map();
    this.memoryStore = new Map();
    this.taskQueue = [];
    this.conflictResolver = null;
    this.resultAggregator = null;
  }

  /**
   * Spawn multiple agents in parallel following "1 MESSAGE = ALL RELATED OPERATIONS" principle
   */
  async spawnAgentsBatch(agentConfigs) {
    const spawnPromises = agentConfigs.map(config => this.createAgent(config));
    const agents = await Promise.all(spawnPromises);

    // Setup inter-agent communication channels
    this.setupCommunicationMatrix(agents);

    // Initialize shared memory coordination
    await this.initializeSharedMemory(agents);

    return agents;
  }

  /**
   * Create individual agent with coordination capabilities
   */
  async createAgent(config) {
    const agent = {
      id: config.id,
      type: config.type,
      capabilities: config.capabilities || [],
      status: 'initializing',
      memory: new Map(),
      communicationChannel: null,
      hooks: {
        preTask: config.preTask || null,
        postEdit: config.postEdit || null,
        postTask: config.postTask || null
      },
      tasks: [],
      results: []
    };

    // Setup agent-specific memory namespace
    const memoryKey = `coord/agents/${agent.id}`;
    this.memoryStore.set(memoryKey, agent.memory);

    // Create communication channel
    agent.communicationChannel = this.createCommunicationChannel(agent.id);

    this.activeAgents.set(agent.id, agent);
    return agent;
  }

  /**
   * Setup communication matrix for cross-agent coordination
   */
  setupCommunicationMatrix(agents) {
    agents.forEach(agent => {
      const channel = {
        send: (targetId, message) => this.sendMessage(agent.id, targetId, message),
        broadcast: (message) => this.broadcastMessage(agent.id, message),
        receive: (callback) => this.subscribeToMessages(agent.id, callback)
      };

      this.communicationChannels.set(agent.id, channel);
      agent.communicationChannel = channel;
    });
  }

  /**
   * Initialize shared memory coordination
   */
  async initializeSharedMemory(agents) {
    const sharedMemoryKey = 'coord/shared';
    const sharedMemory = {
      globalState: {},
      taskResults: new Map(),
      agentStatuses: new Map(),
      dependencies: new Map(),
      conflicts: []
    };

    this.memoryStore.set(sharedMemoryKey, sharedMemory);

    // Register each agent in shared memory
    agents.forEach(agent => {
      sharedMemory.agentStatuses.set(agent.id, {
        status: agent.status,
        lastUpdate: Date.now(),
        currentTask: null
      });
    });
  }

  /**
   * Execute parallel coordination with batch operations
   */
  async executeParallelCoordination(tasks) {
    // Batch all pre-task hooks
    const preTaskPromises = tasks.map(task => this.executePreTaskHooks(task));
    await Promise.all(preTaskPromises);

    // Execute tasks in parallel
    const taskPromises = tasks.map(task => this.executeTask(task));
    const results = await Promise.all(taskPromises);

    // Batch all post-task hooks
    const postTaskPromises = tasks.map((task, index) =>
      this.executePostTaskHooks(task, results[index])
    );
    await Promise.all(postTaskPromises);

    // Aggregate and resolve conflicts
    return this.aggregateResults(results);
  }

  /**
   * Execute pre-task hooks for coordination
   */
  async executePreTaskHooks(task) {
    const agent = this.activeAgents.get(task.agentId);
    if (!agent || !agent.hooks.preTask) return;

    try {
      await agent.hooks.preTask(task);
      this.updateAgentStatus(task.agentId, 'executing', task);
    } catch (error) {
      console.error(`Pre-task hook failed for agent ${task.agentId}:`, error);
    }
  }

  /**
   * Execute post-task hooks with memory coordination
   */
  async executePostTaskHooks(task, result) {
    const agent = this.activeAgents.get(task.agentId);
    if (!agent || !agent.hooks.postTask) return;

    try {
      // Store result in agent memory
      const memoryKey = `coord/agents/${task.agentId}/results/${task.id}`;
      this.memoryStore.set(memoryKey, result);

      // Update shared memory
      const sharedMemory = this.memoryStore.get('coord/shared');
      sharedMemory.taskResults.set(task.id, {
        agentId: task.agentId,
        result,
        timestamp: Date.now()
      });

      await agent.hooks.postTask(task, result);
      this.updateAgentStatus(task.agentId, 'completed', null);
    } catch (error) {
      console.error(`Post-task hook failed for agent ${task.agentId}:`, error);
    }
  }

  /**
   * Send message between agents
   */
  sendMessage(fromId, toId, message) {
    const messageObj = {
      from: fromId,
      to: toId,
      message,
      timestamp: Date.now(),
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    };

    // Store in memory for persistence
    const messagesKey = `coord/messages/${toId}`;
    const messages = this.memoryStore.get(messagesKey) || [];
    messages.push(messageObj);
    this.memoryStore.set(messagesKey, messages);

    return messageObj.id;
  }

  /**
   * Broadcast message to all agents
   */
  broadcastMessage(fromId, message) {
    const messageIds = [];
    this.activeAgents.forEach((agent, agentId) => {
      if (agentId !== fromId) {
        const messageId = this.sendMessage(fromId, agentId, message);
        messageIds.push(messageId);
      }
    });
    return messageIds;
  }

  /**
   * Subscribe to messages for an agent
   */
  subscribeToMessages(agentId, callback) {
    const messagesKey = `coord/messages/${agentId}`;
    const messages = this.memoryStore.get(messagesKey) || [];

    // Return unread messages
    const unreadMessages = messages.filter(msg => !msg.read);
    unreadMessages.forEach(msg => {
      msg.read = true;
      callback(msg);
    });

    // Update memory with read status
    this.memoryStore.set(messagesKey, messages);
  }

  /**
   * Update agent status in shared memory
   */
  updateAgentStatus(agentId, status, currentTask = null) {
    const sharedMemory = this.memoryStore.get('coord/shared');
    const agentStatus = sharedMemory.agentStatuses.get(agentId);

    if (agentStatus) {
      agentStatus.status = status;
      agentStatus.lastUpdate = Date.now();
      agentStatus.currentTask = currentTask;

      sharedMemory.agentStatuses.set(agentId, agentStatus);
    }
  }

  /**
   * Get coordination status for all agents
   */
  getCoordinationStatus() {
    const sharedMemory = this.memoryStore.get('coord/shared');
    const status = {
      totalAgents: this.activeAgents.size,
      agentStatuses: Object.fromEntries(sharedMemory.agentStatuses),
      taskResults: Object.fromEntries(sharedMemory.taskResults),
      conflicts: sharedMemory.conflicts,
      memoryUsage: this.getMemoryUsage()
    };

    return status;
  }

  /**
   * Get memory usage statistics
   */
  getMemoryUsage() {
    return {
      totalKeys: this.memoryStore.size,
      agentMemories: Array.from(this.activeAgents.keys()).length,
      sharedMemorySize: JSON.stringify(this.memoryStore.get('coord/shared') || {}).length
    };
  }

  /**
   * Execute a single task with coordination
   */
  async executeTask(task) {
    const agent = this.activeAgents.get(task.agentId);
    if (!agent) {
      throw new Error(`Agent ${task.agentId} not found`);
    }

    try {
      // Execute the task based on agent type
      const result = await this.delegateTask(agent, task);

      // Store result in agent's memory
      agent.results.push({
        taskId: task.id,
        result,
        timestamp: Date.now()
      });

      return result;
    } catch (error) {
      console.error(`Task execution failed for agent ${task.agentId}:`, error);
      throw error;
    }
  }

  /**
   * Delegate task to appropriate agent handler
   */
  async delegateTask(agent, task) {
    // This would be implemented based on agent type and capabilities
    // For now, return a mock result
    return {
      agentId: agent.id,
      taskId: task.id,
      status: 'completed',
      output: `Task ${task.id} completed by ${agent.type} agent`,
      timestamp: Date.now()
    };
  }

  /**
   * Aggregate results from multiple agents
   */
  aggregateResults(results) {
    const aggregated = {
      totalTasks: results.length,
      successfulTasks: results.filter(r => r.status === 'completed').length,
      failedTasks: results.filter(r => r.status === 'failed').length,
      results: results,
      summary: this.generateSummary(results)
    };

    return aggregated;
  }

  /**
   * Generate summary of coordination results
   */
  generateSummary(results) {
    const agentTypes = [...new Set(results.map(r => r.agentId))];
    const completionRate = (results.filter(r => r.status === 'completed').length / results.length) * 100;

    return {
      agentTypes,
      completionRate: Math.round(completionRate * 100) / 100,
      totalExecutionTime: Math.max(...results.map(r => r.timestamp)) - Math.min(...results.map(r => r.timestamp)),
      averageTaskTime: results.reduce((sum, r) => sum + (r.executionTime || 0), 0) / results.length
    };
  }

  /**
   * Create communication channel for agent
   */
  createCommunicationChannel(agentId) {
    return {
      id: agentId,
      inbox: [],
      outbox: [],
      subscribers: new Set()
    };
  }

  /**
   * Cleanup and shutdown coordination system
   */
  async shutdown() {
    // Execute cleanup hooks for all agents
    const cleanupPromises = Array.from(this.activeAgents.values()).map(agent =>
      this.cleanupAgent(agent)
    );

    await Promise.all(cleanupPromises);

    // Clear all data structures
    this.activeAgents.clear();
    this.communicationChannels.clear();
    this.memoryStore.clear();
    this.taskQueue = [];
  }

  /**
   * Cleanup individual agent
   */
  async cleanupAgent(agent) {
    try {
      if (agent.hooks.postTask) {
        await agent.hooks.postTask(null, { status: 'shutdown' });
      }
      agent.status = 'shutdown';
    } catch (error) {
      console.error(`Cleanup failed for agent ${agent.id}:`, error);
    }
  }
}

module.exports = AgentOrchestrator;