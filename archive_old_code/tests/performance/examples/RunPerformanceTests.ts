#!/usr/bin/env ts-node

/**
 * MT5 Performance Test Suite - Example Runner
 *
 * This file demonstrates how to run comprehensive performance tests
 * for MT5 integration with full coordination and team memory storage.
 */

import {
  MT5PerformanceTestSuite,
  TRADING_PERFORMANCE_SUITE,
  COMPREHENSIVE_PERFORMANCE_SUITE,
  STRESS_TEST_SUITE,
  runTradingPerformanceTest,
  createHooksIntegration
} from '../index';

import type {
  MT5PerformanceTestConfig,
  TestResults
} from '../MT5PerformanceTestSuite';

// Configuration for your MT5 server
const MT5_CONFIG = {
  server: process.env.MT5_SERVER || 'demo-server',
  login: parseInt(process.env.MT5_LOGIN || '12345'),
  password: process.env.MT5_PASSWORD || 'demo-password',
  timeout: 30000,
  retries: 3
};

async function main() {
  console.log('🚀 Starting MT5 Performance Test Suite Examples\n');

  try {
    // Example 1: Quick Trading Performance Test
    console.log('📊 Example 1: Quick Trading Performance Test');
    console.log('============================================');

    const tradingResults = await runQuickTradingTest();
    console.log(`✅ Trading test completed with grade: ${tradingResults.summary.grade}\n`);

    // Example 2: Comprehensive Performance Test
    console.log('🔬 Example 2: Comprehensive Performance Test');
    console.log('=============================================');

    const comprehensiveResults = await runComprehensiveTest();
    console.log(`✅ Comprehensive test completed with grade: ${comprehensiveResults.summary.grade}\n`);

    // Example 3: Stress Test for High-Frequency Trading
    console.log('⚡ Example 3: High-Frequency Trading Stress Test');
    console.log('================================================');

    const stressResults = await runStressTestExample();
    console.log(`✅ Stress test completed with grade: ${stressResults.summary.grade}\n`);

    // Example 4: Custom Test Configuration
    console.log('⚙️  Example 4: Custom Test Configuration');
    console.log('========================================');

    const customResults = await runCustomTest();
    console.log(`✅ Custom test completed with grade: ${customResults.summary.grade}\n`);

    // Example 5: Individual Test Execution
    console.log('🎯 Example 5: Individual Test Execution');
    console.log('=======================================');

    await runIndividualTests();
    console.log('✅ Individual tests completed\n');

    console.log('🎉 All performance test examples completed successfully!');

  } catch (error) {
    console.error('❌ Performance test examples failed:', error);
    process.exit(1);
  }
}

async function runQuickTradingTest(): Promise<TestResults> {
  console.log('Running quick trading performance test...');

  // Use the pre-configured trading suite with hooks integration
  const results = await runTradingPerformanceTest(MT5_CONFIG);

  // Display key metrics
  console.log(`- Total Tests: ${results.summary.totalTests}`);
  console.log(`- Passed: ${results.summary.passedTests}/${results.summary.totalTests}`);
  console.log(`- Overall Score: ${results.summary.overallScore.toFixed(1)}/100`);

  if (results.thresholdViolations.length > 0) {
    console.log(`- ⚠️ Threshold Violations: ${results.thresholdViolations.length}`);
  }

  return results;
}

async function runComprehensiveTest(): Promise<TestResults> {
  console.log('Running comprehensive performance test suite...');

  const suite = new MT5PerformanceTestSuite({
    ...COMPREHENSIVE_PERFORMANCE_SUITE,
    mt5Config: MT5_CONFIG,
    coordination: {
      enabled: true,
      teamMemoryStorage: true,
      realTimeReporting: true
    },
    reporting: {
      generateReports: true,
      exportResults: true,
      compareBaseline: false,
      outputFormats: ['json', 'markdown']
    }
  });

  const results = await suite.runAllTests();

  // Save comprehensive results for team review
  await saveResultsToFile(results, 'comprehensive-test-results.json');

  return results;
}

async function runStressTestExample(): Promise<TestResults> {
  console.log('Running high-frequency trading stress test...');

  // Custom stress test configuration for HFT scenarios
  const hftStressConfig: MT5PerformanceTestConfig = {
    ...STRESS_TEST_SUITE,
    mt5Config: MT5_CONFIG,
    enabledTests: [
      {
        name: 'stress',
        enabled: true,
        priority: 'high',
        tags: ['hft', 'stress', 'scalping'],
        config: {
          duration: 1800000, // 30 minutes
          maxConnections: 100,
          orderVelocity: 20, // 20 orders per second
          tickDataVelocity: 50, // 50 tick requests per second
          errorThreshold: 2, // 2% max error rate
          highFrequencyBursts: {
            enabled: true,
            burstSize: 200,
            burstFrequency: 10, // 10 bursts per minute
            maxConcurrentBursts: 3
          }
        }
      },
      {
        name: 'memory',
        enabled: true,
        priority: 'high',
        tags: ['memory', 'hft'],
        config: {
          duration: 1800000,
          leakDetectionThreshold: 5, // Very strict for HFT
          maxHeapGrowth: 500
        }
      }
    ],
    thresholds: {
      latency: {
        p95: 50, // Very strict latency for HFT
        p99: 100,
        average: 25
      },
      throughput: {
        minimum: 500, // High throughput requirement
        target: 1000
      },
      memory: {
        maxUsage: 1024,
        leakThreshold: 2 // Very strict memory management
      },
      stability: {
        minUptime: 99.9, // High availability requirement
        maxErrorRate: 0.5 // Very low error tolerance
      },
      stress: {
        maxLatencyDegradation: 25, // Max 25% degradation under stress
        minStabilityUnderLoad: 98
      }
    }
  };

  const suite = new MT5PerformanceTestSuite(hftStressConfig);
  const results = await suite.runAllTests();

  // Generate HFT-specific analysis
  await generateHFTAnalysis(results);

  return results;
}

async function runCustomTest(): Promise<TestResults> {
  console.log('Running custom test configuration...');

  // Initialize hooks integration for coordination
  const hooks = createHooksIntegration('CustomPerformanceTest');
  await hooks.initialize();

  const customConfig: MT5PerformanceTestConfig = {
    mt5Config: MT5_CONFIG,
    enabledTests: [
      {
        name: 'latency',
        enabled: true,
        priority: 'high',
        tags: ['custom', 'latency-focused'],
        config: {
          duration: 600000, // 10 minutes
          connectionCount: 5,
          orderTestCount: 200,
          tickDataTestCount: 1000,
          symbols: ['EURUSD', 'GBPUSD'] // Focus on major pairs
        }
      },
      {
        name: 'datafeed',
        enabled: true,
        priority: 'high',
        tags: ['custom', 'data-intensive'],
        config: {
          duration: 900000, // 15 minutes
          symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD'],
          dataFeedPatterns: [
            {
              name: 'CustomHighFrequency',
              description: 'Custom high-frequency pattern',
              symbols: ['EURUSD'],
              frequency: 25, // 25ms
              duration: 300000, // 5 minutes
              concurrent: false,
              expectedThroughput: 40
            }
          ]
        }
      }
    ],
    coordination: {
      enabled: true,
      teamMemoryStorage: true,
      realTimeReporting: false // Disable for custom test
    },
    reporting: {
      generateReports: true,
      exportResults: true,
      compareBaseline: false,
      outputFormats: ['json', 'markdown']
    },
    thresholds: {
      latency: {
        p95: 75, // Custom threshold
        p99: 150,
        average: 35
      },
      throughput: {
        minimum: 150,
        target: 300
      },
      memory: {
        maxUsage: 512,
        leakThreshold: 15
      },
      stability: {
        minUptime: 99.0,
        maxErrorRate: 2
      },
      stress: {
        maxLatencyDegradation: 40,
        minStabilityUnderLoad: 95
      }
    }
  };

  const suite = new MT5PerformanceTestSuite(customConfig);
  const results = await suite.runAllTests();

  // Store custom results with hooks
  await hooks.storeTestResults(results);
  await hooks.shareResults(results, 'Custom MT5 Performance Test Results');
  await hooks.finalize(results);

  return results;
}

async function runIndividualTests(): Promise<void> {
  console.log('Running individual performance tests...');

  const { MT5LatencyTest, MT5ThroughputTest, MT5MemoryTest } = await import('../index');

  // Individual latency test
  console.log('  Running latency test...');
  const latencyTest = new MT5LatencyTest(MT5_CONFIG, {
    duration: 300000,
    orderTestCount: 50,
    tickDataTestCount: 200
  });

  const latencyMetrics = await latencyTest.run();
  console.log(`  ✅ Latency test: P95=${latencyMetrics.latency.p95.toFixed(2)}ms`);

  // Individual throughput test
  console.log('  Running throughput test...');
  const throughputTest = new MT5ThroughputTest(MT5_CONFIG, {
    duration: 300000,
    concurrentConnections: 5,
    testPatterns: ['orders', 'ticks']
  });

  const throughputMetrics = await throughputTest.run();
  console.log(`  ✅ Throughput test: ${throughputMetrics.throughput.requestsPerSecond.toFixed(2)} req/s`);

  // Individual memory test
  console.log('  Running memory test...');
  const memoryTest = new MT5MemoryTest(MT5_CONFIG, {
    duration: 300000,
    memoryMonitoringInterval: 5000,
    leakDetectionThreshold: 20
  });

  const memoryMetrics = await memoryTest.run();
  console.log(`  ✅ Memory test: ${memoryMetrics.memory.heapUsed.toFixed(2)}MB peak`);
}

async function generateHFTAnalysis(results: TestResults): Promise<void> {
  console.log('Generating HFT-specific analysis...');

  const hftAnalysis = {
    suitableForHFT: true,
    latencyGrade: 'A',
    throughputGrade: 'A',
    stabilityGrade: 'A',
    recommendations: [] as string[]
  };

  // Analyze latency for HFT suitability
  for (const [testName, metrics] of results.results) {
    if (metrics.latency.p95 > 50) {
      hftAnalysis.suitableForHFT = false;
      hftAnalysis.latencyGrade = 'C';
      hftAnalysis.recommendations.push('Latency too high for HFT - optimize network and API calls');
    }

    if (metrics.throughput.requestsPerSecond < 500) {
      hftAnalysis.suitableForHFT = false;
      hftAnalysis.throughputGrade = 'C';
      hftAnalysis.recommendations.push('Throughput insufficient for HFT - implement parallel processing');
    }
  }

  // Check for critical violations
  const criticalViolations = results.thresholdViolations.filter(v => v.severity === 'critical');
  if (criticalViolations.length > 0) {
    hftAnalysis.suitableForHFT = false;
    hftAnalysis.recommendations.push('Critical performance issues must be resolved before HFT deployment');
  }

  console.log(`  HFT Suitability: ${hftAnalysis.suitableForHFT ? '✅ Suitable' : '❌ Not Suitable'}`);
  console.log(`  Latency Grade: ${hftAnalysis.latencyGrade}`);
  console.log(`  Throughput Grade: ${hftAnalysis.throughputGrade}`);

  if (hftAnalysis.recommendations.length > 0) {
    console.log('  Recommendations:');
    hftAnalysis.recommendations.forEach(rec => console.log(`    - ${rec}`));
  }

  // Save HFT analysis
  await saveResultsToFile(hftAnalysis, 'hft-analysis.json');
}

async function saveResultsToFile(data: any, filename: string): Promise<void> {
  try {
    const fs = await import('fs').then(m => m.promises);
    const path = await import('path');

    const outputDir = path.join(process.cwd(), 'test-results');

    // Create output directory if it doesn't exist
    try {
      await fs.mkdir(outputDir, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }

    const filePath = path.join(outputDir, filename);
    await fs.writeFile(filePath, JSON.stringify(data, null, 2), 'utf8');

    console.log(`  💾 Results saved to: ${filePath}`);
  } catch (error) {
    console.warn(`  ⚠️ Failed to save results to file: ${error.message}`);
  }
}

// CLI support
if (require.main === module) {
  const args = process.argv.slice(2);
  const testType = args[0] || 'all';

  switch (testType) {
    case 'trading':
      runQuickTradingTest().then(results => {
        console.log(`Trading test completed with grade: ${results.summary.grade}`);
        process.exit(results.summary.grade === 'F' ? 1 : 0);
      }).catch(error => {
        console.error('Trading test failed:', error);
        process.exit(1);
      });
      break;

    case 'comprehensive':
      runComprehensiveTest().then(results => {
        console.log(`Comprehensive test completed with grade: ${results.summary.grade}`);
        process.exit(results.summary.grade === 'F' ? 1 : 0);
      }).catch(error => {
        console.error('Comprehensive test failed:', error);
        process.exit(1);
      });
      break;

    case 'stress':
      runStressTestExample().then(results => {
        console.log(`Stress test completed with grade: ${results.summary.grade}`);
        process.exit(results.summary.grade === 'F' ? 1 : 0);
      }).catch(error => {
        console.error('Stress test failed:', error);
        process.exit(1);
      });
      break;

    case 'custom':
      runCustomTest().then(results => {
        console.log(`Custom test completed with grade: ${results.summary.grade}`);
        process.exit(results.summary.grade === 'F' ? 1 : 0);
      }).catch(error => {
        console.error('Custom test failed:', error);
        process.exit(1);
      });
      break;

    default:
      main().catch(error => {
        console.error('Performance test suite failed:', error);
        process.exit(1);
      });
  }
}

export {
  runQuickTradingTest,
  runComprehensiveTest,
  runStressTestExample,
  runCustomTest,
  runIndividualTests,
  generateHFTAnalysis
};