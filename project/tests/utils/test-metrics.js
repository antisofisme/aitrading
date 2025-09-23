/**
 * Test Metrics Collector
 * Collects and analyzes performance metrics during testing
 */

class TestMetrics {
  constructor() {
    this.reset();
  }

  reset() {
    this.dataProcessingTimes = [];
    this.aiDecisionTimes = [];
    this.errorCounts = {
      dataValidation: 0,
      aiDecisions: 0,
      networkErrors: 0
    };
    this.throughputMetrics = {
      ticksProcessed: 0,
      decisionsGenerated: 0,
      startTime: Date.now()
    };
  }

  recordDataProcessing(processingTime) {
    this.dataProcessingTimes.push(processingTime);
    this.throughputMetrics.ticksProcessed++;
  }

  recordAIDecision(decisionTime) {
    this.aiDecisionTimes.push(decisionTime);
    this.throughputMetrics.decisionsGenerated++;
  }

  recordError(errorType) {
    if (this.errorCounts[errorType] !== undefined) {
      this.errorCounts[errorType]++;
    }
  }

  getAverageDataProcessingTime() {
    if (this.dataProcessingTimes.length === 0) return 0;
    return this.dataProcessingTimes.reduce((a, b) => a + b, 0) / this.dataProcessingTimes.length;
  }

  getAverageAIDecisionTime() {
    if (this.aiDecisionTimes.length === 0) return 0;
    return this.aiDecisionTimes.reduce((a, b) => a + b, 0) / this.aiDecisionTimes.length;
  }

  getPercentile(times, percentile) {
    if (times.length === 0) return 0;
    const sorted = [...times].sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index];
  }

  getThroughputMetrics() {
    const elapsedTime = (Date.now() - this.throughputMetrics.startTime) / 1000; // seconds
    return {
      ticksPerSecond: this.throughputMetrics.ticksProcessed / elapsedTime,
      decisionsPerSecond: this.throughputMetrics.decisionsGenerated / elapsedTime,
      totalTicks: this.throughputMetrics.ticksProcessed,
      totalDecisions: this.throughputMetrics.decisionsGenerated,
      elapsedTime
    };
  }

  getPerformanceReport() {
    const throughput = this.getThroughputMetrics();

    return {
      dataProcessing: {
        average: this.getAverageDataProcessingTime(),
        p95: this.getPercentile(this.dataProcessingTimes, 95),
        p99: this.getPercentile(this.dataProcessingTimes, 99),
        min: Math.min(...this.dataProcessingTimes),
        max: Math.max(...this.dataProcessingTimes),
        count: this.dataProcessingTimes.length
      },
      aiDecisions: {
        average: this.getAverageAIDecisionTime(),
        p95: this.getPercentile(this.aiDecisionTimes, 95),
        p99: this.getPercentile(this.aiDecisionTimes, 99),
        min: Math.min(...this.aiDecisionTimes),
        max: Math.max(...this.aiDecisionTimes),
        count: this.aiDecisionTimes.length
      },
      throughput,
      errors: this.errorCounts,
      totalErrors: Object.values(this.errorCounts).reduce((a, b) => a + b, 0)
    };
  }

  isPerformanceTargetMet(targets) {
    const report = this.getPerformanceReport();

    return {
      dataProcessingTarget: report.dataProcessing.average <= targets.maxDataProcessingMs,
      aiDecisionTarget: report.aiDecisions.average <= targets.maxAIDecisionMs,
      throughputTarget: report.throughput.ticksPerSecond >= targets.minTicksPerSecond,
      errorRateTarget: report.totalErrors / Math.max(report.dataProcessing.count, 1) <= targets.maxErrorRate
    };
  }
}

module.exports = TestMetrics;