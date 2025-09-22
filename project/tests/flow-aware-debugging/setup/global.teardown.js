/**
 * Global Teardown for Flow-Aware Error Handling Tests
 * Cleans up test infrastructure and generates final reports
 */

const fs = require('fs').promises;
const path = require('path');

module.exports = async () => {
  console.log('🧹 Starting Flow-Aware Error Handling Test Teardown...');

  try {
    // Generate test reports
    await generateTestReports();

    // Cleanup test infrastructure
    await cleanupTestInfrastructure();

    // Archive test artifacts
    await archiveTestArtifacts();

    // Cleanup temporary files
    await cleanupTemporaryFiles();

    // Generate performance summary
    await generatePerformanceSummary();

    // Cleanup memory and resources
    await cleanupMemoryAndResources();

    console.log('✅ Flow-Aware Error Handling Test Teardown Complete');

  } catch (error) {
    console.error('❌ Error during teardown:', error);
    // Don't throw to avoid masking test failures
  }
};

async function generateTestReports() {
  try {
    const reportsDir = path.join(__dirname, '..', 'reports');

    // Ensure reports directory exists
    try {
      await fs.mkdir(reportsDir, { recursive: true });
    } catch (e) {
      // Directory might already exist
    }

    // Generate test execution summary
    const testSummary = {
      timestamp: new Date().toISOString(),
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage()
      },
      configuration: {
        nodeEnv: process.env.NODE_ENV,
        testTimeout: process.env.TEST_TIMEOUT,
        performanceMonitoring: process.env.PERFORMANCE_MONITORING
      },
      statistics: {
        totalServices: global.testServices ? global.testServices.size : 0,
        totalFlows: global.testFlows ? global.testFlows.size : 0,
        totalErrors: global.testErrors ? global.testErrors.size : 0,
        totalMetrics: global.testMetrics ?
          (global.testMetrics.counters.size +
           global.testMetrics.gauges.size +
           global.testMetrics.histograms.size) : 0
      }
    };

    await fs.writeFile(
      path.join(reportsDir, 'test-execution-summary.json'),
      JSON.stringify(testSummary, null, 2)
    );

    // Generate metrics report
    if (global.testMetrics) {
      const metricsReport = {
        counters: Object.fromEntries(global.testMetrics.counters),
        gauges: Object.fromEntries(global.testMetrics.gauges),
        histograms: Object.fromEntries(global.testMetrics.histograms),
        summaries: Object.fromEntries(global.testMetrics.summaries),
        generatedAt: new Date().toISOString()
      };

      await fs.writeFile(
        path.join(reportsDir, 'metrics-report.json'),
        JSON.stringify(metricsReport, null, 2)
      );
    }

    // Generate alerts report
    if (global.testAlerts) {
      const alertsReport = {
        activeAlerts: Object.fromEntries(global.testAlerts.active),
        alertHistory: global.testAlerts.history,
        totalAlerts: global.testAlerts.history.length,
        criticalAlerts: global.testAlerts.history.filter(a => a.severity === 'critical').length,
        suppressedAlerts: Object.fromEntries(global.testAlerts.suppressions),
        generatedAt: new Date().toISOString()
      };

      await fs.writeFile(
        path.join(reportsDir, 'alerts-report.json'),
        JSON.stringify(alertsReport, null, 2)
      );
    }

    // Generate chaos testing report
    if (global.chaosTestResults) {
      const chaosReport = {
        experimentsRun: global.chaosTestResults.length,
        successfulExperiments: global.chaosTestResults.filter(r => r.success).length,
        failedExperiments: global.chaosTestResults.filter(r => !r.success).length,
        averageRecoveryTime: global.chaosTestResults
          .filter(r => r.recoveryTime)
          .reduce((sum, r) => sum + r.recoveryTime, 0) /
          global.chaosTestResults.filter(r => r.recoveryTime).length || 0,
        experiments: global.chaosTestResults,
        generatedAt: new Date().toISOString()
      };

      await fs.writeFile(
        path.join(reportsDir, 'chaos-testing-report.json'),
        JSON.stringify(chaosReport, null, 2)
      );
    }

    console.log('📊 Test reports generated');

  } catch (error) {
    console.error('Failed to generate test reports:', error);
  }
}

async function cleanupTestInfrastructure() {
  try {
    // Cleanup mock services
    if (global.testServices) {
      for (const [serviceId, service] of global.testServices) {
        if (service.cleanup && typeof service.cleanup === 'function') {
          try {
            await service.cleanup();
          } catch (error) {
            console.warn(`Failed to cleanup service ${serviceId}:`, error.message);
          }
        }
      }
      global.testServices.clear();
    }

    // Cleanup test databases
    if (global.testDatabases) {
      Object.keys(global.testDatabases).forEach(dbName => {
        const db = global.testDatabases[dbName];
        if (db.flows) db.flows.clear();
        if (db.services) db.services.clear();
        if (db.errors) db.errors.clear();
        if (db.indexes) {
          Object.values(db.indexes).forEach(index => {
            if (index && index.clear) index.clear();
          });
        }
      });
      global.testDatabases = null;
    }

    // Cleanup chaos tools
    if (global.chaosTools) {
      // Stop any ongoing chaos experiments
      if (global.chaosTools.activeExperiments) {
        global.chaosTools.activeExperiments.forEach(experiment => {
          if (experiment.stop && typeof experiment.stop === 'function') {
            experiment.stop();
          }
        });
      }
      global.chaosTools = null;
    }

    // Cleanup performance monitors
    if (global.performanceMonitors) {
      global.performanceMonitors.forEach(monitor => {
        if (monitor.stop && typeof monitor.stop === 'function') {
          monitor.stop();
        }
      });
      global.performanceMonitors = null;
    }

    console.log('🔧 Test infrastructure cleaned up');

  } catch (error) {
    console.error('Failed to cleanup test infrastructure:', error);
  }
}

async function archiveTestArtifacts() {
  try {
    const artifactsDir = path.join(__dirname, '..', 'temp', 'artifacts');
    const archiveDir = path.join(__dirname, '..', 'temp', 'archive');

    try {
      await fs.mkdir(archiveDir, { recursive: true });
    } catch (e) {
      // Directory might already exist
    }

    // Archive logs
    try {
      const logsDir = path.join(__dirname, '..', 'temp', 'logs');
      const logFiles = await fs.readdir(logsDir);

      for (const logFile of logFiles) {
        const sourcePath = path.join(logsDir, logFile);
        const destPath = path.join(archiveDir, `${Date.now()}_${logFile}`);
        await fs.copyFile(sourcePath, destPath);
      }
    } catch (error) {
      // Logs directory might not exist
    }

    // Archive metrics
    try {
      const metricsDir = path.join(__dirname, '..', 'temp', 'metrics');
      const metricFiles = await fs.readdir(metricsDir);

      for (const metricFile of metricFiles) {
        const sourcePath = path.join(metricsDir, metricFile);
        const destPath = path.join(archiveDir, `${Date.now()}_${metricFile}`);
        await fs.copyFile(sourcePath, destPath);
      }
    } catch (error) {
      // Metrics directory might not exist
    }

    console.log('📦 Test artifacts archived');

  } catch (error) {
    console.error('Failed to archive test artifacts:', error);
  }
}

async function cleanupTemporaryFiles() {
  try {
    const tempDir = path.join(__dirname, '..', 'temp');

    // List of directories to clean
    const tempDirs = ['logs', 'data', 'metrics'];

    for (const dir of tempDirs) {
      const dirPath = path.join(tempDir, dir);

      try {
        const files = await fs.readdir(dirPath);

        for (const file of files) {
          const filePath = path.join(dirPath, file);
          const stats = await fs.stat(filePath);

          // Delete files older than 1 hour
          const oneHourAgo = Date.now() - (60 * 60 * 1000);
          if (stats.mtime.getTime() < oneHourAgo) {
            await fs.unlink(filePath);
          }
        }
      } catch (error) {
        // Directory might not exist or be empty
      }
    }

    console.log('🗑️ Temporary files cleaned up');

  } catch (error) {
    console.error('Failed to cleanup temporary files:', error);
  }
}

async function generatePerformanceSummary() {
  try {
    if (!global.performanceBaselines) {
      return;
    }

    const performanceSummary = {
      baselines: global.performanceBaselines,
      actualPerformance: {},
      deviations: {},
      recommendations: [],
      generatedAt: new Date().toISOString()
    };

    // Calculate actual performance vs baselines
    if (global.testMetrics && global.testMetrics.histograms) {
      const histograms = global.testMetrics.histograms;

      Object.keys(global.performanceBaselines).forEach(metric => {
        if (histograms.has(metric)) {
          const histogram = histograms.get(metric);
          performanceSummary.actualPerformance[metric] = histogram;

          // Calculate deviation
          const baseline = global.performanceBaselines[metric];
          const actual = histogram.avg || 0;
          const expectedP95 = baseline.p95 || baseline.maxPerFlow || baseline.heapUsed;

          if (expectedP95) {
            const deviation = ((actual - expectedP95) / expectedP95) * 100;
            performanceSummary.deviations[metric] = {
              deviation: deviation.toFixed(2) + '%',
              status: deviation > 20 ? 'concerning' : deviation > 10 ? 'acceptable' : 'good'
            };

            // Generate recommendations
            if (deviation > 20) {
              performanceSummary.recommendations.push({
                metric,
                issue: `${metric} is ${deviation.toFixed(1)}% above baseline`,
                suggestion: `Investigate performance bottlenecks in ${metric} handling`
              });
            }
          }
        }
      });
    }

    // Memory usage analysis
    const memoryUsage = process.memoryUsage();
    const memoryMB = Math.round(memoryUsage.heapUsed / 1024 / 1024);
    const baselineMemory = global.performanceBaselines.memoryUsage?.heapUsed || 100;

    performanceSummary.memoryAnalysis = {
      current: memoryMB,
      baseline: baselineMemory,
      deviation: ((memoryMB - baselineMemory) / baselineMemory * 100).toFixed(2) + '%',
      status: memoryMB > baselineMemory * 2 ? 'high' : memoryMB > baselineMemory * 1.5 ? 'elevated' : 'normal'
    };

    if (memoryMB > baselineMemory * 2) {
      performanceSummary.recommendations.push({
        metric: 'memory',
        issue: 'Memory usage is significantly above baseline',
        suggestion: 'Check for memory leaks and optimize data structures'
      });
    }

    // Save performance summary
    const reportsDir = path.join(__dirname, '..', 'reports');
    await fs.writeFile(
      path.join(reportsDir, 'performance-summary.json'),
      JSON.stringify(performanceSummary, null, 2)
    );

    console.log('⚡ Performance summary generated');

  } catch (error) {
    console.error('Failed to generate performance summary:', error);
  }
}

async function cleanupMemoryAndResources() {
  try {
    // Clear global test data
    if (global.testFlows) {
      global.testFlows.clear();
      global.testFlows = null;
    }

    if (global.testErrors) {
      global.testErrors.clear();
      global.testErrors = null;
    }

    if (global.testMetrics) {
      global.testMetrics.counters.clear();
      global.testMetrics.gauges.clear();
      global.testMetrics.histograms.clear();
      global.testMetrics.summaries.clear();
      global.testMetrics = null;
    }

    if (global.testAlerts) {
      global.testAlerts.active.clear();
      global.testAlerts.history = [];
      global.testAlerts.suppressions.clear();
      global.testAlerts = null;
    }

    if (global.testDashboards) {
      global.testDashboards = null;
    }

    if (global.performanceBaselines) {
      global.performanceBaselines = null;
    }

    // Clear any remaining timers
    if (global.testTimers) {
      global.testTimers.forEach(timer => clearTimeout(timer));
      global.testTimers = null;
    }

    // Clear any remaining intervals
    if (global.testIntervals) {
      global.testIntervals.forEach(interval => clearInterval(interval));
      global.testIntervals = null;
    }

    // Force garbage collection if available
    if (global.gc) {
      global.gc();

      // Wait a bit and run GC again to ensure cleanup
      setTimeout(() => {
        if (global.gc) global.gc();
      }, 100);
    }

    // Log final memory usage
    const finalMemory = process.memoryUsage();
    console.log(`💾 Final memory usage: ${Math.round(finalMemory.heapUsed / 1024 / 1024)}MB`);

    console.log('🧠 Memory and resources cleaned up');

  } catch (error) {
    console.error('Failed to cleanup memory and resources:', error);
  }
}

// Handle uncaught exceptions during teardown
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception during teardown:', error);
  // Don't exit, let teardown continue
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection during teardown:', reason);
  // Don't exit, let teardown continue
});