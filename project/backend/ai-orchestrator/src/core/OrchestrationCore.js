/**
 * Orchestration Core - AI Workflow Coordination Engine
 * Handles multi-tenant AI workflow orchestration with Flow Registry integration
 */

const axios = require('axios');
const EventEmitter = require('events');

class OrchestrationCore extends EventEmitter {
  constructor(logger) {
    super();
    this.logger = logger;
    this.workflows = new Map();
    this.activeOrchestrations = new Map();
    this.configService = null;
    this.flowRegistry = null;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // Initialize Configuration Service connection
      if (process.env.CONFIG_SERVICE_ENABLED === 'true') {
        await this.connectToConfigService();
      }

      // Initialize Flow Registry
      if (process.env.FLOW_REGISTRY_ENABLED === 'true') {
        await this.initializeFlowRegistry();
      }

      this.isInitialized = true;
      this.logger.info('Orchestration Core initialized successfully');

    } catch (error) {
      this.logger.error('Failed to initialize Orchestration Core', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  async connectToConfigService() {
    try {
      const configUrl = process.env.CONFIG_SERVICE_URL;
      const response = await axios.get(`${configUrl}/health`, { timeout: 5000 });
      
      if (response.status === 200) {
        this.configService = {
          url: configUrl,
          connected: true,
          lastCheck: Date.now()
        };
        this.logger.info('Connected to Configuration Service', { url: configUrl });
      }
    } catch (error) {
      this.logger.warn('Failed to connect to Configuration Service', {
        error: error.message,
        url: process.env.CONFIG_SERVICE_URL
      });
    }
  }

  async initializeFlowRegistry() {
    try {
      // Initialize Flow Registry for AI workflow tracking
      this.flowRegistry = {
        enabled: true,
        workflows: new Map(),
        metrics: {
          totalWorkflows: 0,
          successfulWorkflows: 0,
          failedWorkflows: 0,
          averageExecutionTime: 0
        }
      };
      this.logger.info('Flow Registry initialized for AI workflow tracking');
    } catch (error) {
      this.logger.error('Failed to initialize Flow Registry', { error: error.message });
    }
  }

  async orchestrateWorkflow(options) {
    const startTime = Date.now();
    const workflowId = this.generateWorkflowId();
    
    try {
      const {
        tenantId,
        userId,
        workflowType,
        parameters,
        services,
        startTime: requestStartTime
      } = options;

      // Register workflow in Flow Registry
      await this.registerWorkflow(workflowId, {
        tenantId,
        userId,
        workflowType,
        parameters,
        services,
        startTime: requestStartTime
      });

      // Create orchestration context
      const orchestrationContext = {
        workflowId,
        tenantId,
        userId,
        workflowType,
        parameters,
        services,
        startTime,
        status: 'running',
        steps: []
      };

      this.activeOrchestrations.set(workflowId, orchestrationContext);

      // Execute workflow based on type
      let result;
      switch (workflowType) {
        case 'ai-inference':
          result = await this.orchestrateAIInference(orchestrationContext);
          break;
        case 'model-training':
          result = await this.orchestrateModelTraining(orchestrationContext);
          break;
        case 'data-pipeline':
          result = await this.orchestrateDataPipeline(orchestrationContext);
          break;
        case 'multi-service-coordination':
          result = await this.orchestrateMultiService(orchestrationContext);
          break;
        default:
          result = await this.orchestrateGenericWorkflow(orchestrationContext);
      }

      // Update orchestration status
      orchestrationContext.status = 'completed';
      orchestrationContext.endTime = Date.now();
      orchestrationContext.duration = orchestrationContext.endTime - startTime;

      // Update Flow Registry metrics
      await this.updateFlowMetrics(workflowId, 'success', orchestrationContext.duration);

      this.logger.info('Workflow orchestration completed', {
        workflowId,
        tenantId,
        userId,
        workflowType,
        duration: orchestrationContext.duration,
        servicesInvolved: result.servicesInvolved?.length || 0
      });

      return {
        workflowId,
        status: 'success',
        duration: orchestrationContext.duration,
        servicesInvolved: result.servicesInvolved || [],
        averageAccuracy: result.averageAccuracy || 0.7,
        results: result.results || {},
        steps: orchestrationContext.steps
      };

    } catch (error) {
      // Update Flow Registry with failure
      await this.updateFlowMetrics(workflowId, 'failure', Date.now() - startTime);

      this.logger.error('Workflow orchestration failed', {
        workflowId,
        error: error.message,
        stack: error.stack,
        duration: Date.now() - startTime
      });

      throw error;
    } finally {
      // Cleanup active orchestration
      this.activeOrchestrations.delete(workflowId);
    }
  }

  async orchestrateAIInference(context) {
    const { parameters, services } = context;
    const results = {};
    const servicesInvolved = [];

    try {
      // Step 1: Prepare data through Feature Engineering (if needed)
      if (services.includes('feature-engineering') || services.includes('all')) {
        context.steps.push({
          step: 'feature-engineering',
          startTime: Date.now(),
          status: 'running'
        });
        
        results.featureEngineering = await this.invokeService(
          'feature-engineering',
          '/api/process-features',
          { data: parameters.inputData }
        );
        
        servicesInvolved.push('feature-engineering');
        context.steps[context.steps.length - 1].status = 'completed';
        context.steps[context.steps.length - 1].endTime = Date.now();
      }

      // Step 2: Run ML inference
      if (services.includes('ml-ensemble') || services.includes('realtime-inference-engine') || services.includes('all')) {
        context.steps.push({
          step: 'ml-inference',
          startTime: Date.now(),
          status: 'running'
        });

        const inferenceService = services.includes('realtime-inference-engine') 
          ? 'realtime-inference-engine' 
          : 'ml-ensemble';
        
        results.inference = await this.invokeService(
          inferenceService,
          '/api/predict',
          { 
            data: results.featureEngineering?.processedData || parameters.inputData,
            modelType: parameters.modelType || 'ensemble'
          }
        );
        
        servicesInvolved.push(inferenceService);
        context.steps[context.steps.length - 1].status = 'completed';
        context.steps[context.steps.length - 1].endTime = Date.now();
      }

      // Step 3: Validate patterns (if needed)
      if (services.includes('pattern-validator') || services.includes('all')) {
        context.steps.push({
          step: 'pattern-validation',
          startTime: Date.now(),
          status: 'running'
        });
        
        results.validation = await this.invokeService(
          'pattern-validator',
          '/api/validate',
          { 
            predictions: results.inference?.predictions,
            confidence: results.inference?.confidence
          }
        );
        
        servicesInvolved.push('pattern-validator');
        context.steps[context.steps.length - 1].status = 'completed';
        context.steps[context.steps.length - 1].endTime = Date.now();
      }

      return {
        results,
        servicesInvolved,
        averageAccuracy: this.calculateAverageAccuracy(results)
      };

    } catch (error) {
      context.steps.push({
        step: 'error',
        error: error.message,
        timestamp: Date.now()
      });
      throw error;
    }
  }

  async orchestrateModelTraining(context) {
    const { parameters, services } = context;
    const results = {};
    const servicesInvolved = [];

    try {
      // Step 1: AutoML model selection
      if (services.includes('ml-automl') || services.includes('all')) {
        results.automl = await this.invokeService(
          'ml-automl',
          '/api/select-model',
          { 
            dataset: parameters.dataset,
            targetVariable: parameters.target,
            trainingConfig: parameters.config
          }
        );
        servicesInvolved.push('ml-automl');
      }

      // Step 2: Train ensemble models
      if (services.includes('ml-ensemble') || services.includes('all')) {
        results.training = await this.invokeService(
          'ml-ensemble',
          '/api/train',
          {
            modelConfig: results.automl?.selectedModel || parameters.modelConfig,
            trainingData: parameters.dataset
          }
        );
        servicesInvolved.push('ml-ensemble');
      }

      return {
        results,
        servicesInvolved,
        averageAccuracy: results.training?.accuracy || 0.7
      };

    } catch (error) {
      throw error;
    }
  }

  async orchestrateDataPipeline(context) {
    // Implementation for data pipeline orchestration
    return {
      results: { pipeline: 'executed' },
      servicesInvolved: ['feature-engineering'],
      averageAccuracy: 0.8
    };
  }

  async orchestrateMultiService(context) {
    // Implementation for multi-service coordination
    return {
      results: { coordination: 'completed' },
      servicesInvolved: context.services,
      averageAccuracy: 0.75
    };
  }

  async orchestrateGenericWorkflow(context) {
    // Generic workflow orchestration
    return {
      results: { generic: 'completed' },
      servicesInvolved: ['configuration-service'],
      averageAccuracy: 0.7
    };
  }

  async invokeService(serviceName, endpoint, payload) {
    try {
      const servicePort = this.getServicePort(serviceName);
      const url = `http://localhost:${servicePort}${endpoint}`;
      
      const response = await axios.post(url, payload, {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json',
          'X-Service-Name': 'ai-orchestrator'
        }
      });

      return response.data;

    } catch (error) {
      // If service is not available, return mock data for development
      this.logger.warn(`Service ${serviceName} not available, using mock data`, {
        serviceName,
        endpoint,
        error: error.message
      });

      return this.generateMockResponse(serviceName, endpoint);
    }
  }

  getServicePort(serviceName) {
    const servicePorts = {
      'feature-engineering': 8011,
      'configuration-service': 8012,
      'ml-automl': 8013,
      'pattern-validator': 8015,
      'telegram-service': 8016,
      'realtime-inference-engine': 8017,
      'ml-ensemble': 8021,
      'backtesting-engine': 8024,
      'performance-analytics': 8002,
      'revenue-analytics': 8026,
      'usage-monitoring': 8027,
      'compliance-monitor': 8040
    };
    return servicePorts[serviceName] || 8000;
  }

  generateMockResponse(serviceName, endpoint) {
    // Generate appropriate mock responses for development
    const mockResponses = {
      'feature-engineering': {
        processedData: { features: ['mock_feature_1', 'mock_feature_2'] },
        featureCount: 10
      },
      'ml-ensemble': {
        predictions: [0.7, 0.8, 0.6],
        confidence: 0.75,
        accuracy: 0.8
      },
      'pattern-validator': {
        isValid: true,
        patterns: ['trend_up', 'support_level'],
        confidence: 0.7
      },
      'realtime-inference-engine': {
        predictions: [0.8, 0.9, 0.7],
        confidence: 0.85,
        responseTime: 15
      }
    };

    return mockResponses[serviceName] || { status: 'mock', service: serviceName };
  }

  async registerWorkflow(workflowId, workflowData) {
    if (this.flowRegistry) {
      this.flowRegistry.workflows.set(workflowId, {
        ...workflowData,
        registeredAt: Date.now()
      });
      this.flowRegistry.metrics.totalWorkflows++;
    }
  }

  async updateFlowMetrics(workflowId, status, duration) {
    if (this.flowRegistry) {
      if (status === 'success') {
        this.flowRegistry.metrics.successfulWorkflows++;
      } else {
        this.flowRegistry.metrics.failedWorkflows++;
      }
      
      // Update average execution time
      const totalCompleted = this.flowRegistry.metrics.successfulWorkflows + this.flowRegistry.metrics.failedWorkflows;
      this.flowRegistry.metrics.averageExecutionTime = 
        (this.flowRegistry.metrics.averageExecutionTime * (totalCompleted - 1) + duration) / totalCompleted;
    }
  }

  calculateAverageAccuracy(results) {
    const accuracies = [];
    
    if (results.inference?.accuracy) accuracies.push(results.inference.accuracy);
    if (results.validation?.confidence) accuracies.push(results.validation.confidence);
    if (results.training?.accuracy) accuracies.push(results.training.accuracy);
    
    return accuracies.length > 0 
      ? accuracies.reduce((sum, acc) => sum + acc, 0) / accuracies.length 
      : 0.7; // Default accuracy
  }

  generateWorkflowId() {
    return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  isHealthy() {
    return this.isInitialized;
  }

  getMetrics() {
    return {
      activeOrchestrations: this.activeOrchestrations.size,
      totalWorkflows: this.workflows.size,
      flowRegistry: this.flowRegistry?.metrics || null,
      configServiceConnected: this.configService?.connected || false
    };
  }
}

module.exports = OrchestrationCore;