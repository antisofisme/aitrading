/**
 * ChainMetrics
 * Data model for chain health metrics
 */

export class ChainMetrics {
  constructor({
    chainId,
    timestamp = new Date(),
    totalRequests = 0,
    avgDuration = 0,
    p50Duration = 0,
    p95Duration = 0,
    p99Duration = 0,
    errorRate = 0,
    errorCount = 0,
    dependencyFailureRate = 0,
    bottleneckServices = [],
    healthScore = 100,
    events = [],
    metadata = {}
  }) {
    this.chainId = chainId;
    this.timestamp = timestamp;
    this.totalRequests = totalRequests;
    this.avgDuration = avgDuration;
    this.p50Duration = p50Duration;
    this.p95Duration = p95Duration;
    this.p99Duration = p99Duration;
    this.errorRate = errorRate;
    this.errorCount = errorCount;
    this.dependencyFailureRate = dependencyFailureRate;
    this.bottleneckServices = bottleneckServices;
    this.healthScore = healthScore;
    this.events = events;
    this.metadata = metadata;

    // Calculated fields
    this.performanceCategory = this.calculatePerformanceCategory();
    this.errorCategory = this.calculateErrorCategory();
    this.overallStatus = this.calculateOverallStatus();
  }

  calculatePerformanceCategory() {
    if (this.p99Duration > 10000) return 'critical';
    if (this.p99Duration > 5000) return 'degraded';
    if (this.p99Duration > 2000) return 'slow';
    return 'good';
  }

  calculateErrorCategory() {
    if (this.errorRate > 0.05) return 'critical';
    if (this.errorRate > 0.02) return 'high';
    if (this.errorRate > 0.01) return 'elevated';
    return 'normal';
  }

  calculateOverallStatus() {
    if (this.healthScore < 50) return 'critical';
    if (this.healthScore < 70) return 'degraded';
    if (this.healthScore < 90) return 'warning';
    return 'healthy';
  }

  toJSON() {
    return {
      chainId: this.chainId,
      timestamp: this.timestamp,
      totalRequests: this.totalRequests,
      avgDuration: this.avgDuration,
      p50Duration: this.p50Duration,
      p95Duration: this.p95Duration,
      p99Duration: this.p99Duration,
      errorRate: this.errorRate,
      errorCount: this.errorCount,
      dependencyFailureRate: this.dependencyFailureRate,
      bottleneckServices: this.bottleneckServices,
      healthScore: this.healthScore,
      performanceCategory: this.performanceCategory,
      errorCategory: this.errorCategory,
      overallStatus: this.overallStatus,
      eventCount: this.events.length,
      metadata: this.metadata
    };
  }
}