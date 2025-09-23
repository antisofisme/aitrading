/**
 * Flow Registry Communication Tests
 * Tests flow creation and execution across services using Flow Registry
 */

const { expect } = require('chai');
const axios = require('axios');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

describe('Flow Registry Communication Tests', () => {
  let configServiceUrl;
  let flowRegistryClient;
  let wsConnection;
  const testFlows = new Map();
  
  before(async function() {
    this.timeout(15000);
    
    configServiceUrl = process.env.CONFIG_SERVICE_URL || 'http://localhost:3001';
    
    // Initialize Flow Registry client
    await initializeFlowRegistry();
    
    console.log('Flow Registry communication tests ready');
  });

  after(async function() {
    // Cleanup flows and connections
    await cleanupFlowRegistry();
  });

  describe('Flow Definition and Registration', () => {
    it('should register a simple trading flow', async () => {
      const tradingFlow = {
        id: uuidv4(),
        name: 'simple-trading-flow',
        version: '1.0.0',
        description: 'Basic trading flow for order execution',
        triggers: [
          {
            type: 'api_call',
            endpoint: '/api/trading/execute-order',
            method: 'POST'
          }
        ],
        steps: [
          {
            id: 'validate-order',
            type: 'validation',
            service: 'trading-service',
            action: 'validateOrder',
            parameters: {
              requiredFields: ['symbol', 'quantity', 'type'],
              validTypes: ['market', 'limit', 'stop']
            },
            timeout: 5000
          },
          {
            id: 'check-balance',
            type: 'service_call',
            service: 'account-service',
            action: 'checkBalance',
            parameters: {
              userId: '${input.userId}',
              requiredAmount: '${calculated.orderValue}'
            },
            dependsOn: ['validate-order'],
            timeout: 3000
          },
          {
            id: 'execute-trade',
            type: 'service_call',
            service: 'trading-service',
            action: 'executeTrade',
            parameters: {
              order: '${input}',
              accountId: '${step.check-balance.accountId}'
            },
            dependsOn: ['check-balance'],
            timeout: 10000
          },
          {
            id: 'update-portfolio',
            type: 'service_call',
            service: 'portfolio-service',
            action: 'updatePortfolio',
            parameters: {
              userId: '${input.userId}',
              trade: '${step.execute-trade.result}'
            },
            dependsOn: ['execute-trade'],
            timeout: 5000
          },
          {
            id: 'send-notification',
            type: 'service_call',
            service: 'notification-service',
            action: 'sendTradeConfirmation',
            parameters: {
              userId: '${input.userId}',
              trade: '${step.execute-trade.result}'
            },
            dependsOn: ['update-portfolio'],
            timeout: 3000,
            optional: true
          }
        ],
        errorHandling: {
          retryPolicy: {
            maxRetries: 3,
            backoffStrategy: 'exponential',
            retryableErrors: ['TIMEOUT', 'SERVICE_UNAVAILABLE']
          },
          rollbackSteps: [
            {
              stepId: 'execute-trade',
              rollbackAction: 'cancelTrade',
              service: 'trading-service'
            }
          ]
        },
        monitoring: {
          metrics: ['execution_time', 'success_rate', 'error_rate'],
          alerts: [
            {
              condition: 'execution_time > 30000',
              action: 'send_alert',
              severity: 'warning'
            },
            {
              condition: 'error_rate > 0.05',
              action: 'send_alert',
              severity: 'critical'
            }
          ]
        }
      };

      const response = await axios.post(
        `${configServiceUrl}/api/flows/register`,
        tradingFlow
      );

      expect(response.status).to.equal(201);
      expect(response.data.success).to.be.true;
      expect(response.data.flow.id).to.equal(tradingFlow.id);
      expect(response.data.flow.status).to.equal('registered');
      
      testFlows.set(tradingFlow.id, tradingFlow);
    });

    it('should register a complex analytics flow with parallel execution', async () => {
      const analyticsFlow = {
        id: uuidv4(),
        name: 'portfolio-analytics-flow',
        version: '1.0.0',
        description: 'Comprehensive portfolio analytics with parallel risk calculations',
        triggers: [
          {
            type: 'scheduled',
            schedule: '0 9 * * 1-5', // Every weekday at 9 AM
            timezone: 'America/New_York'
          },
          {
            type: 'event',
            eventType: 'market_close',
            source: 'market-data-service'
          }
        ],
        steps: [
          {
            id: 'fetch-portfolios',
            type: 'service_call',
            service: 'portfolio-service',
            action: 'getAllActivePortfolios',
            timeout: 10000
          },
          {
            id: 'parallel-analysis',
            type: 'parallel',
            dependsOn: ['fetch-portfolios'],
            branches: [
              {
                id: 'risk-analysis',
                steps: [
                  {
                    id: 'calculate-var',
                    type: 'service_call',
                    service: 'risk-service',
                    action: 'calculateVaR',
                    parameters: {
                      portfolios: '${step.fetch-portfolios.result}',
                      confidence: 0.95,
                      timeHorizon: 1
                    },
                    timeout: 30000
                  },
                  {
                    id: 'stress-test',
                    type: 'service_call',
                    service: 'risk-service',
                    action: 'performStressTest',
                    parameters: {
                      portfolios: '${step.fetch-portfolios.result}',
                      scenarios: ['market_crash', 'interest_rate_spike', 'volatility_surge']
                    },
                    timeout: 45000
                  }
                ]
              },
              {
                id: 'performance-analysis',
                steps: [
                  {
                    id: 'calculate-returns',
                    type: 'service_call',
                    service: 'analytics-service',
                    action: 'calculateReturns',
                    parameters: {
                      portfolios: '${step.fetch-portfolios.result}',
                      periods: ['1d', '1w', '1m', '3m', '6m', '1y']
                    },
                    timeout: 20000
                  },
                  {
                    id: 'benchmark-comparison',
                    type: 'service_call',
                    service: 'analytics-service',
                    action: 'compareToBenchmarks',
                    parameters: {
                      portfolios: '${step.fetch-portfolios.result}',
                      benchmarks: ['SPY', 'QQQ', 'VTI']
                    },
                    timeout: 15000
                  }
                ]
              },
              {
                id: 'compliance-check',
                steps: [
                  {
                    id: 'check-regulations',
                    type: 'service_call',
                    service: 'compliance-service',
                    action: 'checkRegulatory',
                    parameters: {
                      portfolios: '${step.fetch-portfolios.result}',
                      regulations: ['FINRA', 'SEC', 'CFTC']
                    },
                    timeout: 10000
                  }
                ]
              }
            ]
          },
          {
            id: 'consolidate-results',
            type: 'aggregation',
            dependsOn: ['parallel-analysis'],
            parameters: {
              aggregationStrategy: 'merge',
              outputFormat: 'comprehensive_report'
            },
            timeout: 5000
          },
          {
            id: 'store-results',
            type: 'service_call',
            service: 'database-service',
            action: 'storeAnalyticsResults',
            parameters: {
              results: '${step.consolidate-results.output}',
              timestamp: '${execution.startTime}'
            },
            dependsOn: ['consolidate-results'],
            timeout: 10000
          },
          {
            id: 'generate-alerts',
            type: 'conditional',
            dependsOn: ['consolidate-results'],
            conditions: [
              {
                if: '${step.consolidate-results.riskLevel} > "high"',
                then: {
                  type: 'service_call',
                  service: 'notification-service',
                  action: 'sendRiskAlert',
                  parameters: {
                    severity: 'high',
                    details: '${step.consolidate-results.riskDetails}'
                  }
                }
              },
              {
                if: '${step.consolidate-results.complianceIssues.length} > 0',
                then: {
                  type: 'service_call',
                  service: 'notification-service',
                  action: 'sendComplianceAlert',
                  parameters: {
                    issues: '${step.consolidate-results.complianceIssues}'
                  }
                }
              }
            ],
            timeout: 5000
          }
        ],
        configuration: {
          maxConcurrentExecutions: 3,
          executionTimeout: 300000, // 5 minutes
          retainHistory: 30 // days
        }
      };

      const response = await axios.post(
        `${configServiceUrl}/api/flows/register`,
        analyticsFlow
      );

      expect(response.status).to.equal(201);
      expect(response.data.success).to.be.true;
      expect(response.data.flow.id).to.equal(analyticsFlow.id);
      
      testFlows.set(analyticsFlow.id, analyticsFlow);
    });

    it('should validate flow definitions', async () => {
      const invalidFlow = {
        id: uuidv4(),
        name: 'invalid-flow',
        // Missing required fields like version, steps
        steps: [
          {
            // Missing required id and type
            service: 'some-service'
          }
        ]
      };

      try {
        await axios.post(
          `${configServiceUrl}/api/flows/register`,
          invalidFlow
        );
        expect.fail('Should have thrown validation error');
      } catch (error) {
        expect(error.response.status).to.equal(400);
        expect(error.response.data.success).to.be.false;
        expect(error.response.data.error).to.contain('validation');
      }
    });
  });

  describe('Flow Execution and Orchestration', () => {
    it('should execute a registered flow with input parameters', async function() {
      this.timeout(30000);
      
      const flowId = Array.from(testFlows.keys())[0]; // Get first registered flow
      const executionInput = {
        userId: 'test-user-123',
        symbol: 'AAPL',
        quantity: 100,
        type: 'market',
        clientOrderId: `order-${Date.now()}`
      };

      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${flowId}/execute`,
        {
          input: executionInput,
          executionMode: 'async',
          callbackUrl: 'http://localhost:3000/api/flow-callbacks'
        }
      );

      expect(executionResponse.status).to.equal(202);
      expect(executionResponse.data.success).to.be.true;
      expect(executionResponse.data.executionId).to.exist;
      
      const executionId = executionResponse.data.executionId;

      // Poll for execution status
      let status = 'running';
      let attempts = 0;
      const maxAttempts = 30;

      while (status === 'running' && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const statusResponse = await axios.get(
          `${configServiceUrl}/api/flows/executions/${executionId}/status`
        );
        
        status = statusResponse.data.execution.status;
        attempts++;
      }

      expect(status).to.be.oneOf(['completed', 'partial_success']);
    });

    it('should handle flow execution with real-time monitoring', async function() {
      this.timeout(45000);
      
      const flowId = Array.from(testFlows.keys())[1]; // Get analytics flow
      
      // Set up WebSocket connection for real-time monitoring
      const wsUrl = `ws://localhost:3001/api/flows/monitor`;
      wsConnection = new WebSocket(wsUrl);
      
      const monitoringEvents = [];
      
      wsConnection.on('message', (data) => {
        const event = JSON.parse(data.toString());
        monitoringEvents.push(event);
      });

      await new Promise((resolve) => {
        wsConnection.on('open', resolve);
      });

      // Subscribe to flow execution events
      wsConnection.send(JSON.stringify({
        action: 'subscribe',
        flowId: flowId,
        eventTypes: ['step_started', 'step_completed', 'step_failed', 'execution_completed']
      }));

      // Execute the flow
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${flowId}/execute`,
        {
          input: { triggerType: 'manual', timestamp: new Date().toISOString() },
          executionMode: 'monitored'
        }
      );

      expect(executionResponse.status).to.equal(202);
      const executionId = executionResponse.data.executionId;

      // Wait for execution to complete and collect events
      await new Promise((resolve) => {
        const checkCompletion = () => {
          const completionEvent = monitoringEvents.find(event => 
            event.type === 'execution_completed' && 
            event.executionId === executionId
          );
          
          if (completionEvent) {
            resolve();
          } else {
            setTimeout(checkCompletion, 1000);
          }
        };
        
        checkCompletion();
      });

      // Verify monitoring events were received
      expect(monitoringEvents.length).to.be.greaterThan(0);
      
      const stepEvents = monitoringEvents.filter(event => 
        event.executionId === executionId && 
        ['step_started', 'step_completed'].includes(event.type)
      );
      
      expect(stepEvents.length).to.be.greaterThan(0);
    });

    it('should handle flow execution errors and rollbacks', async function() {
      this.timeout(20000);
      
      // Create a flow that will intentionally fail
      const failingFlow = {
        id: uuidv4(),
        name: 'failing-flow',
        version: '1.0.0',
        description: 'Flow designed to test error handling',
        steps: [
          {
            id: 'successful-step',
            type: 'service_call',
            service: 'test-service',
            action: 'successfulAction',
            timeout: 5000
          },
          {
            id: 'failing-step',
            type: 'service_call',
            service: 'non-existent-service',
            action: 'impossibleAction',
            dependsOn: ['successful-step'],
            timeout: 5000
          }
        ],
        errorHandling: {
          rollbackSteps: [
            {
              stepId: 'successful-step',
              rollbackAction: 'undoSuccessfulAction',
              service: 'test-service'
            }
          ]
        }
      };

      // Register the failing flow
      await axios.post(
        `${configServiceUrl}/api/flows/register`,
        failingFlow
      );

      // Execute the failing flow
      const executionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${failingFlow.id}/execute`,
        {
          input: { test: 'data' },
          executionMode: 'sync'
        }
      );

      expect(executionResponse.status).to.equal(200);
      expect(executionResponse.data.success).to.be.false;
      expect(executionResponse.data.execution.status).to.equal('failed');
      expect(executionResponse.data.execution.rollbackExecuted).to.be.true;
    });
  });

  describe('Cross-Service Communication', () => {
    it('should facilitate communication between services through flows', async () => {
      const communicationFlow = {
        id: uuidv4(),
        name: 'cross-service-communication',
        version: '1.0.0',
        description: 'Test cross-service communication patterns',
        steps: [
          {
            id: 'fetch-user-data',
            type: 'service_call',
            service: 'user-service',
            action: 'getUserById',
            parameters: {
              userId: '${input.userId}'
            },
            timeout: 5000
          },
          {
            id: 'get-portfolio',
            type: 'service_call',
            service: 'portfolio-service',
            action: 'getPortfolioByUserId',
            parameters: {
              userId: '${input.userId}',
              includeHistory: true
            },
            dependsOn: ['fetch-user-data'],
            timeout: 10000
          },
          {
            id: 'calculate-metrics',
            type: 'service_call',
            service: 'analytics-service',
            action: 'calculatePortfolioMetrics',
            parameters: {
              portfolio: '${step.get-portfolio.result}',
              userPreferences: '${step.fetch-user-data.preferences}'
            },
            dependsOn: ['get-portfolio'],
            timeout: 15000
          },
          {
            id: 'store-cache',
            type: 'service_call',
            service: 'cache-service',
            action: 'storeUserMetrics',
            parameters: {
              userId: '${input.userId}',
              metrics: '${step.calculate-metrics.result}',
              ttl: 3600
            },
            dependsOn: ['calculate-metrics'],
            timeout: 3000
          }
        ]
      };

      // Register the communication flow
      const registerResponse = await axios.post(
        `${configServiceUrl}/api/flows/register`,
        communicationFlow
      );

      expect(registerResponse.status).to.equal(201);

      // Test service discovery through flow registry
      const discoveryResponse = await axios.get(
        `${configServiceUrl}/api/flows/${communicationFlow.id}/services`
      );

      expect(discoveryResponse.status).to.equal(200);
      expect(discoveryResponse.data.services).to.include.members([
        'user-service',
        'portfolio-service',
        'analytics-service',
        'cache-service'
      ]);
    });

    it('should handle service dependency resolution', async () => {
      const dependencyResponse = await axios.get(
        `${configServiceUrl}/api/flows/dependencies/cross-service-communication`
      );

      expect(dependencyResponse.status).to.equal(200);
      expect(dependencyResponse.data.dependencies).to.be.an('object');
      expect(dependencyResponse.data.dependencies).to.have.property('services');
      expect(dependencyResponse.data.dependencies).to.have.property('executionOrder');
    });

    it('should provide flow-based service health monitoring', async () => {
      const healthResponse = await axios.get(
        `${configServiceUrl}/api/flows/health/services`
      );

      expect(healthResponse.status).to.equal(200);
      expect(healthResponse.data.services).to.be.an('object');
      
      // Check that services used in flows are monitored
      const monitoredServices = Object.keys(healthResponse.data.services);
      expect(monitoredServices).to.include.members([
        'user-service',
        'portfolio-service',
        'analytics-service'
      ]);
    });
  });

  describe('Flow Metrics and Analytics', () => {
    it('should collect execution metrics for registered flows', async () => {
      const metricsResponse = await axios.get(
        `${configServiceUrl}/api/flows/metrics/summary`
      );

      expect(metricsResponse.status).to.equal(200);
      expect(metricsResponse.data.metrics).to.be.an('object');
      expect(metricsResponse.data.metrics).to.have.property('totalExecutions');
      expect(metricsResponse.data.metrics).to.have.property('successRate');
      expect(metricsResponse.data.metrics).to.have.property('averageExecutionTime');
    });

    it('should provide flow-specific performance analytics', async () => {
      const flowId = Array.from(testFlows.keys())[0];
      
      const analyticsResponse = await axios.get(
        `${configServiceUrl}/api/flows/${flowId}/analytics?period=1d`
      );

      expect(analyticsResponse.status).to.equal(200);
      expect(analyticsResponse.data.analytics).to.be.an('object');
      expect(analyticsResponse.data.analytics).to.have.property('executionCount');
      expect(analyticsResponse.data.analytics).to.have.property('stepPerformance');
    });

    it('should track service communication patterns', async () => {
      const patternsResponse = await axios.get(
        `${configServiceUrl}/api/flows/analytics/communication-patterns`
      );

      expect(patternsResponse.status).to.equal(200);
      expect(patternsResponse.data.patterns).to.be.an('object');
      expect(patternsResponse.data.patterns).to.have.property('serviceInteractions');
      expect(patternsResponse.data.patterns).to.have.property('communicationFrequency');
    });
  });

  describe('Flow Versioning and Updates', () => {
    it('should support flow versioning', async () => {
      const flowId = Array.from(testFlows.keys())[0];
      const originalFlow = testFlows.get(flowId);
      
      // Create new version of the flow
      const updatedFlow = {
        ...originalFlow,
        version: '1.1.0',
        description: 'Updated trading flow with enhanced validation',
        steps: [
          ...originalFlow.steps,
          {
            id: 'enhanced-validation',
            type: 'validation',
            service: 'enhanced-validation-service',
            action: 'validateEnhanced',
            parameters: {
              riskChecks: true,
              complianceChecks: true
            },
            insertAfter: 'validate-order',
            timeout: 5000
          }
        ]
      };

      const versionResponse = await axios.post(
        `${configServiceUrl}/api/flows/${flowId}/versions`,
        updatedFlow
      );

      expect(versionResponse.status).to.equal(201);
      expect(versionResponse.data.version).to.equal('1.1.0');
    });

    it('should list flow versions', async () => {
      const flowId = Array.from(testFlows.keys())[0];
      
      const versionsResponse = await axios.get(
        `${configServiceUrl}/api/flows/${flowId}/versions`
      );

      expect(versionsResponse.status).to.equal(200);
      expect(versionsResponse.data.versions).to.be.an('array');
      expect(versionsResponse.data.versions.length).to.be.at.least(2);
    });

    it('should support gradual flow rollouts', async () => {
      const flowId = Array.from(testFlows.keys())[0];
      
      const rolloutResponse = await axios.post(
        `${configServiceUrl}/api/flows/${flowId}/rollout`,
        {
          targetVersion: '1.1.0',
          strategy: 'canary',
          percentage: 10, // Start with 10% traffic
          criteria: {
            successRate: 0.95,
            maxErrorRate: 0.05
          }
        }
      );

      expect(rolloutResponse.status).to.equal(200);
      expect(rolloutResponse.data.rollout.status).to.equal('started');
    });
  });

  // Helper functions
  async function initializeFlowRegistry() {
    try {
      // Check if Flow Registry is available
      const healthResponse = await axios.get(`${configServiceUrl}/api/flows/health`);
      expect(healthResponse.status).to.equal(200);
      
      // Initialize any required flow registry components
      const initResponse = await axios.post(`${configServiceUrl}/api/flows/initialize`, {
        registryMode: 'test',
        enableMonitoring: true,
        enableMetrics: true
      });
      
      expect(initResponse.status).to.equal(200);
      
      console.log('Flow Registry initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Flow Registry:', error.message);
      throw error;
    }
  }

  async function cleanupFlowRegistry() {
    try {
      // Clean up test flows
      const cleanupPromises = Array.from(testFlows.keys()).map(async (flowId) => {
        try {
          await axios.delete(`${configServiceUrl}/api/flows/${flowId}`);
        } catch (error) {
          console.warn(`Failed to cleanup flow ${flowId}:`, error.message);
        }
      });
      
      await Promise.all(cleanupPromises);
      
      // Close WebSocket connection if open
      if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.close();
      }
      
      console.log('Flow Registry cleanup completed');
    } catch (error) {
      console.warn('Flow Registry cleanup failed:', error.message);
    }
  }
});
