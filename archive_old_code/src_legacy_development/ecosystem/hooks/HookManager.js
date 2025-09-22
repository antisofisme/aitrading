/**
 * HookManager - Real-time MCP hooks integration
 * Manages lifecycle hooks for ecosystem coordination and response
 */

const { EventEmitter } = require('events');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class HookManager extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      hookTimeout: config.hookTimeout || 5000,
      retryAttempts: config.retryAttempts || 3,
      retryDelay: config.retryDelay || 1000,
      enableBatching: config.enableBatching !== false,
      batchSize: config.batchSize || 10,
      batchTimeout: config.batchTimeout || 2000,
      ...config
    };

    this.pendingHooks = new Map();
    this.batchQueue = [];
    this.batchTimer = null;
    this.hookHistory = [];
    this.isInitialized = false;
  }

  /**
   * Initialize the hook manager
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Setup event listeners for hook coordination
      this.setupEventListeners();

      // Initialize batch processing if enabled
      if (this.config.enableBatching) {
        this.initializeBatchProcessing();
      }

      // Restore any pending hooks from previous session
      await this.restorePendingHooks();

      this.isInitialized = true;
      console.log('🔗 Hook manager initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize hook manager:', error);
      throw error;
    }
  }

  /**
   * Execute pre-task hook
   */
  async executePreTaskHook(taskDescription, additionalData = {}) {
    const hookData = {
      type: 'pre-task',
      description: taskDescription,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      console.log(`🚀 Executing pre-task hook: ${taskDescription}`);

      const result = await this.executeHook('pre-task', {
        description: taskDescription,
        ...additionalData
      });

      // Store hook execution data
      this.storeHookExecution('pre-task', hookData, result);

      return result;
    } catch (error) {
      console.error('❌ Pre-task hook failed:', error);
      await this.handleHookError('pre-task', hookData, error);
      throw error;
    }
  }

  /**
   * Execute post-task hook
   */
  async executePostTaskHook(taskId, result = {}, additionalData = {}) {
    const hookData = {
      type: 'post-task',
      taskId,
      result,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      console.log(`✅ Executing post-task hook: ${taskId}`);

      const hookResult = await this.executeHook('post-task', {
        'task-id': taskId,
        ...additionalData
      });

      // Store hook execution data
      this.storeHookExecution('post-task', hookData, hookResult);

      return hookResult;
    } catch (error) {
      console.error('❌ Post-task hook failed:', error);
      await this.handleHookError('post-task', hookData, error);
      throw error;
    }
  }

  /**
   * Execute post-edit hook for file changes
   */
  async executePostEditHook(filePath, memoryKey, additionalData = {}) {
    const hookData = {
      type: 'post-edit',
      filePath,
      memoryKey,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      console.log(`📝 Executing post-edit hook: ${filePath}`);

      const result = await this.executeHook('post-edit', {
        file: filePath,
        'memory-key': memoryKey,
        ...additionalData
      });

      // Store hook execution data
      this.storeHookExecution('post-edit', hookData, result);

      // Emit event for ecosystem coordination
      this.emit('file-edited', { filePath, memoryKey, result });

      return result;
    } catch (error) {
      console.error('❌ Post-edit hook failed:', error);
      await this.handleHookError('post-edit', hookData, error);
      throw error;
    }
  }

  /**
   * Execute notification hook
   */
  async executeNotificationHook(message, additionalData = {}) {
    const hookData = {
      type: 'notification',
      message,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      if (this.config.enableBatching) {
        return this.addToBatch('notify', { message, ...additionalData });
      }

      const result = await this.executeHook('notify', {
        message,
        ...additionalData
      });

      this.storeHookExecution('notification', hookData, result);
      return result;
    } catch (error) {
      console.warn('⚠️ Notification hook failed:', error.message);
      // Don't throw for notifications as they're not critical
      return null;
    }
  }

  /**
   * Execute session restore hook
   */
  async executeSessionRestoreHook(sessionId, additionalData = {}) {
    const hookData = {
      type: 'session-restore',
      sessionId,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      console.log(`🔄 Executing session restore hook: ${sessionId}`);

      const result = await this.executeHook('session-restore', {
        'session-id': sessionId,
        ...additionalData
      });

      this.storeHookExecution('session-restore', hookData, result);
      return result;
    } catch (error) {
      console.warn('⚠️ Session restore hook failed:', error.message);
      // Don't throw for session restore as it's not critical
      return null;
    }
  }

  /**
   * Execute session end hook
   */
  async executeSessionEndHook(exportMetrics = true, additionalData = {}) {
    const hookData = {
      type: 'session-end',
      exportMetrics,
      timestamp: new Date().toISOString(),
      ...additionalData
    };

    try {
      console.log('🏁 Executing session end hook');

      const result = await this.executeHook('session-end', {
        'export-metrics': exportMetrics,
        ...additionalData
      });

      this.storeHookExecution('session-end', hookData, result);

      // Clean up any pending hooks
      await this.cleanupPendingHooks();

      return result;
    } catch (error) {
      console.error('❌ Session end hook failed:', error);
      throw error;
    }
  }

  /**
   * Core hook execution method
   */
  async executeHook(hookType, params) {
    const hookId = this.generateHookId();
    this.pendingHooks.set(hookId, { type: hookType, params, startTime: Date.now() });

    try {
      // Build command
      const command = this.buildHookCommand(hookType, params);

      // Execute with retry logic
      const result = await this.executeWithRetry(command);

      // Remove from pending hooks
      this.pendingHooks.delete(hookId);

      return result;
    } catch (error) {
      this.pendingHooks.delete(hookId);
      throw error;
    }
  }

  /**
   * Build Claude Flow hook command
   */
  buildHookCommand(hookType, params) {
    let command = `npx claude-flow@alpha hooks ${hookType}`;

    // Add parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (typeof value === 'object') {
          command += ` --${key} '${JSON.stringify(value)}'`;
        } else {
          command += ` --${key} "${value}"`;
        }
      }
    });

    return command;
  }

  /**
   * Execute command with retry logic
   */
  async executeWithRetry(command, attempt = 1) {
    try {
      const result = await execAsync(command, {
        timeout: this.config.hookTimeout,
        maxBuffer: 1024 * 1024 // 1MB buffer
      });

      return {
        success: true,
        stdout: result.stdout,
        stderr: result.stderr,
        command,
        attempt
      };
    } catch (error) {
      if (attempt < this.config.retryAttempts) {
        console.warn(`⚠️ Hook execution failed (attempt ${attempt}), retrying...`);
        await this.delay(this.config.retryDelay * attempt);
        return this.executeWithRetry(command, attempt + 1);
      }

      throw {
        success: false,
        error: error.message,
        command,
        attempts: attempt
      };
    }
  }

  /**
   * Batch processing for non-critical hooks
   */
  initializeBatchProcessing() {
    // Setup periodic batch processing
    setInterval(() => {
      if (this.batchQueue.length > 0) {
        this.processBatch();
      }
    }, this.config.batchTimeout);
  }

  addToBatch(hookType, params) {
    this.batchQueue.push({
      type: hookType,
      params,
      timestamp: new Date().toISOString()
    });

    // Process batch if it reaches max size
    if (this.batchQueue.length >= this.config.batchSize) {
      this.processBatch();
    }

    return Promise.resolve({ batched: true });
  }

  async processBatch() {
    if (this.batchQueue.length === 0) return;

    const batch = [...this.batchQueue];
    this.batchQueue = [];

    console.log(`📦 Processing batch of ${batch.length} hooks`);

    try {
      // Group by hook type for efficient processing
      const groupedHooks = this.groupHooksByType(batch);

      // Process each group in parallel
      const promises = Object.entries(groupedHooks).map(([type, hooks]) =>
        this.processBatchGroup(type, hooks)
      );

      await Promise.allSettled(promises);
    } catch (error) {
      console.error('❌ Failed to process hook batch:', error);
    }
  }

  groupHooksByType(hooks) {
    return hooks.reduce((groups, hook) => {
      if (!groups[hook.type]) {
        groups[hook.type] = [];
      }
      groups[hook.type].push(hook);
      return groups;
    }, {});
  }

  async processBatchGroup(type, hooks) {
    try {
      // For notification hooks, we can batch them together
      if (type === 'notify') {
        const messages = hooks.map(h => h.params.message).join('; ');
        await this.executeHook('notify', { message: `Batch: ${messages}` });
      } else {
        // For other hook types, execute individually
        for (const hook of hooks) {
          await this.executeHook(hook.type, hook.params);
        }
      }
    } catch (error) {
      console.warn(`⚠️ Failed to process batch group ${type}:`, error.message);
    }
  }

  /**
   * Hook coordination and event handling
   */
  setupEventListeners() {
    // Listen for ecosystem events
    this.on('agent-spawned', this.handleAgentSpawned.bind(this));
    this.on('task-completed', this.handleTaskCompleted.bind(this));
    this.on('file-changed', this.handleFileChanged.bind(this));
    this.on('error', this.handleError.bind(this));
  }

  async handleAgentSpawned(agentData) {
    await this.executeNotificationHook(
      `Agent spawned: ${agentData.type} (${agentData.id})`,
      { agentData }
    );
  }

  async handleTaskCompleted(taskData) {
    await this.executePostTaskHook(
      taskData.id,
      taskData.result,
      { duration: taskData.duration }
    );
  }

  async handleFileChanged(changeData) {
    await this.executePostEditHook(
      changeData.filePath,
      `ecosystem/changes/${Date.now()}`,
      { changeType: changeData.type }
    );
  }

  async handleError(error) {
    await this.executeNotificationHook(
      `Ecosystem error: ${error.message}`,
      { error: error.stack, severity: 'error' }
    );
  }

  /**
   * Hook execution tracking and history
   */
  storeHookExecution(type, hookData, result) {
    const execution = {
      id: this.generateHookId(),
      type,
      hookData,
      result,
      timestamp: new Date().toISOString(),
      success: result?.success !== false
    };

    this.hookHistory.push(execution);

    // Limit history size
    if (this.hookHistory.length > 1000) {
      this.hookHistory = this.hookHistory.slice(-500);
    }

    // Emit execution event
    this.emit('hook-executed', execution);
  }

  async handleHookError(hookType, hookData, error) {
    console.error(`Hook execution failed: ${hookType}`, error);

    const errorExecution = {
      id: this.generateHookId(),
      type: hookType,
      hookData,
      error: error.message,
      timestamp: new Date().toISOString(),
      success: false
    };

    this.hookHistory.push(errorExecution);
    this.emit('hook-error', errorExecution);
  }

  /**
   * Cleanup and maintenance
   */
  async restorePendingHooks() {
    // Implementation for restoring hooks from previous session
    // This could involve reading from a persistent store
    console.log('🔄 Checking for pending hooks from previous session...');
  }

  async cleanupPendingHooks() {
    const pendingCount = this.pendingHooks.size;
    if (pendingCount > 0) {
      console.log(`🧹 Cleaning up ${pendingCount} pending hooks...`);

      // Wait for pending hooks to complete or timeout
      const pendingPromises = Array.from(this.pendingHooks.keys()).map(hookId => {
        const hook = this.pendingHooks.get(hookId);
        const elapsed = Date.now() - hook.startTime;
        const remaining = Math.max(0, this.config.hookTimeout - elapsed);

        return new Promise(resolve => {
          setTimeout(() => {
            this.pendingHooks.delete(hookId);
            resolve();
          }, remaining);
        });
      });

      await Promise.allSettled(pendingPromises);
    }
  }

  /**
   * Utility methods
   */
  generateHookId() {
    return `hook_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Public API methods
   */
  getHookHistory(type = null, limit = 50) {
    let history = this.hookHistory;

    if (type) {
      history = history.filter(h => h.type === type);
    }

    return history.slice(-limit);
  }

  getPendingHooks() {
    return Array.from(this.pendingHooks.entries()).map(([id, hook]) => ({
      id,
      ...hook,
      elapsed: Date.now() - hook.startTime
    }));
  }

  getStats() {
    const successful = this.hookHistory.filter(h => h.success).length;
    const failed = this.hookHistory.filter(h => !h.success).length;

    return {
      totalExecutions: this.hookHistory.length,
      successful,
      failed,
      successRate: this.hookHistory.length > 0 ? (successful / this.hookHistory.length) * 100 : 0,
      pendingHooks: this.pendingHooks.size,
      batchQueueSize: this.batchQueue.length
    };
  }
}

module.exports = HookManager;