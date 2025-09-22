import { PerformanceTestBase, TestConfig, PerformanceMetrics } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5OrderRequest } from '../infrastructure/MT5TestHelper';

export interface LatencyTestConfig extends TestConfig {
  connectionCount: number;
  orderTestCount: number;
  tickDataTestCount: number;
  accountInfoTestCount: number;
  symbols: string[];
}

export class MT5LatencyTest extends PerformanceTestBase {
  private mt5Helper: MT5TestHelper;
  private testConfig: LatencyTestConfig;
  private latencyResults: Map<string, number[]> = new Map();

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<LatencyTestConfig> = {}
  ) {
    const config: LatencyTestConfig = {
      duration: 300000, // 5 minutes
      concurrency: 1, // Latency tests are typically sequential
      warmupTime: 10000,
      cooldownTime: 5000,
      sampleInterval: 1000,
      maxMemoryUsage: 256,
      maxLatency: 500, // 500ms max acceptable latency
      minThroughput: 50,
      connectionCount: 1,
      orderTestCount: 100,
      tickDataTestCount: 500,
      accountInfoTestCount: 50,
      symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'],
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.mt5Helper = new MT5TestHelper(mt5Config);

    // Initialize latency tracking for different operations
    this.latencyResults.set('connection', []);
    this.latencyResults.set('orderExecution', []);
    this.latencyResults.set('tickData', []);
    this.latencyResults.set('accountInfo', []);
    this.latencyResults.set('positionInfo', []);
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 latency test warmup...');

    // Initialize connection
    const { success, latency } = await this.mt5Helper.initializeConnection();
    if (!success) {
      throw new Error('Failed to initialize MT5 connection during warmup');
    }

    this.emit('message', `MT5 connection established in ${latency.toFixed(2)}ms`);

    // Warmup operations to stabilize the connection
    for (let i = 0; i < 10; i++) {
      await this.mt5Helper.getAccountInfo();
      await this.mt5Helper.getTickData(this.testConfig.symbols[0]);
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    this.emit('message', 'Warmup completed');
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting latency test execution...');

    // Test 1: Connection Latency
    await this.testConnectionLatency();

    // Test 2: Order Execution Latency
    await this.testOrderExecutionLatency();

    // Test 3: Tick Data Retrieval Latency
    await this.testTickDataLatency();

    // Test 4: Account Info Latency
    await this.testAccountInfoLatency();

    // Test 5: Position Info Latency
    await this.testPositionInfoLatency();

    this.emit('message', 'Latency test execution completed');
  }

  private async testConnectionLatency(): Promise<void> {
    this.emit('message', 'Testing connection latency...');

    // Close current connection and test reconnection latency
    await this.mt5Helper.closeConnection();

    for (let i = 0; i < this.testConfig.connectionCount; i++) {
      const { result, latency } = await this.measureLatency(async () => {
        const { success } = await this.mt5Helper.initializeConnection();
        if (!success) {
          throw new Error('Connection failed');
        }
        return success;
      });

      this.latencyResults.get('connection')!.push(latency);
      this.metrics.throughput.totalRequests++;

      // Close and wait before next connection test
      await this.mt5Helper.closeConnection();
      await new Promise(resolve => setTimeout(resolve, 1000));

      this.emit('progress', {
        operation: 'connection',
        completed: i + 1,
        total: this.testConfig.connectionCount,
        latency: latency.toFixed(2)
      });
    }

    // Reestablish connection for remaining tests
    await this.mt5Helper.initializeConnection();
  }

  private async testOrderExecutionLatency(): Promise<void> {
    this.emit('message', 'Testing order execution latency...');

    const orderTypes: Array<'BUY' | 'SELL'> = ['BUY', 'SELL'];

    for (let i = 0; i < this.testConfig.orderTestCount; i++) {
      const symbol = this.testConfig.symbols[i % this.testConfig.symbols.length];
      const orderType = orderTypes[i % orderTypes.length];

      const order: MT5OrderRequest = {
        symbol,
        volume: 0.01 + (Math.random() * 0.09), // 0.01 to 0.1
        type: orderType,
        comment: `LatencyTest_${i}`
      };

      const { result, latency } = await this.measureLatency(async () => {
        const { success, orderId } = await this.mt5Helper.executeOrder(order);
        if (!success) {
          throw new Error('Order execution failed');
        }
        return orderId;
      });

      this.latencyResults.get('orderExecution')!.push(latency);
      this.metrics.throughput.totalRequests++;

      // Small delay between orders to avoid overwhelming the system
      await new Promise(resolve => setTimeout(resolve, 50));

      this.emit('progress', {
        operation: 'orderExecution',
        completed: i + 1,
        total: this.testConfig.orderTestCount,
        latency: latency.toFixed(2)
      });
    }
  }

  private async testTickDataLatency(): Promise<void> {
    this.emit('message', 'Testing tick data retrieval latency...');

    for (let i = 0; i < this.testConfig.tickDataTestCount; i++) {
      const symbol = this.testConfig.symbols[i % this.testConfig.symbols.length];

      const { result, latency } = await this.measureLatency(async () => {
        const { success, tick } = await this.mt5Helper.getTickData(symbol);
        if (!success) {
          throw new Error('Tick data retrieval failed');
        }
        return tick;
      });

      this.latencyResults.get('tickData')!.push(latency);
      this.metrics.throughput.totalRequests++;

      // Very small delay for tick data
      await new Promise(resolve => setTimeout(resolve, 10));

      if (i % 50 === 0) { // Report progress every 50 requests
        this.emit('progress', {
          operation: 'tickData',
          completed: i + 1,
          total: this.testConfig.tickDataTestCount,
          latency: latency.toFixed(2)
        });
      }
    }
  }

  private async testAccountInfoLatency(): Promise<void> {
    this.emit('message', 'Testing account info retrieval latency...');

    for (let i = 0; i < this.testConfig.accountInfoTestCount; i++) {
      const { result, latency } = await this.measureLatency(async () => {
        return await this.mt5Helper.getAccountInfo();
      });

      this.latencyResults.get('accountInfo')!.push(latency);
      this.metrics.throughput.totalRequests++;

      await new Promise(resolve => setTimeout(resolve, 100));

      this.emit('progress', {
        operation: 'accountInfo',
        completed: i + 1,
        total: this.testConfig.accountInfoTestCount,
        latency: latency.toFixed(2)
      });
    }
  }

  private async testPositionInfoLatency(): Promise<void> {
    this.emit('message', 'Testing position info retrieval latency...');

    for (let i = 0; i < this.testConfig.accountInfoTestCount; i++) {
      const { result, latency } = await this.measureLatency(async () => {
        return await this.mt5Helper.getPositions();
      });

      this.latencyResults.get('positionInfo')!.push(latency);
      this.metrics.throughput.totalRequests++;

      await new Promise(resolve => setTimeout(resolve, 100));

      this.emit('progress', {
        operation: 'positionInfo',
        completed: i + 1,
        total: this.testConfig.accountInfoTestCount,
        latency: latency.toFixed(2)
      });
    }
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting cooldown...');

    // Close MT5 connection
    await this.mt5Helper.closeConnection();

    // Calculate detailed latency statistics for each operation
    this.calculateDetailedLatencyStats();

    this.emit('message', 'Cooldown completed');
  }

  private calculateDetailedLatencyStats(): void {
    const detailedStats: any = {};

    for (const [operation, latencies] of this.latencyResults) {
      if (latencies.length === 0) continue;

      const sorted = [...latencies].sort((a, b) => a - b);
      detailedStats[operation] = {
        count: latencies.length,
        min: Math.min(...latencies),
        max: Math.max(...latencies),
        avg: latencies.reduce((a, b) => a + b, 0) / latencies.length,
        p50: this.getPercentile(sorted, 0.5),
        p75: this.getPercentile(sorted, 0.75),
        p90: this.getPercentile(sorted, 0.9),
        p95: this.getPercentile(sorted, 0.95),
        p99: this.getPercentile(sorted, 0.99),
        standardDeviation: this.calculateStandardDeviation(latencies)
      };
    }

    // Store detailed stats in the metrics object
    (this.metrics as any).detailedLatencyStats = detailedStats;

    this.emit('detailedStats', detailedStats);
  }

  private getPercentile(sorted: number[], percentile: number): number {
    const index = Math.ceil(sorted.length * percentile) - 1;
    return sorted[Math.max(0, index)];
  }

  private calculateStandardDeviation(values: number[]): number {
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => Math.pow(value - avg, 2));
    const avgSquaredDiff = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
    return Math.sqrt(avgSquaredDiff);
  }

  public getLatencyResultsByOperation(): Map<string, number[]> {
    return new Map(this.latencyResults);
  }

  public generateLatencyReport(): string {
    const stats = (this.metrics as any).detailedLatencyStats || {};
    let report = '# MT5 Latency Test Report\n\n';

    for (const [operation, data] of Object.entries(stats)) {
      const operationData = data as any;
      report += `## ${operation.charAt(0).toUpperCase() + operation.slice(1)} Latency\n\n`;
      report += `- **Samples:** ${operationData.count}\n`;
      report += `- **Min:** ${operationData.min.toFixed(2)}ms\n`;
      report += `- **Max:** ${operationData.max.toFixed(2)}ms\n`;
      report += `- **Average:** ${operationData.avg.toFixed(2)}ms\n`;
      report += `- **P50:** ${operationData.p50.toFixed(2)}ms\n`;
      report += `- **P75:** ${operationData.p75.toFixed(2)}ms\n`;
      report += `- **P90:** ${operationData.p90.toFixed(2)}ms\n`;
      report += `- **P95:** ${operationData.p95.toFixed(2)}ms\n`;
      report += `- **P99:** ${operationData.p99.toFixed(2)}ms\n`;
      report += `- **Std Dev:** ${operationData.standardDeviation.toFixed(2)}ms\n\n`;

      // Performance assessment
      if (operationData.p95 < 100) {
        report += '✅ **Excellent latency performance**\n\n';
      } else if (operationData.p95 < 250) {
        report += '⚠️ **Good latency performance**\n\n';
      } else if (operationData.p95 < 500) {
        report += '⚠️ **Acceptable latency performance**\n\n';
      } else {
        report += '❌ **Poor latency performance - optimization needed**\n\n';
      }
    }

    return report;
  }
}