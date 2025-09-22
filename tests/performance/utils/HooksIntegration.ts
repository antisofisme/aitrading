import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface HookData {
  sessionId: string;
  testType: string;
  metrics: any;
  timestamp: number;
  phase: 'start' | 'progress' | 'complete' | 'error';
}

export interface MemoryStorage {
  key: string;
  value: any;
  namespace: string;
  ttl?: number;
  operation: 'set' | 'get' | 'increment' | 'append';
}

export class HooksIntegration {
  private sessionId: string;
  private testType: string;
  private isInitialized: boolean = false;

  constructor(testType: string, sessionId?: string) {
    this.testType = testType;
    this.sessionId = sessionId || `perf_${testType}_${Date.now()}`;
  }

  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      await this.runHook('pre-task', {
        description: `Performance testing: ${this.testType}`,
        sessionId: this.sessionId,
        testType: this.testType
      });

      await this.sessionRestore();
      this.isInitialized = true;

      console.log(`Hooks integration initialized for ${this.testType} (Session: ${this.sessionId})`);
    } catch (error) {
      console.warn('Failed to initialize hooks integration:', error);
    }
  }

  public async storeMetric(key: string, value: any, namespace: string = 'performance'): Promise<void> {
    try {
      const memoryKey = `${namespace}/${this.testType}/${key}`;
      await this.storeInMemory({
        key: memoryKey,
        value,
        namespace,
        operation: 'set'
      });
    } catch (error) {
      console.warn(`Failed to store metric ${key}:`, error);
    }
  }

  public async incrementCounter(key: string, value: number = 1, namespace: string = 'performance'): Promise<void> {
    try {
      const memoryKey = `${namespace}/${this.testType}/${key}`;
      await this.storeInMemory({
        key: memoryKey,
        value,
        namespace,
        operation: 'increment'
      });
    } catch (error) {
      console.warn(`Failed to increment counter ${key}:`, error);
    }
  }

  public async appendToLog(key: string, logEntry: any, namespace: string = 'performance'): Promise<void> {
    try {
      const memoryKey = `${namespace}/${this.testType}/${key}`;
      const logData = {
        timestamp: Date.now(),
        sessionId: this.sessionId,
        ...logEntry
      };

      await this.storeInMemory({
        key: memoryKey,
        value: JSON.stringify(logData),
        namespace,
        operation: 'append'
      });
    } catch (error) {
      console.warn(`Failed to append to log ${key}:`, error);
    }
  }

  public async storeTestResults(results: any): Promise<void> {
    try {
      const resultsWithMeta = {
        sessionId: this.sessionId,
        testType: this.testType,
        timestamp: Date.now(),
        results
      };

      await this.storeMetric('test_results', resultsWithMeta, 'performance/results');

      // Also store in team memory for easy access
      await this.storeInMemory({
        key: `team/performance/${this.testType}/latest`,
        value: resultsWithMeta,
        namespace: 'team',
        operation: 'set'
      });

      console.log(`Test results stored for ${this.testType}`);
    } catch (error) {
      console.warn('Failed to store test results:', error);
    }
  }

  public async notifyProgress(message: string, progress?: number): Promise<void> {
    try {
      await this.notify({
        message: `${this.testType}: ${message}`,
        progress,
        sessionId: this.sessionId,
        timestamp: Date.now()
      });
    } catch (error) {
      console.warn('Failed to notify progress:', error);
    }
  }

  public async notifyError(error: string | Error, context?: any): Promise<void> {
    try {
      const errorMessage = error instanceof Error ? error.message : error;
      await this.notify({
        message: `ERROR in ${this.testType}: ${errorMessage}`,
        error: true,
        context,
        sessionId: this.sessionId,
        timestamp: Date.now()
      });

      // Store error for analysis
      await this.appendToLog('errors', {
        error: errorMessage,
        context,
        stack: error instanceof Error ? error.stack : undefined
      }, 'performance/errors');

    } catch (hookError) {
      console.warn('Failed to notify error:', hookError);
    }
  }

  public async reportMetrics(metrics: any): Promise<void> {
    try {
      // Store detailed metrics
      await this.storeMetric('current_metrics', metrics);

      // Update real-time dashboard data
      await this.postEdit('performance/dashboard', {
        [this.testType]: {
          lastUpdate: Date.now(),
          sessionId: this.sessionId,
          metrics
        }
      });

      console.log(`Metrics reported for ${this.testType}`);
    } catch (error) {
      console.warn('Failed to report metrics:', error);
    }
  }

  public async shareResults(results: any, description: string): Promise<void> {
    try {
      const shareData = {
        testType: this.testType,
        sessionId: this.sessionId,
        description,
        results,
        timestamp: Date.now(),
        shareId: `share_${this.sessionId}_${Date.now()}`
      };

      // Store in shared memory for team access
      await this.storeInMemory({
        key: `shared/performance/${shareData.shareId}`,
        value: shareData,
        namespace: 'shared',
        operation: 'set'
      });

      // Notify team of new shared results
      await this.notify({
        message: `Performance test results shared: ${this.testType} - ${description}`,
        shareId: shareData.shareId,
        sessionId: this.sessionId
      });

      console.log(`Results shared: ${shareData.shareId}`);
    } catch (error) {
      console.warn('Failed to share results:', error);
    }
  }

  public async finalize(summary: any): Promise<void> {
    try {
      // Store final summary
      await this.storeTestResults(summary);

      // Post-task hook
      await this.runHook('post-task', {
        taskId: this.sessionId,
        summary,
        completedAt: Date.now()
      });

      // Session end
      await this.sessionEnd(true);

      console.log(`Performance test finalized: ${this.testType}`);
    } catch (error) {
      console.warn('Failed to finalize test:', error);
    }
  }

  // Private hook methods
  private async runHook(hook: string, data: any): Promise<void> {
    try {
      const dataStr = JSON.stringify(data).replace(/'/g, "\\'");
      await execAsync(`npx claude-flow@alpha hooks ${hook} --data '${dataStr}'`);
    } catch (error) {
      throw new Error(`Hook ${hook} failed: ${error.message}`);
    }
  }

  private async sessionRestore(): Promise<void> {
    try {
      await execAsync(`npx claude-flow@alpha hooks session-restore --session-id "${this.sessionId}"`);
    } catch (error) {
      // Session restore failure is not critical
      console.warn('Session restore failed:', error);
    }
  }

  private async sessionEnd(exportMetrics: boolean = true): Promise<void> {
    try {
      const command = exportMetrics
        ? `npx claude-flow@alpha hooks session-end --export-metrics true --session-id "${this.sessionId}"`
        : `npx claude-flow@alpha hooks session-end --session-id "${this.sessionId}"`;

      await execAsync(command);
    } catch (error) {
      console.warn('Session end failed:', error);
    }
  }

  private async storeInMemory(storage: MemoryStorage): Promise<void> {
    try {
      const value = typeof storage.value === 'object'
        ? JSON.stringify(storage.value)
        : String(storage.value);

      let command = `npx claude-flow@alpha hooks post-edit --memory-key "${storage.key}" --value '${value.replace(/'/g, "\\'")}'`;

      if (storage.operation !== 'set') {
        command += ` --operation "${storage.operation}"`;
      }

      if (storage.namespace) {
        command += ` --namespace "${storage.namespace}"`;
      }

      await execAsync(command);
    } catch (error) {
      throw new Error(`Memory storage failed: ${error.message}`);
    }
  }

  private async postEdit(key: string, data: any): Promise<void> {
    try {
      const dataStr = JSON.stringify(data).replace(/'/g, "\\'");
      await execAsync(`npx claude-flow@alpha hooks post-edit --memory-key "${key}" --value '${dataStr}'`);
    } catch (error) {
      throw new Error(`Post-edit failed: ${error.message}`);
    }
  }

  private async notify(notification: any): Promise<void> {
    try {
      const message = typeof notification === 'string' ? notification : notification.message;
      const messageStr = message.replace(/'/g, "\\'");
      await execAsync(`npx claude-flow@alpha hooks notify --message '${messageStr}'`);
    } catch (error) {
      throw new Error(`Notification failed: ${error.message}`);
    }
  }

  // Utility methods for team coordination
  public async getSharedResults(shareId?: string): Promise<any> {
    try {
      const key = shareId
        ? `shared/performance/${shareId}`
        : `shared/performance/${this.testType}/latest`;

      // Note: In a real implementation, you'd need a hook to retrieve data
      // For now, we'll return a placeholder
      return { message: 'Shared results retrieval not implemented in mock' };
    } catch (error) {
      console.warn('Failed to get shared results:', error);
      return null;
    }
  }

  public async getTeamMetrics(): Promise<any> {
    try {
      // Retrieve team performance metrics
      // In real implementation, this would use a get-memory hook
      return { message: 'Team metrics retrieval not implemented in mock' };
    } catch (error) {
      console.warn('Failed to get team metrics:', error);
      return null;
    }
  }

  public getSessionId(): string {
    return this.sessionId;
  }

  public getTestType(): string {
    return this.testType;
  }

  public isReady(): boolean {
    return this.isInitialized;
  }
}

// Utility function to create hooks integration for different test types
export function createHooksIntegration(testType: string, sessionId?: string): HooksIntegration {
  return new HooksIntegration(testType, sessionId);
}

// Performance test event types for coordination
export enum PerformanceTestEvent {
  STARTED = 'test_started',
  PROGRESS = 'test_progress',
  COMPLETED = 'test_completed',
  ERROR = 'test_error',
  METRICS_UPDATE = 'metrics_update',
  THRESHOLD_EXCEEDED = 'threshold_exceeded',
  MEMORY_LEAK = 'memory_leak_detected',
  CONNECTION_DROP = 'connection_dropped',
  PERFORMANCE_DEGRADATION = 'performance_degradation'
}

// Helper class for coordinating multiple performance tests
export class PerformanceTestCoordinator {
  private hooksIntegrations: Map<string, HooksIntegration> = new Map();
  private coordinationSessionId: string;

  constructor() {
    this.coordinationSessionId = `coord_${Date.now()}`;
  }

  public async initializeCoordination(): Promise<void> {
    const coordination = createHooksIntegration('coordinator', this.coordinationSessionId);
    await coordination.initialize();
    this.hooksIntegrations.set('coordinator', coordination);

    await coordination.notifyProgress('Performance test coordination initialized');
  }

  public async registerTest(testType: string, sessionId?: string): Promise<HooksIntegration> {
    const hooks = createHooksIntegration(testType, sessionId);
    await hooks.initialize();
    this.hooksIntegrations.set(testType, hooks);

    const coordinator = this.hooksIntegrations.get('coordinator');
    if (coordinator) {
      await coordinator.notifyProgress(`Test registered: ${testType}`);
    }

    return hooks;
  }

  public async coordinateResults(results: Map<string, any>): Promise<void> {
    const coordinator = this.hooksIntegrations.get('coordinator');
    if (!coordinator) return;

    const aggregatedResults = {
      coordinationSession: this.coordinationSessionId,
      timestamp: Date.now(),
      tests: Object.fromEntries(results)
    };

    await coordinator.storeTestResults(aggregatedResults);
    await coordinator.shareResults(aggregatedResults, 'Coordinated performance test results');
  }

  public async finalizeCoordination(summary: any): Promise<void> {
    const coordinator = this.hooksIntegrations.get('coordinator');
    if (!coordinator) return;

    await coordinator.finalize(summary);

    // Finalize all test integrations
    for (const [testType, hooks] of this.hooksIntegrations) {
      if (testType !== 'coordinator') {
        await hooks.finalize({ coordinatedBy: this.coordinationSessionId });
      }
    }
  }

  public getCoordinationSessionId(): string {
    return this.coordinationSessionId;
  }
}