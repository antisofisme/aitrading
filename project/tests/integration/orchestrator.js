/**
 * LEVEL 1 Foundation Integration Test Orchestrator
 * Main test runner for all foundation services integration testing
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const config = require('./config/test-config');
const helpers = require('./utils/test-helpers');

class IntegrationTestOrchestrator {
  constructor() {
    this.results = {
      startTime: new Date(),
      endTime: null,
      totalTests: 0,
      passedTests: 0,
      failedTests: 0,
      skippedTests: 0,
      suiteResults: {},
      serviceStatus: {},
      summary: null
    };

    this.testSuites = [
      {
        name: 'API Gateway',
        file: 'api-gateway.test.js',
        dependencies: [],
        critical: true
      },
      {
        name: 'Database Service',
        file: 'database-service.test.js',
        dependencies: [],
        critical: true
      },
      {
        name: 'Data Bridge',
        file: 'data-bridge.test.js',
        dependencies: [],
        critical: false
      },
      {
        name: 'Central Hub',
        file: 'central-hub.test.js',
        dependencies: [],
        critical: true
      },
      {
        name: 'Workspace Configuration',
        file: 'workspace-config.test.js',
        dependencies: [],
        critical: true
      }
    ];
  }

  async initialize() {
    console.log('🚀 LEVEL 1 Foundation Integration Test Orchestrator');
    console.log('================================================');
    console.log('Testing AI Trading Platform Foundation Services');
    console.log('');

    // Create results directory
    const resultsDir = path.join(__dirname, 'results');
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }

    // Check test environment
    await this.checkTestEnvironment();
  }

  async checkTestEnvironment() {
    console.log('🔍 Checking test environment...');

    const environmentChecks = [
      {
        name: 'Node.js Version',
        check: () => process.version,
        validate: (result) => result.startsWith('v') && parseInt(result.slice(1)) >= 18
      },
      {
        name: 'Test Configuration',
        check: () => config,
        validate: (result) => result && result.apiGateway && result.databaseService
      },
      {
        name: 'Test Helpers',
        check: () => helpers,
        validate: (result) => result && typeof result.makeRequest === 'function'
      }
    ];

    for (const check of environmentChecks) {
      try {
        const result = check.check();
        const isValid = check.validate(result);

        console.log(`  ${isValid ? '✅' : '❌'} ${check.name}: ${isValid ? 'OK' : 'FAILED'}`);

        if (!isValid && check.name === 'Test Configuration') {
          throw new Error('Test configuration is invalid');
        }
      } catch (error) {
        console.log(`  ❌ ${check.name}: ERROR - ${error.message}`);
      }
    }

    console.log('');
  }

  async checkServiceAvailability() {
    console.log('🔍 Checking service availability...');

    const services = [
      {
        name: 'API Gateway',
        url: config.apiGateway.baseUrl,
        port: config.apiGateway.expectedPort,
        critical: true
      },
      {
        name: 'Database Service',
        url: config.databaseService.baseUrl,
        port: config.databaseService.expectedPort,
        critical: true
      },
      {
        name: 'Data Bridge',
        url: config.dataBridge.baseUrl,
        port: config.dataBridge.expectedPort,
        critical: false
      },
      {
        name: 'Central Hub',
        url: config.centralHub.baseUrl,
        port: config.centralHub.expectedPort,
        critical: true
      }
    ];

    for (const service of services) {
      try {
        const isPortOpen = await helpers.isPortOpen('localhost', service.port);
        const health = isPortOpen ? await helpers.checkHealth(service.url) : { isHealthy: false, error: 'Port not open' };

        this.results.serviceStatus[service.name] = {
          available: isPortOpen,
          healthy: health.isHealthy,
          url: service.url,
          port: service.port,
          critical: service.critical,
          details: health
        };

        const status = isPortOpen && health.isHealthy ? '🟢' : service.critical ? '🔴' : '🟡';
        console.log(`  ${status} ${service.name} (${service.url}) - ${isPortOpen ? (health.isHealthy ? 'Healthy' : 'Unhealthy') : 'Unavailable'}`);

      } catch (error) {
        this.results.serviceStatus[service.name] = {
          available: false,
          healthy: false,
          url: service.url,
          port: service.port,
          critical: service.critical,
          error: error.message
        };

        const status = service.critical ? '🔴' : '🟡';
        console.log(`  ${status} ${service.name} (${service.url}) - Error: ${error.message}`);
      }
    }

    console.log('');
  }

  async runTestSuite(suite) {
    console.log(`🧪 Running ${suite.name} tests...`);

    return new Promise((resolve) => {
      const jestPath = path.join(__dirname, '../../node_modules/.bin/jest');
      const testFile = path.join(__dirname, 'suites', suite.file);

      // Check if test file exists
      if (!fs.existsSync(testFile)) {
        console.log(`  ⚠️  Test file not found: ${suite.file}`);
        resolve({
          suite: suite.name,
          status: 'skipped',
          reason: 'Test file not found',
          tests: { total: 0, passed: 0, failed: 0, skipped: 1 }
        });
        return;
      }

      const jest = spawn('npx', ['jest', testFile, '--verbose', '--no-cache'], {
        cwd: path.join(__dirname, '../..'),
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, NODE_ENV: 'test' }
      });

      let output = '';
      let errorOutput = '';

      jest.stdout.on('data', (data) => {
        output += data.toString();
      });

      jest.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });

      jest.on('close', (code) => {
        const success = code === 0;
        const result = this.parseJestOutput(output, errorOutput, suite.name);

        console.log(`  ${success ? '✅' : '❌'} ${suite.name}: ${result.tests.passed}/${result.tests.total} tests passed`);

        if (!success && errorOutput) {
          console.log(`  🔍 Error details: ${errorOutput.slice(0, 200)}...`);
        }

        resolve({
          suite: suite.name,
          status: success ? 'passed' : 'failed',
          code: code,
          output: output,
          error: errorOutput,
          tests: result.tests,
          duration: result.duration
        });
      });

      jest.on('error', (error) => {
        console.log(`  ❌ ${suite.name}: Failed to run tests - ${error.message}`);
        resolve({
          suite: suite.name,
          status: 'failed',
          error: error.message,
          tests: { total: 0, passed: 0, failed: 1, skipped: 0 }
        });
      });
    });
  }

  parseJestOutput(output, errorOutput, suiteName) {
    const tests = { total: 0, passed: 0, failed: 0, skipped: 0 };
    let duration = 0;

    try {
      // Parse Jest output for test results
      const lines = output.split('\n');

      for (const line of lines) {
        if (line.includes('✓') || line.includes('PASS')) {
          tests.passed++;
          tests.total++;
        } else if (line.includes('✗') || line.includes('FAIL')) {
          tests.failed++;
          tests.total++;
        } else if (line.includes('○') || line.includes('SKIP')) {
          tests.skipped++;
          tests.total++;
        }

        // Extract duration
        const timeMatch = line.match(/Time:\s*(\d+\.?\d*)\s*s/);
        if (timeMatch) {
          duration = parseFloat(timeMatch[1]) * 1000; // Convert to ms
        }
      }

      // If no tests were parsed, try alternative parsing
      if (tests.total === 0) {
        const summaryMatch = output.match(/Tests:\s*(\d+)\s*passed.*?(\d+)\s*total/);
        if (summaryMatch) {
          tests.passed = parseInt(summaryMatch[1]);
          tests.total = parseInt(summaryMatch[2]);
          tests.failed = tests.total - tests.passed;
        }
      }

    } catch (error) {
      console.log(`Warning: Could not parse Jest output for ${suiteName}`);
    }

    return { tests, duration };
  }

  async runAllTests() {
    console.log('🧪 Running all test suites...');
    console.log('');

    for (const suite of this.testSuites) {
      const result = await this.runTestSuite(suite);
      this.results.suiteResults[suite.name] = result;

      // Update totals
      this.results.totalTests += result.tests.total;
      this.results.passedTests += result.tests.passed;
      this.results.failedTests += result.tests.failed;
      this.results.skippedTests += result.tests.skipped;
    }

    console.log('');
  }

  generateSummary() {
    this.results.endTime = new Date();
    const duration = this.results.endTime - this.results.startTime;

    const summary = {
      testExecution: {
        duration: duration,
        totalTests: this.results.totalTests,
        passedTests: this.results.passedTests,
        failedTests: this.results.failedTests,
        skippedTests: this.results.skippedTests,
        successRate: this.results.totalTests > 0 ? (this.results.passedTests / this.results.totalTests * 100).toFixed(2) : 0
      },
      serviceHealth: {},
      foundationReadiness: {
        level1Complete: false,
        readyForLevel2: false,
        criticalIssues: [],
        recommendations: []
      }
    };

    // Analyze service health
    Object.keys(this.results.serviceStatus).forEach(serviceName => {
      const service = this.results.serviceStatus[serviceName];
      summary.serviceHealth[serviceName] = {
        status: service.available && service.healthy ? 'healthy' : 'unhealthy',
        critical: service.critical,
        issues: service.available ? (service.healthy ? [] : ['Service unhealthy']) : ['Service unavailable']
      };
    });

    // Assess foundation readiness
    const criticalServices = Object.keys(this.results.serviceStatus).filter(name =>
      this.results.serviceStatus[name].critical
    );

    const healthyCriticalServices = criticalServices.filter(name =>
      this.results.serviceStatus[name].available && this.results.serviceStatus[name].healthy
    );

    const failedCriticalTests = Object.keys(this.results.suiteResults).filter(name => {
      const suite = this.testSuites.find(s => s.name === name);
      return suite && suite.critical && this.results.suiteResults[name].status === 'failed';
    });

    summary.foundationReadiness.level1Complete =
      healthyCriticalServices.length === criticalServices.length &&
      failedCriticalTests.length === 0 &&
      summary.testExecution.successRate >= 80;

    summary.foundationReadiness.readyForLevel2 =
      summary.foundationReadiness.level1Complete &&
      summary.testExecution.successRate >= 90;

    // Generate recommendations
    if (!summary.foundationReadiness.level1Complete) {
      if (failedCriticalTests.length > 0) {
        summary.foundationReadiness.criticalIssues.push(`Critical test suites failed: ${failedCriticalTests.join(', ')}`);
        summary.foundationReadiness.recommendations.push('Fix failing critical tests before proceeding');
      }

      const unhealthyCritical = criticalServices.filter(name =>
        !this.results.serviceStatus[name].available || !this.results.serviceStatus[name].healthy
      );

      if (unhealthyCritical.length > 0) {
        summary.foundationReadiness.criticalIssues.push(`Critical services unhealthy: ${unhealthyCritical.join(', ')}`);
        summary.foundationReadiness.recommendations.push('Ensure all critical services are running and healthy');
      }
    }

    if (summary.foundationReadiness.level1Complete && !summary.foundationReadiness.readyForLevel2) {
      summary.foundationReadiness.recommendations.push('Improve test success rate to 90%+ for LEVEL 2 readiness');
    }

    this.results.summary = summary;
    return summary;
  }

  async saveResults() {
    const resultsFile = path.join(__dirname, 'results', `integration-test-results-${Date.now()}.json`);

    try {
      fs.writeFileSync(resultsFile, JSON.stringify(this.results, null, 2));
      console.log(`📄 Results saved to: ${resultsFile}`);
    } catch (error) {
      console.log(`⚠️  Could not save results: ${error.message}`);
    }
  }

  printSummary() {
    const summary = this.results.summary;

    console.log('📊 LEVEL 1 Foundation Integration Test Summary');
    console.log('==============================================');
    console.log('');

    console.log('🧪 Test Execution:');
    console.log(`   Total Tests: ${summary.testExecution.totalTests}`);
    console.log(`   Passed: ${summary.testExecution.passedTests} (${summary.testExecution.successRate}%)`);
    console.log(`   Failed: ${summary.testExecution.failedTests}`);
    console.log(`   Skipped: ${summary.testExecution.skippedTests}`);
    console.log(`   Duration: ${(summary.testExecution.duration / 1000).toFixed(2)}s`);
    console.log('');

    console.log('🏥 Service Health:');
    Object.keys(summary.serviceHealth).forEach(serviceName => {
      const service = summary.serviceHealth[serviceName];
      const icon = service.status === 'healthy' ? '🟢' : (service.critical ? '🔴' : '🟡');
      console.log(`   ${icon} ${serviceName}: ${service.status}${service.critical ? ' (critical)' : ''}`);
      if (service.issues.length > 0) {
        service.issues.forEach(issue => console.log(`      - ${issue}`));
      }
    });
    console.log('');

    console.log('🎯 Foundation Readiness:');
    console.log(`   LEVEL 1 Complete: ${summary.foundationReadiness.level1Complete ? '✅ YES' : '❌ NO'}`);
    console.log(`   Ready for LEVEL 2: ${summary.foundationReadiness.readyForLevel2 ? '✅ YES' : '❌ NO'}`);

    if (summary.foundationReadiness.criticalIssues.length > 0) {
      console.log('');
      console.log('🚨 Critical Issues:');
      summary.foundationReadiness.criticalIssues.forEach(issue => {
        console.log(`   - ${issue}`);
      });
    }

    if (summary.foundationReadiness.recommendations.length > 0) {
      console.log('');
      console.log('💡 Recommendations:');
      summary.foundationReadiness.recommendations.forEach(rec => {
        console.log(`   - ${rec}`);
      });
    }

    console.log('');
    console.log('==============================================');

    if (summary.foundationReadiness.readyForLevel2) {
      console.log('🎉 LEVEL 1 Foundation is solid! Ready for LEVEL 2 Connectivity.');
    } else if (summary.foundationReadiness.level1Complete) {
      console.log('✅ LEVEL 1 Foundation is complete with minor issues.');
    } else {
      console.log('⚠️  LEVEL 1 Foundation needs attention before proceeding.');
    }
  }

  async run() {
    try {
      await this.initialize();
      await this.checkServiceAvailability();
      await this.runAllTests();

      const summary = this.generateSummary();
      this.printSummary();

      await this.saveResults();

      // Exit with appropriate code
      const exitCode = summary.foundationReadiness.level1Complete ? 0 : 1;
      process.exit(exitCode);

    } catch (error) {
      console.error('❌ Orchestrator failed:', error);
      process.exit(1);
    }
  }
}

// Run if called directly
if (require.main === module) {
  const orchestrator = new IntegrationTestOrchestrator();
  orchestrator.run();
}

module.exports = IntegrationTestOrchestrator;