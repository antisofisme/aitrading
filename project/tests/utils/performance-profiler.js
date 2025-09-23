/**
 * Performance Profiler
 * Profiles system performance during testing with detailed metrics
 */

class PerformanceProfiler {
  constructor() {
    this.isRunning = false;
    this.startTime = null;
    this.endTime = null;
    this.memorySnapshots = [];
    this.cpuUsage = [];
    this.profileData = {
      operations: [],
      bottlenecks: [],
      resourceUsage: []
    };
  }

  start() {
    this.isRunning = true;
    this.startTime = process.hrtime.bigint();
    this.memorySnapshots = [];
    this.cpuUsage = [];
    this.profileData = {
      operations: [],
      bottlenecks: [],
      resourceUsage: []
    };

    // Start memory monitoring
    this.memoryMonitor = setInterval(() => {
      if (this.isRunning) {
        this.captureMemorySnapshot();
      }
    }, 100); // Every 100ms

    console.log('🔧 Performance profiler started');
  }

  stop() {
    this.isRunning = false;
    this.endTime = process.hrtime.bigint();

    if (this.memoryMonitor) {
      clearInterval(this.memoryMonitor);
    }

    console.log('🔧 Performance profiler stopped');
    return this.generateReport();
  }

  captureMemorySnapshot() {
    const memUsage = process.memoryUsage();
    const timestamp = Date.now();

    this.memorySnapshots.push({
      timestamp,
      heapUsed: memUsage.heapUsed,
      heapTotal: memUsage.heapTotal,
      external: memUsage.external,
      rss: memUsage.rss
    });

    // Keep only last 1000 snapshots
    if (this.memorySnapshots.length > 1000) {
      this.memorySnapshots.shift();
    }
  }

  profileOperation(name, operation) {
    return async (...args) => {
      const startTime = process.hrtime.bigint();
      const startMemory = process.memoryUsage();

      let result;
      let error = null;

      try {
        result = await operation(...args);
      } catch (err) {
        error = err;
        throw err;
      } finally {
        const endTime = process.hrtime.bigint();
        const endMemory = process.memoryUsage();

        const operationData = {
          name,
          duration: Number(endTime - startTime) / 1000000, // Convert to milliseconds
          memoryDelta: endMemory.heapUsed - startMemory.heapUsed,
          success: error === null,
          error: error ? error.message : null,
          timestamp: Date.now()
        };

        this.profileData.operations.push(operationData);

        // Detect potential bottlenecks
        if (operationData.duration > 100) { // >100ms
          this.profileData.bottlenecks.push({
            operation: name,
            duration: operationData.duration,
            type: 'latency',
            timestamp: operationData.timestamp
          });
        }

        if (operationData.memoryDelta > 10 * 1024 * 1024) { // >10MB
          this.profileData.bottlenecks.push({
            operation: name,
            memoryDelta: operationData.memoryDelta,
            type: 'memory',
            timestamp: operationData.timestamp
          });
        }
      }

      return result;
    };
  }

  analyzeBottlenecks() {
    const operationsByName = new Map();

    // Group operations by name
    this.profileData.operations.forEach(op => {
      if (!operationsByName.has(op.name)) {
        operationsByName.set(op.name, []);
      }
      operationsByName.get(op.name).push(op);
    });

    const analysis = [];

    operationsByName.forEach((operations, name) => {
      const durations = operations.map(op => op.duration);
      const memoryDeltas = operations.map(op => op.memoryDelta);

      const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
      const maxDuration = Math.max(...durations);
      const avgMemoryDelta = memoryDeltas.reduce((a, b) => a + b, 0) / memoryDeltas.length;

      analysis.push({
        operation: name,
        count: operations.length,
        averageDuration: avgDuration,
        maxDuration: maxDuration,
        averageMemoryDelta: avgMemoryDelta,
        successRate: (operations.filter(op => op.success).length / operations.length) * 100
      });
    });

    return analysis.sort((a, b) => b.averageDuration - a.averageDuration);
  }

  analyzeMemoryUsage() {
    if (this.memorySnapshots.length === 0) {
      return null;
    }

    const heapUsages = this.memorySnapshots.map(snap => snap.heapUsed);
    const heapTotals = this.memorySnapshots.map(snap => snap.heapTotal);

    return {
      peak: {
        heapUsed: Math.max(...heapUsages),
        heapTotal: Math.max(...heapTotals)
      },
      average: {
        heapUsed: heapUsages.reduce((a, b) => a + b, 0) / heapUsages.length,
        heapTotal: heapTotals.reduce((a, b) => a + b, 0) / heapTotals.length
      },
      trend: this.calculateMemoryTrend(),
      snapshots: this.memorySnapshots.length
    };
  }

  calculateMemoryTrend() {
    if (this.memorySnapshots.length < 2) {
      return 'insufficient_data';
    }

    const first = this.memorySnapshots[0].heapUsed;
    const last = this.memorySnapshots[this.memorySnapshots.length - 1].heapUsed;
    const change = ((last - first) / first) * 100;

    if (change > 10) return 'increasing';
    if (change < -10) return 'decreasing';
    return 'stable';
  }

  generateReport() {
    if (!this.startTime || !this.endTime) {
      return null;
    }

    const totalDuration = Number(this.endTime - this.startTime) / 1000000; // milliseconds
    const bottleneckAnalysis = this.analyzeBottlenecks();
    const memoryAnalysis = this.analyzeMemoryUsage();

    return {
      summary: {
        totalDuration,
        operationsProfiled: this.profileData.operations.length,
        bottlenecksDetected: this.profileData.bottlenecks.length,
        memorySnapshotsTaken: this.memorySnapshots.length
      },
      operations: bottleneckAnalysis,
      bottlenecks: this.profileData.bottlenecks,
      memory: memoryAnalysis,
      recommendations: this.generateRecommendations(bottleneckAnalysis, memoryAnalysis)
    };
  }

  generateRecommendations(bottleneckAnalysis, memoryAnalysis) {
    const recommendations = [];

    // Performance recommendations
    const slowOperations = bottleneckAnalysis.filter(op => op.averageDuration > 50);
    if (slowOperations.length > 0) {
      recommendations.push({
        type: 'performance',
        priority: 'high',
        issue: 'Slow operations detected',
        operations: slowOperations.map(op => op.operation),
        suggestion: 'Consider optimizing these operations or implementing caching'
      });
    }

    // Memory recommendations
    if (memoryAnalysis && memoryAnalysis.trend === 'increasing') {
      recommendations.push({
        type: 'memory',
        priority: 'medium',
        issue: 'Memory usage trending upward',
        suggestion: 'Monitor for potential memory leaks and implement garbage collection optimization'
      });
    }

    // Success rate recommendations
    const failingOperations = bottleneckAnalysis.filter(op => op.successRate < 95);
    if (failingOperations.length > 0) {
      recommendations.push({
        type: 'reliability',
        priority: 'high',
        issue: 'Operations with low success rates',
        operations: failingOperations.map(op => op.operation),
        suggestion: 'Implement better error handling and retry mechanisms'
      });
    }

    return recommendations;
  }

  getProfiledFunction(name, fn) {
    return this.profileOperation(name, fn);
  }
}

module.exports = PerformanceProfiler;