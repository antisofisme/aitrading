const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');

const mlRoutes = require('./routes/mlRoutes');
const modelRoutes = require('./routes/modelRoutes');
const trainingRoutes = require('./routes/trainingRoutes');
const { errorHandler, notFound } = require('./middleware/errorMiddleware');
const logger = require('./utils/logger');
const { connectDatabase, connectRedis } = require('./config/database');

const app = express();
const PORT = process.env.PORT || 8016; // FIXED: Changed from 8006 to 8016

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true
}));

// Compression and logging
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Rate limiting for ML operations
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: process.env.NODE_ENV === 'production' ? 200 : 1000,
  message: 'Too many ML processing requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: '100mb' })); // Large limit for ML data
app.use(express.urlencoded({ extended: true }));

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'ml-processing-service',
    port: PORT, // Will show 8016
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: '1.0.0',
    portResolution: {
      previousPort: 8006,
      currentPort: 8016,
      conflictResolved: true,
      conflictWith: 'database-service'
    },
    capabilities: {
      modelTraining: true,
      inference: true,
      featureProcessing: true,
      tensorflowSupport: true
    }
  });
});

// API routes
app.use('/api/v1/ml', mlRoutes);
app.use('/api/v1/models', modelRoutes);
app.use('/api/v1/training', trainingRoutes);

// Error handling
app.use(notFound);
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Initialize connections and start server
async function startServer() {
  try {
    await connectDatabase();
    await connectRedis();

    app.listen(PORT, () => {
      logger.info(`ML Processing Service running on port ${PORT} (moved from 8006)`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Process ID: ${process.pid}`);
      logger.info('Port conflict with database-service resolved successfully');
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = app;