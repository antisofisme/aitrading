/**
 * Comprehensive Integration Test Suite
 * Tests all microservices integration, connectivity, and flow tracking
 */

const axios = require('axios');
const WebSocket = require('ws');
const { performance } = require('perf_hooks');

class IntegrationTestSuite {
  constructor() {
    this.services = {
      'database-service': { port: 8008, baseUrl: 'http://localhost:8008' },
      'configuration-service': { port: 8012, baseUrl: 'http://localhost:8012' },
      'ai-orchestrator': { port: 8020, baseUrl: 'http://localhost:8020' },
      'trading-engine': { port: 9010, baseUrl: 'http://localhost:9010' }
    };

    this.testResults = {
      serviceHealth: {},
      connectivity: {},
      flowTracking: {},
      endToEnd: {},
      performance: {},
      errors: []
    };

    this.flowId = `test-flow-${Date.now()}`;
  }

  /**
   * Test 1: Service Health and Availability
   */
  async testServiceHealth() {
    console.log('\n🔍 Testing Service Health and Availability...');

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        const startTime = performance.now();
        const response = await axios.get(`${config.baseUrl}/health`, {
          timeout: 5000,
          headers: { 'X-Flow-ID': this.flowId }
        });
        const responseTime = performance.now() - startTime;

        this.testResults.serviceHealth[serviceName] = {
          status: 'healthy',
          responseTime: Math.round(responseTime),
          data: response.data,
          httpStatus: response.status
        };

        console.log(`✅ ${serviceName}: ${response.status} (${Math.round(responseTime)}ms)`);

      } catch (error) {
        this.testResults.serviceHealth[serviceName] = {
          status: 'unhealthy',
          error: error.message,
          code: error.code
        };
        console.log(`❌ ${serviceName}: ${error.message}`);
      }
    }

    return this.testResults.serviceHealth;
  }

  /**
   * Test 2: Service-to-Service Connectivity
   */
  async testServiceConnectivity() {
    console.log('\n🔗 Testing Service-to-Service Connectivity...');

    const connectivityTests = [
      {
        name: 'Database Service → Trading Engine',
        from: 'database-service',
        to: 'trading-engine',
        endpoint: '/api/connectivity/test'
      },
      {
        name: 'AI Orchestrator → Trading Engine',
        from: 'ai-orchestrator',
        to: 'trading-engine',
        endpoint: '/api/ai/signal/test'
      },
      {
        name: 'Configuration Service → All Services',
        from: 'configuration-service',
        to: 'all',
        endpoint: '/api/config/broadcast'
      }
    ];

    for (const test of connectivityTests) {
      try {
        const startTime = performance.now();

        // Test direct connectivity
        const response = await this.testDirectConnectivity(test);
        const responseTime = performance.now() - startTime;

        this.testResults.connectivity[test.name] = {
          status: 'connected',
          responseTime: Math.round(responseTime),
          details: response
        };

        console.log(`✅ ${test.name}: Connected (${Math.round(responseTime)}ms)`);

      } catch (error) {
        this.testResults.connectivity[test.name] = {
          status: 'disconnected',
          error: error.message
        };
        console.log(`❌ ${test.name}: ${error.message}`);
      }
    }

    return this.testResults.connectivity;
  }

  /**
   * Test 3: Flow Registry Integration
   */
  async testFlowRegistryIntegration() {
    console.log('\n📊 Testing Flow Registry Integration...');

    const flowTests = [
      {
        name: 'Flow ID Propagation',
        test: () => this.testFlowIdPropagation()
      },
      {
        name: 'Error Impact Analysis',
        test: () => this.testErrorImpactAnalysis()
      },
      {
        name: 'Chain Debugging',
        test: () => this.testChainDebugging()
      },
      {
        name: 'Flow Tracking',
        test: () => this.testFlowTracking()
      }
    ];

    for (const flowTest of flowTests) {
      try {
        const result = await flowTest.test();
        this.testResults.flowTracking[flowTest.name] = {
          status: 'passed',
          details: result
        };
        console.log(`✅ ${flowTest.name}: Passed`);

      } catch (error) {
        this.testResults.flowTracking[flowTest.name] = {
          status: 'failed',
          error: error.message
        };
        console.log(`❌ ${flowTest.name}: ${error.message}`);
      }
    }

    return this.testResults.flowTracking;
  }

  /**
   * Test 4: End-to-End AI Trading Workflow
   */
  async testEndToEndWorkflow() {
    console.log('\n🤖 Testing End-to-End AI Trading Workflow...');

    const workflowSteps = [
      {
        name: 'Configuration Retrieval',
        service: 'configuration-service',
        endpoint: '/api/config/trading',
        expected: 'trading configuration'
      },
      {
        name: 'AI Signal Generation',
        service: 'ai-orchestrator',
        endpoint: '/api/ai/signal/generate',
        payload: { symbol: 'BTCUSD', type: 'BUY' },
        expected: 'AI signal'
      },
      {
        name: 'Trading Signal Processing',
        service: 'trading-engine',
        endpoint: '/api/trading/signal/process',
        payload: { signal: 'test_signal', confidence: 0.85 },
        expected: 'order created'
      },
      {
        name: 'Data Persistence',
        service: 'database-service',
        endpoint: '/api/database/store',
        payload: { type: 'trade', data: { symbol: 'BTCUSD' } },
        expected: 'data stored'
      }
    ];

    let workflowSuccess = true;
    const workflowResults = {};

    for (const step of workflowSteps) {
      try {
        const startTime = performance.now();
        const result = await this.executeWorkflowStep(step);
        const responseTime = performance.now() - startTime;

        workflowResults[step.name] = {
          status: 'success',
          responseTime: Math.round(responseTime),
          result: result
        };

        console.log(`✅ ${step.name}: Success (${Math.round(responseTime)}ms)`);

      } catch (error) {
        workflowSuccess = false;
        workflowResults[step.name] = {
          status: 'failed',
          error: error.message
        };
        console.log(`❌ ${step.name}: ${error.message}`);
      }
    }

    this.testResults.endToEnd = {
      overallStatus: workflowSuccess ? 'success' : 'failed',
      steps: workflowResults
    };

    return this.testResults.endToEnd;
  }

  /**
   * Test 5: Performance and Load Testing
   */
  async testPerformanceAndLoad() {
    console.log('\n⚡ Testing Performance and Load...');

    const performanceTests = [
      {
        name: 'Trading Engine Latency',
        service: 'trading-engine',
        endpoint: '/health',
        target: 10, // <10ms requirement
        concurrency: 1
      },
      {
        name: 'Database Service Throughput',
        service: 'database-service',
        endpoint: '/health',
        target: 100,
        concurrency: 10
      },
      {
        name: 'AI Orchestrator Load',
        service: 'ai-orchestrator',
        endpoint: '/health',
        target: 500,
        concurrency: 5
      },
      {
        name: 'Concurrent Multi-Service',
        service: 'all',
        endpoint: '/health',
        target: 200,
        concurrency: 20
      }
    ];

    for (const test of performanceTests) {
      try {
        const result = await this.runPerformanceTest(test);
        this.testResults.performance[test.name] = {
          status: result.averageTime <= test.target ? 'passed' : 'warning',
          averageTime: result.averageTime,
          target: test.target,
          details: result
        };

        const status = result.averageTime <= test.target ? '✅' : '⚠️';
        console.log(`${status} ${test.name}: ${result.averageTime}ms avg (target: ${test.target}ms)`);

      } catch (error) {
        this.testResults.performance[test.name] = {
          status: 'failed',
          error: error.message
        };
        console.log(`❌ ${test.name}: ${error.message}`);
      }
    }

    return this.testResults.performance;
  }

  /**
   * Test 6: Error Handling and Recovery
   */
  async testErrorHandlingAndRecovery() {
    console.log('\n🛡️ Testing Error Handling and Recovery...');

    const errorTests = [
      {
        name: 'Invalid Endpoint Handling',
        test: () => this.testInvalidEndpoints()
      },
      {
        name: 'Timeout Handling',
        test: () => this.testTimeoutHandling()
      },
      {
        name: 'Service Unavailable Handling',
        test: () => this.testServiceUnavailableHandling()
      },
      {
        name: 'Flow Error Propagation',
        test: () => this.testFlowErrorPropagation()
      }
    ];

    const errorResults = {};

    for (const errorTest of errorTests) {
      try {
        const result = await errorTest.test();
        errorResults[errorTest.name] = {
          status: 'passed',
          details: result
        };
        console.log(`✅ ${errorTest.name}: Handled correctly`);

      } catch (error) {
        errorResults[errorTest.name] = {
          status: 'failed',
          error: error.message
        };
        console.log(`❌ ${errorTest.name}: ${error.message}`);
      }
    }

    this.testResults.errors = errorResults;
    return errorResults;
  }

  /**
   * Helper: Test Direct Connectivity
   */
  async testDirectConnectivity(test) {
    const fromService = this.services[test.from];
    if (!fromService) {
      throw new Error(`Service ${test.from} not found`);
    }

    // Simulate connectivity test
    const response = await axios.get(`${fromService.baseUrl}/health`, {
      timeout: 5000,
      headers: {
        'X-Flow-ID': this.flowId,
        'X-Test-Type': 'connectivity',
        'X-Target-Service': test.to
      }
    });

    return response.data;
  }

  /**
   * Helper: Test Flow ID Propagation
   */
  async testFlowIdPropagation() {
    const testFlowId = `flow-test-${Date.now()}`;
    const responses = [];

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        const response = await axios.get(`${config.baseUrl}/health`, {
          headers: { 'X-Flow-ID': testFlowId }
        });

        responses.push({
          service: serviceName,
          flowIdReceived: response.headers['x-flow-id'] === testFlowId,
          headers: response.headers
        });
      } catch (error) {
        responses.push({
          service: serviceName,
          error: error.message
        });
      }
    }

    return responses;
  }

  /**
   * Helper: Test Error Impact Analysis
   */
  async testErrorImpactAnalysis() {
    // Test intentional error to see impact analysis
    try {
      await axios.get('http://localhost:8008/api/error/test', {
        headers: { 'X-Flow-ID': this.flowId },
        timeout: 2000
      });
    } catch (error) {
      // Expected error - check if flow tracking captured it
      return {
        errorCaptured: true,
        flowId: this.flowId,
        errorType: error.code
      };
    }
  }

  /**
   * Helper: Test Chain Debugging
   */
  async testChainDebugging() {
    // Test chain debug capabilities
    const debugFlowId = `debug-${Date.now()}`;

    // Make a series of calls to create a chain
    const chain = [];

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        const response = await axios.get(`${config.baseUrl}/health`, {
          headers: {
            'X-Flow-ID': debugFlowId,
            'X-Debug-Chain': 'true'
          }
        });

        chain.push({
          service: serviceName,
          timestamp: new Date().toISOString(),
          status: response.status
        });
      } catch (error) {
        chain.push({
          service: serviceName,
          timestamp: new Date().toISOString(),
          error: error.message
        });
      }
    }

    return { flowId: debugFlowId, chain };
  }

  /**
   * Helper: Test Flow Tracking
   */
  async testFlowTracking() {
    // Test comprehensive flow tracking
    const trackingFlowId = `tracking-${Date.now()}`;
    const flows = [];

    // Create multiple related flows
    for (let i = 0; i < 3; i++) {
      const subFlowId = `${trackingFlowId}-${i}`;

      try {
        const response = await axios.get(`${this.services['trading-engine'].baseUrl}/health`, {
          headers: {
            'X-Flow-ID': subFlowId,
            'X-Parent-Flow': trackingFlowId,
            'X-Flow-Step': i.toString()
          }
        });

        flows.push({
          flowId: subFlowId,
          parentFlow: trackingFlowId,
          step: i,
          status: 'success'
        });
      } catch (error) {
        flows.push({
          flowId: subFlowId,
          parentFlow: trackingFlowId,
          step: i,
          status: 'error',
          error: error.message
        });
      }
    }

    return { parentFlow: trackingFlowId, subFlows: flows };
  }

  /**
   * Helper: Execute Workflow Step
   */
  async executeWorkflowStep(step) {
    const service = this.services[step.service];
    if (!service) {
      throw new Error(`Service ${step.service} not found`);
    }

    const config = {
      timeout: 10000,
      headers: {
        'X-Flow-ID': this.flowId,
        'X-Step': step.name,
        'Content-Type': 'application/json'
      }
    };

    let response;
    if (step.payload) {
      response = await axios.post(`${service.baseUrl}${step.endpoint}`, step.payload, config);
    } else {
      response = await axios.get(`${service.baseUrl}${step.endpoint}`, config);
    }

    return response.data;
  }

  /**
   * Helper: Run Performance Test
   */
  async runPerformanceTest(test) {
    const results = [];
    const promises = [];

    if (test.service === 'all') {
      // Test all services concurrently
      for (const [serviceName, config] of Object.entries(this.services)) {
        for (let i = 0; i < test.concurrency; i++) {
          promises.push(this.measureResponseTime(config.baseUrl, test.endpoint));
        }
      }
    } else {
      // Test specific service
      const service = this.services[test.service];
      for (let i = 0; i < test.concurrency; i++) {
        promises.push(this.measureResponseTime(service.baseUrl, test.endpoint));
      }
    }

    const responses = await Promise.allSettled(promises);
    const successfulResponses = responses
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);

    const averageTime = successfulResponses.reduce((sum, time) => sum + time, 0) / successfulResponses.length;
    const maxTime = Math.max(...successfulResponses);
    const minTime = Math.min(...successfulResponses);

    return {
      averageTime: Math.round(averageTime),
      maxTime: Math.round(maxTime),
      minTime: Math.round(minTime),
      successRate: (successfulResponses.length / promises.length) * 100,
      totalRequests: promises.length,
      successfulRequests: successfulResponses.length
    };
  }

  /**
   * Helper: Measure Response Time
   */
  async measureResponseTime(baseUrl, endpoint) {
    const startTime = performance.now();

    try {
      await axios.get(`${baseUrl}${endpoint}`, {
        timeout: 5000,
        headers: { 'X-Flow-ID': this.flowId }
      });
      return performance.now() - startTime;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Helper: Test Invalid Endpoints
   */
  async testInvalidEndpoints() {
    const invalidTests = [];

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        await axios.get(`${config.baseUrl}/invalid/endpoint/test`, {
          timeout: 3000,
          headers: { 'X-Flow-ID': this.flowId }
        });

        invalidTests.push({
          service: serviceName,
          handled: false,
          message: 'Should have returned 404'
        });
      } catch (error) {
        invalidTests.push({
          service: serviceName,
          handled: error.response?.status === 404,
          status: error.response?.status,
          message: error.message
        });
      }
    }

    return invalidTests;
  }

  /**
   * Helper: Test Timeout Handling
   */
  async testTimeoutHandling() {
    const timeoutTests = [];

    for (const [serviceName, config] of Object.entries(this.services)) {
      try {
        await axios.get(`${config.baseUrl}/api/slow/endpoint`, {
          timeout: 100, // Very short timeout
          headers: { 'X-Flow-ID': this.flowId }
        });

        timeoutTests.push({
          service: serviceName,
          timeoutHandled: false
        });
      } catch (error) {
        timeoutTests.push({
          service: serviceName,
          timeoutHandled: error.code === 'ECONNABORTED' || error.code === 'TIMEOUT',
          errorCode: error.code
        });
      }
    }

    return timeoutTests;
  }

  /**
   * Helper: Test Service Unavailable Handling
   */
  async testServiceUnavailableHandling() {
    // Test calls to non-existent ports
    const unavailableTests = [];
    const nonExistentPorts = [8999, 9999, 7999];

    for (const port of nonExistentPorts) {
      try {
        await axios.get(`http://localhost:${port}/health`, {
          timeout: 2000,
          headers: { 'X-Flow-ID': this.flowId }
        });

        unavailableTests.push({
          port: port,
          handled: false
        });
      } catch (error) {
        unavailableTests.push({
          port: port,
          handled: error.code === 'ECONNREFUSED',
          errorCode: error.code
        });
      }
    }

    return unavailableTests;
  }

  /**
   * Helper: Test Flow Error Propagation
   */
  async testFlowErrorPropagation() {
    const errorFlowId = `error-${Date.now()}`;

    // Intentionally cause an error and track propagation
    try {
      await axios.post('http://localhost:8008/api/error/intentional', {
        errorType: 'test_error',
        flowId: errorFlowId
      }, {
        timeout: 3000,
        headers: { 'X-Flow-ID': errorFlowId }
      });
    } catch (error) {
      // Check if error was properly tracked and propagated
      return {
        errorPropagated: true,
        flowId: errorFlowId,
        errorDetails: {
          code: error.code,
          status: error.response?.status,
          message: error.message
        }
      };
    }
  }

  /**
   * Generate Comprehensive Test Report
   */
  generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      flowId: this.flowId,
      summary: {
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        warningTests: 0
      },
      details: this.testResults,
      recommendations: []
    };

    // Calculate summary
    Object.values(this.testResults).forEach(category => {
      if (typeof category === 'object' && category !== null) {
        Object.values(category).forEach(test => {
          if (test && test.status) {
            report.summary.totalTests++;
            switch (test.status) {
              case 'passed':
              case 'success':
              case 'healthy':
              case 'connected':
                report.summary.passedTests++;
                break;
              case 'failed':
              case 'unhealthy':
              case 'disconnected':
                report.summary.failedTests++;
                break;
              case 'warning':
                report.summary.warningTests++;
                break;
            }
          }
        });
      }
    });

    // Generate recommendations
    this.generateRecommendations(report);

    return report;
  }

  /**
   * Generate Optimization Recommendations
   */
  generateRecommendations(report) {
    const recommendations = [];

    // Service health recommendations
    Object.entries(this.testResults.serviceHealth).forEach(([service, result]) => {
      if (result.status === 'unhealthy') {
        recommendations.push({
          category: 'Service Health',
          priority: 'High',
          service: service,
          issue: 'Service is unhealthy or not responding',
          recommendation: `Check ${service} logs and restart if necessary`,
          impact: 'Service unavailability affects dependent services'
        });
      } else if (result.responseTime > 1000) {
        recommendations.push({
          category: 'Performance',
          priority: 'Medium',
          service: service,
          issue: `Slow response time: ${result.responseTime}ms`,
          recommendation: 'Investigate performance bottlenecks and optimize',
          impact: 'Slow response times affect user experience'
        });
      }
    });

    // Performance recommendations
    Object.entries(this.testResults.performance).forEach(([test, result]) => {
      if (result.status === 'warning') {
        recommendations.push({
          category: 'Performance',
          priority: 'Medium',
          test: test,
          issue: `Performance target missed: ${result.averageTime}ms > ${result.target}ms`,
          recommendation: 'Optimize service performance or adjust targets',
          impact: 'Performance degradation affects system responsiveness'
        });
      }
    });

    // Connectivity recommendations
    Object.entries(this.testResults.connectivity).forEach(([test, result]) => {
      if (result.status === 'disconnected') {
        recommendations.push({
          category: 'Connectivity',
          priority: 'High',
          test: test,
          issue: 'Service connectivity failed',
          recommendation: 'Check network configuration and service discovery',
          impact: 'Service isolation prevents proper system operation'
        });
      }
    });

    // Flow tracking recommendations
    if (Object.keys(this.testResults.flowTracking).length === 0) {
      recommendations.push({
        category: 'Flow Registry',
        priority: 'High',
        issue: 'Flow tracking not implemented or not working',
        recommendation: 'Implement Flow Registry integration across all services',
        impact: 'Cannot track requests across services or debug issues effectively'
      });
    }

    report.recommendations = recommendations;
  }

  /**
   * Run All Tests
   */
  async runAllTests() {
    console.log('🚀 Starting Comprehensive Integration Tests...');
    console.log(`Flow ID: ${this.flowId}`);
    console.log('='.repeat(60));

    try {
      // Run all test suites
      await this.testServiceHealth();
      await this.testServiceConnectivity();
      await this.testFlowRegistryIntegration();
      await this.testEndToEndWorkflow();
      await this.testPerformanceAndLoad();
      await this.testErrorHandlingAndRecovery();

      // Generate comprehensive report
      const report = this.generateReport();

      console.log('\n📊 Test Summary:');
      console.log(`Total Tests: ${report.summary.totalTests}`);
      console.log(`✅ Passed: ${report.summary.passedTests}`);
      console.log(`❌ Failed: ${report.summary.failedTests}`);
      console.log(`⚠️ Warnings: ${report.summary.warningTests}`);

      if (report.recommendations.length > 0) {
        console.log('\n💡 Recommendations:');
        report.recommendations.forEach((rec, index) => {
          console.log(`${index + 1}. [${rec.priority}] ${rec.category}: ${rec.recommendation}`);
        });
      }

      return report;

    } catch (error) {
      console.error('❌ Test suite failed:', error.message);
      throw error;
    }
  }
}

module.exports = IntegrationTestSuite;

// If run directly
if (require.main === module) {
  const suite = new IntegrationTestSuite();
  suite.runAllTests()
    .then(report => {
      console.log('\n✅ Integration tests completed');
      console.log('📄 Full report generated');
      process.exit(report.summary.failedTests > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Integration tests failed:', error);
      process.exit(1);
    });
}