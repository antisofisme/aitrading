/**
 * Level 4 ML AutoML Service (Port 8013)
 * Purpose: Per-user model training with automated hyperparameter optimization
 * Enhanced: FinBERT + Transfer Learning for 80% faster development
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');

// Load environment variables
dotenv.config();

// Import core modules
const AutoMLCore = require('./core/AutoMLCore');
const ModelManager = require('./services/ModelManager');
const HyperparameterOptimizer = require('./services/HyperparameterOptimizer');
const TransferLearningEngine = require('./services/TransferLearningEngine');
const UserModelManager = require('./services/UserModelManager');

// Import routes
const healthRoutes = require('./routes/health');
const modelRoutes = require('./routes/models');
const trainingRoutes = require('./routes/training');
const predictionRoutes = require('./routes/predictions');

class MLAutoMLService {
  constructor() {
    this.app = express();
    this.port = process.env.ML_AUTOML_PORT || 8013;
    this.serviceName = 'ml-automl';

    // Initialize logger
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: {
        service: this.serviceName,
        level: 'level4-intelligence'
      },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}-error.log`,
          level: 'error'
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}.log`
        })
      ]
    });

    // Initialize core components
    this.autoMLCore = new AutoMLCore(this.logger);
    this.modelManager = new ModelManager(this.logger);
    this.hyperparameterOptimizer = new HyperparameterOptimizer(this.logger);
    this.transferLearningEngine = new TransferLearningEngine(this.logger);
    this.userModelManager = new UserModelManager(this.logger);

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      modelTrainingJobs: 0,
      completedTraining: 0,
      activeUsers: new Set(),
      averageTrainingTime: 0,
      averageAccuracy: 0,
      lastHealthCheck: Date.now(),
      inferenceCount: 0,
      averageInferenceTime: 0
    };

    // AI accuracy targets (Level 4 requirement: >65%)
    this.accuracyTargets = {
      minimum: 0.65,
      good: 0.75,
      excellent: 0.85
    };

    this.initializeMiddleware();
    this.initializeRoutes();
    this.initializeErrorHandling();
    this.setupPerformanceMonitoring();
  }

  initializeMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // Body parsing
    this.app.use(express.json({ limit: '50mb' })); // Larger limit for model data
    this.app.use(express.urlencoded({ extended: true, limit: '50mb' }));

    // Request logging and metrics
    this.app.use((req, res, next) => {
      const startTime = Date.now();

      // Track user sessions for multi-tenancy
      if (req.headers['user-id']) {
        this.metrics.activeUsers.add(req.headers['user-id']);
      }

      // Request logging
      this.logger.info('Incoming request', {
        method: req.method,
        url: req.url,
        userAgent: req.get('User-Agent'),
        userId: req.headers['user-id'],
        ip: req.ip
      });

      // Response time tracking
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        this.metrics.requestCount++;

        this.logger.info('Request completed', {
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          userId: req.headers['user-id']
        });
      });

      next();
    });
  }

  initializeRoutes() {
    // API routes
    this.app.use('/health', healthRoutes);
    this.app.use('/api/models', modelRoutes);
    this.app.use('/api/training', trainingRoutes);
    this.app.use('/api/predictions', predictionRoutes);

    // Level 4 specific endpoints
    this.app.get('/api/status', (req, res) => {
      res.json({
        service: this.serviceName,
        level: 'level4-intelligence',
        status: 'operational',
        version: '1.0.0',
        uptime: Date.now() - this.metrics.startTime,
        performance: {
          requestCount: this.metrics.requestCount,
          modelTrainingJobs: this.metrics.modelTrainingJobs,
          completedTraining: this.metrics.completedTraining,
          activeUsers: this.metrics.activeUsers.size,
          averageTrainingTime: Math.round(this.metrics.averageTrainingTime),
          averageAccuracy: Math.round(this.metrics.averageAccuracy * 100) / 100,
          accuracyTarget: '>65%',
          level4Compliance: this.metrics.averageAccuracy >= this.accuracyTargets.minimum
        },
        capabilities: [
          'per-user-model-training',
          'automated-hyperparameter-optimization',
          'transfer-learning-finbert',
          'real-time-inference',
          'multi-tenant-isolation',
          'ai-accuracy-tracking'
        ],
        integrationPoints: {
          featureEngineering: true,
          configurationService: true,
          level3DataStream: true,
          transferLearning: true
        }
      });
    });

    // Start user model training
    this.app.post('/api/train-user-model', async (req, res) => {
      const startTime = Date.now();

      try {
        const {
          userId,
          modelType,
          trainingData,
          features,
          target,
          hyperparameters
        } = req.body;

        if (!userId || !modelType || !trainingData) {
          return res.status(400).json({
            error: 'Missing required fields: userId, modelType, trainingData'
          });
        }

        // Start training job with user isolation
        const trainingJob = await this.autoMLCore.startUserModelTraining({
          userId,
          modelType,
          trainingData,
          features,
          target,
          hyperparameters: hyperparameters || 'auto'
        });

        this.metrics.modelTrainingJobs++;

        res.json({
          success: true,
          userId,
          trainingJobId: trainingJob.id,
          modelType,
          status: 'training_started',
          estimatedTime: trainingJob.estimatedTime,
          metadata: {
            startTime: new Date().toISOString(),
            transferLearning: trainingJob.transferLearning,
            hyperparameterOptimization: trainingJob.hyperparameterOptimization
          }
        });

      } catch (error) {
        this.logger.error('Model training start error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Model training failed to start',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Get training job status
    this.app.get('/api/training-status/:jobId', async (req, res) => {
      try {
        const { jobId } = req.params;
        const userId = req.headers['user-id'];

        const trainingStatus = await this.autoMLCore.getTrainingStatus(jobId, userId);

        res.json({
          success: true,
          jobId,
          userId,
          status: trainingStatus.status,
          progress: trainingStatus.progress,
          currentAccuracy: trainingStatus.currentAccuracy,
          targetAccuracy: this.accuracyTargets.minimum,
          estimatedTimeRemaining: trainingStatus.estimatedTimeRemaining,
          metadata: {
            startedAt: trainingStatus.startedAt,
            lastUpdate: trainingStatus.lastUpdate,
            iterations: trainingStatus.iterations
          }
        });

      } catch (error) {
        this.logger.error('Training status error', {
          error: error.message,
          jobId: req.params.jobId,
          userId: req.headers['user-id']
        });

        res.status(500).json({
          error: 'Failed to get training status',
          message: error.message
        });
      }
    });

    // Real-time inference endpoint
    this.app.post('/api/predict', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId, modelId, features } = req.body;

        if (!userId || !modelId || !features) {
          return res.status(400).json({
            error: 'Missing required fields: userId, modelId, features'
          });
        }

        // Get user model and make prediction
        const prediction = await this.autoMLCore.makePrediction({
          userId,
          modelId,
          features
        });

        this.metrics.inferenceCount++;
        const inferenceTime = Date.now() - startTime;
        this.metrics.averageInferenceTime =
          (this.metrics.averageInferenceTime + inferenceTime) / 2;

        res.json({
          success: true,
          userId,
          modelId,
          prediction: prediction.value,
          confidence: prediction.confidence,
          metadata: {
            inferenceTime: `${inferenceTime}ms`,
            targetCompliance: inferenceTime < 15 ? 'PASSED' : 'WARNING',
            modelAccuracy: prediction.modelAccuracy,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Prediction error', {
          error: error.message,
          stack: error.stack,
          userId: req.body.userId,
          modelId: req.body.modelId
        });

        res.status(500).json({
          error: 'Prediction failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Get user models
    this.app.get('/api/user-models/:userId', async (req, res) => {
      try {
        const { userId } = req.params;

        const userModels = await this.userModelManager.getUserModels(userId);

        res.json({
          success: true,
          userId,
          models: userModels.map(model => ({
            id: model.id,
            name: model.name,
            type: model.type,
            accuracy: model.accuracy,
            status: model.status,
            createdAt: model.createdAt,
            lastUsed: model.lastUsed,
            trainingDataSize: model.trainingDataSize,
            performance: {
              accuracy: model.accuracy,
              precision: model.precision,
              recall: model.recall,
              f1Score: model.f1Score
            }
          })),
          metadata: {
            totalModels: userModels.length,
            averageAccuracy: userModels.reduce((acc, m) => acc + m.accuracy, 0) / userModels.length,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('User models retrieval error', {
          error: error.message,
          userId: req.params.userId
        });

        res.status(500).json({
          error: 'Failed to retrieve user models',
          message: error.message
        });
      }
    });

    // AutoML recommendations
    this.app.post('/api/automl-recommendations', async (req, res) => {
      try {
        const { userId, dataCharacteristics, objective } = req.body;

        if (!userId || !dataCharacteristics) {
          return res.status(400).json({
            error: 'Missing required fields: userId, dataCharacteristics'
          });
        }

        const recommendations = await this.autoMLCore.getAutoMLRecommendations({
          userId,
          dataCharacteristics,
          objective: objective || 'trading_accuracy'
        });

        res.json({
          success: true,
          userId,
          recommendations: {
            bestModelType: recommendations.bestModelType,
            hyperparameters: recommendations.hyperparameters,
            transferLearningOptions: recommendations.transferLearningOptions,
            estimatedAccuracy: recommendations.estimatedAccuracy,
            estimatedTrainingTime: recommendations.estimatedTrainingTime
          },
          metadata: {
            basedOnData: dataCharacteristics,
            objective,
            confidence: recommendations.confidence,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('AutoML recommendations error', {
          error: error.message,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Failed to generate AutoML recommendations',
          message: error.message
        });
      }
    });

    // Performance metrics endpoint
    this.app.get('/api/performance', (req, res) => {
      const uptime = Date.now() - this.metrics.startTime;

      res.json({
        service: this.serviceName,
        performance: {
          uptime: `${Math.floor(uptime / 1000)}s`,
          requestCount: this.metrics.requestCount,
          modelTrainingJobs: this.metrics.modelTrainingJobs,
          completedTraining: this.metrics.completedTraining,
          activeUsers: this.metrics.activeUsers.size,
          averageTrainingTime: Math.round(this.metrics.averageTrainingTime),
          averageAccuracy: Math.round(this.metrics.averageAccuracy * 100) / 100,
          inferenceCount: this.metrics.inferenceCount,
          averageInferenceTime: Math.round(this.metrics.averageInferenceTime),
          level4Targets: {
            accuracyTarget: `>${this.accuracyTargets.minimum * 100}%`,
            accuracyActual: `${Math.round(this.metrics.averageAccuracy * 100)}%`,
            accuracyCompliance: this.metrics.averageAccuracy >= this.accuracyTargets.minimum ? 'PASSED' : 'WARNING',
            inferenceTime: this.metrics.averageInferenceTime < 15 ? 'PASSED' : 'WARNING',
            multiTenant: this.metrics.activeUsers.size > 0 ? 'ACTIVE' : 'READY'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            autoMLCore: this.autoMLCore.isHealthy(),
            modelManager: this.modelManager.isHealthy(),
            hyperparameterOptimizer: this.hyperparameterOptimizer.isHealthy(),
            transferLearningEngine: this.transferLearningEngine.isHealthy(),
            userModelManager: this.userModelManager.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'ML AutoML Service',
        level: 'Level 4 - Intelligence',
        description: 'Per-user model training with automated hyperparameter optimization',
        version: '1.0.0',
        port: this.port,
        capabilities: [
          'automated-machine-learning',
          'hyperparameter-optimization',
          'transfer-learning-finbert',
          'per-user-model-training',
          'real-time-inference',
          'multi-tenant-isolation'
        ],
        documentation: '/api/docs',
        health: '/health',
        status: '/api/status'
      });
    });
  }

  initializeErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        service: this.serviceName,
        availableEndpoints: [
          'GET /health',
          'GET /api/status',
          'POST /api/train-user-model',
          'GET /api/training-status/:jobId',
          'POST /api/predict',
          'GET /api/user-models/:userId',
          'POST /api/automl-recommendations',
          'GET /api/performance'
        ]
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      this.logger.error('Unhandled error', {
        error: error.message,
        stack: error.stack,
        url: req.url,
        method: req.method,
        userId: req.headers['user-id']
      });

      res.status(500).json({
        error: 'Internal server error',
        message: error.message,
        service: this.serviceName,
        timestamp: new Date().toISOString()
      });
    });
  }

  setupPerformanceMonitoring() {
    // Health check every 30 seconds
    cron.schedule('*/30 * * * * *', () => {
      this.metrics.lastHealthCheck = Date.now();
      this.performHealthCheck();
    });

    // Performance metrics logging every minute
    cron.schedule('0 * * * * *', () => {
      this.logger.info('Performance metrics', {
        service: this.serviceName,
        metrics: {
          uptime: Date.now() - this.metrics.startTime,
          requestCount: this.metrics.requestCount,
          modelTrainingJobs: this.metrics.modelTrainingJobs,
          completedTraining: this.metrics.completedTraining,
          activeUsers: this.metrics.activeUsers.size,
          averageTrainingTime: Math.round(this.metrics.averageTrainingTime),
          averageAccuracy: Math.round(this.metrics.averageAccuracy * 100) / 100,
          inferenceCount: this.metrics.inferenceCount,
          averageInferenceTime: Math.round(this.metrics.averageInferenceTime),
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Reset user sessions every hour
    cron.schedule('0 0 * * * *', () => {
      this.metrics.activeUsers.clear();
      this.logger.info('User sessions reset for new hour');
    });

    // Check model accuracy compliance every 5 minutes
    cron.schedule('*/5 * * * * *', () => {
      if (this.metrics.averageAccuracy < this.accuracyTargets.minimum) {
        this.logger.warn('AI accuracy below Level 4 target', {
          currentAccuracy: this.metrics.averageAccuracy,
          targetAccuracy: this.accuracyTargets.minimum,
          recommendation: 'Review model training parameters and data quality'
        });
      }
    });
  }

  async performHealthCheck() {
    try {
      const health = {
        service: this.serviceName,
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: Date.now() - this.metrics.startTime,
        components: {
          autoMLCore: this.autoMLCore.isHealthy(),
          modelManager: this.modelManager.isHealthy(),
          hyperparameterOptimizer: this.hyperparameterOptimizer.isHealthy(),
          transferLearningEngine: this.transferLearningEngine.isHealthy(),
          userModelManager: this.userModelManager.isHealthy()
        }
      };

      // Check if any components are unhealthy
      const unhealthyComponents = Object.entries(health.components)
        .filter(([, status]) => !status);

      if (unhealthyComponents.length > 0) {
        health.status = 'unhealthy';
        health.issues = unhealthyComponents.map(([component]) => component);
        this.logger.warn('Health check failed', health);
      }

      // Check AI accuracy compliance
      if (this.metrics.averageAccuracy < this.accuracyTargets.minimum) {
        health.status = 'degraded';
        health.accuracyWarning = {
          current: this.metrics.averageAccuracy,
          target: this.accuracyTargets.minimum,
          message: 'AI accuracy below Level 4 requirement'
        };
      }

    } catch (error) {
      this.logger.error('Health check error', {
        error: error.message,
        stack: error.stack
      });
    }
  }

  async start() {
    try {
      // Initialize core components
      await this.autoMLCore.initialize();
      await this.modelManager.initialize();
      await this.hyperparameterOptimizer.initialize();
      await this.transferLearningEngine.initialize();
      await this.userModelManager.initialize();

      // Start server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('ML AutoML Service started', {
          service: this.serviceName,
          port: this.port,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'automated-machine-learning',
            'hyperparameter-optimization',
            'transfer-learning-finbert',
            'per-user-model-training',
            'real-time-inference'
          ],
          accuracyTargets: this.accuracyTargets
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start ML AutoML Service', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    if (this.server) {
      this.server.close(() => {
        this.logger.info('ML AutoML Service stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new MLAutoMLService();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = MLAutoMLService;