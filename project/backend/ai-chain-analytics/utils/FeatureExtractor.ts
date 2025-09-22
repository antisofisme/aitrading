/**
 * Feature Extractor
 * Extracts and transforms features from chain metrics and traces for ML models
 */

import {
  ChainMetrics,
  ChainTrace,
  ChainStepTrace,
  TimeSeriesFeatures,
  GraphFeatures
} from '../types';

export class FeatureExtractor {
  private featureCache: Map<string, any> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  constructor() {}

  async extractFeatures(
    metrics: ChainMetrics[],
    traces: ChainTrace[]
  ): Promise<Record<string, number>> {
    const cacheKey = `${metrics.length}_${traces.length}_${Date.now()}`;

    // Check cache
    if (this.featureCache.has(cacheKey)) {
      return this.featureCache.get(cacheKey);
    }

    const features: Record<string, number> = {};

    // Basic statistical features
    Object.assign(features, this.extractStatisticalFeatures(metrics));

    // Time series features
    Object.assign(features, this.extractTimeSeriesFeatures(metrics));

    // Execution pattern features
    Object.assign(features, this.extractExecutionPatternFeatures(traces));

    // Dependency graph features
    Object.assign(features, this.extractDependencyFeatures(traces));

    // Error and failure features
    Object.assign(features, this.extractErrorFeatures(traces));

    // Performance trend features
    Object.assign(features, this.extractTrendFeatures(metrics));

    // Resource utilization features
    Object.assign(features, this.extractResourceFeatures(metrics));

    // Normalize features
    const normalizedFeatures = this.normalizeFeatures(features);

    // Cache results
    this.featureCache.set(cacheKey, normalizedFeatures);
    setTimeout(() => this.featureCache.delete(cacheKey), this.CACHE_TTL);

    return normalizedFeatures;
  }

  private extractStatisticalFeatures(metrics: ChainMetrics[]): Record<string, number> {
    if (metrics.length === 0) {
      return {};
    }

    const features: Record<string, number> = {};

    // Execution time statistics
    const executionTimes = metrics.map(m => m.executionTime);
    features.executionTime_mean = this.calculateMean(executionTimes);
    features.executionTime_std = this.calculateStandardDeviation(executionTimes);
    features.executionTime_median = this.calculateMedian(executionTimes);
    features.executionTime_min = Math.min(...executionTimes);
    features.executionTime_max = Math.max(...executionTimes);
    features.executionTime_p95 = this.calculatePercentile(executionTimes, 95);
    features.executionTime_cv = features.executionTime_std / features.executionTime_mean;

    // Throughput statistics
    const throughputs = metrics.map(m => m.throughput);
    features.throughput_mean = this.calculateMean(throughputs);
    features.throughput_std = this.calculateStandardDeviation(throughputs);
    features.throughput_median = this.calculateMedian(throughputs);
    features.throughput_min = Math.min(...throughputs);
    features.throughput_max = Math.max(...throughputs);

    // Latency statistics
    const latencies = metrics.map(m => m.latency);
    features.latency_mean = this.calculateMean(latencies);
    features.latency_std = this.calculateStandardDeviation(latencies);
    features.latency_median = this.calculateMedian(latencies);
    features.latency_p95 = this.calculatePercentile(latencies, 95);
    features.latency_p99 = this.calculatePercentile(latencies, 99);

    // Error statistics
    const errorCounts = metrics.map(m => m.errorCount);
    features.errorCount_sum = errorCounts.reduce((sum, e) => sum + e, 0);
    features.errorCount_mean = this.calculateMean(errorCounts);
    features.errorCount_max = Math.max(...errorCounts);
    features.errorRate = features.errorCount_sum / metrics.length;

    // Success rate
    features.successRate_mean = this.calculateMean(metrics.map(m => m.successRate));
    features.successRate_min = Math.min(...metrics.map(m => m.successRate));

    // Step count statistics
    const stepCounts = metrics.map(m => m.stepCount);
    features.stepCount_mean = this.calculateMean(stepCounts);
    features.stepCount_std = this.calculateStandardDeviation(stepCounts);
    features.stepCount_max = Math.max(...stepCounts);

    // Resource utilization statistics
    const memoryUsages = metrics.map(m => m.memoryUsage);
    const cpuUsages = metrics.map(m => m.cpuUsage);

    features.memoryUsage_mean = this.calculateMean(memoryUsages);
    features.memoryUsage_max = Math.max(...memoryUsages);
    features.memoryUsage_p95 = this.calculatePercentile(memoryUsages, 95);

    features.cpuUsage_mean = this.calculateMean(cpuUsages);
    features.cpuUsage_max = Math.max(...cpuUsages);
    features.cpuUsage_p95 = this.calculatePercentile(cpuUsages, 95);

    return features;
  }

  private extractTimeSeriesFeatures(metrics: ChainMetrics[]): Record<string, number> {
    if (metrics.length < 3) {
      return {};
    }

    const features: Record<string, number> = {};

    // Sort metrics by timestamp
    const sortedMetrics = [...metrics].sort((a, b) => a.timestamp - b.timestamp);

    // Execution time series analysis
    const executionTimeSeries = sortedMetrics.map(m => m.executionTime);
    const executionTimeFeatures = this.calculateTimeSeriesFeatures(executionTimeSeries);
    Object.keys(executionTimeFeatures).forEach(key => {
      features[`executionTime_${key}`] = executionTimeFeatures[key as keyof TimeSeriesFeatures];
    });

    // Throughput series analysis
    const throughputSeries = sortedMetrics.map(m => m.throughput);
    const throughputFeatures = this.calculateTimeSeriesFeatures(throughputSeries);
    Object.keys(throughputFeatures).forEach(key => {
      features[`throughput_${key}`] = throughputFeatures[key as keyof TimeSeriesFeatures];
    });

    // Latency series analysis
    const latencySeries = sortedMetrics.map(m => m.latency);
    const latencyFeatures = this.calculateTimeSeriesFeatures(latencySeries);
    Object.keys(latencyFeatures).forEach(key => {
      features[`latency_${key}`] = latencyFeatures[key as keyof TimeSeriesFeatures];
    });

    // Error count series analysis
    const errorSeries = sortedMetrics.map(m => m.errorCount);
    const errorFeatures = this.calculateTimeSeriesFeatures(errorSeries);
    Object.keys(errorFeatures).forEach(key => {
      features[`errorCount_${key}`] = errorFeatures[key as keyof TimeSeriesFeatures];
    });

    // Inter-arrival time features
    const timestamps = sortedMetrics.map(m => m.timestamp);
    const interArrivalTimes = timestamps.slice(1).map((t, i) => t - timestamps[i]);
    if (interArrivalTimes.length > 0) {
      features.interArrivalTime_mean = this.calculateMean(interArrivalTimes);
      features.interArrivalTime_std = this.calculateStandardDeviation(interArrivalTimes);
      features.interArrivalTime_cv = features.interArrivalTime_std / features.interArrivalTime_mean;
    }

    return features;
  }

  private extractExecutionPatternFeatures(traces: ChainTrace[]): Record<string, number> {
    if (traces.length === 0) {
      return {};
    }

    const features: Record<string, number> = {};

    // Step type diversity
    const allStepTypes = new Set<string>();
    traces.forEach(trace => {
      trace.steps.forEach(step => allStepTypes.add(step.stepType));
    });
    features.stepType_diversity = allStepTypes.size;

    // Average steps per trace
    const stepCounts = traces.map(trace => trace.steps.length);
    features.stepsPerTrace_mean = this.calculateMean(stepCounts);
    features.stepsPerTrace_std = this.calculateStandardDeviation(stepCounts);

    // Step execution patterns
    const stepDurations = traces.flatMap(trace => trace.steps.map(step => step.duration));
    features.stepDuration_mean = this.calculateMean(stepDurations);
    features.stepDuration_std = this.calculateStandardDeviation(stepDurations);
    features.stepDuration_p95 = this.calculatePercentile(stepDurations, 95);

    // Parallel vs sequential execution patterns
    let parallelSteps = 0;
    let sequentialSteps = 0;

    traces.forEach(trace => {
      const stepsByTime = trace.steps.sort((a, b) => a.startTime - b.startTime);

      for (let i = 1; i < stepsByTime.length; i++) {
        const current = stepsByTime[i];
        const previous = stepsByTime[i - 1];

        if (current.startTime < previous.endTime) {
          parallelSteps++;
        } else {
          sequentialSteps++;
        }
      }
    });

    const totalStepTransitions = parallelSteps + sequentialSteps;
    features.parallelExecution_ratio = totalStepTransitions > 0 ? parallelSteps / totalStepTransitions : 0;
    features.sequentialExecution_ratio = totalStepTransitions > 0 ? sequentialSteps / totalStepTransitions : 0;

    // Completion rate patterns
    const completionRates = traces.map(trace => {
      const completedSteps = trace.steps.filter(step => step.status === 'success').length;
      return completedSteps / trace.steps.length;
    });
    features.completionRate_mean = this.calculateMean(completionRates);
    features.completionRate_std = this.calculateStandardDeviation(completionRates);
    features.completionRate_min = Math.min(...completionRates);

    // Step retry patterns
    const retryPatterns = this.analyzeRetryPatterns(traces);
    features.retryCount_mean = retryPatterns.avgRetries;
    features.retrySuccess_rate = retryPatterns.retrySuccessRate;

    return features;
  }

  private extractDependencyFeatures(traces: ChainTrace[]): Record<string, number> {
    const features: Record<string, number> = {};

    // Build dependency graph
    const dependencyMap = new Map<string, Set<string>>();
    const stepTypes = new Set<string>();

    traces.forEach(trace => {
      trace.steps.forEach(step => {
        stepTypes.add(step.stepType);

        if (!dependencyMap.has(step.stepType)) {
          dependencyMap.set(step.stepType, new Set());
        }

        step.dependencies.forEach(dep => {
          dependencyMap.get(step.stepType)!.add(dep);
        });
      });
    });

    // Graph structure features
    features.dependency_nodeCount = stepTypes.size;
    features.dependency_edgeCount = Array.from(dependencyMap.values())
      .reduce((sum, deps) => sum + deps.size, 0);

    // Graph density
    const maxPossibleEdges = stepTypes.size * (stepTypes.size - 1);
    features.dependency_density = maxPossibleEdges > 0 ?
      features.dependency_edgeCount / maxPossibleEdges : 0;

    // Node degree features
    const inDegrees: number[] = [];
    const outDegrees: number[] = [];

    stepTypes.forEach(stepType => {
      const outDegree = dependencyMap.get(stepType)?.size || 0;
      outDegrees.push(outDegree);

      // Calculate in-degree
      let inDegree = 0;
      dependencyMap.forEach(deps => {
        if (deps.has(stepType)) inDegree++;
      });
      inDegrees.push(inDegree);
    });

    features.dependency_avgInDegree = this.calculateMean(inDegrees);
    features.dependency_avgOutDegree = this.calculateMean(outDegrees);
    features.dependency_maxInDegree = Math.max(...inDegrees);
    features.dependency_maxOutDegree = Math.max(...outDegrees);

    // Critical path features
    const criticalPaths = this.findCriticalPaths(traces);
    features.criticalPath_count = criticalPaths.length;
    features.criticalPath_avgLength = criticalPaths.length > 0 ?
      this.calculateMean(criticalPaths.map(p => p.length)) : 0;

    // Bottleneck identification
    const bottlenecks = this.identifyBottlenecks(traces);
    features.bottleneck_count = bottlenecks.length;
    features.bottleneck_ratio = stepTypes.size > 0 ? bottlenecks.length / stepTypes.size : 0;

    return features;
  }

  private extractErrorFeatures(traces: ChainTrace[]): Record<string, number> {
    const features: Record<string, number> = {};

    if (traces.length === 0) {
      return features;
    }

    // Error rate by step type
    const stepTypeErrors = new Map<string, { total: number; errors: number }>();

    traces.forEach(trace => {
      trace.steps.forEach(step => {
        if (!stepTypeErrors.has(step.stepType)) {
          stepTypeErrors.set(step.stepType, { total: 0, errors: 0 });
        }

        const stats = stepTypeErrors.get(step.stepType)!;
        stats.total++;
        if (step.status === 'failure') {
          stats.errors++;
        }
      });
    });

    // Calculate error rates
    const errorRates = Array.from(stepTypeErrors.values())
      .map(stats => stats.errors / stats.total);

    features.errorRate_byStepType_mean = this.calculateMean(errorRates);
    features.errorRate_byStepType_max = Math.max(...errorRates);
    features.errorRate_byStepType_std = this.calculateStandardDeviation(errorRates);

    // Error clustering
    const errorClusters = this.analyzeErrorClusters(traces);
    features.errorCluster_count = errorClusters.length;
    features.errorCluster_avgSize = errorClusters.length > 0 ?
      this.calculateMean(errorClusters.map(c => c.size)) : 0;

    // Error propagation patterns
    const propagationData = this.analyzeErrorPropagation(traces);
    features.errorPropagation_ratio = propagationData.propagationRatio;
    features.errorPropagation_avgHops = propagationData.avgHops;

    // Recovery patterns
    const recoveryData = this.analyzeRecoveryPatterns(traces);
    features.recovery_successRate = recoveryData.successRate;
    features.recovery_avgTime = recoveryData.avgRecoveryTime;

    return features;
  }

  private extractTrendFeatures(metrics: ChainMetrics[]): Record<string, number> {
    if (metrics.length < 3) {
      return {};
    }

    const features: Record<string, number> = {};

    // Sort metrics by timestamp
    const sortedMetrics = [...metrics].sort((a, b) => a.timestamp - b.timestamp);

    // Execution time trend
    const executionTimes = sortedMetrics.map(m => m.executionTime);
    features.executionTime_trend = this.calculateTrend(executionTimes);
    features.executionTime_trendStrength = this.calculateTrendStrength(executionTimes);

    // Throughput trend
    const throughputs = sortedMetrics.map(m => m.throughput);
    features.throughput_trend = this.calculateTrend(throughputs);
    features.throughput_trendStrength = this.calculateTrendStrength(throughputs);

    // Latency trend
    const latencies = sortedMetrics.map(m => m.latency);
    features.latency_trend = this.calculateTrend(latencies);
    features.latency_trendStrength = this.calculateTrendStrength(latencies);

    // Error trend
    const errorCounts = sortedMetrics.map(m => m.errorCount);
    features.errorCount_trend = this.calculateTrend(errorCounts);
    features.errorCount_trendStrength = this.calculateTrendStrength(errorCounts);

    // Memory usage trend
    const memoryUsages = sortedMetrics.map(m => m.memoryUsage);
    features.memoryUsage_trend = this.calculateTrend(memoryUsages);
    features.memoryUsage_trendStrength = this.calculateTrendStrength(memoryUsages);

    // CPU usage trend
    const cpuUsages = sortedMetrics.map(m => m.cpuUsage);
    features.cpuUsage_trend = this.calculateTrend(cpuUsages);
    features.cpuUsage_trendStrength = this.calculateTrendStrength(cpuUsages);

    return features;
  }

  private extractResourceFeatures(metrics: ChainMetrics[]): Record<string, number> {
    if (metrics.length === 0) {
      return {};
    }

    const features: Record<string, number> = {};

    // Memory utilization patterns
    const memoryUsages = metrics.map(m => m.memoryUsage);
    features.memory_utilization_mean = this.calculateMean(memoryUsages);
    features.memory_utilization_max = Math.max(...memoryUsages);
    features.memory_utilization_volatility = this.calculateVolatility(memoryUsages);
    features.memory_pressure_ratio = memoryUsages.filter(m => m > 0.8).length / memoryUsages.length;

    // CPU utilization patterns
    const cpuUsages = metrics.map(m => m.cpuUsage);
    features.cpu_utilization_mean = this.calculateMean(cpuUsages);
    features.cpu_utilization_max = Math.max(...cpuUsages);
    features.cpu_utilization_volatility = this.calculateVolatility(cpuUsages);
    features.cpu_pressure_ratio = cpuUsages.filter(c => c > 0.8).length / cpuUsages.length;

    // Resource correlation
    const memCpuCorrelation = this.calculateCorrelation(memoryUsages, cpuUsages);
    features.memory_cpu_correlation = memCpuCorrelation;

    // Resource efficiency
    const throughputs = metrics.map(m => m.throughput);
    const memoryEfficiency = throughputs.map((t, i) => t / Math.max(memoryUsages[i], 0.01));
    const cpuEfficiency = throughputs.map((t, i) => t / Math.max(cpuUsages[i], 0.01));

    features.memory_efficiency_mean = this.calculateMean(memoryEfficiency);
    features.cpu_efficiency_mean = this.calculateMean(cpuEfficiency);

    return features;
  }

  private normalizeFeatures(features: Record<string, number>): Record<string, number> {
    const normalized: Record<string, number> = {};

    // Apply feature-specific normalization
    Object.entries(features).forEach(([key, value]) => {
      if (isNaN(value) || !isFinite(value)) {
        normalized[key] = 0;
      } else if (key.includes('_ratio') || key.includes('_rate')) {
        // Already normalized between 0-1
        normalized[key] = Math.max(0, Math.min(1, value));
      } else if (key.includes('_trend')) {
        // Normalize trends to [-1, 1]
        normalized[key] = Math.max(-1, Math.min(1, value));
      } else if (key.includes('time') || key.includes('latency')) {
        // Log normalize time-based features
        normalized[key] = Math.log(value + 1);
      } else if (key.includes('count')) {
        // Square root normalize count features
        normalized[key] = Math.sqrt(value);
      } else {
        // Standard normalization for other features
        normalized[key] = value;
      }
    });

    return normalized;
  }

  // Utility methods

  private calculateMean(values: number[]): number {
    return values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : 0;
  }

  private calculateStandardDeviation(values: number[]): number {
    if (values.length === 0) return 0;
    const mean = this.calculateMean(values);
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    return Math.sqrt(variance);
  }

  private calculateMedian(values: number[]): number {
    if (values.length === 0) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
  }

  private calculatePercentile(values: number[], percentile: number): number {
    if (values.length === 0) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[Math.max(0, Math.min(index, sorted.length - 1))];
  }

  private calculateTimeSeriesFeatures(values: number[]): TimeSeriesFeatures {
    if (values.length < 3) {
      return {
        trend: 0,
        seasonality: 0,
        volatility: 0,
        autocorrelation: 0,
        stationarity: 0,
        outlierRatio: 0
      };
    }

    const trend = this.calculateTrend(values);
    const seasonality = this.calculateSeasonality(values);
    const volatility = this.calculateVolatility(values);
    const autocorrelation = this.calculateAutocorrelation(values, 1);
    const stationarity = this.calculateStationarity(values);
    const outlierRatio = this.calculateOutlierRatio(values);

    return {
      trend,
      seasonality,
      volatility,
      autocorrelation,
      stationarity,
      outlierRatio
    };
  }

  private calculateTrend(values: number[]): number {
    if (values.length < 2) return 0;

    const n = values.length;
    const x = Array.from({ length: n }, (_, i) => i);
    const y = values;

    const sumX = x.reduce((sum, val) => sum + val, 0);
    const sumY = y.reduce((sum, val) => sum + val, 0);
    const sumXY = x.reduce((sum, val, i) => sum + val * y[i], 0);
    const sumXX = x.reduce((sum, val) => sum + val * val, 0);

    const denominator = n * sumXX - sumX * sumX;
    return denominator !== 0 ? (n * sumXY - sumX * sumY) / denominator : 0;
  }

  private calculateTrendStrength(values: number[]): number {
    const trend = this.calculateTrend(values);
    const mean = this.calculateMean(values);
    return mean !== 0 ? Math.abs(trend) / mean : 0;
  }

  private calculateSeasonality(values: number[]): number {
    // Simplified seasonality detection using autocorrelation
    const maxLag = Math.min(values.length / 2, 24);
    let maxAutocorr = 0;

    for (let lag = 2; lag < maxLag; lag++) {
      const autocorr = Math.abs(this.calculateAutocorrelation(values, lag));
      maxAutocorr = Math.max(maxAutocorr, autocorr);
    }

    return maxAutocorr;
  }

  private calculateVolatility(values: number[]): number {
    if (values.length < 2) return 0;
    const mean = this.calculateMean(values);
    const stdDev = this.calculateStandardDeviation(values);
    return mean > 0 ? stdDev / mean : stdDev;
  }

  private calculateAutocorrelation(values: number[], lag: number): number {
    if (values.length <= lag) return 0;

    const n = values.length - lag;
    const mean = this.calculateMean(values);

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {
      numerator += (values[i] - mean) * (values[i + lag] - mean);
    }

    for (let i = 0; i < values.length; i++) {
      denominator += Math.pow(values[i] - mean, 2);
    }

    return denominator > 0 ? numerator / denominator : 0;
  }

  private calculateStationarity(values: number[]): number {
    // Simplified stationarity check using rolling statistics
    if (values.length < 20) return 0;

    const windowSize = Math.floor(values.length / 4);
    const windows = [];

    for (let i = 0; i <= values.length - windowSize; i += windowSize) {
      const window = values.slice(i, i + windowSize);
      const mean = this.calculateMean(window);
      const variance = this.calculateStandardDeviation(window) ** 2;
      windows.push({ mean, variance });
    }

    const means = windows.map(w => w.mean);
    const variances = windows.map(w => w.variance);

    const meanStability = 1 - this.calculateVolatility(means);
    const varianceStability = 1 - this.calculateVolatility(variances);

    return (meanStability + varianceStability) / 2;
  }

  private calculateOutlierRatio(values: number[]): number {
    if (values.length < 5) return 0;

    const sorted = [...values].sort((a, b) => a - b);
    const q1 = this.calculatePercentile(sorted, 25);
    const q3 = this.calculatePercentile(sorted, 75);
    const iqr = q3 - q1;
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;

    const outliers = values.filter(v => v < lowerBound || v > upperBound);
    return outliers.length / values.length;
  }

  private calculateCorrelation(x: number[], y: number[]): number {
    if (x.length !== y.length || x.length === 0) return 0;

    const meanX = this.calculateMean(x);
    const meanY = this.calculateMean(y);

    let numerator = 0;
    let sumXSquared = 0;
    let sumYSquared = 0;

    for (let i = 0; i < x.length; i++) {
      const diffX = x[i] - meanX;
      const diffY = y[i] - meanY;

      numerator += diffX * diffY;
      sumXSquared += diffX * diffX;
      sumYSquared += diffY * diffY;
    }

    const denominator = Math.sqrt(sumXSquared * sumYSquared);
    return denominator === 0 ? 0 : numerator / denominator;
  }

  private analyzeRetryPatterns(traces: ChainTrace[]): { avgRetries: number; retrySuccessRate: number } {
    // Simplified retry analysis - would need more sophisticated logic
    let totalRetries = 0;
    let successfulRetries = 0;
    let retryAttempts = 0;

    traces.forEach(trace => {
      // Look for potential retry patterns in step sequences
      const stepTypes = trace.steps.map(s => s.stepType);
      const duplicateSteps = stepTypes.filter((step, index) => stepTypes.indexOf(step) !== index);

      totalRetries += duplicateSteps.length;
      retryAttempts += duplicateSteps.length;

      // Count successful retries (simplified)
      duplicateSteps.forEach(stepType => {
        const lastOccurrence = trace.steps.reverse().find(s => s.stepType === stepType);
        if (lastOccurrence && lastOccurrence.status === 'success') {
          successfulRetries++;
        }
      });
    });

    return {
      avgRetries: traces.length > 0 ? totalRetries / traces.length : 0,
      retrySuccessRate: retryAttempts > 0 ? successfulRetries / retryAttempts : 0
    };
  }

  private findCriticalPaths(traces: ChainTrace[]): string[][] {
    // Simplified critical path identification
    return traces
      .filter(trace => trace.endTime - trace.startTime > 10000) // > 10s
      .map(trace => trace.steps.map(s => s.stepType))
      .slice(0, 5); // Limit to top 5
  }

  private identifyBottlenecks(traces: ChainTrace[]): string[] {
    const stepPerformance = new Map<string, { totalTime: number; count: number }>();

    traces.forEach(trace => {
      trace.steps.forEach(step => {
        if (!stepPerformance.has(step.stepType)) {
          stepPerformance.set(step.stepType, { totalTime: 0, count: 0 });
        }

        const perf = stepPerformance.get(step.stepType)!;
        perf.totalTime += step.duration;
        perf.count++;
      });
    });

    // Identify steps with high average execution time
    return Array.from(stepPerformance.entries())
      .filter(([_, perf]) => perf.totalTime / perf.count > 5000) // > 5s average
      .map(([stepType, _]) => stepType);
  }

  private analyzeErrorClusters(traces: ChainTrace[]): { size: number }[] {
    // Simplified error clustering - would use more sophisticated clustering
    const errorTraces = traces.filter(trace =>
      trace.steps.some(step => step.status === 'failure')
    );

    return [{ size: errorTraces.length }]; // Simplified single cluster
  }

  private analyzeErrorPropagation(traces: ChainTrace[]): { propagationRatio: number; avgHops: number } {
    let propagationEvents = 0;
    let totalHops = 0;
    let errorSequences = 0;

    traces.forEach(trace => {
      const errorSteps = trace.steps.filter(s => s.status === 'failure');
      if (errorSteps.length > 1) {
        errorSequences++;
        propagationEvents += errorSteps.length - 1;
        totalHops += errorSteps.length;
      }
    });

    return {
      propagationRatio: traces.length > 0 ? propagationEvents / traces.length : 0,
      avgHops: errorSequences > 0 ? totalHops / errorSequences : 0
    };
  }

  private analyzeRecoveryPatterns(traces: ChainTrace[]): { successRate: number; avgRecoveryTime: number } {
    let recoveryAttempts = 0;
    let successfulRecoveries = 0;
    let totalRecoveryTime = 0;

    traces.forEach(trace => {
      let foundError = false;
      let errorTime = 0;

      trace.steps.forEach(step => {
        if (step.status === 'failure' && !foundError) {
          foundError = true;
          errorTime = step.endTime;
        } else if (foundError && step.status === 'success') {
          recoveryAttempts++;
          successfulRecoveries++;
          totalRecoveryTime += step.endTime - errorTime;
          foundError = false;
        }
      });
    });

    return {
      successRate: recoveryAttempts > 0 ? successfulRecoveries / recoveryAttempts : 0,
      avgRecoveryTime: successfulRecoveries > 0 ? totalRecoveryTime / successfulRecoveries : 0
    };
  }
}