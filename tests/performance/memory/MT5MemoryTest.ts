import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5ConnectionPool } from '../infrastructure/MT5TestHelper';

export interface MemoryTestConfig extends TestConfig {
  memoryMonitoringInterval: number;
  leakDetectionThreshold: number; // MB per minute
  maxHeapGrowth: number; // Maximum allowed heap growth in MB
  gcForceInterval: number; // Force GC every N milliseconds
  memoryStressPatterns: ('connections' | 'orders' | 'data' | 'mixed')[];
  dataRetentionTest: {
    enabled: boolean;
    retainDuration: number; // How long to retain data in memory
    dataPoints: number; // Number of data points to accumulate
  };
}

export interface MemorySnapshot {
  timestamp: number;
  heapUsed: number;
  heapTotal: number;
  external: number;
  rss: number;
  arrayBuffers: number;
  activeConnections: number;
  totalOperations: number;
}

export class MT5MemoryTest extends PerformanceTestBase {
  private connectionPool: MT5ConnectionPool;
  private testConfig: MemoryTestConfig;
  private memorySnapshots: MemorySnapshot[] = [];
  private memoryBaseline: MemorySnapshot;
  private leakDetected: boolean = false;
  private dataRetentionBuffer: Array<any> = [];
  private operationCount: number = 0;

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<MemoryTestConfig> = {}
  ) {
    const config: MemoryTestConfig = {
      duration: 900000, // 15 minutes
      concurrency: 20,
      warmupTime: 60000, // 1 minute warmup
      cooldownTime: 30000,
      sampleInterval: 1000,
      maxMemoryUsage: 1024, // 1GB
      maxLatency: 1000,
      minThroughput: 50,
      memoryMonitoringInterval: 5000, // 5 seconds
      leakDetectionThreshold: 10, // 10MB per minute growth
      maxHeapGrowth: 500, // 500MB max heap growth
      gcForceInterval: 60000, // Force GC every minute
      memoryStressPatterns: ['connections', 'orders', 'data', 'mixed'],
      dataRetentionTest: {
        enabled: true,
        retainDuration: 300000, // 5 minutes
        dataPoints: 10000
      },
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.connectionPool = new MT5ConnectionPool(mt5Config);

    // Capture initial memory baseline
    this.memoryBaseline = this.captureMemorySnapshot();
  }

  private captureMemorySnapshot(): MemorySnapshot {
    const memUsage = process.memoryUsage();
    return {
      timestamp: Date.now(),
      heapUsed: memUsage.heapUsed / 1024 / 1024, // Convert to MB
      heapTotal: memUsage.heapTotal / 1024 / 1024,
      external: memUsage.external / 1024 / 1024,
      rss: memUsage.rss / 1024 / 1024,
      arrayBuffers: memUsage.arrayBuffers / 1024 / 1024,
      activeConnections: this.connectionPool.getActiveConnectionCount(),
      totalOperations: this.operationCount
    };
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 memory test warmup...');

    // Capture pre-warmup memory state
    const preWarmup = this.captureMemorySnapshot();
    this.emit('memorySnapshot', { phase: 'pre-warmup', snapshot: preWarmup });

    // Initialize baseline connections
    const baselineConnections = 5;
    await this.connectionPool.createMultipleConnections(baselineConnections);

    // Warmup operations to stabilize memory usage
    const connections = this.connectionPool.getAllConnections();
    for (let i = 0; i < 50; i++) {
      const conn = connections[i % connections.length];
      await conn.getAccountInfo();
      await conn.getTickData('EURUSD');
      this.operationCount++;
    }

    // Force garbage collection to establish clean baseline
    if (global.gc) {
      global.gc();
    }

    // Capture post-warmup baseline
    this.memoryBaseline = this.captureMemorySnapshot();
    this.emit('memorySnapshot', { phase: 'post-warmup', snapshot: this.memoryBaseline });

    this.emit('message', `Memory baseline established: ${this.memoryBaseline.heapUsed.toFixed(2)} MB`);
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting memory test execution...');

    // Start memory monitoring
    const monitoringPromise = this.startMemoryMonitoring();

    // Start GC forcing if enabled
    const gcPromise = this.startPeriodicGC();

    // Execute memory stress patterns
    const stressPromises = this.testConfig.memoryStressPatterns.map(pattern =>
      this.executeMemoryStressPattern(pattern)
    );

    // Start data retention test if enabled
    if (this.testConfig.dataRetentionTest.enabled) {
      stressPromises.push(this.executeDataRetentionTest());
    }

    await Promise.all([monitoringPromise, gcPromise, ...stressPromises]);

    this.emit('message', 'Memory test execution completed');
  }

  private async startMemoryMonitoring(): Promise<void> {
    while (this.isRunning) {
      const snapshot = this.captureMemorySnapshot();
      this.memorySnapshots.push(snapshot);

      // Analyze memory growth
      this.analyzeMemoryGrowth(snapshot);

      // Emit memory update
      this.emit('memoryUpdate', {
        current: snapshot.heapUsed,
        growth: snapshot.heapUsed - this.memoryBaseline.heapUsed,
        leakDetected: this.leakDetected
      });

      // Check for memory threshold violations
      if (snapshot.heapUsed > this.config.maxMemoryUsage) {
        this.emit('memoryThresholdExceeded', {
          current: snapshot.heapUsed,
          threshold: this.config.maxMemoryUsage
        });
      }

      // Keep snapshots within reasonable bounds
      if (this.memorySnapshots.length > 1000) {
        this.memorySnapshots = this.memorySnapshots.slice(-500);
      }

      await new Promise(resolve => setTimeout(resolve, this.testConfig.memoryMonitoringInterval));
    }
  }

  private analyzeMemoryGrowth(currentSnapshot: MemorySnapshot): void {
    if (this.memorySnapshots.length < 12) return; // Need at least 1 minute of data

    // Calculate growth rate over the last minute
    const oneMinuteAgo = this.memorySnapshots[this.memorySnapshots.length - 12];
    const timeDiff = (currentSnapshot.timestamp - oneMinuteAgo.timestamp) / 1000 / 60; // minutes
    const memoryGrowth = currentSnapshot.heapUsed - oneMinuteAgo.heapUsed;
    const growthRate = memoryGrowth / timeDiff; // MB per minute

    if (growthRate > this.testConfig.leakDetectionThreshold && !this.leakDetected) {
      this.leakDetected = true;
      this.emit('memoryLeakDetected', {
        growthRate,
        threshold: this.testConfig.leakDetectionThreshold,
        currentMemory: currentSnapshot.heapUsed
      });
    }

    // Check for total heap growth limit
    const totalGrowth = currentSnapshot.heapUsed - this.memoryBaseline.heapUsed;
    if (totalGrowth > this.testConfig.maxHeapGrowth) {
      this.emit('heapGrowthLimitExceeded', {
        totalGrowth,
        limit: this.testConfig.maxHeapGrowth
      });
    }
  }

  private async startPeriodicGC(): Promise<void> {
    while (this.isRunning) {
      await new Promise(resolve => setTimeout(resolve, this.testConfig.gcForceInterval));

      if (global.gc) {
        const beforeGC = this.captureMemorySnapshot();
        global.gc();
        const afterGC = this.captureMemorySnapshot();

        this.emit('gcExecuted', {
          before: beforeGC.heapUsed,
          after: afterGC.heapUsed,
          recovered: beforeGC.heapUsed - afterGC.heapUsed
        });
      }
    }
  }

  private async executeMemoryStressPattern(pattern: string): Promise<void> {
    this.emit('message', `Starting ${pattern} memory stress pattern...`);

    const patternDuration = this.config.duration / this.testConfig.memoryStressPatterns.length;
    const startTime = performance.now();

    while (performance.now() - startTime < patternDuration && this.isRunning) {
      try {
        switch (pattern) {
          case 'connections':
            await this.stressTestConnections();
            break;
          case 'orders':
            await this.stressTestOrders();
            break;
          case 'data':
            await this.stressTestDataProcessing();
            break;
          case 'mixed':
            await this.stressTestMixed();
            break;
        }
      } catch (error) {
        this.recordError(error);
      }

      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.emit('message', `Completed ${pattern} memory stress pattern`);
  }

  private async stressTestConnections(): Promise<void> {
    // Create and destroy connections rapidly to test connection memory management
    const tempConnections = await this.connectionPool.createMultipleConnections(10);

    // Use connections briefly
    for (const conn of tempConnections) {
      await conn.getAccountInfo();
      this.operationCount++;
    }

    // Close connections to test cleanup
    for (const conn of tempConnections) {
      await conn.closeConnection();
    }
  }

  private async stressTestOrders(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) return;

    // Execute many orders to test order object memory management
    const orderPromises = connections.map(async (conn) => {
      for (let i = 0; i < 20; i++) {
        try {
          await conn.executeOrder({
            symbol: 'EURUSD',
            volume: 0.01,
            type: 'BUY',
            comment: `MemoryTest_${i}`
          });
          this.operationCount++;
        } catch (error) {
          // Ignore errors for memory testing
        }
      }
    });

    await Promise.all(orderPromises);
  }

  private async stressTestDataProcessing(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) return;

    // Rapidly request tick data to test data processing memory
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];

    const dataPromises = connections.map(async (conn, connIndex) => {
      for (let i = 0; i < 50; i++) {
        try {
          const symbol = symbols[i % symbols.length];
          await conn.getTickData(symbol);
          this.operationCount++;
        } catch (error) {
          // Ignore errors for memory testing
        }
      }
    });

    await Promise.all(dataPromises);
  }

  private async stressTestMixed(): Promise<void> {
    const connections = this.connectionPool.getAllConnections();
    if (connections.length === 0) return;

    // Mixed operations to test overall memory behavior
    const mixedPromises = connections.map(async (conn) => {
      for (let i = 0; i < 10; i++) {
        try {
          // Rotate through different operations
          switch (i % 4) {
            case 0:
              await conn.getAccountInfo();
              break;
            case 1:
              await conn.getTickData('EURUSD');
              break;
            case 2:
              await conn.getPositions();
              break;
            case 3:
              await conn.executeOrder({
                symbol: 'EURUSD',
                volume: 0.01,
                type: 'BUY',
                comment: `Mixed_${i}`
              });
              break;
          }
          this.operationCount++;
        } catch (error) {
          // Ignore errors for memory testing
        }
      }
    });

    await Promise.all(mixedPromises);
  }

  private async executeDataRetentionTest(): Promise<void> {
    this.emit('message', 'Starting data retention memory test...');

    const retentionConfig = this.testConfig.dataRetentionTest;
    const startTime = performance.now();

    while (performance.now() - startTime < retentionConfig.retainDuration && this.isRunning) {
      // Accumulate data points to test memory retention
      const dataPoint = {
        timestamp: Date.now(),
        price: Math.random() * 1.2,
        volume: Math.random() * 1000,
        metadata: {
          id: Math.random().toString(36),
          source: 'memory_test',
          tags: Array.from({ length: 10 }, () => Math.random().toString(36))
        }
      };

      this.dataRetentionBuffer.push(dataPoint);

      // Maintain buffer size
      if (this.dataRetentionBuffer.length > retentionConfig.dataPoints) {
        this.dataRetentionBuffer = this.dataRetentionBuffer.slice(-retentionConfig.dataPoints / 2);
      }

      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Clear retention buffer at the end
    this.dataRetentionBuffer = [];

    this.emit('message', 'Data retention memory test completed');
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting memory test cooldown...');

    // Force final garbage collection
    if (global.gc) {
      global.gc();
    }

    // Close all connections
    await this.connectionPool.closeAllConnections();

    // Clear data retention buffer
    this.dataRetentionBuffer = [];

    // Capture final memory state
    const finalSnapshot = this.captureMemorySnapshot();
    this.emit('memorySnapshot', { phase: 'final', snapshot: finalSnapshot });

    // Generate memory analysis
    this.generateMemoryAnalysis();

    this.emit('message', 'Memory test cooldown completed');
  }

  private generateMemoryAnalysis(): void {
    if (this.memorySnapshots.length === 0) return;

    const finalSnapshot = this.memorySnapshots[this.memorySnapshots.length - 1];
    const peakMemory = Math.max(...this.memorySnapshots.map(s => s.heapUsed));
    const memoryGrowth = finalSnapshot.heapUsed - this.memoryBaseline.heapUsed;

    // Calculate average growth rate
    const testDurationMinutes = (finalSnapshot.timestamp - this.memoryBaseline.timestamp) / 1000 / 60;
    const averageGrowthRate = memoryGrowth / testDurationMinutes;

    // Memory efficiency metrics
    const operationsPerMB = this.operationCount / Math.max(memoryGrowth, 1);

    const analysis = {
      baseline: {
        heapUsed: this.memoryBaseline.heapUsed,
        timestamp: this.memoryBaseline.timestamp
      },
      final: {
        heapUsed: finalSnapshot.heapUsed,
        timestamp: finalSnapshot.timestamp
      },
      growth: {
        totalMB: memoryGrowth,
        peakMB: peakMemory,
        averageRateMBPerMin: averageGrowthRate,
        exceedsThreshold: averageGrowthRate > this.testConfig.leakDetectionThreshold
      },
      efficiency: {
        operationsPerMB,
        totalOperations: this.operationCount,
        memoryPerOperation: memoryGrowth / Math.max(this.operationCount, 1)
      },
      leakDetection: {
        detected: this.leakDetected,
        threshold: this.testConfig.leakDetectionThreshold,
        assessment: this.getLeakAssessment(averageGrowthRate)
      },
      snapshots: this.memorySnapshots.length,
      testDurationMinutes
    };

    // Store analysis in metrics
    (this.metrics as any).memoryAnalysis = analysis;

    this.emit('memoryAnalysis', analysis);
  }

  private getLeakAssessment(growthRate: number): string {
    if (growthRate < 1) {
      return 'Excellent - Minimal memory growth';
    } else if (growthRate < 5) {
      return 'Good - Low memory growth';
    } else if (growthRate < this.testConfig.leakDetectionThreshold) {
      return 'Acceptable - Moderate memory growth';
    } else if (growthRate < this.testConfig.leakDetectionThreshold * 2) {
      return 'Poor - High memory growth detected';
    } else {
      return 'Critical - Severe memory leak suspected';
    }
  }

  public getMemorySnapshots(): MemorySnapshot[] {
    return [...this.memorySnapshots];
  }

  public generateMemoryReport(): string {
    const analysis = (this.metrics as any).memoryAnalysis || {};
    let report = '# MT5 Memory Usage Test Report\n\n';

    if (analysis.baseline && analysis.final) {
      report += `## Memory Usage Summary\n\n`;
      report += `- **Baseline Memory:** ${analysis.baseline.heapUsed.toFixed(2)} MB\n`;
      report += `- **Final Memory:** ${analysis.final.heapUsed.toFixed(2)} MB\n`;
      report += `- **Peak Memory:** ${analysis.growth.peakMB.toFixed(2)} MB\n`;
      report += `- **Total Growth:** ${analysis.growth.totalMB.toFixed(2)} MB\n`;
      report += `- **Test Duration:** ${analysis.testDurationMinutes.toFixed(1)} minutes\n\n`;
    }

    if (analysis.growth) {
      report += `## Memory Growth Analysis\n\n`;
      report += `- **Average Growth Rate:** ${analysis.growth.averageRateMBPerMin.toFixed(2)} MB/min\n`;
      report += `- **Threshold:** ${this.testConfig.leakDetectionThreshold} MB/min\n`;
      report += `- **Exceeds Threshold:** ${analysis.growth.exceedsThreshold ? 'Yes ❌' : 'No ✅'}\n\n`;
    }

    if (analysis.efficiency) {
      report += `## Efficiency Metrics\n\n`;
      report += `- **Total Operations:** ${analysis.efficiency.totalOperations.toLocaleString()}\n`;
      report += `- **Operations per MB:** ${analysis.efficiency.operationsPerMB.toFixed(2)}\n`;
      report += `- **Memory per Operation:** ${(analysis.efficiency.memoryPerOperation * 1024).toFixed(2)} KB\n\n`;
    }

    if (analysis.leakDetection) {
      report += `## Leak Detection\n\n`;
      report += `- **Assessment:** ${analysis.leakDetection.assessment}\n`;
      report += `- **Leak Detected:** ${analysis.leakDetection.detected ? 'Yes ❌' : 'No ✅'}\n\n`;

      if (analysis.leakDetection.detected) {
        report += `### Recommendations\n\n`;
        report += `1. Review connection pooling and cleanup procedures\n`;
        report += `2. Implement proper object disposal in MT5 operations\n`;
        report += `3. Consider implementing memory usage limits\n`;
        report += `4. Add more frequent garbage collection for high-volume operations\n\n`;
      }
    }

    return report;
  }
}