/**
 * API Gateway Routing Integration Tests
 * Tests routing to backend services through API Gateway
 */

const request = require('supertest');
const { expect } = require('chai');
const axios = require('axios');
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const rateLimit = require('express-rate-limit');

describe('API Gateway Routing Integration Tests', () => {
  let gatewayApp;
  let mockServices = {};
  const gatewayPort = 3000;
  const baseURL = `http://localhost:${gatewayPort}`;

  before(async function() {
    this.timeout(15000);
    
    // Create mock backend services
    await createMockServices();
    
    // Create and configure API Gateway
    gatewayApp = await createAPIGateway();
    
    console.log('API Gateway and mock services ready');
  });

  after(async function() {
    // Cleanup mock services
    Object.values(mockServices).forEach(server => {
      if (server && server.close) {
        server.close();
      }
    });
  });

  describe('Service Route Discovery', () => {
    it('should route requests to user service', async () => {
      const response = await request(gatewayApp)
        .get('/api/users')
        .expect(200);

      expect(response.body.service).to.equal('user-service');
      expect(response.body.endpoint).to.equal('/users');
      expect(response.body.users).to.be.an('array');
    });

    it('should route requests to trading service', async () => {
      const response = await request(gatewayApp)
        .post('/api/trading/orders')
        .send({ symbol: 'AAPL', quantity: 100, type: 'market' })
        .expect(201);

      expect(response.body.service).to.equal('trading-service');
      expect(response.body.endpoint).to.equal('/orders');
      expect(response.body.order).to.include({
        symbol: 'AAPL',
        quantity: 100,
        type: 'market'
      });
    });

    it('should route requests to analytics service', async () => {
      const response = await request(gatewayApp)
        .get('/api/analytics/portfolio/summary')
        .expect(200);

      expect(response.body.service).to.equal('analytics-service');
      expect(response.body.endpoint).to.equal('/portfolio/summary');
      expect(response.body.portfolio).to.be.an('object');
    });

    it('should route requests to notification service', async () => {
      const response = await request(gatewayApp)
        .post('/api/notifications/send')
        .send({ 
          userId: 'user123',
          type: 'email',
          subject: 'Test Notification',
          message: 'This is a test notification'
        })
        .expect(200);

      expect(response.body.service).to.equal('notification-service');
      expect(response.body.success).to.be.true;
    });
  });

  describe('Load Balancing', () => {
    it('should distribute requests across multiple service instances', async function() {
      this.timeout(10000);
      
      const responses = [];
      const numberOfRequests = 10;

      // Make multiple requests to the same endpoint
      for (let i = 0; i < numberOfRequests; i++) {
        const response = await request(gatewayApp)
          .get('/api/users/load-test')
          .expect(200);
        
        responses.push(response.body.instanceId);
      }

      // Check that requests were distributed across different instances
      const uniqueInstances = [...new Set(responses)];
      expect(uniqueInstances.length).to.be.at.least(2); // At least 2 different instances
    });

    it('should handle failover when a service instance is down', async () => {
      // Simulate instance failure by stopping one mock service
      if (mockServices.userService2) {
        mockServices.userService2.close();
      }

      const response = await request(gatewayApp)
        .get('/api/users/failover-test')
        .expect(200);

      expect(response.body.service).to.equal('user-service');
      // Request should still succeed using healthy instance
    });
  });

  describe('Authentication and Authorization', () => {
    let authToken;

    before(async () => {
      // Get authentication token
      const authResponse = await request(gatewayApp)
        .post('/api/auth/login')
        .send({
          username: 'testuser',
          password: 'testpassword'
        })
        .expect(200);

      authToken = authResponse.body.token;
    });

    it('should authenticate requests with valid token', async () => {
      const response = await request(gatewayApp)
        .get('/api/trading/positions')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.service).to.equal('trading-service');
      expect(response.body.positions).to.be.an('array');
    });

    it('should reject requests without authentication', async () => {
      await request(gatewayApp)
        .get('/api/trading/positions')
        .expect(401);
    });

    it('should reject requests with invalid token', async () => {
      await request(gatewayApp)
        .get('/api/trading/positions')
        .set('Authorization', 'Bearer invalid-token')
        .expect(401);
    });

    it('should enforce role-based access control', async () => {
      // Admin only endpoint
      await request(gatewayApp)
        .get('/api/admin/users')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(403); // Forbidden for non-admin user
    });
  });

  describe('Rate Limiting', () => {
    it('should apply rate limiting per endpoint', async function() {
      this.timeout(30000);
      
      const rateLimitEndpoint = '/api/analytics/compute-intensive';
      let successfulRequests = 0;
      let rateLimitedRequests = 0;

      // Make multiple rapid requests
      for (let i = 0; i < 20; i++) {
        try {
          const response = await request(gatewayApp)
            .get(rateLimitEndpoint);
          
          if (response.status === 200) {
            successfulRequests++;
          } else if (response.status === 429) {
            rateLimitedRequests++;
          }
        } catch (error) {
          if (error.status === 429) {
            rateLimitedRequests++;
          }
        }
        
        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      expect(rateLimitedRequests).to.be.greaterThan(0);
      expect(successfulRequests).to.be.lessThan(20);
    });

    it('should apply different rate limits for different user tiers', async () => {
      // Premium user should have higher rate limits
      const premiumToken = await getPremiumUserToken();
      
      let premiumSuccessCount = 0;
      let basicSuccessCount = 0;

      // Test premium user rate limit
      for (let i = 0; i < 15; i++) {
        try {
          const response = await request(gatewayApp)
            .get('/api/analytics/premium-data')
            .set('Authorization', `Bearer ${premiumToken}`);
          
          if (response.status === 200) {
            premiumSuccessCount++;
          }
        } catch (error) {
          // Rate limited
        }
      }

      // Test basic user rate limit
      for (let i = 0; i < 15; i++) {
        try {
          const response = await request(gatewayApp)
            .get('/api/analytics/premium-data')
            .set('Authorization', `Bearer ${authToken}`);
          
          if (response.status === 200) {
            basicSuccessCount++;
          }
        } catch (error) {
          // Rate limited
        }
      }

      expect(premiumSuccessCount).to.be.greaterThan(basicSuccessCount);
    });
  });

  describe('Request/Response Transformation', () => {
    it('should transform request headers for backend services', async () => {
      const response = await request(gatewayApp)
        .get('/api/users/headers-test')
        .set('X-Client-Version', '1.2.3')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.headers).to.include({
        'x-service-name': 'api-gateway',
        'x-request-id': response.body.headers['x-request-id']
      });
      expect(response.body.headers['x-user-id']).to.exist;
    });

    it('should transform response data format', async () => {
      const response = await request(gatewayApp)
        .get('/api/analytics/raw-data')
        .expect(200);

      // Should wrap response in standard format
      expect(response.body).to.have.property('success', true);
      expect(response.body).to.have.property('data');
      expect(response.body).to.have.property('timestamp');
      expect(response.body).to.have.property('service', 'analytics-service');
    });

    it('should handle error response transformation', async () => {
      const response = await request(gatewayApp)
        .get('/api/users/error-test')
        .expect(500);

      expect(response.body).to.have.property('success', false);
      expect(response.body).to.have.property('error');
      expect(response.body).to.have.property('timestamp');
      expect(response.body).to.have.property('requestId');
    });
  });

  describe('Circuit Breaker', () => {
    it('should open circuit breaker after multiple failures', async function() {
      this.timeout(20000);
      
      // Simulate service failures
      const failingEndpoint = '/api/external/unstable-service';
      let circuitOpenCount = 0;

      // Make multiple requests to trigger circuit breaker
      for (let i = 0; i < 10; i++) {
        try {
          const response = await request(gatewayApp)
            .get(failingEndpoint);
          
          if (response.status === 503 && 
              response.body.error && 
              response.body.error.includes('Circuit breaker open')) {
            circuitOpenCount++;
          }
        } catch (error) {
          // Expected for failing service
        }
        
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      expect(circuitOpenCount).to.be.greaterThan(0);
    });

    it('should reset circuit breaker after timeout', async function() {
      this.timeout(35000);
      
      // Wait for circuit breaker to enter half-open state
      await new Promise(resolve => setTimeout(resolve, 30000));
      
      const response = await request(gatewayApp)
        .get('/api/external/recovered-service')
        .expect(200);

      expect(response.body.service).to.equal('external-service');
    });
  });

  describe('Health Check Routing', () => {
    it('should route health checks to all services', async () => {
      const response = await request(gatewayApp)
        .get('/health/services')
        .expect(200);

      expect(response.body.services).to.be.an('object');
      expect(response.body.services).to.have.property('user-service');
      expect(response.body.services).to.have.property('trading-service');
      expect(response.body.services).to.have.property('analytics-service');
      expect(response.body.services).to.have.property('notification-service');
    });

    it('should provide overall health status', async () => {
      const response = await request(gatewayApp)
        .get('/health')
        .expect(200);

      expect(response.body).to.have.property('status', 'healthy');
      expect(response.body).to.have.property('uptime');
      expect(response.body).to.have.property('timestamp');
    });
  });

  // Helper functions
  async function createMockServices() {
    // User Service Mock
    const userApp = express();
    userApp.use(express.json());
    userApp.get('/users', (req, res) => {
      res.json({
        service: 'user-service',
        endpoint: '/users',
        users: [{ id: 1, name: 'John Doe' }, { id: 2, name: 'Jane Smith' }]
      });
    });
    userApp.get('/users/load-test', (req, res) => {
      res.json({
        service: 'user-service',
        instanceId: 'user-instance-1'
      });
    });
    userApp.get('/users/failover-test', (req, res) => {
      res.json({
        service: 'user-service',
        instanceId: 'user-instance-1'
      });
    });
    userApp.get('/users/headers-test', (req, res) => {
      res.json({
        service: 'user-service',
        headers: req.headers
      });
    });
    userApp.get('/users/error-test', (req, res) => {
      res.status(500).json({ error: 'Internal server error' });
    });
    mockServices.userService = userApp.listen(3001);

    // User Service Instance 2 (for load balancing test)
    const userApp2 = express();
    userApp2.use(express.json());
    userApp2.get('/users/load-test', (req, res) => {
      res.json({
        service: 'user-service',
        instanceId: 'user-instance-2'
      });
    });
    mockServices.userService2 = userApp2.listen(3011);

    // Trading Service Mock
    const tradingApp = express();
    tradingApp.use(express.json());
    tradingApp.post('/orders', (req, res) => {
      res.status(201).json({
        service: 'trading-service',
        endpoint: '/orders',
        order: { id: 'order-123', ...req.body }
      });
    });
    tradingApp.get('/positions', (req, res) => {
      res.json({
        service: 'trading-service',
        positions: [{ symbol: 'AAPL', quantity: 100 }]
      });
    });
    mockServices.tradingService = tradingApp.listen(3002);

    // Analytics Service Mock
    const analyticsApp = express();
    analyticsApp.use(express.json());
    analyticsApp.get('/portfolio/summary', (req, res) => {
      res.json({
        service: 'analytics-service',
        endpoint: '/portfolio/summary',
        portfolio: { totalValue: 50000, dayChange: 250 }
      });
    });
    analyticsApp.get('/compute-intensive', (req, res) => {
      res.json({ service: 'analytics-service', result: 'computed' });
    });
    analyticsApp.get('/premium-data', (req, res) => {
      res.json({ service: 'analytics-service', data: 'premium' });
    });
    analyticsApp.get('/raw-data', (req, res) => {
      res.json({ rawData: [1, 2, 3, 4, 5] });
    });
    mockServices.analyticsService = analyticsApp.listen(3003);

    // Notification Service Mock
    const notificationApp = express();
    notificationApp.use(express.json());
    notificationApp.post('/send', (req, res) => {
      res.json({
        service: 'notification-service',
        success: true,
        notificationId: 'notif-123'
      });
    });
    mockServices.notificationService = notificationApp.listen(3004);

    // External Service Mock (for circuit breaker testing)
    const externalApp = express();
    let failureCount = 0;
    externalApp.get('/unstable-service', (req, res) => {
      failureCount++;
      if (failureCount <= 5) {
        res.status(500).json({ error: 'Service unavailable' });
      } else {
        res.json({ service: 'external-service', status: 'recovered' });
      }
    });
    externalApp.get('/recovered-service', (req, res) => {
      res.json({ service: 'external-service', status: 'healthy' });
    });
    mockServices.externalService = externalApp.listen(3005);
  }

  async function createAPIGateway() {
    const app = express();
    app.use(express.json());

    // Rate limiting middleware
    const limiter = rateLimit({
      windowMs: 1 * 60 * 1000, // 1 minute
      max: 10, // limit each IP to 10 requests per windowMs
      message: { error: 'Too many requests' }
    });

    const premiumLimiter = rateLimit({
      windowMs: 1 * 60 * 1000,
      max: 25, // Premium users get higher limits
      message: { error: 'Too many requests' }
    });

    // Authentication middleware
    const authenticate = (req, res, next) => {
      const authHeader = req.headers.authorization;
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Authentication required' });
      }
      
      const token = authHeader.substring(7);
      if (token === 'valid-token') {
        req.user = { id: 'user123', role: 'user' };
      } else if (token === 'premium-token') {
        req.user = { id: 'premium123', role: 'premium', tier: 'premium' };
      } else if (token === 'admin-token') {
        req.user = { id: 'admin123', role: 'admin' };
      } else {
        return res.status(401).json({ error: 'Invalid token' });
      }
      
      next();
    };

    // Request transformation middleware
    const transformRequest = (req, res, next) => {
      req.headers['x-service-name'] = 'api-gateway';
      req.headers['x-request-id'] = `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      if (req.user) {
        req.headers['x-user-id'] = req.user.id;
        req.headers['x-user-role'] = req.user.role;
      }
      next();
    };

    // Response transformation middleware
    const transformResponse = (req, res, next) => {
      const originalSend = res.send;
      res.send = function(data) {
        if (req.path.includes('/raw-data')) {
          const transformedData = {
            success: true,
            data: JSON.parse(data),
            timestamp: new Date().toISOString(),
            service: 'analytics-service'
          };
          data = JSON.stringify(transformedData);
        }
        originalSend.call(this, data);
      };
      next();
    };

    // Error handling middleware
    const errorHandler = (err, req, res, next) => {
      res.status(500).json({
        success: false,
        error: err.message,
        timestamp: new Date().toISOString(),
        requestId: req.headers['x-request-id']
      });
    };

    // Auth endpoint
    app.post('/api/auth/login', (req, res) => {
      const { username, password } = req.body;
      if (username === 'testuser' && password === 'testpassword') {
        res.json({ token: 'valid-token', user: { id: 'user123', username } });
      } else {
        res.status(401).json({ error: 'Invalid credentials' });
      }
    });

    // Health endpoints
    app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
      });
    });

    app.get('/health/services', async (req, res) => {
      const services = {
        'user-service': { healthy: true, responseTime: 50 },
        'trading-service': { healthy: true, responseTime: 75 },
        'analytics-service': { healthy: true, responseTime: 120 },
        'notification-service': { healthy: true, responseTime: 30 }
      };
      res.json({ services });
    });

    // Apply middleware
    app.use(transformRequest);
    app.use(transformResponse);

    // Rate limiting for specific endpoints
    app.use('/api/analytics/compute-intensive', limiter);
    app.use('/api/analytics/premium-data', (req, res, next) => {
      if (req.user && req.user.tier === 'premium') {
        premiumLimiter(req, res, next);
      } else {
        limiter(req, res, next);
      }
    });

    // Protected routes
    app.use('/api/trading', authenticate);
    app.use('/api/admin', authenticate, (req, res, next) => {
      if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
      }
      next();
    });

    // Service proxies with load balancing
    const userServiceInstances = ['http://localhost:3001', 'http://localhost:3011'];
    let userServiceIndex = 0;

    app.use('/api/users', (req, res, next) => {
      const targetUrl = userServiceInstances[userServiceIndex % userServiceInstances.length];
      userServiceIndex++;
      
      const proxy = createProxyMiddleware({
        target: targetUrl,
        changeOrigin: true,
        pathRewrite: { '^/api/users': '' },
        onError: (err, req, res) => {
          res.status(503).json({ error: 'Service unavailable' });
        }
      });
      
      proxy(req, res, next);
    });

    app.use('/api/trading', createProxyMiddleware({
      target: 'http://localhost:3002',
      changeOrigin: true,
      pathRewrite: { '^/api/trading': '' }
    }));

    app.use('/api/analytics', createProxyMiddleware({
      target: 'http://localhost:3003',
      changeOrigin: true,
      pathRewrite: { '^/api/analytics': '' }
    }));

    app.use('/api/notifications', createProxyMiddleware({
      target: 'http://localhost:3004',
      changeOrigin: true,
      pathRewrite: { '^/api/notifications': '' }
    }));

    // Circuit breaker simulation
    let circuitOpen = false;
    let failureCount = 0;
    const circuitThreshold = 3;
    
    app.use('/api/external', (req, res, next) => {
      if (circuitOpen) {
        return res.status(503).json({ error: 'Circuit breaker open' });
      }
      
      const proxy = createProxyMiddleware({
        target: 'http://localhost:3005',
        changeOrigin: true,
        pathRewrite: { '^/api/external': '' },
        onError: (err, req, res) => {
          failureCount++;
          if (failureCount >= circuitThreshold) {
            circuitOpen = true;
            // Reset after 30 seconds
            setTimeout(() => {
              circuitOpen = false;
              failureCount = 0;
            }, 30000);
          }
          res.status(503).json({ error: 'Service unavailable' });
        }
      });
      
      proxy(req, res, next);
    });

    app.use(errorHandler);

    return app;
  }

  async function getPremiumUserToken() {
    // Mock premium user authentication
    return 'premium-token';
  }
});
