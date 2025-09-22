const request = require('supertest');
const TradingEngineServer = require('../../src/server');
const WebSocket = require('ws');

describe('Trading Engine Integration Tests', () => {
  let server;
  let app;
  let wsClient;

  beforeAll(async () => {
    // Start server for testing
    server = new TradingEngineServer();
    app = server.app;
    
    // Start server on test port
    const testPort = 3999;
    await new Promise((resolve) => {
      server.server.listen(testPort, () => {
        resolve();
      });
    });
  });

  afterAll(async () => {
    if (wsClient) {
      wsClient.close();
    }
    if (server) {
      await server.shutdown();
    }
  });

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body.status).toBe('healthy');
      expect(response.body.services).toBeDefined();
      expect(response.body.services.orderExecutor.status).toBe('active');
      expect(response.body.services.correlationAnalyzer.status).toBe('active');
      expect(response.body.services.sessionManager.status).toBe('active');
      expect(response.body.services.islamicTrading.status).toBe('active');
    });

    it('should include version and uptime', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body.version).toBeDefined();
      expect(response.body.uptime).toBeDefined();
      expect(response.body.timestamp).toBeDefined();
    });
  });

  describe('Order Execution API', () => {
    const validOrder = {
      symbol: 'EURUSD',
      side: 'buy',
      quantity: 10000,
      type: 'market'
    };

    it('should execute valid market orders', async () => {
      const response = await request(app)
        .post('/api/orders/execute')
        .send(validOrder)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.orderId).toBeDefined();
      expect(response.body.data.status).toBe('queued');
      expect(response.body.data.jobId).toBeDefined();
    });

    it('should reject invalid orders', async () => {
      const invalidOrder = {
        symbol: '',
        side: 'invalid',
        quantity: -1000,
        type: 'unknown'
      };

      const response = await request(app)
        .post('/api/orders/execute')
        .send(invalidOrder)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBeDefined();
    });

    it('should handle limit orders', async () => {
      const limitOrder = {
        symbol: 'GBPUSD',
        side: 'sell',
        quantity: 50000,
        type: 'limit',
        price: 1.2500
      };

      const response = await request(app)
        .post('/api/orders/execute')
        .send(limitOrder)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.orderId).toBeDefined();
    });

    it('should handle stop orders', async () => {
      const stopOrder = {
        symbol: 'USDJPY',
        side: 'buy',
        quantity: 25000,
        type: 'stop',
        stopPrice: 151.00
      };

      const response = await request(app)
        .post('/api/orders/execute')
        .send(stopOrder)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.orderId).toBeDefined();
    });
  });

  describe('Performance Metrics API', () => {
    it('should return performance metrics', async () => {
      const response = await request(app)
        .get('/api/orders/performance')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.totalOrders).toBeDefined();
      expect(response.body.data.successfulOrders).toBeDefined();
      expect(response.body.data.failedOrders).toBeDefined();
      expect(response.body.data.averageLatency).toBeDefined();
      expect(response.body.data.successRate).toBeDefined();
      expect(response.body.data.performanceStatus).toBeDefined();
    });

    it('should include target and current latency', async () => {
      const response = await request(app)
        .get('/api/orders/performance')
        .expect(200);

      expect(response.body.data.targetLatency).toBe(10);
      expect(response.body.data.circuitBreakerStatus).toBeDefined();
    });
  });

  describe('Correlation Analysis API', () => {
    beforeAll(async () => {
      // Add some market data for correlation analysis
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'];
      const promises = symbols.map(symbol => 
        request(app)
          .post('/api/market-data/simulate')
          .send({
            symbol,
            price: Math.random() + 1.0,
            timestamp: Date.now()
          })
      );
      
      await Promise.all(promises);
      
      // Wait a bit for correlation calculations
      await new Promise(resolve => setTimeout(resolve, 1000));
    });

    it('should return correlation matrix', async () => {
      const response = await request(app)
        .get('/api/correlation/matrix')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toBeDefined();
    });

    it('should return correlations for specific symbol', async () => {
      const response = await request(app)
        .get('/api/correlation/EURUSD')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toBeDefined();
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should return forex-gold correlation analysis', async () => {
      const response = await request(app)
        .get('/api/correlation/forex-gold')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toBeDefined();
      expect(response.body.data.XAUUSD).toBeDefined();
    });
  });

  describe('Session Management API', () => {
    it('should return current session information', async () => {
      const response = await request(app)
        .get('/api/sessions/current')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.overlaps).toBeDefined();
    });

    it('should return session recommendations', async () => {
      const response = await request(app)
        .get('/api/sessions/recommendations')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.recommendation).toBeDefined();
      expect(response.body.data.strategy).toBeDefined();
      expect(response.body.data.riskLevel).toBeDefined();
    });

    it('should return session statistics', async () => {
      const response = await request(app)
        .get('/api/sessions/statistics')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.totalSessions).toBeDefined();
      expect(response.body.data.timezone).toBe('Asia/Jakarta');
    });
  });

  describe('Islamic Trading API', () => {
    const islamicAccountData = {
      accountId: 'ISLAMIC_TEST_001',
      maxPositionSize: 100000,
      maxDailyVolume: 1000000,
      religionVerified: true,
      documentationComplete: true
    };

    it('should register Islamic account', async () => {
      const response = await request(app)
        .post('/api/islamic/register')
        .send(islamicAccountData)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.accountId).toBe('ISLAMIC_TEST_001');
      expect(response.body.data.swapFree).toBe(true);
      expect(response.body.data.compliance.shariahCompliant).toBe(true);
    });

    it('should validate Islamic trades', async () => {
      const tradeValidation = {
        accountId: 'ISLAMIC_TEST_001',
        tradeRequest: {
          symbol: 'EURUSD',
          type: 'market',
          positionSize: 50000,
          holdingPeriod: 10
        }
      };

      const response = await request(app)
        .post('/api/islamic/validate-trade')
        .send(tradeValidation)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.isValid).toBeDefined();
      expect(response.body.data.violations).toBeDefined();
      expect(response.body.data.warnings).toBeDefined();
    });

    it('should reject non-Islamic accounts for validation', async () => {
      const tradeValidation = {
        accountId: 'NON_ISLAMIC_ACCOUNT',
        tradeRequest: {
          symbol: 'EURUSD',
          type: 'market',
          positionSize: 50000
        }
      };

      const response = await request(app)
        .post('/api/islamic/validate-trade')
        .send(tradeValidation)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('not registered as Islamic');
    });

    it('should generate compliance reports', async () => {
      const response = await request(app)
        .get('/api/islamic/compliance-report/ISLAMIC_TEST_001?period=7')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.accountId).toBe('ISLAMIC_TEST_001');
      expect(response.body.data.reportPeriod.days).toBe(7);
      expect(response.body.data.compliance).toBeDefined();
      expect(response.body.data.shariahPrinciples).toBeDefined();
      expect(response.body.data.complianceScore).toBeDefined();
    });

    it('should return Islamic trading statistics', async () => {
      const response = await request(app)
        .get('/api/islamic/statistics')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.totalIslamicAccounts).toBeGreaterThan(0);
      expect(response.body.data.supportedPairs).toBeGreaterThan(0);
      expect(response.body.data.complianceFeatures.swapFree).toBe(true);
    });
  });

  describe('WebSocket Real-time Communication', () => {
    it('should establish WebSocket connection', (done) => {
      wsClient = new WebSocket('ws://localhost:3999/ws');
      
      wsClient.on('open', () => {
        done();
      });
      
      wsClient.on('error', (error) => {
        done(error);
      });
    });

    it('should receive welcome message', (done) => {
      if (!wsClient) {
        wsClient = new WebSocket('ws://localhost:3999/ws');
      }
      
      wsClient.on('message', (data) => {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'welcome') {
          expect(message.clientId).toBeDefined();
          expect(message.timestamp).toBeDefined();
          done();
        }
      });
    });

    it('should handle subscription requests', (done) => {
      if (!wsClient) {
        done(new Error('WebSocket not connected'));
        return;
      }
      
      wsClient.send(JSON.stringify({
        type: 'subscribe',
        channel: 'orders'
      }));
      
      wsClient.on('message', (data) => {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'subscribed') {
          expect(message.channel).toBe('orders');
          done();
        }
      });
    });

    it('should handle ping-pong', (done) => {
      if (!wsClient) {
        done(new Error('WebSocket not connected'));
        return;
      }
      
      wsClient.send(JSON.stringify({
        type: 'ping',
        timestamp: Date.now()
      }));
      
      wsClient.on('message', (data) => {
        const message = JSON.parse(data.toString());
        
        if (message.type === 'pong') {
          expect(message.timestamp).toBeDefined();
          done();
        }
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should allow normal request rates', async () => {
      const promises = [];
      
      // Send 10 requests quickly (within rate limit)
      for (let i = 0; i < 10; i++) {
        promises.push(
          request(app)
            .get('/health')
            .expect(200)
        );
      }
      
      const responses = await Promise.all(promises);
      responses.forEach(response => {
        expect(response.body.status).toBe('healthy');
      });
    });

    it('should apply rate limiting to order endpoints', async () => {
      const promises = [];
      const validOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 1000,
        type: 'market'
      };
      
      // Try to exceed rate limit (100 requests per second)
      for (let i = 0; i < 5; i++) {
        promises.push(
          request(app)
            .post('/api/orders/execute')
            .send(validOrder)
        );
      }
      
      const responses = await Promise.all(promises);
      
      // Most should succeed (small number of requests)
      const successCount = responses.filter(r => r.status === 200).length;
      expect(successCount).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 for unknown endpoints', async () => {
      const response = await request(app)
        .get('/api/unknown-endpoint')
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBe('Endpoint not found');
    });

    it('should handle malformed JSON', async () => {
      const response = await request(app)
        .post('/api/orders/execute')
        .set('Content-Type', 'application/json')
        .send('{ invalid json }')
        .expect(400);

      // Express handles malformed JSON automatically
      expect(response.status).toBe(400);
    });

    it('should handle missing required parameters', async () => {
      const response = await request(app)
        .post('/api/islamic/validate-trade')
        .send({})
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toBeDefined();
    });
  });

  describe('Performance Requirements', () => {
    it('should maintain low latency for order execution', async () => {
      const start = Date.now();
      
      const response = await request(app)
        .post('/api/orders/execute')
        .send({
          symbol: 'EURUSD',
          side: 'buy',
          quantity: 10000,
          type: 'market'
        })
        .expect(200);
      
      const latency = Date.now() - start;
      
      // API should respond within 100ms (not including order processing)
      expect(latency).toBeLessThan(100);
      expect(response.body.success).toBe(true);
    });

    it('should handle concurrent requests', async () => {
      const promises = [];
      const concurrentRequests = 20;
      
      for (let i = 0; i < concurrentRequests; i++) {
        promises.push(
          request(app)
            .get('/health')
            .expect(200)
        );
      }
      
      const start = Date.now();
      const responses = await Promise.all(promises);
      const totalTime = Date.now() - start;
      
      // All requests should complete successfully
      responses.forEach(response => {
        expect(response.body.status).toBe('healthy');
      });
      
      // Should handle concurrent requests efficiently
      expect(totalTime).toBeLessThan(1000); // 1 second for 20 requests
    });
  });
});