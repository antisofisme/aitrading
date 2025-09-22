import { performance } from 'perf_hooks';
import * as os from 'os';
import { EventEmitter } from 'events';

export interface PerformanceMetrics {
  latency: {
    min: number;
    max: number;
    avg: number;
    p50: number;
    p95: number;
    p99: number;
    samples: number[];
  };
  throughput: {
    requestsPerSecond: number;
    totalRequests: number;
    duration: number;
  };
  memory: {
    heapUsed: number;
    heapTotal: number;
    external: number;
    rss: number;
    arrayBuffers: number;
  };
  cpu: {
    usage: number;
    loadAverage: number[];
  };
  errors: {
    count: number;
    types: Record<string, number>;
  };
}

export interface TestConfig {
  duration: number; // Test duration in milliseconds
  concurrency: number; // Number of concurrent operations
  warmupTime: number; // Warmup period in milliseconds
  cooldownTime: number; // Cooldown period in milliseconds
  sampleInterval: number; // Metrics collection interval
  maxMemoryUsage: number; // Memory threshold in MB
  maxLatency: number; // Latency threshold in ms
  minThroughput: number; // Minimum required throughput
}

export abstract class PerformanceTestBase extends EventEmitter {
  protected metrics: PerformanceMetrics;
  protected config: TestConfig;
  protected startTime: number = 0;
  protected endTime: number = 0;
  protected isRunning: boolean = false;
  protected samples: number[] = [];
  protected errors: Map<string, number> = new Map();
  protected memoryMonitorInterval?: NodeJS.Timeout;

  constructor(config: Partial<TestConfig> = {}) {
    super();
    this.config = {
      duration: 60000, // 1 minute default
      concurrency: 10,
      warmupTime: 5000,
      cooldownTime: 2000,
      sampleInterval: 1000,
      maxMemoryUsage: 512, // MB
      maxLatency: 1000, // ms
      minThroughput: 100, // requests/second
      ...config
    };

    this.initializeMetrics();
  }

  private initializeMetrics(): void {
    this.metrics = {
      latency: {
        min: Infinity,
        max: 0,
        avg: 0,
        p50: 0,
        p95: 0,
        p99: 0,
        samples: []
      },
      throughput: {
        requestsPerSecond: 0,
        totalRequests: 0,
        duration: 0
      },
      memory: {
        heapUsed: 0,
        heapTotal: 0,
        external: 0,
        rss: 0,
        arrayBuffers: 0
      },
      cpu: {
        usage: 0,
        loadAverage: []
      },
      errors: {
        count: 0,
        types: {}
      }
    };
  }

  protected async measureLatency<T>(operation: () => Promise<T>): Promise<{ result: T; latency: number }> {
    const start = performance.now();
    try {
      const result = await operation();
      const latency = performance.now() - start;
      this.recordLatency(latency);
      return { result, latency };
    } catch (error) {
      const latency = performance.now() - start;
      this.recordError(error);
      throw error;
    }
  }

  protected recordLatency(latency: number): void {
    this.samples.push(latency);
    this.metrics.latency.samples.push(latency);
    this.metrics.latency.min = Math.min(this.metrics.latency.min, latency);
    this.metrics.latency.max = Math.max(this.metrics.latency.max, latency);
  }

  protected recordError(error: any): void {
    this.metrics.errors.count++;
    const errorType = error.constructor.name || 'Unknown';
    this.metrics.errors.types[errorType] = (this.metrics.errors.types[errorType] || 0) + 1;
  }

  protected calculatePercentiles(): void {
    const sorted = [...this.samples].sort((a, b) => a - b);
    const len = sorted.length;

    if (len === 0) return;

    this.metrics.latency.avg = sorted.reduce((a, b) => a + b, 0) / len;
    this.metrics.latency.p50 = this.getPercentile(sorted, 0.5);
    this.metrics.latency.p95 = this.getPercentile(sorted, 0.95);
    this.metrics.latency.p99 = this.getPercentile(sorted, 0.99);
  }

  private getPercentile(sorted: number[], percentile: number): number {
    const index = Math.ceil(sorted.length * percentile) - 1;
    return sorted[Math.max(0, index)];
  }

  protected startMemoryMonitoring(): void {
    this.memoryMonitorInterval = setInterval(() => {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();

      this.metrics.memory = {
        heapUsed: memUsage.heapUsed / 1024 / 1024, // MB
        heapTotal: memUsage.heapTotal / 1024 / 1024,
        external: memUsage.external / 1024 / 1024,
        rss: memUsage.rss / 1024 / 1024,
        arrayBuffers: memUsage.arrayBuffers / 1024 / 1024
      };

      this.metrics.cpu = {
        usage: (cpuUsage.user + cpuUsage.system) / 1000, // microseconds to milliseconds
        loadAverage: os.loadavg()
      };

      // Check memory threshold
      if (this.metrics.memory.heapUsed > this.config.maxMemoryUsage) {
        this.emit('memoryThresholdExceeded', this.metrics.memory);
      }

      this.emit('metricsUpdate', this.metrics);
    }, this.config.sampleInterval);
  }

  protected stopMemoryMonitoring(): void {
    if (this.memoryMonitorInterval) {
      clearInterval(this.memoryMonitorInterval);
      this.memoryMonitorInterval = undefined;
    }
  }

  protected calculateThroughput(): void {
    const duration = this.endTime - this.startTime;
    this.metrics.throughput = {
      requestsPerSecond: (this.metrics.throughput.totalRequests / duration) * 1000,
      totalRequests: this.metrics.throughput.totalRequests,
      duration
    };
  }

  public async run(): Promise<PerformanceMetrics> {
    this.emit('testStarting', this.config);

    // Warmup phase
    if (this.config.warmupTime > 0) {
      this.emit('warmupStarting');
      await this.warmup();
      this.emit('warmupCompleted');
    }

    // Start monitoring
    this.startMemoryMonitoring();
    this.isRunning = true;
    this.startTime = performance.now();

    try {
      // Execute test
      this.emit('testExecutionStarting');
      await this.executeTest();
      this.emit('testExecutionCompleted');
    } finally {
      this.endTime = performance.now();
      this.isRunning = false;
      this.stopMemoryMonitoring();
    }

    // Cooldown phase
    if (this.config.cooldownTime > 0) {
      this.emit('cooldownStarting');
      await this.cooldown();
      this.emit('cooldownCompleted');
    }

    // Calculate final metrics
    this.calculatePercentiles();
    this.calculateThroughput();

    this.emit('testCompleted', this.metrics);
    return this.metrics;
  }

  // Abstract methods to be implemented by specific test classes
  protected abstract warmup(): Promise<void>;
  protected abstract executeTest(): Promise<void>;
  protected abstract cooldown(): Promise<void>;

  public getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  public isTestRunning(): boolean {
    return this.isRunning;
  }

  // Utility method to validate performance thresholds
  public validateThresholds(): { passed: boolean; violations: string[] } {
    const violations: string[] = [];

    if (this.metrics.latency.p95 > this.config.maxLatency) {
      violations.push(`P95 latency (${this.metrics.latency.p95}ms) exceeds threshold (${this.config.maxLatency}ms)`);
    }

    if (this.metrics.throughput.requestsPerSecond < this.config.minThroughput) {
      violations.push(`Throughput (${this.metrics.throughput.requestsPerSecond} req/s) below threshold (${this.config.minThroughput} req/s)`);
    }

    if (this.metrics.memory.heapUsed > this.config.maxMemoryUsage) {
      violations.push(`Memory usage (${this.metrics.memory.heapUsed}MB) exceeds threshold (${this.config.maxMemoryUsage}MB)`);
    }

    return {
      passed: violations.length === 0,
      violations
    };
  }
}

export class PerformanceTestRunner {
  private tests: Map<string, PerformanceTestBase> = new Map();
  private results: Map<string, PerformanceMetrics> = new Map();

  public addTest(name: string, test: PerformanceTestBase): void {
    this.tests.set(name, test);
  }

  public async runAll(): Promise<Map<string, PerformanceMetrics>> {
    const promises = Array.from(this.tests.entries()).map(async ([name, test]) => {
      try {
        const metrics = await test.run();
        this.results.set(name, metrics);
        return { name, success: true, metrics };
      } catch (error) {
        console.error(`Test ${name} failed:`, error);
        return { name, success: false, error };
      }
    });

    await Promise.all(promises);
    return this.results;
  }

  public async runTest(name: string): Promise<PerformanceMetrics> {
    const test = this.tests.get(name);
    if (!test) {
      throw new Error(`Test ${name} not found`);
    }

    const metrics = await test.run();
    this.results.set(name, metrics);
    return metrics;
  }

  public getResults(): Map<string, PerformanceMetrics> {
    return new Map(this.results);
  }

  public generateReport(): string {
    let report = '# Performance Test Report\n\n';

    for (const [name, metrics] of this.results) {
      report += `## ${name}\n\n`;
      report += `**Latency:**\n`;
      report += `- Min: ${metrics.latency.min.toFixed(2)}ms\n`;
      report += `- Max: ${metrics.latency.max.toFixed(2)}ms\n`;
      report += `- Avg: ${metrics.latency.avg.toFixed(2)}ms\n`;
      report += `- P50: ${metrics.latency.p50.toFixed(2)}ms\n`;
      report += `- P95: ${metrics.latency.p95.toFixed(2)}ms\n`;
      report += `- P99: ${metrics.latency.p99.toFixed(2)}ms\n\n`;

      report += `**Throughput:**\n`;
      report += `- ${metrics.throughput.requestsPerSecond.toFixed(2)} req/s\n`;
      report += `- ${metrics.throughput.totalRequests} total requests\n`;
      report += `- ${(metrics.throughput.duration / 1000).toFixed(2)}s duration\n\n`;

      report += `**Memory:**\n`;
      report += `- Heap Used: ${metrics.memory.heapUsed.toFixed(2)}MB\n`;
      report += `- RSS: ${metrics.memory.rss.toFixed(2)}MB\n\n`;

      if (metrics.errors.count > 0) {
        report += `**Errors:** ${metrics.errors.count}\n\n`;
      }
    }

    return report;
  }
}