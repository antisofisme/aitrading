#!/usr/bin/env node

/**
 * Test Results Aggregation Script
 * Processes test results from multiple test runners and generates unified reports
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TestResultsAggregator {
  constructor(artifactsDir) {
    this.artifactsDir = artifactsDir;
    this.results = {
      summary: {
        totalTests: 0,
        passedTests: 0,
        failedTests: 0,
        skippedTests: 0,
        duration: 0,
        coverage: {
          lines: { total: 0, covered: 0, pct: 0 },
          functions: { total: 0, covered: 0, pct: 0 },
          statements: { total: 0, covered: 0, pct: 0 },
          branches: { total: 0, covered: 0, pct: 0 }
        }
      },
      suites: [],
      failures: [],
      performance: {
        slowestTests: [],
        flakyTests: [],
        memoryUsage: []
      }
    };
  }

  /**
   * Main aggregation method
   */
  async aggregate() {
    console.log('🔄 Starting test results aggregation...');

    try {
      await this.discoverTestArtifacts();
      await this.processJestResults();
      await this.processCoverageReports();
      await this.processE2EResults();
      await this.processPerformanceResults();
      await this.generateSummary();
      await this.exportResults();

      console.log('✅ Test results aggregation completed successfully');
    } catch (error) {
      console.error('❌ Error during aggregation:', error.message);
      process.exit(1);
    }
  }

  /**
   * Discover all test artifact directories
   */
  async discoverTestArtifacts() {
    console.log('🔍 Discovering test artifacts...');

    if (!fs.existsSync(this.artifactsDir)) {
      throw new Error(`Artifacts directory not found: ${this.artifactsDir}`);
    }

    this.artifactDirs = fs.readdirSync(this.artifactsDir)
      .filter(dir => dir.startsWith('test-results-'))
      .map(dir => path.join(this.artifactsDir, dir));

    console.log(`📁 Found ${this.artifactDirs.length} test artifact directories`);
  }

  /**
   * Process Jest test results
   */
  async processJestResults() {
    console.log('🧪 Processing Jest test results...');

    for (const artifactDir of this.artifactDirs) {
      const testResultFiles = fs.readdirSync(artifactDir)
        .filter(file => file.includes('test-results') && file.endsWith('.json'));

      for (const file of testResultFiles) {
        try {
          const filePath = path.join(artifactDir, file);
          const content = fs.readFileSync(filePath, 'utf8');
          const results = JSON.parse(content);

          await this.processJestResult(results, file);
        } catch (error) {
          console.warn(`⚠️ Could not process Jest result ${file}:`, error.message);
        }
      }
    }
  }

  /**
   * Process individual Jest result
   */
  async processJestResult(results, filename) {
    const suiteType = this.extractSuiteType(filename);

    // Update summary totals
    this.results.summary.totalTests += results.numTotalTests || 0;
    this.results.summary.passedTests += results.numPassedTests || 0;
    this.results.summary.failedTests += results.numFailedTests || 0;
    this.results.summary.skippedTests += results.numPendingTests || 0;

    // Process test suites
    if (results.testResults) {
      for (const testResult of results.testResults) {
        const suite = {
          name: path.basename(testResult.name),
          type: suiteType,
          duration: testResult.endTime - testResult.startTime,
          tests: testResult.numTotalTests || 0,
          passed: testResult.numPassedTests || 0,
          failed: testResult.numFailedTests || 0,
          skipped: testResult.numPendingTests || 0,
          file: testResult.name
        };

        this.results.suites.push(suite);
        this.results.summary.duration += suite.duration;

        // Collect failures
        if (testResult.assertionResults) {
          for (const assertion of testResult.assertionResults) {
            if (assertion.status === 'failed') {
              this.results.failures.push({
                suite: suite.name,
                test: assertion.title,
                message: assertion.failureMessages?.[0] || 'Unknown error',
                file: testResult.name,
                duration: assertion.duration || 0
              });
            }

            // Collect slow tests
            if (assertion.duration > 5000) { // > 5 seconds
              this.results.performance.slowestTests.push({
                suite: suite.name,
                test: assertion.title,
                duration: assertion.duration,
                file: testResult.name
              });
            }
          }
        }
      }
    }
  }

  /**
   * Process coverage reports
   */
  async processCoverageReports() {
    console.log('📊 Processing coverage reports...');

    const coverageFiles = [];
    let totalCoverage = {
      lines: { total: 0, covered: 0 },
      functions: { total: 0, covered: 0 },
      statements: { total: 0, covered: 0 },
      branches: { total: 0, covered: 0 }
    };

    for (const artifactDir of this.artifactDirs) {
      const coverageSummaryFiles = fs.readdirSync(artifactDir)
        .filter(file => file.includes('coverage-summary') && file.endsWith('.json'));

      for (const file of coverageSummaryFiles) {
        try {
          const filePath = path.join(artifactDir, file);
          const content = fs.readFileSync(filePath, 'utf8');
          const coverage = JSON.parse(content);

          if (coverage.total) {
            coverageFiles.push(coverage);

            // Aggregate coverage metrics
            const total = coverage.total;
            totalCoverage.lines.total += total.lines?.total || 0;
            totalCoverage.lines.covered += total.lines?.covered || 0;
            totalCoverage.functions.total += total.functions?.total || 0;
            totalCoverage.functions.covered += total.functions?.covered || 0;
            totalCoverage.statements.total += total.statements?.total || 0;
            totalCoverage.statements.covered += total.statements?.covered || 0;
            totalCoverage.branches.total += total.branches?.total || 0;
            totalCoverage.branches.covered += total.branches?.covered || 0;
          }
        } catch (error) {
          console.warn(`⚠️ Could not process coverage file ${file}:`, error.message);
        }
      }
    }

    // Calculate aggregate coverage percentages
    if (totalCoverage.lines.total > 0) {
      this.results.summary.coverage = {
        lines: {
          total: totalCoverage.lines.total,
          covered: totalCoverage.lines.covered,
          pct: Math.round((totalCoverage.lines.covered / totalCoverage.lines.total) * 100 * 100) / 100
        },
        functions: {
          total: totalCoverage.functions.total,
          covered: totalCoverage.functions.covered,
          pct: Math.round((totalCoverage.functions.covered / totalCoverage.functions.total) * 100 * 100) / 100
        },
        statements: {
          total: totalCoverage.statements.total,
          covered: totalCoverage.statements.covered,
          pct: Math.round((totalCoverage.statements.covered / totalCoverage.statements.total) * 100 * 100) / 100
        },
        branches: {
          total: totalCoverage.branches.total,
          covered: totalCoverage.branches.covered,
          pct: Math.round((totalCoverage.branches.covered / totalCoverage.branches.total) * 100 * 100) / 100
        }
      };
    }

    console.log(`📊 Processed ${coverageFiles.length} coverage reports`);
  }

  /**
   * Process E2E test results
   */
  async processE2EResults() {
    console.log('🌐 Processing E2E test results...');

    for (const artifactDir of this.artifactDirs) {
      // Look for Playwright or Cypress results
      const playwrightResults = path.join(artifactDir, 'playwright-report');
      const cypressResults = path.join(artifactDir, 'cypress');

      if (fs.existsSync(playwrightResults)) {
        await this.processPlaywrightResults(playwrightResults);
      }

      if (fs.existsSync(cypressResults)) {
        await this.processCypressResults(cypressResults);
      }
    }
  }

  /**
   * Process Playwright results
   */
  async processPlaywrightResults(resultsDir) {
    try {
      const reportPath = path.join(resultsDir, 'results.json');
      if (fs.existsSync(reportPath)) {
        const content = fs.readFileSync(reportPath, 'utf8');
        const results = JSON.parse(content);

        // Process Playwright results structure
        if (results.suites) {
          for (const suite of results.suites) {
            this.processPlaywrightSuite(suite);
          }
        }
      }
    } catch (error) {
      console.warn('⚠️ Could not process Playwright results:', error.message);
    }
  }

  /**
   * Process Cypress results
   */
  async processCypressResults(resultsDir) {
    try {
      const resultFiles = fs.readdirSync(resultsDir)
        .filter(file => file.endsWith('.json'));

      for (const file of resultFiles) {
        const content = fs.readFileSync(path.join(resultsDir, file), 'utf8');
        const results = JSON.parse(content);

        // Process Cypress results structure
        if (results.tests) {
          for (const test of results.tests) {
            this.processCypressTest(test);
          }
        }
      }
    } catch (error) {
      console.warn('⚠️ Could not process Cypress results:', error.message);
    }
  }

  /**
   * Process performance test results
   */
  async processPerformanceResults() {
    console.log('⚡ Processing performance test results...');

    for (const artifactDir of this.artifactDirs) {
      const perfFiles = fs.readdirSync(artifactDir)
        .filter(file => file.includes('performance') || file.includes('lighthouse'));

      for (const file of perfFiles) {
        try {
          const filePath = path.join(artifactDir, file);
          const content = fs.readFileSync(filePath, 'utf8');

          if (file.includes('lighthouse')) {
            await this.processLighthouseResults(JSON.parse(content));
          } else if (file.includes('performance')) {
            await this.processPerformanceMetrics(JSON.parse(content));
          }
        } catch (error) {
          console.warn(`⚠️ Could not process performance file ${file}:`, error.message);
        }
      }
    }
  }

  /**
   * Process Lighthouse results
   */
  async processLighthouseResults(results) {
    if (results.audits) {
      const metrics = {
        performanceScore: results.categories?.performance?.score * 100 || 0,
        firstContentfulPaint: results.audits['first-contentful-paint']?.numericValue || 0,
        largestContentfulPaint: results.audits['largest-contentful-paint']?.numericValue || 0,
        speedIndex: results.audits['speed-index']?.numericValue || 0,
        timeToInteractive: results.audits['interactive']?.numericValue || 0
      };

      this.results.performance.lighthouse = metrics;
    }
  }

  /**
   * Process general performance metrics
   */
  async processPerformanceMetrics(metrics) {
    this.results.performance.metrics = metrics;
  }

  /**
   * Generate summary statistics
   */
  async generateSummary() {
    console.log('📋 Generating summary statistics...');

    // Calculate success rate
    const totalTests = this.results.summary.totalTests;
    const passedTests = this.results.summary.passedTests;
    this.results.summary.successRate = totalTests > 0
      ? Math.round((passedTests / totalTests) * 100 * 100) / 100
      : 0;

    // Sort performance data
    this.results.performance.slowestTests.sort((a, b) => b.duration - a.duration);
    this.results.performance.slowestTests = this.results.performance.slowestTests.slice(0, 10);

    // Generate flaky test detection (tests that failed and passed in different runs)
    const testCounts = {};
    for (const suite of this.results.suites) {
      const key = `${suite.type}-${suite.name}`;
      if (!testCounts[key]) {
        testCounts[key] = { passed: 0, failed: 0, total: 0 };
      }
      testCounts[key].passed += suite.passed;
      testCounts[key].failed += suite.failed;
      testCounts[key].total += suite.tests;
    }

    for (const [testKey, counts] of Object.entries(testCounts)) {
      if (counts.failed > 0 && counts.passed > 0) {
        this.results.performance.flakyTests.push({
          test: testKey,
          failureRate: Math.round((counts.failed / counts.total) * 100 * 100) / 100,
          totalRuns: counts.total
        });
      }
    }

    // Memory usage estimation
    this.results.performance.memoryUsage = {
      peak: process.memoryUsage().heapUsed,
      average: process.memoryUsage().heapUsed * 0.8 // Estimation
    };

    console.log('📊 Summary generated successfully');
  }

  /**
   * Export results to files
   */
  async exportResults() {
    console.log('💾 Exporting aggregated results...');

    // Export full results as JSON
    fs.writeFileSync(
      'test-results-aggregated.json',
      JSON.stringify(this.results, null, 2)
    );

    // Export summary for CI consumption
    const summary = {
      totalTests: this.results.summary.totalTests,
      passedTests: this.results.summary.passedTests,
      failedTests: this.results.summary.failedTests,
      successRate: this.results.summary.successRate,
      coverage: this.results.summary.coverage.lines.pct,
      duration: this.results.summary.duration,
      timestamp: new Date().toISOString()
    };

    fs.writeFileSync(
      'test-summary.json',
      JSON.stringify(summary, null, 2)
    );

    // Export JUnit XML for CI integration
    await this.exportJUnitXML();

    console.log('✅ Results exported successfully');
  }

  /**
   * Export JUnit XML format
   */
  async exportJUnitXML() {
    const xml = this.generateJUnitXML();
    fs.writeFileSync('test-results-junit.xml', xml);
  }

  /**
   * Generate JUnit XML format
   */
  generateJUnitXML() {
    const { summary, suites, failures } = this.results;

    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += `<testsuites name="AiTrading Test Results" tests="${summary.totalTests}" failures="${summary.failedTests}" time="${summary.duration / 1000}">\n`;

    for (const suite of suites) {
      xml += `  <testsuite name="${suite.name}" tests="${suite.tests}" failures="${suite.failed}" time="${suite.duration / 1000}">\n`;

      // Find failures for this suite
      const suiteFailures = failures.filter(f => f.suite === suite.name);

      for (const failure of suiteFailures) {
        xml += `    <testcase name="${failure.test}" time="${failure.duration / 1000}">\n`;
        xml += `      <failure message="${this.escapeXml(failure.message)}"></failure>\n`;
        xml += `    </testcase>\n`;
      }

      xml += `  </testsuite>\n`;
    }

    xml += `</testsuites>\n`;
    return xml;
  }

  /**
   * Extract suite type from filename
   */
  extractSuiteType(filename) {
    if (filename.includes('backend')) return 'backend';
    if (filename.includes('frontend')) return 'frontend';
    if (filename.includes('integration')) return 'integration';
    if (filename.includes('e2e')) return 'e2e';
    if (filename.includes('api')) return 'api';
    return 'unit';
  }

  /**
   * Escape XML special characters
   */
  escapeXml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }
}

// Main execution
async function main() {
  const artifactsDir = process.argv[2] || 'test-artifacts';

  console.log('🧪 Test Results Aggregator');
  console.log('==========================');
  console.log(`📁 Artifacts directory: ${artifactsDir}`);

  const aggregator = new TestResultsAggregator(artifactsDir);
  await aggregator.aggregate();

  console.log('\n✅ Test results aggregation completed!');
  console.log('📊 Generated files:');
  console.log('  - test-results-aggregated.json (full results)');
  console.log('  - test-summary.json (summary for CI)');
  console.log('  - test-results-junit.xml (JUnit format)');
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = TestResultsAggregator;