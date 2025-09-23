/**
 * Flow Registry Integration Tests
 * Tests Flow Registry implementation across all services
 */

const axios = require('axios');
const { performance } = require('perf_hooks');

class FlowRegistryTests {
  constructor() {
    this.services = {
      'database-service': { port: 8008, baseUrl: 'http://localhost:8008' },
      'configuration-service': { port: 8012, baseUrl: 'http://localhost:8012' },
      'ai-orchestrator': { port: 8020, baseUrl: 'http://localhost:8020' },
      'trading-engine': { port: 9010, baseUrl: 'http://localhost:9010' }
    };

    this.testResults = {
      flowIdPropagation: {},
      errorTracking: {},
      chainDebugging: {},
      flowMetrics: {},
      crossServiceTracking: {}
    };
  }

  /**
   * Test Flow ID Propagation Across Services
   */
  async testFlowIdPropagation() {
    console.log('\n🆔 Testing Flow ID Propagation...');

    const testFlowId = `flow-prop-${Date.now()}`;
    const propagationResults = {};

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        const response = await axios.get(`${config.baseUrl}/health`, {
          headers: {
            'X-Flow-ID': testFlowId,
            'X-Request-Source': 'flow-registry-test',
            'X-Test-Type': 'propagation'
          },
          timeout: 5000
        });

        // Check if service echoes back the flow ID
        const receivedFlowId = response.headers['x-flow-id'] ||
                              response.headers['x-request-id'] ||
                              response.data?.flowId;

        propagationResults[serviceName] = {
          status: 'success',
          flowIdSent: testFlowId,
          flowIdReceived: receivedFlowId,
          propagated: receivedFlowId === testFlowId,
          headers: this.extractFlowHeaders(response.headers),
          responseTime: response.headers['x-response-time'] || 'not-provided'
        };

        const propagatedIcon = receivedFlowId === testFlowId ? '✅' : '❌';
        console.log(`${propagatedIcon} ${serviceName}: Flow ID ${receivedFlowId === testFlowId ? 'propagated' : 'not propagated'}`);

      } catch (error) {
        propagationResults[serviceName] = {
          status: 'error',
          flowIdSent: testFlowId,
          error: error.message,
          propagated: false
        };
        console.log(`❌ ${serviceName}: Error - ${error.message}`);
      }
    }

    this.testResults.flowIdPropagation = propagationResults;
    return propagationResults;
  }

  /**
   * Test Error Tracking and Impact Analysis
   */
  async testErrorTracking() {
    console.log('\n🔍 Testing Error Tracking and Impact Analysis...');

    const errorFlowId = `error-track-${Date.now()}`;
    const errorResults = {};

    // Test error scenarios across different services
    const errorScenarios = [
      {
        service: 'database-service',
        endpoint: '/api/database/nonexistent',
        expectedError: 404
      },
      {
        service: 'trading-engine',
        endpoint: '/api/trading/invalid-order',
        expectedError: 400
      },
      {
        service: 'ai-orchestrator',
        endpoint: '/api/ai/invalid-model',
        expectedError: 404
      }
    ];

    for (const scenario of errorScenarios) {
      const service = this.services[scenario.service];
      if (!service) continue;

      try {
        await axios.get(`${service.baseUrl}${scenario.endpoint}`, {
          headers: {
            'X-Flow-ID': errorFlowId,
            'X-Error-Test': 'true',
            'X-Expected-Error': scenario.expectedError.toString()
          },
          timeout: 5000
        });

        // If no error thrown, that's unexpected
        errorResults[scenario.service] = {
          status: 'unexpected',
          expected: scenario.expectedError,
          actual: 'no-error',
          errorTracked: false
        };

      } catch (error) {
        const actualStatus = error.response?.status;
        const errorTracked = this.checkErrorTracking(error.response);

        errorResults[scenario.service] = {
          status: actualStatus === scenario.expectedError ? 'expected' : 'unexpected',
          expected: scenario.expectedError,
          actual: actualStatus,
          errorTracked: errorTracked,
          flowId: errorFlowId,
          errorDetails: {
            message: error.message,
            code: error.code,
            headers: this.extractFlowHeaders(error.response?.headers || {})
          }
        };

        const statusIcon = actualStatus === scenario.expectedError ? '✅' : '❌';
        const trackingIcon = errorTracked ? '📊' : '❌';
        console.log(`${statusIcon} ${scenario.service}: Error ${actualStatus} ${trackingIcon} Tracking`);
      }
    }

    this.testResults.errorTracking = errorResults;
    return errorResults;
  }

  /**
   * Test Chain Debugging Capabilities
   */
  async testChainDebugging() {
    console.log('\n🔗 Testing Chain Debugging...');

    const chainFlowId = `chain-debug-${Date.now()}`;
    const chainResults = [];

    // Create a simulated chain of service calls
    const chainSteps = [
      { service: 'configuration-service', step: 'config-retrieval' },
      { service: 'ai-orchestrator', step: 'signal-generation' },
      { service: 'trading-engine', step: 'order-processing' },
      { service: 'database-service', step: 'data-persistence' }
    ];

    let previousStepId = null;

    for (const [index, step] of chainSteps.entries()) {
      const service = this.services[step.service];
      if (!service) continue;

      const stepId = `${chainFlowId}-step-${index}`;

      try {
        const startTime = performance.now();

        const response = await axios.get(`${service.baseUrl}/health`, {
          headers: {
            'X-Flow-ID': chainFlowId,
            'X-Step-ID': stepId,
            'X-Previous-Step': previousStepId || 'none',
            'X-Step-Name': step.step,
            'X-Step-Index': index.toString(),
            'X-Chain-Debug': 'true'
          },
          timeout: 5000
        });

        const responseTime = performance.now() - startTime;

        chainResults.push({
          stepIndex: index,
          stepId: stepId,
          service: step.service,
          stepName: step.step,
          status: 'success',
          responseTime: Math.round(responseTime),
          timestamp: new Date().toISOString(),
          previousStep: previousStepId,
          chainTracking: this.checkChainTracking(response.headers),
          debugInfo: this.extractDebugInfo(response.headers)
        });

        console.log(`✅ Step ${index + 1} (${step.service}): ${step.step} - ${Math.round(responseTime)}ms`);

        previousStepId = stepId;

      } catch (error) {
        chainResults.push({
          stepIndex: index,
          stepId: stepId,
          service: step.service,
          stepName: step.step,
          status: 'error',
          error: error.message,
          timestamp: new Date().toISOString(),
          previousStep: previousStepId
        });

        console.log(`❌ Step ${index + 1} (${step.service}): ${step.step} - Error: ${error.message}`);
        break; // Stop chain on error
      }
    }

    this.testResults.chainDebugging = {
      flowId: chainFlowId,
      totalSteps: chainSteps.length,
      completedSteps: chainResults.filter(r => r.status === 'success').length,
      chain: chainResults
    };

    return this.testResults.chainDebugging;
  }

  /**
   * Test Flow Metrics Collection
   */
  async testFlowMetrics() {
    console.log('\n📊 Testing Flow Metrics Collection...');

    const metricsFlowId = `metrics-${Date.now()}`;
    const metricsResults = {};

    // Test metrics collection across services
    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        const startTime = performance.now();

        const response = await axios.get(`${config.baseUrl}/health`, {
          headers: {
            'X-Flow-ID': metricsFlowId,
            'X-Metrics-Collection': 'true',
            'X-Service-Name': serviceName,
            'X-Request-Type': 'metrics-test'
          },
          timeout: 5000
        });

        const responseTime = performance.now() - startTime;

        metricsResults[serviceName] = {
          status: 'success',
          responseTime: Math.round(responseTime),
          metricsHeaders: this.extractMetricsHeaders(response.headers),
          metricsInResponse: this.extractMetricsFromResponse(response.data),
          timestamp: new Date().toISOString()
        };

        console.log(`✅ ${serviceName}: Metrics collected - ${Math.round(responseTime)}ms`);

      } catch (error) {
        metricsResults[serviceName] = {
          status: 'error',
          error: error.message,
          timestamp: new Date().toISOString()
        };

        console.log(`❌ ${serviceName}: Metrics collection failed - ${error.message}`);
      }
    }

    this.testResults.flowMetrics = metricsResults;
    return metricsResults;
  }

  /**
   * Test Cross-Service Flow Tracking
   */
  async testCrossServiceTracking() {
    console.log('\n🌐 Testing Cross-Service Flow Tracking...');

    const crossFlowId = `cross-service-${Date.now()}`;

    // Simulate a complex cross-service workflow
    const workflow = [
      {
        name: 'Configuration Fetch',
        service: 'configuration-service',
        endpoint: '/health',
        dependencies: []
      },
      {
        name: 'AI Model Initialization',
        service: 'ai-orchestrator',
        endpoint: '/health',
        dependencies: ['Configuration Fetch']
      },
      {
        name: 'Trading Engine Ready',
        service: 'trading-engine',
        endpoint: '/health',
        dependencies: ['Configuration Fetch', 'AI Model Initialization']
      },
      {
        name: 'Database Connection',
        service: 'database-service',
        endpoint: '/health',
        dependencies: ['Configuration Fetch']
      }
    ];

    const workflowResults = [];
    const completedSteps = new Set();

    for (const step of workflow) {
      // Check if dependencies are met
      const dependenciesMet = step.dependencies.every(dep =>
        completedSteps.has(dep)
      );

      if (!dependenciesMet) {
        workflowResults.push({
          stepName: step.name,
          service: step.service,
          status: 'blocked',
          reason: 'dependencies not met',
          dependencies: step.dependencies,
          completedDependencies: Array.from(completedSteps)
        });
        continue;
      }

      const service = this.services[step.service];
      if (!service) {
        workflowResults.push({
          stepName: step.name,
          service: step.service,
          status: 'error',
          reason: 'service not found'
        });
        continue;
      }

      try {
        const startTime = performance.now();

        const response = await axios.get(`${service.baseUrl}${step.endpoint}`, {
          headers: {
            'X-Flow-ID': crossFlowId,
            'X-Workflow-Step': step.name,
            'X-Dependencies': step.dependencies.join(','),
            'X-Cross-Service-Tracking': 'true'
          },
          timeout: 5000
        });

        const responseTime = performance.now() - startTime;

        workflowResults.push({
          stepName: step.name,
          service: step.service,
          status: 'completed',
          responseTime: Math.round(responseTime),
          timestamp: new Date().toISOString(),
          dependencies: step.dependencies,
          trackingHeaders: this.extractFlowHeaders(response.headers)
        });

        completedSteps.add(step.name);
        console.log(`✅ ${step.name} (${step.service}): Completed - ${Math.round(responseTime)}ms`);

      } catch (error) {
        workflowResults.push({
          stepName: step.name,
          service: step.service,
          status: 'failed',
          error: error.message,
          dependencies: step.dependencies
        });

        console.log(`❌ ${step.name} (${step.service}): Failed - ${error.message}`);
      }
    }

    this.testResults.crossServiceTracking = {
      flowId: crossFlowId,
      workflow: workflowResults,
      completedSteps: Array.from(completedSteps),
      successRate: (completedSteps.size / workflow.length) * 100
    };

    return this.testResults.crossServiceTracking;
  }

  /**
   * Helper: Extract Flow-related Headers
   */
  extractFlowHeaders(headers) {
    const flowHeaders = {};

    Object.keys(headers).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('flow') ||
          lowerKey.includes('trace') ||
          lowerKey.includes('request') ||
          lowerKey.includes('step') ||
          lowerKey.includes('chain')) {
        flowHeaders[key] = headers[key];
      }
    });

    return flowHeaders;
  }

  /**
   * Helper: Check Error Tracking Implementation
   */
  checkErrorTracking(response) {
    if (!response) return false;

    const headers = response.headers || {};
    const data = response.data || {};

    // Check for flow tracking in error responses
    return !!(
      headers['x-flow-id'] ||
      headers['x-error-id'] ||
      headers['x-error-tracked'] ||
      data.flowId ||
      data.errorId ||
      data.tracked
    );
  }

  /**
   * Helper: Check Chain Tracking Implementation
   */
  checkChainTracking(headers) {
    return !!(
      headers['x-step-id'] ||
      headers['x-chain-id'] ||
      headers['x-previous-step'] ||
      headers['x-step-index']
    );
  }

  /**
   * Helper: Extract Debug Information
   */
  extractDebugInfo(headers) {
    return {
      responseTime: headers['x-response-time'],
      serviceVersion: headers['x-service-version'],
      nodeId: headers['x-node-id'],
      requestId: headers['x-request-id'],
      debugEnabled: headers['x-debug-enabled']
    };
  }

  /**
   * Helper: Extract Metrics Headers
   */
  extractMetricsHeaders(headers) {
    const metricsHeaders = {};

    Object.keys(headers).forEach(key => {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('metric') ||
          lowerKey.includes('time') ||
          lowerKey.includes('count') ||
          lowerKey.includes('performance')) {
        metricsHeaders[key] = headers[key];
      }
    });

    return metricsHeaders;
  }

  /**
   * Helper: Extract Metrics from Response Data
   */
  extractMetricsFromResponse(data) {
    if (!data || typeof data !== 'object') return {};

    const metrics = {};

    // Look for common metric fields
    ['responseTime', 'uptime', 'requestCount', 'errorCount', 'version', 'status'].forEach(field => {
      if (data[field] !== undefined) {
        metrics[field] = data[field];
      }
    });

    return metrics;
  }

  /**
   * Generate Flow Registry Report
   */
  generateFlowRegistryReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        flowIdPropagation: this.calculateTestSuccess(this.testResults.flowIdPropagation),
        errorTracking: this.calculateTestSuccess(this.testResults.errorTracking),
        chainDebugging: this.calculateTestSuccess(this.testResults.chainDebugging),
        flowMetrics: this.calculateTestSuccess(this.testResults.flowMetrics),
        crossServiceTracking: this.calculateTestSuccess(this.testResults.crossServiceTracking)
      },
      details: this.testResults,
      recommendations: []
    };

    // Generate recommendations
    this.generateFlowRegistryRecommendations(report);

    return report;
  }

  /**
   * Helper: Calculate Test Success Rate
   */
  calculateTestSuccess(testResults) {
    if (!testResults || typeof testResults !== 'object') {
      return { successRate: 0, total: 0, passed: 0 };
    }

    const results = Object.values(testResults);
    const total = results.length;

    let passed = 0;
    results.forEach(result => {
      if (result.status === 'success' ||
          result.status === 'completed' ||
          result.propagated === true ||
          result.successRate > 80) {
        passed++;
      }
    });

    return {
      successRate: total > 0 ? Math.round((passed / total) * 100) : 0,
      total,
      passed
    };
  }

  /**
   * Generate Flow Registry Recommendations
   */
  generateFlowRegistryRecommendations(report) {
    const recommendations = [];

    // Flow ID Propagation recommendations
    if (report.summary.flowIdPropagation.successRate < 100) {
      recommendations.push({
        category: 'Flow ID Propagation',
        priority: 'High',
        issue: 'Some services not propagating Flow IDs correctly',
        recommendation: 'Implement consistent Flow ID handling in all service middleware',
        impact: 'Cannot track requests across service boundaries'
      });
    }

    // Error Tracking recommendations
    if (report.summary.errorTracking.successRate < 100) {
      recommendations.push({
        category: 'Error Tracking',
        priority: 'High',
        issue: 'Error tracking not implemented consistently',
        recommendation: 'Add Flow ID to all error responses and error logging',
        impact: 'Difficult to debug cross-service errors'
      });
    }

    // Chain Debugging recommendations
    if (report.summary.chainDebugging.successRate < 100) {
      recommendations.push({
        category: 'Chain Debugging',
        priority: 'Medium',
        issue: 'Chain debugging capabilities missing',
        recommendation: 'Implement step tracking and chain visualization',
        impact: 'Cannot trace complex multi-service workflows'
      });
    }

    // Flow Metrics recommendations
    if (report.summary.flowMetrics.successRate < 100) {
      recommendations.push({
        category: 'Flow Metrics',
        priority: 'Medium',
        issue: 'Flow metrics collection incomplete',
        recommendation: 'Add comprehensive metrics collection to all services',
        impact: 'Limited visibility into system performance'
      });
    }

    // Cross-Service Tracking recommendations
    if (report.summary.crossServiceTracking.successRate < 100) {
      recommendations.push({
        category: 'Cross-Service Tracking',
        priority: 'High',
        issue: 'Cross-service flow tracking not working properly',
        recommendation: 'Implement distributed tracing with proper correlation IDs',
        impact: 'Cannot monitor end-to-end business processes'
      });
    }

    report.recommendations = recommendations;
  }

  /**
   * Run All Flow Registry Tests
   */
  async runAllFlowRegistryTests() {
    console.log('🔍 Starting Flow Registry Integration Tests...');
    console.log('='.repeat(60));

    try {
      await this.testFlowIdPropagation();
      await this.testErrorTracking();
      await this.testChainDebugging();
      await this.testFlowMetrics();
      await this.testCrossServiceTracking();

      const report = this.generateFlowRegistryReport();

      console.log('\n📊 Flow Registry Test Summary:');
      Object.entries(report.summary).forEach(([test, result]) => {
        console.log(`${test}: ${result.successRate}% (${result.passed}/${result.total})`);
      });

      if (report.recommendations.length > 0) {
        console.log('\n💡 Flow Registry Recommendations:');
        report.recommendations.forEach((rec, index) => {
          console.log(`${index + 1}. [${rec.priority}] ${rec.category}: ${rec.recommendation}`);
        });
      }

      return report;

    } catch (error) {
      console.error('❌ Flow Registry tests failed:', error.message);
      throw error;
    }
  }
}

module.exports = FlowRegistryTests;

// If run directly
if (require.main === module) {
  const tests = new FlowRegistryTests();
  tests.runAllFlowRegistryTests()
    .then(report => {
      console.log('\n✅ Flow Registry tests completed');
      const overallSuccess = Object.values(report.summary)
        .reduce((sum, result) => sum + result.successRate, 0) / Object.keys(report.summary).length;

      console.log(`📊 Overall Flow Registry Success Rate: ${Math.round(overallSuccess)}%`);
      process.exit(overallSuccess < 80 ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Flow Registry tests failed:', error);
      process.exit(1);
    });
}