/**
 * CrossAgentCommunication - Inter-agent messaging and coordination system
 * Implements real-time communication between parallel agents
 */

class CrossAgentCommunication {
  constructor(memoryStore) {
    this.memoryStore = memoryStore;
    this.messageQueue = new Map();
    this.subscriptions = new Map();
    this.channels = new Map();
    this.messageHistory = [];
    this.conflictQueue = [];
  }

  /**
   * Initialize communication system for agent batch
   */
  initializeBatchCommunication(agentIds) {
    const communicationMatrix = {
      agents: agentIds,
      channels: new Map(),
      messageRoutes: new Map(),
      broadcastChannels: new Set(),
      priorities: new Map()
    };

    // Create channels for each agent
    agentIds.forEach(agentId => {
      const channel = this.createAgentChannel(agentId);
      communicationMatrix.channels.set(agentId, channel);
      this.channels.set(agentId, channel);
    });

    // Setup routing table for efficient message delivery
    this.setupMessageRouting(agentIds, communicationMatrix);

    // Store communication matrix in memory
    this.memoryStore.set('coord/communication/matrix', communicationMatrix);

    return communicationMatrix;
  }

  /**
   * Create dedicated communication channel for agent
   */
  createAgentChannel(agentId) {
    const channel = {
      id: agentId,
      inbox: [],
      outbox: [],
      subscriptions: new Set(),
      messageHandlers: new Map(),
      priority: 'normal',
      status: 'active',
      statistics: {
        messagesSent: 0,
        messagesReceived: 0,
        lastActivity: Date.now()
      }
    };

    this.messageQueue.set(agentId, []);
    return channel;
  }

  /**
   * Setup message routing for efficient delivery
   */
  setupMessageRouting(agentIds, communicationMatrix) {
    agentIds.forEach(sourceId => {
      const routes = new Map();
      agentIds.forEach(targetId => {
        if (sourceId !== targetId) {
          routes.set(targetId, {
            direct: true,
            latency: 0,
            reliability: 1.0
          });
        }
      });
      communicationMatrix.messageRoutes.set(sourceId, routes);
    });
  }

  /**
   * Send message between agents with coordination tracking
   */
  async sendMessage(fromId, toId, message, options = {}) {
    const messageObj = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      from: fromId,
      to: toId,
      content: message,
      type: options.type || 'general',
      priority: options.priority || 'normal',
      timestamp: Date.now(),
      status: 'pending',
      metadata: options.metadata || {}
    };

    // Store in sender's outbox
    const senderChannel = this.channels.get(fromId);
    if (senderChannel) {
      senderChannel.outbox.push(messageObj);
      senderChannel.statistics.messagesSent++;
      senderChannel.statistics.lastActivity = Date.now();
    }

    // Queue for delivery
    const recipientQueue = this.messageQueue.get(toId);
    if (recipientQueue) {
      recipientQueue.push(messageObj);
      messageObj.status = 'queued';
    }

    // Store in memory for coordination hooks
    const memoryKey = `coord/messages/${fromId}/${toId}/${messageObj.id}`;
    this.memoryStore.set(memoryKey, messageObj);

    // Add to message history
    this.messageHistory.push(messageObj);

    // Trigger delivery
    await this.deliverMessage(messageObj);

    return messageObj.id;
  }

  /**
   * Deliver message to recipient agent
   */
  async deliverMessage(messageObj) {
    const recipientChannel = this.channels.get(messageObj.to);
    if (!recipientChannel) {
      messageObj.status = 'failed';
      return false;
    }

    // Add to recipient's inbox
    recipientChannel.inbox.push(messageObj);
    recipientChannel.statistics.messagesReceived++;
    recipientChannel.statistics.lastActivity = Date.now();

    // Update message status
    messageObj.status = 'delivered';
    messageObj.deliveredAt = Date.now();

    // Trigger subscribed handlers
    await this.triggerMessageHandlers(messageObj.to, messageObj);

    // Update memory
    const memoryKey = `coord/messages/${messageObj.from}/${messageObj.to}/${messageObj.id}`;
    this.memoryStore.set(memoryKey, messageObj);

    return true;
  }

  /**
   * Broadcast message to multiple agents
   */
  async broadcastMessage(fromId, message, targets = null, options = {}) {
    const communicationMatrix = this.memoryStore.get('coord/communication/matrix');
    const targetAgents = targets || communicationMatrix.agents.filter(id => id !== fromId);

    const broadcastId = `broadcast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const messagePromises = targetAgents.map(targetId =>
      this.sendMessage(fromId, targetId, message, {
        ...options,
        type: 'broadcast',
        broadcastId
      })
    );

    const messageIds = await Promise.all(messagePromises);

    // Store broadcast info in memory
    const broadcastInfo = {
      id: broadcastId,
      from: fromId,
      targets: targetAgents,
      messageIds,
      timestamp: Date.now(),
      content: message
    };

    this.memoryStore.set(`coord/broadcasts/${broadcastId}`, broadcastInfo);

    return broadcastId;
  }

  /**
   * Subscribe agent to specific message types
   */
  subscribe(agentId, messageType, handler) {
    const channel = this.channels.get(agentId);
    if (!channel) return false;

    channel.subscriptions.add(messageType);
    channel.messageHandlers.set(messageType, handler);

    // Store subscription in memory
    const subscriptionKey = `coord/subscriptions/${agentId}/${messageType}`;
    this.memoryStore.set(subscriptionKey, {
      agentId,
      messageType,
      timestamp: Date.now(),
      active: true
    });

    return true;
  }

  /**
   * Trigger message handlers for agent
   */
  async triggerMessageHandlers(agentId, message) {
    const channel = this.channels.get(agentId);
    if (!channel) return;

    const handler = channel.messageHandlers.get(message.type);
    if (handler) {
      try {
        await handler(message);
      } catch (error) {
        console.error(`Message handler failed for agent ${agentId}:`, error);
      }
    }

    // Trigger wildcard handlers
    const wildcardHandler = channel.messageHandlers.get('*');
    if (wildcardHandler) {
      try {
        await wildcardHandler(message);
      } catch (error) {
        console.error(`Wildcard handler failed for agent ${agentId}:`, error);
      }
    }
  }

  /**
   * Get unread messages for agent
   */
  getUnreadMessages(agentId) {
    const queue = this.messageQueue.get(agentId);
    if (!queue) return [];

    const unreadMessages = queue.filter(msg => msg.status === 'queued');

    // Mark as read
    unreadMessages.forEach(msg => {
      msg.status = 'read';
      msg.readAt = Date.now();
    });

    return unreadMessages;
  }

  /**
   * Request coordination between agents for task execution
   */
  async requestCoordination(requesterId, targetIds, coordinationRequest) {
    const coordinationId = `coord_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const coordination = {
      id: coordinationId,
      requester: requesterId,
      targets: targetIds,
      request: coordinationRequest,
      status: 'pending',
      responses: new Map(),
      timestamp: Date.now(),
      deadline: coordinationRequest.deadline || (Date.now() + 30000) // 30 second default
    };

    // Store coordination request
    this.memoryStore.set(`coord/requests/${coordinationId}`, coordination);

    // Send coordination request to all targets
    const requestPromises = targetIds.map(targetId =>
      this.sendMessage(requesterId, targetId, {
        type: 'coordination_request',
        coordinationId,
        request: coordinationRequest
      }, { type: 'coordination', priority: 'high' })
    );

    await Promise.all(requestPromises);

    return coordinationId;
  }

  /**
   * Respond to coordination request
   */
  async respondToCoordination(responderId, coordinationId, response) {
    const coordination = this.memoryStore.get(`coord/requests/${coordinationId}`);
    if (!coordination) {
      throw new Error(`Coordination ${coordinationId} not found`);
    }

    // Store response
    coordination.responses.set(responderId, {
      response,
      timestamp: Date.now(),
      agentId: responderId
    });

    // Check if all responses received
    if (coordination.responses.size === coordination.targets.length) {
      coordination.status = 'complete';
      coordination.completedAt = Date.now();

      // Notify requester of completion
      await this.sendMessage('system', coordination.requester, {
        type: 'coordination_complete',
        coordinationId,
        responses: Object.fromEntries(coordination.responses)
      }, { type: 'coordination', priority: 'high' });
    }

    // Update coordination in memory
    this.memoryStore.set(`coord/requests/${coordinationId}`, coordination);

    return coordination.status;
  }

  /**
   * Detect and handle conflicts between agents
   */
  detectConflicts() {
    const conflicts = [];
    const recentMessages = this.messageHistory.filter(
      msg => Date.now() - msg.timestamp < 60000 // Last minute
    );

    // Detect resource conflicts
    const resourceClaims = new Map();
    recentMessages.forEach(msg => {
      if (msg.content && msg.content.resourceClaim) {
        const resource = msg.content.resourceClaim;
        if (resourceClaims.has(resource)) {
          conflicts.push({
            type: 'resource_conflict',
            resource,
            agents: [resourceClaims.get(resource), msg.from],
            timestamp: Date.now()
          });
        } else {
          resourceClaims.set(resource, msg.from);
        }
      }
    });

    // Store conflicts for resolution
    conflicts.forEach(conflict => {
      this.conflictQueue.push(conflict);
      this.memoryStore.set(`coord/conflicts/${conflict.timestamp}`, conflict);
    });

    return conflicts;
  }

  /**
   * Get communication statistics
   */
  getCommunicationStats() {
    const stats = {
      totalMessages: this.messageHistory.length,
      totalAgents: this.channels.size,
      messagesByType: {},
      messagesByAgent: {},
      averageLatency: 0,
      conflictsDetected: this.conflictQueue.length
    };

    // Calculate message distribution
    this.messageHistory.forEach(msg => {
      stats.messagesByType[msg.type] = (stats.messagesByType[msg.type] || 0) + 1;
      stats.messagesByAgent[msg.from] = (stats.messagesByAgent[msg.from] || 0) + 1;
    });

    // Calculate average latency
    const deliveredMessages = this.messageHistory.filter(msg => msg.deliveredAt);
    if (deliveredMessages.length > 0) {
      const totalLatency = deliveredMessages.reduce(
        (sum, msg) => sum + (msg.deliveredAt - msg.timestamp), 0
      );
      stats.averageLatency = totalLatency / deliveredMessages.length;
    }

    return stats;
  }

  /**
   * Cleanup communication system
   */
  cleanup() {
    this.messageQueue.clear();
    this.subscriptions.clear();
    this.channels.clear();
    this.messageHistory = [];
    this.conflictQueue = [];
  }
}

module.exports = CrossAgentCommunication;