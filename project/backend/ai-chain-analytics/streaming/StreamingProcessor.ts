/**
 * Streaming Processor
 * Real-time data streaming and processing for AI chain analytics
 */

import { EventEmitter } from 'events';
import {
  ChainMetrics,
  ChainTrace,
  StreamingConfig,
  ChainAnalyticsResult
} from '../types';

export interface StreamingBatch {
  batchId: string;
  timestamp: number;
  size: number;
  data: (ChainMetrics | ChainTrace)[];
  processingTime?: number;
}

export interface StreamingStats {
  totalBatches: number;
  totalRecords: number;
  avgBatchSize: number;
  avgProcessingTime: number;
  throughputPerSecond: number;
  bufferUtilization: number;
  lastProcessedTime: number;
}

export interface WindowData {
  windowId: string;
  startTime: number;
  endTime: number;
  metrics: ChainMetrics[];
  traces: ChainTrace[];
  aggregatedFeatures: Record<string, number>;
}

export class StreamingProcessor extends EventEmitter {
  private config: StreamingConfig;
  private buffer: (ChainMetrics | ChainTrace)[] = [];
  private processingInterval: NodeJS.Timeout | null = null;
  private windows: Map<string, WindowData> = new Map();
  private stats: StreamingStats;
  private isProcessing: boolean = false;
  private isInitialized: boolean = false;
  private batchCounter: number = 0;
  private recordCounter: number = 0;
  private processingTimes: number[] = [];

  constructor(config: StreamingConfig) {
    super();
    this.config = config;
    this.stats = {
      totalBatches: 0,
      totalRecords: 0,
      avgBatchSize: 0,
      avgProcessingTime: 0,
      throughputPerSecond: 0,
      bufferUtilization: 0,
      lastProcessedTime: 0
    };
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing Streaming Processor...');

      // Validate configuration
      this.validateConfig();

      // Setup processing interval
      this.startProcessing();

      // Setup cleanup interval
      this.startCleanup();

      this.isInitialized = true;
      console.log('Streaming Processor initialized');
    } catch (error) {
      console.error('Failed to initialize streaming processor:', error);
      throw error;
    }
  }

  async ingestData(data: ChainMetrics | ChainTrace | (ChainMetrics | ChainTrace)[]): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('Streaming processor not initialized');
    }

    const items = Array.isArray(data) ? data : [data];

    // Add to buffer
    this.buffer.push(...items);
    this.recordCounter += items.length;

    // Check buffer size
    if (this.buffer.length >= this.config.bufferSize) {
      console.warn(`Buffer size limit reached: ${this.buffer.length}`);
      // Remove oldest items to maintain buffer size
      const overflow = this.buffer.length - this.config.bufferSize;
      this.buffer.splice(0, overflow);
    }

    // Update buffer utilization
    this.stats.bufferUtilization = this.buffer.length / this.config.bufferSize;

    // Emit buffer events
    if (this.stats.bufferUtilization > 0.8) {
      this.emit('bufferHigh', this.stats.bufferUtilization);
    }

    if (this.buffer.length >= this.config.batchSize) {
      this.emit('batchReady', await this.createBatch());
    }
  }

  async processWindow(windowSizeMinutes: number): Promise<WindowData> {
    const now = Date.now();
    const windowStart = now - windowSizeMinutes * 60 * 1000;
    const windowId = `window_${windowStart}_${now}`;

    // Filter data within window
    const windowMetrics = this.buffer
      .filter(item => this.isMetrics(item) && item.timestamp >= windowStart)
      .map(item => item as ChainMetrics);

    const windowTraces = this.buffer
      .filter(item => this.isTrace(item) && item.startTime >= windowStart)
      .map(item => item as ChainTrace);

    // Calculate aggregated features
    const aggregatedFeatures = this.calculateAggregatedFeatures(windowMetrics, windowTraces);

    const windowData: WindowData = {
      windowId,
      startTime: windowStart,
      endTime: now,
      metrics: windowMetrics,
      traces: windowTraces,
      aggregatedFeatures
    };

    // Store window data
    this.windows.set(windowId, windowData);

    // Emit window ready event
    this.emit('windowReady', windowData);

    return windowData;
  }

  async processSlidingWindow(): Promise<WindowData[]> {
    const windows: WindowData[] = [];
    const now = Date.now();
    const windowSize = this.config.windowSizeMinutes * 60 * 1000;
    const slideSize = this.config.slidingWindowMinutes * 60 * 1000;

    // Create multiple overlapping windows
    const numWindows = Math.ceil(windowSize / slideSize);

    for (let i = 0; i < numWindows; i++) {
      const windowEnd = now - i * slideSize;
      const windowStart = windowEnd - windowSize;
      const windowId = `sliding_${windowStart}_${windowEnd}`;

      // Filter data for this window
      const windowMetrics = this.buffer
        .filter(item =>
          this.isMetrics(item) &&
          item.timestamp >= windowStart &&
          item.timestamp <= windowEnd
        )
        .map(item => item as ChainMetrics);

      const windowTraces = this.buffer
        .filter(item =>
          this.isTrace(item) &&
          item.startTime >= windowStart &&
          item.startTime <= windowEnd
        )
        .map(item => item as ChainTrace);

      if (windowMetrics.length > 0 || windowTraces.length > 0) {
        const aggregatedFeatures = this.calculateAggregatedFeatures(windowMetrics, windowTraces);

        const windowData: WindowData = {
          windowId,
          startTime: windowStart,
          endTime: windowEnd,
          metrics: windowMetrics,
          traces: windowTraces,
          aggregatedFeatures
        };

        windows.push(windowData);
        this.windows.set(windowId, windowData);
      }
    }

    return windows;
  }

  getStreamingStats(): StreamingStats {
    // Update throughput calculation
    const timeSpanSeconds = (Date.now() - (this.stats.lastProcessedTime || Date.now())) / 1000;
    this.stats.throughputPerSecond = timeSpanSeconds > 0 ? this.recordCounter / timeSpanSeconds : 0;

    return { ...this.stats };
  }

  getWindowData(windowId: string): WindowData | undefined {
    return this.windows.get(windowId);
  }

  getAllWindows(): WindowData[] {
    return Array.from(this.windows.values());
  }

  async flush(): Promise<StreamingBatch[]> {
    const batches: StreamingBatch[] = [];

    while (this.buffer.length > 0) {
      const batch = await this.createBatch(Math.min(this.buffer.length, this.config.batchSize));
      batches.push(batch);
    }

    return batches;
  }

  async stop(): Promise<void> {
    console.log('Stopping streaming processor...');

    if (this.processingInterval) {
      clearInterval(this.processingInterval);
      this.processingInterval = null;
    }

    // Process remaining data
    if (this.buffer.length > 0) {
      const remainingBatches = await this.flush();
      for (const batch of remainingBatches) {
        this.emit('batchReady', batch);
      }
    }

    this.isInitialized = false;
    console.log('Streaming processor stopped');
  }

  // Real-time analysis methods

  async analyzeIncomingData(data: ChainMetrics | ChainTrace): Promise<{
    anomalies: string[];
    patterns: string[];
    alerts: string[];
  }> {
    const results = {
      anomalies: [],
      patterns: [],
      alerts: []
    };

    if (this.isMetrics(data)) {
      // Real-time metrics analysis
      const metricsAnomalies = this.detectMetricsAnomalies(data);
      results.anomalies.push(...metricsAnomalies);

      // Check for alerts
      const alerts = this.checkMetricsAlerts(data);
      results.alerts.push(...alerts);
    }

    if (this.isTrace(data)) {
      // Real-time trace analysis
      const tracePatterns = this.detectTracePatterns(data);
      results.patterns.push(...tracePatterns);

      // Check for error patterns
      const errorAlerts = this.checkTraceAlerts(data);
      results.alerts.push(...errorAlerts);
    }

    // Emit real-time analysis results
    if (results.anomalies.length > 0 || results.patterns.length > 0 || results.alerts.length > 0) {
      this.emit('realTimeAnalysis', results);
    }

    return results;
  }

  // Private methods

  private validateConfig(): void {
    if (this.config.batchSize <= 0) {
      throw new Error('Batch size must be positive');
    }
    if (this.config.bufferSize < this.config.batchSize) {
      throw new Error('Buffer size must be at least batch size');
    }
    if (this.config.processingIntervalMs <= 0) {
      throw new Error('Processing interval must be positive');
    }
  }

  private startProcessing(): void {
    this.processingInterval = setInterval(async () => {
      if (!this.isProcessing && this.buffer.length >= this.config.batchSize) {
        this.isProcessing = true;
        try {
          const batch = await this.createBatch();
          this.emit('batchReady', batch);
        } catch (error) {
          console.error('Batch processing error:', error);
          this.emit('processingError', error);
        } finally {
          this.isProcessing = false;
        }
      }
    }, this.config.processingIntervalMs);
  }

  private startCleanup(): void {
    // Cleanup old windows every 5 minutes
    setInterval(() => {
      this.cleanupOldWindows();
    }, 5 * 60 * 1000);
  }

  private cleanupOldWindows(): void {
    const cutoffTime = Date.now() - this.config.retentionDays * 24 * 60 * 60 * 1000;
    let cleaned = 0;

    for (const [windowId, windowData] of this.windows.entries()) {
      if (windowData.endTime < cutoffTime) {
        this.windows.delete(windowId);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      console.log(`Cleaned up ${cleaned} old windows`);
    }
  }

  private async createBatch(size?: number): Promise<StreamingBatch> {
    const batchSize = size || this.config.batchSize;
    const batchData = this.buffer.splice(0, batchSize);
    const processingStart = Date.now();

    const batch: StreamingBatch = {
      batchId: `batch_${this.batchCounter++}`,
      timestamp: processingStart,
      size: batchData.length,
      data: batchData
    };

    // Update statistics
    this.stats.totalBatches++;
    this.stats.totalRecords += batchData.length;
    this.stats.avgBatchSize = this.stats.totalRecords / this.stats.totalBatches;
    this.stats.lastProcessedTime = Date.now();

    // Calculate processing time (will be updated when batch is processed)
    batch.processingTime = Date.now() - processingStart;
    this.processingTimes.push(batch.processingTime);

    // Keep only last 100 processing times for average calculation
    if (this.processingTimes.length > 100) {
      this.processingTimes.shift();
    }

    this.stats.avgProcessingTime = this.processingTimes.reduce((sum, time) => sum + time, 0) / this.processingTimes.length;

    return batch;
  }

  private calculateAggregatedFeatures(
    metrics: ChainMetrics[],
    traces: ChainTrace[]
  ): Record<string, number> {
    const features: Record<string, number> = {};

    if (metrics.length > 0) {
      // Metrics aggregations
      const executionTimes = metrics.map(m => m.executionTime);
      const throughputs = metrics.map(m => m.throughput);
      const latencies = metrics.map(m => m.latency);
      const errorCounts = metrics.map(m => m.errorCount);

      features.avg_execution_time = this.calculateMean(executionTimes);
      features.max_execution_time = Math.max(...executionTimes);
      features.min_execution_time = Math.min(...executionTimes);
      features.std_execution_time = this.calculateStandardDeviation(executionTimes);

      features.avg_throughput = this.calculateMean(throughputs);
      features.avg_latency = this.calculateMean(latencies);
      features.total_errors = errorCounts.reduce((sum, e) => sum + e, 0);
      features.error_rate = features.total_errors / metrics.length;

      features.metrics_count = metrics.length;
    }

    if (traces.length > 0) {
      // Trace aggregations
      const traceDurations = traces.map(t => t.endTime - t.startTime);
      const stepCounts = traces.map(t => t.steps.length);
      const failedTraces = traces.filter(t => t.status === 'failure').length;

      features.avg_trace_duration = this.calculateMean(traceDurations);
      features.max_trace_duration = Math.max(...traceDurations);
      features.avg_step_count = this.calculateMean(stepCounts);
      features.trace_failure_rate = failedTraces / traces.length;

      features.traces_count = traces.length;
    }

    // Cross-metric features
    if (metrics.length > 0 && traces.length > 0) {
      features.metrics_to_traces_ratio = metrics.length / traces.length;
    }

    return features;
  }

  private isMetrics(item: ChainMetrics | ChainTrace): item is ChainMetrics {
    return 'executionTime' in item && 'throughput' in item;
  }

  private isTrace(item: ChainMetrics | ChainTrace): item is ChainTrace {
    return 'steps' in item && 'traceId' in item;
  }

  private detectMetricsAnomalies(metrics: ChainMetrics): string[] {
    const anomalies: string[] = [];

    // Simple threshold-based anomaly detection
    if (metrics.executionTime > 30000) { // 30 seconds
      anomalies.push(`High execution time: ${metrics.executionTime}ms`);
    }

    if (metrics.errorCount > 5) {
      anomalies.push(`High error count: ${metrics.errorCount}`);
    }

    if (metrics.throughput < 10) {
      anomalies.push(`Low throughput: ${metrics.throughput}`);
    }

    if (metrics.latency > 10000) { // 10 seconds
      anomalies.push(`High latency: ${metrics.latency}ms`);
    }

    if (metrics.memoryUsage > 0.9) { // 90%
      anomalies.push(`High memory usage: ${(metrics.memoryUsage * 100).toFixed(1)}%`);
    }

    if (metrics.cpuUsage > 0.9) { // 90%
      anomalies.push(`High CPU usage: ${(metrics.cpuUsage * 100).toFixed(1)}%`);
    }

    return anomalies;
  }

  private checkMetricsAlerts(metrics: ChainMetrics): string[] {
    const alerts: string[] = [];

    // Critical thresholds
    if (metrics.successRate < 0.5) {
      alerts.push(`CRITICAL: Success rate below 50%: ${(metrics.successRate * 100).toFixed(1)}%`);
    }

    if (metrics.memoryUsage > 0.95) {
      alerts.push(`CRITICAL: Memory usage above 95%: ${(metrics.memoryUsage * 100).toFixed(1)}%`);
    }

    if (metrics.cpuUsage > 0.95) {
      alerts.push(`CRITICAL: CPU usage above 95%: ${(metrics.cpuUsage * 100).toFixed(1)}%`);
    }

    return alerts;
  }

  private detectTracePatterns(trace: ChainTrace): string[] {
    const patterns: string[] = [];

    // Detect common patterns
    const stepTypes = trace.steps.map(s => s.stepType);
    const uniqueSteps = new Set(stepTypes);

    // Repetitive steps pattern
    if (stepTypes.length > uniqueSteps.size * 2) {
      patterns.push('Repetitive step pattern detected');
    }

    // Long execution pattern
    const totalDuration = trace.endTime - trace.startTime;
    if (totalDuration > 60000) { // 1 minute
      patterns.push(`Long execution pattern: ${(totalDuration / 1000).toFixed(1)}s`);
    }

    // Failure cascade pattern
    const failedSteps = trace.steps.filter(s => s.status === 'failure');
    if (failedSteps.length > 1) {
      patterns.push('Failure cascade pattern detected');
    }

    return patterns;
  }

  private checkTraceAlerts(trace: ChainTrace): string[] {
    const alerts: string[] = [];

    if (trace.status === 'failure') {
      alerts.push(`Trace failed: ${trace.traceId}`);
    }

    if (trace.status === 'timeout') {
      alerts.push(`Trace timeout: ${trace.traceId}`);
    }

    // Check for critical step failures
    const criticalStepFailures = trace.steps.filter(s =>
      s.status === 'failure' && s.stepType.includes('critical')
    );

    if (criticalStepFailures.length > 0) {
      alerts.push(`Critical step failure in trace: ${trace.traceId}`);
    }

    return alerts;
  }

  private calculateMean(values: number[]): number {
    return values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0;
  }

  private calculateStandardDeviation(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = this.calculateMean(values);
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    return Math.sqrt(variance);
  }
}