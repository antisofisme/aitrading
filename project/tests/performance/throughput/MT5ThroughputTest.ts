import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5OrderRequest } from '../infrastructure/MT5TestHelper';

export interface ThroughputTestConfig extends TestConfig {
  concurrentConnections: number;
  ordersPerConnection: number;
  tickDataRequestsPerSecond: number;
  testPatterns: ('orders' | 'ticks' | 'mixed' | 'burst')[];
  burstSize: number;
  burstInterval: number;
}

export class MT5ThroughputTest extends PerformanceTestBase {
  private connections: MT5TestHelper[] = [];
  private testConfig: ThroughputTestConfig;
  private throughputResults: Map<string, { requests: number; duration: number; rps: number }> = new Map();
  private mt5Config: MT5ConnectionConfig;

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<ThroughputTestConfig> = {}
  ) {
    const config: ThroughputTestConfig = {
      duration: 600000, // 10 minutes
      concurrency: 10,
      warmupTime: 15000,
      cooldownTime: 10000,
      sampleInterval: 5000,
      maxMemoryUsage: 1024, // 1GB
      maxLatency: 1000,
      minThroughput: 100,
      concurrentConnections: 5,
      ordersPerConnection: 50,
      tickDataRequestsPerSecond: 20,
      testPatterns: ['orders', 'ticks', 'mixed', 'burst'],
      burstSize: 50,
      burstInterval: 10000, // 10 seconds
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.mt5Config = mt5Config;
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 throughput test warmup...');

    // Initialize multiple connections
    this.emit('message', `Initializing ${this.testConfig.concurrentConnections} MT5 connections...`);

    const connectionPromises = Array.from({ length: this.testConfig.concurrentConnections }, async (_, i) => {
      const helper = new MT5TestHelper(this.mt5Config);
      const { success } = await helper.initializeConnection();
      if (!success) {
        throw new Error(`Failed to initialize connection ${i}`);
      }
      return helper;
    });

    this.connections = await Promise.all(connectionPromises);
    this.emit('message', `All ${this.connections.length} connections established`);

    // Warmup each connection
    const warmupPromises = this.connections.map(async (conn, i) => {
      for (let j = 0; j < 5; j++) {
        await conn.getAccountInfo();
        await conn.getTickData('EURUSD');
      }
      this.emit('message', `Connection ${i} warmed up`);
    });

    await Promise.all(warmupPromises);
    this.emit('message', 'Warmup completed');
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting throughput test execution...');

    // Run all test patterns in parallel
    const testPromises = this.testConfig.testPatterns.map(pattern =>
      this.executeTestPattern(pattern)
    );

    await Promise.all(testPromises);

    this.emit('message', 'Throughput test execution completed');
  }

  private async executeTestPattern(pattern: string): Promise<void> {
    this.emit('message', `Starting ${pattern} throughput test...`);

    const startTime = performance.now();
    let totalRequests = 0;

    try {
      switch (pattern) {
        case 'orders':
          totalRequests = await this.testOrderThroughput();
          break;
        case 'ticks':
          totalRequests = await this.testTickDataThroughput();
          break;
        case 'mixed':
          totalRequests = await this.testMixedThroughput();
          break;
        case 'burst':
          totalRequests = await this.testBurstThroughput();
          break;
      }

      const duration = performance.now() - startTime;
      const rps = (totalRequests / duration) * 1000;

      this.throughputResults.set(pattern, {
        requests: totalRequests,
        duration,
        rps
      });

      this.emit('patternCompleted', {
        pattern,
        requests: totalRequests,
        duration: duration.toFixed(2),
        rps: rps.toFixed(2)
      });

    } catch (error) {
      this.emit('patternFailed', { pattern, error: error.message });
      this.recordError(error);
    }
  }

  private async testOrderThroughput(): Promise<number> {
    let totalRequests = 0;
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];

    // Execute orders concurrently across all connections
    const connectionPromises = this.connections.map(async (conn, connIndex) => {
      let connectionRequests = 0;

      for (let i = 0; i < this.testConfig.ordersPerConnection; i++) {
        const symbol = symbols[i % symbols.length];
        const orderType = i % 2 === 0 ? 'BUY' : 'SELL';

        const order: MT5OrderRequest = {
          symbol,
          volume: 0.01,
          type: orderType,
          comment: `ThroughputTest_${connIndex}_${i}`
        };

        try {
          const { success } = await conn.executeOrder(order);
          if (success) {
            connectionRequests++;
            this.metrics.throughput.totalRequests++;
          }
        } catch (error) {
          this.recordError(error);
        }

        // Small delay to prevent overwhelming
        await new Promise(resolve => setTimeout(resolve, 20));
      }

      return connectionRequests;
    });

    const results = await Promise.all(connectionPromises);
    totalRequests = results.reduce((sum, count) => sum + count, 0);

    return totalRequests;
  }

  private async testTickDataThroughput(): Promise<number> {
    let totalRequests = 0;
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];
    const testDuration = 60000; // 1 minute for tick data test
    const startTime = performance.now();

    // Create tick data streams for each connection
    const streamPromises = this.connections.map(async (conn, connIndex) => {
      let connectionRequests = 0;

      while (performance.now() - startTime < testDuration) {
        const symbol = symbols[connIndex % symbols.length];

        try {
          const { success } = await conn.getTickData(symbol);
          if (success) {
            connectionRequests++;
            this.metrics.throughput.totalRequests++;
          }
        } catch (error) {
          this.recordError(error);
        }

        // Rate limiting based on tickDataRequestsPerSecond
        const delayMs = 1000 / this.testConfig.tickDataRequestsPerSecond;
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }

      return connectionRequests;
    });

    const results = await Promise.all(streamPromises);
    totalRequests = results.reduce((sum, count) => sum + count, 0);

    return totalRequests;
  }

  private async testMixedThroughput(): Promise<number> {
    let totalRequests = 0;
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY'];
    const testDuration = 120000; // 2 minutes for mixed test
    const startTime = performance.now();

    const mixedPromises = this.connections.map(async (conn, connIndex) => {
      let connectionRequests = 0;
      let operationCount = 0;

      while (performance.now() - startTime < testDuration) {
        const operationType = operationCount % 4;

        try {
          switch (operationType) {
            case 0: // Order execution
              const order: MT5OrderRequest = {
                symbol: symbols[operationCount % symbols.length],
                volume: 0.01,
                type: operationCount % 2 === 0 ? 'BUY' : 'SELL',
                comment: `Mixed_${connIndex}_${operationCount}`
              };
              const { success: orderSuccess } = await conn.executeOrder(order);
              if (orderSuccess) connectionRequests++;
              break;

            case 1: // Tick data
              const { success: tickSuccess } = await conn.getTickData(symbols[operationCount % symbols.length]);
              if (tickSuccess) connectionRequests++;
              break;

            case 2: // Account info
              await conn.getAccountInfo();
              connectionRequests++;
              break;

            case 3: // Position info
              await conn.getPositions();
              connectionRequests++;
              break;
          }

          this.metrics.throughput.totalRequests++;
        } catch (error) {
          this.recordError(error);
        }

        operationCount++;
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      return connectionRequests;
    });

    const results = await Promise.all(mixedPromises);
    totalRequests = results.reduce((sum, count) => sum + count, 0);

    return totalRequests;
  }

  private async testBurstThroughput(): Promise<number> {
    let totalRequests = 0;
    const testDuration = 180000; // 3 minutes for burst test
    const startTime = performance.now();

    while (performance.now() - startTime < testDuration) {
      // Execute burst across all connections
      const burstPromises = this.connections.map(async (conn, connIndex) => {
        let burstRequests = 0;

        // Execute burst of operations
        for (let i = 0; i < this.testConfig.burstSize; i++) {
          try {
            const { success } = await conn.getTickData('EURUSD');
            if (success) {
              burstRequests++;
              this.metrics.throughput.totalRequests++;
            }
          } catch (error) {
            this.recordError(error);
          }
        }

        return burstRequests;
      });

      const burstResults = await Promise.all(burstPromises);
      const burstTotal = burstResults.reduce((sum, count) => sum + count, 0);
      totalRequests += burstTotal;

      this.emit('burstCompleted', {
        requests: burstTotal,
        timestamp: new Date().toISOString()
      });

      // Wait for next burst interval
      await new Promise(resolve => setTimeout(resolve, this.testConfig.burstInterval));
    }

    return totalRequests;
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting cooldown...');

    // Close all connections
    const closePromises = this.connections.map(async (conn, i) => {
      await conn.closeConnection();
      this.emit('message', `Connection ${i} closed`);
    });

    await Promise.all(closePromises);

    // Generate throughput analysis
    this.generateThroughputAnalysis();

    this.emit('message', 'Cooldown completed');
  }

  private generateThroughputAnalysis(): void {
    const analysis: any = {
      overall: {
        totalRequests: this.metrics.throughput.totalRequests,
        duration: this.metrics.throughput.duration,
        averageRps: this.metrics.throughput.requestsPerSecond,
        peakRps: 0,
        patterns: {}
      }
    };

    // Analyze each test pattern
    for (const [pattern, result] of this.throughputResults) {
      analysis.overall.patterns[pattern] = {
        requests: result.requests,
        rps: result.rps,
        efficiency: (result.rps / this.testConfig.minThroughput) * 100
      };

      analysis.overall.peakRps = Math.max(analysis.overall.peakRps, result.rps);
    }

    // Performance classification
    if (analysis.overall.averageRps >= this.testConfig.minThroughput * 2) {
      analysis.overall.classification = 'Excellent';
    } else if (analysis.overall.averageRps >= this.testConfig.minThroughput) {
      analysis.overall.classification = 'Good';
    } else if (analysis.overall.averageRps >= this.testConfig.minThroughput * 0.8) {
      analysis.overall.classification = 'Acceptable';
    } else {
      analysis.overall.classification = 'Poor';
    }

    // Store analysis in metrics
    (this.metrics as any).throughputAnalysis = analysis;

    this.emit('throughputAnalysis', analysis);
  }

  public getThroughputResults(): Map<string, { requests: number; duration: number; rps: number }> {
    return new Map(this.throughputResults);
  }

  public generateThroughputReport(): string {
    const analysis = (this.metrics as any).throughputAnalysis || {};
    let report = '# MT5 Throughput Test Report\n\n';

    if (analysis.overall) {
      report += `## Overall Performance\n\n`;
      report += `- **Classification:** ${analysis.overall.classification}\n`;
      report += `- **Total Requests:** ${analysis.overall.totalRequests.toLocaleString()}\n`;
      report += `- **Test Duration:** ${(analysis.overall.duration / 1000).toFixed(2)} seconds\n`;
      report += `- **Average RPS:** ${analysis.overall.averageRps.toFixed(2)}\n`;
      report += `- **Peak RPS:** ${analysis.overall.peakRps.toFixed(2)}\n\n`;

      report += `## Test Pattern Results\n\n`;

      for (const [pattern, data] of Object.entries(analysis.overall.patterns)) {
        const patternData = data as any;
        report += `### ${pattern.charAt(0).toUpperCase() + pattern.slice(1)} Pattern\n\n`;
        report += `- **Requests:** ${patternData.requests.toLocaleString()}\n`;
        report += `- **RPS:** ${patternData.rps.toFixed(2)}\n`;
        report += `- **Efficiency:** ${patternData.efficiency.toFixed(1)}%\n\n`;

        if (patternData.efficiency >= 200) {
          report += '✅ **Excellent throughput**\n\n';
        } else if (patternData.efficiency >= 100) {
          report += '✅ **Good throughput**\n\n';
        } else if (patternData.efficiency >= 80) {
          report += '⚠️ **Acceptable throughput**\n\n';
        } else {
          report += '❌ **Poor throughput - optimization needed**\n\n';
        }
      }
    }

    return report;
  }
}