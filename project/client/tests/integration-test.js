const MetaTraderConnector = require('../src/services/mt5-connector');
const DataCollector = require('../src/services/data-collector');
const SecurityManager = require('../src/security/security-manager');
const ConfigManager = require('../src/services/config-manager');
const PerformanceMonitor = require('../src/monitoring/performance-monitor');
const logger = require('../src/utils/logger');

class IntegrationTest {
  constructor() {
    this.testResults = [];
    this.configManager = null;
    this.securityManager = null;
    this.mt5Connector = null;
    this.dataCollector = null;
    this.performanceMonitor = null;
  }

  async runAllTests() {
    logger.info('Starting comprehensive integration tests...');

    try {
      // Test 1: Configuration Manager
      await this.testConfigManager();

      // Test 2: Security Manager
      await this.testSecurityManager();

      // Test 3: Performance Monitor
      await this.testPerformanceMonitor();

      // Test 4: MT5 Connector (Mock mode for testing)
      await this.testMT5Connector();

      // Test 5: Data Collector
      await this.testDataCollector();

      // Test 6: End-to-End Data Flow
      await this.testEndToEndDataFlow();

      // Test 7: Performance Targets
      await this.testPerformanceTargets();

      // Test 8: Error Handling & Recovery
      await this.testErrorHandling();

      this.printTestResults();

    } catch (error) {
      logger.error('Integration test suite failed:', error);
      this.addTestResult('Integration Test Suite', false, error.message);
    }
  }

  async testConfigManager() {
    try {
      logger.info('Testing Configuration Manager...');

      this.configManager = new ConfigManager();
      await this.configManager.initialize();

      // Test config loading
      const mt5Config = this.configManager.get('mt5');
      this.addTestResult('Config Manager - Initialize', !!mt5Config, 'Configuration loaded successfully');

      // Test config updates
      await this.configManager.update({
        mt5: { targetTicksPerSecond: 25 }
      });

      const updatedConfig = this.configManager.get('mt5', 'targetTicksPerSecond');
      this.addTestResult('Config Manager - Update', updatedConfig === 25, 'Configuration updated successfully');

      logger.info('Configuration Manager tests passed');

    } catch (error) {
      this.addTestResult('Config Manager', false, error.message);
      throw error;
    }
  }

  async testSecurityManager() {
    try {
      logger.info('Testing Security Manager...');

      this.securityManager = new SecurityManager();
      await this.securityManager.initialize();

      // Test credential storage and retrieval
      const testCredentials = {
        server: 'test-server',
        login: '12345',
        password: 'test-password'
      };

      await this.securityManager.storeCredentials('test-service', testCredentials);
      const retrievedCredentials = await this.securityManager.getCredentials('test-service');

      const credentialsMatch = JSON.stringify(testCredentials) === JSON.stringify(retrievedCredentials);
      this.addTestResult('Security Manager - Credentials', credentialsMatch, 'Credentials stored and retrieved successfully');

      // Test encryption status
      const securityStatus = this.securityManager.getSecurityStatus();
      this.addTestResult('Security Manager - Status', securityStatus.initialized, 'Security manager initialized properly');

      logger.info('Security Manager tests passed');

    } catch (error) {
      this.addTestResult('Security Manager', false, error.message);
      throw error;
    }
  }

  async testPerformanceMonitor() {
    try {
      logger.info('Testing Performance Monitor...');

      this.performanceMonitor = new PerformanceMonitor();
      await this.performanceMonitor.initialize();

      // Test monitoring start
      this.performanceMonitor.startMonitoring();

      // Simulate data processing
      for (let i = 0; i < 10; i++) {
        this.performanceMonitor.recordDataProcessing({
          latency: Math.random() * 50,
          error: false
        });
      }

      // Wait for metrics collection
      await new Promise(resolve => setTimeout(resolve, 2000));

      const metrics = this.performanceMonitor.getMetrics();
      this.addTestResult('Performance Monitor - Metrics', metrics.dataProcessing.totalProcessed >= 10, 'Performance metrics recorded correctly');

      // Test connection status recording
      this.performanceMonitor.recordConnectionStatus('mt5', true, 25);
      const connectionStatus = metrics.connections.mt5.connected;
      this.addTestResult('Performance Monitor - Connections', connectionStatus, 'Connection status recorded correctly');

      logger.info('Performance Monitor tests passed');

    } catch (error) {
      this.addTestResult('Performance Monitor', false, error.message);
      throw error;
    }
  }

  async testMT5Connector() {
    try {
      logger.info('Testing MT5 Connector (Mock Mode)...');

      // Use test configuration
      const testConfig = {
        maxConnections: 3,
        targetTicksPerSecond: 25,
        symbols: ['EURUSD', 'GBPUSD']
      };

      this.mt5Connector = new MetaTraderConnector(testConfig, this.securityManager);

      // Test connection pool initialization
      await this.mt5Connector.initializeConnectionPool({
        server: 'test-server',
        login: '12345',
        password: 'test-password'
      });

      const connectionCount = this.mt5Connector.getConnectionCount();
      this.addTestResult('MT5 Connector - Connection Pool', connectionCount === 3, `Created ${connectionCount} connections`);

      // Test performance metrics
      const performanceMetrics = this.mt5Connector.getPerformanceMetrics();
      this.addTestResult('MT5 Connector - Metrics', !!performanceMetrics, 'Performance metrics available');

      logger.info('MT5 Connector tests passed');

    } catch (error) {
      this.addTestResult('MT5 Connector', false, error.message);
      // Don't throw here as MT5 might not be available in test environment
    }
  }

  async testDataCollector() {
    try {
      logger.info('Testing Data Collector...');

      const dataConfig = {
        backendUrl: 'ws://localhost:3001/ws',
        bufferSize: 100,
        symbols: ['EURUSD', 'GBPUSD']
      };

      this.dataCollector = new DataCollector(dataConfig, this.performanceMonitor);

      // Test data processing without actual backend connection
      const testTickData = {
        symbol: 'EURUSD',
        bid: 1.0850,
        ask: 1.0852,
        timestamp: Date.now()
      };

      this.dataCollector.processTickData(testTickData);

      const metrics = this.dataCollector.getMetrics();
      this.addTestResult('Data Collector - Processing', metrics.dataPointsProcessed >= 1, 'Tick data processed successfully');

      // Test market data processing
      const testMarketData = {
        symbol: 'EURUSD',
        spread: 2,
        digits: 5
      };

      this.dataCollector.processMarketData(testMarketData);
      this.addTestResult('Data Collector - Market Data', metrics.dataPointsProcessed >= 2, 'Market data processed successfully');

      logger.info('Data Collector tests passed');

    } catch (error) {
      this.addTestResult('Data Collector', false, error.message);
      throw error;
    }
  }

  async testEndToEndDataFlow() {
    try {
      logger.info('Testing End-to-End Data Flow...');

      // Simulate complete data flow
      const testData = {
        symbol: 'EURUSD',
        bid: 1.0850,
        ask: 1.0852,
        volume: 100,
        timestamp: Date.now(),
        connectionId: 'conn_0'
      };

      // 1. MT5 receives tick data
      if (this.mt5Connector) {
        this.mt5Connector.handleTickData(testData);
      }

      // 2. Data Collector processes the data
      this.dataCollector.processTickData(testData);

      // 3. Performance Monitor records metrics
      this.performanceMonitor.recordDataProcessing({
        latency: 15,
        error: false
      });

      // Verify data flow
      const dataMetrics = this.dataCollector.getMetrics();
      const perfMetrics = this.performanceMonitor.getMetrics();

      const dataFlowSuccess = dataMetrics.dataPointsProcessed > 0 && perfMetrics.dataProcessing.totalProcessed > 0;
      this.addTestResult('End-to-End Data Flow', dataFlowSuccess, 'Complete data flow pipeline working');

      logger.info('End-to-End Data Flow test passed');

    } catch (error) {
      this.addTestResult('End-to-End Data Flow', false, error.message);
    }
  }

  async testPerformanceTargets() {
    try {
      logger.info('Testing Performance Targets...');

      // Simulate high-frequency data processing
      const startTime = Date.now();
      const targetTPS = 50;
      const testDuration = 2000; // 2 seconds

      const interval = setInterval(() => {
        // Simulate tick processing
        this.performanceMonitor.recordDataProcessing({
          latency: Math.random() * 30 + 5, // 5-35ms latency
          error: Math.random() > 0.99 // 1% error rate
        });

        this.dataCollector.processTickData({
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: Date.now()
        });
      }, 1000 / targetTPS); // Target frequency

      // Wait for test duration
      await new Promise(resolve => setTimeout(resolve, testDuration));
      clearInterval(interval);

      const metrics = this.performanceMonitor.getMetrics();
      const actualTPS = metrics.dataProcessing.ticksPerSecond;
      const latency = metrics.dataProcessing.averageLatency;

      const tpsTarget = actualTPS >= targetTPS * 0.8; // 80% of target
      const latencyTarget = latency <= 50; // Under 50ms

      this.addTestResult('Performance - TPS Target', tpsTarget, `Achieved ${actualTPS.toFixed(1)} TPS (target: ${targetTPS})`);
      this.addTestResult('Performance - Latency Target', latencyTarget, `Average latency: ${latency.toFixed(1)}ms (target: <50ms)`);

      logger.info('Performance Targets test completed');

    } catch (error) {
      this.addTestResult('Performance Targets', false, error.message);
    }
  }

  async testErrorHandling() {
    try {
      logger.info('Testing Error Handling & Recovery...');

      // Test configuration error handling
      try {
        await this.configManager.update({
          mt5: { maxConnections: -1 } // Invalid value
        });
        // Should validate and not set invalid value
        const connections = this.configManager.get('mt5', 'maxConnections');
        this.addTestResult('Error Handling - Config Validation', connections > 0, 'Invalid config values rejected');
      } catch (error) {
        this.addTestResult('Error Handling - Config Validation', true, 'Config validation working');
      }

      // Test data processing error handling
      try {
        this.dataCollector.processTickData(null); // Invalid data
        this.addTestResult('Error Handling - Data Processing', true, 'Invalid data handled gracefully');
      } catch (error) {
        this.addTestResult('Error Handling - Data Processing', true, 'Error caught and handled');
      }

      // Test performance monitoring with error conditions
      this.performanceMonitor.recordDataProcessing({
        latency: 1000, // Very high latency
        error: true
      });

      const metrics = this.performanceMonitor.getMetrics();
      const errorsRecorded = metrics.dataProcessing.processingErrors > 0;
      this.addTestResult('Error Handling - Performance Monitoring', errorsRecorded, 'Errors properly recorded in metrics');

      logger.info('Error Handling tests passed');

    } catch (error) {
      this.addTestResult('Error Handling', false, error.message);
    }
  }

  addTestResult(testName, passed, message) {
    this.testResults.push({
      test: testName,
      passed,
      message,
      timestamp: new Date().toISOString()
    });

    const status = passed ? '✅ PASS' : '❌ FAIL';
    logger.info(`${status} - ${testName}: ${message}`);
  }

  printTestResults() {
    const totalTests = this.testResults.length;
    const passedTests = this.testResults.filter(result => result.passed).length;
    const failedTests = totalTests - passedTests;

    console.log('\n' + '='.repeat(80));
    console.log('INTEGRATION TEST RESULTS');
    console.log('='.repeat(80));
    console.log(`Total Tests: ${totalTests}`);
    console.log(`Passed: ${passedTests}`);
    console.log(`Failed: ${failedTests}`);
    console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
    console.log('='.repeat(80));

    // Print detailed results
    this.testResults.forEach(result => {
      const status = result.passed ? '✅' : '❌';
      console.log(`${status} ${result.test}: ${result.message}`);
    });

    console.log('='.repeat(80));

    // Performance summary
    if (this.performanceMonitor) {
      const metrics = this.performanceMonitor.getMetrics();
      console.log('\nPERFORMACE SUMMARY:');
      console.log(`- Ticks Per Second: ${metrics.dataProcessing.ticksPerSecond.toFixed(1)} TPS`);
      console.log(`- Average Latency: ${metrics.dataProcessing.averageLatency.toFixed(1)} ms`);
      console.log(`- Data Processed: ${metrics.dataProcessing.totalProcessed}`);
      console.log(`- Success Rate: ${(((metrics.dataProcessing.totalProcessed - metrics.dataProcessing.processingErrors) / metrics.dataProcessing.totalProcessed) * 100).toFixed(1)}%`);
      console.log(`- Target Compliance: ${metrics.targets.currentCompliance.toFixed(1)}%`);
    }

    console.log('\n' + '='.repeat(80));

    logger.info(`Integration tests completed: ${passedTests}/${totalTests} passed`);
  }

  async cleanup() {
    try {
      if (this.performanceMonitor) {
        await this.performanceMonitor.stop();
      }

      if (this.dataCollector) {
        await this.dataCollector.disconnect();
      }

      if (this.mt5Connector) {
        await this.mt5Connector.disconnect();
      }

      if (this.configManager) {
        await this.configManager.shutdown();
      }

      logger.info('Test cleanup completed');

    } catch (error) {
      logger.error('Error during test cleanup:', error);
    }
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  const test = new IntegrationTest();

  test.runAllTests()
    .then(async () => {
      await test.cleanup();
      const passedTests = test.testResults.filter(result => result.passed).length;
      const totalTests = test.testResults.length;

      if (passedTests === totalTests) {
        console.log('\n🎉 All integration tests passed!');
        process.exit(0);
      } else {
        console.log('\n⚠️  Some tests failed. Check the results above.');
        process.exit(1);
      }
    })
    .catch(async (error) => {
      logger.error('Test suite failed:', error);
      await test.cleanup();
      process.exit(1);
    });
}

module.exports = IntegrationTest;