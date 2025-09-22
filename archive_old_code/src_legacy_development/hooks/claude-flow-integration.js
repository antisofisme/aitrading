/**
 * Claude Flow Integration Module
 * Handles communication with Claude Flow MCP for coordination and memory
 */

import { EventEmitter } from 'events';
import { execSync, exec } from 'child_process';
import fs from 'fs/promises';
import path from 'path';

export class ClaudeFlowIntegration extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      claudeFlowPath: config.claudeFlowPath || 'npx claude-flow@alpha',
      sessionId: config.sessionId || `mermaid-${Date.now()}`,
      memoryNamespace: config.memoryNamespace || 'mermaid-diagrams',
      enableHooks: config.enableHooks !== false,
      hookTimeout: config.hookTimeout || 30000,
      ...config
    };

    this.hooks = new Map();
    this.memoryCache = new Map();
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // Check if Claude Flow is available
      await this.checkClaudeFlowAvailability();

      // Initialize session
      await this.initializeSession();

      // Setup hooks if enabled
      if (this.config.enableHooks) {
        await this.setupHooks();
      }

      this.isInitialized = true;
      this.emit('initialized');

      console.log('Claude Flow integration initialized successfully');
    } catch (error) {
      console.warn('Claude Flow integration failed to initialize:', error.message);
      // Continue without Claude Flow integration
      this.isInitialized = false;
    }
  }

  async checkClaudeFlowAvailability() {
    return new Promise((resolve, reject) => {
      exec(`${this.config.claudeFlowPath} --version`, (error, stdout, stderr) => {
        if (error) {
          reject(new Error('Claude Flow not available. Please install: npm install -g claude-flow@alpha'));
        } else {
          resolve(stdout.trim());
        }
      });
    });
  }

  async initializeSession() {
    try {
      const result = await this.executeCommand('hooks session-start', {
        sessionId: this.config.sessionId,
        description: 'Mermaid diagram generation session'
      });

      console.log('Claude Flow session started:', this.config.sessionId);
      return result;
    } catch (error) {
      throw new Error(`Failed to initialize Claude Flow session: ${error.message}`);
    }
  }

  async setupHooks() {
    const hookCommands = [
      'hooks register pre-task --description "Before diagram generation"',
      'hooks register post-task --description "After diagram generation"',
      'hooks register post-edit --description "After file changes"',
      'hooks register session-restore --description "Restore session state"',
      'hooks register session-end --description "End session"'
    ];

    for (const command of hookCommands) {
      try {
        await this.executeCommand(command);
      } catch (error) {
        console.warn(`Failed to register hook: ${command}`, error.message);
      }
    }
  }

  async executeCommand(command, options = {}) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error(`Command timeout: ${command}`));
      }, this.config.hookTimeout);

      const fullCommand = `${this.config.claudeFlowPath} ${command}`;
      const env = { ...process.env, ...options };

      exec(fullCommand, { env }, (error, stdout, stderr) => {
        clearTimeout(timeout);

        if (error) {
          reject(new Error(`Command failed: ${command}\n${stderr || error.message}`));
        } else {
          try {
            // Try to parse JSON response
            const result = stdout.trim() ? JSON.parse(stdout) : {};
            resolve(result);
          } catch (parseError) {
            // Return raw output if not JSON
            resolve(stdout.trim());
          }
        }
      });
    });
  }

  // Hook Management
  async registerHook(hookType, callback) {
    if (!this.isInitialized) {
      console.warn('Claude Flow not initialized, hook registration skipped');
      return;
    }

    this.hooks.set(hookType, callback);
    this.emit('hook-registered', { type: hookType });
  }

  async triggerHook(hookType, data = {}) {
    if (!this.isInitialized) {
      return;
    }

    try {
      // Execute Claude Flow hook
      await this.executeCommand(`hooks ${hookType}`, data);

      // Execute local callback if registered
      const callback = this.hooks.get(hookType);
      if (callback) {
        await callback(data);
      }

      this.emit(hookType, data);
    } catch (error) {
      console.warn(`Hook execution failed: ${hookType}`, error.message);
    }
  }

  // Memory Management
  async storeInMemory(key, value, options = {}) {
    if (!this.isInitialized) {
      // Store in local cache if Claude Flow not available
      this.memoryCache.set(key, value);
      return;
    }

    try {
      const memoryKey = `${this.config.memoryNamespace}/${key}`;
      const data = {
        key: memoryKey,
        value: JSON.stringify(value),
        namespace: this.config.memoryNamespace,
        ttl: options.ttl || 86400, // 24 hours default
        sessionId: this.config.sessionId
      };

      const result = await this.executeCommand('memory store', data);

      // Also store in local cache for faster access
      this.memoryCache.set(key, value);

      return result;
    } catch (error) {
      console.warn(`Failed to store in Claude Flow memory: ${key}`, error.message);
      // Fallback to local cache
      this.memoryCache.set(key, value);
    }
  }

  async getFromMemory(key) {
    // Try local cache first
    if (this.memoryCache.has(key)) {
      return this.memoryCache.get(key);
    }

    if (!this.isInitialized) {
      return null;
    }

    try {
      const memoryKey = `${this.config.memoryNamespace}/${key}`;
      const result = await this.executeCommand('memory retrieve', {
        key: memoryKey,
        namespace: this.config.memoryNamespace
      });

      if (result && result.value) {
        const value = JSON.parse(result.value);
        this.memoryCache.set(key, value);
        return value;
      }

      return null;
    } catch (error) {
      console.warn(`Failed to retrieve from Claude Flow memory: ${key}`, error.message);
      return null;
    }
  }

  async searchMemory(pattern, options = {}) {
    if (!this.isInitialized) {
      // Search local cache with pattern
      const results = [];
      for (const [key, value] of this.memoryCache) {
        if (key.includes(pattern)) {
          results.push({ key, value });
        }
      }
      return results;
    }

    try {
      const result = await this.executeCommand('memory search', {
        pattern,
        namespace: this.config.memoryNamespace,
        limit: options.limit || 100
      });

      return result.results || [];
    } catch (error) {
      console.warn(`Failed to search Claude Flow memory: ${pattern}`, error.message);
      return [];
    }
  }

  async clearMemory(pattern = '') {
    // Clear local cache
    if (pattern) {
      for (const key of this.memoryCache.keys()) {
        if (key.includes(pattern)) {
          this.memoryCache.delete(key);
        }
      }
    } else {
      this.memoryCache.clear();
    }

    if (!this.isInitialized) {
      return;
    }

    try {
      await this.executeCommand('memory clear', {
        namespace: this.config.memoryNamespace,
        pattern
      });
    } catch (error) {
      console.warn(`Failed to clear Claude Flow memory: ${pattern}`, error.message);
    }
  }

  // Coordination Methods
  async notifyAgents(message, data = {}) {
    if (!this.isInitialized) {
      this.emit('agent-notification', { message, data });
      return;
    }

    try {
      await this.executeCommand('hooks notify', {
        message,
        data: JSON.stringify(data),
        sessionId: this.config.sessionId
      });
    } catch (error) {
      console.warn('Failed to notify agents:', error.message);
    }
  }

  async reportProgress(task, progress, details = {}) {
    if (!this.isInitialized) {
      this.emit('progress-update', { task, progress, details });
      return;
    }

    try {
      await this.executeCommand('hooks progress', {
        task,
        progress,
        details: JSON.stringify(details),
        sessionId: this.config.sessionId
      });
    } catch (error) {
      console.warn('Failed to report progress:', error.message);
    }
  }

  async logActivity(activity, metadata = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      activity,
      metadata,
      sessionId: this.config.sessionId
    };

    // Store in memory for persistence
    await this.storeInMemory(`activity_${Date.now()}`, logEntry);

    if (!this.isInitialized) {
      console.log('Activity:', activity, metadata);
      return;
    }

    try {
      await this.executeCommand('hooks log', {
        activity,
        metadata: JSON.stringify(metadata),
        sessionId: this.config.sessionId
      });
    } catch (error) {
      console.warn('Failed to log activity:', error.message);
    }
  }

  // Session Management
  async saveSession() {
    if (!this.isInitialized) {
      return;
    }

    try {
      await this.executeCommand('hooks session-save', {
        sessionId: this.config.sessionId,
        data: JSON.stringify({
          memoryCache: Array.from(this.memoryCache.entries()),
          hooks: Array.from(this.hooks.keys()),
          timestamp: new Date().toISOString()
        })
      });
    } catch (error) {
      console.warn('Failed to save session:', error.message);
    }
  }

  async restoreSession(sessionId = null) {
    const targetSessionId = sessionId || this.config.sessionId;

    if (!this.isInitialized) {
      return;
    }

    try {
      const result = await this.executeCommand('hooks session-restore', {
        sessionId: targetSessionId
      });

      if (result && result.data) {
        const sessionData = JSON.parse(result.data);

        // Restore memory cache
        if (sessionData.memoryCache) {
          this.memoryCache.clear();
          for (const [key, value] of sessionData.memoryCache) {
            this.memoryCache.set(key, value);
          }
        }

        this.emit('session-restored', sessionData);
        return sessionData;
      }
    } catch (error) {
      console.warn('Failed to restore session:', error.message);
    }

    return null;
  }

  async endSession() {
    try {
      // Save session before ending
      await this.saveSession();

      if (this.isInitialized) {
        await this.executeCommand('hooks session-end', {
          sessionId: this.config.sessionId,
          exportMetrics: true
        });
      }

      this.emit('session-ended');
    } catch (error) {
      console.warn('Failed to end session properly:', error.message);
    }
  }

  // Utility Methods
  async getSessionMetrics() {
    if (!this.isInitialized) {
      return {
        memoryEntries: this.memoryCache.size,
        hooks: this.hooks.size,
        sessionId: this.config.sessionId
      };
    }

    try {
      const result = await this.executeCommand('hooks metrics', {
        sessionId: this.config.sessionId
      });

      return result || {};
    } catch (error) {
      console.warn('Failed to get session metrics:', error.message);
      return {};
    }
  }

  async getSwarmStatus() {
    if (!this.isInitialized) {
      return { status: 'disconnected' };
    }

    try {
      const result = await this.executeCommand('swarm status');
      return result || { status: 'unknown' };
    } catch (error) {
      console.warn('Failed to get swarm status:', error.message);
      return { status: 'error', error: error.message };
    }
  }

  // Integration with MCP Tools
  async executeMCPTool(toolName, params = {}) {
    if (!this.isInitialized) {
      throw new Error('Claude Flow not initialized');
    }

    try {
      const result = await this.executeCommand(`mcp ${toolName}`, params);
      return result;
    } catch (error) {
      throw new Error(`MCP tool execution failed: ${toolName} - ${error.message}`);
    }
  }

  // Configuration
  updateConfig(newConfig) {
    Object.assign(this.config, newConfig);
    this.emit('config-updated', this.config);
  }

  getConfig() {
    return { ...this.config };
  }

  getStatus() {
    return {
      isInitialized: this.isInitialized,
      sessionId: this.config.sessionId,
      memoryEntries: this.memoryCache.size,
      registeredHooks: Array.from(this.hooks.keys()),
      config: this.config
    };
  }

  // Cleanup
  async cleanup() {
    try {
      await this.endSession();
      this.memoryCache.clear();
      this.hooks.clear();
      this.removeAllListeners();
    } catch (error) {
      console.warn('Cleanup failed:', error.message);
    }
  }
}