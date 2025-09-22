/**
 * Chain Anomaly Detector
 * ML-based anomaly detection with baseline learning and real-time monitoring
 */

import { EventEmitter } from 'events';
import {
  ChainMetrics,
  ChainTrace,
  AnomalyDetectionResult,
  MLModelConfig,
  ModelPerformance,
  TimeSeriesFeatures
} from '../types';

export class ChainAnomalyDetector extends EventEmitter {
  private isolationForestModel: any;
  private lstmModel: any;
  private svmModel: any;
  private baseline: Map<string, any> = new Map();
  private featureBaselines: Map<string, number[]> = new Map();
  private isInitialized: boolean = false;
  private modelPerformance: ModelPerformance;
  private readonly ANOMALY_THRESHOLD = 0.3;
  private readonly BASELINE_WINDOW_SIZE = 1000;

  constructor() {
    super();
    this.modelPerformance = {
      accuracy: 0,
      precision: 0,
      recall: 0,
      f1Score: 0,
      auc: 0,
      lastEvaluated: 0,
      validationMethod: 'cross_validation'
    };
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing Chain Anomaly Detector...');

      // Initialize ML models
      await this.initializeModels();

      // Load baseline data
      await this.loadBaselines();

      this.isInitialized = true;
      console.log('Chain Anomaly Detector initialized');
    } catch (error) {
      console.error('Failed to initialize anomaly detector:', error);
      throw error;
    }
  }

  async detectAnomalies(
    chainId: string,
    features: Record<string, number>,
    metrics: ChainMetrics[]
  ): Promise<AnomalyDetectionResult[]> {
    if (!this.isInitialized) {
      throw new Error('Anomaly detector not initialized');
    }

    const anomalies: AnomalyDetectionResult[] = [];

    try {
      // Statistical anomaly detection
      const statisticalAnomalies = await this.detectStatisticalAnomalies(chainId, features, metrics);
      anomalies.push(...statisticalAnomalies);

      // Time series anomaly detection
      const timeSeriesAnomalies = await this.detectTimeSeriesAnomalies(chainId, metrics);
      anomalies.push(...timeSeriesAnomalies);

      // ML-based anomaly detection
      const mlAnomalies = await this.detectMLAnomalies(chainId, features);
      anomalies.push(...mlAnomalies);

      // Resource usage anomalies
      const resourceAnomalies = await this.detectResourceAnomalies(chainId, metrics);
      anomalies.push(...resourceAnomalies);

      // Update baselines with non-anomalous data
      await this.updateBaselines(chainId, features, anomalies.length === 0);

      return anomalies;
    } catch (error) {
      console.error(`Failed to detect anomalies for chain ${chainId}:`, error);
      throw error;
    }
  }

  async detectStatisticalAnomalies(
    chainId: string,
    features: Record<string, number>,
    metrics: ChainMetrics[]
  ): Promise<AnomalyDetectionResult[]> {
    const anomalies: AnomalyDetectionResult[] = [];
    const baseline = this.baseline.get(chainId);

    if (!baseline) {
      // Not enough baseline data
      return anomalies;
    }

    // Z-score based detection
    for (const [feature, value] of Object.entries(features)) {
      const baselineStats = baseline[feature];
      if (!baselineStats) continue;

      const zScore = Math.abs((value - baselineStats.mean) / baselineStats.stdDev);

      if (zScore > 3) { // 3-sigma rule
        anomalies.push({
          anomalyId: `stat_${chainId}_${feature}_${Date.now()}`,
          chainId,
          timestamp: Date.now(),
          anomalyType: 'performance',
          severity: zScore > 5 ? 'critical' : zScore > 4 ? 'high' : 'medium',
          confidence: Math.min(zScore / 3, 1),
          description: `Statistical anomaly in ${feature}: ${value.toFixed(2)} (baseline: ${baselineStats.mean.toFixed(2)} ± ${baselineStats.stdDev.toFixed(2)})`,
          features: { [feature]: value },
          baseline: { [feature]: baselineStats.mean },
          recommendations: [
            `Investigate ${feature} spike`,
            'Check for configuration changes',
            'Review recent deployments'
          ]
        });
      }
    }

    // Interquartile Range (IQR) based detection
    const iqrAnomalies = this.detectIQRAnomalies(chainId, features, baseline);
    anomalies.push(...iqrAnomalies);

    return anomalies;
  }

  async detectTimeSeriesAnomalies(
    chainId: string,
    metrics: ChainMetrics[]
  ): Promise<AnomalyDetectionResult[]> {
    const anomalies: AnomalyDetectionResult[] = [];

    if (metrics.length < 10) {
      return anomalies; // Need more data points
    }

    // Extract time series for key metrics
    const timeSeries = this.extractTimeSeries(metrics);

    for (const [metric, values] of Object.entries(timeSeries)) {
      // Calculate time series features
      const features = this.calculateTimeSeriesFeatures(values);

      // Detect anomalies using LSTM predictions
      const lstmAnomalies = await this.detectLSTMAnomalies(chainId, metric, values, features);
      anomalies.push(...lstmAnomalies);

      // Detect seasonal anomalies
      const seasonalAnomalies = this.detectSeasonalAnomalies(chainId, metric, values, features);
      anomalies.push(...seasonalAnomalies);
    }

    return anomalies;
  }

  async detectMLAnomalies(
    chainId: string,
    features: Record<string, number>
  ): Promise<AnomalyDetectionResult[]> {
    const anomalies: AnomalyDetectionResult[] = [];

    // Prepare feature vector
    const featureVector = this.prepareFeatureVector(features);

    // Isolation Forest detection
    if (this.isolationForestModel) {
      const isolationScore = await this.isolationForestModel.predict(featureVector);

      if (isolationScore < this.ANOMALY_THRESHOLD) {
        anomalies.push({
          anomalyId: `isolation_${chainId}_${Date.now()}`,
          chainId,
          timestamp: Date.now(),
          anomalyType: 'pattern',
          severity: isolationScore < 0.1 ? 'critical' : isolationScore < 0.2 ? 'high' : 'medium',
          confidence: 1 - isolationScore,
          description: `Isolation Forest detected anomalous pattern (score: ${isolationScore.toFixed(3)})`,
          features,
          baseline: this.getFeatureBaseline(features),
          recommendations: [
            'Review system behavior patterns',
            'Check for unusual input data',
            'Validate process execution flow'
          ]
        });
      }
    }

    // SVM one-class detection
    if (this.svmModel) {
      const svmPrediction = await this.svmModel.predict(featureVector);

      if (svmPrediction === -1) { // Outlier
        anomalies.push({
          anomalyId: `svm_${chainId}_${Date.now()}`,
          chainId,
          timestamp: Date.now(),
          anomalyType: 'pattern',
          severity: 'medium',
          confidence: 0.8,
          description: 'SVM detected anomalous behavior pattern',
          features,
          baseline: this.getFeatureBaseline(features),
          recommendations: [
            'Investigate unusual execution patterns',
            'Check system configuration',
            'Review input data quality'
          ]
        });
      }
    }

    return anomalies;
  }

  async detectResourceAnomalies(
    chainId: string,
    metrics: ChainMetrics[]
  ): Promise<AnomalyDetectionResult[]> {
    const anomalies: AnomalyDetectionResult[] = [];

    if (metrics.length === 0) return anomalies;

    const latest = metrics[metrics.length - 1];
    const resourceBaseline = this.baseline.get(`${chainId}_resources`);

    if (!resourceBaseline) return anomalies;

    // Memory usage anomaly
    if (latest.memoryUsage > resourceBaseline.memory.p95) {
      anomalies.push({
        anomalyId: `memory_${chainId}_${Date.now()}`,
        chainId,
        timestamp: Date.now(),
        anomalyType: 'resource',
        severity: latest.memoryUsage > resourceBaseline.memory.p99 ? 'critical' : 'high',
        confidence: 0.9,
        description: `Memory usage spike: ${latest.memoryUsage}MB (baseline: ${resourceBaseline.memory.median}MB)`,
        features: { memoryUsage: latest.memoryUsage },
        baseline: { memoryUsage: resourceBaseline.memory.median },
        recommendations: [
          'Check for memory leaks',
          'Review data processing efficiency',
          'Consider scaling resources'
        ]
      });
    }

    // CPU usage anomaly
    if (latest.cpuUsage > resourceBaseline.cpu.p95) {
      anomalies.push({
        anomalyId: `cpu_${chainId}_${Date.now()}`,
        chainId,
        timestamp: Date.now(),
        anomalyType: 'resource',
        severity: latest.cpuUsage > resourceBaseline.cpu.p99 ? 'critical' : 'high',
        confidence: 0.9,
        description: `CPU usage spike: ${latest.cpuUsage}% (baseline: ${resourceBaseline.cpu.median}%)`,
        features: { cpuUsage: latest.cpuUsage },
        baseline: { cpuUsage: resourceBaseline.cpu.median },
        recommendations: [
          'Identify CPU-intensive operations',
          'Optimize algorithms',
          'Consider load balancing'
        ]
      });
    }

    // Latency anomaly
    if (latest.latency > resourceBaseline.latency.p95) {
      anomalies.push({
        anomalyId: `latency_${chainId}_${Date.now()}`,
        chainId,
        timestamp: Date.now(),
        anomalyType: 'performance',
        severity: latest.latency > resourceBaseline.latency.p99 ? 'critical' : 'high',
        confidence: 0.9,
        description: `Latency spike: ${latest.latency}ms (baseline: ${resourceBaseline.latency.median}ms)`,
        features: { latency: latest.latency },
        baseline: { latency: resourceBaseline.latency.median },
        recommendations: [
          'Check network connectivity',
          'Review database performance',
          'Optimize critical path'
        ]
      });
    }

    return anomalies;
  }

  private detectIQRAnomalies(
    chainId: string,
    features: Record<string, number>,
    baseline: any
  ): AnomalyDetectionResult[] {
    const anomalies: AnomalyDetectionResult[] = [];

    for (const [feature, value] of Object.entries(features)) {
      const stats = baseline[feature];
      if (!stats) continue;

      const iqr = stats.q3 - stats.q1;
      const lowerBound = stats.q1 - 1.5 * iqr;
      const upperBound = stats.q3 + 1.5 * iqr;

      if (value < lowerBound || value > upperBound) {
        anomalies.push({
          anomalyId: `iqr_${chainId}_${feature}_${Date.now()}`,
          chainId,
          timestamp: Date.now(),
          anomalyType: 'performance',
          severity: 'medium',
          confidence: 0.7,
          description: `IQR anomaly in ${feature}: ${value.toFixed(2)} outside bounds [${lowerBound.toFixed(2)}, ${upperBound.toFixed(2)}]`,
          features: { [feature]: value },
          baseline: { [feature]: stats.median },
          recommendations: [
            `Investigate ${feature} outlier`,
            'Check for data quality issues',
            'Review process variations'
          ]
        });
      }
    }

    return anomalies;
  }

  private async detectLSTMAnomalies(
    chainId: string,
    metric: string,
    values: number[],
    features: TimeSeriesFeatures
  ): Promise<AnomalyDetectionResult[]> {
    const anomalies: AnomalyDetectionResult[] = [];

    if (!this.lstmModel || values.length < 20) {
      return anomalies;
    }

    try {
      // Predict next value using LSTM
      const prediction = await this.lstmModel.predict(values.slice(-10));
      const actual = values[values.length - 1];
      const error = Math.abs(actual - prediction) / Math.max(actual, prediction);

      if (error > 0.3) { // 30% deviation threshold
        anomalies.push({
          anomalyId: `lstm_${chainId}_${metric}_${Date.now()}`,
          chainId,
          timestamp: Date.now(),
          anomalyType: 'performance',
          severity: error > 0.5 ? 'high' : 'medium',
          confidence: Math.min(error, 1),
          description: `LSTM detected anomaly in ${metric}: predicted ${prediction.toFixed(2)}, actual ${actual.toFixed(2)} (error: ${(error * 100).toFixed(1)}%)`,
          features: { [metric]: actual, predicted: prediction, error },
          baseline: { [metric]: prediction },
          recommendations: [
            'Check for trend changes',
            'Validate input data',
            'Review model assumptions'
          ]
        });
      }
    } catch (error) {
      console.error(`LSTM anomaly detection failed for ${metric}:`, error);
    }

    return anomalies;
  }

  private detectSeasonalAnomalies(
    chainId: string,
    metric: string,
    values: number[],
    features: TimeSeriesFeatures
  ): AnomalyDetectionResult[] {
    const anomalies: AnomalyDetectionResult[] = [];

    // Simple seasonal decomposition
    if (features.seasonality > 0.7 && values.length > 50) {
      const seasonLength = this.detectSeasonLength(values);
      if (seasonLength > 0) {
        const seasonal = this.extractSeasonalComponent(values, seasonLength);
        const residual = values.map((v, i) => v - seasonal[i % seasonal.length]);
        const residualStd = this.calculateStandardDeviation(residual);
        const latestResidual = residual[residual.length - 1];

        if (Math.abs(latestResidual) > 3 * residualStd) {
          anomalies.push({
            anomalyId: `seasonal_${chainId}_${metric}_${Date.now()}`,
            chainId,
            timestamp: Date.now(),
            anomalyType: 'performance',
            severity: Math.abs(latestResidual) > 5 * residualStd ? 'high' : 'medium',
            confidence: 0.8,
            description: `Seasonal anomaly in ${metric}: residual ${latestResidual.toFixed(2)} exceeds 3σ (${(3 * residualStd).toFixed(2)})`,
            features: { [metric]: values[values.length - 1], residual: latestResidual },
            baseline: { [metric]: seasonal[seasonal.length - 1] },
            recommendations: [
              'Check for seasonal pattern disruption',
              'Validate time-based dependencies',
              'Review periodic processes'
            ]
          });
        }
      }
    }

    return anomalies;
  }

  private async initializeModels(): Promise<void> {
    // Initialize Isolation Forest model (mock implementation)
    this.isolationForestModel = {
      predict: async (features: number[]) => {
        // Mock isolation score calculation
        const randomness = Math.random() * 0.1;
        const featureSum = features.reduce((sum, f) => sum + Math.abs(f), 0);
        return Math.max(0.05, Math.min(0.95, (featureSum / features.length / 100) + randomness));
      }
    };

    // Initialize LSTM model (mock implementation)
    this.lstmModel = {
      predict: async (sequence: number[]) => {
        // Mock LSTM prediction
        const trend = sequence.length > 1 ? sequence[sequence.length - 1] - sequence[sequence.length - 2] : 0;
        return sequence[sequence.length - 1] + trend * 0.5 + (Math.random() - 0.5) * 0.1;
      }
    };

    // Initialize SVM model (mock implementation)
    this.svmModel = {
      predict: async (features: number[]) => {
        // Mock SVM one-class prediction
        const featureSum = features.reduce((sum, f) => sum + f * f, 0);
        return featureSum > 10000 ? -1 : 1; // -1 for outlier, 1 for normal
      }
    };
  }

  private async loadBaselines(): Promise<void> {
    // Load historical baseline data
    // This would typically load from a database
    console.log('Loading anomaly detection baselines...');
  }

  private async updateBaselines(
    chainId: string,
    features: Record<string, number>,
    isNormal: boolean
  ): Promise<void> {
    if (!isNormal) return; // Don't update with anomalous data

    // Update rolling baselines
    for (const [feature, value] of Object.entries(features)) {
      const key = `${chainId}_${feature}`;
      if (!this.featureBaselines.has(key)) {
        this.featureBaselines.set(key, []);
      }

      const baseline = this.featureBaselines.get(key)!;
      baseline.push(value);

      // Keep only recent values
      if (baseline.length > this.BASELINE_WINDOW_SIZE) {
        baseline.shift();
      }

      // Update statistical measures
      this.updateStatisticalBaseline(chainId, feature, baseline);
    }
  }

  private updateStatisticalBaseline(
    chainId: string,
    feature: string,
    values: number[]
  ): void {
    if (values.length < 10) return;

    const sorted = [...values].sort((a, b) => a - b);
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    const baseline = this.baseline.get(chainId) || {};
    baseline[feature] = {
      mean,
      stdDev,
      median: sorted[Math.floor(sorted.length / 2)],
      q1: sorted[Math.floor(sorted.length * 0.25)],
      q3: sorted[Math.floor(sorted.length * 0.75)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
      min: sorted[0],
      max: sorted[sorted.length - 1]
    };

    this.baseline.set(chainId, baseline);
  }

  private extractTimeSeries(metrics: ChainMetrics[]): Record<string, number[]> {
    const series: Record<string, number[]> = {
      executionTime: [],
      throughput: [],
      latency: [],
      errorCount: [],
      memoryUsage: [],
      cpuUsage: []
    };

    for (const metric of metrics) {
      series.executionTime.push(metric.executionTime);
      series.throughput.push(metric.throughput);
      series.latency.push(metric.latency);
      series.errorCount.push(metric.errorCount);
      series.memoryUsage.push(metric.memoryUsage);
      series.cpuUsage.push(metric.cpuUsage);
    }

    return series;
  }

  private calculateTimeSeriesFeatures(values: number[]): TimeSeriesFeatures {
    if (values.length < 5) {
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

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    return slope;
  }

  private calculateSeasonality(values: number[]): number {
    // Simplified seasonality detection using autocorrelation
    const maxLag = Math.min(values.length / 2, 24); // Check up to 24 periods
    let maxAutocorr = 0;

    for (let lag = 2; lag < maxLag; lag++) {
      const autocorr = Math.abs(this.calculateAutocorrelation(values, lag));
      maxAutocorr = Math.max(maxAutocorr, autocorr);
    }

    return maxAutocorr;
  }

  private calculateVolatility(values: number[]): number {
    if (values.length < 2) return 0;

    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return mean > 0 ? stdDev / mean : stdDev; // Coefficient of variation
  }

  private calculateAutocorrelation(values: number[], lag: number): number {
    if (values.length <= lag) return 0;

    const n = values.length - lag;
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;

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
      const mean = window.reduce((sum, v) => sum + v, 0) / window.length;
      const variance = window.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / window.length;
      windows.push({ mean, variance });
    }

    // Check variance of means and variances
    const means = windows.map(w => w.mean);
    const variances = windows.map(w => w.variance);

    const meanStability = 1 - this.calculateVolatility(means);
    const varianceStability = 1 - this.calculateVolatility(variances);

    return (meanStability + varianceStability) / 2;
  }

  private calculateOutlierRatio(values: number[]): number {
    if (values.length < 5) return 0;

    const sorted = [...values].sort((a, b) => a - b);
    const q1 = sorted[Math.floor(sorted.length * 0.25)];
    const q3 = sorted[Math.floor(sorted.length * 0.75)];
    const iqr = q3 - q1;
    const lowerBound = q1 - 1.5 * iqr;
    const upperBound = q3 + 1.5 * iqr;

    const outliers = values.filter(v => v < lowerBound || v > upperBound);
    return outliers.length / values.length;
  }

  private calculateStandardDeviation(values: number[]): number {
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    return Math.sqrt(variance);
  }

  private detectSeasonLength(values: number[]): number {
    // Simplified season length detection
    const maxPeriod = Math.min(values.length / 3, 48);
    let bestPeriod = 0;
    let bestAutocorr = 0;

    for (let period = 2; period < maxPeriod; period++) {
      const autocorr = Math.abs(this.calculateAutocorrelation(values, period));
      if (autocorr > bestAutocorr) {
        bestAutocorr = autocorr;
        bestPeriod = period;
      }
    }

    return bestAutocorr > 0.3 ? bestPeriod : 0;
  }

  private extractSeasonalComponent(values: number[], seasonLength: number): number[] {
    const seasonal = new Array(seasonLength).fill(0);
    const counts = new Array(seasonLength).fill(0);

    for (let i = 0; i < values.length; i++) {
      const seasonIndex = i % seasonLength;
      seasonal[seasonIndex] += values[i];
      counts[seasonIndex]++;
    }

    return seasonal.map((sum, i) => sum / Math.max(counts[i], 1));
  }

  private prepareFeatureVector(features: Record<string, number>): number[] {
    const keys = Object.keys(features).sort();
    return keys.map(key => features[key] || 0);
  }

  private getFeatureBaseline(features: Record<string, number>): Record<string, number> {
    const baseline: Record<string, number> = {};

    for (const [feature, value] of Object.entries(features)) {
      const baselineValues = this.featureBaselines.get(feature);
      if (baselineValues && baselineValues.length > 0) {
        baseline[feature] = baselineValues.reduce((sum, v) => sum + v, 0) / baselineValues.length;
      } else {
        baseline[feature] = value;
      }
    }

    return baseline;
  }

  async trainModel(
    metrics: ChainMetrics[],
    traces: ChainTrace[]
  ): Promise<void> {
    console.log('Training anomaly detection models...');

    // Extract features for training
    const trainingData = this.prepareTrainingData(metrics, traces);

    // Train isolation forest
    await this.trainIsolationForest(trainingData);

    // Train LSTM for time series prediction
    await this.trainLSTM(trainingData);

    // Train SVM one-class
    await this.trainSVM(trainingData);

    console.log('Anomaly detection model training completed');
  }

  async loadModel(version: string): Promise<void> {
    console.log(`Loading anomaly detection model version: ${version}`);
    // Implementation would load serialized models
  }

  private prepareTrainingData(metrics: ChainMetrics[], traces: ChainTrace[]): any {
    // Prepare training data from metrics and traces
    return {
      features: metrics.map(m => [m.executionTime, m.throughput, m.latency, m.errorCount]),
      timeSeries: metrics.map(m => m.executionTime),
      labels: metrics.map(m => m.errorCount > 0 ? 1 : 0) // 1 for anomaly, 0 for normal
    };
  }

  private async trainIsolationForest(data: any): Promise<void> {
    // Mock implementation - would use real ML library
    console.log('Training Isolation Forest model...');
  }

  private async trainLSTM(data: any): Promise<void> {
    // Mock implementation - would use real ML library
    console.log('Training LSTM model...');
  }

  private async trainSVM(data: any): Promise<void> {
    // Mock implementation - would use real ML library
    console.log('Training SVM one-class model...');
  }
}