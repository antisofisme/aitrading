/**
 * Multi-Tenant Validator
 * Validates tenant isolation and resource allocation in the AI trading system
 */

class MultiTenantValidator {
  constructor() {
    this.tenantData = new Map();
    this.resourceUsage = new Map();
    this.isolationTests = [];
    this.startTime = Date.now();
  }

  registerTenant(tenantId, config = {}) {
    this.tenantData.set(tenantId, {
      id: tenantId,
      config,
      dataAccess: [],
      resourceAllocations: [],
      securityEvents: [],
      performanceMetrics: {
        requestCount: 0,
        averageLatency: 0,
        errorCount: 0
      },
      registrationTime: Date.now()
    });

    this.resourceUsage.set(tenantId, {
      memoryUsage: 0,
      cpuUsage: 0,
      networkBandwidth: 0,
      storageUsage: 0,
      aiTokensConsumed: 0,
      requestsPerSecond: 0
    });

    console.log(`👤 Tenant ${tenantId} registered for validation`);
  }

  recordDataAccess(tenantId, dataType, resourceId, timestamp = Date.now()) {
    const tenant = this.tenantData.get(tenantId);
    if (!tenant) {
      throw new Error(`Tenant ${tenantId} not registered`);
    }

    tenant.dataAccess.push({
      dataType,
      resourceId,
      timestamp,
      accessType: 'read' // Could be extended for write/modify
    });
  }

  recordResourceAllocation(tenantId, resourceType, amount, timestamp = Date.now()) {
    const tenant = this.tenantData.get(tenantId);
    const usage = this.resourceUsage.get(tenantId);

    if (!tenant || !usage) {
      throw new Error(`Tenant ${tenantId} not registered`);
    }

    tenant.resourceAllocations.push({
      resourceType,
      amount,
      timestamp
    });

    // Update current usage
    if (usage[resourceType] !== undefined) {
      usage[resourceType] += amount;
    }
  }

  recordPerformanceMetric(tenantId, metricType, value, timestamp = Date.now()) {
    const tenant = this.tenantData.get(tenantId);
    if (!tenant) {
      throw new Error(`Tenant ${tenantId} not registered`);
    }

    switch (metricType) {
      case 'request':
        tenant.performanceMetrics.requestCount++;
        break;
      case 'latency':
        const currentAvg = tenant.performanceMetrics.averageLatency;
        const requestCount = tenant.performanceMetrics.requestCount;
        tenant.performanceMetrics.averageLatency =
          (currentAvg * (requestCount - 1) + value) / requestCount;
        break;
      case 'error':
        tenant.performanceMetrics.errorCount++;
        break;
    }
  }

  validateDataIsolation(tenantIds) {
    const isolationResults = {
      passed: true,
      violations: [],
      summary: {
        tenantsChecked: tenantIds.length,
        dataLeaks: 0,
        unauthorizedAccess: 0
      }
    };

    // Check for data access violations between tenants
    for (let i = 0; i < tenantIds.length; i++) {
      for (let j = i + 1; j < tenantIds.length; j++) {
        const tenant1 = this.tenantData.get(tenantIds[i]);
        const tenant2 = this.tenantData.get(tenantIds[j]);

        if (!tenant1 || !tenant2) continue;

        // Check if tenant1 accessed tenant2's data
        const violations = this.findDataAccessViolations(tenant1, tenant2);
        if (violations.length > 0) {
          isolationResults.passed = false;
          isolationResults.violations.push(...violations);
          isolationResults.summary.dataLeaks += violations.length;
        }
      }
    }

    this.isolationTests.push({
      type: 'data_isolation',
      timestamp: Date.now(),
      result: isolationResults
    });

    return isolationResults;
  }

  findDataAccessViolations(tenant1, tenant2) {
    const violations = [];

    // Check if tenant1 accessed resources belonging to tenant2
    tenant1.dataAccess.forEach(access => {
      // In a real system, you'd check if the resourceId belongs to tenant2
      // For testing, we'll simulate by checking if resourceId contains tenant2's ID
      if (access.resourceId && access.resourceId.includes(tenant2.id)) {
        violations.push({
          violatingTenant: tenant1.id,
          victimTenant: tenant2.id,
          resourceId: access.resourceId,
          timestamp: access.timestamp,
          type: 'unauthorized_data_access'
        });
      }
    });

    return violations;
  }

  validateResourceFairness(tenantIds, expectedAllocations = {}) {
    const fairnessResults = {
      passed: true,
      imbalances: [],
      summary: {
        tenantsChecked: tenantIds.length,
        resourceTypes: Object.keys(expectedAllocations),
        fairnessScore: 0
      }
    };

    const resourceTypes = ['memoryUsage', 'cpuUsage', 'networkBandwidth', 'aiTokensConsumed'];
    const usageStats = {};

    // Calculate usage statistics for each resource type
    resourceTypes.forEach(resourceType => {
      const usages = tenantIds.map(tenantId => {
        const usage = this.resourceUsage.get(tenantId);
        return usage ? usage[resourceType] : 0;
      });

      const total = usages.reduce((a, b) => a + b, 0);
      const average = total / usages.length;
      const variance = usages.reduce((sum, usage) => sum + Math.pow(usage - average, 2), 0) / usages.length;
      const standardDeviation = Math.sqrt(variance);
      const coefficientOfVariation = average > 0 ? standardDeviation / average : 0;

      usageStats[resourceType] = {
        total,
        average,
        variance,
        standardDeviation,
        coefficientOfVariation,
        usages
      };

      // Flag high variation as potential unfairness (CV > 0.5)
      if (coefficientOfVariation > 0.5) {
        fairnessResults.passed = false;
        fairnessResults.imbalances.push({
          resourceType,
          coefficientOfVariation,
          severity: coefficientOfVariation > 1.0 ? 'high' : 'medium'
        });
      }
    });

    // Calculate overall fairness score (0-100, higher is better)
    const avgCV = Object.values(usageStats).reduce((sum, stat) => sum + stat.coefficientOfVariation, 0) / resourceTypes.length;
    fairnessResults.summary.fairnessScore = Math.max(0, 100 - (avgCV * 100));

    this.isolationTests.push({
      type: 'resource_fairness',
      timestamp: Date.now(),
      result: fairnessResults,
      usageStats
    });

    return fairnessResults;
  }

  validatePerformanceIsolation(tenantIds) {
    const performanceResults = {
      passed: true,
      issues: [],
      summary: {
        tenantsChecked: tenantIds.length,
        performanceVariation: 0,
        noiseFactors: []
      }
    };

    const performanceMetrics = tenantIds.map(tenantId => {
      const tenant = this.tenantData.get(tenantId);
      return tenant ? tenant.performanceMetrics : null;
    }).filter(metrics => metrics !== null);

    if (performanceMetrics.length < 2) {
      performanceResults.issues.push('Insufficient tenants for performance comparison');
      return performanceResults;
    }

    // Check for performance consistency across tenants
    const latencies = performanceMetrics.map(m => m.averageLatency);
    const errorRates = performanceMetrics.map(m => {
      return m.requestCount > 0 ? (m.errorCount / m.requestCount) * 100 : 0;
    });

    // Calculate coefficient of variation for latencies
    const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    const latencyVariance = latencies.reduce((sum, lat) => sum + Math.pow(lat - avgLatency, 2), 0) / latencies.length;
    const latencyCV = avgLatency > 0 ? Math.sqrt(latencyVariance) / avgLatency : 0;

    performanceResults.summary.performanceVariation = latencyCV;

    // Flag high latency variation (>0.3 CV)
    if (latencyCV > 0.3) {
      performanceResults.passed = false;
      performanceResults.issues.push({
        type: 'high_latency_variation',
        coefficientOfVariation: latencyCV,
        description: 'Significant performance variation between tenants detected'
      });
    }

    // Check for tenants with significantly higher error rates
    const avgErrorRate = errorRates.reduce((a, b) => a + b, 0) / errorRates.length;
    errorRates.forEach((errorRate, index) => {
      if (errorRate > avgErrorRate * 2 && errorRate > 5) { // >2x average and >5%
        performanceResults.passed = false;
        performanceResults.issues.push({
          type: 'high_error_rate',
          tenantId: tenantIds[index],
          errorRate,
          averageErrorRate: avgErrorRate,
          description: `Tenant ${tenantIds[index]} has significantly higher error rate`
        });
      }
    });

    this.isolationTests.push({
      type: 'performance_isolation',
      timestamp: Date.now(),
      result: performanceResults
    });

    return performanceResults;
  }

  generateTenantReport(tenantId) {
    const tenant = this.tenantData.get(tenantId);
    const usage = this.resourceUsage.get(tenantId);

    if (!tenant || !usage) {
      throw new Error(`Tenant ${tenantId} not found`);
    }

    const uptime = Date.now() - tenant.registrationTime;

    return {
      tenantId,
      uptime,
      dataAccess: {
        totalAccesses: tenant.dataAccess.length,
        uniqueResources: new Set(tenant.dataAccess.map(a => a.resourceId)).size,
        lastAccess: tenant.dataAccess.length > 0 ?
          Math.max(...tenant.dataAccess.map(a => a.timestamp)) : null
      },
      performance: {
        ...tenant.performanceMetrics,
        requestsPerSecond: uptime > 0 ? (tenant.performanceMetrics.requestCount / (uptime / 1000)) : 0
      },
      resourceUsage: { ...usage },
      securityEvents: tenant.securityEvents.length,
      isolationScore: this.calculateIsolationScore(tenantId)
    };
  }

  calculateIsolationScore(tenantId) {
    // Calculate a score (0-100) based on isolation compliance
    let score = 100;

    // Check recent isolation tests for this tenant
    this.isolationTests.forEach(test => {
      if (test.result.violations) {
        const tenantViolations = test.result.violations.filter(v =>
          v.violatingTenant === tenantId || v.victimTenant === tenantId
        );
        score -= tenantViolations.length * 10; // -10 points per violation
      }

      if (test.result.imbalances) {
        score -= test.result.imbalances.length * 5; // -5 points per imbalance
      }

      if (test.result.issues) {
        const tenantIssues = test.result.issues.filter(issue =>
          issue.tenantId === tenantId
        );
        score -= tenantIssues.length * 15; // -15 points per performance issue
      }
    });

    return Math.max(0, score);
  }

  generateComprehensiveReport() {
    const allTenants = Array.from(this.tenantData.keys());
    const totalUptime = Date.now() - this.startTime;

    const report = {
      summary: {
        totalTenants: allTenants.length,
        testDuration: totalUptime,
        isolationTestsRun: this.isolationTests.length,
        overallCompliance: this.calculateOverallCompliance()
      },
      tenantReports: allTenants.map(tenantId => this.generateTenantReport(tenantId)),
      isolationTests: this.isolationTests,
      recommendations: this.generateRecommendations()
    };

    return report;
  }

  calculateOverallCompliance() {
    if (this.isolationTests.length === 0) return 100;

    const passedTests = this.isolationTests.filter(test => test.result.passed).length;
    return (passedTests / this.isolationTests.length) * 100;
  }

  generateRecommendations() {
    const recommendations = [];

    // Analyze isolation test results for patterns
    const failedTests = this.isolationTests.filter(test => !test.result.passed);

    if (failedTests.length > 0) {
      const dataIsolationFailures = failedTests.filter(test => test.type === 'data_isolation');
      if (dataIsolationFailures.length > 0) {
        recommendations.push({
          priority: 'high',
          category: 'security',
          issue: 'Data isolation violations detected',
          recommendation: 'Review access control mechanisms and implement stricter data boundaries',
          affectedTests: dataIsolationFailures.length
        });
      }

      const performanceIssues = failedTests.filter(test => test.type === 'performance_isolation');
      if (performanceIssues.length > 0) {
        recommendations.push({
          priority: 'medium',
          category: 'performance',
          issue: 'Performance isolation inconsistencies',
          recommendation: 'Implement resource throttling and quality of service controls',
          affectedTests: performanceIssues.length
        });
      }

      const fairnessIssues = failedTests.filter(test => test.type === 'resource_fairness');
      if (fairnessIssues.length > 0) {
        recommendations.push({
          priority: 'medium',
          category: 'resource_management',
          issue: 'Resource allocation imbalances',
          recommendation: 'Implement fair resource scheduling and usage quotas',
          affectedTests: fairnessIssues.length
        });
      }
    }

    return recommendations;
  }

  reset() {
    this.tenantData.clear();
    this.resourceUsage.clear();
    this.isolationTests = [];
    this.startTime = Date.now();
  }
}

module.exports = MultiTenantValidator;