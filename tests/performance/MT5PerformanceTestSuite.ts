import { PerformanceTestRunner, PerformanceMetrics } from './infrastructure/PerformanceTestBase';
import { MT5ConnectionConfig } from './infrastructure/MT5TestHelper';
import { MT5LatencyTest } from './latency/MT5LatencyTest';
import { MT5ThroughputTest } from './throughput/MT5ThroughputTest';
import { MT5StressTest } from './stress/MT5StressTest';
import { MT5MemoryTest } from './memory/MT5MemoryTest';
import { MT5LoadTest } from './load/MT5LoadTest';
import { MT5BenchmarkSuite } from './benchmarks/MT5BenchmarkSuite';
import { MT5DataFeedTest } from './datafeed/MT5DataFeedTest';
import { MT5StabilityTest } from './stability/MT5StabilityTest';
import { HooksIntegration, PerformanceTestCoordinator, createHooksIntegration } from './utils/HooksIntegration';

export interface MT5PerformanceTestConfig {
  mt5Config: MT5ConnectionConfig;
  enabledTests: TestSuite[];
  coordination: {
    enabled: boolean;
    teamMemoryStorage: boolean;
    realTimeReporting: boolean;
    slackNotifications?: boolean;
  };
  reporting: {
    generateReports: boolean;
    exportResults: boolean;
    compareBaseline: boolean;
    outputFormats: ('json' | 'html' | 'markdown' | 'csv')[];
  };
  thresholds: PerformanceThresholds;
}

export interface TestSuite {
  name: string;
  enabled: boolean;
  config?: any;
  priority: 'high' | 'medium' | 'low';
  tags: string[];
}

export interface PerformanceThresholds {
  latency: {
    p95: number; // milliseconds
    p99: number;
    average: number;
  };
  throughput: {
    minimum: number; // requests per second
    target: number;
  };
  memory: {
    maxUsage: number; // MB
    leakThreshold: number; // MB per minute
  };
  stability: {
    minUptime: number; // percentage
    maxErrorRate: number; // percentage
  };
  stress: {
    maxLatencyDegradation: number; // percentage
    minStabilityUnderLoad: number; // percentage
  };
}

export interface TestResults {
  summary: TestSummary;
  results: Map<string, PerformanceMetrics>;
  reports: Map<string, string>;
  thresholdViolations: ThresholdViolation[];
  recommendations: string[];
}

export interface TestSummary {
  totalTests: number;
  passedTests: number;
  failedTests: number;
  duration: number;
  overallScore: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  timestamp: number;
}

export interface ThresholdViolation {
  testName: string;
  metric: string;
  expected: number;
  actual: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export class MT5PerformanceTestSuite {
  private config: MT5PerformanceTestConfig;
  private coordinator: PerformanceTestCoordinator;
  private testRunner: PerformanceTestRunner;
  private hooks: HooksIntegration;
  private results: Map<string, PerformanceMetrics> = new Map();
  private reports: Map<string, string> = new Map();
  private thresholdViolations: ThresholdViolation[] = [];

  constructor(config: MT5PerformanceTestConfig) {
    this.config = config;
    this.testRunner = new PerformanceTestRunner();
    this.coordinator = new PerformanceTestCoordinator();
    this.hooks = createHooksIntegration('MT5PerformanceTestSuite');
  }

  public async runAllTests(): Promise<TestResults> {
    console.log('🚀 Starting MT5 Performance Test Suite...');

    // Initialize coordination and hooks
    await this.initializeTestSuite();

    try {
      // Setup all enabled tests
      await this.setupTests();

      // Execute tests based on priority
      await this.executeTestsByPriority();

      // Analyze results and generate reports
      const testResults = await this.analyzeAndReport();

      // Share results with team if coordination is enabled
      if (this.config.coordination.enabled) {
        await this.shareResultsWithTeam(testResults);
      }

      // Finalize and cleanup
      await this.finalizeTestSuite(testResults);

      return testResults;

    } catch (error) {
      await this.hooks.notifyError(error, { phase: 'test_execution' });
      throw error;
    }
  }

  private async initializeTestSuite(): Promise<void> {
    console.log('Initializing test suite coordination...');

    // Initialize hooks integration
    await this.hooks.initialize();
    await this.hooks.notifyProgress('MT5 Performance Test Suite starting');

    // Initialize coordination if enabled
    if (this.config.coordination.enabled) {
      await this.coordinator.initializeCoordination();
    }

    // Store test configuration in memory for team access
    await this.hooks.storeMetric('test_config', this.config, 'performance/config');

    console.log('Test suite initialization completed');
  }

  private async setupTests(): Promise<void> {
    console.log('Setting up performance tests...');

    for (const testSuite of this.config.enabledTests) {
      if (!testSuite.enabled) continue;

      let test;

      switch (testSuite.name) {
        case 'latency':
          test = new MT5LatencyTest(this.config.mt5Config, testSuite.config);
          break;
        case 'throughput':
          test = new MT5ThroughputTest(this.config.mt5Config, testSuite.config);
          break;
        case 'stress':
          test = new MT5StressTest(this.config.mt5Config, testSuite.config);
          break;
        case 'memory':
          test = new MT5MemoryTest(this.config.mt5Config, testSuite.config);
          break;
        case 'load':
          test = new MT5LoadTest(this.config.mt5Config, testSuite.config);
          break;
        case 'benchmark':
          test = new MT5BenchmarkSuite(this.config.mt5Config, testSuite.config);
          break;
        case 'datafeed':
          test = new MT5DataFeedTest(this.config.mt5Config, testSuite.config);
          break;
        case 'stability':
          test = new MT5StabilityTest(this.config.mt5Config, testSuite.config);
          break;
        default:
          console.warn(`Unknown test suite: ${testSuite.name}`);
          continue;
      }

      // Setup test event listeners for coordination
      this.setupTestEventListeners(test, testSuite.name);

      // Register test with coordinator
      if (this.config.coordination.enabled) {
        await this.coordinator.registerTest(testSuite.name);
      }

      this.testRunner.addTest(testSuite.name, test);
      console.log(`✅ Set up ${testSuite.name} test`);
    }

    await this.hooks.notifyProgress(`Set up ${this.config.enabledTests.filter(t => t.enabled).length} tests`);
  }

  private setupTestEventListeners(test: any, testName: string): void {
    // Listen to test events and coordinate through hooks
    test.on('testStarting', async (config: any) => {
      await this.hooks.notifyProgress(`${testName} test starting`);
      await this.hooks.storeMetric(`${testName}_start_time`, Date.now());
    });

    test.on('testCompleted', async (metrics: PerformanceMetrics) => {
      await this.hooks.notifyProgress(`${testName} test completed`);
      await this.hooks.storeMetric(`${testName}_metrics`, metrics);

      // Check thresholds immediately
      this.checkThresholds(testName, metrics);
    });

    test.on('memoryThresholdExceeded', async (data: any) => {
      await this.hooks.notifyError(`Memory threshold exceeded in ${testName}`, data);
    });

    test.on('latencyThresholdExceeded', async (data: any) => {
      await this.hooks.notifyError(`Latency threshold exceeded in ${testName}`, data);
    });

    test.on('memoryLeakDetected', async (data: any) => {
      await this.hooks.notifyError(`Memory leak detected in ${testName}`, data);
    });

    test.on('connectionFailed', async (data: any) => {
      await this.hooks.notifyError(`Connection failed in ${testName}`, data);
    });

    test.on('progress', async (data: any) => {
      if (this.config.coordination.realTimeReporting) {
        await this.hooks.reportMetrics({
          testName,
          progress: data,
          timestamp: Date.now()
        });
      }
    });
  }

  private async executeTestsByPriority(): Promise<void> {
    console.log('Executing tests by priority...');

    // Group tests by priority
    const highPriorityTests = this.config.enabledTests.filter(t => t.enabled && t.priority === 'high');
    const mediumPriorityTests = this.config.enabledTests.filter(t => t.enabled && t.priority === 'medium');
    const lowPriorityTests = this.config.enabledTests.filter(t => t.enabled && t.priority === 'low');

    // Execute high priority tests first (critical for trading systems)
    for (const testSuite of highPriorityTests) {
      await this.executeTest(testSuite.name, 'high');
    }

    // Execute medium priority tests
    for (const testSuite of mediumPriorityTests) {
      await this.executeTest(testSuite.name, 'medium');
    }

    // Execute low priority tests
    for (const testSuite of lowPriorityTests) {
      await this.executeTest(testSuite.name, 'low');
    }
  }

  private async executeTest(testName: string, priority: string): Promise<void> {
    console.log(`🧪 Executing ${testName} test (${priority} priority)...`);

    try {
      const startTime = performance.now();

      await this.hooks.notifyProgress(`Starting ${testName} test`);

      const metrics = await this.testRunner.runTest(testName);
      this.results.set(testName, metrics);

      const duration = performance.now() - startTime;

      console.log(`✅ ${testName} test completed in ${(duration / 1000).toFixed(2)}s`);

      // Store results immediately for real-time access
      await this.hooks.storeMetric(`${testName}_results`, {
        metrics,
        duration,
        timestamp: Date.now()
      });

      // Check thresholds and notify if violated
      this.checkThresholds(testName, metrics);

    } catch (error) {
      console.error(`❌ ${testName} test failed:`, error);
      await this.hooks.notifyError(`${testName} test failed`, error);
      throw error;
    }
  }

  private checkThresholds(testName: string, metrics: PerformanceMetrics): void {
    const thresholds = this.config.thresholds;

    // Check latency thresholds
    if (metrics.latency.p95 > thresholds.latency.p95) {
      this.thresholdViolations.push({
        testName,
        metric: 'latency_p95',
        expected: thresholds.latency.p95,
        actual: metrics.latency.p95,
        severity: metrics.latency.p95 > thresholds.latency.p95 * 1.5 ? 'critical' : 'high'
      });
    }

    // Check throughput thresholds
    if (metrics.throughput.requestsPerSecond < thresholds.throughput.minimum) {
      this.thresholdViolations.push({
        testName,
        metric: 'throughput',
        expected: thresholds.throughput.minimum,
        actual: metrics.throughput.requestsPerSecond,
        severity: metrics.throughput.requestsPerSecond < thresholds.throughput.minimum * 0.5 ? 'critical' : 'high'
      });
    }

    // Check memory thresholds
    if (metrics.memory.heapUsed > thresholds.memory.maxUsage) {
      this.thresholdViolations.push({
        testName,
        metric: 'memory_usage',
        expected: thresholds.memory.maxUsage,
        actual: metrics.memory.heapUsed,
        severity: metrics.memory.heapUsed > thresholds.memory.maxUsage * 1.5 ? 'critical' : 'medium'
      });
    }

    // Notify team of critical violations immediately
    const criticalViolations = this.thresholdViolations.filter(v => v.severity === 'critical');
    if (criticalViolations.length > 0) {
      this.hooks.notifyError(`Critical performance threshold violations in ${testName}`, criticalViolations);
    }
  }

  private async analyzeAndReport(): Promise<TestResults> {
    console.log('Analyzing results and generating reports...');

    // Generate individual test reports
    for (const [testName, metrics] of this.results) {
      const report = await this.generateTestReport(testName, metrics);
      this.reports.set(testName, report);
    }

    // Generate comprehensive summary report
    const summaryReport = this.generateSummaryReport();
    this.reports.set('summary', summaryReport);

    // Calculate overall test summary
    const summary = this.calculateTestSummary();

    // Generate recommendations based on results
    const recommendations = this.generateRecommendations();

    await this.hooks.notifyProgress('Analysis and reporting completed');

    return {
      summary,
      results: this.results,
      reports: this.reports,
      thresholdViolations: this.thresholdViolations,
      recommendations
    };
  }

  private async generateTestReport(testName: string, metrics: PerformanceMetrics): Promise<string> {
    let report = `# ${testName.toUpperCase()} Performance Test Report\n\n`;

    report += `**Test Completed:** ${new Date().toISOString()}\n\n`;

    report += `## Performance Metrics\n\n`;
    report += `### Latency\n`;
    report += `- **Average:** ${metrics.latency.avg.toFixed(2)}ms\n`;
    report += `- **P50:** ${metrics.latency.p50.toFixed(2)}ms\n`;
    report += `- **P95:** ${metrics.latency.p95.toFixed(2)}ms\n`;
    report += `- **P99:** ${metrics.latency.p99.toFixed(2)}ms\n`;
    report += `- **Min/Max:** ${metrics.latency.min.toFixed(2)}ms / ${metrics.latency.max.toFixed(2)}ms\n\n`;

    report += `### Throughput\n`;
    report += `- **Requests/Second:** ${metrics.throughput.requestsPerSecond.toFixed(2)}\n`;
    report += `- **Total Requests:** ${metrics.throughput.totalRequests.toLocaleString()}\n`;
    report += `- **Duration:** ${(metrics.throughput.duration / 1000).toFixed(2)}s\n\n`;

    report += `### Memory Usage\n`;
    report += `- **Heap Used:** ${metrics.memory.heapUsed.toFixed(2)}MB\n`;
    report += `- **RSS:** ${metrics.memory.rss.toFixed(2)}MB\n`;
    report += `- **External:** ${metrics.memory.external.toFixed(2)}MB\n\n`;

    if (metrics.errors.count > 0) {
      report += `### Errors\n`;
      report += `- **Total Errors:** ${metrics.errors.count}\n`;
      report += `- **Error Types:**\n`;
      for (const [errorType, count] of Object.entries(metrics.errors.types)) {
        report += `  - ${errorType}: ${count}\n`;
      }
      report += '\n';
    }

    // Check against thresholds
    const violations = this.thresholdViolations.filter(v => v.testName === testName);
    if (violations.length > 0) {
      report += `### ⚠️ Threshold Violations\n\n`;
      for (const violation of violations) {
        report += `- **${violation.metric}:** Expected ≤ ${violation.expected}, Actual: ${violation.actual.toFixed(2)} (${violation.severity})\n`;
      }
      report += '\n';
    }

    return report;
  }

  private generateSummaryReport(): string {
    let report = `# MT5 Performance Test Suite - Summary Report\n\n`;

    report += `**Test Suite Completed:** ${new Date().toISOString()}\n\n`;

    const summary = this.calculateTestSummary();

    report += `## Overall Results\n\n`;
    report += `- **Total Tests:** ${summary.totalTests}\n`;
    report += `- **Passed:** ${summary.passedTests}\n`;
    report += `- **Failed:** ${summary.failedTests}\n`;
    report += `- **Success Rate:** ${((summary.passedTests / summary.totalTests) * 100).toFixed(1)}%\n`;
    report += `- **Overall Score:** ${summary.overallScore.toFixed(1)}/100\n`;
    report += `- **Grade:** ${summary.grade}\n`;
    report += `- **Total Duration:** ${(summary.duration / 1000 / 60).toFixed(1)} minutes\n\n`;

    // Threshold violations summary
    if (this.thresholdViolations.length > 0) {
      report += `## ⚠️ Performance Issues\n\n`;

      const criticalViolations = this.thresholdViolations.filter(v => v.severity === 'critical');
      const highViolations = this.thresholdViolations.filter(v => v.severity === 'high');

      if (criticalViolations.length > 0) {
        report += `### 🚨 Critical Issues (${criticalViolations.length})\n`;
        for (const violation of criticalViolations) {
          report += `- **${violation.testName}:** ${violation.metric} significantly exceeds threshold\n`;
        }
        report += '\n';
      }

      if (highViolations.length > 0) {
        report += `### ⚠️ High Priority Issues (${highViolations.length})\n`;
        for (const violation of highViolations) {
          report += `- **${violation.testName}:** ${violation.metric} exceeds acceptable limits\n`;
        }
        report += '\n';
      }
    }

    // Test-specific summaries
    report += `## Test Results Summary\n\n`;
    for (const [testName, metrics] of this.results) {
      const passed = this.thresholdViolations.filter(v => v.testName === testName && v.severity === 'critical').length === 0;
      report += `### ${testName.toUpperCase()} ${passed ? '✅' : '❌'}\n`;
      report += `- **Avg Latency:** ${metrics.latency.avg.toFixed(2)}ms\n`;
      report += `- **Throughput:** ${metrics.throughput.requestsPerSecond.toFixed(2)} req/s\n`;
      report += `- **Memory Usage:** ${metrics.memory.heapUsed.toFixed(2)}MB\n`;
      report += `- **Errors:** ${metrics.errors.count}\n\n`;
    }

    return report;
  }

  private calculateTestSummary(): TestSummary {
    const totalTests = this.results.size;
    const criticalFailures = new Set(
      this.thresholdViolations.filter(v => v.severity === 'critical').map(v => v.testName)
    ).size;
    const passedTests = totalTests - criticalFailures;

    // Calculate overall score based on multiple factors
    let score = 100;

    // Penalize for failures
    score -= (criticalFailures / totalTests) * 50;

    // Penalize for high/medium violations
    const highViolations = this.thresholdViolations.filter(v => v.severity === 'high').length;
    const mediumViolations = this.thresholdViolations.filter(v => v.severity === 'medium').length;

    score -= (highViolations * 5) + (mediumViolations * 2);

    // Bonus for excellent performance
    const excellentTests = Array.from(this.results.values()).filter(metrics =>
      metrics.latency.p95 < this.config.thresholds.latency.p95 * 0.5 &&
      metrics.throughput.requestsPerSecond > this.config.thresholds.throughput.target
    ).length;

    score += (excellentTests / totalTests) * 10;

    score = Math.max(0, Math.min(100, score));

    // Assign grade
    let grade: 'A' | 'B' | 'C' | 'D' | 'F';
    if (score >= 90) grade = 'A';
    else if (score >= 80) grade = 'B';
    else if (score >= 70) grade = 'C';
    else if (score >= 60) grade = 'D';
    else grade = 'F';

    return {
      totalTests,
      passedTests,
      failedTests: criticalFailures,
      duration: 0, // Will be calculated elsewhere
      overallScore: score,
      grade,
      timestamp: Date.now()
    };
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    // Analyze violations and generate specific recommendations
    const latencyIssues = this.thresholdViolations.filter(v => v.metric.includes('latency'));
    const throughputIssues = this.thresholdViolations.filter(v => v.metric.includes('throughput'));
    const memoryIssues = this.thresholdViolations.filter(v => v.metric.includes('memory'));

    if (latencyIssues.length > 0) {
      recommendations.push('High latency detected - Consider optimizing MT5 API calls and network configuration');
      recommendations.push('Review connection pooling and implement connection keep-alive mechanisms');
    }

    if (throughputIssues.length > 0) {
      recommendations.push('Low throughput detected - Consider implementing parallel processing and request batching');
      recommendations.push('Optimize database queries and consider caching frequently accessed data');
    }

    if (memoryIssues.length > 0) {
      recommendations.push('High memory usage detected - Implement proper object disposal and garbage collection');
      recommendations.push('Review data structures and consider memory-efficient alternatives');
    }

    const errorRates = Array.from(this.results.values()).map(m =>
      (m.errors.count / Math.max(1, m.throughput.totalRequests)) * 100
    );
    const avgErrorRate = errorRates.reduce((a, b) => a + b, 0) / errorRates.length;

    if (avgErrorRate > 5) {
      recommendations.push('High error rate detected - Implement robust error handling and retry mechanisms');
      recommendations.push('Monitor MT5 server health and implement circuit breaker patterns');
    }

    // Add general recommendations
    if (this.thresholdViolations.filter(v => v.severity === 'critical').length > 0) {
      recommendations.push('Critical performance issues detected - Immediate optimization required before production');
    }

    if (recommendations.length === 0) {
      recommendations.push('Excellent performance - System meets all requirements for production deployment');
    }

    return recommendations;
  }

  private async shareResultsWithTeam(testResults: TestResults): Promise<void> {
    console.log('Sharing results with team...');

    try {
      // Share comprehensive results
      await this.hooks.shareResults(testResults, 'MT5 Performance Test Suite Results');

      // Share individual test results for detailed analysis
      for (const [testName, metrics] of testResults.results) {
        await this.hooks.storeMetric(`${testName}_detailed_results`, {
          metrics,
          report: testResults.reports.get(testName),
          violations: testResults.thresholdViolations.filter(v => v.testName === testName)
        }, 'performance/detailed');
      }

      // Store recommendations for team review
      await this.hooks.storeMetric('recommendations', testResults.recommendations, 'performance/recommendations');

      console.log('✅ Results shared with team successfully');

    } catch (error) {
      console.warn('Failed to share results with team:', error);
    }
  }

  private async finalizeTestSuite(testResults: TestResults): Promise<void> {
    console.log('Finalizing test suite...');

    try {
      // Generate final summary for coordination
      const finalSummary = {
        testSuite: 'MT5PerformanceTestSuite',
        results: testResults,
        timestamp: Date.now(),
        configuration: this.config
      };

      // Finalize hooks integration
      await this.hooks.finalize(finalSummary);

      // Finalize coordination if enabled
      if (this.config.coordination.enabled) {
        await this.coordinator.finalizeCoordination(finalSummary);
      }

      console.log('🎉 MT5 Performance Test Suite completed successfully!');
      console.log(`Overall Grade: ${testResults.summary.grade} (${testResults.summary.overallScore.toFixed(1)}/100)`);

    } catch (error) {
      console.warn('Failed to finalize test suite:', error);
    }
  }

  // Public methods for external access
  public async runSpecificTest(testName: string): Promise<PerformanceMetrics> {
    await this.initializeTestSuite();
    await this.setupTests();
    return await this.testRunner.runTest(testName);
  }

  public getResults(): Map<string, PerformanceMetrics> {
    return new Map(this.results);
  }

  public getReports(): Map<string, string> {
    return new Map(this.reports);
  }

  public getThresholdViolations(): ThresholdViolation[] {
    return [...this.thresholdViolations];
  }

  public getHooksIntegration(): HooksIntegration {
    return this.hooks;
  }
}