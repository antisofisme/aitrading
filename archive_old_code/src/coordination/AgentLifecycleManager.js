/**
 * AgentLifecycleManager - Manages the complete lifecycle of agents in coordination
 * Handles spawning, monitoring, scaling, and cleanup following CLAUDE.md protocols
 */

class AgentLifecycleManager {
  constructor(memoryCoordination, communicationSystem) {
    this.memoryCoordination = memoryCoordination;
    this.communicationSystem = communicationSystem;
    this.activeAgents = new Map();
    this.agentPools = new Map();
    this.lifecycleHistory = [];
    this.monitoringIntervals = new Map();
    this.healthChecks = new Map();
    this.scalingPolicies = new Map();
  }

  /**
   * Initialize agent lifecycle management
   */
  async initialize() {
    // Setup default scaling policies
    this.setupDefaultScalingPolicies();

    // Initialize agent pools
    await this.initializeAgentPools();

    // Start health monitoring
    this.startHealthMonitoring();

    // Store initialization in memory
    await this.memoryCoordination.store(
      'coord/lifecycle',
      'initialization',
      {
        initialized: Date.now(),
        defaultPolicies: Array.from(this.scalingPolicies.keys()),
        pools: Array.from(this.agentPools.keys())
      },
      'system'
    );
  }

  /**
   * Spawn agent with complete lifecycle management
   */
  async spawnAgent(config) {
    const agentId = config.id || `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const agent = {
      id: agentId,
      type: config.type,
      capabilities: config.capabilities || [],
      status: 'spawning',
      health: 'unknown',
      lifecycle: {
        spawned: Date.now(),
        lastHealthCheck: null,
        heartbeat: Date.now(),
        restarts: 0,
        totalUptime: 0
      },
      resources: {
        cpu: config.resources?.cpu || 1,
        memory: config.resources?.memory || '512MB',
        storage: config.resources?.storage || '1GB'
      },
      coordination: {
        batchId: config.batchId || null,
        parentPool: config.pool || 'default',
        dependencies: config.dependencies || [],
        subscribers: new Set()
      },
      monitoring: {
        metricsCollectionEnabled: true,
        alertsEnabled: true,
        healthCheckInterval: config.healthCheckInterval || 30000
      }
    };

    try {
      // Register agent in active agents
      this.activeAgents.set(agentId, agent);

      // Add to appropriate pool
      this.addAgentToPool(agent);

      // Start agent-specific monitoring
      await this.startAgentMonitoring(agent);

      // Execute lifecycle hooks
      await this.executeLifecycleHook('post-spawn', agent);

      // Update status
      agent.status = 'active';
      agent.lifecycle.spawned = Date.now();

      // Store in memory
      await this.memoryCoordination.store(
        'coord/agents',
        agentId,
        agent,
        'system'
      );

      // Record lifecycle event
      this.recordLifecycleEvent('spawn', agentId, {
        type: agent.type,
        pool: agent.coordination.parentPool,
        resources: agent.resources
      });

      return agent;

    } catch (error) {
      agent.status = 'failed';
      agent.error = error.message;
      throw new Error(`Failed to spawn agent ${agentId}: ${error.message}`);
    }
  }

  /**
   * Spawn multiple agents in batch following single-message principle
   */
  async spawnAgentsBatch(configs) {
    const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Prepare all configurations for parallel spawning
    const enhancedConfigs = configs.map(config => ({
      ...config,
      batchId,
      spawnTime: Date.now()
    }));

    try {
      // Spawn all agents in parallel
      const spawnPromises = enhancedConfigs.map(config => this.spawnAgent(config));
      const agents = await Promise.all(spawnPromises);

      // Setup batch coordination
      await this.setupBatchCoordination(agents, batchId);

      // Record batch spawn
      this.recordLifecycleEvent('batch_spawn', batchId, {
        agentCount: agents.length,
        types: [...new Set(agents.map(a => a.type))],
        pools: [...new Set(agents.map(a => a.coordination.parentPool))]
      });

      return agents;

    } catch (error) {
      // Handle batch spawn failure
      await this.handleBatchSpawnFailure(enhancedConfigs, error);
      throw error;
    }
  }

  /**
   * Monitor agent health and performance
   */
  async monitorAgent(agentId) {
    const agent = this.activeAgents.get(agentId);
    if (!agent) return null;

    const healthCheck = {
      agentId,
      timestamp: Date.now(),
      status: 'checking',
      metrics: {},
      issues: []
    };

    try {
      // Check agent responsiveness
      const responsiveness = await this.checkAgentResponsiveness(agent);
      healthCheck.metrics.responsiveness = responsiveness;

      // Check resource usage
      const resourceUsage = await this.checkResourceUsage(agent);
      healthCheck.metrics.resources = resourceUsage;

      // Check coordination health
      const coordinationHealth = await this.checkCoordinationHealth(agent);
      healthCheck.metrics.coordination = coordinationHealth;

      // Determine overall health
      const overallHealth = this.calculateOverallHealth(healthCheck.metrics);
      healthCheck.health = overallHealth.status;
      healthCheck.score = overallHealth.score;

      // Update agent health
      agent.health = overallHealth.status;
      agent.lifecycle.lastHealthCheck = Date.now();
      agent.lifecycle.heartbeat = Date.now();

      // Store health check result
      await this.memoryCoordination.store(
        'coord/health_checks',
        `${agentId}_${Date.now()}`,
        healthCheck,
        'system'
      );

      // Handle health issues if detected
      if (overallHealth.status !== 'healthy') {
        await this.handleHealthIssues(agent, healthCheck);
      }

      return healthCheck;

    } catch (error) {
      healthCheck.status = 'failed';
      healthCheck.error = error.message;
      agent.health = 'unhealthy';

      console.error(`Health check failed for agent ${agentId}:`, error);
      return healthCheck;
    }
  }

  /**
   * Scale agent pool based on policies and demand
   */
  async scaleAgentPool(poolName, targetSize, reason = 'manual') {
    const pool = this.agentPools.get(poolName);
    if (!pool) {
      throw new Error(`Agent pool ${poolName} not found`);
    }

    const currentSize = pool.agents.size;
    const scalingAction = {
      pool: poolName,
      currentSize,
      targetSize,
      reason,
      timestamp: Date.now(),
      status: 'in_progress'
    };

    try {
      if (targetSize > currentSize) {
        // Scale up
        const agentsToAdd = targetSize - currentSize;
        await this.scaleUp(pool, agentsToAdd);
        scalingAction.action = 'scale_up';
        scalingAction.agentsAdded = agentsToAdd;

      } else if (targetSize < currentSize) {
        // Scale down
        const agentsToRemove = currentSize - targetSize;
        await this.scaleDown(pool, agentsToRemove);
        scalingAction.action = 'scale_down';
        scalingAction.agentsRemoved = agentsToRemove;

      } else {
        scalingAction.action = 'no_change';
      }

      scalingAction.status = 'completed';
      scalingAction.completedAt = Date.now();

      // Record scaling action
      this.recordLifecycleEvent('scaling', poolName, scalingAction);

      return scalingAction;

    } catch (error) {
      scalingAction.status = 'failed';
      scalingAction.error = error.message;
      throw error;
    }
  }

  /**
   * Terminate agent with cleanup
   */
  async terminateAgent(agentId, reason = 'manual') {
    const agent = this.activeAgents.get(agentId);
    if (!agent) {
      throw new Error(`Agent ${agentId} not found`);
    }

    const termination = {
      agentId,
      reason,
      timestamp: Date.now(),
      status: 'terminating'
    };

    try {
      // Update agent status
      agent.status = 'terminating';

      // Execute pre-termination hooks
      await this.executeLifecycleHook('pre-terminate', agent);

      // Stop monitoring
      this.stopAgentMonitoring(agentId);

      // Clean up resources
      await this.cleanupAgentResources(agent);

      // Remove from coordination
      await this.removeFromCoordination(agent);

      // Remove from pool
      this.removeAgentFromPool(agent);

      // Remove from active agents
      this.activeAgents.delete(agentId);

      // Update termination record
      termination.status = 'terminated';
      termination.terminatedAt = Date.now();

      // Calculate final uptime
      const uptime = Date.now() - agent.lifecycle.spawned;
      agent.lifecycle.totalUptime = uptime;

      // Execute post-termination hooks
      await this.executeLifecycleHook('post-terminate', agent);

      // Record lifecycle event
      this.recordLifecycleEvent('terminate', agentId, {
        reason,
        uptime,
        restarts: agent.lifecycle.restarts
      });

      return termination;

    } catch (error) {
      termination.status = 'failed';
      termination.error = error.message;
      agent.status = 'termination_failed';
      throw error;
    }
  }

  /**
   * Restart agent with state preservation
   */
  async restartAgent(agentId, preserveState = true) {
    const agent = this.activeAgents.get(agentId);
    if (!agent) {
      throw new Error(`Agent ${agentId} not found`);
    }

    const restart = {
      agentId,
      preserveState,
      timestamp: Date.now(),
      status: 'restarting'
    };

    try {
      // Save current state if requested
      let savedState = null;
      if (preserveState) {
        savedState = await this.saveAgentState(agent);
      }

      // Stop current instance
      await this.stopAgentInstance(agent);

      // Start new instance
      const newAgent = await this.startAgentInstance(agent.type, {
        ...agent,
        id: agentId, // Keep same ID
        savedState,
        isRestart: true
      });

      // Update restart count
      newAgent.lifecycle.restarts = (agent.lifecycle.restarts || 0) + 1;

      // Restore state if preserved
      if (savedState) {
        await this.restoreAgentState(newAgent, savedState);
      }

      restart.status = 'completed';
      restart.completedAt = Date.now();

      // Record restart
      this.recordLifecycleEvent('restart', agentId, restart);

      return newAgent;

    } catch (error) {
      restart.status = 'failed';
      restart.error = error.message;
      throw error;
    }
  }

  /**
   * Setup default scaling policies
   */
  setupDefaultScalingPolicies() {
    // CPU-based scaling
    this.scalingPolicies.set('cpu_based', {
      type: 'cpu_based',
      scaleUpThreshold: 80,
      scaleDownThreshold: 20,
      minAgents: 1,
      maxAgents: 10,
      cooldown: 300000 // 5 minutes
    });

    // Task queue-based scaling
    this.scalingPolicies.set('queue_based', {
      type: 'queue_based',
      scaleUpThreshold: 10, // tasks per agent
      scaleDownThreshold: 2,
      minAgents: 1,
      maxAgents: 20,
      cooldown: 180000 // 3 minutes
    });

    // Response time-based scaling
    this.scalingPolicies.set('response_time', {
      type: 'response_time',
      scaleUpThreshold: 2000, // ms
      scaleDownThreshold: 500,
      minAgents: 1,
      maxAgents: 15,
      cooldown: 240000 // 4 minutes
    });
  }

  /**
   * Initialize agent pools
   */
  async initializeAgentPools() {
    const defaultPools = [
      { name: 'default', type: 'general', minSize: 1, maxSize: 10 },
      { name: 'coder', type: 'coder', minSize: 2, maxSize: 8 },
      { name: 'researcher', type: 'researcher', minSize: 1, maxSize: 5 },
      { name: 'tester', type: 'tester', minSize: 1, maxSize: 6 },
      { name: 'reviewer', type: 'reviewer', minSize: 1, maxSize: 4 }
    ];

    for (const poolConfig of defaultPools) {
      const pool = {
        name: poolConfig.name,
        type: poolConfig.type,
        agents: new Set(),
        minSize: poolConfig.minSize,
        maxSize: poolConfig.maxSize,
        scaling: {
          policy: 'cpu_based',
          lastScale: Date.now(),
          cooldown: 300000
        },
        metrics: {
          totalSpawned: 0,
          totalTerminated: 0,
          averageUptime: 0,
          healthScore: 100
        }
      };

      this.agentPools.set(poolConfig.name, pool);
    }
  }

  /**
   * Start health monitoring for all agents
   */
  startHealthMonitoring() {
    // Global health monitoring interval
    const globalInterval = setInterval(async () => {
      const monitoringPromises = Array.from(this.activeAgents.keys()).map(
        agentId => this.monitorAgent(agentId)
      );

      try {
        await Promise.all(monitoringPromises);
      } catch (error) {
        console.error('Health monitoring batch failed:', error);
      }
    }, 30000); // Every 30 seconds

    this.monitoringIntervals.set('global', globalInterval);
  }

  /**
   * Start monitoring for specific agent
   */
  async startAgentMonitoring(agent) {
    const interval = setInterval(async () => {
      try {
        await this.monitorAgent(agent.id);
      } catch (error) {
        console.error(`Monitoring failed for agent ${agent.id}:`, error);
      }
    }, agent.monitoring.healthCheckInterval);

    this.monitoringIntervals.set(agent.id, interval);
  }

  /**
   * Stop monitoring for specific agent
   */
  stopAgentMonitoring(agentId) {
    const interval = this.monitoringIntervals.get(agentId);
    if (interval) {
      clearInterval(interval);
      this.monitoringIntervals.delete(agentId);
    }
  }

  /**
   * Add agent to pool
   */
  addAgentToPool(agent) {
    const poolName = agent.coordination.parentPool;
    const pool = this.agentPools.get(poolName);
    if (pool) {
      pool.agents.add(agent.id);
      pool.metrics.totalSpawned++;
      agent.coordination.parentPool = poolName;
    }
  }

  /**
   * Remove agent from pool
   */
  removeAgentFromPool(agent) {
    const poolName = agent.coordination.parentPool;
    const pool = this.agentPools.get(poolName);
    if (pool) {
      pool.agents.delete(agent.id);
      pool.metrics.totalTerminated++;
    }
  }

  /**
   * Setup batch coordination for agents
   */
  async setupBatchCoordination(agents, batchId) {
    const coordination = {
      batchId,
      agents: agents.map(a => a.id),
      coordinator: 'system',
      started: Date.now(),
      communication: {
        channels: [],
        messageRoutes: new Map()
      }
    };

    // Setup inter-batch communication
    for (const agent of agents) {
      agent.coordination.batchId = batchId;

      // Subscribe to batch coordination messages
      await this.communicationSystem.subscribe(
        agent.id,
        'batch_coordination',
        this.createBatchCoordinationHandler(agent)
      );
    }

    // Store batch coordination
    await this.memoryCoordination.store(
      'coord/batches',
      batchId,
      coordination,
      'system'
    );
  }

  /**
   * Create batch coordination message handler
   */
  createBatchCoordinationHandler(agent) {
    return async (message) => {
      switch (message.content.type) {
        case 'batch_status_request':
          await this.handleBatchStatusRequest(agent, message);
          break;

        case 'batch_termination':
          await this.handleBatchTermination(agent, message);
          break;

        case 'batch_scaling':
          await this.handleBatchScaling(agent, message);
          break;

        default:
          console.warn(`Unknown batch coordination message type: ${message.content.type}`);
      }
    };
  }

  /**
   * Check agent responsiveness
   */
  async checkAgentResponsiveness(agent) {
    const start = Date.now();

    try {
      // Send ping message
      const messageId = await this.communicationSystem.sendMessage(
        'system',
        agent.id,
        { type: 'ping', timestamp: start },
        { type: 'health_check', priority: 'high' }
      );

      // Wait for pong (simplified - in real implementation, use proper async handling)
      const latency = Date.now() - start;

      return {
        responsive: latency < 5000, // 5 second timeout
        latency,
        lastResponse: Date.now()
      };

    } catch (error) {
      return {
        responsive: false,
        error: error.message,
        lastResponse: null
      };
    }
  }

  /**
   * Check resource usage
   */
  async checkResourceUsage(agent) {
    // Simplified resource check - in real implementation, use actual metrics
    return {
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      storage: Math.random() * 100,
      limits: {
        cpu: 80,
        memory: 85,
        storage: 90
      }
    };
  }

  /**
   * Check coordination health
   */
  async checkCoordinationHealth(agent) {
    const batchId = agent.coordination.batchId;
    if (!batchId) return { healthy: true, issues: [] };

    // Check communication with other agents
    const issues = [];
    const communicationStats = this.communicationSystem.getCommunicationStats();

    // Check message delivery rates
    const agentStats = communicationStats.messagesByAgent[agent.id] || 0;
    if (agentStats === 0) {
      issues.push('No message activity detected');
    }

    return {
      healthy: issues.length === 0,
      issues,
      messageCount: agentStats,
      lastActivity: Date.now() // Simplified
    };
  }

  /**
   * Calculate overall health score
   */
  calculateOverallHealth(metrics) {
    let score = 100;
    let status = 'healthy';

    // Factor in responsiveness
    if (!metrics.responsiveness?.responsive) {
      score -= 40;
      status = 'unhealthy';
    } else if (metrics.responsiveness.latency > 2000) {
      score -= 20;
      status = 'degraded';
    }

    // Factor in resource usage
    const resources = metrics.resources;
    if (resources.cpu > resources.limits.cpu) {
      score -= 20;
      status = 'degraded';
    }
    if (resources.memory > resources.limits.memory) {
      score -= 20;
      status = 'degraded';
    }

    // Factor in coordination health
    if (!metrics.coordination?.healthy) {
      score -= 30;
      status = 'unhealthy';
    }

    return { score: Math.max(0, score), status };
  }

  /**
   * Handle health issues
   */
  async handleHealthIssues(agent, healthCheck) {
    const issues = healthCheck.issues || [];

    // Determine severity
    const severity = healthCheck.health === 'unhealthy' ? 'high' : 'medium';

    // Take appropriate action based on severity
    if (severity === 'high') {
      // Consider restart or termination
      if (agent.lifecycle.restarts < 3) {
        console.warn(`Restarting unhealthy agent ${agent.id}`);
        await this.restartAgent(agent.id, true);
      } else {
        console.error(`Terminating repeatedly unhealthy agent ${agent.id}`);
        await this.terminateAgent(agent.id, 'health_issues');
      }
    }

    // Store health issue record
    await this.memoryCoordination.store(
      'coord/health_issues',
      `${agent.id}_${Date.now()}`,
      {
        agentId: agent.id,
        severity,
        issues,
        healthCheck,
        action: severity === 'high' ? 'restart_or_terminate' : 'monitor',
        timestamp: Date.now()
      },
      'system'
    );
  }

  /**
   * Execute lifecycle hooks
   */
  async executeLifecycleHook(hookType, agent, data = {}) {
    try {
      const hookData = {
        hookType,
        agentId: agent.id,
        agentType: agent.type,
        timestamp: Date.now(),
        ...data
      };

      // Store hook execution
      await this.memoryCoordination.store(
        'coord/lifecycle_hooks',
        `${hookType}_${agent.id}_${Date.now()}`,
        hookData,
        'system'
      );

      // Notify subscribers
      if (agent.coordination.subscribers.size > 0) {
        const notification = {
          type: 'lifecycle_event',
          event: hookType,
          agentId: agent.id,
          data: hookData
        };

        const notificationPromises = Array.from(agent.coordination.subscribers).map(
          subscriberId => this.communicationSystem.sendMessage(
            'system',
            subscriberId,
            notification,
            { type: 'lifecycle', priority: 'medium' }
          )
        );

        await Promise.all(notificationPromises);
      }

    } catch (error) {
      console.error(`Failed to execute lifecycle hook ${hookType} for agent ${agent.id}:`, error);
    }
  }

  /**
   * Record lifecycle event
   */
  recordLifecycleEvent(eventType, entityId, data) {
    const event = {
      type: eventType,
      entityId,
      timestamp: Date.now(),
      data: { ...data }
    };

    this.lifecycleHistory.push(event);

    // Limit history size
    if (this.lifecycleHistory.length > 10000) {
      this.lifecycleHistory = this.lifecycleHistory.slice(-5000);
    }
  }

  /**
   * Get lifecycle statistics
   */
  getLifecycleStatistics() {
    const stats = {
      activeAgents: this.activeAgents.size,
      totalAgentPools: this.agentPools.size,
      totalEvents: this.lifecycleHistory.length,
      monitoringIntervals: this.monitoringIntervals.size,
      poolStats: {},
      eventStats: {},
      healthStats: this.getHealthStatistics()
    };

    // Collect pool statistics
    this.agentPools.forEach((pool, name) => {
      stats.poolStats[name] = {
        currentSize: pool.agents.size,
        minSize: pool.minSize,
        maxSize: pool.maxSize,
        totalSpawned: pool.metrics.totalSpawned,
        totalTerminated: pool.metrics.totalTerminated,
        healthScore: pool.metrics.healthScore
      };
    });

    // Collect event statistics
    this.lifecycleHistory.forEach(event => {
      stats.eventStats[event.type] = (stats.eventStats[event.type] || 0) + 1;
    });

    return stats;
  }

  /**
   * Get health statistics
   */
  getHealthStatistics() {
    const healthCounts = { healthy: 0, degraded: 0, unhealthy: 0, unknown: 0 };

    this.activeAgents.forEach(agent => {
      healthCounts[agent.health] = (healthCounts[agent.health] || 0) + 1;
    });

    return {
      counts: healthCounts,
      totalAgents: this.activeAgents.size,
      healthyPercentage: this.activeAgents.size > 0 ?
        (healthCounts.healthy / this.activeAgents.size) * 100 : 0
    };
  }

  /**
   * Helper methods for lifecycle operations
   */

  async handleBatchSpawnFailure(configs, error) {
    console.error('Batch spawn failed:', error);
    // Cleanup any partially spawned agents
  }

  async scaleUp(pool, count) {
    const spawnPromises = [];
    for (let i = 0; i < count; i++) {
      spawnPromises.push(this.spawnAgent({
        type: pool.type,
        pool: pool.name
      }));
    }
    return await Promise.all(spawnPromises);
  }

  async scaleDown(pool, count) {
    const agentsToRemove = Array.from(pool.agents).slice(0, count);
    const terminationPromises = agentsToRemove.map(agentId =>
      this.terminateAgent(agentId, 'scaling_down')
    );
    return await Promise.all(terminationPromises);
  }

  async saveAgentState(agent) {
    return {
      agentId: agent.id,
      memory: await this.memoryCoordination.retrieve(`coord/agents/${agent.id}`, 'state', 'system'),
      configuration: agent,
      timestamp: Date.now()
    };
  }

  async restoreAgentState(agent, savedState) {
    if (savedState.memory) {
      await this.memoryCoordination.store(
        `coord/agents/${agent.id}`,
        'state',
        savedState.memory,
        'system'
      );
    }
  }

  async stopAgentInstance(agent) {
    agent.status = 'stopping';
    this.stopAgentMonitoring(agent.id);
  }

  async startAgentInstance(type, config) {
    return await this.spawnAgent({ ...config, type });
  }

  async cleanupAgentResources(agent) {
    // Cleanup memory allocations
    const agentKeys = [`coord/agents/${agent.id}`, `coord/health_checks/${agent.id}`];
    // Implementation would clean up these keys
  }

  async removeFromCoordination(agent) {
    if (agent.coordination.batchId) {
      await this.communicationSystem.unsubscribe(agent.id, 'batch_coordination');
    }
  }

  async handleBatchStatusRequest(agent, message) {
    // Handle batch status requests
  }

  async handleBatchTermination(agent, message) {
    // Handle batch termination messages
  }

  async handleBatchScaling(agent, message) {
    // Handle batch scaling messages
  }

  /**
   * Cleanup lifecycle manager
   */
  cleanup() {
    // Stop all monitoring intervals
    this.monitoringIntervals.forEach(interval => clearInterval(interval));
    this.monitoringIntervals.clear();

    // Clear data structures
    this.activeAgents.clear();
    this.agentPools.clear();
    this.lifecycleHistory = [];
    this.healthChecks.clear();
    this.scalingPolicies.clear();
  }
}

module.exports = AgentLifecycleManager;