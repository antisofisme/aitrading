/**
 * AI Chain Analytics Types
 * Comprehensive type definitions for AI-powered chain analysis
 */

export interface ChainMetrics {
  chainId: string;
  timestamp: number;
  executionTime: number;
  stepCount: number;
  successRate: number;
  errorCount: number;
  memoryUsage: number;
  cpuUsage: number;
  throughput: number;
  latency: number;
}

export interface ChainTrace {
  traceId: string;
  chainId: string;
  steps: ChainStepTrace[];
  startTime: number;
  endTime: number;
  status: 'success' | 'failure' | 'timeout' | 'cancelled';
  metadata: Record<string, any>;
}

export interface ChainStepTrace {
  stepId: string;
  stepType: string;
  startTime: number;
  endTime: number;
  duration: number;
  status: 'success' | 'failure' | 'skipped';
  input: any;
  output: any;
  error?: string;
  dependencies: string[];
}

export interface AnomalyDetectionResult {
  anomalyId: string;
  chainId: string;
  timestamp: number;
  anomalyType: 'performance' | 'error' | 'resource' | 'pattern';
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  description: string;
  features: Record<string, number>;
  baseline: Record<string, number>;
  recommendations: string[];
}

export interface PatternRecognitionResult {
  patternId: string;
  patternType: 'sequence' | 'frequency' | 'temporal' | 'correlation';
  description: string;
  confidence: number;
  frequency: number;
  instances: PatternInstance[];
  impact: 'positive' | 'negative' | 'neutral';
  recommendations: string[];
}

export interface PatternInstance {
  instanceId: string;
  timestamp: number;
  chainId: string;
  features: Record<string, any>;
  outcome: string;
}

export interface PredictionResult {
  predictionId: string;
  chainId: string;
  predictionType: 'failure' | 'performance' | 'resource' | 'completion';
  timestamp: number;
  horizonMinutes: number;
  probability: number;
  confidence: number;
  factors: PredictionFactor[];
  preventiveActions: string[];
  estimatedImpact: string;
}

export interface PredictionFactor {
  factor: string;
  importance: number;
  currentValue: number;
  threshold: number;
  trend: 'increasing' | 'decreasing' | 'stable';
}

export interface MLModelConfig {
  modelType: 'lstm' | 'gnn' | 'isolation_forest' | 'svm' | 'random_forest' | 'xgboost';
  version: string;
  parameters: Record<string, any>;
  features: string[];
  targetVariable?: string;
  trainingData: {
    startDate: string;
    endDate: string;
    sampleSize: number;
  };
  performance: ModelPerformance;
}

export interface ModelPerformance {
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  auc: number;
  mse?: number;
  mae?: number;
  lastEvaluated: number;
  validationMethod: string;
}

export interface TimeSeriesFeatures {
  trend: number;
  seasonality: number;
  volatility: number;
  autocorrelation: number;
  stationarity: number;
  outlierRatio: number;
}

export interface GraphFeatures {
  nodeCount: number;
  edgeCount: number;
  density: number;
  clusteringCoefficient: number;
  pathLength: number;
  centrality: Record<string, number>;
  communities: string[][];
}

export interface StreamingConfig {
  batchSize: number;
  windowSizeMinutes: number;
  slidingWindowMinutes: number;
  bufferSize: number;
  processingIntervalMs: number;
  retentionDays: number;
}

export interface ModelVersion {
  version: string;
  createdAt: number;
  modelPath: string;
  config: MLModelConfig;
  performance: ModelPerformance;
  status: 'training' | 'validating' | 'active' | 'deprecated';
  deployedAt?: number;
  rollbackVersion?: string;
}

export interface ChainDependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  criticalPath: string[];
  bottlenecks: string[];
}

export interface DependencyNode {
  nodeId: string;
  stepType: string;
  avgExecutionTime: number;
  failureRate: number;
  resourceUsage: Record<string, number>;
  importance: number;
}

export interface DependencyEdge {
  source: string;
  target: string;
  weight: number;
  dependency_type: 'sequential' | 'conditional' | 'parallel' | 'resource';
  latency: number;
}

export interface AIAnalysisConfig {
  enableRealTimeAnalysis: boolean;
  enablePatternRecognition: boolean;
  enableAnomalyDetection: boolean;
  enablePredictiveAnalysis: boolean;
  modelUpdateFrequency: number;
  confidenceThreshold: number;
  alertThresholds: {
    anomaly: number;
    prediction: number;
    pattern: number;
  };
}

export interface ChainAnalyticsResult {
  analysisId: string;
  chainId: string;
  timestamp: number;
  anomalies: AnomalyDetectionResult[];
  patterns: PatternRecognitionResult[];
  predictions: PredictionResult[];
  recommendations: AnalysisRecommendation[];
  overallHealth: 'excellent' | 'good' | 'warning' | 'critical';
  riskScore: number;
}

export interface AnalysisRecommendation {
  type: 'optimization' | 'scaling' | 'maintenance' | 'alert';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  description: string;
  estimatedImpact: string;
  implementationComplexity: 'low' | 'medium' | 'high';
  estimatedEffort: string;
}