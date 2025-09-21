/**
 * Data Bridge Service Integration Tests
 * Testing Data Bridge service startup, WebSocket connections, and data flow
 */

const config = require('../config/test-config');
const helpers = require('../utils/test-helpers');

describe('Data Bridge Service Integration Tests', () => {
  const { dataBridge } = config;
  let testResults = [];

  beforeAll(async () => {
    console.log('🌉 Starting Data Bridge Service integration tests...');

    // Check if Data Bridge Service is running
    const isPortOpen = await helpers.isPortOpen('localhost', dataBridge.expectedPort);
    if (!isPortOpen) {
      console.warn(`⚠️  Data Bridge Service port ${dataBridge.expectedPort} is not open. Some tests may fail.`);
    }
  });

  afterAll(async () => {
    await helpers.cleanup();
    console.log('📊 Data Bridge Service test results:', helpers.formatTestResults(testResults));
  });

  describe('Service Connectivity', () => {
    test('Data Bridge Service should be accessible on configured port', async () => {
      const isPortOpen = await helpers.isPortOpen('localhost', dataBridge.expectedPort);

      testResults.push({
        test: 'Port Accessibility',
        status: isPortOpen ? 'passed' : 'failed',
        details: { port: dataBridge.expectedPort, accessible: isPortOpen }
      });

      expect(isPortOpen).toBe(true);
    }, 10000);

    test('Health endpoint should return service status', async () => {
      const health = await helpers.checkHealth(dataBridge.baseUrl, dataBridge.endpoints.health);

      testResults.push({
        test: 'Health Endpoint',
        status: health.isHealthy ? 'passed' : 'failed',
        details: health
      });

      expect(health.isHealthy).toBe(true);
      expect(health.status).toBe(200);
      expect(health.data).toHaveProperty('status', 'healthy');
      expect(health.data).toHaveProperty('timestamp');
      expect(health.data).toHaveProperty('uptime');
    }, 15000);

    test('Service should report MT5 connection status', async () => {
      const health = await helpers.checkHealth(dataBridge.baseUrl, dataBridge.endpoints.health);

      const hasMT5Status = health.data?.mt5Connected !== undefined;

      testResults.push({
        test: 'MT5 Connection Status',
        status: hasMT5Status ? 'passed' : 'failed',
        details: {
          mt5Connected: health.data?.mt5Connected,
          statusReported: hasMT5Status
        }
      });

      expect(health.isHealthy).toBe(true);
      expect(health.data).toHaveProperty('mt5Connected');
    }, 15000);
  });

  describe('API Endpoints', () => {
    test('Status endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('GET', `${dataBridge.baseUrl}${dataBridge.endpoints.status}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Status Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          hasData: response.data ? true : false
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);

    test('Symbols endpoint should be accessible', async () => {
      const response = await helpers.makeRequest('GET', `${dataBridge.baseUrl}${dataBridge.endpoints.symbols}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Symbols Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          hasSymbols: Array.isArray(response.data) || response.data?.symbols
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);

    test('Market data endpoint should handle symbol requests', async () => {
      const testSymbol = 'EURUSD';
      const response = await helpers.makeRequest('GET', `${dataBridge.baseUrl}${dataBridge.endpoints.marketData}/${testSymbol}`);

      const isAccessible = response.status < 500;

      testResults.push({
        test: 'Market Data Endpoint',
        status: isAccessible ? 'passed' : 'failed',
        details: {
          status: response.status,
          accessible: isAccessible,
          symbol: testSymbol,
          hasMarketData: response.data ? true : false
        }
      });

      expect(isAccessible).toBe(true);
    }, 10000);
  });

  describe('WebSocket Connectivity', () => {
    test('WebSocket server should be accessible', async () => {
      const wsTest = await helpers.testWebSocketConnection(dataBridge.wsUrl, { timeout: 10000 });

      testResults.push({
        test: 'WebSocket Connectivity',
        status: wsTest.connected ? 'passed' : 'failed',
        details: wsTest
      });

      expect(wsTest.connected).toBe(true);
    }, 15000);

    test('WebSocket should send welcome message on connection', async () => {
      const wsTest = await helpers.testWebSocketConnection(dataBridge.wsUrl, { timeout: 10000 });

      const hasWelcomeMessage = wsTest.connected && wsTest.welcomeMessage;

      testResults.push({
        test: 'WebSocket Welcome Message',
        status: hasWelcomeMessage ? 'passed' : 'failed',
        details: {
          connected: wsTest.connected,
          hasWelcome: hasWelcomeMessage,
          messageType: wsTest.welcomeMessage?.type,
          clientId: wsTest.welcomeMessage?.clientId
        }
      });

      if (wsTest.connected) {
        expect(wsTest.welcomeMessage).toBeDefined();
        expect(wsTest.welcomeMessage).toHaveProperty('type');
        expect(wsTest.welcomeMessage).toHaveProperty('timestamp');
      }
    }, 15000);

    test('WebSocket should handle ping/pong correctly', async () => {
      const WebSocket = require('ws');

      return new Promise((resolve) => {
        const ws = new WebSocket(dataBridge.wsUrl);
        let pingPongWorking = false;

        const timeout = setTimeout(() => {
          ws.close();
          testResults.push({
            test: 'WebSocket Ping/Pong',
            status: 'failed',
            details: { error: 'Timeout waiting for pong response' }
          });
          expect(pingPongWorking).toBe(true);
          resolve();
        }, 10000);

        ws.on('open', () => {
          // Send ping message
          ws.send(JSON.stringify({ type: 'ping' }));
        });

        ws.on('message', (data) => {
          try {
            const message = JSON.parse(data.toString());

            if (message.type === 'pong') {
              pingPongWorking = true;
              clearTimeout(timeout);
              ws.close();

              testResults.push({
                test: 'WebSocket Ping/Pong',
                status: 'passed',
                details: { pongReceived: true, timestamp: message.timestamp }
              });

              expect(pingPongWorking).toBe(true);
              resolve();
            }
          } catch (error) {
            clearTimeout(timeout);
            ws.close();

            testResults.push({
              test: 'WebSocket Ping/Pong',
              status: 'failed',
              details: { error: 'Invalid message format' }
            });

            expect(pingPongWorking).toBe(true);
            resolve();
          }
        });

        ws.on('error', (error) => {
          clearTimeout(timeout);
          testResults.push({
            test: 'WebSocket Ping/Pong',
            status: 'failed',
            details: { error: error.message }
          });
          expect(pingPongWorking).toBe(true);
          resolve();
        });
      });
    }, 15000);
  });

  describe('Error Handling', () => {
    test('Should handle invalid routes gracefully', async () => {
      const response = await helpers.makeRequest('GET', `${dataBridge.baseUrl}/invalid-route`);

      const handles404 = response.status === 404;

      testResults.push({
        test: '404 Error Handling',
        status: handles404 ? 'passed' : 'failed',
        details: {
          status: response.status,
          hasErrorMessage: response.data?.error ? true : false
        }
      });

      expect(response.status).toBe(404);
      expect(response.data).toHaveProperty('error');
    }, 10000);

    test('Should handle malformed requests gracefully', async () => {
      const response = await helpers.makeRequest('POST', `${dataBridge.baseUrl}${dataBridge.endpoints.status}`,
        'invalid-json',
        {
          axiosConfig: {
            headers: { 'Content-Type': 'application/json' },
            validateStatus: () => true
          }
        }
      );

      const handlesError = response.status >= 400 && response.status < 500;

      testResults.push({
        test: 'Malformed Request Handling',
        status: handlesError ? 'passed' : 'failed',
        details: {
          status: response.status,
          handlesError: handlesError
        }
      });

      expect(handlesError).toBe(true);
    }, 10000);
  });

  describe('Performance Tests', () => {
    test('Health endpoint response time should be fast', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.checkHealth(dataBridge.baseUrl, dataBridge.endpoints.health);
      }, 3);

      const isFast = performance.averageDuration < config.performance.responseTime.fast;

      testResults.push({
        test: 'Health Check Performance',
        status: isFast ? 'passed' : 'failed',
        details: {
          averageDuration: performance.averageDuration,
          threshold: config.performance.responseTime.fast,
          successRate: performance.successRate
        }
      });

      expect(performance.averageDuration).toBeLessThan(config.performance.responseTime.fast);
      expect(performance.successRate).toBe(100);
    }, 20000);

    test('WebSocket connection time should be acceptable', async () => {
      const performance = await helpers.measurePerformance(async () => {
        await helpers.testWebSocketConnection(dataBridge.wsUrl, { timeout: 5000 });
      }, 3);

      const isAcceptable = performance.averageDuration < config.performance.responseTime.acceptable;

      testResults.push({
        test: 'WebSocket Connection Performance',
        status: isAcceptable ? 'passed' : 'failed',
        details: {
          averageDuration: performance.averageDuration,
          threshold: config.performance.responseTime.acceptable,
          successRate: performance.successRate
        }
      });

      expect(performance.averageDuration).toBeLessThan(config.performance.responseTime.acceptable);
      expect(performance.successRate).toBeGreaterThan(66); // 66% success rate for WebSocket
    }, 25000);
  });
});