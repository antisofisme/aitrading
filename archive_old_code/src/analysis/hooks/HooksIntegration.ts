/**
 * Hooks Integration - Integrates with Claude Flow hooks for coordination
 * Supports pre/post operations, memory management, and notifications
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import {
  HooksConfig,
  Logger
} from '../types';

const execAsync = promisify(exec);

export class HooksIntegration {
  private config: HooksConfig;
  private logger: Logger;
  private sessionId: string;
  private isInitialized = false;

  constructor(config: HooksConfig, logger: Logger) {
    this.config = config;
    this.logger = logger;
    this.sessionId = this.generateSessionId();
  }

  async initialize(): Promise<void> {
    if (!this.config.enabled) {
      this.logger.debug('Hooks integration disabled');
      return;
    }

    this.logger.info('Initializing Hooks Integration...');

    try {
      // Check if Claude Flow is available
      await execAsync('npx claude-flow@alpha --version');

      // Initialize session
      await this.sessionStart();

      this.isInitialized = true;
      this.logger.info(`Hooks integration initialized with session: ${this.sessionId}`);

    } catch (error) {
      this.logger.warn('Claude Flow hooks not available:', error);
      this.config.enabled = false;
    }
  }

  // Session Management

  async sessionStart(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks session-start --session-id "${this.sessionId}" --type "analysis"`);
      this.logger.debug(`Session started: ${this.sessionId}`);
    } catch (error) {
      this.logger.error('Failed to start session:', error);
    }
  }

  async sessionEnd(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks session-end --session-id "${this.sessionId}" --export-metrics true`);
      this.logger.debug(`Session ended: ${this.sessionId}`);
    } catch (error) {
      this.logger.error('Failed to end session:', error);
    }
  }

  async sessionRestore(): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks session-restore --session-id "${this.sessionId}"`);
      this.logger.debug(`Session restored: ${this.sessionId}`);
    } catch (error) {
      this.logger.error('Failed to restore session:', error);
    }
  }

  // Pre/Post Operation Hooks

  async preTask(taskDescription: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks pre-task --description "${taskDescription}" --session-id "${this.sessionId}"`);
      this.logger.debug(`Pre-task hook: ${taskDescription}`);
    } catch (error) {
      this.logger.error('Failed to execute pre-task hook:', error);
    }
  }

  async postTask(taskId: string, result?: any): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const resultJson = result ? JSON.stringify(result) : '{}';
      await execAsync(`npx claude-flow@alpha hooks post-task --task-id "${taskId}" --result '${resultJson}' --session-id "${this.sessionId}"`);
      this.logger.debug(`Post-task hook: ${taskId}`);
    } catch (error) {
      this.logger.error('Failed to execute post-task hook:', error);
    }
  }

  async preEdit(filePath: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks pre-edit --file "${filePath}" --session-id "${this.sessionId}"`);
      this.logger.debug(`Pre-edit hook: ${filePath}`);
    } catch (error) {
      this.logger.error('Failed to execute pre-edit hook:', error);
    }
  }

  async postEdit(filePath: string, memoryKey?: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const memoryKeyArg = memoryKey ? `--memory-key "${memoryKey}"` : '';
      await execAsync(`npx claude-flow@alpha hooks post-edit --file "${filePath}" ${memoryKeyArg} --session-id "${this.sessionId}"`);
      this.logger.debug(`Post-edit hook: ${filePath}`);
    } catch (error) {
      this.logger.error('Failed to execute post-edit hook:', error);
    }
  }

  async preSearch(query: string, cacheResults = true): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks pre-search --query "${query}" --cache-results ${cacheResults} --session-id "${this.sessionId}"`);
      this.logger.debug(`Pre-search hook: ${query}`);
    } catch (error) {
      this.logger.error('Failed to execute pre-search hook:', error);
    }
  }

  // Memory Management

  async storeMemory(key: string, value: any, ttl?: number): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const valueJson = typeof value === 'string' ? value : JSON.stringify(value);
      const ttlArg = ttl ? `--ttl ${ttl}` : '';
      await execAsync(`npx claude-flow@alpha memory store --key "${key}" --value '${valueJson}' ${ttlArg}`);
      this.logger.debug(`Memory stored: ${key}`);
    } catch (error) {
      this.logger.error(`Failed to store memory for key ${key}:`, error);
    }
  }

  async retrieveMemory(key: string): Promise<any> {
    if (!this.isEnabled()) return null;

    try {
      const { stdout } = await execAsync(`npx claude-flow@alpha memory retrieve --key "${key}"`);
      const result = JSON.parse(stdout);

      if (result.success && result.value) {
        try {
          return JSON.parse(result.value);
        } catch {
          return result.value; // Return as string if not JSON
        }
      }

      return null;
    } catch (error) {
      this.logger.error(`Failed to retrieve memory for key ${key}:`, error);
      return null;
    }
  }

  async deleteMemory(key: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha memory delete --key "${key}"`);
      this.logger.debug(`Memory deleted: ${key}`);
    } catch (error) {
      this.logger.error(`Failed to delete memory for key ${key}:`, error);
    }
  }

  async searchMemory(pattern: string, limit = 10): Promise<any[]> {
    if (!this.isEnabled()) return [];

    try {
      const { stdout } = await execAsync(`npx claude-flow@alpha memory search --pattern "${pattern}" --limit ${limit}`);
      const result = JSON.parse(stdout);

      if (result.success && result.results) {
        return result.results;
      }

      return [];
    } catch (error) {
      this.logger.error(`Failed to search memory for pattern ${pattern}:`, error);
      return [];
    }
  }

  // Notifications

  async notify(message: string, level = 'info'): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      await execAsync(`npx claude-flow@alpha hooks notify --message "${message}" --level ${level} --session-id "${this.sessionId}"`);
      this.logger.debug(`Notification sent: ${message}`);
    } catch (error) {
      this.logger.error('Failed to send notification:', error);
    }
  }

  async notifyProgress(current: number, total: number, message?: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const messageArg = message ? `--message "${message}"` : '';
      await execAsync(`npx claude-flow@alpha hooks notify-progress --current ${current} --total ${total} ${messageArg} --session-id "${this.sessionId}"`);
      this.logger.debug(`Progress notification: ${current}/${total}`);
    } catch (error) {
      this.logger.error('Failed to send progress notification:', error);
    }
  }

  async notifyError(error: Error, context?: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const contextArg = context ? `--context "${context}"` : '';
      await execAsync(`npx claude-flow@alpha hooks notify-error --error "${error.message}" ${contextArg} --session-id "${this.sessionId}"`);
      this.logger.debug(`Error notification sent: ${error.message}`);
    } catch (hookError) {
      this.logger.error('Failed to send error notification:', hookError);
    }
  }

  // Analysis-specific hooks

  async notifyAnalysisStart(filePaths: string[]): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const fileCount = filePaths.length;
      await this.notify(`Starting analysis of ${fileCount} files`, 'info');
      await this.storeMemory('analysis/current-session', {
        sessionId: this.sessionId,
        startTime: new Date().toISOString(),
        fileCount,
        status: 'started'
      });
    } catch (error) {
      this.logger.error('Failed to notify analysis start:', error);
    }
  }

  async notifyAnalysisProgress(processed: number, total: number, currentFile?: string): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const message = currentFile ? `Processing: ${currentFile}` : undefined;
      await this.notifyProgress(processed, total, message);

      // Update session memory
      const sessionData = await this.retrieveMemory('analysis/current-session') || {};
      sessionData.processed = processed;
      sessionData.lastFile = currentFile;
      sessionData.lastUpdate = new Date().toISOString();
      await this.storeMemory('analysis/current-session', sessionData);

    } catch (error) {
      this.logger.error('Failed to notify analysis progress:', error);
    }
  }

  async notifyAnalysisComplete(result: any): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const summary = {
        elementsFound: result.graph?.elements?.size || 0,
        relationshipsFound: result.graph?.relationships?.size || 0,
        diagramsGenerated: result.diagrams?.length || 0,
        recommendationsCount: result.recommendations?.length || 0
      };

      await this.notify(`Analysis complete: ${summary.elementsFound} elements, ${summary.relationshipsFound} relationships`, 'success');

      // Store final session data
      const sessionData = await this.retrieveMemory('analysis/current-session') || {};
      sessionData.status = 'completed';
      sessionData.endTime = new Date().toISOString();
      sessionData.summary = summary;
      await this.storeMemory('analysis/current-session', sessionData);
      await this.storeMemory('analysis/latest-result-summary', summary);

    } catch (error) {
      this.logger.error('Failed to notify analysis complete:', error);
    }
  }

  async notifyFileAnalyzed(filePath: string, elementsFound: number): Promise<void> {
    if (!this.isEnabled() || !this.config.incremental) return;

    try {
      if (elementsFound >= this.config.notificationThreshold) {
        await this.notify(`Analyzed ${filePath}: ${elementsFound} elements found`, 'info');
      }

      // Store file analysis data
      await this.storeMemory(`analysis/files/${filePath}`, {
        lastAnalyzed: new Date().toISOString(),
        elementsFound,
        sessionId: this.sessionId
      });

    } catch (error) {
      this.logger.error('Failed to notify file analyzed:', error);
    }
  }

  // Pattern Training

  async trainPattern(patternType: string, data: any): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const dataJson = JSON.stringify(data);
      await execAsync(`npx claude-flow@alpha neural train --pattern-type "${patternType}" --data '${dataJson}' --session-id "${this.sessionId}"`);
      this.logger.debug(`Pattern training: ${patternType}`);
    } catch (error) {
      this.logger.error('Failed to train pattern:', error);
    }
  }

  async predictPattern(patternType: string, input: any): Promise<any> {
    if (!this.isEnabled()) return null;

    try {
      const inputJson = JSON.stringify(input);
      const { stdout } = await execAsync(`npx claude-flow@alpha neural predict --pattern-type "${patternType}" --input '${inputJson}'`);
      const result = JSON.parse(stdout);

      return result.success ? result.prediction : null;
    } catch (error) {
      this.logger.error('Failed to predict pattern:', error);
      return null;
    }
  }

  // Performance Tracking

  async trackPerformance(operation: string, duration: number, metadata?: any): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      const metadataJson = metadata ? JSON.stringify(metadata) : '{}';
      await execAsync(`npx claude-flow@alpha hooks track-performance --operation "${operation}" --duration ${duration} --metadata '${metadataJson}' --session-id "${this.sessionId}"`);
      this.logger.debug(`Performance tracked: ${operation} (${duration}ms)`);
    } catch (error) {
      this.logger.error('Failed to track performance:', error);
    }
  }

  async getPerformanceMetrics(): Promise<any> {
    if (!this.isEnabled()) return null;

    try {
      const { stdout } = await execAsync(`npx claude-flow@alpha hooks get-performance --session-id "${this.sessionId}"`);
      const result = JSON.parse(stdout);

      return result.success ? result.metrics : null;
    } catch (error) {
      this.logger.error('Failed to get performance metrics:', error);
      return null;
    }
  }

  // Utilities

  async dispose(): Promise<void> {
    if (this.isInitialized) {
      await this.sessionEnd();
    }
    this.logger.info('Hooks integration disposed');
  }

  getSessionId(): string {
    return this.sessionId;
  }

  isEnabled(): boolean {
    return this.config.enabled && this.isInitialized;
  }

  getConfig(): HooksConfig {
    return { ...this.config };
  }

  // Private methods

  private generateSessionId(): string {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `analysis-${timestamp}-${random}`;
  }

  // Event handlers for incremental analysis

  async onFileChanged(filePath: string, changeType: 'add' | 'change' | 'unlink'): Promise<void> {
    if (!this.isEnabled() || !this.config.incremental) return;

    try {
      await this.preEdit(filePath);
      await this.notify(`File ${changeType}: ${filePath}`, 'info');

      // Invalidate related cache entries
      await this.deleteMemory(`analysis/files/${filePath}`);

      // Store change event
      await this.storeMemory(`analysis/changes/${Date.now()}`, {
        filePath,
        changeType,
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId
      }, 3600); // 1 hour TTL

    } catch (error) {
      this.logger.error('Failed to handle file change:', error);
    }
  }

  async onElementsFound(filePath: string, elements: any[]): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      // Store elements for later use
      await this.storeMemory(`analysis/elements/${filePath}`, {
        elements: elements.map(e => ({
          id: e.id,
          name: e.name,
          type: e.type,
          complexity: e.metadata?.complexity
        })),
        timestamp: new Date().toISOString()
      });

      // Train patterns if enough data
      if (elements.length > 5) {
        await this.trainPattern('code-structure', {
          filePath,
          elementCount: elements.length,
          types: elements.map(e => e.type)
        });
      }

    } catch (error) {
      this.logger.error('Failed to handle elements found:', error);
    }
  }

  async onRelationshipsFound(filePath: string, relationships: any[]): Promise<void> {
    if (!this.isEnabled()) return;

    try {
      // Store relationships for later use
      await this.storeMemory(`analysis/relationships/${filePath}`, {
        relationships: relationships.map(r => ({
          id: r.id,
          type: r.type,
          confidence: r.metadata?.confidence
        })),
        timestamp: new Date().toISOString()
      });

      // Train relationship patterns
      if (relationships.length > 3) {
        await this.trainPattern('relationship-patterns', {
          filePath,
          relationshipCount: relationships.length,
          types: relationships.map(r => r.type)
        });
      }

    } catch (error) {
      this.logger.error('Failed to handle relationships found:', error);
    }
  }
}