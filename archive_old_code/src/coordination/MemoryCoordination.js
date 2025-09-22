/**
 * MemoryCoordination - Shared memory system for agent coordination
 * Implements memory-based state sharing and persistence
 */

class MemoryCoordination {
  constructor() {
    this.globalMemory = new Map();
    this.agentMemories = new Map();
    this.sharedNamespaces = new Map();
    this.memorySubscriptions = new Map();
    this.memoryHistory = [];
    this.lockManager = new Map();
    this.versionControl = new Map();
  }

  /**
   * Initialize memory coordination for agent batch
   */
  initializeBatchMemory(agentIds) {
    const memoryStructure = {
      global: this.createGlobalMemory(),
      agents: new Map(),
      shared: new Map(),
      coordination: this.createCoordinationMemory(),
      locks: new Map(),
      metadata: {
        created: Date.now(),
        agents: agentIds,
        version: 1
      }
    };

    // Create individual agent memory spaces
    agentIds.forEach(agentId => {
      const agentMemory = this.createAgentMemory(agentId);
      memoryStructure.agents.set(agentId, agentMemory);
      this.agentMemories.set(agentId, agentMemory);
    });

    // Setup shared namespaces
    this.setupSharedNamespaces(agentIds, memoryStructure);

    // Store in global memory
    this.globalMemory.set('coordination/structure', memoryStructure);

    return memoryStructure;
  }

  /**
   * Create global memory space
   */
  createGlobalMemory() {
    return {
      state: new Map(),
      taskResults: new Map(),
      agentStatuses: new Map(),
      dependencies: new Map(),
      conflicts: [],
      events: [],
      metrics: {
        totalOperations: 0,
        memoryUsage: 0,
        lastUpdate: Date.now()
      }
    };
  }

  /**
   * Create individual agent memory space
   */
  createAgentMemory(agentId) {
    const memory = {
      id: agentId,
      local: new Map(),
      shared: new Map(),
      cache: new Map(),
      subscriptions: new Set(),
      locks: new Set(),
      history: [],
      metadata: {
        created: Date.now(),
        lastAccess: Date.now(),
        operations: 0,
        size: 0
      }
    };

    return memory;
  }

  /**
   * Create coordination memory for cross-agent operations
   */
  createCoordinationMemory() {
    return {
      activeCoordinations: new Map(),
      coordinationHistory: [],
      messageQueues: new Map(),
      synchronizationPoints: new Map(),
      conflictResolution: new Map(),
      resourceAllocations: new Map()
    };
  }

  /**
   * Setup shared namespaces for specific coordination patterns
   */
  setupSharedNamespaces(agentIds, memoryStructure) {
    const namespaces = [
      'coord/tasks',
      'coord/results',
      'coord/dependencies',
      'coord/conflicts',
      'coord/resources',
      'coord/synchronization'
    ];

    namespaces.forEach(namespace => {
      const sharedSpace = {
        namespace,
        data: new Map(),
        subscribers: new Set(),
        accessControl: new Map(),
        version: 1,
        lastModified: Date.now()
      };

      // Grant access to all agents
      agentIds.forEach(agentId => {
        sharedSpace.accessControl.set(agentId, ['read', 'write']);
        sharedSpace.subscribers.add(agentId);
      });

      this.sharedNamespaces.set(namespace, sharedSpace);
      memoryStructure.shared.set(namespace, sharedSpace);
    });
  }

  /**
   * Store data in memory with coordination tracking
   */
  async store(namespace, key, data, agentId, options = {}) {
    const operation = {
      id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'store',
      namespace,
      key,
      agentId,
      timestamp: Date.now(),
      data: this.cloneData(data),
      options
    };

    // Check permissions
    if (!this.checkPermissions(namespace, agentId, 'write')) {
      throw new Error(`Agent ${agentId} does not have write permission for ${namespace}`);
    }

    // Acquire lock if needed
    if (options.lock) {
      await this.acquireLock(namespace, key, agentId);
    }

    try {
      // Store in appropriate memory space
      if (namespace.startsWith('coord/')) {
        await this.storeInSharedNamespace(namespace, key, data, agentId);
      } else {
        await this.storeInAgentMemory(agentId, namespace, key, data);
      }

      // Update version control
      this.updateVersion(namespace, key);

      // Record operation
      this.recordOperation(operation);

      // Notify subscribers
      await this.notifySubscribers(namespace, key, data, agentId, 'store');

      return operation.id;
    } finally {
      // Release lock if acquired
      if (options.lock) {
        this.releaseLock(namespace, key, agentId);
      }
    }
  }

  /**
   * Retrieve data from memory with coordination tracking
   */
  async retrieve(namespace, key, agentId, options = {}) {
    const operation = {
      id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'retrieve',
      namespace,
      key,
      agentId,
      timestamp: Date.now(),
      options
    };

    // Check permissions
    if (!this.checkPermissions(namespace, agentId, 'read')) {
      throw new Error(`Agent ${agentId} does not have read permission for ${namespace}`);
    }

    let data;
    if (namespace.startsWith('coord/')) {
      data = await this.retrieveFromSharedNamespace(namespace, key);
    } else {
      data = await this.retrieveFromAgentMemory(agentId, namespace, key);
    }

    // Update access metadata
    this.updateAccessMetadata(agentId, namespace, key);

    // Record operation
    this.recordOperation(operation);

    return data;
  }

  /**
   * Store data in shared namespace
   */
  async storeInSharedNamespace(namespace, key, data, agentId) {
    const sharedSpace = this.sharedNamespaces.get(namespace);
    if (!sharedSpace) {
      throw new Error(`Shared namespace ${namespace} not found`);
    }

    const previousData = sharedSpace.data.get(key);
    sharedSpace.data.set(key, {
      value: this.cloneData(data),
      storedBy: agentId,
      timestamp: Date.now(),
      version: sharedSpace.version + 1
    });

    sharedSpace.lastModified = Date.now();
    sharedSpace.version++;

    // Store in global memory as well
    const globalMemory = this.globalMemory.get('coordination/structure').global;
    const globalKey = `${namespace}/${key}`;
    globalMemory.state.set(globalKey, {
      value: data,
      agentId,
      timestamp: Date.now()
    });
  }

  /**
   * Retrieve data from shared namespace
   */
  async retrieveFromSharedNamespace(namespace, key) {
    const sharedSpace = this.sharedNamespaces.get(namespace);
    if (!sharedSpace) {
      return null;
    }

    const storedData = sharedSpace.data.get(key);
    return storedData ? storedData.value : null;
  }

  /**
   * Store data in agent's private memory
   */
  async storeInAgentMemory(agentId, namespace, key, data) {
    const agentMemory = this.agentMemories.get(agentId);
    if (!agentMemory) {
      throw new Error(`Agent memory for ${agentId} not found`);
    }

    const memoryKey = `${namespace}/${key}`;
    agentMemory.local.set(memoryKey, {
      value: this.cloneData(data),
      timestamp: Date.now(),
      namespace,
      key
    });

    agentMemory.metadata.lastAccess = Date.now();
    agentMemory.metadata.operations++;
    agentMemory.metadata.size = agentMemory.local.size;
  }

  /**
   * Retrieve data from agent's private memory
   */
  async retrieveFromAgentMemory(agentId, namespace, key) {
    const agentMemory = this.agentMemories.get(agentId);
    if (!agentMemory) {
      return null;
    }

    const memoryKey = `${namespace}/${key}`;
    const storedData = agentMemory.local.get(memoryKey);

    if (storedData) {
      agentMemory.metadata.lastAccess = Date.now();
      return storedData.value;
    }

    return null;
  }

  /**
   * Subscribe to memory changes in namespace
   */
  subscribe(agentId, namespace, callback) {
    const subscriptionKey = `${agentId}:${namespace}`;

    if (!this.memorySubscriptions.has(subscriptionKey)) {
      this.memorySubscriptions.set(subscriptionKey, {
        agentId,
        namespace,
        callback,
        created: Date.now(),
        notifications: 0
      });

      // Add to shared namespace subscribers
      const sharedSpace = this.sharedNamespaces.get(namespace);
      if (sharedSpace) {
        sharedSpace.subscribers.add(agentId);
      }

      return true;
    }

    return false;
  }

  /**
   * Unsubscribe from memory changes
   */
  unsubscribe(agentId, namespace) {
    const subscriptionKey = `${agentId}:${namespace}`;
    const removed = this.memorySubscriptions.delete(subscriptionKey);

    if (removed) {
      const sharedSpace = this.sharedNamespaces.get(namespace);
      if (sharedSpace) {
        sharedSpace.subscribers.delete(agentId);
      }
    }

    return removed;
  }

  /**
   * Notify subscribers of memory changes
   */
  async notifySubscribers(namespace, key, data, agentId, operation) {
    const sharedSpace = this.sharedNamespaces.get(namespace);
    if (!sharedSpace) return;

    const notification = {
      namespace,
      key,
      data: this.cloneData(data),
      changedBy: agentId,
      operation,
      timestamp: Date.now()
    };

    const notificationPromises = Array.from(sharedSpace.subscribers)
      .filter(subscriberId => subscriberId !== agentId) // Don't notify the agent who made the change
      .map(subscriberId => {
        const subscriptionKey = `${subscriberId}:${namespace}`;
        const subscription = this.memorySubscriptions.get(subscriptionKey);

        if (subscription && subscription.callback) {
          subscription.notifications++;
          return subscription.callback(notification);
        }
      })
      .filter(Boolean);

    await Promise.all(notificationPromises);
  }

  /**
   * Acquire lock for exclusive access
   */
  async acquireLock(namespace, key, agentId, timeout = 5000) {
    const lockKey = `${namespace}/${key}`;
    const existingLock = this.lockManager.get(lockKey);

    if (existingLock && existingLock.agentId !== agentId) {
      // Wait for lock to be released or timeout
      const startTime = Date.now();
      while (this.lockManager.has(lockKey) && (Date.now() - startTime) < timeout) {
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      if (this.lockManager.has(lockKey)) {
        throw new Error(`Could not acquire lock for ${lockKey} within timeout`);
      }
    }

    const lock = {
      namespace,
      key,
      agentId,
      acquired: Date.now(),
      timeout
    };

    this.lockManager.set(lockKey, lock);

    // Add to agent's locks
    const agentMemory = this.agentMemories.get(agentId);
    if (agentMemory) {
      agentMemory.locks.add(lockKey);
    }

    return lock;
  }

  /**
   * Release lock
   */
  releaseLock(namespace, key, agentId) {
    const lockKey = `${namespace}/${key}`;
    const lock = this.lockManager.get(lockKey);

    if (lock && lock.agentId === agentId) {
      this.lockManager.delete(lockKey);

      // Remove from agent's locks
      const agentMemory = this.agentMemories.get(agentId);
      if (agentMemory) {
        agentMemory.locks.delete(lockKey);
      }

      return true;
    }

    return false;
  }

  /**
   * Check permissions for memory access
   */
  checkPermissions(namespace, agentId, operation) {
    const sharedSpace = this.sharedNamespaces.get(namespace);
    if (!sharedSpace) {
      // For agent-specific namespaces, only the agent can access
      return namespace.startsWith(agentId) || namespace === agentId;
    }

    const permissions = sharedSpace.accessControl.get(agentId);
    return permissions && permissions.includes(operation);
  }

  /**
   * Update version control for memory objects
   */
  updateVersion(namespace, key) {
    const versionKey = `${namespace}/${key}`;
    const currentVersion = this.versionControl.get(versionKey) || 0;
    this.versionControl.set(versionKey, currentVersion + 1);
  }

  /**
   * Update access metadata
   */
  updateAccessMetadata(agentId, namespace, key) {
    const agentMemory = this.agentMemories.get(agentId);
    if (agentMemory) {
      agentMemory.metadata.lastAccess = Date.now();
    }
  }

  /**
   * Record memory operation for auditing
   */
  recordOperation(operation) {
    this.memoryHistory.push(operation);

    // Update global metrics
    const globalMemory = this.globalMemory.get('coordination/structure').global;
    globalMemory.metrics.totalOperations++;
    globalMemory.metrics.lastUpdate = Date.now();

    // Limit history size
    if (this.memoryHistory.length > 10000) {
      this.memoryHistory = this.memoryHistory.slice(-5000);
    }
  }

  /**
   * Get memory statistics and usage
   */
  getMemoryStatistics() {
    const stats = {
      global: {
        totalMemorySpaces: this.globalMemory.size,
        totalOperations: this.memoryHistory.length,
        locksActive: this.lockManager.size
      },
      agents: {},
      shared: {},
      operations: {
        byType: {},
        byAgent: {},
        recentActivity: this.getRecentActivity()
      }
    };

    // Collect agent statistics
    this.agentMemories.forEach((memory, agentId) => {
      stats.agents[agentId] = {
        localKeys: memory.local.size,
        sharedKeys: memory.shared.size,
        operations: memory.metadata.operations,
        lastAccess: memory.metadata.lastAccess,
        locks: memory.locks.size
      };
    });

    // Collect shared namespace statistics
    this.sharedNamespaces.forEach((space, namespace) => {
      stats.shared[namespace] = {
        keys: space.data.size,
        subscribers: space.subscribers.size,
        version: space.version,
        lastModified: space.lastModified
      };
    });

    // Analyze operations
    this.memoryHistory.forEach(op => {
      stats.operations.byType[op.type] = (stats.operations.byType[op.type] || 0) + 1;
      stats.operations.byAgent[op.agentId] = (stats.operations.byAgent[op.agentId] || 0) + 1;
    });

    return stats;
  }

  /**
   * Get recent activity summary
   */
  getRecentActivity(timeWindow = 60000) {
    const cutoff = Date.now() - timeWindow;
    const recentOperations = this.memoryHistory.filter(op => op.timestamp >= cutoff);

    return {
      totalOperations: recentOperations.length,
      stores: recentOperations.filter(op => op.type === 'store').length,
      retrieves: recentOperations.filter(op => op.type === 'retrieve').length,
      uniqueAgents: new Set(recentOperations.map(op => op.agentId)).size,
      uniqueNamespaces: new Set(recentOperations.map(op => op.namespace)).size
    };
  }

  /**
   * Clone data to prevent reference issues
   */
  cloneData(data) {
    try {
      return JSON.parse(JSON.stringify(data));
    } catch (error) {
      // For non-serializable data, return as-is
      return data;
    }
  }

  /**
   * Cleanup memory coordination system
   */
  cleanup() {
    this.globalMemory.clear();
    this.agentMemories.clear();
    this.sharedNamespaces.clear();
    this.memorySubscriptions.clear();
    this.memoryHistory = [];
    this.lockManager.clear();
    this.versionControl.clear();
  }
}

module.exports = MemoryCoordination;