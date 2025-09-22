import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5ConnectionPool } from '../infrastructure/MT5TestHelper';

export interface StressTestConfig extends TestConfig {
  maxConnections: number;
  connectionRampUpRate: number; // connections per second
  orderVelocity: number; // orders per second per connection
  tickDataVelocity: number; // tick requests per second per connection
  errorThreshold: number; // max error rate percentage
  memoryLeakThreshold: number; // MB growth per minute
  connectionDropThreshold: number; // max acceptable connection drops
  highFrequencyBursts: {
    enabled: boolean;
    burstSize: number;
    burstFrequency: number; // bursts per minute
    maxConcurrentBursts: number;
  };
}

export class MT5StressTest extends PerformanceTestBase {
  private connectionPool: MT5ConnectionPool;
  private testConfig: StressTestConfig;
  private stressMetrics: Map<string, any> = new Map();
  private activeConnections: number = 0;
  private connectionErrors: number = 0;
  private orderErrors: number = 0;
  private memoryBaseline: number = 0;
  private burstController: AbortController = new AbortController();

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<StressTestConfig> = {}
  ) {
    const config: StressTestConfig = {
      duration: 1800000, // 30 minutes
      concurrency: 50,
      warmupTime: 30000,
      cooldownTime: 15000,
      sampleInterval: 2000,
      maxMemoryUsage: 2048, // 2GB
      maxLatency: 2000, // 2 seconds under stress
      minThroughput: 200,
      maxConnections: 100,
      connectionRampUpRate: 2, // 2 connections per second
      orderVelocity: 5, // 5 orders per second per connection
      tickDataVelocity: 10, // 10 tick requests per second per connection
      errorThreshold: 5, // 5% max error rate
      memoryLeakThreshold: 50, // 50MB growth per minute
      connectionDropThreshold: 2, // max 2% connection drops
      highFrequencyBursts: {
        enabled: true,
        burstSize: 100,
        burstFrequency: 6, // 6 bursts per minute
        maxConcurrentBursts: 3
      },
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.connectionPool = new MT5ConnectionPool(mt5Config);

    this.initializeStressMetrics();
  }

  private initializeStressMetrics(): void {
    this.stressMetrics.set('connectionStability', {
      attempted: 0,
      successful: 0,
      failed: 0,
      dropped: 0,
      reconnections: 0
    });

    this.stressMetrics.set('orderProcessing', {
      attempted: 0,
      successful: 0,
      failed: 0,
      rejections: 0,
      timeouts: 0
    });

    this.stressMetrics.set('dataFeed', {
      ticksRequested: 0,
      ticksReceived: 0,
      missedTicks: 0,
      delays: []
    });

    this.stressMetrics.set('systemResources', {
      peakMemory: 0,
      memoryGrowthRate: 0,
      cpuPeaks: [],
      connectionPeaks: []
    });
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 stress test warmup...');

    // Establish baseline memory usage
    this.memoryBaseline = process.memoryUsage().heapUsed / 1024 / 1024;

    // Initialize a small number of connections for baseline
    const baselineConnections = Math.min(5, this.testConfig.maxConnections);
    this.emit('message', `Establishing ${baselineConnections} baseline connections...`);

    const connections = await this.connectionPool.createMultipleConnections(baselineConnections);
    this.activeConnections = connections.length;

    // Warmup operations
    const warmupPromises = connections.map(async (conn, i) => {
      for (let j = 0; j < 10; j++) {
        await conn.getAccountInfo();
        await conn.getTickData('EURUSD');
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      this.emit('message', `Baseline connection ${i} warmed up`);
    });

    await Promise.all(warmupPromises);
    this.emit('message', 'Stress test warmup completed');
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting stress test execution...');

    // Start parallel stress test components
    const stressPromises = [
      this.executeConnectionStressTest(),
      this.executeOrderStressTest(),
      this.executeDataFeedStressTest(),
      this.executeMemoryStressTest()
    ];

    // Add high-frequency burst testing if enabled
    if (this.testConfig.highFrequencyBursts.enabled) {
      stressPromises.push(this.executeHighFrequencyBursts());
    }

    await Promise.all(stressPromises);

    this.emit('message', 'Stress test execution completed');
  }

  private async executeConnectionStressTest(): Promise<void> {
    this.emit('message', 'Starting connection stress test...');

    const rampUpInterval = 1000 / this.testConfig.connectionRampUpRate;
    const connectionStability = this.stressMetrics.get('connectionStability');

    // Gradual ramp-up of connections
    while (this.activeConnections < this.testConfig.maxConnections && this.isRunning) {
      try {
        connectionStability.attempted++;

        const newConnection = await this.connectionPool.createConnection(`stress_${this.activeConnections}`);
        this.activeConnections++;
        connectionStability.successful++;

        this.emit('connectionAdded', {
          active: this.activeConnections,
          target: this.testConfig.maxConnections
        });

        // Monitor connection health
        this.monitorConnectionHealth(newConnection);

      } catch (error) {
        connectionStability.failed++;
        this.connectionErrors++;
        this.recordError(error);

        this.emit('connectionFailed', {
          error: error.message,
          activeConnections: this.activeConnections
        });
      }

      await new Promise(resolve => setTimeout(resolve, rampUpInterval));
    }

    this.emit('message', `Connection ramp-up completed. Active: ${this.activeConnections}`);
  }

  private async executeOrderStressTest(): Promise<void> {
    this.emit('message', 'Starting order stress test...');

    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];
    const orderProcessing = this.stressMetrics.get('orderProcessing');

    // Continuous order processing across all connections
    const orderInterval = 1000 / this.testConfig.orderVelocity;

    const processOrders = async () => {
      while (this.isRunning) {
        const connections = this.connectionPool.getAllConnections();

        if (connections.length === 0) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          continue;
        }

        const orderPromises = connections.map(async (conn, connIndex) => {
          if (!conn.isConnectionActive()) return;

          try {
            orderProcessing.attempted++;

            const order = {
              symbol: symbols[connIndex % symbols.length],
              volume: 0.01,
              type: Math.random() > 0.5 ? 'BUY' : 'SELL' as 'BUY' | 'SELL',
              comment: `StressTest_${connIndex}_${Date.now()}`
            };

            const { success, latency } = await conn.executeOrder(order);

            if (success) {
              orderProcessing.successful++;
              this.metrics.throughput.totalRequests++;
            } else {
              orderProcessing.failed++;
              this.orderErrors++;
            }

            // Check for timeout (latency > 5 seconds indicates timeout)
            if (latency > 5000) {
              orderProcessing.timeouts++;
            }

          } catch (error) {
            orderProcessing.failed++;
            this.orderErrors++;
            this.recordError(error);
          }
        });

        await Promise.all(orderPromises);
        await new Promise(resolve => setTimeout(resolve, orderInterval));
      }
    };

    await processOrders();
  }

  private async executeDataFeedStressTest(): Promise<void> {
    this.emit('message', 'Starting data feed stress test...');

    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD', 'EURJPY', 'GBPJPY'];
    const dataFeed = this.stressMetrics.get('dataFeed');

    const tickInterval = 1000 / this.testConfig.tickDataVelocity;

    const processTickData = async () => {
      while (this.isRunning) {
        const connections = this.connectionPool.getAllConnections();

        if (connections.length === 0) {
          await new Promise(resolve => setTimeout(resolve, 1000));
          continue;
        }

        const tickPromises = connections.map(async (conn, connIndex) => {
          if (!conn.isConnectionActive()) return;

          const symbol = symbols[connIndex % symbols.length];
          const requestTime = performance.now();

          try {
            dataFeed.ticksRequested++;

            const { success, latency, tick } = await conn.getTickData(symbol);

            if (success && tick) {
              dataFeed.ticksReceived++;
              dataFeed.delays.push(latency);

              // Keep only recent delays for memory efficiency
              if (dataFeed.delays.length > 1000) {
                dataFeed.delays = dataFeed.delays.slice(-500);
              }
            } else {
              dataFeed.missedTicks++;
            }

          } catch (error) {
            dataFeed.missedTicks++;
            this.recordError(error);
          }
        });

        await Promise.all(tickPromises);
        await new Promise(resolve => setTimeout(resolve, tickInterval));
      }
    };

    await processTickData();
  }

  private async executeMemoryStressTest(): Promise<void> {
    this.emit('message', 'Starting memory stress test...');

    const systemResources = this.stressMetrics.get('systemResources');
    let lastMemoryCheck = performance.now();
    let lastMemoryUsage = this.memoryBaseline;

    const monitorMemory = async () => {
      while (this.isRunning) {
        const currentMemory = process.memoryUsage().heapUsed / 1024 / 1024;
        const currentTime = performance.now();

        // Track peak memory
        systemResources.peakMemory = Math.max(systemResources.peakMemory, currentMemory);

        // Calculate memory growth rate (MB per minute)
        const timeDiff = currentTime - lastMemoryCheck;
        if (timeDiff >= 60000) { // Check every minute
          const memoryGrowth = currentMemory - lastMemoryUsage;
          systemResources.memoryGrowthRate = (memoryGrowth / timeDiff) * 60000;

          lastMemoryCheck = currentTime;
          lastMemoryUsage = currentMemory;

          this.emit('memoryGrowthUpdate', {
            current: currentMemory,
            growth: systemResources.memoryGrowthRate,
            threshold: this.testConfig.memoryLeakThreshold
          });

          // Check for memory leak
          if (systemResources.memoryGrowthRate > this.testConfig.memoryLeakThreshold) {
            this.emit('memoryLeakDetected', {
              growthRate: systemResources.memoryGrowthRate,
              threshold: this.testConfig.memoryLeakThreshold
            });
          }
        }

        // Monitor CPU usage
        const cpuUsage = process.cpuUsage();
        const totalCpuTime = (cpuUsage.user + cpuUsage.system) / 1000000; // Convert to seconds
        systemResources.cpuPeaks.push(totalCpuTime);

        // Keep only recent CPU data
        if (systemResources.cpuPeaks.length > 100) {
          systemResources.cpuPeaks = systemResources.cpuPeaks.slice(-50);
        }

        await new Promise(resolve => setTimeout(resolve, 5000)); // Check every 5 seconds
      }
    };

    await monitorMemory();
  }

  private async executeHighFrequencyBursts(): Promise<void> {
    this.emit('message', 'Starting high-frequency burst testing...');

    const burstConfig = this.testConfig.highFrequencyBursts;
    const burstInterval = 60000 / burstConfig.burstFrequency; // ms between bursts
    let activeBursts = 0;

    const executeBurst = async (burstId: number) => {
      activeBursts++;
      this.emit('burstStarted', { burstId, activeBursts });

      try {
        const connections = this.connectionPool.getAllConnections();
        const burstPromises = [];

        for (let i = 0; i < burstConfig.burstSize; i++) {
          if (this.burstController.signal.aborted) break;

          const conn = connections[i % connections.length];
          if (conn && conn.isConnectionActive()) {
            burstPromises.push(
              conn.getTickData('EURUSD').catch(error => {
                this.recordError(error);
                return { success: false };
              })
            );
          }
        }

        const results = await Promise.all(burstPromises);
        const successCount = results.filter(r => r.success).length;

        this.emit('burstCompleted', {
          burstId,
          requested: burstConfig.burstSize,
          successful: successCount,
          successRate: (successCount / burstConfig.burstSize) * 100
        });

      } catch (error) {
        this.emit('burstFailed', { burstId, error: error.message });
        this.recordError(error);
      } finally {
        activeBursts--;
      }
    };

    let burstCount = 0;
    while (this.isRunning && !this.burstController.signal.aborted) {
      if (activeBursts < burstConfig.maxConcurrentBursts) {
        executeBurst(++burstCount);
      }

      await new Promise(resolve => setTimeout(resolve, burstInterval));
    }
  }

  private monitorConnectionHealth(connection: MT5TestHelper): void {
    // Periodically check connection health and attempt reconnection if needed
    const healthCheck = setInterval(async () => {
      if (!this.isRunning) {
        clearInterval(healthCheck);
        return;
      }

      if (!connection.isConnectionActive()) {
        const connectionStability = this.stressMetrics.get('connectionStability');
        connectionStability.dropped++;

        try {
          // Attempt reconnection
          await connection.initializeConnection();
          connectionStability.reconnections++;

          this.emit('connectionReconnected', {
            activeConnections: this.activeConnections
          });
        } catch (error) {
          this.recordError(error);
          this.activeConnections = Math.max(0, this.activeConnections - 1);
        }
      }
    }, 10000); // Check every 10 seconds
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting stress test cooldown...');

    // Stop burst testing
    this.burstController.abort();

    // Gradually close connections
    await this.connectionPool.closeAllConnections();

    // Generate stress test analysis
    this.generateStressAnalysis();

    this.emit('message', 'Stress test cooldown completed');
  }

  private generateStressAnalysis(): void {
    const analysis: any = {
      summary: {
        testDuration: this.metrics.throughput.duration / 1000 / 60, // minutes
        peakConnections: this.activeConnections,
        totalErrors: this.metrics.errors.count,
        errorRate: (this.metrics.errors.count / Math.max(1, this.metrics.throughput.totalRequests)) * 100
      },
      stability: {},
      performance: {},
      recommendations: []
    };

    // Connection stability analysis
    const connectionStability = this.stressMetrics.get('connectionStability');
    analysis.stability.connections = {
      attempted: connectionStability.attempted,
      successful: connectionStability.successful,
      failed: connectionStability.failed,
      dropped: connectionStability.dropped,
      reconnections: connectionStability.reconnections,
      successRate: (connectionStability.successful / Math.max(1, connectionStability.attempted)) * 100,
      dropRate: (connectionStability.dropped / Math.max(1, connectionStability.successful)) * 100
    };

    // Order processing analysis
    const orderProcessing = this.stressMetrics.get('orderProcessing');
    analysis.performance.orders = {
      attempted: orderProcessing.attempted,
      successful: orderProcessing.successful,
      failed: orderProcessing.failed,
      timeouts: orderProcessing.timeouts,
      successRate: (orderProcessing.successful / Math.max(1, orderProcessing.attempted)) * 100,
      timeoutRate: (orderProcessing.timeouts / Math.max(1, orderProcessing.attempted)) * 100
    };

    // Data feed analysis
    const dataFeed = this.stressMetrics.get('dataFeed');
    analysis.performance.dataFeed = {
      requested: dataFeed.ticksRequested,
      received: dataFeed.ticksReceived,
      missed: dataFeed.missedTicks,
      successRate: (dataFeed.ticksReceived / Math.max(1, dataFeed.ticksRequested)) * 100,
      averageDelay: dataFeed.delays.length > 0 ?
        dataFeed.delays.reduce((a, b) => a + b, 0) / dataFeed.delays.length : 0
    };

    // System resources analysis
    const systemResources = this.stressMetrics.get('systemResources');
    analysis.performance.system = {
      peakMemoryMB: systemResources.peakMemory,
      memoryGrowthRateMBPerMin: systemResources.memoryGrowthRate,
      memoryLeakDetected: systemResources.memoryGrowthRate > this.testConfig.memoryLeakThreshold
    };

    // Generate recommendations
    if (analysis.stability.connections.dropRate > this.testConfig.connectionDropThreshold) {
      analysis.recommendations.push('High connection drop rate detected - investigate network stability');
    }

    if (analysis.summary.errorRate > this.testConfig.errorThreshold) {
      analysis.recommendations.push('Error rate exceeds threshold - review error handling and retry logic');
    }

    if (analysis.performance.system.memoryLeakDetected) {
      analysis.recommendations.push('Memory leak detected - investigate memory management and cleanup routines');
    }

    if (analysis.performance.orders.timeoutRate > 10) {
      analysis.recommendations.push('High order timeout rate - consider increasing timeout values or optimizing order processing');
    }

    // Store analysis
    (this.metrics as any).stressAnalysis = analysis;
    this.emit('stressAnalysis', analysis);
  }

  public getStressMetrics(): Map<string, any> {
    return new Map(this.stressMetrics);
  }

  public generateStressReport(): string {
    const analysis = (this.metrics as any).stressAnalysis || {};
    let report = '# MT5 Stress Test Report\n\n';

    if (analysis.summary) {
      report += `## Test Summary\n\n`;
      report += `- **Duration:** ${analysis.summary.testDuration.toFixed(1)} minutes\n`;
      report += `- **Peak Connections:** ${analysis.summary.peakConnections}\n`;
      report += `- **Total Errors:** ${analysis.summary.totalErrors}\n`;
      report += `- **Error Rate:** ${analysis.summary.errorRate.toFixed(2)}%\n\n`;
    }

    if (analysis.stability?.connections) {
      const conn = analysis.stability.connections;
      report += `## Connection Stability\n\n`;
      report += `- **Success Rate:** ${conn.successRate.toFixed(2)}%\n`;
      report += `- **Drop Rate:** ${conn.dropRate.toFixed(2)}%\n`;
      report += `- **Reconnections:** ${conn.reconnections}\n\n`;

      if (conn.dropRate < 1) {
        report += '✅ **Excellent connection stability**\n\n';
      } else if (conn.dropRate < 3) {
        report += '⚠️ **Good connection stability**\n\n';
      } else {
        report += '❌ **Poor connection stability - investigation needed**\n\n';
      }
    }

    if (analysis.performance?.system) {
      const sys = analysis.performance.system;
      report += `## System Performance\n\n`;
      report += `- **Peak Memory:** ${sys.peakMemoryMB.toFixed(2)} MB\n`;
      report += `- **Memory Growth Rate:** ${sys.memoryGrowthRateMBPerMin.toFixed(2)} MB/min\n`;
      report += `- **Memory Leak:** ${sys.memoryLeakDetected ? 'Detected ❌' : 'None ✅'}\n\n`;
    }

    if (analysis.recommendations?.length > 0) {
      report += `## Recommendations\n\n`;
      analysis.recommendations.forEach((rec: string, i: number) => {
        report += `${i + 1}. ${rec}\n`;
      });
      report += '\n';
    }

    return report;
  }
}