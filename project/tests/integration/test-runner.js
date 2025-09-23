/**
 * Comprehensive Test Runner for Plan2 Microservices Integration Tests
 * Orchestrates all integration test suites with proper setup and teardown
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs-extra');
const axios = require('axios');
const { performance } = require('perf_hooks');

class TestRunner {
  constructor() {
    this.services = new Map();
    this.testResults = new Map();
    this.serviceEndpoints = {
      configService: 'http://localhost:3001',
      apiGateway: 'http://localhost:3000',
      databaseService: 'http://localhost:3002'
    };
    this.logLevel = process.env.LOG_LEVEL || 'info';
  }

  async run() {
    console.log('🚀 Starting Plan2 Microservices Integration Tests');
    console.log('=' .repeat(60));
    
    const startTime = performance.now();
    
    try {
      // Pre-test setup
      await this.setupTestEnvironment();
      
      // Run test suites in sequence for stability
      await this.runTestSuite('Service Registry Tests', 'service-registry.test.js');
      await this.runTestSuite('API Gateway Routing Tests', 'api-gateway-routing.test.js');
      await this.runTestSuite('Database Service Tests', 'database-service.test.js');
      await this.runTestSuite('Flow Registry Tests', 'flow-registry.test.js');
      await this.runTestSuite('Error Propagation Tests', 'error-propagation.test.js');
      await this.runTestSuite('End-to-End Mesh Tests', 'microservices-mesh.test.js');
      
      // Generate comprehensive report
      await this.generateReport();
      
      const endTime = performance.now();
      const totalTime = ((endTime - startTime) / 1000).toFixed(2);
      
      console.log('\n🎉 All integration tests completed!');
      console.log(`Total execution time: ${totalTime}s`);
      
      return this.getOverallResults();
      
    } catch (error) {
      console.error('❌ Test execution failed:', error.message);
      throw error;
    } finally {
      await this.cleanup();
    }
  }

  async setupTestEnvironment() {
    console.log('🔧 Setting up test environment...');
    
    // Create necessary directories
    await fs.ensureDir('./logs');
    await fs.ensureDir('./results');
    await fs.ensureDir('./coverage');
    
    // Check if services are running
    const serviceChecks = await this.checkServices();
    
    if (!serviceChecks.allHealthy) {
      console.warn('⚠️  Some services are not running. Integration tests may fail.');
      console.log('Service status:', serviceChecks.statuses);
    }
    
    // Setup test databases if needed
    await this.setupTestDatabases();
    
    console.log('✅ Test environment setup complete');
  }

  async checkServices() {
    const statuses = {};
    let allHealthy = true;
    
    for (const [name, url] of Object.entries(this.serviceEndpoints)) {
      try {
        const response = await axios.get(`${url}/health`, { timeout: 5000 });
        statuses[name] = {
          healthy: response.status === 200,
          url: url,
          responseTime: response.duration || 'N/A'
        };
      } catch (error) {
        statuses[name] = {
          healthy: false,
          url: url,
          error: error.message
        };
        allHealthy = false;
      }
    }
    
    return { allHealthy, statuses };
  }

  async setupTestDatabases() {
    console.log('🗄️  Setting up test databases...');
    
    // PostgreSQL test setup
    try {
      await axios.post(`${this.serviceEndpoints.databaseService}/api/database/setup-test`, {
        database: 'postgres',
        testSchema: true
      });
    } catch (error) {
      console.warn('Failed to setup PostgreSQL test schema:', error.message);
    }
    
    // MongoDB test setup
    try {
      await axios.post(`${this.serviceEndpoints.databaseService}/api/database/setup-test`, {
        database: 'mongodb',
        testCollections: true
      });
    } catch (error) {
      console.warn('Failed to setup MongoDB test collections:', error.message);
    }
    
    // Redis test setup
    try {
      await axios.post(`${this.serviceEndpoints.databaseService}/api/database/setup-test`, {
        database: 'redis',
        flushTestDb: true
      });
    } catch (error) {
      console.warn('Failed to setup Redis test database:', error.message);
    }
  }

  async runTestSuite(suiteName, testFile) {
    console.log(`\n📋 Running ${suiteName}...`);
    console.log('-'.repeat(40));
    
    const startTime = performance.now();
    
    return new Promise((resolve, reject) => {
      const testProcess = spawn('npx', ['mocha', testFile, '--timeout', '60000', '--reporter', 'json'], {
        cwd: __dirname,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      testProcess.stdout.on('data', (data) => {
        stdout += data.toString();
        if (this.logLevel === 'debug') {
          process.stdout.write(data);
        }
      });
      
      testProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        if (this.logLevel === 'debug') {
          process.stderr.write(data);
        }
      });
      
      testProcess.on('close', (code) => {
        const endTime = performance.now();
        const duration = ((endTime - startTime) / 1000).toFixed(2);
        
        let results;
        try {
          results = JSON.parse(stdout);
        } catch (error) {
          results = {
            stats: { passes: 0, failures: 1, tests: 1 },
            failures: [{ title: 'Parse Error', err: { message: error.message } }]
          };
        }
        
        const testResult = {
          suiteName,
          testFile,
          duration: parseFloat(duration),
          passed: results.stats.passes || 0,
          failed: results.stats.failures || 0,
          total: results.stats.tests || 0,
          exitCode: code,
          stdout,
          stderr,
          timestamp: new Date().toISOString()
        };
        
        this.testResults.set(suiteName, testResult);
        
        // Log summary
        const status = code === 0 ? '✅' : '❌';
        console.log(`${status} ${suiteName}: ${testResult.passed}/${testResult.total} passed (${duration}s)`);
        
        if (testResult.failed > 0) {
          console.log(`   Failures: ${testResult.failed}`);
          if (results.failures && this.logLevel !== 'quiet') {
            results.failures.forEach((failure, index) => {
              console.log(`   ${index + 1}. ${failure.title}: ${failure.err.message}`);
            });
          }
        }
        
        resolve(testResult);
      });
      
      testProcess.on('error', (error) => {
        console.error(`❌ Failed to start test process for ${suiteName}:`, error.message);
        reject(error);
      });
    });
  }

  async generateReport() {
    console.log('\n📊 Generating test report...');
    
    const report = {
      timestamp: new Date().toISOString(),
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
      },
      summary: this.calculateSummary(),
      testSuites: Array.from(this.testResults.values()),
      recommendations: this.generateRecommendations()
    };
    
    // Write JSON report
    await fs.writeJson('./results/integration-test-report.json', report, { spaces: 2 });
    
    // Write HTML report
    await this.generateHtmlReport(report);
    
    // Write coverage report if available
    await this.generateCoverageReport();
    
    console.log('✅ Test report generated: ./results/integration-test-report.json');
    console.log('🌐 HTML report generated: ./results/integration-test-report.html');
  }

  calculateSummary() {
    const results = Array.from(this.testResults.values());
    
    return {
      totalSuites: results.length,
      totalTests: results.reduce((sum, r) => sum + r.total, 0),
      totalPassed: results.reduce((sum, r) => sum + r.passed, 0),
      totalFailed: results.reduce((sum, r) => sum + r.failed, 0),
      totalDuration: results.reduce((sum, r) => sum + r.duration, 0),
      successRate: this.calculateSuccessRate(results),
      averageDuration: results.length > 0 ? 
        (results.reduce((sum, r) => sum + r.duration, 0) / results.length).toFixed(2) : 0
    };
  }

  calculateSuccessRate(results) {
    const totalTests = results.reduce((sum, r) => sum + r.total, 0);
    const totalPassed = results.reduce((sum, r) => sum + r.passed, 0);
    return totalTests > 0 ? ((totalPassed / totalTests) * 100).toFixed(2) : 0;
  }

  generateRecommendations() {
    const recommendations = [];
    const results = Array.from(this.testResults.values());
    
    // Check for slow tests
    const slowTests = results.filter(r => r.duration > 30);
    if (slowTests.length > 0) {
      recommendations.push({
        category: 'Performance',
        priority: 'Medium',
        message: `${slowTests.length} test suite(s) took longer than 30 seconds. Consider optimizing: ${slowTests.map(t => t.suiteName).join(', ')}`
      });
    }
    
    // Check for failed tests
    const failedTests = results.filter(r => r.failed > 0);
    if (failedTests.length > 0) {
      recommendations.push({
        category: 'Reliability',
        priority: 'High',
        message: `${failedTests.length} test suite(s) have failures. Review and fix: ${failedTests.map(t => t.suiteName).join(', ')}`
      });
    }
    
    // Check success rate
    const summary = this.calculateSummary();
    if (summary.successRate < 95) {
      recommendations.push({
        category: 'Quality',
        priority: 'High',
        message: `Overall success rate is ${summary.successRate}%. Target should be above 95%.`
      });
    }
    
    return recommendations;
  }

  async generateHtmlReport(report) {
    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plan2 Microservices Integration Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007acc; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; border-left: 4px solid #007acc; }
        .metric-value { font-size: 2em; font-weight: bold; color: #007acc; }
        .metric-label { color: #666; font-size: 0.9em; }
        .suite { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .suite-header { display: flex; justify-content: space-between; align-items: center; }
        .suite-name { font-weight: bold; font-size: 1.1em; }
        .status { padding: 4px 8px; border-radius: 3px; color: white; font-size: 0.8em; }
        .passed { background-color: #28a745; }
        .failed { background-color: #dc3545; }
        .warning { background-color: #ffc107; color: black; }
        .recommendations { margin-top: 30px; }
        .recommendation { margin: 10px 0; padding: 10px; border-left: 4px solid #ffc107; background: #fff3cd; }
        .recommendation.high { border-left-color: #dc3545; background: #f8d7da; }
        .recommendation.medium { border-left-color: #ffc107; background: #fff3cd; }
        .timestamp { color: #666; font-size: 0.9em; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Plan2 Microservices Integration Test Report</h1>
        <p class="timestamp">Generated: ${report.timestamp}</p>
        
        <h2>Summary</h2>
        <div class="summary">
            <div class="metric">
                <div class="metric-value">${report.summary.totalSuites}</div>
                <div class="metric-label">Test Suites</div>
            </div>
            <div class="metric">
                <div class="metric-value">${report.summary.totalTests}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric">
                <div class="metric-value">${report.summary.totalPassed}</div>
                <div class="metric-label">Passed</div>
            </div>
            <div class="metric">
                <div class="metric-value">${report.summary.totalFailed}</div>
                <div class="metric-label">Failed</div>
            </div>
            <div class="metric">
                <div class="metric-value">${report.summary.successRate}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">${report.summary.totalDuration.toFixed(2)}s</div>
                <div class="metric-label">Total Duration</div>
            </div>
        </div>
        
        <h2>Test Suites</h2>
        ${report.testSuites.map(suite => `
            <div class="suite">
                <div class="suite-header">
                    <span class="suite-name">${suite.suiteName}</span>
                    <span class="status ${suite.failed > 0 ? 'failed' : 'passed'}">
                        ${suite.passed}/${suite.total} passed (${suite.duration}s)
                    </span>
                </div>
                <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                    File: ${suite.testFile} | Exit Code: ${suite.exitCode}
                </div>
            </div>
        `).join('')}
        
        ${report.recommendations.length > 0 ? `
            <h2>Recommendations</h2>
            <div class="recommendations">
                ${report.recommendations.map(rec => `
                    <div class="recommendation ${rec.priority.toLowerCase()}">
                        <strong>${rec.category} (${rec.priority} Priority):</strong> ${rec.message}
                    </div>
                `).join('')}
            </div>
        ` : ''}
        
        <h2>Environment</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Node.js Version</td><td>${report.environment.nodeVersion}</td></tr>
            <tr><td>Platform</td><td>${report.environment.platform}</td></tr>
            <tr><td>Architecture</td><td>${report.environment.arch}</td></tr>
        </table>
    </div>
</body>
</html>
    `;
    
    await fs.writeFile('./results/integration-test-report.html', html);
  }

  async generateCoverageReport() {
    // Placeholder for coverage report generation
    // This would typically involve nyc or istanbul
    console.log('📈 Coverage report generation skipped (not configured)');
  }

  getOverallResults() {
    const summary = this.calculateSummary();
    return {
      success: summary.totalFailed === 0,
      summary,
      results: Array.from(this.testResults.values())
    };
  }

  async cleanup() {
    console.log('\n🧹 Cleaning up test environment...');
    
    try {
      // Cleanup test databases
      await axios.post(`${this.serviceEndpoints.databaseService}/api/database/cleanup-test`, {
        databases: ['postgres', 'mongodb', 'redis']
      });
    } catch (error) {
      console.warn('Failed to cleanup test databases:', error.message);
    }
    
    console.log('✅ Cleanup complete');
  }
}

// CLI execution
if (require.main === module) {
  const runner = new TestRunner();
  
  runner.run()
    .then((results) => {
      if (results.success) {
        console.log('\n🎉 All tests passed successfully!');
        process.exit(0);
      } else {
        console.log('\n❌ Some tests failed. Check the report for details.');
        process.exit(1);
      }
    })
    .catch((error) => {
      console.error('\n💥 Test runner failed:', error.message);
      process.exit(1);
    });
}

module.exports = TestRunner;
