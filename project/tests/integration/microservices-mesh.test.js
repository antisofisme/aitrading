/**
 * End-to-End Microservices Mesh Integration Tests
 * Tests complete service mesh functionality with Plan2 architecture
 */

const { expect } = require('chai');
const axios = require('axios');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');
const { performance } = require('perf_hooks');

describe('Microservices Mesh Integration Tests', () => {
  let serviceEndpoints;
  let testUser;
  let authToken;
  let wsConnections = new Map();
  const testData = new Map();

  before(async function() {
    this.timeout(30000);
    
    // Initialize service endpoints
    serviceEndpoints = {
      configService: process.env.CONFIG_SERVICE_URL || 'http://localhost:3001',
      apiGateway: process.env.API_GATEWAY_URL || 'http://localhost:3000',
      databaseService: process.env.DATABASE_SERVICE_URL || 'http://localhost:3002',
      userService: process.env.USER_SERVICE_URL || 'http://localhost:3003',
      tradingService: process.env.TRADING_SERVICE_URL || 'http://localhost:3004',
      portfolioService: process.env.PORTFOLIO_SERVICE_URL || 'http://localhost:3005',
      analyticsService: process.env.ANALYTICS_SERVICE_URL || 'http://localhost:3006',
      notificationService: process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:3007'
    };
    
    // Setup test environment
    await setupTestEnvironment();
    
    console.log('Microservices mesh test environment ready');
  });

  after(async function() {
    this.timeout(10000);
    
    // Cleanup test environment
    await cleanupTestEnvironment();
  });

  describe('Service Discovery and Registration', () => {
    it('should discover all services through configuration service', async () => {
      const discoveryResponse = await axios.get(
        `${serviceEndpoints.configService}/api/services`
      );

      expect(discoveryResponse.status).to.equal(200);
      expect(discoveryResponse.data.success).to.be.true;
      expect(discoveryResponse.data.services).to.be.an('array');
      
      const serviceNames = discoveryResponse.data.services.map(s => s.name);
      expect(serviceNames).to.include.members([
        'api-gateway',
        'database-service',
        'user-service',
        'trading-service',
        'portfolio-service',
        'analytics-service',
        'notification-service'
      ]);
    });

    it('should validate service health across the mesh', async () => {
      const healthResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/health/services`
      );

      expect(healthResponse.status).to.equal(200);
      expect(healthResponse.data.services).to.be.an('object');
      
      // Verify all critical services are healthy
      const criticalServices = [
        'configuration-service',
        'database-service',
        'user-service',
        'trading-service',
        'portfolio-service'
      ];
      
      criticalServices.forEach(serviceName => {
        expect(healthResponse.data.services[serviceName]).to.include({
          healthy: true
        });
      });
    });

    it('should handle dynamic service registration and deregistration', async () => {
      const dynamicService = {
        name: 'test-dynamic-service',
        version: '1.0.0',
        host: 'localhost',
        port: 9999,
        healthCheckUrl: '/health',
        endpoints: [
          { path: '/api/test', method: 'GET' }
        ],
        tags: ['test', 'dynamic'],
        metadata: {
          description: 'Test dynamic service registration'
        }
      };

      // Register dynamic service
      const registerResponse = await axios.post(
        `${serviceEndpoints.configService}/api/services/register`,
        dynamicService
      );

      expect(registerResponse.status).to.equal(201);
      expect(registerResponse.data.success).to.be.true;

      // Verify service appears in discovery
      const discoveryResponse = await axios.get(
        `${serviceEndpoints.configService}/api/services/discover/test-dynamic-service`
      );

      expect(discoveryResponse.status).to.equal(200);
      expect(discoveryResponse.data.service.name).to.equal('test-dynamic-service');

      // Deregister service
      const deregisterResponse = await axios.delete(
        `${serviceEndpoints.configService}/api/services/test-dynamic-service`
      );

      expect(deregisterResponse.status).to.equal(200);
      expect(deregisterResponse.data.success).to.be.true;
    });
  });

  describe('Complete User Journey Integration', () => {
    it('should handle complete user registration and authentication flow', async () => {
      const registrationData = {
        username: `testuser_${Date.now()}`,
        email: `test_${Date.now()}@example.com`,
        password: 'SecurePassword123!',
        firstName: 'Test',
        lastName: 'User',
        phoneNumber: '+1234567890',
        preferences: {
          notifications: true,
          theme: 'dark',
          tradingLevel: 'intermediate'
        }
      };

      // User registration through API Gateway
      const registrationResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/auth/register`,
        registrationData
      );

      expect(registrationResponse.status).to.equal(201);
      expect(registrationResponse.data.success).to.be.true;
      expect(registrationResponse.data.user.id).to.exist;
      
      testUser = registrationResponse.data.user;

      // Login and get authentication token
      const loginResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/auth/login`,
        {
          email: registrationData.email,
          password: registrationData.password
        }
      );

      expect(loginResponse.status).to.equal(200);
      expect(loginResponse.data.success).to.be.true;
      expect(loginResponse.data.token).to.exist;
      
      authToken = loginResponse.data.token;

      // Verify user data propagated across services
      const userProfileResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/api/users/profile`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(userProfileResponse.status).to.equal(200);
      expect(userProfileResponse.data.user.email).to.equal(registrationData.email);
    });

    it('should handle complete trading workflow', async function() {
      this.timeout(45000);
      
      // First, fund the account
      const fundingResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/accounts/deposit`,
        {
          amount: 10000,
          currency: 'USD',
          paymentMethod: 'bank_transfer'
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(fundingResponse.status).to.equal(200);
      expect(fundingResponse.data.success).to.be.true;

      // Place a buy order
      const buyOrderData = {
        symbol: 'AAPL',
        side: 'buy',
        quantity: 10,
        orderType: 'market',
        timeInForce: 'GTC'
      };

      const buyOrderResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/trading/orders`,
        buyOrderData,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(buyOrderResponse.status).to.equal(201);
      expect(buyOrderResponse.data.success).to.be.true;
      expect(buyOrderResponse.data.order.id).to.exist;
      
      const orderId = buyOrderResponse.data.order.id;
      testData.set('buyOrderId', orderId);

      // Monitor order status until filled
      let orderStatus = 'pending';
      let attempts = 0;
      const maxAttempts = 30;

      while (orderStatus !== 'filled' && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const statusResponse = await axios.get(
          `${serviceEndpoints.apiGateway}/api/trading/orders/${orderId}`,
          {
            headers: { Authorization: `Bearer ${authToken}` }
          }
        );
        
        orderStatus = statusResponse.data.order.status;
        attempts++;
      }

      expect(orderStatus).to.equal('filled');

      // Verify portfolio was updated
      const portfolioResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/api/portfolio`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(portfolioResponse.status).to.equal(200);
      expect(portfolioResponse.data.portfolio.positions).to.be.an('array');
      
      const aaplPosition = portfolioResponse.data.portfolio.positions.find(
        pos => pos.symbol === 'AAPL'
      );
      expect(aaplPosition).to.exist;
      expect(aaplPosition.quantity).to.equal(10);
    });

    it('should handle portfolio analytics and reporting', async () => {
      // Request portfolio analytics
      const analyticsResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/api/analytics/portfolio/summary`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(analyticsResponse.status).to.equal(200);
      expect(analyticsResponse.data.success).to.be.true;
      expect(analyticsResponse.data.analytics).to.be.an('object');
      expect(analyticsResponse.data.analytics).to.have.property('totalValue');
      expect(analyticsResponse.data.analytics).to.have.property('dayChange');
      expect(analyticsResponse.data.analytics).to.have.property('allocation');

      // Request risk analysis
      const riskResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/api/analytics/risk/assessment`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(riskResponse.status).to.equal(200);
      expect(riskResponse.data.riskMetrics).to.be.an('object');
      expect(riskResponse.data.riskMetrics).to.have.property('beta');
      expect(riskResponse.data.riskMetrics).to.have.property('sharpeRatio');
      expect(riskResponse.data.riskMetrics).to.have.property('valueAtRisk');
    });

    it('should handle notifications across the journey', async () => {
      // Check notifications generated during the trading workflow
      const notificationsResponse = await axios.get(
        `${serviceEndpoints.apiGateway}/api/notifications`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(notificationsResponse.status).to.equal(200);
      expect(notificationsResponse.data.notifications).to.be.an('array');
      
      const notifications = notificationsResponse.data.notifications;
      
      // Should have notifications for registration, funding, and trading
      const notificationTypes = notifications.map(n => n.type);
      expect(notificationTypes).to.include.members([
        'account_funded',
        'order_filled'
      ]);
    });
  });

  describe('Real-time Data Flow and Communication', () => {
    it('should handle real-time market data streaming', async function() {
      this.timeout(30000);
      
      // Set up WebSocket connection for market data
      const marketDataWs = new WebSocket(
        `ws://localhost:3000/api/market-data/stream`,
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      
      wsConnections.set('marketData', marketDataWs);
      
      const marketUpdates = [];
      
      marketDataWs.on('message', (data) => {
        const update = JSON.parse(data.toString());
        marketUpdates.push(update);
      });

      await new Promise((resolve) => {
        marketDataWs.on('open', () => {
          // Subscribe to AAPL updates
          marketDataWs.send(JSON.stringify({
            action: 'subscribe',
            symbols: ['AAPL', 'GOOGL', 'MSFT'],
            updateTypes: ['price', 'volume', 'bid_ask']
          }));
          resolve();
        });
      });

      // Wait for market data updates
      await new Promise(resolve => setTimeout(resolve, 10000));

      expect(marketUpdates.length).to.be.greaterThan(0);
      expect(marketUpdates[0]).to.have.property('symbol');
      expect(marketUpdates[0]).to.have.property('price');
      expect(marketUpdates[0]).to.have.property('timestamp');
    });

    it('should handle real-time portfolio updates', async function() {
      this.timeout(20000);
      
      // Set up WebSocket connection for portfolio updates
      const portfolioWs = new WebSocket(
        `ws://localhost:3000/api/portfolio/stream`,
        { headers: { Authorization: `Bearer ${authToken}` } }
      );
      
      wsConnections.set('portfolio', portfolioWs);
      
      const portfolioUpdates = [];
      
      portfolioWs.on('message', (data) => {
        const update = JSON.parse(data.toString());
        portfolioUpdates.push(update);
      });

      await new Promise((resolve) => {
        portfolioWs.on('open', () => {
          portfolioWs.send(JSON.stringify({
            action: 'subscribe',
            updateTypes: ['value_change', 'position_update', 'pnl_update']
          }));
          resolve();
        });
      });

      // Place a small trade to trigger portfolio update
      await axios.post(
        `${serviceEndpoints.apiGateway}/api/trading/orders`,
        {
          symbol: 'MSFT',
          side: 'buy',
          quantity: 1,
          orderType: 'market'
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      // Wait for portfolio updates
      await new Promise(resolve => setTimeout(resolve, 5000));

      expect(portfolioUpdates.length).to.be.greaterThan(0);
      expect(portfolioUpdates.some(update => update.type === 'position_update')).to.be.true;
    });

    it('should handle cross-service event propagation', async () => {
      const eventData = {
        eventType: 'market_alert',
        symbol: 'AAPL',
        alertType: 'price_target',
        threshold: 150.00,
        direction: 'above'
      };

      // Publish event through event bus
      const eventResponse = await axios.post(
        `${serviceEndpoints.configService}/api/events/publish`,
        eventData,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(eventResponse.status).to.equal(200);
      expect(eventResponse.data.success).to.be.true;
      expect(eventResponse.data.eventId).to.exist;

      // Verify event was processed by relevant services
      await new Promise(resolve => setTimeout(resolve, 3000));

      const eventLogResponse = await axios.get(
        `${serviceEndpoints.configService}/api/events/${eventResponse.data.eventId}/processing-log`
      );

      expect(eventLogResponse.status).to.equal(200);
      expect(eventLogResponse.data.processingLog).to.be.an('array');
      
      const processedServices = eventLogResponse.data.processingLog.map(log => log.service);
      expect(processedServices).to.include.members([
        'analytics-service',
        'notification-service'
      ]);
    });
  });

  describe('Performance and Load Testing', () => {
    it('should handle concurrent user operations', async function() {
      this.timeout(60000);
      
      const concurrentOperations = [];
      const numberOfOperations = 20;

      // Simulate concurrent portfolio requests
      for (let i = 0; i < numberOfOperations; i++) {
        const operation = axios.get(
          `${serviceEndpoints.apiGateway}/api/portfolio/performance`,
          {
            headers: { Authorization: `Bearer ${authToken}` }
          }
        );
        concurrentOperations.push(operation);
      }

      const startTime = performance.now();
      const results = await Promise.allSettled(concurrentOperations);
      const endTime = performance.now();

      const successfulOps = results.filter(result => 
        result.status === 'fulfilled' && 
        result.value.status === 200
      );

      expect(successfulOps.length).to.be.at.least(numberOfOperations * 0.95); // 95% success rate
      expect(endTime - startTime).to.be.lessThan(10000); // Complete within 10 seconds
    });

    it('should maintain performance under database load', async function() {
      this.timeout(45000);
      
      const databaseOperations = [];
      const numberOfOps = 50;

      // Create multiple concurrent database operations
      for (let i = 0; i < numberOfOps; i++) {
        const operation = axios.post(
          `${serviceEndpoints.databaseService}/api/database/execute`,
          {
            database: 'postgres',
            operation: 'select',
            tableName: 'users',
            conditions: { id: testUser.id },
            fields: ['id', 'username', 'email']
          }
        );
        databaseOperations.push(operation);
      }

      const startTime = performance.now();
      const results = await Promise.allSettled(databaseOperations);
      const endTime = performance.now();

      const successfulOps = results.filter(result => 
        result.status === 'fulfilled' && 
        result.value.status === 200
      );

      expect(successfulOps.length).to.equal(numberOfOps);
      expect(endTime - startTime).to.be.lessThan(15000); // Complete within 15 seconds
      
      // Check average response time
      const avgResponseTime = (endTime - startTime) / numberOfOps;
      expect(avgResponseTime).to.be.lessThan(300); // Average under 300ms
    });

    it('should handle flow execution under load', async function() {
      this.timeout(90000);
      
      // Create a test flow for load testing
      const loadTestFlow = {
        id: uuidv4(),
        name: 'load-test-flow',
        version: '1.0.0',
        description: 'Flow for load testing the mesh',
        steps: [
          {
            id: 'get-user',
            type: 'service_call',
            service: 'user-service',
            action: 'getUserById',
            parameters: { userId: '${input.userId}' },
            timeout: 5000
          },
          {
            id: 'get-portfolio',
            type: 'service_call',
            service: 'portfolio-service',
            action: 'getPortfolio',
            parameters: { userId: '${input.userId}' },
            dependsOn: ['get-user'],
            timeout: 5000
          },
          {
            id: 'calculate-metrics',
            type: 'service_call',
            service: 'analytics-service',
            action: 'calculateMetrics',
            parameters: { portfolio: '${step.get-portfolio.result}' },
            dependsOn: ['get-portfolio'],
            timeout: 10000
          }
        ]
      };

      await axios.post(
        `${serviceEndpoints.configService}/api/flows/register`,
        loadTestFlow
      );

      // Execute flow multiple times concurrently
      const flowExecutions = [];
      const numberOfExecutions = 15;

      for (let i = 0; i < numberOfExecutions; i++) {
        const execution = axios.post(
          `${serviceEndpoints.configService}/api/flows/${loadTestFlow.id}/execute`,
          {
            input: { userId: testUser.id },
            executionMode: 'async'
          }
        );
        flowExecutions.push(execution);
      }

      const startTime = performance.now();
      const results = await Promise.allSettled(flowExecutions);
      const endTime = performance.now();

      const successfulExecutions = results.filter(result => 
        result.status === 'fulfilled' && 
        result.value.status === 202
      );

      expect(successfulExecutions.length).to.be.at.least(numberOfExecutions * 0.9); // 90% success rate
      expect(endTime - startTime).to.be.lessThan(30000); // Complete within 30 seconds
    });
  });

  describe('Data Consistency and ACID Properties', () => {
    it('should maintain data consistency across distributed operations', async () => {
      const initialBalance = await getAccountBalance();
      const initialPortfolioValue = await getPortfolioValue();

      // Perform a large trade that affects multiple services
      const largeTradeResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/trading/orders`,
        {
          symbol: 'GOOGL',
          side: 'buy',
          quantity: 5,
          orderType: 'market'
        },
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      );

      expect(largeTradeResponse.status).to.equal(201);

      // Wait for settlement
      await new Promise(resolve => setTimeout(resolve, 5000));

      const finalBalance = await getAccountBalance();
      const finalPortfolioValue = await getPortfolioValue();
      const tradeDetails = await getTradeDetails(largeTradeResponse.data.order.id);

      // Verify consistency: Balance decrease should match trade cost
      const balanceChange = initialBalance - finalBalance;
      const tradeCost = tradeDetails.executedPrice * tradeDetails.executedQuantity;
      
      expect(Math.abs(balanceChange - tradeCost)).to.be.lessThan(0.01); // Allow for rounding
      
      // Verify portfolio value increased
      expect(finalPortfolioValue).to.be.greaterThan(initialPortfolioValue);
    });

    it('should handle distributed transaction rollbacks', async () => {
      const initialState = await captureSystemState();

      // Attempt a transaction that will fail at the final step
      const failingTransactionFlow = {
        id: uuidv4(),
        name: 'failing-transaction-test',
        version: '1.0.0',
        description: 'Test distributed transaction rollback',
        steps: [
          {
            id: 'reserve-funds',
            type: 'service_call',
            service: 'account-service',
            action: 'reserveFunds',
            parameters: {
              userId: testUser.id,
              amount: 1000
            },
            compensationAction: {
              service: 'account-service',
              action: 'releaseFunds'
            }
          },
          {
            id: 'create-temp-position',
            type: 'service_call',
            service: 'portfolio-service',
            action: 'createTempPosition',
            parameters: {
              symbol: 'TEMP',
              quantity: 100
            },
            dependsOn: ['reserve-funds'],
            compensationAction: {
              service: 'portfolio-service',
              action: 'removeTempPosition'
            }
          },
          {
            id: 'invalid-operation',
            type: 'service_call',
            service: 'invalid-service',
            action: 'impossibleAction',
            dependsOn: ['create-temp-position']
          }
        ],
        errorHandling: {
          compensationStrategy: 'reverse_order'
        }
      };

      await axios.post(
        `${serviceEndpoints.configService}/api/flows/register`,
        failingTransactionFlow
      );

      const executionResponse = await axios.post(
        `${serviceEndpoints.configService}/api/flows/${failingTransactionFlow.id}/execute`,
        {
          input: {},
          executionMode: 'sync'
        }
      );

      expect(executionResponse.data.success).to.be.false;
      expect(executionResponse.data.execution.compensationExecuted).to.be.true;

      // Wait for rollback completion
      await new Promise(resolve => setTimeout(resolve, 3000));

      const finalState = await captureSystemState();

      // Verify system state returned to initial state
      expect(finalState.accountBalance).to.equal(initialState.accountBalance);
      expect(finalState.portfolioPositions).to.deep.equal(initialState.portfolioPositions);
    });
  });

  describe('Security and Access Control', () => {
    it('should enforce proper authentication across all services', async () => {
      const protectedEndpoints = [
        `${serviceEndpoints.apiGateway}/api/portfolio`,
        `${serviceEndpoints.apiGateway}/api/trading/orders`,
        `${serviceEndpoints.apiGateway}/api/analytics/portfolio/summary`,
        `${serviceEndpoints.apiGateway}/api/notifications`,
        `${serviceEndpoints.apiGateway}/api/users/profile`
      ];

      for (const endpoint of protectedEndpoints) {
        // Test without authentication
        try {
          await axios.get(endpoint);
          expect.fail(`Endpoint ${endpoint} should require authentication`);
        } catch (error) {
          expect(error.response.status).to.equal(401);
        }

        // Test with invalid token
        try {
          await axios.get(endpoint, {
            headers: { Authorization: 'Bearer invalid-token' }
          });
          expect.fail(`Endpoint ${endpoint} should reject invalid tokens`);
        } catch (error) {
          expect(error.response.status).to.equal(401);
        }

        // Test with valid token
        const response = await axios.get(endpoint, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        expect(response.status).to.be.oneOf([200, 404]); // 404 if resource doesn't exist
      }
    });

    it('should enforce proper authorization and data isolation', async () => {
      // Create another user
      const secondUserResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/auth/register`,
        {
          username: `testuser2_${Date.now()}`,
          email: `test2_${Date.now()}@example.com`,
          password: 'SecurePassword123!',
          firstName: 'Test2',
          lastName: 'User2'
        }
      );

      const secondUserLoginResponse = await axios.post(
        `${serviceEndpoints.apiGateway}/api/auth/login`,
        {
          email: secondUserResponse.data.user.email,
          password: 'SecurePassword123!'
        }
      );

      const secondUserToken = secondUserLoginResponse.data.token;

      // Try to access first user's data with second user's token
      try {
        await axios.get(
          `${serviceEndpoints.apiGateway}/api/users/${testUser.id}/profile`,
          {
            headers: { Authorization: `Bearer ${secondUserToken}` }
          }
        );
        expect.fail('Should not allow access to other user\'s data');
      } catch (error) {
        expect(error.response.status).to.be.oneOf([403, 404]); // Forbidden or Not Found
      }
    });
  });

  // Helper functions
  async function setupTestEnvironment() {
    try {
      // Verify all services are available
      const healthChecks = Object.entries(serviceEndpoints).map(async ([name, url]) => {
        try {
          const response = await axios.get(`${url}/health`, { timeout: 5000 });
          return { name, healthy: response.status === 200 };
        } catch (error) {
          return { name, healthy: false, error: error.message };
        }
      });

      const healthResults = await Promise.all(healthChecks);
      const unhealthyServices = healthResults.filter(result => !result.healthy);
      
      if (unhealthyServices.length > 0) {
        console.warn('Some services are not healthy:', unhealthyServices);
      }

      console.log('Test environment setup completed');
    } catch (error) {
      console.error('Failed to setup test environment:', error.message);
      throw error;
    }
  }

  async function cleanupTestEnvironment() {
    try {
      // Close WebSocket connections
      wsConnections.forEach((ws, name) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });

      // Clean up test data if possible
      if (testUser && authToken) {
        try {
          await axios.delete(
            `${serviceEndpoints.apiGateway}/api/users/profile`,
            {
              headers: { Authorization: `Bearer ${authToken}` }
            }
          );
        } catch (error) {
          console.warn('Failed to cleanup test user:', error.message);
        }
      }

      console.log('Test environment cleanup completed');
    } catch (error) {
      console.warn('Test environment cleanup failed:', error.message);
    }
  }

  async function getAccountBalance() {
    const response = await axios.get(
      `${serviceEndpoints.apiGateway}/api/accounts/balance`,
      {
        headers: { Authorization: `Bearer ${authToken}` }
      }
    );
    return response.data.balance.available;
  }

  async function getPortfolioValue() {
    const response = await axios.get(
      `${serviceEndpoints.apiGateway}/api/portfolio/value`,
      {
        headers: { Authorization: `Bearer ${authToken}` }
      }
    );
    return response.data.totalValue;
  }

  async function getTradeDetails(orderId) {
    const response = await axios.get(
      `${serviceEndpoints.apiGateway}/api/trading/orders/${orderId}`,
      {
        headers: { Authorization: `Bearer ${authToken}` }
      }
    );
    return response.data.order;
  }

  async function captureSystemState() {
    const [balance, portfolio] = await Promise.all([
      getAccountBalance(),
      axios.get(
        `${serviceEndpoints.apiGateway}/api/portfolio`,
        {
          headers: { Authorization: `Bearer ${authToken}` }
        }
      )
    ]);

    return {
      accountBalance: balance,
      portfolioPositions: portfolio.data.portfolio.positions
    };
  }
});
