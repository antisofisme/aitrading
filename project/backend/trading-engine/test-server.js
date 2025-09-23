#!/usr/bin/env node
/**
 * Trading Engine Server - Functional Version
 * Core trading functionality with stable operation
 */

require('dotenv').config();

console.log('Starting Trading Engine Server...');

const express = require('express');
const http = require('http');
const cors = require('cors');

const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors({
  origin: (process.env.CORS_ORIGINS || '').split(',').filter(Boolean),
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Mock services for simulation
const mockServices = {
  orderExecutor: {
    executeOrder: async (order) => {
      const executionTime = Math.floor(Math.random() * 8) + 2; // 2-10ms
      return {
        orderId: `ORD_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
        symbol: order.symbol,
        side: order.side,
        quantity: order.quantity,
        price: order.price || (50000 + Math.random() * 1000),
        status: 'FILLED',
        executedQuantity: order.quantity,
        executedPrice: order.price || (50000 + Math.random() * 1000),
        fees: parseFloat(order.quantity) * 0.001, // 0.1% fee
        timestamp: Date.now(),
        latency: executionTime,
        success: true,
        simulation: true
      };
    }
  },

  aiSignals: {
    generateSignals: async (instruments, timeframe) => {
      return instruments.map(instrument => ({
        instrument,
        timestamp: Date.now(),
        source: 'ai-orchestrator',
        confidence: 0.7 + Math.random() * 0.3, // 70-100%
        direction: Math.random() > 0.5 ? 'long' : 'short',
        strength: Math.random(),
        entryPrice: 50000 + Math.random() * 1000,
        stopLoss: 49500,
        takeProfit: 51000,
        timeframe,
        simulation: true
      }));
    }
  },

  marketData: {
    getBinanceData: async (symbol) => ({
      symbol,
      price: 50000 + Math.random() * 1000,
      change24h: (Math.random() - 0.5) * 10,
      volume24h: 1000000 + Math.random() * 500000,
      bid: 49990,
      ask: 50010,
      spread: 20,
      timestamp: Date.now(),
      source: 'binance',
      simulation: true
    }),

    getCoinbaseData: async (symbol) => ({
      symbol,
      price: 50000 + Math.random() * 1000,
      volume24h: 800000 + Math.random() * 300000,
      bid: 49985,
      ask: 50015,
      spread: 30,
      timestamp: Date.now(),
      source: 'coinbase',
      simulation: true
    })
  },

  metrics: {
    orderMetrics: {
      totalOrders: 0,
      successfulOrders: 0,
      failedOrders: 0,
      averageLatency: 0,
      successRate: 0
    },

    recordOrder: (orderData) => {
      mockServices.metrics.orderMetrics.totalOrders++;
      if (orderData.success) {
        mockServices.metrics.orderMetrics.successfulOrders++;
      } else {
        mockServices.metrics.orderMetrics.failedOrders++;
      }

      const totalOrders = mockServices.metrics.orderMetrics.totalOrders;
      const successfulOrders = mockServices.metrics.orderMetrics.successfulOrders;

      mockServices.metrics.orderMetrics.successRate = totalOrders > 0 ?
        (successfulOrders / totalOrders) * 100 : 0;

      if (orderData.latency) {
        mockServices.metrics.orderMetrics.averageLatency =
          (mockServices.metrics.orderMetrics.averageLatency + orderData.latency) / 2;
      }
    },

    getSnapshot: () => ({
      timestamp: Date.now(),
      orders: mockServices.metrics.orderMetrics,
      performance: {
        targetLatency: '10ms',
        compliance: mockServices.metrics.orderMetrics.averageLatency < 10 ? 'PASSED' : 'WARNING'
      },
      simulation: true
    })
  }
};

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'trading-engine',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    port: process.env.PORT || 9010,
    environment: process.env.NODE_ENV || 'development',
    mode: 'simulation',
    services: {
      orderExecutor: 'active',
      aiSignalIntegration: 'active',
      marketData: 'active',
      metrics: 'active'
    },
    features: {
      aiSignalIntegration: true,
      realTimeTrading: true,
      simulationMode: true
    }
  });
});

// Trading endpoints
app.post('/api/orders/execute', async (req, res) => {
  const startTime = Date.now();

  try {
    const order = req.body;
    const { userId, tenantId } = req.query;

    // Validate order
    if (!order.symbol || !order.side || !order.quantity) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: symbol, side, quantity'
      });
    }

    // Execute order (simulation)
    const result = await mockServices.orderExecutor.executeOrder(order);
    const executionTime = Date.now() - startTime;

    // Record metrics
    mockServices.metrics.recordOrder({
      orderId: result.orderId,
      success: true,
      latency: result.latency,
      executionTime
    });

    console.log(`Order executed: ${result.orderId} ${order.side} ${order.quantity} ${order.symbol} in ${result.latency}ms`);

    res.json({
      success: true,
      data: {
        ...result,
        totalExecutionTime: `${executionTime}ms`,
        performance: {
          latency: `${result.latency}ms`,
          targetCompliance: result.latency < 10 ? 'PASSED' : 'WARNING'
        }
      }
    });

  } catch (error) {
    const executionTime = Date.now() - startTime;

    mockServices.metrics.recordOrder({
      orderId: req.body.id || 'unknown',
      success: false,
      latency: executionTime,
      executionTime
    });

    console.error('Order execution failed:', error.message);

    res.status(500).json({
      success: false,
      error: error.message,
      executionTime: `${executionTime}ms`
    });
  }
});

// AI signals endpoint
app.post('/api/ai/signals', async (req, res) => {
  try {
    const { instruments = ['BTCUSD'], timeframe = '1m' } = req.body;

    const signals = await mockServices.aiSignals.generateSignals(instruments, timeframe);

    console.log(`Generated ${signals.length} AI signals for ${instruments.join(', ')}`);

    res.json({
      success: true,
      data: signals,
      metadata: {
        count: signals.length,
        timeframe,
        simulation: true
      }
    });

  } catch (error) {
    console.error('AI signals generation failed:', error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Market data endpoints
app.get('/api/market/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const { exchange = 'binance' } = req.query;

    let marketData;
    if (exchange === 'binance') {
      marketData = await mockServices.marketData.getBinanceData(symbol);
    } else if (exchange === 'coinbase') {
      marketData = await mockServices.marketData.getCoinbaseData(symbol);
    } else {
      throw new Error(`Unsupported exchange: ${exchange}`);
    }

    res.json({
      success: true,
      data: marketData
    });

  } catch (error) {
    console.error('Market data request failed:', error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Metrics endpoint
app.get('/api/metrics', (req, res) => {
  try {
    const metrics = mockServices.metrics.getSnapshot();

    res.json({
      success: true,
      data: metrics
    });

  } catch (error) {
    console.error('Metrics request failed:', error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Performance test endpoint
app.get('/api/performance/test', async (req, res) => {
  try {
    const { iterations = 10 } = req.query;
    const results = [];

    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();

      // Simulate order execution
      await mockServices.orderExecutor.executeOrder({
        symbol: 'BTCUSD',
        side: 'buy',
        quantity: '0.001'
      });

      const latency = Date.now() - startTime;
      results.push(latency);
    }

    const averageLatency = results.reduce((a, b) => a + b, 0) / results.length;
    const maxLatency = Math.max(...results);
    const minLatency = Math.min(...results);

    res.json({
      success: true,
      data: {
        iterations: parseInt(iterations),
        averageLatency: `${averageLatency.toFixed(2)}ms`,
        maxLatency: `${maxLatency}ms`,
        minLatency: `${minLatency}ms`,
        targetCompliance: averageLatency < 10 ? 'PASSED' : 'WARNING',
        results
      }
    });

  } catch (error) {
    console.error('Performance test failed:', error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

const port = process.env.PORT || 9010;
const host = process.env.HOST || '0.0.0.0';

server.listen(port, host, (err) => {
  if (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }

  console.log(`Trading Engine Test Server started on ${host}:${port}`);
  console.log(`Health endpoint: http://localhost:${port}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('Shutting down...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('Shutting down...');
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});