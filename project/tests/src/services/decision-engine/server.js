const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');

const decisionRoutes = require('./routes/decisionRoutes');
const modelRoutes = require('./routes/modelRoutes');
const consensusRoutes = require('./routes/consensusRoutes');
const { errorHandler, notFound } = require('./middleware/errorMiddleware');
const logger = require('./utils/logger');
const { connectDatabase, connectRedis } = require('./config/database');
const DecisionEngine = require('./services/DecisionEngine');

const app = express();
const PORT = process.env.PORT || 8031;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true
}));

// Compression and logging
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Rate limiting optimized for high-frequency decision making
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: process.env.NODE_ENV === 'production' ? 2000 : 10000, // Very high limit for decision engine
  message: 'Too many decision requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Initialize decision engine
const decisionEngine = new DecisionEngine();

// Make decision engine available to routes
app.locals.decisionEngine = decisionEngine;

// Health check
app.get('/health', async (req, res) => {
  const engineStatus = await decisionEngine.getStatus();

  res.json({
    status: 'healthy',
    service: 'decision-engine',
    port: PORT,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: '1.0.0',
    performance: {
      averageDecisionTime: engineStatus.averageDecisionTime,
      totalDecisions: engineStatus.totalDecisions,
      successRate: engineStatus.successRate,
      modelsLoaded: engineStatus.modelsLoaded
    },
    capabilities: {
      multiAgentDecisions: true,
      ensembleModels: true,
      realTimeInference: true,
      bayesianOptimization: true,
      performanceTarget: '<15ms decision time'
    }
  });
});

// API routes
app.use('/api/v1/decisions', decisionRoutes);
app.use('/api/v1/models', modelRoutes);
app.use('/api/v1/consensus', consensusRoutes);

// Error handling
app.use(notFound);
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  decisionEngine.shutdown();
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  decisionEngine.shutdown();
  process.exit(0);
});

// Initialize connections and start server
async function startServer() {
  try {
    await connectDatabase();
    await connectRedis();
    await decisionEngine.initialize();

    app.listen(PORT, () => {
      logger.info(`Decision Engine running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Process ID: ${process.pid}`);
      logger.info('Decision engine ready for <15ms multi-agent decisions');
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = app;