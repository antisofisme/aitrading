/**
 * Performance Integration Tests
 * Tests system performance under various load conditions
 */

const axios = require('axios');
const { performance } = require('perf_hooks');
const cluster = require('cluster');
const os = require('os');

class PerformanceIntegrationTests {
  constructor() {
    this.services = {
      'database-service': { port: 8008, baseUrl: 'http://localhost:8008', target: 100 },
      'configuration-service': { port: 8012, baseUrl: 'http://localhost:8012', target: 50 },
      'ai-orchestrator': { port: 8020, baseUrl: 'http://localhost:8020', target: 500 },
      'trading-engine': { port: 9010, baseUrl: 'http://localhost:9010', target: 10 } // <10ms requirement
    };

    this.testResults = {
      latency: {},
      throughput: {},
      concurrency: {},
      endurance: {},
      memory: {},
      cpu: {}
    };

    this.baselineMetrics = {};
  }

  /**
   * Test 1: Service Latency Testing
   */
  async testServiceLatency() {
    console.log('\n⚡ Testing Service Latency...');

    for (const [serviceName, config] of Object.entries(this.services)) {
      console.log(`\nTesting ${serviceName} latency...`);

      try {
        const latencyResults = await this.measureLatency(config, 100); // 100 requests

        this.testResults.latency[serviceName] = {
          average: Math.round(latencyResults.average),
          median: Math.round(latencyResults.median),
          p95: Math.round(latencyResults.p95),
          p99: Math.round(latencyResults.p99),
          min: Math.round(latencyResults.min),
          max: Math.round(latencyResults.max),
          target: config.target,
          passed: latencyResults.average <= config.target,
          samples: latencyResults.samples.length,
          successRate: latencyResults.successRate
        };

        const passed = latencyResults.average <= config.target;
        const icon = passed ? '✅' : '❌';

        console.log(`${icon} ${serviceName}:`);
        console.log(`   Average: ${Math.round(latencyResults.average)}ms (target: ${config.target}ms)`);
        console.log(`   Median: ${Math.round(latencyResults.median)}ms`);
        console.log(`   P95: ${Math.round(latencyResults.p95)}ms`);
        console.log(`   P99: ${Math.round(latencyResults.p99)}ms`);
        console.log(`   Success Rate: ${latencyResults.successRate}%`);

      } catch (error) {
        this.testResults.latency[serviceName] = {
          error: error.message,
          passed: false
        };
        console.log(`❌ ${serviceName}: ${error.message}`);
      }
    }

    return this.testResults.latency;
  }

  /**
   * Test 2: Throughput Testing
   */
  async testThroughput() {
    console.log('\n🚀 Testing Service Throughput...');

    const throughputTests = [
      { name: 'Low Load', concurrency: 10, duration: 30000 },
      { name: 'Medium Load', concurrency: 50, duration: 30000 },
      { name: 'High Load', concurrency: 100, duration: 30000 }
    ];

    for (const test of throughputTests) {
      console.log(`\nTesting ${test.name} (${test.concurrency} concurrent, ${test.duration / 1000}s)...`);

      const testResults = {};

      for (const [serviceName, config] of Object.entries(this.services)) {
        try {
          const result = await this.measureThroughput(config, test.concurrency, test.duration);

          testResults[serviceName] = {
            requestsPerSecond: Math.round(result.requestsPerSecond),
            totalRequests: result.totalRequests,
            successfulRequests: result.successfulRequests,
            failedRequests: result.failedRequests,
            averageLatency: Math.round(result.averageLatency),
            successRate: Math.round(result.successRate),
            concurrency: test.concurrency
          };

          console.log(`✅ ${serviceName}: ${Math.round(result.requestsPerSecond)} req/s (${Math.round(result.successRate)}% success)`);

        } catch (error) {
          testResults[serviceName] = {
            error: error.message,
            concurrency: test.concurrency
          };
          console.log(`❌ ${serviceName}: ${error.message}`);
        }
      }

      this.testResults.throughput[test.name] = testResults;
    }

    return this.testResults.throughput;
  }

  /**
   * Test 3: Concurrency Testing
   */
  async testConcurrency() {
    console.log('\n🔄 Testing Concurrency Handling...');

    const concurrencyLevels = [1, 10, 25, 50, 100, 200];

    for (const [serviceName, config] of Object.entries(this.services)) {
      console.log(`\nTesting ${serviceName} concurrency...`);

      const concurrencyResults = [];

      for (const level of concurrencyLevels) {
        try {
          const result = await this.testConcurrencyLevel(config, level);

          concurrencyResults.push({
            concurrency: level,
            averageLatency: Math.round(result.averageLatency),
            successRate: Math.round(result.successRate),
            errorsPerSecond: Math.round(result.errorsPerSecond),
            passed: result.successRate >= 95 // 95% success rate threshold
          });

          const passed = result.successRate >= 95;
          const icon = passed ? '✅' : '❌';
          console.log(`${icon} ${level} concurrent: ${Math.round(result.averageLatency)}ms avg, ${Math.round(result.successRate)}% success`);

        } catch (error) {
          concurrencyResults.push({
            concurrency: level,
            error: error.message,
            passed: false
          });
          console.log(`❌ ${level} concurrent: ${error.message}`);
        }
      }

      this.testResults.concurrency[serviceName] = concurrencyResults;
    }

    return this.testResults.concurrency;
  }

  /**
   * Test 4: Endurance Testing
   */
  async testEndurance() {
    console.log('\n⏰ Testing Service Endurance (5 minutes sustained load)...');

    const enduranceConfig = {
      duration: 5 * 60 * 1000, // 5 minutes
      concurrency: 25,
      samplingInterval: 10000 // Sample every 10 seconds
    };

    for (const [serviceName, config] of Object.entries(this.services)) {
      console.log(`\nTesting ${serviceName} endurance...`);

      try {
        const result = await this.measureEndurance(config, enduranceConfig);

        this.testResults.endurance[serviceName] = {
          duration: enduranceConfig.duration,
          totalRequests: result.totalRequests,
          averageLatency: Math.round(result.averageLatency),
          successRate: Math.round(result.successRate),
          degradation: result.degradation,
          samples: result.samples,
          memoryLeak: result.memoryLeak,
          passed: result.successRate >= 95 && !result.memoryLeak
        };

        const passed = result.successRate >= 95 && !result.memoryLeak;
        const icon = passed ? '✅' : '❌';
        console.log(`${icon} ${serviceName}: ${Math.round(result.successRate)}% success, ${result.degradation}% degradation`);

        if (result.memoryLeak) {
          console.log(`⚠️ Potential memory leak detected in ${serviceName}`);
        }

      } catch (error) {
        this.testResults.endurance[serviceName] = {
          error: error.message,
          passed: false
        };
        console.log(`❌ ${serviceName}: ${error.message}`);
      }
    }

    return this.testResults.endurance;
  }

  /**
   * Test 5: Memory Performance Testing
   */
  async testMemoryPerformance() {
    console.log('\n💾 Testing Memory Performance...');

    for (const [serviceName, config] of Object.entries(this.services)) {
      console.log(`\nTesting ${serviceName} memory usage...`);

      try {
        const result = await this.measureMemoryUsage(config);

        this.testResults.memory[serviceName] = {
          initialMemory: result.initialMemory,
          peakMemory: result.peakMemory,
          finalMemory: result.finalMemory,
          memoryGrowth: result.memoryGrowth,
          gcEfficiency: result.gcEfficiency,
          memoryLeakSuspected: result.memoryLeakSuspected,
          passed: !result.memoryLeakSuspected && result.memoryGrowth < 50 // <50MB growth
        };

        const passed = !result.memoryLeakSuspected && result.memoryGrowth < 50;
        const icon = passed ? '✅' : '❌';
        console.log(`${icon} ${serviceName}: ${result.memoryGrowth}MB growth, GC efficiency: ${result.gcEfficiency}%`);

      } catch (error) {
        this.testResults.memory[serviceName] = {
          error: error.message,
          passed: false
        };
        console.log(`❌ ${serviceName}: ${error.message}`);
      }
    }

    return this.testResults.memory;
  }

  /**
   * Test 6: End-to-End Performance
   */
  async testEndToEndPerformance() {
    console.log('\n🔗 Testing End-to-End Performance...');

    const e2eFlowId = `e2e-perf-${Date.now()}`;

    const workflows = [
      {
        name: 'Trading Workflow',
        steps: [
          { service: 'configuration-service', endpoint: '/health', target: 50 },
          { service: 'ai-orchestrator', endpoint: '/health', target: 500 },
          { service: 'trading-engine', endpoint: '/health', target: 10 },
          { service: 'database-service', endpoint: '/health', target: 100 }
        ]
      }
    ];

    const e2eResults = {};

    for (const workflow of workflows) {
      console.log(`\nTesting ${workflow.name}...`);

      try {
        const result = await this.measureEndToEndWorkflow(workflow, e2eFlowId);

        e2eResults[workflow.name] = {
          totalTime: Math.round(result.totalTime),
          steps: result.steps,
          successRate: Math.round(result.successRate),
          bottleneck: result.bottleneck,
          passed: result.successRate >= 95 && result.totalTime <= 1000 // <1s total
        };

        const passed = result.successRate >= 95 && result.totalTime <= 1000;
        const icon = passed ? '✅' : '❌';
        console.log(`${icon} ${workflow.name}: ${Math.round(result.totalTime)}ms total, bottleneck: ${result.bottleneck}`);

      } catch (error) {
        e2eResults[workflow.name] = {
          error: error.message,
          passed: false
        };
        console.log(`❌ ${workflow.name}: ${error.message}`);
      }
    }

    this.testResults.endToEnd = e2eResults;
    return e2eResults;
  }

  /**
   * Helper: Measure Service Latency
   */
  async measureLatency(config, samples = 100) {
    const latencies = [];
    let successCount = 0;

    for (let i = 0; i < samples; i++) {
      try {
        const startTime = performance.now();

        await axios.get(`${config.baseUrl}/health`, {
          timeout: 5000,
          headers: { 'X-Performance-Test': 'latency' }
        });

        const latency = performance.now() - startTime;
        latencies.push(latency);
        successCount++;

      } catch (error) {
        // Count as failed request
      }
    }

    if (latencies.length === 0) {
      throw new Error('All requests failed');
    }

    latencies.sort((a, b) => a - b);

    return {
      samples: latencies,
      average: latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length,
      median: latencies[Math.floor(latencies.length / 2)],
      p95: latencies[Math.floor(latencies.length * 0.95)],
      p99: latencies[Math.floor(latencies.length * 0.99)],
      min: Math.min(...latencies),
      max: Math.max(...latencies),
      successRate: (successCount / samples) * 100
    };
  }

  /**
   * Helper: Measure Throughput
   */
  async measureThroughput(config, concurrency, duration) {
    const startTime = Date.now();
    const endTime = startTime + duration;
    let totalRequests = 0;
    let successfulRequests = 0;
    let totalLatency = 0;

    const workers = [];

    // Create worker promises
    for (let i = 0; i < concurrency; i++) {
      workers.push(this.throughputWorker(config, endTime));
    }

    // Wait for all workers to complete
    const results = await Promise.all(workers);

    // Aggregate results
    results.forEach(result => {
      totalRequests += result.requests;
      successfulRequests += result.successful;
      totalLatency += result.totalLatency;
    });

    const actualDuration = (Date.now() - startTime) / 1000; // seconds

    return {
      requestsPerSecond: totalRequests / actualDuration,
      totalRequests,
      successfulRequests,
      failedRequests: totalRequests - successfulRequests,
      averageLatency: totalLatency / successfulRequests,
      successRate: (successfulRequests / totalRequests) * 100
    };
  }

  /**
   * Helper: Throughput Worker
   */
  async throughputWorker(config, endTime) {
    let requests = 0;
    let successful = 0;
    let totalLatency = 0;

    while (Date.now() < endTime) {
      try {
        const startTime = performance.now();

        await axios.get(`${config.baseUrl}/health`, {
          timeout: 5000,
          headers: { 'X-Performance-Test': 'throughput' }
        });

        const latency = performance.now() - startTime;
        totalLatency += latency;
        successful++;

      } catch (error) {
        // Request failed
      }

      requests++;
    }

    return { requests, successful, totalLatency };
  }

  /**
   * Helper: Test Concurrency Level
   */
  async testConcurrencyLevel(config, concurrency, duration = 10000) {
    const promises = [];
    const startTime = performance.now();

    // Launch concurrent requests
    for (let i = 0; i < concurrency; i++) {
      promises.push(this.concurrentRequest(config, startTime));
    }

    const results = await Promise.allSettled(promises);

    const successful = results.filter(r => r.status === 'fulfilled').length;
    const failed = results.filter(r => r.status === 'rejected').length;

    const latencies = results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);

    const averageLatency = latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;
    const actualDuration = (performance.now() - startTime) / 1000;

    return {
      averageLatency: averageLatency || 0,
      successRate: (successful / concurrency) * 100,
      errorsPerSecond: failed / actualDuration
    };
  }

  /**
   * Helper: Concurrent Request
   */
  async concurrentRequest(config, startTime) {
    const requestStart = performance.now();

    await axios.get(`${config.baseUrl}/health`, {
      timeout: 5000,
      headers: {
        'X-Performance-Test': 'concurrency',
        'X-Start-Time': startTime.toString()
      }
    });

    return performance.now() - requestStart;
  }

  /**
   * Helper: Measure Endurance
   */
  async measureEndurance(config, enduranceConfig) {
    const startTime = Date.now();
    const endTime = startTime + enduranceConfig.duration;
    const samples = [];
    let totalRequests = 0;
    let successfulRequests = 0;
    let totalLatency = 0;

    console.log(`   Running for ${enduranceConfig.duration / 1000} seconds...`);

    while (Date.now() < endTime) {
      const sampleStart = Date.now();
      const sampleResults = await this.enduranceSample(config, enduranceConfig.concurrency, enduranceConfig.samplingInterval);

      samples.push({
        timestamp: Date.now(),
        averageLatency: sampleResults.averageLatency,
        successRate: sampleResults.successRate,
        requestsPerSecond: sampleResults.requestsPerSecond
      });

      totalRequests += sampleResults.totalRequests;
      successfulRequests += sampleResults.successfulRequests;
      totalLatency += sampleResults.totalLatency;

      // Progress indicator
      const elapsed = Date.now() - startTime;
      const progress = Math.round((elapsed / enduranceConfig.duration) * 100);
      process.stdout.write(`\r   Progress: ${progress}%`);
    }

    console.log(); // New line after progress

    // Calculate degradation
    const firstHalf = samples.slice(0, Math.floor(samples.length / 2));
    const secondHalf = samples.slice(Math.floor(samples.length / 2));

    const firstHalfAvg = firstHalf.reduce((sum, s) => sum + s.averageLatency, 0) / firstHalf.length;
    const secondHalfAvg = secondHalf.reduce((sum, s) => sum + s.averageLatency, 0) / secondHalf.length;

    const degradation = ((secondHalfAvg - firstHalfAvg) / firstHalfAvg) * 100;

    // Check for memory leak indicators
    const latencyTrend = this.calculateTrend(samples.map(s => s.averageLatency));
    const memoryLeak = latencyTrend > 0.1; // Increasing latency trend

    return {
      totalRequests,
      successfulRequests,
      averageLatency: totalLatency / successfulRequests,
      successRate: (successfulRequests / totalRequests) * 100,
      degradation: Math.max(0, degradation),
      samples,
      memoryLeak
    };
  }

  /**
   * Helper: Endurance Sample
   */
  async enduranceSample(config, concurrency, duration) {
    const sampleStart = performance.now();
    const promises = [];

    for (let i = 0; i < concurrency; i++) {
      promises.push(this.enduranceRequest(config));
    }

    const results = await Promise.allSettled(promises);
    const sampleDuration = (performance.now() - sampleStart) / 1000;

    const successful = results.filter(r => r.status === 'fulfilled').length;
    const latencies = results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value);

    return {
      totalRequests: results.length,
      successfulRequests: successful,
      totalLatency: latencies.reduce((sum, lat) => sum + lat, 0),
      averageLatency: latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length,
      successRate: (successful / results.length) * 100,
      requestsPerSecond: results.length / sampleDuration
    };
  }

  /**
   * Helper: Endurance Request
   */
  async enduranceRequest(config) {
    const startTime = performance.now();

    await axios.get(`${config.baseUrl}/health`, {
      timeout: 10000,
      headers: { 'X-Performance-Test': 'endurance' }
    });

    return performance.now() - startTime;
  }

  /**
   * Helper: Measure Memory Usage
   */
  async measureMemoryUsage(config) {
    // This is a simplified version - in a real scenario, you'd need
    // to instrument the actual services to report memory usage
    const memoryTests = [];

    // Baseline measurement
    let initialMemory = await this.getServiceMemoryUsage(config);

    // Load test to stress memory
    for (let i = 0; i < 1000; i++) {
      try {
        await axios.get(`${config.baseUrl}/health`, {
          timeout: 5000,
          headers: { 'X-Memory-Test': 'true' }
        });

        if (i % 100 === 0) {
          const currentMemory = await this.getServiceMemoryUsage(config);
          memoryTests.push({
            iteration: i,
            memory: currentMemory,
            timestamp: Date.now()
          });
        }
      } catch (error) {
        // Continue testing
      }
    }

    // Final measurement
    const finalMemory = await this.getServiceMemoryUsage(config);

    // Calculate memory growth and GC efficiency
    const memoryGrowth = finalMemory - initialMemory;
    const peakMemory = Math.max(...memoryTests.map(t => t.memory));

    // Simple leak detection
    const trend = this.calculateTrend(memoryTests.map(t => t.memory));
    const memoryLeakSuspected = trend > 0.1 && memoryGrowth > 100; // >100MB growth

    return {
      initialMemory: Math.round(initialMemory),
      peakMemory: Math.round(peakMemory),
      finalMemory: Math.round(finalMemory),
      memoryGrowth: Math.round(memoryGrowth),
      gcEfficiency: Math.round(((peakMemory - finalMemory) / peakMemory) * 100),
      memoryLeakSuspected
    };
  }

  /**
   * Helper: Get Service Memory Usage (Mock)
   */
  async getServiceMemoryUsage(config) {
    // Mock memory usage - in real scenario, get from service metrics
    return Math.random() * 100 + 50; // 50-150 MB
  }

  /**
   * Helper: Measure End-to-End Workflow
   */
  async measureEndToEndWorkflow(workflow, flowId) {
    const workflowStart = performance.now();
    const stepResults = [];
    let successfulSteps = 0;

    for (const step of workflow.steps) {
      const service = this.services[step.service];
      if (!service) continue;

      try {
        const stepStart = performance.now();

        await axios.get(`${service.baseUrl}${step.endpoint}`, {
          timeout: 10000,
          headers: {
            'X-Flow-ID': flowId,
            'X-Workflow': workflow.name,
            'X-Performance-Test': 'e2e'
          }
        });

        const stepTime = performance.now() - stepStart;

        stepResults.push({
          service: step.service,
          time: Math.round(stepTime),
          target: step.target,
          passed: stepTime <= step.target,
          status: 'success'
        });

        successfulSteps++;

      } catch (error) {
        stepResults.push({
          service: step.service,
          error: error.message,
          status: 'failed',
          passed: false
        });
      }
    }

    const totalTime = performance.now() - workflowStart;

    // Find bottleneck
    const bottleneck = stepResults.reduce((slowest, step) => {
      if (step.time && (!slowest.time || step.time > slowest.time)) {
        return step;
      }
      return slowest;
    }, {});

    return {
      totalTime,
      steps: stepResults,
      successRate: (successfulSteps / workflow.steps.length) * 100,
      bottleneck: bottleneck.service || 'unknown'
    };
  }

  /**
   * Helper: Calculate Trend
   */
  calculateTrend(values) {
    if (values.length < 2) return 0;

    const n = values.length;
    const sumX = (n * (n - 1)) / 2;
    const sumY = values.reduce((sum, val) => sum + val, 0);
    const sumXY = values.reduce((sum, val, index) => sum + (index * val), 0);
    const sumX2 = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    return slope;
  }

  /**
   * Generate Performance Report
   */
  generatePerformanceReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        overallScore: 0,
        criticalIssues: 0,
        warnings: 0,
        passed: 0
      },
      details: this.testResults,
      recommendations: []
    };

    // Calculate overall score and generate recommendations
    this.calculatePerformanceScore(report);
    this.generatePerformanceRecommendations(report);

    return report;
  }

  /**
   * Calculate Performance Score
   */
  calculatePerformanceScore(report) {
    let totalTests = 0;
    let passedTests = 0;
    let criticalIssues = 0;
    let warnings = 0;

    // Latency tests
    Object.values(this.testResults.latency).forEach(result => {
      totalTests++;
      if (result.passed) passedTests++;
      else criticalIssues++;
    });

    // Concurrency tests
    Object.values(this.testResults.concurrency).forEach(serviceResults => {
      serviceResults.forEach(result => {
        totalTests++;
        if (result.passed) passedTests++;
        else warnings++;
      });
    });

    // Endurance tests
    Object.values(this.testResults.endurance).forEach(result => {
      totalTests++;
      if (result.passed) passedTests++;
      else if (result.memoryLeak) criticalIssues++;
      else warnings++;
    });

    report.summary.overallScore = totalTests > 0 ? Math.round((passedTests / totalTests) * 100) : 0;
    report.summary.criticalIssues = criticalIssues;
    report.summary.warnings = warnings;
    report.summary.passed = passedTests;
  }

  /**
   * Generate Performance Recommendations
   */
  generatePerformanceRecommendations(report) {
    const recommendations = [];

    // Latency recommendations
    Object.entries(this.testResults.latency).forEach(([service, result]) => {
      if (!result.passed && result.average > result.target) {
        recommendations.push({
          category: 'Latency',
          priority: service === 'trading-engine' ? 'Critical' : 'High',
          service: service,
          issue: `Latency ${result.average}ms exceeds target ${result.target}ms`,
          recommendation: 'Optimize service performance, check database queries, and implement caching',
          impact: service === 'trading-engine' ? 'Trading latency directly affects profitability' : 'User experience degradation'
        });
      }
    });

    // Throughput recommendations
    Object.entries(this.testResults.throughput).forEach(([testName, results]) => {
      Object.entries(results).forEach(([service, result]) => {
        if (result.successRate < 95) {
          recommendations.push({
            category: 'Throughput',
            priority: 'High',
            service: service,
            test: testName,
            issue: `Success rate ${result.successRate}% under load`,
            recommendation: 'Implement connection pooling, optimize resource usage, and add circuit breakers',
            impact: 'Service becomes unreliable under load'
          });
        }
      });
    });

    // Memory recommendations
    Object.entries(this.testResults.memory).forEach(([service, result]) => {
      if (result.memoryLeakSuspected) {
        recommendations.push({
          category: 'Memory',
          priority: 'Critical',
          service: service,
          issue: 'Potential memory leak detected',
          recommendation: 'Review memory management, implement proper garbage collection, and monitor heap usage',
          impact: 'Service stability and performance degradation over time'
        });
      }
    });

    report.recommendations = recommendations;
  }

  /**
   * Run All Performance Tests
   */
  async runAllPerformanceTests() {
    console.log('⚡ Starting Performance Integration Tests...');
    console.log('='.repeat(60));

    try {
      await this.testServiceLatency();
      await this.testThroughput();
      await this.testConcurrency();
      await this.testEndurance();
      await this.testMemoryPerformance();
      await this.testEndToEndPerformance();

      const report = this.generatePerformanceReport();

      console.log('\n📊 Performance Test Summary:');
      console.log(`Overall Score: ${report.summary.overallScore}%`);
      console.log(`✅ Passed: ${report.summary.passed}`);
      console.log(`⚠️ Warnings: ${report.summary.warnings}`);
      console.log(`❌ Critical Issues: ${report.summary.criticalIssues}`);

      if (report.recommendations.length > 0) {
        console.log('\n💡 Performance Recommendations:');
        report.recommendations.forEach((rec, index) => {
          console.log(`${index + 1}. [${rec.priority}] ${rec.category} - ${rec.service}: ${rec.recommendation}`);
        });
      }

      return report;

    } catch (error) {
      console.error('❌ Performance tests failed:', error.message);
      throw error;
    }
  }
}

module.exports = PerformanceIntegrationTests;

// If run directly
if (require.main === module) {
  const tests = new PerformanceIntegrationTests();
  tests.runAllPerformanceTests()
    .then(report => {
      console.log('\n✅ Performance tests completed');
      process.exit(report.summary.criticalIssues > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Performance tests failed:', error);
      process.exit(1);
    });
}