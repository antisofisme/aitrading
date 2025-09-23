/**
 * Order Management Server
 * AI Trading Platform - Trade Execution and Order Lifecycle Management
 * Port: 9002
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
const PORT = process.env.ORDER_MANAGEMENT_PORT || 9002;
const SERVICE_NAME = 'order-management';

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
    service: 'Order Management Service',
    description: 'Trade execution and order lifecycle management for AI Trading Platform',
    version: '1.0.0',
    port: PORT,
    endpoints: {
      health: '/health',
      orders: '/api/orders',
      execute: '/api/orders/execute',
      cancel: '/api/orders/cancel',
      status: '/api/orders/status'
    },
    capabilities: [
      'order-execution',
      'order-tracking',
      'trade-management',
      'order-validation',
      'exchange-integration'
    ]
  });
});

// Order management endpoints
app.get('/api/orders', (req, res) => {
  res.json({
    success: true,
    orders: [
      {
        id: 'order_001',
        symbol: 'BTC/USDT',
        type: 'market',
        side: 'buy',
        amount: 0.1,
        price: 45000,
        status: 'filled',
        createdAt: new Date().toISOString()
      },
      {
        id: 'order_002',
        symbol: 'ETH/USDT',
        type: 'limit',
        side: 'sell',
        amount: 1.5,
        price: 3200,
        status: 'pending',
        createdAt: new Date().toISOString()
      }
    ]
  });
});

app.post('/api/orders/execute', (req, res) => {
  const { symbol, type, side, amount, price } = req.body;

  if (!symbol || !type || !side || !amount) {
    return res.status(400).json({
      success: false,
      error: 'Missing required order parameters'
    });
  }

  const order = {
    id: `order_${Date.now()}`,
    symbol,
    type,
    side,
    amount,
    price: price || null,
    status: 'pending',
    createdAt: new Date().toISOString(),
    estimatedFill: new Date(Date.now() + 5000).toISOString()
  };

  logger.info('Order executed', { orderId: order.id, symbol, type, side, amount });

  res.json({
    success: true,
    order
  });
});

app.get('/api/orders/:orderId/status', (req, res) => {
  const { orderId } = req.params;

  res.json({
    success: true,
    orderId,
    status: 'filled',
    fillPrice: 45123.45,
    fillAmount: 0.1,
    fillTime: new Date().toISOString(),
    fees: {
      amount: 0.0001,
      currency: 'BTC'
    }
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
  logger.info(`📋 Order Management service running on port ${PORT}`);
});

module.exports = app;