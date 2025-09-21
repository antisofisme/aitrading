/**
 * ProtocolHandlers - Handles coordination protocols and communication patterns
 * Implements standardized protocols for agent interaction and coordination
 */

class ProtocolHandlers {
  constructor(memoryCoordination, communicationSystem) {
    this.memoryCoordination = memoryCoordination;
    this.communicationSystem = communicationSystem;

    this.protocols = new Map();
    this.handlers = new Map();
    this.middlewares = new Map();
    this.protocolStats = new Map();
    this.activeProtocols = new Set();

    this.setupStandardProtocols();
  }

  /**
   * Initialize protocol handlers system
   */
  async initialize() {
    try {
      // Register standard protocol handlers
      await this.registerStandardHandlers();

      // Setup protocol middleware
      this.setupProtocolMiddleware();

      // Initialize protocol statistics
      this.initializeProtocolStats();

      // Store initialization
      await this.memoryCoordination.store(
        'coord/protocols',
        'initialization',
        {
          initialized: Date.now(),
          protocols: Array.from(this.protocols.keys()),
          handlers: Array.from(this.handlers.keys())
        },
        'system'
      );

      console.log('Protocol handlers system initialized');

    } catch (error) {
      console.error('Failed to initialize protocol handlers:', error);
      throw error;
    }
  }

  /**
   * Setup standard coordination protocols
   */
  setupStandardProtocols() {
    // Task coordination protocol
    this.protocols.set('task_coordination', {
      name: 'task_coordination',
      version: '1.0',
      description: 'Handles task assignment and execution coordination',
      messageTypes: ['task_assign', 'task_start', 'task_progress', 'task_complete', 'task_fail'],
      requiredFields: ['taskId', 'agentId', 'timestamp'],
      optional: ['priority', 'dependencies', 'deadline']
    });

    // Resource sharing protocol
    this.protocols.set('resource_sharing', {
      name: 'resource_sharing',
      version: '1.0',
      description: 'Manages resource allocation and sharing between agents',
      messageTypes: ['resource_request', 'resource_grant', 'resource_deny', 'resource_release'],
      requiredFields: ['resourceId', 'agentId', 'timestamp'],
      optional: ['duration', 'priority', 'exclusive']
    });

    // Consensus protocol
    this.protocols.set('consensus', {
      name: 'consensus',
      version: '1.0',
      description: 'Implements distributed consensus for decision making',
      messageTypes: ['consensus_propose', 'consensus_vote', 'consensus_commit', 'consensus_abort'],
      requiredFields: ['proposalId', 'agentId', 'timestamp'],
      optional: ['value', 'round', 'evidence']
    });

    // Health monitoring protocol
    this.protocols.set('health_monitoring', {
      name: 'health_monitoring',
      version: '1.0',
      description: 'Agent health checks and status reporting',
      messageTypes: ['health_ping', 'health_pong', 'health_report', 'health_alert'],
      requiredFields: ['agentId', 'timestamp'],
      optional: ['status', 'metrics', 'issues']
    });

    // Synchronization protocol
    this.protocols.set('synchronization', {
      name: 'synchronization',
      version: '1.0',
      description: 'Synchronizes agent states and operations',
      messageTypes: ['sync_request', 'sync_response', 'sync_commit', 'sync_rollback'],
      requiredFields: ['syncId', 'agentId', 'timestamp'],
      optional: ['state', 'checkpoint', 'version']
    });

    // Coordination lifecycle protocol
    this.protocols.set('lifecycle', {
      name: 'lifecycle',
      version: '1.0',
      description: 'Manages agent lifecycle events and coordination',
      messageTypes: ['lifecycle_spawn', 'lifecycle_ready', 'lifecycle_terminate', 'lifecycle_restart'],
      requiredFields: ['agentId', 'event', 'timestamp'],
      optional: ['reason', 'state', 'metadata']
    });
  }

  /**
   * Register standard protocol handlers
   */
  async registerStandardHandlers() {
    // Task coordination handlers
    this.registerHandler('task_coordination', 'task_assign', this.handleTaskAssign.bind(this));
    this.registerHandler('task_coordination', 'task_start', this.handleTaskStart.bind(this));
    this.registerHandler('task_coordination', 'task_progress', this.handleTaskProgress.bind(this));
    this.registerHandler('task_coordination', 'task_complete', this.handleTaskComplete.bind(this));
    this.registerHandler('task_coordination', 'task_fail', this.handleTaskFail.bind(this));

    // Resource sharing handlers
    this.registerHandler('resource_sharing', 'resource_request', this.handleResourceRequest.bind(this));
    this.registerHandler('resource_sharing', 'resource_grant', this.handleResourceGrant.bind(this));
    this.registerHandler('resource_sharing', 'resource_deny', this.handleResourceDeny.bind(this));
    this.registerHandler('resource_sharing', 'resource_release', this.handleResourceRelease.bind(this));

    // Consensus handlers
    this.registerHandler('consensus', 'consensus_propose', this.handleConsensusPropose.bind(this));
    this.registerHandler('consensus', 'consensus_vote', this.handleConsensusVote.bind(this));
    this.registerHandler('consensus', 'consensus_commit', this.handleConsensusCommit.bind(this));
    this.registerHandler('consensus', 'consensus_abort', this.handleConsensusAbort.bind(this));

    // Health monitoring handlers
    this.registerHandler('health_monitoring', 'health_ping', this.handleHealthPing.bind(this));
    this.registerHandler('health_monitoring', 'health_pong', this.handleHealthPong.bind(this));
    this.registerHandler('health_monitoring', 'health_report', this.handleHealthReport.bind(this));
    this.registerHandler('health_monitoring', 'health_alert', this.handleHealthAlert.bind(this));

    // Synchronization handlers
    this.registerHandler('synchronization', 'sync_request', this.handleSyncRequest.bind(this));
    this.registerHandler('synchronization', 'sync_response', this.handleSyncResponse.bind(this));
    this.registerHandler('synchronization', 'sync_commit', this.handleSyncCommit.bind(this));
    this.registerHandler('synchronization', 'sync_rollback', this.handleSyncRollback.bind(this));

    // Lifecycle handlers
    this.registerHandler('lifecycle', 'lifecycle_spawn', this.handleLifecycleSpawn.bind(this));
    this.registerHandler('lifecycle', 'lifecycle_ready', this.handleLifecycleReady.bind(this));
    this.registerHandler('lifecycle', 'lifecycle_terminate', this.handleLifecycleTerminate.bind(this));
    this.registerHandler('lifecycle', 'lifecycle_restart', this.handleLifecycleRestart.bind(this));
  }

  /**
   * Register a protocol handler
   */
  registerHandler(protocol, messageType, handler) {
    const handlerKey = `${protocol}:${messageType}`;
    this.handlers.set(handlerKey, {
      protocol,
      messageType,
      handler,
      registered: Date.now(),
      callCount: 0,
      lastCall: null
    });
  }

  /**
   * Process incoming protocol message
   */
  async processProtocolMessage(message) {
    const processingId = `proc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Validate message format
      const validation = await this.validateProtocolMessage(message);
      if (!validation.valid) {
        throw new Error(`Invalid protocol message: ${validation.error}`);
      }

      // Apply middleware (pre-processing)
      const processedMessage = await this.applyMiddleware('pre', message);

      // Find and execute handler
      const handlerKey = `${processedMessage.protocol}:${processedMessage.type}`;
      const handlerInfo = this.handlers.get(handlerKey);

      if (!handlerInfo) {
        throw new Error(`No handler found for ${handlerKey}`);
      }

      // Execute handler
      const result = await handlerInfo.handler(processedMessage);

      // Update handler statistics
      handlerInfo.callCount++;
      handlerInfo.lastCall = Date.now();

      // Apply middleware (post-processing)
      const finalResult = await this.applyMiddleware('post', result, processedMessage);

      // Record protocol usage
      await this.recordProtocolUsage(processedMessage, result);

      return {
        processingId,
        success: true,
        result: finalResult,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error(`Protocol message processing failed:`, error);

      return {
        processingId,
        success: false,
        error: error.message,
        timestamp: Date.now()
      };
    }
  }

  /**
   * Validate protocol message
   */
  async validateProtocolMessage(message) {
    if (!message.protocol) {
      return { valid: false, error: 'Missing protocol field' };
    }

    if (!message.type) {
      return { valid: false, error: 'Missing message type field' };
    }

    const protocol = this.protocols.get(message.protocol);
    if (!protocol) {
      return { valid: false, error: `Unknown protocol: ${message.protocol}` };
    }

    if (!protocol.messageTypes.includes(message.type)) {
      return { valid: false, error: `Invalid message type ${message.type} for protocol ${message.protocol}` };
    }

    // Check required fields
    for (const field of protocol.requiredFields) {
      if (!(field in message)) {
        return { valid: false, error: `Missing required field: ${field}` };
      }
    }

    return { valid: true };
  }

  /**
   * Apply middleware to message processing
   */
  async applyMiddleware(phase, data, originalMessage = null) {
    const middlewareKey = `${phase}_processing`;
    const middleware = this.middlewares.get(middlewareKey);

    if (!middleware || middleware.length === 0) {
      return data;
    }

    let processedData = data;

    for (const middlewareFunc of middleware) {
      try {
        processedData = await middlewareFunc(processedData, originalMessage);
      } catch (error) {
        console.error(`Middleware ${middlewareFunc.name} failed:`, error);
      }
    }

    return processedData;
  }

  /**
   * Task Coordination Protocol Handlers
   */

  async handleTaskAssign(message) {
    const { taskId, agentId, task } = message;

    // Store task assignment
    await this.memoryCoordination.store(
      'coord/tasks',
      taskId,
      {
        id: taskId,
        assignedTo: agentId,
        task,
        status: 'assigned',
        assigned: Date.now()
      },
      'system'
    );

    // Send acknowledgment
    await this.communicationSystem.sendMessage(
      'system',
      agentId,
      {
        protocol: 'task_coordination',
        type: 'task_assign_ack',
        taskId,
        status: 'acknowledged'
      },
      { type: 'protocol', priority: 'high' }
    );

    return { taskId, status: 'assigned', agentId };
  }

  async handleTaskStart(message) {
    const { taskId, agentId } = message;

    // Update task status
    const task = await this.memoryCoordination.retrieve('coord/tasks', taskId, 'system');
    if (task) {
      task.status = 'started';
      task.started = Date.now();

      await this.memoryCoordination.store('coord/tasks', taskId, task, 'system');
    }

    return { taskId, status: 'started', timestamp: Date.now() };
  }

  async handleTaskProgress(message) {
    const { taskId, agentId, progress } = message;

    // Update task progress
    await this.memoryCoordination.store(
      'coord/task_progress',
      `${taskId}_${Date.now()}`,
      {
        taskId,
        agentId,
        progress,
        timestamp: Date.now()
      },
      agentId
    );

    return { taskId, progressRecorded: true };
  }

  async handleTaskComplete(message) {
    const { taskId, agentId, result } = message;

    // Update task status
    const task = await this.memoryCoordination.retrieve('coord/tasks', taskId, 'system');
    if (task) {
      task.status = 'completed';
      task.completed = Date.now();
      task.result = result;

      await this.memoryCoordination.store('coord/tasks', taskId, task, 'system');
    }

    // Notify completion to interested parties
    await this.communicationSystem.broadcastMessage(
      agentId,
      {
        protocol: 'task_coordination',
        type: 'task_completion_notice',
        taskId,
        result
      },
      null,
      { type: 'protocol', priority: 'medium' }
    );

    return { taskId, status: 'completed', result };
  }

  async handleTaskFail(message) {
    const { taskId, agentId, error, reason } = message;

    // Update task status
    const task = await this.memoryCoordination.retrieve('coord/tasks', taskId, 'system');
    if (task) {
      task.status = 'failed';
      task.failed = Date.now();
      task.error = error;
      task.reason = reason;

      await this.memoryCoordination.store('coord/tasks', taskId, task, 'system');
    }

    return { taskId, status: 'failed', error, reason };
  }

  /**
   * Resource Sharing Protocol Handlers
   */

  async handleResourceRequest(message) {
    const { resourceId, agentId, duration, priority, exclusive } = message;

    // Check resource availability
    const resource = await this.memoryCoordination.retrieve('coord/resources', resourceId, 'system');

    let granted = false;
    let reason = '';

    if (!resource || !resource.allocated) {
      // Resource is available
      granted = true;

      // Allocate resource
      await this.memoryCoordination.store(
        'coord/resources',
        resourceId,
        {
          id: resourceId,
          allocated: true,
          allocatedTo: agentId,
          allocatedAt: Date.now(),
          duration,
          exclusive,
          priority
        },
        'system'
      );
    } else {
      reason = 'Resource already allocated';
    }

    // Send response
    const responseType = granted ? 'resource_grant' : 'resource_deny';
    await this.communicationSystem.sendMessage(
      'system',
      agentId,
      {
        protocol: 'resource_sharing',
        type: responseType,
        resourceId,
        granted,
        reason
      },
      { type: 'protocol', priority: 'high' }
    );

    return { resourceId, granted, reason };
  }

  async handleResourceGrant(message) {
    const { resourceId, agentId } = message;

    // Record resource grant
    await this.memoryCoordination.store(
      'coord/resource_grants',
      `${resourceId}_${agentId}`,
      {
        resourceId,
        agentId,
        granted: Date.now()
      },
      agentId
    );

    return { resourceId, status: 'granted' };
  }

  async handleResourceDeny(message) {
    const { resourceId, agentId, reason } = message;

    // Record resource denial
    await this.memoryCoordination.store(
      'coord/resource_denials',
      `${resourceId}_${agentId}`,
      {
        resourceId,
        agentId,
        reason,
        denied: Date.now()
      },
      agentId
    );

    return { resourceId, status: 'denied', reason };
  }

  async handleResourceRelease(message) {
    const { resourceId, agentId } = message;

    // Release resource
    const resource = await this.memoryCoordination.retrieve('coord/resources', resourceId, 'system');
    if (resource && resource.allocatedTo === agentId) {
      resource.allocated = false;
      resource.releasedAt = Date.now();
      delete resource.allocatedTo;

      await this.memoryCoordination.store('coord/resources', resourceId, resource, 'system');
    }

    return { resourceId, status: 'released' };
  }

  /**
   * Consensus Protocol Handlers
   */

  async handleConsensusPropose(message) {
    const { proposalId, agentId, value, round } = message;

    // Store proposal
    await this.memoryCoordination.store(
      'coord/consensus',
      proposalId,
      {
        id: proposalId,
        proposer: agentId,
        value,
        round: round || 1,
        votes: new Map(),
        status: 'proposed',
        proposed: Date.now()
      },
      'system'
    );

    return { proposalId, status: 'proposed' };
  }

  async handleConsensusVote(message) {
    const { proposalId, agentId, vote, evidence } = message;

    // Record vote
    const proposal = await this.memoryCoordination.retrieve('coord/consensus', proposalId, 'system');
    if (proposal) {
      proposal.votes.set(agentId, {
        vote,
        evidence,
        timestamp: Date.now()
      });

      await this.memoryCoordination.store('coord/consensus', proposalId, proposal, 'system');
    }

    return { proposalId, vote, agentId };
  }

  async handleConsensusCommit(message) {
    const { proposalId, agentId } = message;

    // Commit consensus
    const proposal = await this.memoryCoordination.retrieve('coord/consensus', proposalId, 'system');
    if (proposal) {
      proposal.status = 'committed';
      proposal.committed = Date.now();

      await this.memoryCoordination.store('coord/consensus', proposalId, proposal, 'system');
    }

    return { proposalId, status: 'committed' };
  }

  async handleConsensusAbort(message) {
    const { proposalId, agentId, reason } = message;

    // Abort consensus
    const proposal = await this.memoryCoordination.retrieve('coord/consensus', proposalId, 'system');
    if (proposal) {
      proposal.status = 'aborted';
      proposal.reason = reason;
      proposal.aborted = Date.now();

      await this.memoryCoordination.store('coord/consensus', proposalId, proposal, 'system');
    }

    return { proposalId, status: 'aborted', reason };
  }

  /**
   * Health Monitoring Protocol Handlers
   */

  async handleHealthPing(message) {
    const { agentId } = message;

    // Send pong response
    await this.communicationSystem.sendMessage(
      'system',
      agentId,
      {
        protocol: 'health_monitoring',
        type: 'health_pong',
        timestamp: Date.now(),
        systemStatus: 'healthy'
      },
      { type: 'protocol', priority: 'high' }
    );

    return { agentId, response: 'pong_sent' };
  }

  async handleHealthPong(message) {
    const { agentId, systemStatus } = message;

    // Record health response
    await this.memoryCoordination.store(
      'coord/health_responses',
      `${agentId}_${Date.now()}`,
      {
        agentId,
        systemStatus,
        responseTime: Date.now() - (message.pingTime || Date.now()),
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, status: 'response_recorded' };
  }

  async handleHealthReport(message) {
    const { agentId, status, metrics, issues } = message;

    // Store health report
    await this.memoryCoordination.store(
      'coord/health_reports',
      `${agentId}_${Date.now()}`,
      {
        agentId,
        status,
        metrics,
        issues,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, reportReceived: true };
  }

  async handleHealthAlert(message) {
    const { agentId, alertType, severity, details } = message;

    // Process health alert
    await this.memoryCoordination.store(
      'coord/health_alerts',
      `${agentId}_${Date.now()}`,
      {
        agentId,
        alertType,
        severity,
        details,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, alertProcessed: true };
  }

  /**
   * Synchronization Protocol Handlers
   */

  async handleSyncRequest(message) {
    const { syncId, agentId, state, checkpoint } = message;

    // Process sync request
    await this.memoryCoordination.store(
      'coord/sync_requests',
      syncId,
      {
        id: syncId,
        requester: agentId,
        state,
        checkpoint,
        timestamp: Date.now()
      },
      'system'
    );

    return { syncId, status: 'request_received' };
  }

  async handleSyncResponse(message) {
    const { syncId, agentId, state, version } = message;

    // Store sync response
    await this.memoryCoordination.store(
      'coord/sync_responses',
      `${syncId}_${agentId}`,
      {
        syncId,
        agentId,
        state,
        version,
        timestamp: Date.now()
      },
      'system'
    );

    return { syncId, agentId, status: 'response_received' };
  }

  async handleSyncCommit(message) {
    const { syncId, agentId, state } = message;

    // Commit synchronization
    await this.memoryCoordination.store(
      'coord/sync_commits',
      syncId,
      {
        syncId,
        agentId,
        state,
        committed: Date.now()
      },
      'system'
    );

    return { syncId, status: 'committed' };
  }

  async handleSyncRollback(message) {
    const { syncId, agentId, reason } = message;

    // Rollback synchronization
    await this.memoryCoordination.store(
      'coord/sync_rollbacks',
      syncId,
      {
        syncId,
        agentId,
        reason,
        rolledBack: Date.now()
      },
      'system'
    );

    return { syncId, status: 'rolled_back', reason };
  }

  /**
   * Lifecycle Protocol Handlers
   */

  async handleLifecycleSpawn(message) {
    const { agentId, metadata } = message;

    await this.memoryCoordination.store(
      'coord/lifecycle_events',
      `spawn_${agentId}_${Date.now()}`,
      {
        event: 'spawn',
        agentId,
        metadata,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, event: 'spawn', status: 'recorded' };
  }

  async handleLifecycleReady(message) {
    const { agentId, state } = message;

    await this.memoryCoordination.store(
      'coord/lifecycle_events',
      `ready_${agentId}_${Date.now()}`,
      {
        event: 'ready',
        agentId,
        state,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, event: 'ready', status: 'recorded' };
  }

  async handleLifecycleTerminate(message) {
    const { agentId, reason } = message;

    await this.memoryCoordination.store(
      'coord/lifecycle_events',
      `terminate_${agentId}_${Date.now()}`,
      {
        event: 'terminate',
        agentId,
        reason,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, event: 'terminate', status: 'recorded' };
  }

  async handleLifecycleRestart(message) {
    const { agentId, reason, state } = message;

    await this.memoryCoordination.store(
      'coord/lifecycle_events',
      `restart_${agentId}_${Date.now()}`,
      {
        event: 'restart',
        agentId,
        reason,
        state,
        timestamp: Date.now()
      },
      'system'
    );

    return { agentId, event: 'restart', status: 'recorded' };
  }

  /**
   * Setup protocol middleware
   */
  setupProtocolMiddleware() {
    // Pre-processing middleware
    this.middlewares.set('pre_processing', [
      this.timestampMiddleware.bind(this),
      this.validationMiddleware.bind(this),
      this.authenticationMiddleware.bind(this)
    ]);

    // Post-processing middleware
    this.middlewares.set('post_processing', [
      this.loggingMiddleware.bind(this),
      this.metricsMiddleware.bind(this)
    ]);
  }

  /**
   * Middleware functions
   */

  async timestampMiddleware(message) {
    if (!message.timestamp) {
      message.timestamp = Date.now();
    }
    return message;
  }

  async validationMiddleware(message) {
    // Additional validation beyond basic protocol validation
    return message;
  }

  async authenticationMiddleware(message) {
    // Authentication and authorization checks
    return message;
  }

  async loggingMiddleware(result, originalMessage) {
    // Log protocol interactions
    console.debug(`Protocol ${originalMessage.protocol}:${originalMessage.type} processed`);
    return result;
  }

  async metricsMiddleware(result, originalMessage) {
    // Update protocol metrics
    const protocolKey = `${originalMessage.protocol}:${originalMessage.type}`;
    const stats = this.protocolStats.get(protocolKey) || { count: 0, lastUsed: null };
    stats.count++;
    stats.lastUsed = Date.now();
    this.protocolStats.set(protocolKey, stats);

    return result;
  }

  /**
   * Initialize protocol statistics
   */
  initializeProtocolStats() {
    // Initialize stats for all registered protocols
    this.protocols.forEach((protocol, protocolName) => {
      protocol.messageTypes.forEach(messageType => {
        const key = `${protocolName}:${messageType}`;
        this.protocolStats.set(key, {
          count: 0,
          lastUsed: null,
          errors: 0
        });
      });
    });
  }

  /**
   * Record protocol usage
   */
  async recordProtocolUsage(message, result) {
    const usage = {
      protocol: message.protocol,
      messageType: message.type,
      agentId: message.agentId,
      success: !!result,
      timestamp: Date.now()
    };

    await this.memoryCoordination.store(
      'coord/protocol_usage',
      `${message.protocol}_${message.type}_${Date.now()}`,
      usage,
      'system'
    );
  }

  /**
   * Get protocol statistics
   */
  getProtocolStatistics() {
    return {
      registeredProtocols: this.protocols.size,
      registeredHandlers: this.handlers.size,
      activeProtocols: this.activeProtocols.size,
      statistics: Object.fromEntries(this.protocolStats),
      handlerStats: this.getHandlerStatistics()
    };
  }

  /**
   * Get handler statistics
   */
  getHandlerStatistics() {
    const stats = {};
    this.handlers.forEach((handlerInfo, key) => {
      stats[key] = {
        callCount: handlerInfo.callCount,
        lastCall: handlerInfo.lastCall,
        registered: handlerInfo.registered
      };
    });
    return stats;
  }

  /**
   * Add custom protocol
   */
  addProtocol(protocolName, protocolDefinition) {
    this.protocols.set(protocolName, {
      ...protocolDefinition,
      name: protocolName,
      registered: Date.now()
    });

    this.activeProtocols.add(protocolName);

    return true;
  }

  /**
   * Remove protocol
   */
  removeProtocol(protocolName) {
    this.protocols.delete(protocolName);
    this.activeProtocols.delete(protocolName);

    // Remove related handlers
    const handlersToRemove = [];
    this.handlers.forEach((handlerInfo, key) => {
      if (handlerInfo.protocol === protocolName) {
        handlersToRemove.push(key);
      }
    });

    handlersToRemove.forEach(key => this.handlers.delete(key));

    return true;
  }

  /**
   * Cleanup protocol handlers
   */
  cleanup() {
    this.protocols.clear();
    this.handlers.clear();
    this.middlewares.clear();
    this.protocolStats.clear();
    this.activeProtocols.clear();
  }
}

module.exports = ProtocolHandlers;