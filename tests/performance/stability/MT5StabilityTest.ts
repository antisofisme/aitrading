import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5ConnectionPool } from '../infrastructure/MT5TestHelper';

export interface StabilityTestConfig extends TestConfig {
  testScenarios: StabilityScenario[];
  connectionResilience: {
    forcedDisconnections: number;
    reconnectionTimeout: number;
    maxReconnectionAttempts: number;
    heartbeatInterval: number;
  };
  networkSimulation: {
    enabled: boolean;
    latencyVariation: number; // Additional latency variation in ms
    packetLoss: number; // Packet loss percentage (0-100)
    networkJitter: number; // Network jitter in ms
  };
  longRunningTest: {
    enabled: boolean;
    duration: number; // Extended test duration in ms
    degradationThreshold: number; // Performance degradation threshold %
  };
}

export interface StabilityScenario {
  name: string;
  description: string;
  duration: number;
  operations: StabilityOperation[];
  expectedStability: number; // Expected uptime percentage
  errorTolerance: number; // Acceptable error percentage
}

export interface StabilityOperation {
  type: 'order' | 'tick' | 'account' | 'disconnect' | 'reconnect' | 'stress';
  frequency: number; // Operations per minute
  parameters?: any;
  criticalOperation: boolean; // Whether failure is critical
}

export interface StabilityMetrics {
  uptime: number; // Percentage
  availability: number; // Percentage
  connectionDrops: number;
  reconnectionTime: number; // Average in ms
  errorRecoveryTime: number; // Average in ms
  operationSuccess: Map<string, number>; // Success rates by operation type
  mtbf: number; // Mean time between failures in minutes
  mttr: number; // Mean time to recovery in minutes
}

export class MT5StabilityTest extends PerformanceTestBase {
  private connectionPool: MT5ConnectionPool;
  private testConfig: StabilityTestConfig;
  private stabilityMetrics: StabilityMetrics;
  private connectionHistory: Array<{ timestamp: number; event: string; duration?: number }> = [];
  private operationHistory: Array<{ timestamp: number; operation: string; success: boolean; latency: number }> = [];
  private disconnectionCount: number = 0;
  private testStartTime: number = 0;

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<StabilityTestConfig> = {}
  ) {
    const config: StabilityTestConfig = {
      duration: 3600000, // 1 hour default
      concurrency: 10,
      warmupTime: 60000,
      cooldownTime: 30000,
      sampleInterval: 5000,
      maxMemoryUsage: 1024,
      maxLatency: 2000,
      minThroughput: 100,
      testScenarios: [],
      connectionResilience: {
        forcedDisconnections: 5,
        reconnectionTimeout: 30000,
        maxReconnectionAttempts: 3,
        heartbeatInterval: 10000
      },
      networkSimulation: {
        enabled: true,
        latencyVariation: 50,
        packetLoss: 1,
        networkJitter: 20
      },
      longRunningTest: {
        enabled: true,
        duration: 7200000, // 2 hours
        degradationThreshold: 20 // 20% degradation threshold
      },
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.connectionPool = new MT5ConnectionPool(mt5Config);

    this.initializeStabilityMetrics();
    this.initializeStabilityScenarios();
  }

  private initializeStabilityMetrics(): void {
    this.stabilityMetrics = {
      uptime: 0,
      availability: 0,
      connectionDrops: 0,
      reconnectionTime: 0,
      errorRecoveryTime: 0,
      operationSuccess: new Map(),
      mtbf: 0,
      mttr: 0
    };
  }

  private initializeStabilityScenarios(): void {
    this.testConfig.testScenarios = [
      {
        name: 'NormalOperations',
        description: 'Normal trading operations under stable conditions',
        duration: 600000, // 10 minutes
        expectedStability: 99.5,
        errorTolerance: 1,
        operations: [
          {
            type: 'tick',
            frequency: 60, // 1 per second
            criticalOperation: true
          },
          {
            type: 'account',
            frequency: 12, // Every 5 seconds
            criticalOperation: true
          },
          {
            type: 'order',
            frequency: 6, // Every 10 seconds
            criticalOperation: true
          }
        ]
      },
      {
        name: 'ConnectionResilience',
        description: 'Test connection recovery after forced disconnections',
        duration: 900000, // 15 minutes
        expectedStability: 95,
        errorTolerance: 5,
        operations: [
          {
            type: 'disconnect',
            frequency: 2, // Every 30 seconds
            criticalOperation: false
          },
          {
            type: 'reconnect',
            frequency: 2, // Every 30 seconds
            criticalOperation: true
          },
          {
            type: 'tick',
            frequency: 30, // Every 2 seconds
            criticalOperation: true
          }
        ]
      },
      {
        name: 'StressStability',
        description: 'High load stability testing',
        duration: 1200000, // 20 minutes
        expectedStability: 98,
        errorTolerance: 2,
        operations: [
          {
            type: 'stress',
            frequency: 300, // High frequency operations
            criticalOperation: false
          },
          {
            type: 'tick',
            frequency: 120, // 2 per second
            criticalOperation: true
          },
          {
            type: 'order',
            frequency: 30, // Every 2 seconds
            criticalOperation: true
          }
        ]
      },
      {
        name: 'NetworkAdversity',
        description: 'Stability under adverse network conditions',
        duration: 800000, // ~13 minutes
        expectedStability: 92,
        errorTolerance: 8,
        operations: [
          {
            type: 'tick',
            frequency: 60,
            criticalOperation: true
          },
          {
            type: 'account',
            frequency: 20,
            criticalOperation: true
          }
        ]
      }
    ];
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 stability test warmup...');

    // Initialize connection pool
    const baselineConnections = 3;
    await this.connectionPool.createMultipleConnections(baselineConnections);

    // Test basic operations
    const connections = this.connectionPool.getAllConnections();
    for (const conn of connections) {
      await conn.getAccountInfo();
      await conn.getTickData('EURUSD');
    }

    // Start connection monitoring
    this.startConnectionMonitoring();

    this.emit('message', 'Stability test warmup completed');
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting stability test execution...');
    this.testStartTime = performance.now();

    // Execute stability scenarios sequentially
    for (const scenario of this.testConfig.testScenarios) {
      await this.executeStabilityScenario(scenario);

      // Brief recovery period between scenarios
      await new Promise(resolve => setTimeout(resolve, 30000));
    }

    // Extended long-running test if enabled
    if (this.testConfig.longRunningTest.enabled) {
      await this.executeLongRunningTest();
    }

    this.emit('message', 'Stability test execution completed');
  }

  private async startConnectionMonitoring(): Promise<void> {
    const monitorInterval = setInterval(async () => {
      if (!this.isRunning) {
        clearInterval(monitorInterval);
        return;
      }

      await this.performHeartbeatCheck();
    }, this.testConfig.connectionResilience.heartbeatInterval);
  }

  private async performHeartbeatCheck(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();

    for (const [index, conn] of connections.entries()) {
      try {
        if (!conn.isConnectionActive()) {
          this.recordConnectionEvent('heartbeat_failure', index);
          await this.attemptReconnection(conn, index);
        } else {
          // Quick heartbeat operation
          await conn.getAccountInfo();
        }
      } catch (error) {
        this.recordConnectionEvent('heartbeat_error', index);
        this.recordError(error);
      }
    }
  }

  private async executeStabilityScenario(scenario: StabilityScenario): Promise<void> {
    this.emit('message', `Executing stability scenario: ${scenario.name}`);

    const scenarioStartTime = performance.now();
    const scenarioEndTime = scenarioStartTime + scenario.duration;

    // Track scenario-specific metrics
    const scenarioMetrics = {
      operations: 0,
      successes: 0,
      errors: 0,
      connectionIssues: 0
    };

    while (performance.now() < scenarioEndTime && this.isRunning) {
      for (const operation of scenario.operations) {
        if (performance.now() >= scenarioEndTime) break;

        await this.executeStabilityOperation(operation, scenarioMetrics);

        // Wait based on operation frequency
        const delayMs = (60 * 1000) / operation.frequency; // Convert frequency to delay
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
    }

    const scenarioDuration = performance.now() - scenarioStartTime;
    const scenarioStability = (scenarioMetrics.successes / Math.max(1, scenarioMetrics.operations)) * 100;

    this.emit('scenarioCompleted', {
      name: scenario.name,
      duration: scenarioDuration.toFixed(2),
      operations: scenarioMetrics.operations,
      stability: scenarioStability.toFixed(2),
      expectedStability: scenario.expectedStability,
      meetsTarget: scenarioStability >= scenario.expectedStability
    });
  }

  private async executeStabilityOperation(
    operation: StabilityOperation,
    scenarioMetrics: any
  ): Promise<void> {
    scenarioMetrics.operations++;
    const operationStartTime = performance.now();

    try {
      switch (operation.type) {
        case 'tick':
          await this.executeTickOperation();
          break;
        case 'account':
          await this.executeAccountOperation();
          break;
        case 'order':
          await this.executeOrderOperation();
          break;
        case 'disconnect':
          await this.executeForcedDisconnection();
          break;
        case 'reconnect':
          await this.executeReconnection();
          break;
        case 'stress':
          await this.executeStressOperation();
          break;
      }

      scenarioMetrics.successes++;

      const latency = performance.now() - operationStartTime;
      this.recordOperationHistory(operation.type, true, latency);

    } catch (error) {
      scenarioMetrics.errors++;

      const latency = performance.now() - operationStartTime;
      this.recordOperationHistory(operation.type, false, latency);

      if (operation.criticalOperation) {
        scenarioMetrics.connectionIssues++;
      }

      this.recordError(error);
    }
  }

  private async executeTickOperation(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) throw new Error('No active connections');

    const conn = connections[0];
    const { success } = await conn.getTickData('EURUSD');

    if (!success) {
      throw new Error('Tick operation failed');
    }
  }

  private async executeAccountOperation(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) throw new Error('No active connections');

    const conn = connections[0];
    await conn.getAccountInfo();
  }

  private async executeOrderOperation(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) throw new Error('No active connections');

    const conn = connections[0];
    const { success } = await conn.executeOrder({
      symbol: 'EURUSD',
      volume: 0.01,
      type: 'BUY',
      comment: 'StabilityTest'
    });

    if (!success) {
      throw new Error('Order operation failed');
    }
  }

  private async executeForcedDisconnection(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) return;

    const conn = connections[0];
    const disconnectStartTime = performance.now();

    await conn.closeConnection();
    this.disconnectionCount++;

    this.recordConnectionEvent('forced_disconnect', 0, performance.now() - disconnectStartTime);
  }

  private async executeReconnection(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) return;

    const conn = connections[0];
    if (conn.isConnectionActive()) return; // Already connected

    await this.attemptReconnection(conn, 0);
  }

  private async executeStressOperation(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) throw new Error('No active connections');

    // Execute multiple operations rapidly
    const promises = connections.map(async (conn, index) => {
      try {
        await Promise.all([
          conn.getTickData('EURUSD'),
          conn.getAccountInfo(),
          conn.getPositions()
        ]);
      } catch (error) {
        // Individual stress operation failures are acceptable
      }
    });

    await Promise.all(promises);
  }

  private async attemptReconnection(connection: MT5TestHelper, connectionIndex: number): Promise<void> {
    const reconnectStartTime = performance.now();
    let attempts = 0;

    while (attempts < this.testConfig.connectionResilience.maxReconnectionAttempts) {
      try {
        const { success } = await connection.initializeConnection();

        if (success) {
          const reconnectionTime = performance.now() - reconnectStartTime;
          this.recordConnectionEvent('reconnect_success', connectionIndex, reconnectionTime);

          // Update reconnection time metric
          this.updateReconnectionMetrics(reconnectionTime);
          return;
        }
      } catch (error) {
        attempts++;
        this.recordError(error);

        if (attempts < this.testConfig.connectionResilience.maxReconnectionAttempts) {
          await new Promise(resolve => setTimeout(resolve, this.testConfig.connectionResilience.reconnectionTimeout));
        }
      }
    }

    // Reconnection failed after all attempts
    const reconnectionTime = performance.now() - reconnectStartTime;
    this.recordConnectionEvent('reconnect_failure', connectionIndex, reconnectionTime);
  }

  private async executeLongRunningTest(): Promise<void> {
    this.emit('message', 'Starting extended long-running stability test...');

    const longRunStartTime = performance.now();
    const longRunEndTime = longRunStartTime + this.testConfig.longRunningTest.duration;

    // Baseline performance measurement
    const baselineMetrics = this.capturePerformanceBaseline();

    while (performance.now() < longRunEndTime && this.isRunning) {
      // Execute mixed operations continuously
      try {
        await this.executeTickOperation();
        await this.executeAccountOperation();

        // Occasional order operations
        if (Math.random() < 0.1) {
          await this.executeOrderOperation();
        }

        // Check for performance degradation every 10 minutes
        if ((performance.now() - longRunStartTime) % 600000 < 5000) {
          await this.checkPerformanceDegradation(baselineMetrics);
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        this.recordError(error);
        await new Promise(resolve => setTimeout(resolve, 5000)); // Recovery delay
      }
    }

    this.emit('message', 'Long-running stability test completed');
  }

  private capturePerformanceBaseline(): any {
    return {
      timestamp: performance.now(),
      latency: this.metrics.latency.avg,
      throughput: this.metrics.throughput.requestsPerSecond,
      errorRate: (this.metrics.errors.count / Math.max(1, this.metrics.throughput.totalRequests)) * 100
    };
  }

  private async checkPerformanceDegradation(baseline: any): Promise<void> {
    const current = this.capturePerformanceBaseline();

    const latencyDegradation = ((current.latency - baseline.latency) / baseline.latency) * 100;
    const throughputDegradation = ((baseline.throughput - current.throughput) / baseline.throughput) * 100;

    if (latencyDegradation > this.testConfig.longRunningTest.degradationThreshold ||
        throughputDegradation > this.testConfig.longRunningTest.degradationThreshold) {

      this.emit('performanceDegradation', {
        latencyDegradation: latencyDegradation.toFixed(2),
        throughputDegradation: throughputDegradation.toFixed(2),
        threshold: this.testConfig.longRunningTest.degradationThreshold
      });
    }
  }

  private recordConnectionEvent(event: string, connectionIndex: number, duration?: number): void {
    this.connectionHistory.push({
      timestamp: Date.now(),
      event: `${event}_${connectionIndex}`,
      duration
    });

    // Update stability metrics
    if (event.includes('disconnect')) {
      this.stabilityMetrics.connectionDrops++;
    }
  }

  private recordOperationHistory(operation: string, success: boolean, latency: number): void {
    this.operationHistory.push({
      timestamp: Date.now(),
      operation,
      success,
      latency
    });

    // Update operation success rates
    const currentSuccess = this.stabilityMetrics.operationSuccess.get(operation) || 0;
    this.stabilityMetrics.operationSuccess.set(operation, success ? currentSuccess + 1 : currentSuccess);
  }

  private updateReconnectionMetrics(reconnectionTime: number): void {
    // Update average reconnection time
    const totalReconnections = this.connectionHistory.filter(e => e.event.includes('reconnect_success')).length;
    const totalTime = this.stabilityMetrics.reconnectionTime * (totalReconnections - 1) + reconnectionTime;
    this.stabilityMetrics.reconnectionTime = totalTime / totalReconnections;
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting stability test cooldown...');

    // Close all connections gracefully
    await this.connectionPool.closeAllConnections();

    // Calculate final stability metrics
    this.calculateFinalStabilityMetrics();

    this.emit('message', 'Stability test cooldown completed');
  }

  private calculateFinalStabilityMetrics(): void {
    const testDuration = performance.now() - this.testStartTime;

    // Calculate uptime
    const downtime = this.connectionHistory
      .filter(e => e.event.includes('disconnect'))
      .reduce((total, event) => total + (event.duration || 0), 0);

    this.stabilityMetrics.uptime = ((testDuration - downtime) / testDuration) * 100;

    // Calculate availability
    const totalOperations = this.operationHistory.length;
    const successfulOperations = this.operationHistory.filter(op => op.success).length;
    this.stabilityMetrics.availability = (successfulOperations / Math.max(1, totalOperations)) * 100;

    // Calculate MTBF and MTTR
    const failures = this.connectionHistory.filter(e => e.event.includes('disconnect')).length;
    if (failures > 0) {
      this.stabilityMetrics.mtbf = (testDuration / 1000 / 60) / failures; // minutes

      const recoveryTimes = this.connectionHistory
        .filter(e => e.event.includes('reconnect_success'))
        .map(e => e.duration || 0);

      if (recoveryTimes.length > 0) {
        this.stabilityMetrics.mttr = recoveryTimes.reduce((a, b) => a + b, 0) / recoveryTimes.length / 1000 / 60; // minutes
      }
    }

    // Store final metrics
    (this.metrics as any).stabilityMetrics = this.stabilityMetrics;
    this.emit('stabilityAnalysis', this.stabilityMetrics);
  }

  public getStabilityMetrics(): StabilityMetrics {
    return { ...this.stabilityMetrics };
  }

  public getConnectionHistory(): Array<{ timestamp: number; event: string; duration?: number }> {
    return [...this.connectionHistory];
  }

  public generateStabilityReport(): string {
    let report = '# MT5 Connection Stability Test Report\n\n';

    const metrics = this.stabilityMetrics;

    report += `## Overall Stability Metrics\n\n`;
    report += `- **Uptime:** ${metrics.uptime.toFixed(2)}%\n`;
    report += `- **Availability:** ${metrics.availability.toFixed(2)}%\n`;
    report += `- **Connection Drops:** ${metrics.connectionDrops}\n`;
    report += `- **Average Reconnection Time:** ${metrics.reconnectionTime.toFixed(2)}ms\n`;
    report += `- **MTBF:** ${metrics.mtbf.toFixed(2)} minutes\n`;
    report += `- **MTTR:** ${metrics.mttr.toFixed(2)} minutes\n\n`;

    // Stability assessment
    if (metrics.uptime >= 99.5) {
      report += '✅ **Excellent stability - Production ready**\n\n';
    } else if (metrics.uptime >= 99.0) {
      report += '✅ **Good stability - Minor optimizations recommended**\n\n';
    } else if (metrics.uptime >= 95.0) {
      report += '⚠️ **Acceptable stability - Improvements needed**\n\n';
    } else {
      report += '❌ **Poor stability - Significant issues require attention**\n\n';
    }

    report += `## Operation Success Rates\n\n`;
    for (const [operation, successCount] of metrics.operationSuccess) {
      const totalOps = this.operationHistory.filter(op => op.operation === operation).length;
      const successRate = (successCount / Math.max(1, totalOps)) * 100;
      report += `- **${operation}:** ${successRate.toFixed(2)}% (${successCount}/${totalOps})\n`;
    }
    report += '\n';

    if (metrics.connectionDrops > 0) {
      report += `## Connection Issues\n\n`;
      report += `- Total disconnections: ${metrics.connectionDrops}\n`;
      report += `- Average recovery time: ${metrics.reconnectionTime.toFixed(2)}ms\n`;

      if (metrics.mttr > 1) {
        report += `⚠️ **High recovery time - investigate connection stability**\n`;
      }
      report += '\n';
    }

    return report;
  }
}