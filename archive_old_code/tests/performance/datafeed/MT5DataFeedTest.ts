import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5TickData } from '../infrastructure/MT5TestHelper';

export interface DataFeedTestConfig extends TestConfig {
  symbols: string[];
  dataFeedPatterns: DataFeedPattern[];
  tickProcessingTargets: {
    ticksPerSecond: number;
    maxLatency: number;
    maxMissedTicks: number;
    bufferSize: number;
  };
  realtimeSimulation: {
    enabled: boolean;
    marketHours: boolean;
    weekendMode: boolean;
    volatilitySimulation: boolean;
  };
}

export interface DataFeedPattern {
  name: string;
  description: string;
  symbols: string[];
  frequency: number; // milliseconds between requests
  duration: number; // pattern duration in milliseconds
  concurrent: boolean;
  expectedThroughput: number; // ticks per second
}

export interface TickProcessingMetrics {
  symbol: string;
  ticksReceived: number;
  ticksMissed: number;
  averageLatency: number;
  maxLatency: number;
  processingRate: number; // ticks per second
  bufferOverflows: number;
  dataQuality: number; // 0-100 score
}

export class MT5DataFeedTest extends PerformanceTestBase {
  private mt5Helper: MT5TestHelper;
  private testConfig: DataFeedTestConfig;
  private dataFeedMetrics: Map<string, TickProcessingMetrics> = new Map();
  private tickBuffers: Map<string, MT5TickData[]> = new Map();
  private activeStreams: Map<string, boolean> = new Map();
  private streamStartTimes: Map<string, number> = new Map();

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<DataFeedTestConfig> = {}
  ) {
    const config: DataFeedTestConfig = {
      duration: 1200000, // 20 minutes
      concurrency: 50,
      warmupTime: 60000,
      cooldownTime: 30000,
      sampleInterval: 2000,
      maxMemoryUsage: 1024,
      maxLatency: 100, // 100ms for data feed
      minThroughput: 500,
      symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD', 'EURJPY', 'GBPJPY', 'EURGBP'],
      dataFeedPatterns: [],
      tickProcessingTargets: {
        ticksPerSecond: 100,
        maxLatency: 50,
        maxMissedTicks: 5, // 5% max
        bufferSize: 1000
      },
      realtimeSimulation: {
        enabled: true,
        marketHours: true,
        weekendMode: false,
        volatilitySimulation: true
      },
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.mt5Helper = new MT5TestHelper(mt5Config);

    this.initializeDataFeedPatterns();
    this.initializeTickBuffers();
  }

  private initializeDataFeedPatterns(): void {
    this.testConfig.dataFeedPatterns = [
      {
        name: 'LowFrequencyMonitoring',
        description: 'Low frequency monitoring for all symbols',
        symbols: this.testConfig.symbols,
        frequency: 1000, // 1 second
        duration: 300000, // 5 minutes
        concurrent: false,
        expectedThroughput: 8 // 8 symbols per second
      },
      {
        name: 'HighFrequencyTrading',
        description: 'High frequency tick streaming for major pairs',
        symbols: ['EURUSD', 'GBPUSD', 'USDJPY'],
        frequency: 100, // 100ms
        duration: 600000, // 10 minutes
        concurrent: true,
        expectedThroughput: 30 // 30 ticks per second
      },
      {
        name: 'ScalpingPattern',
        description: 'Ultra-high frequency for scalping strategies',
        symbols: ['EURUSD'],
        frequency: 50, // 50ms
        duration: 180000, // 3 minutes
        concurrent: false,
        expectedThroughput: 20 // 20 ticks per second
      },
      {
        name: 'MultiSymbolStream',
        description: 'Concurrent streaming of all symbols',
        symbols: this.testConfig.symbols,
        frequency: 200, // 200ms
        duration: 480000, // 8 minutes
        concurrent: true,
        expectedThroughput: 40 // 40 ticks per second total
      },
      {
        name: 'BurstPattern',
        description: 'Burst requests to test buffer handling',
        symbols: ['EURUSD', 'GBPUSD'],
        frequency: 10, // 10ms bursts
        duration: 120000, // 2 minutes
        concurrent: true,
        expectedThroughput: 100 // 100 ticks per second
      }
    ];
  }

  private initializeTickBuffers(): void {
    for (const symbol of this.testConfig.symbols) {
      this.tickBuffers.set(symbol, []);
      this.dataFeedMetrics.set(symbol, {
        symbol,
        ticksReceived: 0,
        ticksMissed: 0,
        averageLatency: 0,
        maxLatency: 0,
        processingRate: 0,
        bufferOverflows: 0,
        dataQuality: 100
      });
      this.activeStreams.set(symbol, false);
    }
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 data feed test warmup...');

    // Initialize MT5 connection
    const { success } = await this.mt5Helper.initializeConnection();
    if (!success) {
      throw new Error('Failed to initialize MT5 connection for data feed test');
    }

    // Warmup each symbol with a few tick requests
    for (const symbol of this.testConfig.symbols) {
      for (let i = 0; i < 10; i++) {
        try {
          await this.mt5Helper.getTickData(symbol);
        } catch (error) {
          // Ignore warmup errors
        }
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    this.emit('message', 'Data feed test warmup completed');
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting data feed test execution...');

    // Start buffer monitoring
    const bufferMonitoringPromise = this.startBufferMonitoring();

    // Execute data feed patterns sequentially to avoid interference
    for (const pattern of this.testConfig.dataFeedPatterns) {
      await this.executeDataFeedPattern(pattern);

      // Brief pause between patterns
      await new Promise(resolve => setTimeout(resolve, 5000));
    }

    // Stop buffer monitoring
    this.isRunning = false;
    await bufferMonitoringPromise;

    this.emit('message', 'Data feed test execution completed');
  }

  private async startBufferMonitoring(): Promise<void> {
    while (this.isRunning) {
      // Monitor buffer sizes and quality
      for (const [symbol, buffer] of this.tickBuffers) {
        const metrics = this.dataFeedMetrics.get(symbol)!;

        // Check for buffer overflow
        if (buffer.length > this.testConfig.tickProcessingTargets.bufferSize) {
          metrics.bufferOverflows++;

          // Remove oldest entries to prevent memory issues
          this.tickBuffers.set(symbol, buffer.slice(-this.testConfig.tickProcessingTargets.bufferSize / 2));

          this.emit('bufferOverflow', {
            symbol,
            bufferSize: buffer.length,
            threshold: this.testConfig.tickProcessingTargets.bufferSize
          });
        }

        // Calculate processing rate
        const activeTime = this.streamStartTimes.get(symbol);
        if (activeTime) {
          const elapsed = (performance.now() - activeTime) / 1000; // seconds
          metrics.processingRate = metrics.ticksReceived / elapsed;
        }

        // Update data quality score
        metrics.dataQuality = this.calculateDataQuality(metrics);
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  private async executeDataFeedPattern(pattern: DataFeedPattern): Promise<void> {
    this.emit('message', `Executing data feed pattern: ${pattern.name}`);

    const startTime = performance.now();

    if (pattern.concurrent) {
      await this.executeConcurrentPattern(pattern);
    } else {
      await this.executeSequentialPattern(pattern);
    }

    const duration = performance.now() - startTime;

    this.emit('patternCompleted', {
      name: pattern.name,
      duration: duration.toFixed(2),
      expectedThroughput: pattern.expectedThroughput,
      actualThroughput: this.calculatePatternThroughput(pattern, duration)
    });
  }

  private async executeConcurrentPattern(pattern: DataFeedPattern): Promise<void> {
    // Mark streams as active
    for (const symbol of pattern.symbols) {
      this.activeStreams.set(symbol, true);
      this.streamStartTimes.set(symbol, performance.now());
    }

    // Start concurrent tick streams
    const streamPromises = pattern.symbols.map(symbol =>
      this.executeTickStream(symbol, pattern.frequency, pattern.duration)
    );

    await Promise.all(streamPromises);

    // Mark streams as inactive
    for (const symbol of pattern.symbols) {
      this.activeStreams.set(symbol, false);
    }
  }

  private async executeSequentialPattern(pattern: DataFeedPattern): Promise<void> {
    const endTime = performance.now() + pattern.duration;

    while (performance.now() < endTime && this.isRunning) {
      for (const symbol of pattern.symbols) {
        if (performance.now() >= endTime) break;

        await this.requestTick(symbol);
        await new Promise(resolve => setTimeout(resolve, pattern.frequency));
      }
    }
  }

  private async executeTickStream(symbol: string, frequency: number, duration: number): Promise<void> {
    const endTime = performance.now() + duration;

    while (performance.now() < endTime && this.isRunning && this.activeStreams.get(symbol)) {
      await this.requestTick(symbol);
      await new Promise(resolve => setTimeout(resolve, frequency));
    }
  }

  private async requestTick(symbol: string): Promise<void> {
    const requestStartTime = performance.now();

    try {
      const { success, latency, tick } = await this.mt5Helper.getTickData(symbol);
      const metrics = this.dataFeedMetrics.get(symbol)!;

      if (success && tick) {
        // Record successful tick
        metrics.ticksReceived++;
        this.metrics.throughput.totalRequests++;

        // Update latency metrics
        metrics.maxLatency = Math.max(metrics.maxLatency, latency);

        // Calculate running average latency
        const totalLatency = metrics.averageLatency * (metrics.ticksReceived - 1) + latency;
        metrics.averageLatency = totalLatency / metrics.ticksReceived;

        // Store tick in buffer
        const buffer = this.tickBuffers.get(symbol)!;
        buffer.push({
          ...tick,
          time: Date.now() // Add processing timestamp
        });

        // Check latency threshold
        if (latency > this.testConfig.tickProcessingTargets.maxLatency) {
          this.emit('latencyThresholdExceeded', {
            symbol,
            latency: latency.toFixed(2),
            threshold: this.testConfig.tickProcessingTargets.maxLatency
          });
        }

        this.recordLatency(latency);

      } else {
        // Record missed tick
        metrics.ticksMissed++;
        this.recordError(new Error(`Failed to retrieve tick for ${symbol}`));
      }

    } catch (error) {
      const metrics = this.dataFeedMetrics.get(symbol)!;
      metrics.ticksMissed++;
      this.recordError(error);
    }
  }

  private calculatePatternThroughput(pattern: DataFeedPattern, duration: number): number {
    const totalTicks = pattern.symbols.reduce((total, symbol) => {
      const metrics = this.dataFeedMetrics.get(symbol);
      return total + (metrics ? metrics.ticksReceived : 0);
    }, 0);

    return (totalTicks / duration) * 1000; // ticks per second
  }

  private calculateDataQuality(metrics: TickProcessingMetrics): number {
    const totalAttempts = metrics.ticksReceived + metrics.ticksMissed;
    if (totalAttempts === 0) return 100;

    const successRate = (metrics.ticksReceived / totalAttempts) * 100;
    const latencyPenalty = Math.min(20, (metrics.averageLatency / this.testConfig.tickProcessingTargets.maxLatency) * 10);
    const bufferPenalty = Math.min(10, metrics.bufferOverflows * 2);

    return Math.max(0, successRate - latencyPenalty - bufferPenalty);
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting data feed test cooldown...');

    // Stop all active streams
    for (const symbol of this.testConfig.symbols) {
      this.activeStreams.set(symbol, false);
    }

    // Clear tick buffers
    for (const symbol of this.testConfig.symbols) {
      this.tickBuffers.set(symbol, []);
    }

    // Close MT5 connection
    await this.mt5Helper.closeConnection();

    // Generate data feed analysis
    this.generateDataFeedAnalysis();

    this.emit('message', 'Data feed test cooldown completed');
  }

  private generateDataFeedAnalysis(): void {
    const analysis = {
      overall: {
        totalTicks: Array.from(this.dataFeedMetrics.values()).reduce((sum, m) => sum + m.ticksReceived, 0),
        totalMissed: Array.from(this.dataFeedMetrics.values()).reduce((sum, m) => sum + m.ticksMissed, 0),
        averageQuality: Array.from(this.dataFeedMetrics.values()).reduce((sum, m) => sum + m.dataQuality, 0) / this.dataFeedMetrics.size,
        patterns: {}
      },
      symbolAnalysis: {},
      performance: {
        meetsTargets: true,
        issues: [] as string[]
      }
    };

    // Analyze each symbol
    for (const [symbol, metrics] of this.dataFeedMetrics) {
      const missRate = (metrics.ticksMissed / Math.max(1, metrics.ticksReceived + metrics.ticksMissed)) * 100;

      analysis.symbolAnalysis[symbol] = {
        ticksReceived: metrics.ticksReceived,
        missRate: missRate.toFixed(2),
        averageLatency: metrics.averageLatency.toFixed(2),
        maxLatency: metrics.maxLatency.toFixed(2),
        processingRate: metrics.processingRate.toFixed(2),
        dataQuality: metrics.dataQuality.toFixed(1),
        bufferOverflows: metrics.bufferOverflows
      };

      // Check performance targets
      if (missRate > this.testConfig.tickProcessingTargets.maxMissedTicks) {
        analysis.performance.meetsTargets = false;
        analysis.performance.issues.push(`${symbol}: High miss rate (${missRate.toFixed(1)}%)`);
      }

      if (metrics.averageLatency > this.testConfig.tickProcessingTargets.maxLatency) {
        analysis.performance.meetsTargets = false;
        analysis.performance.issues.push(`${symbol}: High latency (${metrics.averageLatency.toFixed(1)}ms)`);
      }

      if (metrics.bufferOverflows > 0) {
        analysis.performance.issues.push(`${symbol}: Buffer overflows detected (${metrics.bufferOverflows})`);
      }
    }

    // Pattern analysis
    for (const pattern of this.testConfig.dataFeedPatterns) {
      const patternTicks = pattern.symbols.reduce((total, symbol) => {
        const metrics = this.dataFeedMetrics.get(symbol);
        return total + (metrics ? metrics.ticksReceived : 0);
      }, 0);

      analysis.overall.patterns[pattern.name] = {
        ticksProcessed: patternTicks,
        expectedThroughput: pattern.expectedThroughput,
        symbols: pattern.symbols.length
      };
    }

    // Store analysis
    (this.metrics as any).dataFeedAnalysis = analysis;
    this.emit('dataFeedAnalysis', analysis);
  }

  public getDataFeedMetrics(): Map<string, TickProcessingMetrics> {
    return new Map(this.dataFeedMetrics);
  }

  public getTickBuffers(): Map<string, MT5TickData[]> {
    return new Map(this.tickBuffers);
  }

  public generateDataFeedReport(): string {
    const analysis = (this.metrics as any).dataFeedAnalysis || {};
    let report = '# MT5 Data Feed Performance Test Report\n\n';

    if (analysis.overall) {
      report += `## Overall Performance\n\n`;
      report += `- **Total Ticks Processed:** ${analysis.overall.totalTicks.toLocaleString()}\n`;
      report += `- **Total Missed:** ${analysis.overall.totalMissed.toLocaleString()}\n`;
      report += `- **Average Data Quality:** ${analysis.overall.averageQuality.toFixed(1)}%\n`;
      report += `- **Performance Target Met:** ${analysis.performance.meetsTargets ? '✅' : '❌'}\n\n`;
    }

    if (analysis.symbolAnalysis) {
      report += `## Symbol Analysis\n\n`;

      for (const [symbol, data] of Object.entries(analysis.symbolAnalysis)) {
        const symbolData = data as any;
        report += `### ${symbol}\n\n`;
        report += `- **Ticks Received:** ${symbolData.ticksReceived.toLocaleString()}\n`;
        report += `- **Miss Rate:** ${symbolData.missRate}%\n`;
        report += `- **Average Latency:** ${symbolData.averageLatency}ms\n`;
        report += `- **Max Latency:** ${symbolData.maxLatency}ms\n`;
        report += `- **Processing Rate:** ${symbolData.processingRate} ticks/sec\n`;
        report += `- **Data Quality:** ${symbolData.dataQuality}%\n`;
        report += `- **Buffer Overflows:** ${symbolData.bufferOverflows}\n\n`;

        // Quality assessment
        const quality = parseFloat(symbolData.dataQuality);
        if (quality >= 95) {
          report += '✅ **Excellent data feed quality**\n\n';
        } else if (quality >= 85) {
          report += '⚠️ **Good data feed quality**\n\n';
        } else if (quality >= 70) {
          report += '⚠️ **Acceptable data feed quality**\n\n';
        } else {
          report += '❌ **Poor data feed quality - optimization needed**\n\n';
        }
      }
    }

    if (analysis.performance?.issues?.length > 0) {
      report += `## Performance Issues\n\n`;
      analysis.performance.issues.forEach((issue: string, i: number) => {
        report += `${i + 1}. ${issue}\n`;
      });
      report += '\n';
    }

    return report;
  }
}