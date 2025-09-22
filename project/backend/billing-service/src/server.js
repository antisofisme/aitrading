const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const cron = require('cron');
require('dotenv').config();

// Import routes
const invoiceRoutes = require('./routes/invoices');
const billingRoutes = require('./routes/billing');
const reportRoutes = require('./routes/reports');
const healthRoutes = require('./routes/health');

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const authMiddleware = require('./middleware/auth');
const loggingMiddleware = require('./middleware/logging');

// Import services
const { initializeDatabase } = require('./database/connection');
const { processMonthlyBilling } = require('./services/billingProcessor');
const { generateRecurringInvoices } = require('./services/invoiceService');
const { sendBillingReminders } = require('./services/reminderService');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'billing-service' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();
const PORT = process.env.PORT || 8025;

// Trust proxy for rate limiting behind load balancer
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: '15 minutes'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Middleware
app.use(compression());
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-User-ID']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', {
    stream: { write: message => logger.info(message.trim()) }
  }));
}

app.use(loggingMiddleware);
app.use(limiter);

// Health check (no auth required)
app.use('/health', healthRoutes);

// Routes with authentication
app.use('/api/invoices', authMiddleware, invoiceRoutes);
app.use('/api/billing', authMiddleware, billingRoutes);
app.use('/api/reports', authMiddleware, reportRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Billing Service',
    version: '1.0.0',
    status: 'operational',
    endpoints: {
      invoices: '/api/invoices',
      billing: '/api/billing',
      reports: '/api/reports',
      health: '/health'
    },
    features: {
      invoiceGeneration: 'enabled',
      pdfGeneration: 'enabled',
      automaticBilling: 'enabled',
      paymentTracking: 'enabled',
      billingReports: 'enabled',
      recurringInvoices: 'enabled'
    },
    supportedCurrencies: ['IDR', 'USD'],
    paymentMethods: ['credit_card', 'bank_transfer', 'e_wallet', 'virtual_account']
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: `The endpoint ${req.method} ${req.originalUrl} does not exist`,
    availableEndpoints: [
      'GET /',
      'GET /health',
      'GET /api/invoices',
      'POST /api/invoices',
      'GET /api/billing/summary',
      'GET /api/reports'
    ]
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Cron jobs for automated billing tasks
function setupCronJobs() {
  // Monthly billing processing on 1st of each month at 2 AM
  const monthlyBillingJob = new cron.CronJob('0 2 1 * *', async () => {
    logger.info('Starting monthly billing processing...');
    try {
      await processMonthlyBilling();
      logger.info('Monthly billing processing completed successfully');
    } catch (error) {
      logger.error('Monthly billing processing failed:', error);
    }
  });

  // Generate recurring invoices daily at 3 AM
  const recurringInvoicesJob = new cron.CronJob('0 3 * * *', async () => {
    logger.info('Starting recurring invoice generation...');
    try {
      await generateRecurringInvoices();
      logger.info('Recurring invoice generation completed successfully');
    } catch (error) {
      logger.error('Recurring invoice generation failed:', error);
    }
  });

  // Send billing reminders daily at 10 AM
  const billingRemindersJob = new cron.CronJob('0 10 * * *', async () => {
    logger.info('Starting billing reminders...');
    try {
      await sendBillingReminders();
      logger.info('Billing reminders sent successfully');
    } catch (error) {
      logger.error('Billing reminders failed:', error);
    }
  });

  // Start jobs if not in test environment
  if (process.env.NODE_ENV !== 'test') {
    monthlyBillingJob.start();
    recurringInvoicesJob.start();
    billingRemindersJob.start();
    logger.info('Billing cron jobs started successfully');
  }

  return { monthlyBillingJob, recurringInvoicesJob, billingRemindersJob };
}

// Initialize database and start server
async function startServer() {
  try {
    logger.info('Initializing Billing Service...');

    // Initialize database connection
    await initializeDatabase();
    logger.info('Database connection established');

    // Setup cron jobs
    setupCronJobs();

    // Start server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Billing Service running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Health check: http://localhost:${PORT}/health`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM received, shutting down gracefully');
      server.close(() => {
        logger.info('Process terminated');
        process.exit(0);
      });
    });

    process.on('SIGINT', () => {
      logger.info('SIGINT received, shutting down gracefully');
      server.close(() => {
        logger.info('Process terminated');
        process.exit(0);
      });
    });

    return server;
  } catch (error) {
    logger.error('Failed to start Billing Service:', error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer };