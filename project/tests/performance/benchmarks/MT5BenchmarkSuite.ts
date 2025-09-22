import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig } from '../infrastructure/MT5TestHelper';

export interface BenchmarkConfig extends TestConfig {
  benchmarkSuites: BenchmarkSuite[];
  iterations: number;
  warmupIterations: number;
  statisticalSignificance: number; // p-value threshold
  baselineComparison: boolean;
  exportResults: boolean;
}

export interface BenchmarkSuite {
  name: string;
  description: string;
  benchmarks: Benchmark[];
  targetBaseline?: BenchmarkBaseline;
}

export interface Benchmark {
  name: string;
  operation: BenchmarkOperation;
  expectedLatency: number; // Expected latency in ms
  acceptableVariance: number; // Acceptable variance percentage
  parameters?: any;
}

export interface BenchmarkOperation {
  type: 'order_execution' | 'tick_retrieval' | 'account_query' | 'position_query' | 'connection_setup' | 'bulk_operations';
  setup?: () => Promise<void>;
  execute: (helper: MT5TestHelper, params?: any) => Promise<any>;
  cleanup?: () => Promise<void>;
}

export interface BenchmarkBaseline {
  version: string;
  timestamp: number;
  results: Map<string, BenchmarkResult>;
}

export interface BenchmarkResult {
  benchmarkName: string;
  iterations: number;
  statistics: {
    min: number;
    max: number;
    mean: number;
    median: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
    standardDeviation: number;
    variance: number;
  };
  performance: {
    meetsTarget: boolean;
    varianceAcceptable: boolean;
    performanceScore: number; // 0-100
    grade: 'A' | 'B' | 'C' | 'D' | 'F';
  };
  rawData: number[];
}

export class MT5BenchmarkSuite extends PerformanceTestBase {
  private mt5Helper: MT5TestHelper;
  private testConfig: BenchmarkConfig;
  private benchmarkResults: Map<string, BenchmarkResult> = new Map();
  private baseline?: BenchmarkBaseline;

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<BenchmarkConfig> = {}
  ) {
    const config: BenchmarkConfig = {
      duration: 1800000, // 30 minutes
      concurrency: 1, // Benchmarks are sequential
      warmupTime: 30000,
      cooldownTime: 10000,
      sampleInterval: 1000,
      maxMemoryUsage: 512,
      maxLatency: 1000,
      minThroughput: 100,
      benchmarkSuites: [],
      iterations: 1000,
      warmupIterations: 100,
      statisticalSignificance: 0.05,
      baselineComparison: true,
      exportResults: true,
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.mt5Helper = new MT5TestHelper(mt5Config);

    // Initialize default benchmark suites
    this.initializeDefaultBenchmarks();
  }

  private initializeDefaultBenchmarks(): void {
    this.testConfig.benchmarkSuites = [
      {
        name: 'OrderExecutionBenchmarks',
        description: 'Benchmarks for order execution performance',
        benchmarks: [
          {
            name: 'MarketOrderExecution',
            expectedLatency: 50,
            acceptableVariance: 20,
            operation: {
              type: 'order_execution',
              execute: async (helper) => {
                return await helper.executeOrder({
                  symbol: 'EURUSD',
                  volume: 0.01,
                  type: 'BUY',
                  comment: 'BenchmarkMarketOrder'
                });
              }
            }
          },
          {
            name: 'LimitOrderExecution',
            expectedLatency: 75,
            acceptableVariance: 25,
            operation: {
              type: 'order_execution',
              execute: async (helper) => {
                return await helper.executeOrder({
                  symbol: 'EURUSD',
                  volume: 0.01,
                  type: 'BUY_LIMIT',
                  price: 1.0500,
                  comment: 'BenchmarkLimitOrder'
                });
              }
            }
          }
        ]
      },
      {
        name: 'DataRetrievalBenchmarks',
        description: 'Benchmarks for data retrieval operations',
        benchmarks: [
          {
            name: 'SingleTickRetrieval',
            expectedLatency: 10,
            acceptableVariance: 30,
            operation: {
              type: 'tick_retrieval',
              execute: async (helper) => {
                return await helper.getTickData('EURUSD');
              }
            }
          },
          {
            name: 'AccountInfoRetrieval',
            expectedLatency: 30,
            acceptableVariance: 25,
            operation: {
              type: 'account_query',
              execute: async (helper) => {
                return await helper.getAccountInfo();
              }
            }
          },
          {
            name: 'PositionInfoRetrieval',
            expectedLatency: 40,
            acceptableVariance: 30,
            operation: {
              type: 'position_query',
              execute: async (helper) => {
                return await helper.getPositions();
              }
            }
          }
        ]
      },
      {
        name: 'ConnectionBenchmarks',
        description: 'Benchmarks for connection operations',
        benchmarks: [
          {
            name: 'ConnectionSetup',
            expectedLatency: 200,
            acceptableVariance: 40,
            operation: {
              type: 'connection_setup',
              execute: async (helper) => {
                // Close and reconnect to benchmark connection setup
                await helper.closeConnection();
                return await helper.initializeConnection();
              }
            }
          }
        ]
      },
      {
        name: 'BulkOperationBenchmarks',
        description: 'Benchmarks for bulk operations',
        benchmarks: [
          {
            name: 'BulkTickRetrieval',
            expectedLatency: 100,
            acceptableVariance: 35,
            operation: {
              type: 'bulk_operations',
              execute: async (helper) => {
                const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];
                const promises = symbols.map(symbol => helper.getTickData(symbol));
                return await Promise.all(promises);
              }
            }
          }
        ]
      }
    ];
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 benchmark suite warmup...');

    // Initialize MT5 connection
    const { success } = await this.mt5Helper.initializeConnection();
    if (!success) {
      throw new Error('Failed to initialize MT5 connection for benchmarks');
    }

    // Execute warmup iterations for each benchmark
    for (const suite of this.testConfig.benchmarkSuites) {
      for (const benchmark of suite.benchmarks) {
        await this.warmupBenchmark(benchmark);
      }
    }

    this.emit('message', 'Benchmark warmup completed');
  }

  private async warmupBenchmark(benchmark: Benchmark): Promise<void> {
    this.emit('message', `Warming up benchmark: ${benchmark.name}`);

    for (let i = 0; i < this.testConfig.warmupIterations; i++) {
      try {
        await benchmark.operation.execute(this.mt5Helper);
      } catch (error) {
        // Ignore warmup errors
      }
    }
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting benchmark execution...');

    for (const suite of this.testConfig.benchmarkSuites) {
      await this.executeBenchmarkSuite(suite);
    }

    // Compare against baseline if available
    if (this.testConfig.baselineComparison) {
      await this.compareAgainstBaseline();
    }

    this.emit('message', 'Benchmark execution completed');
  }

  private async executeBenchmarkSuite(suite: BenchmarkSuite): Promise<void> {
    this.emit('message', `Executing benchmark suite: ${suite.name}`);

    for (const benchmark of suite.benchmarks) {
      const result = await this.executeBenchmark(benchmark);
      this.benchmarkResults.set(benchmark.name, result);

      this.emit('benchmarkCompleted', {
        name: benchmark.name,
        result: result.statistics,
        performance: result.performance
      });
    }
  }

  private async executeBenchmark(benchmark: Benchmark): Promise<BenchmarkResult> {
    this.emit('message', `Executing benchmark: ${benchmark.name}`);

    const measurements: number[] = [];

    // Setup if needed
    if (benchmark.operation.setup) {
      await benchmark.operation.setup();
    }

    try {
      // Execute benchmark iterations
      for (let i = 0; i < this.testConfig.iterations; i++) {
        const { latency } = await this.measureLatency(() =>
          benchmark.operation.execute(this.mt5Helper, benchmark.parameters)
        );

        measurements.push(latency);

        // Progress reporting every 100 iterations
        if (i % 100 === 0) {
          this.emit('benchmarkProgress', {
            name: benchmark.name,
            completed: i + 1,
            total: this.testConfig.iterations,
            currentLatency: latency.toFixed(2)
          });
        }
      }

      // Calculate statistics
      const statistics = this.calculateStatistics(measurements);

      // Evaluate performance
      const performance = this.evaluatePerformance(benchmark, statistics);

      return {
        benchmarkName: benchmark.name,
        iterations: this.testConfig.iterations,
        statistics,
        performance,
        rawData: measurements
      };

    } finally {
      // Cleanup if needed
      if (benchmark.operation.cleanup) {
        await benchmark.operation.cleanup();
      }
    }
  }

  private calculateStatistics(measurements: number[]): BenchmarkResult['statistics'] {
    const sorted = [...measurements].sort((a, b) => a - b);
    const len = sorted.length;

    const sum = measurements.reduce((a, b) => a + b, 0);
    const mean = sum / len;

    // Calculate variance and standard deviation
    const squaredDiffs = measurements.map(x => Math.pow(x - mean, 2));
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / len;
    const standardDeviation = Math.sqrt(variance);

    return {
      min: sorted[0],
      max: sorted[len - 1],
      mean,
      median: this.getPercentile(sorted, 0.5),
      p75: this.getPercentile(sorted, 0.75),
      p90: this.getPercentile(sorted, 0.90),
      p95: this.getPercentile(sorted, 0.95),
      p99: this.getPercentile(sorted, 0.99),
      standardDeviation,
      variance
    };
  }

  private getPercentile(sorted: number[], percentile: number): number {
    const index = Math.ceil(sorted.length * percentile) - 1;
    return sorted[Math.max(0, index)];
  }

  private evaluatePerformance(
    benchmark: Benchmark,
    statistics: BenchmarkResult['statistics']
  ): BenchmarkResult['performance'] {
    const meetsTarget = statistics.p95 <= benchmark.expectedLatency;
    const actualVariance = (statistics.standardDeviation / statistics.mean) * 100;
    const varianceAcceptable = actualVariance <= benchmark.acceptableVariance;

    // Calculate performance score (0-100)
    let performanceScore = 100;

    // Penalty for exceeding target latency
    if (statistics.p95 > benchmark.expectedLatency) {
      const overage = (statistics.p95 - benchmark.expectedLatency) / benchmark.expectedLatency;
      performanceScore -= Math.min(50, overage * 100);
    }

    // Penalty for high variance
    if (actualVariance > benchmark.acceptableVariance) {
      const varianceOverage = (actualVariance - benchmark.acceptableVariance) / benchmark.acceptableVariance;
      performanceScore -= Math.min(30, varianceOverage * 50);
    }

    // Bonus for beating target significantly
    if (statistics.p95 < benchmark.expectedLatency * 0.8) {
      performanceScore += 10;
    }

    performanceScore = Math.max(0, Math.min(100, performanceScore));

    // Assign grade
    let grade: 'A' | 'B' | 'C' | 'D' | 'F';
    if (performanceScore >= 90) grade = 'A';
    else if (performanceScore >= 80) grade = 'B';
    else if (performanceScore >= 70) grade = 'C';
    else if (performanceScore >= 60) grade = 'D';
    else grade = 'F';

    return {
      meetsTarget,
      varianceAcceptable,
      performanceScore,
      grade
    };
  }

  private async compareAgainstBaseline(): Promise<void> {
    if (!this.baseline) {
      this.emit('message', 'No baseline available for comparison');
      return;
    }

    this.emit('message', 'Comparing results against baseline...');

    const comparisons: Map<string, any> = new Map();

    for (const [benchmarkName, currentResult] of this.benchmarkResults) {
      const baselineResult = this.baseline.results.get(benchmarkName);
      if (!baselineResult) continue;

      const comparison = {
        benchmarkName,
        current: currentResult.statistics,
        baseline: baselineResult.statistics,
        improvement: {
          mean: ((baselineResult.statistics.mean - currentResult.statistics.mean) / baselineResult.statistics.mean) * 100,
          p95: ((baselineResult.statistics.p95 - currentResult.statistics.p95) / baselineResult.statistics.p95) * 100,
          variance: ((baselineResult.statistics.variance - currentResult.statistics.variance) / baselineResult.statistics.variance) * 100
        },
        significance: this.calculateStatisticalSignificance(currentResult, baselineResult)
      };

      comparisons.set(benchmarkName, comparison);
    }

    this.emit('baselineComparison', Array.from(comparisons.values()));
  }

  private calculateStatisticalSignificance(
    current: BenchmarkResult,
    baseline: BenchmarkResult
  ): { significant: boolean; pValue: number } {
    // Simplified t-test for demonstration
    // In production, use proper statistical library
    const n1 = current.rawData.length;
    const n2 = baseline.rawData.length;

    const mean1 = current.statistics.mean;
    const mean2 = baseline.statistics.mean;

    const var1 = current.statistics.variance;
    const var2 = baseline.statistics.variance;

    // Pooled variance
    const pooledVar = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2);
    const standardError = Math.sqrt(pooledVar * (1/n1 + 1/n2));

    const tStat = Math.abs(mean1 - mean2) / standardError;

    // Simplified p-value calculation (should use proper t-distribution)
    const pValue = Math.exp(-tStat * tStat / 2) / Math.sqrt(2 * Math.PI);

    return {
      significant: pValue < this.testConfig.statisticalSignificance,
      pValue
    };
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting benchmark cooldown...');

    // Close MT5 connection
    await this.mt5Helper.closeConnection();

    // Export results if configured
    if (this.testConfig.exportResults) {
      await this.exportBenchmarkResults();
    }

    this.emit('message', 'Benchmark cooldown completed');
  }

  private async exportBenchmarkResults(): Promise<void> {
    const results = {
      timestamp: Date.now(),
      version: process.env.npm_package_version || '1.0.0',
      configuration: {
        iterations: this.testConfig.iterations,
        warmupIterations: this.testConfig.warmupIterations
      },
      results: Array.from(this.benchmarkResults.entries()).map(([name, result]) => ({
        name,
        ...result
      }))
    };

    // Store results in memory for team access via hooks
    try {
      const { exec } = require('child_process');
      const { promisify } = require('util');
      const execAsync = promisify(exec);

      await execAsync(`npx claude-flow@alpha hooks post-edit --memory-key "performance/benchmarks/results" --value '${JSON.stringify(results)}'`);
      this.emit('message', 'Benchmark results exported to team memory');
    } catch (error) {
      this.emit('exportError', error);
    }
  }

  public getBenchmarkResults(): Map<string, BenchmarkResult> {
    return new Map(this.benchmarkResults);
  }

  public setBaseline(baseline: BenchmarkBaseline): void {
    this.baseline = baseline;
  }

  public generateBenchmarkReport(): string {
    let report = '# MT5 Performance Benchmark Report\n\n';

    report += `**Test Configuration:**\n`;
    report += `- Iterations: ${this.testConfig.iterations.toLocaleString()}\n`;
    report += `- Warmup Iterations: ${this.testConfig.warmupIterations.toLocaleString()}\n`;
    report += `- Timestamp: ${new Date().toISOString()}\n\n`;

    for (const suite of this.testConfig.benchmarkSuites) {
      report += `## ${suite.name}\n\n`;
      report += `${suite.description}\n\n`;

      for (const benchmark of suite.benchmarks) {
        const result = this.benchmarkResults.get(benchmark.name);
        if (!result) continue;

        report += `### ${benchmark.name}\n\n`;
        report += `**Target:** ${benchmark.expectedLatency}ms (±${benchmark.acceptableVariance}%)\n\n`;

        report += `**Results:**\n`;
        report += `- Mean: ${result.statistics.mean.toFixed(2)}ms\n`;
        report += `- Median: ${result.statistics.median.toFixed(2)}ms\n`;
        report += `- P95: ${result.statistics.p95.toFixed(2)}ms\n`;
        report += `- P99: ${result.statistics.p99.toFixed(2)}ms\n`;
        report += `- Std Dev: ${result.statistics.standardDeviation.toFixed(2)}ms\n\n`;

        report += `**Performance:**\n`;
        report += `- Score: ${result.performance.performanceScore.toFixed(1)}/100\n`;
        report += `- Grade: ${result.performance.grade}\n`;
        report += `- Meets Target: ${result.performance.meetsTarget ? '✅' : '❌'}\n`;
        report += `- Variance OK: ${result.performance.varianceAcceptable ? '✅' : '❌'}\n\n`;
      }
    }

    return report;
  }
}