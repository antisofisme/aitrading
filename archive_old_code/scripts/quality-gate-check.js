#!/usr/bin/env node

/**
 * Quality Gate Checker
 * Validates test results against quality standards and blocks deployment if gates fail
 */

const fs = require('fs');
const process = require('process');

class QualityGateChecker {
  constructor() {
    this.config = {
      minCoverage: parseFloat(process.env.MIN_COVERAGE) || 80,
      maxFailedTests: parseInt(process.env.MAX_FAILED_TESTS) || 0,
      maxCriticalIssues: parseInt(process.env.MAX_CRITICAL_ISSUES) || 0,
      minSuccessRate: parseFloat(process.env.MIN_SUCCESS_RATE) || 95,
      maxDuration: parseInt(process.env.MAX_DURATION) || 3600000, // 1 hour in ms
      maxFlakyTests: parseInt(process.env.MAX_FLAKY_TESTS) || 3,
      requiredTestTypes: (process.env.REQUIRED_TEST_TYPES || 'unit,integration').split(',')
    };

    this.gates = [];
    this.results = null;
    this.exitCode = 0;
  }

  /**
   * Run all quality gate checks
   */
  async runChecks() {
    console.log('🎯 Running Quality Gate Checks');
    console.log('==============================');

    try {
      await this.loadTestResults();
      await this.checkTestResults();
      await this.checkCoverage();
      await this.checkPerformance();
      await this.checkSecurity();
      await this.checkRequiredTestTypes();
      await this.generateReport();

      const passed = this.gates.every(gate => gate.passed);

      if (passed) {
        console.log('✅ All quality gates passed!');
        this.exitCode = 0;
      } else {
        console.log('❌ Quality gates failed!');
        this.exitCode = 1;
      }

      process.exit(this.exitCode);
    } catch (error) {
      console.error('💥 Error during quality gate checks:', error.message);
      process.exit(1);
    }
  }

  /**
   * Load test results from various sources
   */
  async loadTestResults() {
    console.log('📂 Loading test results...');

    // Try to load aggregated results first
    if (fs.existsSync('test-results-aggregated.json')) {
      const content = fs.readFileSync('test-results-aggregated.json', 'utf8');
      this.results = JSON.parse(content);
      console.log('✅ Loaded aggregated test results');
      return;
    }

    // Fallback to summary results
    if (fs.existsSync('test-summary.json')) {
      const content = fs.readFileSync('test-summary.json', 'utf8');
      this.results = {
        summary: JSON.parse(content),
        suites: [],
        failures: [],
        performance: {}
      };
      console.log('✅ Loaded test summary');
      return;
    }

    throw new Error('No test results found. Please run tests first.');
  }

  /**
   * Check basic test results
   */
  async checkTestResults() {
    console.log('🧪 Checking test results...');

    const { summary } = this.results;

    // Check for test failures
    const failedTestsGate = {
      name: 'Failed Tests',
      description: `Maximum ${this.config.maxFailedTests} failed tests allowed`,
      value: summary.failedTests,
      threshold: this.config.maxFailedTests,
      passed: summary.failedTests <= this.config.maxFailedTests,
      critical: true
    };

    this.gates.push(failedTestsGate);
    this.logGateResult(failedTestsGate);

    // Check success rate
    const successRateGate = {
      name: 'Success Rate',
      description: `Minimum ${this.config.minSuccessRate}% success rate required`,
      value: summary.successRate,
      threshold: this.config.minSuccessRate,
      passed: summary.successRate >= this.config.minSuccessRate,
      critical: true
    };

    this.gates.push(successRateGate);
    this.logGateResult(successRateGate);

    // Check test execution duration
    const durationGate = {
      name: 'Test Duration',
      description: `Maximum ${this.config.maxDuration / 60000} minutes execution time`,
      value: summary.duration,
      threshold: this.config.maxDuration,
      passed: summary.duration <= this.config.maxDuration,
      critical: false
    };

    this.gates.push(durationGate);
    this.logGateResult(durationGate);

    // Check minimum test count
    const minTestsGate = {
      name: 'Minimum Tests',
      description: 'At least 1 test must be executed',
      value: summary.totalTests,
      threshold: 1,
      passed: summary.totalTests >= 1,
      critical: true
    };

    this.gates.push(minTestsGate);
    this.logGateResult(minTestsGate);
  }

  /**
   * Check code coverage
   */
  async checkCoverage() {
    console.log('📊 Checking code coverage...');

    const { summary } = this.results;

    if (!summary.coverage || summary.coverage.lines.total === 0) {
      const noCoverageGate = {
        name: 'Coverage Data',
        description: 'Coverage data must be available',
        value: 0,
        threshold: 1,
        passed: false,
        critical: false,
        warning: 'No coverage data found'
      };

      this.gates.push(noCoverageGate);
      this.logGateResult(noCoverageGate);
      return;
    }

    // Line coverage
    const lineCoverageGate = {
      name: 'Line Coverage',
      description: `Minimum ${this.config.minCoverage}% line coverage required`,
      value: summary.coverage.lines.pct,
      threshold: this.config.minCoverage,
      passed: summary.coverage.lines.pct >= this.config.minCoverage,
      critical: true
    };

    this.gates.push(lineCoverageGate);
    this.logGateResult(lineCoverageGate);

    // Function coverage
    const functionCoverageGate = {
      name: 'Function Coverage',
      description: `Minimum ${this.config.minCoverage}% function coverage required`,
      value: summary.coverage.functions.pct,
      threshold: this.config.minCoverage,
      passed: summary.coverage.functions.pct >= this.config.minCoverage,
      critical: false
    };

    this.gates.push(functionCoverageGate);
    this.logGateResult(functionCoverageGate);

    // Branch coverage (lower threshold)
    const branchCoverageGate = {
      name: 'Branch Coverage',
      description: `Minimum ${this.config.minCoverage * 0.8}% branch coverage required`,
      value: summary.coverage.branches.pct,
      threshold: this.config.minCoverage * 0.8,
      passed: summary.coverage.branches.pct >= (this.config.minCoverage * 0.8),
      critical: false
    };

    this.gates.push(branchCoverageGate);
    this.logGateResult(branchCoverageGate);
  }

  /**
   * Check performance metrics
   */
  async checkPerformance() {
    console.log('⚡ Checking performance metrics...');

    const { performance } = this.results;

    if (!performance) {
      console.log('⚠️ No performance data available');
      return;
    }

    // Check for flaky tests
    if (performance.flakyTests) {
      const flakyTestsGate = {
        name: 'Flaky Tests',
        description: `Maximum ${this.config.maxFlakyTests} flaky tests allowed`,
        value: performance.flakyTests.length,
        threshold: this.config.maxFlakyTests,
        passed: performance.flakyTests.length <= this.config.maxFlakyTests,
        critical: false
      };

      this.gates.push(flakyTestsGate);
      this.logGateResult(flakyTestsGate);
    }

    // Check Lighthouse performance (if available)
    if (performance.lighthouse) {
      const lighthouseGate = {
        name: 'Lighthouse Performance',
        description: 'Minimum 70% Lighthouse performance score',
        value: performance.lighthouse.performanceScore,
        threshold: 70,
        passed: performance.lighthouse.performanceScore >= 70,
        critical: false
      };

      this.gates.push(lighthouseGate);
      this.logGateResult(lighthouseGate);
    }

    // Check for memory leaks (basic heuristic)
    if (performance.memoryUsage) {
      const memoryUsageGate = {
        name: 'Memory Usage',
        description: 'Memory usage should be reasonable',
        value: performance.memoryUsage.peak,
        threshold: 500 * 1024 * 1024, // 500MB
        passed: performance.memoryUsage.peak <= (500 * 1024 * 1024),
        critical: false
      };

      this.gates.push(memoryUsageGate);
      this.logGateResult(memoryUsageGate);
    }
  }

  /**
   * Check security-related metrics
   */
  async checkSecurity() {
    console.log('🛡️ Checking security metrics...');

    // Check for security scan results
    if (fs.existsSync('security-scan-results.json')) {
      try {
        const content = fs.readFileSync('security-scan-results.json', 'utf8');
        const securityResults = JSON.parse(content);

        const criticalIssues = securityResults.vulnerabilities?.filter(v => v.severity === 'critical')?.length || 0;

        const securityGate = {
          name: 'Security Vulnerabilities',
          description: `Maximum ${this.config.maxCriticalIssues} critical security issues allowed`,
          value: criticalIssues,
          threshold: this.config.maxCriticalIssues,
          passed: criticalIssues <= this.config.maxCriticalIssues,
          critical: true
        };

        this.gates.push(securityGate);
        this.logGateResult(securityGate);
      } catch (error) {
        console.warn('⚠️ Could not parse security scan results:', error.message);
      }
    } else {
      console.log('⚠️ No security scan results found');
    }

    // Check for dependency vulnerabilities
    if (fs.existsSync('npm-audit.json')) {
      try {
        const content = fs.readFileSync('npm-audit.json', 'utf8');
        const auditResults = JSON.parse(content);

        const criticalVulns = auditResults.metadata?.vulnerabilities?.critical || 0;

        const dependencyGate = {
          name: 'Dependency Vulnerabilities',
          description: 'No critical dependency vulnerabilities allowed',
          value: criticalVulns,
          threshold: 0,
          passed: criticalVulns === 0,
          critical: true
        };

        this.gates.push(dependencyGate);
        this.logGateResult(dependencyGate);
      } catch (error) {
        console.warn('⚠️ Could not parse npm audit results:', error.message);
      }
    }
  }

  /**
   * Check if required test types were executed
   */
  async checkRequiredTestTypes() {
    console.log('📋 Checking required test types...');

    const { suites } = this.results;
    const executedTypes = new Set(suites.map(suite => suite.type));

    for (const requiredType of this.config.requiredTestTypes) {
      const typeGate = {
        name: `${requiredType} Tests`,
        description: `${requiredType} tests must be executed`,
        value: executedTypes.has(requiredType) ? 1 : 0,
        threshold: 1,
        passed: executedTypes.has(requiredType),
        critical: requiredType === 'unit' // Unit tests are always critical
      };

      this.gates.push(typeGate);
      this.logGateResult(typeGate);
    }
  }

  /**
   * Generate quality gate report
   */
  async generateReport() {
    console.log('\n📊 Quality Gate Report');
    console.log('======================');

    const passed = this.gates.filter(gate => gate.passed);
    const failed = this.gates.filter(gate => !gate.passed);
    const critical = failed.filter(gate => gate.critical);

    console.log(`✅ Passed: ${passed.length}`);
    console.log(`❌ Failed: ${failed.length}`);
    console.log(`🚨 Critical Failed: ${critical.length}`);

    if (failed.length > 0) {
      console.log('\n❌ Failed Quality Gates:');
      console.log('========================');

      for (const gate of failed) {
        const icon = gate.critical ? '🚨' : '⚠️';
        console.log(`${icon} ${gate.name}: ${gate.value} (threshold: ${gate.threshold})`);
        if (gate.warning) {
          console.log(`   Warning: ${gate.warning}`);
        }
      }
    }

    // Generate JSON report for CI consumption
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total: this.gates.length,
        passed: passed.length,
        failed: failed.length,
        critical: critical.length,
        overallStatus: critical.length === 0 ? (failed.length === 0 ? 'PASSED' : 'WARNING') : 'FAILED'
      },
      gates: this.gates,
      config: this.config
    };

    fs.writeFileSync('quality-gate-report.json', JSON.stringify(report, null, 2));

    // Generate markdown summary for PR comments
    await this.generateMarkdownSummary(report);

    console.log('\n📄 Reports generated:');
    console.log('  - quality-gate-report.json');
    console.log('  - quality-gate-summary.md');
  }

  /**
   * Generate markdown summary for PR comments
   */
  async generateMarkdownSummary(report) {
    let markdown = '';

    // Header
    const statusIcon = report.summary.overallStatus === 'PASSED' ? '✅' :
                      report.summary.overallStatus === 'WARNING' ? '⚠️' : '❌';

    markdown += `## ${statusIcon} Quality Gate Results\n\n`;

    // Summary
    markdown += '### Summary\n\n';
    markdown += `- **Status**: ${report.summary.overallStatus}\n`;
    markdown += `- **Total Gates**: ${report.summary.total}\n`;
    markdown += `- **Passed**: ${report.summary.passed} ✅\n`;
    markdown += `- **Failed**: ${report.summary.failed} ❌\n`;
    markdown += `- **Critical Failed**: ${report.summary.critical} 🚨\n\n`;

    // Detailed results
    if (report.summary.failed > 0) {
      markdown += '### Failed Gates\n\n';
      markdown += '| Gate | Status | Value | Threshold | Critical |\n';
      markdown += '|------|--------|-------|-----------|----------|\n';

      for (const gate of this.gates.filter(g => !g.passed)) {
        const icon = gate.critical ? '🚨' : '⚠️';
        markdown += `| ${gate.name} | ${icon} | ${gate.value} | ${gate.threshold} | ${gate.critical ? 'Yes' : 'No'} |\n`;
      }
      markdown += '\n';
    }

    // Recommendations
    markdown += '### Recommendations\n\n';
    const recommendations = this.generateRecommendations();
    for (const rec of recommendations) {
      markdown += `- ${rec}\n`;
    }

    markdown += '\n---\n';
    markdown += `*Generated on ${new Date().toISOString()}*\n`;

    fs.writeFileSync('quality-gate-summary.md', markdown);
  }

  /**
   * Generate recommendations based on failed gates
   */
  generateRecommendations() {
    const recommendations = [];
    const failed = this.gates.filter(gate => !gate.passed);

    for (const gate of failed) {
      switch (gate.name) {
        case 'Failed Tests':
          recommendations.push('🔧 Fix failing tests before deployment');
          break;
        case 'Line Coverage':
          recommendations.push('📊 Add more unit tests to increase coverage');
          break;
        case 'Success Rate':
          recommendations.push('🎯 Improve test reliability and fix intermittent failures');
          break;
        case 'Test Duration':
          recommendations.push('⚡ Optimize test performance or increase parallelization');
          break;
        case 'Flaky Tests':
          recommendations.push('🎲 Investigate and fix unstable tests');
          break;
        case 'Security Vulnerabilities':
          recommendations.push('🛡️ Address critical security vulnerabilities');
          break;
        case 'Dependency Vulnerabilities':
          recommendations.push('📦 Update dependencies with security patches');
          break;
        default:
          recommendations.push(`🔍 Review and address: ${gate.name}`);
      }
    }

    if (recommendations.length === 0) {
      recommendations.push('🎉 All quality gates passed! Ready for deployment.');
    }

    return recommendations;
  }

  /**
   * Log gate result to console
   */
  logGateResult(gate) {
    const icon = gate.passed ? '✅' : (gate.critical ? '🚨' : '⚠️');
    const status = gate.passed ? 'PASS' : 'FAIL';
    console.log(`${icon} ${gate.name}: ${status} (${gate.value}/${gate.threshold})`);

    if (gate.warning) {
      console.log(`   ⚠️ ${gate.warning}`);
    }
  }
}

// Main execution
async function main() {
  console.log('🎯 Quality Gate Checker');
  console.log('=======================');

  const checker = new QualityGateChecker();
  await checker.runChecks();
}

if (require.main === module) {
  main().catch(error => {
    console.error('💥 Fatal error:', error);
    process.exit(1);
  });
}

module.exports = QualityGateChecker;