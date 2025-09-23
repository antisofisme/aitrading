/**
 * ML Predictor Server
 * AI Trading Platform - Machine Learning Predictions and Model Inference
 * Port: 8021
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const compression = require('compression');
const winston = require('winston');

// Create Express app
const app = express();
const PORT = process.env.ML_PREDICTOR_PORT || 8021;
const SERVICE_NAME = 'ml-predictor';

// Logger setup
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: {
    service: SERVICE_NAME,
    port: PORT
  },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(morgan('combined'));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    success: true,
    service: SERVICE_NAME,
    status: 'healthy',
    timestamp: new Date().toISOString(),
    port: PORT,
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

// Service info endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'ML Predictor Service',
    description: 'Machine learning predictions and model inference for AI Trading Platform',
    version: '1.0.0',
    port: PORT,
    endpoints: {
      health: '/health',
      predict: '/api/predict',
      models: '/api/models',
      training: '/api/training'
    },
    capabilities: [
      'price-prediction',
      'trend-analysis',
      'risk-scoring',
      'model-inference',
      'real-time-predictions'
    ]
  });
});

// ML Prediction endpoints
app.get('/api/models', (req, res) => {
  res.json({
    success: true,
    models: [
      {
        id: 'price-predictor-v1',
        name: 'Price Prediction Model',
        type: 'LSTM',
        status: 'active',
        accuracy: 0.82,
        lastTrained: '2024-01-01T00:00:00Z'
      },
      {
        id: 'trend-analyzer-v1',
        name: 'Trend Analysis Model',
        type: 'CNN',
        status: 'active',
        accuracy: 0.76,
        lastTrained: '2024-01-01T00:00:00Z'
      }
    ],
    timestamp: new Date().toISOString()
  });
});

app.post('/api/predict', (req, res) => {
  const { symbol, model, timeframe, data } = req.body;

  if (!symbol || !model) {
    return res.status(400).json({
      success: false,
      error: 'Symbol and model are required',
      code: 'MISSING_PARAMETERS'
    });
  }

  // Mock prediction logic
  const prediction = {
    symbol,
    model,
    timeframe: timeframe || '1h',
    prediction: {
      direction: Math.random() > 0.5 ? 'up' : 'down',
      confidence: Math.random() * 0.4 + 0.6, // 0.6-1.0
      expectedChange: (Math.random() - 0.5) * 0.1, // -5% to +5%
      timestamp: new Date().toISOString()
    },
    metadata: {
      processingTime: Math.floor(Math.random() * 100) + 50 + 'ms',
      dataPoints: data ? data.length : 100,
      features: ['price', 'volume', 'volatility', 'momentum']
    }
  };

  logger.info('Prediction generated', {
    symbol,
    model,
    confidence: prediction.prediction.confidence
  });

  res.json({
    success: true,
    ...prediction
  });
});

app.post('/api/training', (req, res) => {
  const { model, dataset, parameters } = req.body;

  const trainingJob = {
    id: `train_${Date.now()}`,
    model,
    status: 'started',
    progress: 0,
    startedAt: new Date().toISOString(),
    estimatedCompletion: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes
    parameters: parameters || {}
  };

  logger.info('Training job started', { jobId: trainingJob.id, model });

  res.json({
    success: true,
    trainingJob
  });
});

// Service metrics endpoint
app.get('/api/metrics', (req, res) => {
  res.json({
    service: SERVICE_NAME,
    metrics: {
      totalPredictions: Math.floor(Math.random() * 10000) + 5000,
      activeModels: 2,
      averageResponseTime: Math.floor(Math.random() * 50) + 25 + 'ms',
      accuracy: {
        pricePredictor: 0.82,
        trendAnalyzer: 0.76
      },
      uptime: process.uptime()
    },
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found',
    service: SERVICE_NAME,
    path: req.originalUrl
  });
});

// Error handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path
  });

  res.status(500).json({
    success: false,
    message: 'Internal server error',
    service: SERVICE_NAME,
    error: process.env.NODE_ENV === 'development' ? err.message : 'Internal error'
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`🤖 ML Predictor service running on port ${PORT}`, {
    service: SERVICE_NAME,
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    timestamp: new Date().toISOString()
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

module.exports = app;