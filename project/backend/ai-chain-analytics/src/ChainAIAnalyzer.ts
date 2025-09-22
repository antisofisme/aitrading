/**
 * AI-Powered Chain Analyzer
 * Core AI orchestration for chain analysis with pattern recognition and optimization
 */

import { EventEmitter } from 'events';
import {
  ChainMetrics,
  ChainTrace,
  ChainAnalyticsResult,
  AIAnalysisConfig,
  MLModelConfig,
  ModelVersion,
  ChainDependencyGraph,
  AnalysisRecommendation
} from '../types';
import { ChainAnomalyDetector } from './ChainAnomalyDetector';
import { ChainPatternRecognizer } from './ChainPatternRecognizer';
import { ChainPredictor } from './ChainPredictor';
import { ModelVersionManager } from './ModelVersionManager';
import { FeatureExtractor } from '../utils/FeatureExtractor';
import { StreamingProcessor } from '../streaming/StreamingProcessor';

export class ChainAIAnalyzer extends EventEmitter {
  private anomalyDetector: ChainAnomalyDetector;
  private patternRecognizer: ChainPatternRecognizer;
  private predictor: ChainPredictor;
  private modelVersionManager: ModelVersionManager;
  private featureExtractor: FeatureExtractor;
  private streamingProcessor: StreamingProcessor;
  private config: AIAnalysisConfig;
  private isInitialized: boolean = false;
  private analysisCache: Map<string, ChainAnalyticsResult> = new Map();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  constructor(config: AIAnalysisConfig) {
    super();
    this.config = config;
    this.anomalyDetector = new ChainAnomalyDetector();
    this.patternRecognizer = new ChainPatternRecognizer();
    this.predictor = new ChainPredictor();
    this.modelVersionManager = new ModelVersionManager();
    this.featureExtractor = new FeatureExtractor();
    this.streamingProcessor = new StreamingProcessor({
      batchSize: 100,
      windowSizeMinutes: 15,
      slidingWindowMinutes: 5,
      bufferSize: 1000,
      processingIntervalMs: 30000,
      retentionDays: 30
    });
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing AI Chain Analyzer...');

      // Initialize components
      await Promise.all([
        this.anomalyDetector.initialize(),
        this.patternRecognizer.initialize(),
        this.predictor.initialize(),
        this.modelVersionManager.initialize(),
        this.streamingProcessor.initialize()
      ]);

      // Load active models
      await this.loadActiveModels();

      // Setup real-time processing
      if (this.config.enableRealTimeAnalysis) {
        this.setupRealTimeProcessing();
      }

      this.isInitialized = true;
      this.emit('initialized');
      console.log('AI Chain Analyzer initialized successfully');
    } catch (error) {
      console.error('Failed to initialize AI Chain Analyzer:', error);
      throw error;
    }
  }

  async analyzeChain(
    chainId: string,
    metrics: ChainMetrics[],
    traces: ChainTrace[],
    realTime: boolean = false
  ): Promise<ChainAnalyticsResult> {
    if (!this.isInitialized) {
      throw new Error('AI Chain Analyzer not initialized');
    }

    const cacheKey = `${chainId}_${Date.now()}`;

    // Check cache for recent analysis
    if (!realTime && this.analysisCache.has(cacheKey)) {
      const cached = this.analysisCache.get(cacheKey)!;
      if (Date.now() - cached.timestamp < this.CACHE_TTL) {
        return cached;
      }
    }

    try {
      console.log(`Starting AI analysis for chain: ${chainId}`);

      // Extract features from metrics and traces
      const features = await this.featureExtractor.extractFeatures(metrics, traces);

      // Build dependency graph
      const dependencyGraph = await this.buildDependencyGraph(traces);

      // Run parallel analysis
      const [anomalies, patterns, predictions] = await Promise.all([
        this.config.enableAnomalyDetection
          ? this.anomalyDetector.detectAnomalies(chainId, features, metrics)
          : Promise.resolve([]),
        this.config.enablePatternRecognition
          ? this.patternRecognizer.recognizePatterns(chainId, traces, features)
          : Promise.resolve([]),
        this.config.enablePredictiveAnalysis
          ? this.predictor.predictFailures(chainId, features, dependencyGraph)
          : Promise.resolve([])
      ]);

      // Generate recommendations
      const recommendations = await this.generateRecommendations(
        anomalies,
        patterns,
        predictions,
        dependencyGraph
      );

      // Calculate overall health and risk score
      const { overallHealth, riskScore } = this.calculateHealthScore(
        anomalies,
        patterns,
        predictions
      );

      const result: ChainAnalyticsResult = {
        analysisId: `analysis_${chainId}_${Date.now()}`,
        chainId,
        timestamp: Date.now(),
        anomalies,
        patterns,
        predictions,
        recommendations,
        overallHealth,
        riskScore
      };

      // Cache result
      this.analysisCache.set(cacheKey, result);

      // Emit analysis event
      this.emit('analysisComplete', result);

      // Store analysis for training
      await this.storeAnalysisForTraining(result, features);

      return result;
    } catch (error) {
      console.error(`Failed to analyze chain ${chainId}:`, error);
      throw error;
    }
  }

  async analyzeMultipleChains(
    chainIds: string[],
    lookbackHours: number = 24
  ): Promise<ChainAnalyticsResult[]> {
    console.log(`Analyzing ${chainIds.length} chains with ${lookbackHours}h lookback`);

    const results = await Promise.allSettled(
      chainIds.map(async (chainId) => {
        const metrics = await this.getChainMetrics(chainId, lookbackHours);
        const traces = await this.getChainTraces(chainId, lookbackHours);
        return this.analyzeChain(chainId, metrics, traces);
      })
    );

    const successful = results
      .filter((result): result is PromiseFulfilledResult<ChainAnalyticsResult> =>
        result.status === 'fulfilled'
      )
      .map(result => result.value);

    const failed = results.filter(result => result.status === 'rejected');

    if (failed.length > 0) {
      console.warn(`${failed.length} chain analyses failed`);
    }

    return successful;
  }

  async trainModels(
    trainingData: {
      metrics: ChainMetrics[];
      traces: ChainTrace[];
      labels?: any[];
    },
    modelTypes: string[] = ['anomaly', 'pattern', 'prediction']
  ): Promise<void> {
    console.log('Training AI models...');

    const trainingPromises = [];

    if (modelTypes.includes('anomaly')) {
      trainingPromises.push(
        this.anomalyDetector.trainModel(trainingData.metrics, trainingData.traces)
      );
    }

    if (modelTypes.includes('pattern')) {
      trainingPromises.push(
        this.patternRecognizer.trainModel(trainingData.traces, trainingData.labels)
      );
    }

    if (modelTypes.includes('prediction')) {
      trainingPromises.push(
        this.predictor.trainModel(trainingData.metrics, trainingData.traces, trainingData.labels)
      );
    }

    await Promise.all(trainingPromises);

    // Update model versions
    await this.modelVersionManager.createNewVersions();

    console.log('Model training completed');
    this.emit('modelsRetrained');
  }

  async updateModels(): Promise<void> {
    if (Date.now() - this.modelVersionManager.getLastUpdateTime() < this.config.modelUpdateFrequency) {
      return;
    }

    console.log('Updating AI models...');

    // Get recent training data
    const recentData = await this.getRecentTrainingData();

    // Retrain models
    await this.trainModels(recentData);

    console.log('AI models updated successfully');
  }

  private async loadActiveModels(): Promise<void> {
    const activeVersions = await this.modelVersionManager.getActiveVersions();

    await Promise.all([
      this.anomalyDetector.loadModel(activeVersions.anomaly),
      this.patternRecognizer.loadModel(activeVersions.pattern),
      this.predictor.loadModel(activeVersions.prediction)
    ]);
  }

  private setupRealTimeProcessing(): void {
    this.streamingProcessor.on('batchReady', async (batch) => {
      try {
        const chainGroups = this.groupByChain(batch);

        await Promise.all(
          Object.entries(chainGroups).map(async ([chainId, data]) => {
            const result = await this.analyzeChain(chainId, data.metrics, data.traces, true);

            // Emit real-time alerts for critical issues
            if (result.overallHealth === 'critical' || result.riskScore > 0.8) {
              this.emit('criticalAlert', result);
            }
          })
        );
      } catch (error) {
        console.error('Real-time processing error:', error);
        this.emit('processingError', error);
      }
    });

    console.log('Real-time processing enabled');
  }

  private async buildDependencyGraph(traces: ChainTrace[]): Promise<ChainDependencyGraph> {
    // Analyze step dependencies and build graph
    const nodes = new Map();
    const edges = new Map();

    for (const trace of traces) {
      for (const step of trace.steps) {
        // Create or update node
        if (!nodes.has(step.stepId)) {
          nodes.set(step.stepId, {
            nodeId: step.stepId,
            stepType: step.stepType,
            avgExecutionTime: step.duration,
            failureRate: step.status === 'failure' ? 1 : 0,
            resourceUsage: {},
            importance: 1
          });
        } else {
          const node = nodes.get(step.stepId);
          node.avgExecutionTime = (node.avgExecutionTime + step.duration) / 2;
          node.failureRate = (node.failureRate + (step.status === 'failure' ? 1 : 0)) / 2;
        }

        // Create edges for dependencies
        for (const dep of step.dependencies) {
          const edgeKey = `${dep}_${step.stepId}`;
          if (!edges.has(edgeKey)) {
            edges.set(edgeKey, {
              source: dep,
              target: step.stepId,
              weight: 1,
              dependency_type: 'sequential',
              latency: 0
            });
          }
        }
      }
    }

    // Find critical path and bottlenecks
    const criticalPath = this.findCriticalPath(Array.from(nodes.values()), Array.from(edges.values()));
    const bottlenecks = this.identifyBottlenecks(Array.from(nodes.values()));

    return {
      nodes: Array.from(nodes.values()),
      edges: Array.from(edges.values()),
      criticalPath,
      bottlenecks
    };
  }

  private findCriticalPath(nodes: any[], edges: any[]): string[] {
    // Simplified critical path algorithm
    const sorted = this.topologicalSort(nodes, edges);
    return sorted.slice(0, Math.ceil(sorted.length * 0.2)); // Top 20% by execution time
  }

  private identifyBottlenecks(nodes: any[]): string[] {
    return nodes
      .filter(node => node.avgExecutionTime > 1000 || node.failureRate > 0.1)
      .map(node => node.nodeId);
  }

  private topologicalSort(nodes: any[], edges: any[]): string[] {
    // Implementation of topological sort for dependency ordering
    return nodes
      .sort((a, b) => b.avgExecutionTime - a.avgExecutionTime)
      .map(node => node.nodeId);
  }

  private async generateRecommendations(
    anomalies: any[],
    patterns: any[],
    predictions: any[],
    dependencyGraph: ChainDependencyGraph
  ): Promise<AnalysisRecommendation[]> {
    const recommendations: AnalysisRecommendation[] = [];

    // Anomaly-based recommendations
    for (const anomaly of anomalies) {
      if (anomaly.severity === 'high' || anomaly.severity === 'critical') {
        recommendations.push({
          type: 'alert',
          priority: anomaly.severity === 'critical' ? 'urgent' : 'high',
          description: `Address ${anomaly.anomalyType} anomaly: ${anomaly.description}`,
          estimatedImpact: 'High performance improvement',
          implementationComplexity: 'medium',
          estimatedEffort: '2-4 hours'
        });
      }
    }

    // Pattern-based recommendations
    for (const pattern of patterns) {
      if (pattern.impact === 'negative' && pattern.confidence > 0.8) {
        recommendations.push({
          type: 'optimization',
          priority: 'medium',
          description: `Optimize recurring pattern: ${pattern.description}`,
          estimatedImpact: 'Moderate efficiency gain',
          implementationComplexity: 'medium',
          estimatedEffort: '4-8 hours'
        });
      }
    }

    // Prediction-based recommendations
    for (const prediction of predictions) {
      if (prediction.probability > 0.7) {
        recommendations.push({
          type: 'maintenance',
          priority: 'high',
          description: `Preventive action needed: ${prediction.estimatedImpact}`,
          estimatedImpact: 'Prevent system failure',
          implementationComplexity: 'low',
          estimatedEffort: '1-2 hours'
        });
      }
    }

    // Dependency graph recommendations
    for (const bottleneck of dependencyGraph.bottlenecks) {
      recommendations.push({
        type: 'scaling',
        priority: 'medium',
        description: `Scale bottleneck step: ${bottleneck}`,
        estimatedImpact: 'Significant throughput improvement',
        implementationComplexity: 'high',
        estimatedEffort: '1-2 days'
      });
    }

    return recommendations.slice(0, 10); // Limit to top 10 recommendations
  }

  private calculateHealthScore(
    anomalies: any[],
    patterns: any[],
    predictions: any[]
  ): { overallHealth: 'excellent' | 'good' | 'warning' | 'critical'; riskScore: number } {
    let riskScore = 0;

    // Factor in anomalies
    for (const anomaly of anomalies) {
      switch (anomaly.severity) {
        case 'critical': riskScore += 0.4; break;
        case 'high': riskScore += 0.3; break;
        case 'medium': riskScore += 0.2; break;
        case 'low': riskScore += 0.1; break;
      }
    }

    // Factor in negative patterns
    const negativePatterns = patterns.filter(p => p.impact === 'negative');
    riskScore += negativePatterns.length * 0.1;

    // Factor in predictions
    for (const prediction of predictions) {
      if (prediction.predictionType === 'failure') {
        riskScore += prediction.probability * 0.5;
      }
    }

    // Normalize risk score
    riskScore = Math.min(riskScore, 1);

    let overallHealth: 'excellent' | 'good' | 'warning' | 'critical';
    if (riskScore < 0.2) overallHealth = 'excellent';
    else if (riskScore < 0.4) overallHealth = 'good';
    else if (riskScore < 0.7) overallHealth = 'warning';
    else overallHealth = 'critical';

    return { overallHealth, riskScore };
  }

  private async storeAnalysisForTraining(
    result: ChainAnalyticsResult,
    features: any
  ): Promise<void> {
    // Store analysis results for future model training
    // This would typically save to a training database
    console.log(`Storing analysis ${result.analysisId} for training`);
  }

  private async getChainMetrics(chainId: string, lookbackHours: number): Promise<ChainMetrics[]> {
    // Mock implementation - would integrate with ClickHouse
    return [];
  }

  private async getChainTraces(chainId: string, lookbackHours: number): Promise<ChainTrace[]> {
    // Mock implementation - would integrate with ClickHouse
    return [];
  }

  private async getRecentTrainingData(): Promise<{
    metrics: ChainMetrics[];
    traces: ChainTrace[];
    labels?: any[];
  }> {
    // Mock implementation - would get recent data for retraining
    return { metrics: [], traces: [] };
  }

  private groupByChain(batch: any[]): Record<string, { metrics: ChainMetrics[]; traces: ChainTrace[] }> {
    const groups: Record<string, { metrics: ChainMetrics[]; traces: ChainTrace[] }> = {};

    for (const item of batch) {
      if (!groups[item.chainId]) {
        groups[item.chainId] = { metrics: [], traces: [] };
      }

      if (item.type === 'metric') {
        groups[item.chainId].metrics.push(item);
      } else if (item.type === 'trace') {
        groups[item.chainId].traces.push(item);
      }
    }

    return groups;
  }

  async getAnalysisHistory(chainId: string, days: number = 7): Promise<ChainAnalyticsResult[]> {
    // Mock implementation - would query historical analysis results
    return [];
  }

  async exportModel(modelType: string, version: string): Promise<Buffer> {
    return this.modelVersionManager.exportModel(modelType, version);
  }

  async importModel(modelType: string, modelData: Buffer): Promise<string> {
    return this.modelVersionManager.importModel(modelType, modelData);
  }
}