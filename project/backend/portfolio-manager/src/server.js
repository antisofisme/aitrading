/**
 * Portfolio Manager Server
 * AI Trading Platform - Portfolio Optimization and Asset Allocation
 * Port: 9001
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
const PORT = process.env.PORTFOLIO_MANAGER_PORT || 9001;
const SERVICE_NAME = 'portfolio-manager';

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
app.use(express.json());
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
    version: '1.0.0'
  });
});

// Service info endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Portfolio Manager Service',
    description: 'Portfolio optimization and asset allocation for AI Trading Platform',
    version: '1.0.0',
    port: PORT,
    endpoints: {
      health: '/health',
      portfolios: '/api/portfolios',
      optimization: '/api/optimize',
      allocation: '/api/allocation',
      rebalance: '/api/rebalance'
    },
    capabilities: [
      'portfolio-optimization',
      'asset-allocation',
      'risk-management',
      'rebalancing',
      'performance-tracking'
    ]
  });
});

// Portfolio management endpoints
app.get('/api/portfolios', (req, res) => {
  res.json({
    success: true,
    portfolios: [
      {
        id: 'portfolio_1',
        name: 'Conservative Growth',
        totalValue: 100000,
        assets: [
          { symbol: 'BTC', allocation: 0.3, value: 30000 },
          { symbol: 'ETH', allocation: 0.2, value: 20000 },
          { symbol: 'USDT', allocation: 0.5, value: 50000 }
        ],
        performance: {
          daily: 0.012,
          weekly: 0.045,
          monthly: 0.128
        }
      }
    ]
  });
});

app.post('/api/optimize', (req, res) => {
  const { portfolioId, constraints, objectives } = req.body;

  const optimization = {
    portfolioId,
    optimizedAllocation: [
      { symbol: 'BTC', currentAllocation: 0.3, suggestedAllocation: 0.35 },
      { symbol: 'ETH', currentAllocation: 0.2, suggestedAllocation: 0.25 },
      { symbol: 'USDT', currentAllocation: 0.5, suggestedAllocation: 0.4 }
    ],
    expectedReturn: 0.15,
    expectedRisk: 0.08,
    sharpeRatio: 1.875
  };

  res.json({
    success: true,
    optimization
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found',
    service: SERVICE_NAME
  });
});

// Error handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error', { error: err.message });
  res.status(500).json({
    success: false,
    message: 'Internal server error',
    service: SERVICE_NAME
  });
});

// Start server
app.listen(PORT, () => {
  logger.info(`📊 Portfolio Manager service running on port ${PORT}`);
});

module.exports = app;