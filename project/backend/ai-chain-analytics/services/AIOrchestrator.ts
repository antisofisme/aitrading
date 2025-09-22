/**
 * AI Orchestrator
 * Coordinates with AI Orchestrator (8020) and ML AutoML (8021) services
 */

import { EventEmitter } from 'events';
import {
  ChainAnalyticsResult,
  MLModelConfig,
  ModelPerformance,
  PredictionResult,
  AnomalyDetectionResult,
  PatternRecognitionResult
} from '../types';

export interface AIServiceConfig {
  orchestratorUrl: string;
  automlUrl: string;
  inferenceUrl: string;
  apiKey?: string;
  timeout: number;
  retryAttempts: number;
}

export interface ModelTrainingRequest {
  modelType: 'anomaly' | 'pattern' | 'prediction' | 'gnn';
  trainingData: any;
  config: MLModelConfig;
  priority: 'low' | 'medium' | 'high';
  callback?: string;
}

export interface ModelTrainingResponse {
  jobId: string;
  status: 'queued' | 'training' | 'completed' | 'failed';
  progress: number;
  eta: number;
  modelId?: string;
  performance?: ModelPerformance;
  error?: string;
}

export interface InferenceRequest {
  modelId: string;
  inputData: any;
  options?: {
    batchSize?: number;
    timeout?: number;
    returnConfidence?: boolean;
  };
}

export interface InferenceResponse {
  requestId: string;
  predictions: any[];
  confidence?: number[];
  processingTime: number;
  modelVersion: string;
}

export interface ModelOptimizationRequest {
  modelId: string;
  optimizationType: 'hyperparameter' | 'architecture' | 'ensemble';
  targetMetric: 'accuracy' | 'precision' | 'recall' | 'f1' | 'auc';
  constraints: {
    maxTrainingTime?: number;
    maxModelSize?: number;
    minAccuracy?: number;
  };
}

export class AIOrchestrator extends EventEmitter {
  private config: AIServiceConfig;
  private trainingJobs: Map<string, ModelTrainingResponse> = new Map();
  private activeModels: Map<string, string> = new Map(); // modelType -> modelId
  private modelCache: Map<string, any> = new Map();
  private isInitialized: boolean = false;

  constructor(config: AIServiceConfig) {
    super();
    this.config = config;
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing AI Orchestrator...');

      // Verify service connectivity
      await this.verifyServices();

      // Load active models
      await this.loadActiveModels();

      // Setup job monitoring
      this.startJobMonitoring();

      this.isInitialized = true;
      console.log('AI Orchestrator initialized successfully');
    } catch (error) {
      console.error('Failed to initialize AI Orchestrator:', error);
      throw error;
    }
  }

  async submitTrainingJob(request: ModelTrainingRequest): Promise<string> {
    if (!this.isInitialized) {
      throw new Error('AI Orchestrator not initialized');
    }

    try {
      console.log(`Submitting training job for ${request.modelType} model...`);

      const response = await this.makeRequest('POST', '/training/submit', {
        modelType: request.modelType,
        config: request.config,
        trainingData: request.trainingData,
        priority: request.priority,
        callback: request.callback || `${this.config.orchestratorUrl}/callback`
      });

      const jobResponse: ModelTrainingResponse = {
        jobId: response.jobId,
        status: 'queued',
        progress: 0,
        eta: response.estimatedTime || 3600 // Default 1 hour
      };

      this.trainingJobs.set(response.jobId, jobResponse);

      this.emit('trainingJobSubmitted', jobResponse);
      console.log(`Training job submitted: ${response.jobId}`);

      return response.jobId;
    } catch (error) {
      console.error('Failed to submit training job:', error);
      throw error;
    }
  }

  async getTrainingJobStatus(jobId: string): Promise<ModelTrainingResponse> {
    try {
      const response = await this.makeRequest('GET', `/training/status/${jobId}`);

      const jobStatus: ModelTrainingResponse = {
        jobId,
        status: response.status,
        progress: response.progress || 0,
        eta: response.eta || 0,
        modelId: response.modelId,
        performance: response.performance,
        error: response.error
      };

      this.trainingJobs.set(jobId, jobStatus);

      // Emit status update
      this.emit('trainingJobUpdated', jobStatus);

      return jobStatus;
    } catch (error) {
      console.error(`Failed to get training job status for ${jobId}:`, error);
      throw error;
    }
  }

  async optimizeModel(request: ModelOptimizationRequest): Promise<string> {
    try {
      console.log(`Starting model optimization for ${request.modelId}...`);

      const response = await this.makeRequest('POST', '/automl/optimize', {
        modelId: request.modelId,
        optimizationType: request.optimizationType,
        targetMetric: request.targetMetric,
        constraints: request.constraints
      });

      console.log(`Model optimization job started: ${response.jobId}`);
      return response.jobId;
    } catch (error) {
      console.error('Failed to start model optimization:', error);
      throw error;
    }
  }

  async runInference(request: InferenceRequest): Promise<InferenceResponse> {
    try {
      const startTime = Date.now();

      const response = await this.makeRequest('POST', '/inference/predict', {
        modelId: request.modelId,
        inputData: request.inputData,
        options: request.options || {}
      });

      const inferenceResponse: InferenceResponse = {
        requestId: response.requestId,
        predictions: response.predictions,
        confidence: response.confidence,
        processingTime: Date.now() - startTime,
        modelVersion: response.modelVersion
      };

      // Cache response for a short time
      this.modelCache.set(request.modelId, {
        lastUsed: Date.now(),
        response: inferenceResponse
      });

      return inferenceResponse;
    } catch (error) {
      console.error('Failed to run inference:', error);
      throw error;
    }
  }

  async analyzeWithAI(
    chainId: string,
    analyticsResult: ChainAnalyticsResult
  ): Promise<{
    enhancedAnomalies: AnomalyDetectionResult[];
    enhancedPatterns: PatternRecognitionResult[];
    enhancedPredictions: PredictionResult[];
    aiInsights: string[];
    recommendations: string[];
  }> {
    try {
      console.log(`Running AI analysis for chain: ${chainId}`);

      // Prepare input data for AI services
      const inputData = {
        chainId,
        anomalies: analyticsResult.anomalies,
        patterns: analyticsResult.patterns,
        predictions: analyticsResult.predictions,
        overallHealth: analyticsResult.overallHealth,
        riskScore: analyticsResult.riskScore
      };

      // Run parallel AI analyses
      const [
        anomalyEnhancement,
        patternEnhancement,
        predictionEnhancement,
        insightGeneration
      ] = await Promise.allSettled([
        this.enhanceAnomalyDetection(inputData),
        this.enhancePatternRecognition(inputData),
        this.enhancePredictiveAnalysis(inputData),
        this.generateAIInsights(inputData)
      ]);

      // Process results
      const enhancedAnomalies = anomalyEnhancement.status === 'fulfilled' ?
        anomalyEnhancement.value : analyticsResult.anomalies;

      const enhancedPatterns = patternEnhancement.status === 'fulfilled' ?
        patternEnhancement.value : analyticsResult.patterns;

      const enhancedPredictions = predictionEnhancement.status === 'fulfilled' ?
        predictionEnhancement.value : analyticsResult.predictions;

      const insights = insightGeneration.status === 'fulfilled' ?
        insightGeneration.value : { insights: [], recommendations: [] };

      this.emit('aiAnalysisCompleted', {
        chainId,
        enhancedAnomalies,
        enhancedPatterns,
        enhancedPredictions,
        insights: insights.insights
      });

      return {
        enhancedAnomalies,
        enhancedPatterns,
        enhancedPredictions,
        aiInsights: insights.insights,
        recommendations: insights.recommendations
      };
    } catch (error) {
      console.error('AI analysis failed:', error);
      throw error;
    }
  }

  async deployModel(modelId: string, deployment: {
    environment: 'staging' | 'production';
    scalingConfig?: {
      minInstances: number;
      maxInstances: number;
      targetCPU: number;
    };
    routingConfig?: {
      canaryPercentage?: number;
      rolloutStrategy?: 'immediate' | 'gradual';
    };
  }): Promise<string> {
    try {
      console.log(`Deploying model ${modelId} to ${deployment.environment}...`);

      const response = await this.makeRequest('POST', '/deployment/deploy', {
        modelId,
        environment: deployment.environment,
        scalingConfig: deployment.scalingConfig,
        routingConfig: deployment.routingConfig
      });

      const deploymentId = response.deploymentId;
      console.log(`Model deployment started: ${deploymentId}`);

      // Update active models if deploying to production
      if (deployment.environment === 'production') {
        const modelInfo = await this.getModelInfo(modelId);
        this.activeModels.set(modelInfo.modelType, modelId);
      }

      return deploymentId;
    } catch (error) {
      console.error('Failed to deploy model:', error);
      throw error;
    }
  }

  async getModelPerformance(modelId: string): Promise<ModelPerformance & {
    detailedMetrics: Record<string, number>;
    benchmarkComparisons: Array<{
      metric: string;
      value: number;
      baseline: number;
      improvement: number;
    }>;
  }> {
    try {
      const response = await this.makeRequest('GET', `/models/${modelId}/performance`);

      return {
        accuracy: response.accuracy,
        precision: response.precision,
        recall: response.recall,
        f1Score: response.f1Score,
        auc: response.auc,
        mse: response.mse,
        mae: response.mae,
        lastEvaluated: response.lastEvaluated,
        validationMethod: response.validationMethod,
        detailedMetrics: response.detailedMetrics || {},
        benchmarkComparisons: response.benchmarkComparisons || []
      };
    } catch (error) {
      console.error('Failed to get model performance:', error);
      throw error;
    }
  }

  async getAIRecommendations(context: {
    chainId: string;
    historicalData: any;
    currentMetrics: any;
    businessObjectives: string[];
  }): Promise<{
    strategicRecommendations: string[];
    tacticalRecommendations: string[];
    prioritizedActions: Array<{
      action: string;
      priority: 'high' | 'medium' | 'low';
      effort: 'low' | 'medium' | 'high';
      impact: 'low' | 'medium' | 'high';
      timeline: string;
    }>;
  }> {
    try {
      const response = await this.makeRequest('POST', '/ai/recommendations', context);

      return {
        strategicRecommendations: response.strategic || [],
        tacticalRecommendations: response.tactical || [],
        prioritizedActions: response.actions || []
      };
    } catch (error) {
      console.error('Failed to get AI recommendations:', error);
      throw error;
    }
  }

  // Private methods

  private async verifyServices(): Promise<void> {
    try {
      // Test AI Orchestrator connectivity
      await this.makeRequest('GET', '/health');
      console.log('AI Orchestrator service is healthy');

      // Test AutoML service
      await this.makeRequest('GET', '/automl/health');
      console.log('AutoML service is healthy');

      // Test Inference Engine
      await this.makeRequest('GET', '/inference/health');
      console.log('Inference Engine is healthy');
    } catch (error) {
      console.error('Service verification failed:', error);
      throw error;
    }
  }

  private async loadActiveModels(): Promise<void> {
    try {
      const response = await this.makeRequest('GET', '/models/active');

      for (const model of response.models) {
        this.activeModels.set(model.modelType, model.modelId);
      }

      console.log(`Loaded ${this.activeModels.size} active models`);
    } catch (error) {
      console.warn('Failed to load active models:', error);
    }
  }

  private startJobMonitoring(): void {
    // Monitor training jobs every 30 seconds
    setInterval(async () => {
      for (const [jobId, job] of this.trainingJobs.entries()) {
        if (job.status === 'queued' || job.status === 'training') {
          try {
            await this.getTrainingJobStatus(jobId);
          } catch (error) {
            console.error(`Failed to check job ${jobId}:`, error);
          }
        }
      }
    }, 30000);

    // Clean up completed jobs every 5 minutes
    setInterval(() => {
      const cutoffTime = Date.now() - 24 * 60 * 60 * 1000; // 24 hours ago

      for (const [jobId, job] of this.trainingJobs.entries()) {
        if ((job.status === 'completed' || job.status === 'failed') &&
            Date.now() - cutoffTime > 0) {
          this.trainingJobs.delete(jobId);
        }
      }
    }, 5 * 60 * 1000);
  }

  private async enhanceAnomalyDetection(inputData: any): Promise<AnomalyDetectionResult[]> {
    const request: InferenceRequest = {
      modelId: this.activeModels.get('anomaly') || 'default-anomaly-model',
      inputData: {
        anomalies: inputData.anomalies,
        chainMetrics: inputData
      },
      options: {
        returnConfidence: true,
        timeout: 10000
      }
    };

    const response = await this.runInference(request);

    // Convert AI response to enhanced anomalies
    return response.predictions.map((pred, index) => ({
      ...inputData.anomalies[index],
      confidence: response.confidence?.[index] || pred.confidence,
      aiEnhanced: true,
      additionalContext: pred.context || {},
      severityAdjustment: pred.severityAdjustment,
      rootCauseHypotheses: pred.rootCauses || []
    }));
  }

  private async enhancePatternRecognition(inputData: any): Promise<PatternRecognitionResult[]> {
    const request: InferenceRequest = {
      modelId: this.activeModels.get('pattern') || 'default-pattern-model',
      inputData: {
        patterns: inputData.patterns,
        chainContext: inputData
      }
    };

    const response = await this.runInference(request);

    return response.predictions.map((pred, index) => ({
      ...inputData.patterns[index],
      confidence: pred.confidence,
      aiEnhanced: true,
      similarPatterns: pred.similarPatterns || [],
      patternEvolution: pred.evolution || {},
      businessImpact: pred.businessImpact
    }));
  }

  private async enhancePredictiveAnalysis(inputData: any): Promise<PredictionResult[]> {
    const request: InferenceRequest = {
      modelId: this.activeModels.get('prediction') || 'default-prediction-model',
      inputData: {
        predictions: inputData.predictions,
        currentState: inputData
      }
    };

    const response = await this.runInference(request);

    return response.predictions.map((pred, index) => ({
      ...inputData.predictions[index],
      probability: pred.adjustedProbability || inputData.predictions[index].probability,
      confidence: pred.confidence,
      aiEnhanced: true,
      alternativeScenarios: pred.scenarios || [],
      mitigationStrategies: pred.mitigations || [],
      timelineAdjustments: pred.timelineAdjustments
    }));
  }

  private async generateAIInsights(inputData: any): Promise<{
    insights: string[];
    recommendations: string[];
  }> {
    const request: InferenceRequest = {
      modelId: 'insight-generation-model',
      inputData
    };

    try {
      const response = await this.runInference(request);
      return {
        insights: response.predictions[0]?.insights || [],
        recommendations: response.predictions[0]?.recommendations || []
      };
    } catch (error) {
      console.warn('Failed to generate AI insights:', error);
      return { insights: [], recommendations: [] };
    }
  }

  private async getModelInfo(modelId: string): Promise<{ modelType: string; version: string }> {
    const response = await this.makeRequest('GET', `/models/${modelId}/info`);
    return {
      modelType: response.modelType,
      version: response.version
    };
  }

  private async makeRequest(method: string, endpoint: string, data?: any): Promise<any> {
    const url = `${this.config.orchestratorUrl}${endpoint}`;
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
      }
    };

    if (data && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(data);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('Request timeout');
      }

      throw error;
    }
  }

  // Public API methods

  getActiveModels(): Record<string, string> {
    return Object.fromEntries(this.activeModels.entries());
  }

  getTrainingJobs(): ModelTrainingResponse[] {
    return Array.from(this.trainingJobs.values());
  }

  async cancelTrainingJob(jobId: string): Promise<void> {
    try {
      await this.makeRequest('POST', `/training/cancel/${jobId}`);
      const job = this.trainingJobs.get(jobId);
      if (job) {
        job.status = 'failed';
        job.error = 'Cancelled by user';
        this.emit('trainingJobCancelled', job);
      }
    } catch (error) {
      console.error(`Failed to cancel training job ${jobId}:`, error);
      throw error;
    }
  }

  async getModelMetrics(modelId: string, timeRange: string = '24h'): Promise<{
    inferenceCount: number;
    avgLatency: number;
    errorRate: number;
    throughput: number;
    resourceUsage: {
      cpu: number;
      memory: number;
      gpu?: number;
    };
  }> {
    const response = await this.makeRequest('GET', `/models/${modelId}/metrics?timeRange=${timeRange}`);
    return response;
  }

  async updateModelConfig(modelId: string, config: Partial<MLModelConfig>): Promise<void> {
    await this.makeRequest('PUT', `/models/${modelId}/config`, config);
    console.log(`Updated config for model ${modelId}`);
  }
}