/**
 * Error Propagation Integration Tests
 * Tests Flow-Aware Error Handling across service boundaries
 */

const { expect } = require('chai');
const axios = require('axios');
const express = require('express');
const { v4: uuidv4 } = require('uuid');

describe('Error Propagation Integration Tests', () => {
  let errorTestServices = {};
  let configServiceUrl;
  let apiGatewayUrl;
  const testScenarios = new Map();

  before(async function() {
    this.timeout(20000);
    
    configServiceUrl = process.env.CONFIG_SERVICE_URL || 'http://localhost:3001';
    apiGatewayUrl = process.env.API_GATEWAY_URL || 'http://localhost:3000';
    
    // Set up mock services for error testing
    await setupErrorTestServices();
    
    console.log('Error propagation test environment ready');
  });

  after(async function() {
    // Cleanup test services
    Object.values(errorTestServices).forEach(server => {
      if (server && server.close) {
        server.close();
      }
    });
  });

  describe('Service-Level Error Handling', () => {
    it('should propagate HTTP error codes correctly', async () => {
      const testCases = [
        { status: 400, expectedPropagation: 'client_error' },
        { status: 401, expectedPropagation: 'authentication_error' },
        { status: 403, expectedPropagation: 'authorization_error' },
        { status: 404, expectedPropagation: 'not_found_error' },
        { status: 500, expectedPropagation: 'server_error' },
        { status: 502, expectedPropagation: 'bad_gateway_error' },
        { status: 503, expectedPropagation: 'service_unavailable_error' },
        { status: 504, expectedPropagation: 'timeout_error' }
      ];

      for (const testCase of testCases) {
        try {
          await axios.get(`${apiGatewayUrl}/api/error-test/http-error/${testCase.status}`);
          expect.fail(`Should have thrown error for status ${testCase.status}`);
        } catch (error) {
          expect(error.response.status).to.equal(testCase.status);
          expect(error.response.data.errorType).to.equal(testCase.expectedPropagation);
          expect(error.response.data.flowAware).to.be.true;
        }
      }
    });

    it('should handle timeout errors with proper propagation', async function() {
      this.timeout(35000);
      
      try {
        await axios.get(`${apiGatewayUrl}/api/error-test/timeout/30000`, {
          timeout: 5000 // Client timeout shorter than service timeout
        });
        expect.fail('Should have thrown timeout error');
      } catch (error) {
        expect(error.code).to.equal('ECONNABORTED');
        
        // Check if the error was logged in the flow registry
        const errorLogResponse = await axios.get(
          `${configServiceUrl}/api/flows/errors/recent?errorType=timeout`
        );
        
        expect(errorLogResponse.status).to.equal(200);
        expect(errorLogResponse.data.errors.length).to.be.greaterThan(0);
      }
    });

    it('should handle connection errors and circuit breaker activation', async function() {
      this.timeout(30000);
      
      // Simulate connection failures
      const failures = [];
      
      for (let i = 0; i < 5; i++) {
        try {
          await axios.get(`${apiGatewayUrl}/api/error-test/connection-failure`);
        } catch (error) {
          failures.push(error.response?.status || error.code);
        }
      }

      expect(failures.length).to.equal(5);
      
      // Check circuit breaker status
      const circuitBreakerResponse = await axios.get(
        `${apiGatewayUrl}/api/internal/circuit-breaker/status/error-test-service`
      );
      
      expect(circuitBreakerResponse.status).to.equal(200);
      expect(circuitBreakerResponse.data.state).to.be.oneOf(['open', 'half-open']);
    });
  });

  describe('Flow-Aware Error Context', () => {
    it('should maintain error context across service calls', async () => {
      const flowContext = {
        flowId: uuidv4(),
        executionId: uuidv4(),
        stepId: 'test-step-001',
        userId: 'test-user-123',
        correlationId: uuidv4()
      };

      try {
        await axios.post(
          `${apiGatewayUrl}/api/error-test/flow-context-error`,
          { testData: 'test' },
          {
            headers: {
              'X-Flow-Id': flowContext.flowId,
              'X-Execution-Id': flowContext.executionId,
              'X-Step-Id': flowContext.stepId,
              'X-User-Id': flowContext.userId,
              'X-Correlation-Id': flowContext.correlationId
            }
          }
        );
        expect.fail('Should have thrown error');
      } catch (error) {
        expect(error.response.status).to.equal(500);
        expect(error.response.data.flowContext).to.include({
          flowId: flowContext.flowId,
          executionId: flowContext.executionId,
          stepId: flowContext.stepId
        });
        expect(error.response.data.errorId).to.exist;
        expect(error.response.data.timestamp).to.exist;
      }
    });

    it('should provide detailed error traces in flow execution', async () => {
      const chainedErrorFlow = {
        id: uuidv4(),
        name: 'chained-error-test-flow',
        version: '1.0.0',
        description: 'Flow to test error propagation through multiple services',
        steps: [
          {
            id: 'step-1',
            type: 'service_call',
            service: 'error-test-service',
            action: 'successfulOperation',
            timeout: 5000
          },
          {
            id: 'step-2',
            type: 'service_call',
            service: 'error-test-service',
            action: 'failingOperation',
            dependsOn: ['step-1'],
            timeout: 5000
          },
          {
            id: 'step-3',
            type: 'service_call',
            service: 'error-test-service',
            action: 'unreachableOperation',
            dependsOn: ['step-2'],
            timeout: 5000
          }
        ],
        errorHandling: {
          captureFullTrace: true,
          includeServiceLogs: true,
          retryPolicy: {
            maxRetries: 1,
            backoffStrategy: 'linear'
          }
        }
      };

      // Register the error test flow
      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        chainedErrorFlow
      );

      // Execute the flow
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${chainedErrorFlow.id}/execute`,
        {
          input: { test: 'error propagation' },
          executionMode: 'sync'
        }
      );

      expect(executionResponse.status).to.equal(200);
      expect(executionResponse.data.success).to.be.false;
      expect(executionResponse.data.execution.status).to.equal('failed');
      expect(executionResponse.data.execution.errorTrace).to.be.an('array');
      expect(executionResponse.data.execution.errorTrace.length).to.be.greaterThan(1);
      
      // Verify error trace contains step information
      const errorTrace = executionResponse.data.execution.errorTrace;
      expect(errorTrace[0]).to.include({
        stepId: 'step-2',
        errorType: 'business_logic_error'
      });
    });

    it('should handle partial failures with compensating actions', async () => {
      const compensationFlow = {
        id: uuidv4(),
        name: 'compensation-test-flow',
        version: '1.0.0',
        description: 'Flow to test compensating actions on partial failures',
        steps: [
          {
            id: 'create-order',
            type: 'service_call',
            service: 'order-service',
            action: 'createOrder',
            parameters: {
              symbol: '${input.symbol}',
              quantity: '${input.quantity}'
            },
            timeout: 5000,
            compensationAction: {
              service: 'order-service',
              action: 'cancelOrder',
              parameters: {
                orderId: '${step.create-order.orderId}'
              }
            }
          },
          {
            id: 'reserve-funds',
            type: 'service_call',
            service: 'account-service',
            action: 'reserveFunds',
            parameters: {
              userId: '${input.userId}',
              amount: '${input.totalAmount}'
            },
            dependsOn: ['create-order'],
            timeout: 5000,
            compensationAction: {
              service: 'account-service',
              action: 'releaseFunds',
              parameters: {
                reservationId: '${step.reserve-funds.reservationId}'
              }
            }
          },
          {
            id: 'execute-trade',
            type: 'service_call',
            service: 'trading-service',
            action: 'executeTrade',
            parameters: {
              orderId: '${step.create-order.orderId}',
              reservationId: '${step.reserve-funds.reservationId}'
            },
            dependsOn: ['reserve-funds'],
            timeout: 10000
          }
        ],
        errorHandling: {
          compensationStrategy: 'reverse_order',
          maxCompensationRetries: 3
        }
      };

      // Register the compensation flow
      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        compensationFlow
      );

      // Execute the flow with data that will cause trade execution to fail
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${compensationFlow.id}/execute`,
        {
          input: {
            userId: 'test-user-123',
            symbol: 'INVALID',
            quantity: 100,
            totalAmount: 15000
          },
          executionMode: 'sync'
        }
      );

      expect(executionResponse.status).to.equal(200);
      expect(executionResponse.data.success).to.be.false;
      expect(executionResponse.data.execution.compensationExecuted).to.be.true;
      expect(executionResponse.data.execution.compensatedSteps).to.include.members([
        'reserve-funds',
        'create-order'
      ]);
    });
  });

  describe('Cross-Service Error Coordination', () => {
    it('should coordinate error responses across multiple services', async () => {
      const multiServiceErrorScenario = {
        id: uuidv4(),
        name: 'multi-service-error-coordination',
        services: ['user-service', 'portfolio-service', 'notification-service'],
        errorType: 'database_connection_failure',
        expectedBehavior: {
          'user-service': 'return_cached_data',
          'portfolio-service': 'graceful_degradation',
          'notification-service': 'queue_for_retry'
        }
      };

      // Simulate coordinated error across services
      const coordinationResponse = await axios.post(
        `${configServiceUrl}/api/error-coordination/simulate`,
        multiServiceErrorScenario
      );

      expect(coordinationResponse.status).to.equal(200);
      expect(coordinationResponse.data.coordinationId).to.exist;

      // Test service responses during error condition
      const serviceResponses = await Promise.allSettled([
        axios.get(`${apiGatewayUrl}/api/users/test-user-123`),
        axios.get(`${apiGatewayUrl}/api/portfolio/test-user-123`),
        axios.post(`${apiGatewayUrl}/api/notifications/send`, {
          userId: 'test-user-123',
          message: 'Test notification'
        })
      ]);

      // User service should return cached data (success with warning)
      expect(serviceResponses[0].status).to.equal('fulfilled');
      expect(serviceResponses[0].value.data.source).to.equal('cache');
      expect(serviceResponses[0].value.data.warning).to.contain('degraded');

      // Portfolio service should return limited data (graceful degradation)
      expect(serviceResponses[1].status).to.equal('fulfilled');
      expect(serviceResponses[1].value.data.limited).to.be.true;

      // Notification service should queue the request
      expect(serviceResponses[2].status).to.equal('fulfilled');
      expect(serviceResponses[2].value.data.queued).to.be.true;
    });

    it('should handle cascading failures with proper isolation', async () => {
      const cascadeTestFlow = {
        id: uuidv4(),
        name: 'cascade-failure-test',
        version: '1.0.0',
        description: 'Test cascading failure isolation',
        steps: [
          {
            id: 'critical-service-call',
            type: 'service_call',
            service: 'critical-service',
            action: 'processData',
            criticality: 'high',
            isolationLevel: 'strict',
            timeout: 5000
          },
          {
            id: 'dependent-service-call-1',
            type: 'service_call',
            service: 'dependent-service-1',
            action: 'processResult',
            dependsOn: ['critical-service-call'],
            criticality: 'medium',
            isolationLevel: 'moderate',
            timeout: 5000
          },
          {
            id: 'dependent-service-call-2',
            type: 'service_call',
            service: 'dependent-service-2',
            action: 'logResult',
            dependsOn: ['critical-service-call'],
            criticality: 'low',
            isolationLevel: 'loose',
            timeout: 5000,
            optional: true
          }
        ],
        errorHandling: {
          isolationStrategy: 'bulkhead',
          failureThreshold: {
            'critical-service': 1,
            'dependent-service-1': 3,
            'dependent-service-2': 5
          }
        }
      };

      // Register cascade test flow
      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        cascadeTestFlow
      );

      // Execute flow that will cause critical service to fail
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${cascadeTestFlow.id}/execute`,
        {
          input: { trigger: 'critical_failure' },
          executionMode: 'sync'
        }
      );

      expect(executionResponse.data.execution.status).to.equal('failed');
      expect(executionResponse.data.execution.isolationTriggered).to.be.true;
      expect(executionResponse.data.execution.affectedServices).to.include('critical-service');
      expect(executionResponse.data.execution.isolatedServices).to.include.members([
        'dependent-service-1',
        'dependent-service-2'
      ]);
    });
  });

  describe('Error Recovery and Resilience', () => {
    it('should implement exponential backoff retry strategy', async function() {
      this.timeout(60000);
      
      const retryTestFlow = {
        id: uuidv4(),
        name: 'retry-strategy-test',
        version: '1.0.0',
        description: 'Test exponential backoff retry strategy',
        steps: [
          {
            id: 'unreliable-service-call',
            type: 'service_call',
            service: 'unreliable-service',
            action: 'intermittentFailure',
            timeout: 5000
          }
        ],
        errorHandling: {
          retryPolicy: {
            maxRetries: 5,
            backoffStrategy: 'exponential',
            baseDelay: 1000,
            maxDelay: 30000,
            jitter: true,
            retryableErrors: ['TIMEOUT', 'SERVICE_UNAVAILABLE', 'INTERNAL_ERROR']
          }
        }
      };

      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        retryTestFlow
      );

      const startTime = Date.now();
      
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${retryTestFlow.id}/execute`,
        {
          input: { failureRate: 0.7 }, // 70% failure rate
          executionMode: 'sync'
        }
      );

      const executionTime = Date.now() - startTime;

      expect(executionResponse.data.execution.retryAttempts).to.be.greaterThan(0);
      expect(executionResponse.data.execution.totalRetryDelay).to.be.greaterThan(1000);
      expect(executionTime).to.be.greaterThan(1000); // Should take at least base delay
    });

    it('should implement circuit breaker pattern with health monitoring', async function() {
      this.timeout(45000);
      
      const circuitBreakerFlow = {
        id: uuidv4(),
        name: 'circuit-breaker-test',
        version: '1.0.0',
        description: 'Test circuit breaker pattern implementation',
        steps: [
          {
            id: 'monitored-service-call',
            type: 'service_call',
            service: 'monitored-service',
            action: 'healthSensitiveOperation',
            timeout: 5000
          }
        ],
        errorHandling: {
          circuitBreaker: {
            failureThreshold: 3,
            recoveryTimeout: 10000,
            halfOpenRequestLimit: 2,
            healthCheckInterval: 5000
          }
        }
      };

      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        circuitBreakerFlow
      );

      // Execute multiple requests to trigger circuit breaker
      const failurePromises = [];
      
      for (let i = 0; i < 5; i++) {
        failurePromises.push(
          axios.post(
            `${configServiceUrl}/api/flows/${circuitBreakerFlow.id}/execute`,
            {
              input: { shouldFail: true },
              executionMode: 'sync'
            }
          ).catch(error => error.response)
        );
        
        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      const failureResponses = await Promise.all(failurePromises);
      
      // Check that circuit breaker opened after threshold
      const circuitOpenResponses = failureResponses.filter(response => 
        response.data?.execution?.circuitBreakerState === 'open'
      );
      
      expect(circuitOpenResponses.length).to.be.greaterThan(0);

      // Wait for potential recovery and test half-open state
      await new Promise(resolve => setTimeout(resolve, 12000));
      
      const recoveryResponse = await axios.post(
        `${configServiceUrl}/api/flows/${circuitBreakerFlow.id}/execute`,
        {
          input: { shouldFail: false },
          executionMode: 'sync'
        }
      );

      expect(recoveryResponse.data.execution.circuitBreakerState).to.be.oneOf(['half-open', 'closed']);
    });
  });

  describe('Error Monitoring and Alerting', () => {
    it('should generate alerts for error rate thresholds', async () => {
      const alertingResponse = await axios.get(
        `${configServiceUrl}/api/monitoring/alerts/error-rates`
      );

      expect(alertingResponse.status).to.equal(200);
      expect(alertingResponse.data.alerts).to.be.an('array');
      
      // Check for recent error rate alerts
      const recentAlerts = alertingResponse.data.alerts.filter(alert => 
        new Date(alert.timestamp) > new Date(Date.now() - 300000) // Last 5 minutes
      );
      
      if (recentAlerts.length > 0) {
        expect(recentAlerts[0]).to.have.property('severity');
        expect(recentAlerts[0]).to.have.property('errorRate');
        expect(recentAlerts[0]).to.have.property('affectedServices');
      }
    });

    it('should provide error analytics and trends', async () => {
      const analyticsResponse = await axios.get(
        `${configServiceUrl}/api/monitoring/error-analytics?period=1h`
      );

      expect(analyticsResponse.status).to.equal(200);
      expect(analyticsResponse.data.analytics).to.be.an('object');
      expect(analyticsResponse.data.analytics).to.have.property('totalErrors');
      expect(analyticsResponse.data.analytics).to.have.property('errorsByService');
      expect(analyticsResponse.data.analytics).to.have.property('errorsByType');
      expect(analyticsResponse.data.analytics).to.have.property('trends');
    });

    it('should track error correlation across services', async () => {
      const correlationResponse = await axios.get(
        `${configServiceUrl}/api/monitoring/error-correlation?timeWindow=30m`
      );

      expect(correlationResponse.status).to.equal(200);
      expect(correlationResponse.data.correlations).to.be.an('array');
      
      if (correlationResponse.data.correlations.length > 0) {
        expect(correlationResponse.data.correlations[0]).to.have.property('correlationId');
        expect(correlationResponse.data.correlations[0]).to.have.property('affectedServices');
        expect(correlationResponse.data.correlations[0]).to.have.property('correlationStrength');
      }
    });
  });

  // Helper functions
  async function setupErrorTestServices() {
    // Error Test Service
    const errorTestApp = express();
    errorTestApp.use(express.json());
    
    // HTTP Error endpoints
    errorTestApp.get('/http-error/:status', (req, res) => {
      const status = parseInt(req.params.status);
      const errorTypes = {
        400: 'client_error',
        401: 'authentication_error',
        403: 'authorization_error',
        404: 'not_found_error',
        500: 'server_error',
        502: 'bad_gateway_error',
        503: 'service_unavailable_error',
        504: 'timeout_error'
      };
      
      res.status(status).json({
        success: false,
        errorType: errorTypes[status] || 'unknown_error',
        flowAware: true,
        message: `Simulated ${status} error`,
        timestamp: new Date().toISOString()
      });
    });
    
    // Timeout endpoint
    errorTestApp.get('/timeout/:duration', (req, res) => {
      const duration = parseInt(req.params.duration);
      setTimeout(() => {
        res.json({ message: 'Delayed response', duration });
      }, duration);
    });
    
    // Connection failure endpoint
    errorTestApp.get('/connection-failure', (req, res) => {
      // Simulate connection drop
      req.socket.destroy();
    });
    
    // Flow context error endpoint
    errorTestApp.post('/flow-context-error', (req, res) => {
      const flowContext = {
        flowId: req.headers['x-flow-id'],
        executionId: req.headers['x-execution-id'],
        stepId: req.headers['x-step-id'],
        userId: req.headers['x-user-id'],
        correlationId: req.headers['x-correlation-id']
      };
      
      res.status(500).json({
        success: false,
        error: 'Simulated flow context error',
        flowContext,
        errorId: uuidv4(),
        timestamp: new Date().toISOString(),
        serviceName: 'error-test-service'
      });
    });
    
    errorTestServices.errorTestService = errorTestApp.listen(3010);
    
    // Unreliable Service (for retry testing)
    const unreliableApp = express();
    unreliableApp.use(express.json());
    
    let requestCount = 0;
    unreliableApp.post('/intermittent-failure', (req, res) => {
      requestCount++;
      const failureRate = req.body.failureRate || 0.5;
      
      if (Math.random() < failureRate && requestCount < 4) {
        res.status(503).json({
          success: false,
          error: 'Service temporarily unavailable',
          attempt: requestCount
        });
      } else {
        res.json({
          success: true,
          message: 'Service available',
          attempt: requestCount
        });
      }
    });
    
    errorTestServices.unreliableService = unreliableApp.listen(3011);
    
    // Monitored Service (for circuit breaker testing)
    const monitoredApp = express();
    monitoredApp.use(express.json());
    
    let healthStatus = true;
    monitoredApp.post('/health-sensitive-operation', (req, res) => {
      const shouldFail = req.body.shouldFail;
      
      if (shouldFail) {
        healthStatus = false;
        res.status(500).json({
          success: false,
          error: 'Service is unhealthy',
          healthStatus
        });
      } else {
        healthStatus = true;
        res.json({
          success: true,
          message: 'Service is healthy',
          healthStatus
        });
      }
    });
    
    monitoredApp.get('/health', (req, res) => {
      res.json({ healthy: healthStatus });
    });
    
    errorTestServices.monitoredService = monitoredApp.listen(3012);
    
    console.log('Error test services started');
  }
});
