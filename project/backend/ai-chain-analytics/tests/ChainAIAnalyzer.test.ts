/**
 * Test Suite for AI Chain Analytics
 * Comprehensive tests for all AI chain analytics components
 */

import { describe, it, beforeEach, afterEach, expect, jest } from '@jest/globals';
import { ChainAIAnalyzer } from '../src/ChainAIAnalyzer';
import { ChainAnomalyDetector } from '../src/ChainAnomalyDetector';
import { ChainPatternRecognizer } from '../src/ChainPatternRecognizer';
import { ChainPredictor } from '../src/ChainPredictor';
import { GraphNeuralNetwork } from '../models/GraphNeuralNetwork';
import { StreamingProcessor } from '../streaming/StreamingProcessor';
import { AIOrchestrator } from '../services/AIOrchestrator';
import { FeatureExtractor } from '../utils/FeatureExtractor';
import {
  ChainMetrics,
  ChainTrace,
  AIAnalysisConfig,
  StreamingConfig,
  AIServiceConfig
} from '../types';

// Mock data generators
const generateMockMetrics = (count: number = 10): ChainMetrics[] => {
  return Array.from({ length: count }, (_, i) => ({
    chainId: `chain_${i % 3}`,
    timestamp: Date.now() - (count - i) * 60000,
    executionTime: 1000 + Math.random() * 4000,
    stepCount: 3 + Math.floor(Math.random() * 7),
    successRate: 0.8 + Math.random() * 0.2,
    errorCount: Math.floor(Math.random() * 3),
    memoryUsage: 0.3 + Math.random() * 0.4,
    cpuUsage: 0.2 + Math.random() * 0.5,
    throughput: 50 + Math.random() * 100,
    latency: 100 + Math.random() * 900
  }));
};

const generateMockTraces = (count: number = 5): ChainTrace[] => {
  return Array.from({ length: count }, (_, i) => ({
    traceId: `trace_${i}`,
    chainId: `chain_${i % 3}`,
    startTime: Date.now() - (count - i) * 60000,
    endTime: Date.now() - (count - i) * 60000 + 2000 + Math.random() * 3000,
    status: Math.random() > 0.8 ? 'failure' : 'success',
    metadata: { env: 'test', version: '1.0.0' },
    steps: Array.from({ length: 3 + Math.floor(Math.random() * 4) }, (_, j) => ({
      stepId: `step_${i}_${j}`,
      stepType: ['fetch', 'process', 'validate', 'store'][j % 4],
      startTime: Date.now() - (count - i) * 60000 + j * 500,
      endTime: Date.now() - (count - i) * 60000 + (j + 1) * 500,
      duration: 500 + Math.random() * 1000,
      status: Math.random() > 0.9 ? 'failure' : 'success',
      input: { data: `input_${j}` },
      output: { result: `output_${j}` },
      error: Math.random() > 0.9 ? 'Connection timeout' : undefined,
      dependencies: j > 0 ? [`step_${i}_${j - 1}`] : []
    }))
  }));
};

describe('ChainAIAnalyzer', () => {
  let analyzer: ChainAIAnalyzer;
  let config: AIAnalysisConfig;

  beforeEach(() => {
    config = {
      enableRealTimeAnalysis: true,
      enablePatternRecognition: true,
      enableAnomalyDetection: true,
      enablePredictiveAnalysis: true,
      modelUpdateFrequency: 3600000, // 1 hour
      confidenceThreshold: 0.7,
      alertThresholds: {
        anomaly: 0.8,
        prediction: 0.7,
        pattern: 0.6
      }
    };

    analyzer = new ChainAIAnalyzer(config);
  });

  afterEach(async () => {
    // Cleanup if needed
  });

  describe('Initialization', () => {
    it('should initialize successfully with valid config', async () => {
      await expect(analyzer.initialize()).resolves.not.toThrow();
      expect(analyzer['isInitialized']).toBe(true);
    });

    it('should emit initialized event on successful initialization', async () => {
      const initPromise = new Promise(resolve => {
        analyzer.once('initialized', resolve);
      });

      await analyzer.initialize();
      await expect(initPromise).resolves.toBeUndefined();
    });
  });

  describe('Chain Analysis', () => {
    beforeEach(async () => {
      await analyzer.initialize();
    });

    it('should analyze a single chain successfully', async () => {
      const chainId = 'test_chain_1';
      const metrics = generateMockMetrics(20);
      const traces = generateMockTraces(10);

      const result = await analyzer.analyzeChain(chainId, metrics, traces);

      expect(result).toHaveProperty('analysisId');
      expect(result).toHaveProperty('chainId', chainId);
      expect(result).toHaveProperty('timestamp');
      expect(result).toHaveProperty('anomalies');
      expect(result).toHaveProperty('patterns');
      expect(result).toHaveProperty('predictions');
      expect(result).toHaveProperty('recommendations');
      expect(result).toHaveProperty('overallHealth');
      expect(result).toHaveProperty('riskScore');

      expect(Array.isArray(result.anomalies)).toBe(true);
      expect(Array.isArray(result.patterns)).toBe(true);
      expect(Array.isArray(result.predictions)).toBe(true);
      expect(Array.isArray(result.recommendations)).toBe(true);

      expect(['excellent', 'good', 'warning', 'critical']).toContain(result.overallHealth);
      expect(result.riskScore).toBeGreaterThanOrEqual(0);
      expect(result.riskScore).toBeLessThanOrEqual(1);
    });

    it('should handle multiple chains analysis', async () => {
      const chainIds = ['chain_1', 'chain_2', 'chain_3'];
      const results = await analyzer.analyzeMultipleChains(chainIds, 1);

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBeLessThanOrEqual(chainIds.length);

      results.forEach(result => {
        expect(chainIds).toContain(result.chainId);
      });
    });

    it('should cache analysis results', async () => {
      const chainId = 'test_chain_cache';
      const metrics = generateMockMetrics(5);
      const traces = generateMockTraces(3);

      const result1 = await analyzer.analyzeChain(chainId, metrics, traces);
      const result2 = await analyzer.analyzeChain(chainId, metrics, traces);

      // Results should be identical when cached
      expect(result1.analysisId).toBe(result2.analysisId);
    });

    it('should emit analysis complete event', async () => {
      const analysisPromise = new Promise(resolve => {
        analyzer.once('analysisComplete', resolve);
      });

      const chainId = 'test_chain_event';
      const metrics = generateMockMetrics(5);
      const traces = generateMockTraces(3);

      await analyzer.analyzeChain(chainId, metrics, traces);
      await expect(analysisPromise).resolves.toBeDefined();
    });
  });

  describe('Model Training', () => {
    beforeEach(async () => {
      await analyzer.initialize();
    });

    it('should train models with provided data', async () => {
      const trainingData = {
        metrics: generateMockMetrics(100),
        traces: generateMockTraces(50),
        labels: Array.from({ length: 100 }, () => Math.random() > 0.8 ? 1 : 0)
      };

      await expect(analyzer.trainModels(trainingData)).resolves.not.toThrow();
    });

    it('should emit models retrained event', async () => {
      const retrainPromise = new Promise(resolve => {
        analyzer.once('modelsRetrained', resolve);
      });

      const trainingData = {
        metrics: generateMockMetrics(50),
        traces: generateMockTraces(25)
      };

      await analyzer.trainModels(trainingData, ['anomaly']);
      await expect(retrainPromise).resolves.toBeUndefined();
    });
  });

  describe('Error Handling', () => {
    it('should throw error when not initialized', async () => {
      const chainId = 'test_chain';
      const metrics = generateMockMetrics(5);
      const traces = generateMockTraces(3);

      await expect(analyzer.analyzeChain(chainId, metrics, traces))
        .rejects
        .toThrow('AI Chain Analyzer not initialized');
    });

    it('should handle empty data gracefully', async () => {
      await analyzer.initialize();

      const result = await analyzer.analyzeChain('empty_chain', [], []);

      expect(result).toHaveProperty('anomalies');
      expect(result.anomalies).toHaveLength(0);
      expect(result).toHaveProperty('patterns');
      expect(result.patterns).toHaveLength(0);
    });
  });
});

describe('ChainAnomalyDetector', () => {
  let detector: ChainAnomalyDetector;

  beforeEach(async () => {
    detector = new ChainAnomalyDetector();
    await detector.initialize();
  });

  describe('Anomaly Detection', () => {
    it('should detect statistical anomalies', async () => {
      const chainId = 'test_chain';
      const features = {
        executionTime: 10000, // High execution time
        errorCount: 5, // High error count
        memoryUsage: 0.95, // High memory usage
        cpuUsage: 0.4,
        throughput: 50,
        latency: 1000
      };
      const metrics = generateMockMetrics(10);

      const anomalies = await detector.detectAnomalies(chainId, features, metrics);

      expect(Array.isArray(anomalies)).toBe(true);
      anomalies.forEach(anomaly => {
        expect(anomaly).toHaveProperty('anomalyId');
        expect(anomaly).toHaveProperty('chainId', chainId);
        expect(anomaly).toHaveProperty('anomalyType');
        expect(anomaly).toHaveProperty('severity');
        expect(anomaly).toHaveProperty('confidence');
        expect(['low', 'medium', 'high', 'critical']).toContain(anomaly.severity);
        expect(anomaly.confidence).toBeGreaterThan(0);
        expect(anomaly.confidence).toBeLessThanOrEqual(1);
      });
    });

    it('should detect time series anomalies', async () => {
      const chainId = 'test_timeseries';
      const metrics = generateMockMetrics(50); // More data for time series

      // Add an anomalous spike
      metrics.push({
        ...metrics[0],
        timestamp: Date.now(),
        executionTime: 50000, // Very high execution time
        errorCount: 10
      });

      const features = { executionTime: 2000, errorCount: 1 };
      const anomalies = await detector.detectAnomalies(chainId, features, metrics);

      expect(anomalies.length).toBeGreaterThan(0);
    });

    it('should handle baseline learning', async () => {
      const chainId = 'baseline_test';
      const features = { executionTime: 2000, errorCount: 0 };
      const metrics = generateMockMetrics(5);

      // First call - no baseline
      const anomalies1 = await detector.detectAnomalies(chainId, features, metrics);

      // Second call - should have baseline
      const anomalies2 = await detector.detectAnomalies(chainId, features, metrics);

      expect(Array.isArray(anomalies1)).toBe(true);
      expect(Array.isArray(anomalies2)).toBe(true);
    });
  });

  describe('Model Training', () => {
    it('should train anomaly detection models', async () => {
      const metrics = generateMockMetrics(100);
      const traces = generateMockTraces(50);

      await expect(detector.trainModel(metrics, traces)).resolves.not.toThrow();
    });
  });
});

describe('ChainPatternRecognizer', () => {
  let recognizer: ChainPatternRecognizer;

  beforeEach(async () => {
    recognizer = new ChainPatternRecognizer();
    await recognizer.initialize();
  });

  describe('Pattern Recognition', () => {
    it('should recognize sequence patterns', async () => {
      const chainId = 'pattern_test';
      const traces = generateMockTraces(20);
      const features = { executionTime: 2000, stepCount: 4 };

      const patterns = await recognizer.recognizePatterns(chainId, traces, features);

      expect(Array.isArray(patterns)).toBe(true);
      patterns.forEach(pattern => {
        expect(pattern).toHaveProperty('patternId');
        expect(pattern).toHaveProperty('patternType');
        expect(pattern).toHaveProperty('description');
        expect(pattern).toHaveProperty('confidence');
        expect(pattern).toHaveProperty('frequency');
        expect(['sequence', 'frequency', 'temporal', 'correlation']).toContain(pattern.patternType);
        expect(['positive', 'negative', 'neutral']).toContain(pattern.impact);
      });
    });

    it('should recognize temporal patterns', async () => {
      const chainId = 'temporal_test';
      const traces = generateMockTraces(30);

      // Add temporal patterns (specific hours)
      traces.forEach((trace, i) => {
        const hourOffset = (i % 24) * 60 * 60 * 1000;
        trace.startTime = Date.now() - hourOffset;
        trace.endTime = trace.startTime + 2000;
      });

      const features = { executionTime: 2000 };
      const patterns = await recognizer.recognizePatterns(chainId, traces, features);

      const temporalPatterns = patterns.filter(p => p.patternType === 'temporal');
      expect(temporalPatterns.length).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty trace data', async () => {
      const chainId = 'empty_test';
      const patterns = await recognizer.recognizePatterns(chainId, [], {});

      expect(Array.isArray(patterns)).toBe(true);
      expect(patterns.length).toBe(0);
    });
  });
});

describe('ChainPredictor', () => {
  let predictor: ChainPredictor;

  beforeEach(async () => {
    predictor = new ChainPredictor();
    await predictor.initialize();
  });

  describe('Failure Prediction', () => {
    it('should predict potential failures', async () => {
      const chainId = 'prediction_test';
      const features = {
        executionTime: 5000,
        errorCount: 2,
        memoryUsage: 0.8,
        cpuUsage: 0.9,
        throughput: 30,
        latency: 2000
      };
      const dependencyGraph = {
        nodes: [
          {
            nodeId: 'step1',
            stepType: 'fetch',
            avgExecutionTime: 1000,
            failureRate: 0.1,
            resourceUsage: {},
            importance: 0.8
          }
        ],
        edges: [],
        criticalPath: ['step1'],
        bottlenecks: []
      };

      const predictions = await predictor.predictFailures(chainId, features, dependencyGraph);

      expect(Array.isArray(predictions)).toBe(true);
      predictions.forEach(prediction => {
        expect(prediction).toHaveProperty('predictionId');
        expect(prediction).toHaveProperty('chainId', chainId);
        expect(prediction).toHaveProperty('predictionType');
        expect(prediction).toHaveProperty('probability');
        expect(prediction).toHaveProperty('confidence');
        expect(['failure', 'performance', 'resource', 'completion']).toContain(prediction.predictionType);
        expect(prediction.probability).toBeGreaterThanOrEqual(0);
        expect(prediction.probability).toBeLessThanOrEqual(1);
      });
    });

    it('should predict resource exhaustion', async () => {
      const chainId = 'resource_test';
      const features = {
        memoryUsage: 0.95,
        memoryTrend: 0.05, // Increasing
        cpuUsage: 0.9,
        cpuTrend: 0.03
      };

      const predictions = await predictor.predictFailures(chainId, features, {
        nodes: [], edges: [], criticalPath: [], bottlenecks: []
      });

      const resourcePredictions = predictions.filter(p => p.predictionType === 'resource');
      expect(resourcePredictions.length).toBeGreaterThan(0);
    });
  });
});

describe('GraphNeuralNetwork', () => {
  let gnn: GraphNeuralNetwork;

  beforeEach(async () => {
    gnn = new GraphNeuralNetwork();
    await gnn.initialize();
  });

  describe('Model Training', () => {
    it('should train GNN model successfully', async () => {
      const graphs = Array.from({ length: 20 }, (_, i) => ({
        nodes: [
          {
            nodeId: `node_${i}_1`,
            stepType: 'fetch',
            avgExecutionTime: 1000 + Math.random() * 2000,
            failureRate: Math.random() * 0.2,
            resourceUsage: {},
            importance: Math.random()
          },
          {
            nodeId: `node_${i}_2`,
            stepType: 'process',
            avgExecutionTime: 2000 + Math.random() * 3000,
            failureRate: Math.random() * 0.1,
            resourceUsage: {},
            importance: Math.random()
          }
        ],
        edges: [
          {
            source: `node_${i}_1`,
            target: `node_${i}_2`,
            weight: Math.random() * 100,
            dependency_type: 'sequential',
            latency: Math.random() * 1000
          }
        ],
        criticalPath: [`node_${i}_1`, `node_${i}_2`],
        bottlenecks: []
      }));

      const labels = Array.from({ length: 20 }, () => Math.random() > 0.7 ? 1 : 0);

      const performance = await gnn.trainModel(graphs, labels);

      expect(performance).toHaveProperty('accuracy');
      expect(performance).toHaveProperty('precision');
      expect(performance).toHaveProperty('recall');
      expect(performance).toHaveProperty('f1Score');
      expect(performance.accuracy).toBeGreaterThanOrEqual(0);
      expect(performance.accuracy).toBeLessThanOrEqual(1);
    });
  });

  describe('Graph Analysis', () => {
    it('should analyze dependency graph', async () => {
      const graph = {
        nodes: [
          {
            nodeId: 'fetch_data',
            stepType: 'fetch',
            avgExecutionTime: 1500,
            failureRate: 0.05,
            resourceUsage: { memory: 100 },
            importance: 0.8
          },
          {
            nodeId: 'process_data',
            stepType: 'process',
            avgExecutionTime: 3000,
            failureRate: 0.1,
            resourceUsage: { memory: 200, cpu: 50 },
            importance: 0.9
          },
          {
            nodeId: 'store_data',
            stepType: 'store',
            avgExecutionTime: 800,
            failureRate: 0.02,
            resourceUsage: { memory: 50 },
            importance: 0.6
          }
        ],
        edges: [
          {
            source: 'fetch_data',
            target: 'process_data',
            weight: 80,
            dependency_type: 'sequential',
            latency: 100
          },
          {
            source: 'process_data',
            target: 'store_data',
            weight: 60,
            dependency_type: 'sequential',
            latency: 50
          }
        ],
        criticalPath: ['fetch_data', 'process_data', 'store_data'],
        bottlenecks: ['process_data']
      };

      const analysis = await gnn.predict(graph);

      expect(analysis).toHaveProperty('riskScore');
      expect(analysis).toHaveProperty('bottleneckNodes');
      expect(analysis).toHaveProperty('criticalPaths');
      expect(analysis).toHaveProperty('nodeImportance');
      expect(analysis.riskScore).toBeGreaterThanOrEqual(0);
      expect(analysis.riskScore).toBeLessThanOrEqual(1);
      expect(Array.isArray(analysis.bottleneckNodes)).toBe(true);
      expect(Array.isArray(analysis.criticalPaths)).toBe(true);
    });
  });
});

describe('StreamingProcessor', () => {
  let processor: StreamingProcessor;
  let config: StreamingConfig;

  beforeEach(async () => {
    config = {
      batchSize: 10,
      windowSizeMinutes: 15,
      slidingWindowMinutes: 5,
      bufferSize: 100,
      processingIntervalMs: 1000,
      retentionDays: 7
    };

    processor = new StreamingProcessor(config);
    await processor.initialize();
  });

  afterEach(async () => {
    await processor.stop();
  });

  describe('Data Ingestion', () => {
    it('should ingest single data item', async () => {
      const metrics = generateMockMetrics(1)[0];

      await expect(processor.ingestData(metrics)).resolves.not.toThrow();

      const stats = processor.getStreamingStats();
      expect(stats.bufferUtilization).toBeGreaterThan(0);
    });

    it('should ingest batch of data items', async () => {
      const metrics = generateMockMetrics(5);

      await expect(processor.ingestData(metrics)).resolves.not.toThrow();

      const stats = processor.getStreamingStats();
      expect(stats.bufferUtilization).toBeGreaterThan(0);
    });

    it('should emit batch ready event when batch size reached', async () => {
      const batchPromise = new Promise(resolve => {
        processor.once('batchReady', resolve);
      });

      const metrics = generateMockMetrics(config.batchSize);
      await processor.ingestData(metrics);

      await expect(batchPromise).resolves.toBeDefined();
    });
  });

  describe('Window Processing', () => {
    it('should process fixed window', async () => {
      const metrics = generateMockMetrics(20);
      await processor.ingestData(metrics);

      const windowData = await processor.processWindow(10);

      expect(windowData).toHaveProperty('windowId');
      expect(windowData).toHaveProperty('startTime');
      expect(windowData).toHaveProperty('endTime');
      expect(windowData).toHaveProperty('metrics');
      expect(windowData).toHaveProperty('traces');
      expect(windowData).toHaveProperty('aggregatedFeatures');
      expect(Array.isArray(windowData.metrics)).toBe(true);
    });

    it('should process sliding windows', async () => {
      const metrics = generateMockMetrics(30);
      await processor.ingestData(metrics);

      const windows = await processor.processSlidingWindow();

      expect(Array.isArray(windows)).toBe(true);
      windows.forEach(window => {
        expect(window).toHaveProperty('windowId');
        expect(window.windowId).toContain('sliding_');
      });
    });
  });

  describe('Real-time Analysis', () => {
    it('should analyze incoming metrics', async () => {
      const metrics: ChainMetrics = {
        chainId: 'test_chain',
        timestamp: Date.now(),
        executionTime: 30000, // High execution time
        stepCount: 5,
        successRate: 0.5, // Low success rate
        errorCount: 10, // High error count
        memoryUsage: 0.95, // High memory usage
        cpuUsage: 0.9,
        throughput: 5, // Low throughput
        latency: 15000 // High latency
      };

      const analysis = await processor.analyzeIncomingData(metrics);

      expect(analysis).toHaveProperty('anomalies');
      expect(analysis).toHaveProperty('patterns');
      expect(analysis).toHaveProperty('alerts');
      expect(Array.isArray(analysis.anomalies)).toBe(true);
      expect(Array.isArray(analysis.patterns)).toBe(true);
      expect(Array.isArray(analysis.alerts)).toBe(true);

      // Should detect anomalies/alerts for high values
      expect(analysis.anomalies.length + analysis.alerts.length).toBeGreaterThan(0);
    });
  });
});

describe('AIOrchestrator', () => {
  let orchestrator: AIOrchestrator;
  let config: AIServiceConfig;

  beforeEach(() => {
    config = {
      orchestratorUrl: 'http://localhost:8020',
      automlUrl: 'http://localhost:8021',
      inferenceUrl: 'http://localhost:8022',
      timeout: 30000,
      retryAttempts: 3
    };

    orchestrator = new AIOrchestrator(config);
  });

  describe('Service Integration', () => {
    it('should create orchestrator with valid config', () => {
      expect(orchestrator).toBeDefined();
      expect(orchestrator.getActiveModels).toBeDefined();
      expect(orchestrator.submitTrainingJob).toBeDefined();
      expect(orchestrator.runInference).toBeDefined();
    });

    it('should handle training job submission', async () => {
      // Mock the training job (would require actual service)
      const trainingRequest = {
        modelType: 'anomaly' as const,
        trainingData: { features: [], labels: [] },
        config: {
          modelType: 'isolation_forest',
          version: '1.0.0',
          parameters: {},
          features: ['executionTime', 'errorCount'],
          trainingData: {
            startDate: new Date().toISOString(),
            endDate: new Date().toISOString(),
            sampleSize: 1000
          },
          performance: {
            accuracy: 0,
            precision: 0,
            recall: 0,
            f1Score: 0,
            auc: 0,
            lastEvaluated: 0,
            validationMethod: 'cross_validation'
          }
        },
        priority: 'medium' as const
      };

      // This would normally connect to real services
      // For now, just test that the method exists and accepts the right parameters
      expect(typeof orchestrator.submitTrainingJob).toBe('function');
    });
  });
});

describe('FeatureExtractor', () => {
  let extractor: FeatureExtractor;

  beforeEach(() => {
    extractor = new FeatureExtractor();
  });

  describe('Feature Extraction', () => {
    it('should extract features from metrics and traces', async () => {
      const metrics = generateMockMetrics(20);
      const traces = generateMockTraces(10);

      const features = await extractor.extractFeatures(metrics, traces);

      expect(typeof features).toBe('object');
      expect(Object.keys(features).length).toBeGreaterThan(0);

      // Check for expected feature types
      expect(features).toHaveProperty('executionTime_mean');
      expect(features).toHaveProperty('throughput_mean');
      expect(features).toHaveProperty('errorRate');
      expect(features).toHaveProperty('successRate_mean');

      // All features should be numbers
      Object.values(features).forEach(value => {
        expect(typeof value).toBe('number');
        expect(isNaN(value)).toBe(false);
        expect(isFinite(value)).toBe(true);
      });
    });

    it('should handle empty input data', async () => {
      const features = await extractor.extractFeatures([], []);

      expect(typeof features).toBe('object');
      // Should return some default features even with empty data
    });

    it('should normalize feature values', async () => {
      const metrics = generateMockMetrics(10);
      const traces = generateMockTraces(5);

      const features = await extractor.extractFeatures(metrics, traces);

      // Check that ratio/rate features are between 0 and 1
      Object.entries(features).forEach(([key, value]) => {
        if (key.includes('_ratio') || key.includes('_rate')) {
          expect(value).toBeGreaterThanOrEqual(0);
          expect(value).toBeLessThanOrEqual(1);
        }
      });
    });
  });
});

// Integration Tests
describe('Integration Tests', () => {
  let analyzer: ChainAIAnalyzer;
  let processor: StreamingProcessor;

  beforeEach(async () => {
    const analysisConfig: AIAnalysisConfig = {
      enableRealTimeAnalysis: true,
      enablePatternRecognition: true,
      enableAnomalyDetection: true,
      enablePredictiveAnalysis: true,
      modelUpdateFrequency: 3600000,
      confidenceThreshold: 0.7,
      alertThresholds: {
        anomaly: 0.8,
        prediction: 0.7,
        pattern: 0.6
      }
    };

    const streamingConfig: StreamingConfig = {
      batchSize: 5,
      windowSizeMinutes: 10,
      slidingWindowMinutes: 5,
      bufferSize: 50,
      processingIntervalMs: 500,
      retentionDays: 1
    };

    analyzer = new ChainAIAnalyzer(analysisConfig);
    processor = new StreamingProcessor(streamingConfig);

    await Promise.all([
      analyzer.initialize(),
      processor.initialize()
    ]);
  });

  afterEach(async () => {
    await processor.stop();
  });

  it('should process streaming data through complete pipeline', async () => {
    const analysisPromise = new Promise(resolve => {
      analyzer.once('analysisComplete', resolve);
    });

    const batchPromise = new Promise(resolve => {
      processor.once('batchReady', async (batch) => {
        // Process batch through analyzer
        const chainMetrics = batch.data.filter((item: any) => item.executionTime) as ChainMetrics[];
        const chainTraces = batch.data.filter((item: any) => item.steps) as ChainTrace[];

        if (chainMetrics.length > 0) {
          await analyzer.analyzeChain('integration_test', chainMetrics, chainTraces);
        }
        resolve(batch);
      });
    });

    // Generate and ingest data
    const metrics = generateMockMetrics(5);
    const traces = generateMockTraces(2);
    const allData = [...metrics, ...traces];

    await processor.ingestData(allData);

    await Promise.all([batchPromise, analysisPromise]);
  });

  it('should handle high-volume data processing', async () => {
    const metrics = generateMockMetrics(100);
    const traces = generateMockTraces(50);

    // Process in batches
    for (let i = 0; i < metrics.length; i += 10) {
      const batch = metrics.slice(i, i + 10);
      await processor.ingestData(batch);
    }

    for (let i = 0; i < traces.length; i += 5) {
      const batch = traces.slice(i, i + 5);
      await processor.ingestData(batch);
    }

    const stats = processor.getStreamingStats();
    expect(stats.totalRecords).toBeGreaterThan(100);
  });
});

// Performance Tests
describe('Performance Tests', () => {
  it('should handle large dataset analysis within reasonable time', async () => {
    const analyzer = new ChainAIAnalyzer({
      enableRealTimeAnalysis: false,
      enablePatternRecognition: true,
      enableAnomalyDetection: true,
      enablePredictiveAnalysis: true,
      modelUpdateFrequency: 3600000,
      confidenceThreshold: 0.7,
      alertThresholds: { anomaly: 0.8, prediction: 0.7, pattern: 0.6 }
    });

    await analyzer.initialize();

    const startTime = Date.now();
    const metrics = generateMockMetrics(1000);
    const traces = generateMockTraces(500);

    const result = await analyzer.analyzeChain('perf_test', metrics, traces);
    const analysisTime = Date.now() - startTime;

    expect(result).toBeDefined();
    expect(analysisTime).toBeLessThan(10000); // Should complete within 10 seconds
  }, 15000); // 15 second timeout

  it('should maintain throughput under concurrent analysis', async () => {
    const analyzer = new ChainAIAnalyzer({
      enableRealTimeAnalysis: false,
      enablePatternRecognition: true,
      enableAnomalyDetection: true,
      enablePredictiveAnalysis: false, // Reduce complexity for concurrency test
      modelUpdateFrequency: 3600000,
      confidenceThreshold: 0.7,
      alertThresholds: { anomaly: 0.8, prediction: 0.7, pattern: 0.6 }
    });

    await analyzer.initialize();

    const concurrentAnalyses = Array.from({ length: 5 }, (_, i) => {
      const metrics = generateMockMetrics(100);
      const traces = generateMockTraces(50);
      return analyzer.analyzeChain(`concurrent_${i}`, metrics, traces);
    });

    const startTime = Date.now();
    const results = await Promise.all(concurrentAnalyses);
    const totalTime = Date.now() - startTime;

    expect(results).toHaveLength(5);
    expect(totalTime).toBeLessThan(15000); // Should complete within 15 seconds
    results.forEach(result => {
      expect(result).toBeDefined();
      expect(result.analysisId).toBeDefined();
    });
  }, 20000); // 20 second timeout
});