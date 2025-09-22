#!/usr/bin/env node

/**
 * Test Report Generator
 * Creates comprehensive test reports in multiple formats (Markdown, HTML, JSON)
 */

const fs = require('fs');
const path = require('path');

class TestReportGenerator {
  constructor() {
    this.results = null;
    this.timestamp = new Date();
  }

  /**
   * Generate all report formats
   */
  async generateReports() {
    console.log('📝 Generating test reports...');

    try {
      await this.loadResults();
      await this.generateMarkdownReport();
      await this.generateHTMLReport();
      await this.generateConsoleReport();
      await this.generateSlackReport();

      console.log('✅ All test reports generated successfully');
    } catch (error) {
      console.error('❌ Error generating reports:', error.message);
      process.exit(1);
    }
  }

  /**
   * Load aggregated test results
   */
  async loadResults() {
    console.log('📂 Loading test results...');

    if (fs.existsSync('test-results-aggregated.json')) {
      const content = fs.readFileSync('test-results-aggregated.json', 'utf8');
      this.results = JSON.parse(content);
    } else if (fs.existsSync('test-summary.json')) {
      const content = fs.readFileSync('test-summary.json', 'utf8');
      this.results = { summary: JSON.parse(content), suites: [], failures: [] };
    } else {
      throw new Error('No test results found. Run test aggregation first.');
    }

    console.log('✅ Test results loaded');
  }

  /**
   * Generate Markdown report
   */
  async generateMarkdownReport() {
    console.log('📝 Generating Markdown report...');

    const { summary, suites, failures, performance } = this.results;
    let markdown = '';

    // Header
    markdown += '# 🧪 Test Execution Report\n\n';
    markdown += `**Generated**: ${this.timestamp.toISOString()}\n`;
    markdown += `**Environment**: ${process.env.GITHUB_REF_NAME || 'local'}\n`;
    markdown += `**Commit**: ${process.env.GITHUB_SHA?.substring(0, 7) || 'unknown'}\n\n`;

    // Summary section
    markdown += '## 📊 Test Summary\n\n';
    markdown += '| Metric | Value | Status |\n';
    markdown += '|--------|-------|--------|\n';
    markdown += `| Total Tests | ${summary.totalTests} | ${this.getStatusIcon(summary.totalTests > 0)} |\n`;
    markdown += `| Passed | ${summary.passedTests} | ${this.getStatusIcon(summary.passedTests > 0)} |\n`;
    markdown += `| Failed | ${summary.failedTests} | ${this.getStatusIcon(summary.failedTests === 0)} |\n`;
    markdown += `| Skipped | ${summary.skippedTests || 0} | ℹ️ |\n`;
    markdown += `| Success Rate | ${summary.successRate}% | ${this.getStatusIcon(summary.successRate >= 95)} |\n`;
    markdown += `| Duration | ${this.formatDuration(summary.duration)} | ⏱️ |\n\n`;

    // Coverage section
    if (summary.coverage && summary.coverage.lines.total > 0) {
      markdown += '## 📊 Code Coverage\n\n';
      markdown += '| Type | Coverage | Status |\n';
      markdown += '|------|----------|--------|\n';
      markdown += `| Lines | ${summary.coverage.lines.pct}% | ${this.getStatusIcon(summary.coverage.lines.pct >= 80)} |\n`;
      markdown += `| Functions | ${summary.coverage.functions.pct}% | ${this.getStatusIcon(summary.coverage.functions.pct >= 80)} |\n`;
      markdown += `| Statements | ${summary.coverage.statements.pct}% | ${this.getStatusIcon(summary.coverage.statements.pct >= 80)} |\n`;
      markdown += `| Branches | ${summary.coverage.branches.pct}% | ${this.getStatusIcon(summary.coverage.branches.pct >= 70)} |\n\n`;

      // Coverage details
      markdown += '### Coverage Details\n\n';
      markdown += `- **Lines**: ${summary.coverage.lines.covered}/${summary.coverage.lines.total}\n`;
      markdown += `- **Functions**: ${summary.coverage.functions.covered}/${summary.coverage.functions.total}\n`;
      markdown += `- **Statements**: ${summary.coverage.statements.covered}/${summary.coverage.statements.total}\n`;
      markdown += `- **Branches**: ${summary.coverage.branches.covered}/${summary.coverage.branches.total}\n\n`;
    }

    // Test Suites section
    if (suites && suites.length > 0) {
      markdown += '## 🧪 Test Suites\n\n';
      markdown += '| Suite | Type | Tests | Passed | Failed | Duration |\n';
      markdown += '|-------|------|-------|--------|--------|---------|\n';

      for (const suite of suites.slice(0, 20)) { // Limit to 20 suites
        const status = suite.failed === 0 ? '✅' : '❌';
        markdown += `| ${status} ${suite.name} | ${suite.type} | ${suite.tests} | ${suite.passed} | ${suite.failed} | ${this.formatDuration(suite.duration)} |\n`;
      }

      if (suites.length > 20) {
        markdown += `\n*... and ${suites.length - 20} more suites*\n`;
      }
      markdown += '\n';
    }

    // Failures section
    if (failures && failures.length > 0) {
      markdown += '## ❌ Test Failures\n\n';

      for (const failure of failures.slice(0, 10)) { // Limit to 10 failures
        markdown += `### ${failure.suite} - ${failure.test}\n\n`;
        markdown += '```\n';
        markdown += failure.message.substring(0, 500); // Limit message length
        if (failure.message.length > 500) {
          markdown += '\n... (truncated)';
        }
        markdown += '\n```\n\n';
      }

      if (failures.length > 10) {
        markdown += `*... and ${failures.length - 10} more failures*\n\n`;
      }
    }

    // Performance section
    if (performance) {
      markdown += '## ⚡ Performance Insights\n\n';

      if (performance.slowestTests && performance.slowestTests.length > 0) {
        markdown += '### 🐌 Slowest Tests\n\n';
        markdown += '| Test | Suite | Duration |\n';
        markdown += '|------|-------|----------|\n';

        for (const test of performance.slowestTests.slice(0, 5)) {
          markdown += `| ${test.test} | ${test.suite} | ${this.formatDuration(test.duration)} |\n`;
        }
        markdown += '\n';
      }

      if (performance.flakyTests && performance.flakyTests.length > 0) {
        markdown += '### 🎲 Potentially Flaky Tests\n\n';
        markdown += '| Test | Failure Rate | Total Runs |\n';
        markdown += '|------|--------------|------------|\n';

        for (const test of performance.flakyTests) {
          markdown += `| ${test.test} | ${test.failureRate}% | ${test.totalRuns} |\n`;
        }
        markdown += '\n';
      }

      if (performance.lighthouse) {
        markdown += '### 🌐 Lighthouse Performance\n\n';
        const { lighthouse } = performance;
        markdown += `- **Performance Score**: ${Math.round(lighthouse.performanceScore)}%\n`;
        markdown += `- **First Contentful Paint**: ${Math.round(lighthouse.firstContentfulPaint)}ms\n`;
        markdown += `- **Largest Contentful Paint**: ${Math.round(lighthouse.largestContentfulPaint)}ms\n`;
        markdown += `- **Speed Index**: ${Math.round(lighthouse.speedIndex)}ms\n`;
        markdown += `- **Time to Interactive**: ${Math.round(lighthouse.timeToInteractive)}ms\n\n`;
      }
    }

    // Quality gates section
    markdown += '## 🎯 Quality Gates\n\n';
    const qualityGates = this.evaluateQualityGates(summary);

    for (const gate of qualityGates) {
      markdown += `- ${gate.status} **${gate.name}**: ${gate.message}\n`;
    }
    markdown += '\n';

    // Recommendations section
    markdown += '## 💡 Recommendations\n\n';
    const recommendations = this.generateRecommendations(summary, failures, performance);

    for (const rec of recommendations) {
      markdown += `- ${rec}\n`;
    }
    markdown += '\n';

    // Footer
    markdown += '---\n';
    markdown += `*Report generated by GitHub Actions on ${this.timestamp.toLocaleString()}*\n`;

    fs.writeFileSync('test-summary-report.md', markdown);
    console.log('✅ Markdown report generated: test-summary-report.md');
  }

  /**
   * Generate HTML report
   */
  async generateHTMLReport() {
    console.log('🌐 Generating HTML report...');

    const { summary, suites, failures } = this.results;
    let html = '';

    // HTML header
    html += '<!DOCTYPE html>\n';
    html += '<html lang="en">\n';
    html += '<head>\n';
    html += '    <meta charset="UTF-8">\n';
    html += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n';
    html += '    <title>Test Execution Report</title>\n';
    html += this.getHTMLStyles();
    html += '</head>\n';
    html += '<body>\n';

    // Header
    html += '    <div class="header">\n';
    html += '        <h1>🧪 Test Execution Report</h1>\n';
    html += `        <p class="meta">Generated: ${this.timestamp.toISOString()}</p>\n`;
    html += '    </div>\n';

    // Summary section
    html += '    <div class="section">\n';
    html += '        <h2>📊 Summary</h2>\n';
    html += '        <div class="summary-grid">\n';
    html += `            <div class="metric-card ${summary.failedTests === 0 ? 'success' : 'failure'}">\n`;
    html += '                <div class="metric-value">' + summary.totalTests + '</div>\n';
    html += '                <div class="metric-label">Total Tests</div>\n';
    html += '            </div>\n';
    html += `            <div class="metric-card success">\n`;
    html += '                <div class="metric-value">' + summary.passedTests + '</div>\n';
    html += '                <div class="metric-label">Passed</div>\n';
    html += '            </div>\n';
    html += `            <div class="metric-card ${summary.failedTests === 0 ? 'success' : 'failure'}">\n`;
    html += '                <div class="metric-value">' + summary.failedTests + '</div>\n';
    html += '                <div class="metric-label">Failed</div>\n';
    html += '            </div>\n';
    html += `            <div class="metric-card ${summary.successRate >= 95 ? 'success' : 'warning'}">\n`;
    html += '                <div class="metric-value">' + summary.successRate + '%</div>\n';
    html += '                <div class="metric-label">Success Rate</div>\n';
    html += '            </div>\n';
    html += '        </div>\n';
    html += '    </div>\n';

    // Coverage section
    if (summary.coverage && summary.coverage.lines.total > 0) {
      html += '    <div class="section">\n';
      html += '        <h2>📊 Coverage</h2>\n';
      html += '        <div class="coverage-bars">\n';
      html += this.generateCoverageBar('Lines', summary.coverage.lines.pct);
      html += this.generateCoverageBar('Functions', summary.coverage.functions.pct);
      html += this.generateCoverageBar('Statements', summary.coverage.statements.pct);
      html += this.generateCoverageBar('Branches', summary.coverage.branches.pct);
      html += '        </div>\n';
      html += '    </div>\n';
    }

    // Failures section
    if (failures && failures.length > 0) {
      html += '    <div class="section">\n';
      html += '        <h2>❌ Failures</h2>\n';
      html += '        <div class="failures">\n';

      for (const failure of failures.slice(0, 10)) {
        html += '            <div class="failure-item">\n';
        html += `                <h4>${failure.suite} - ${failure.test}</h4>\n`;
        html += `                <pre class="error-message">${this.escapeHtml(failure.message.substring(0, 500))}</pre>\n`;
        html += '            </div>\n';
      }

      html += '        </div>\n';
      html += '    </div>\n';
    }

    // Footer
    html += '    <div class="footer">\n';
    html += `        <p>Report generated on ${this.timestamp.toLocaleString()}</p>\n`;
    html += '    </div>\n';

    html += '</body>\n';
    html += '</html>\n';

    fs.writeFileSync('test-report.html', html);
    console.log('✅ HTML report generated: test-report.html');
  }

  /**
   * Generate console report
   */
  async generateConsoleReport() {
    console.log('📺 Generating console report...');

    const { summary } = this.results;
    let report = '';

    report += '\n🧪 TEST EXECUTION SUMMARY\n';
    report += '========================\n';
    report += `Total Tests:     ${summary.totalTests}\n`;
    report += `Passed:          ${summary.passedTests} ✅\n`;
    report += `Failed:          ${summary.failedTests} ${summary.failedTests > 0 ? '❌' : '✅'}\n`;
    report += `Success Rate:    ${summary.successRate}% ${summary.successRate >= 95 ? '✅' : '⚠️'}\n`;
    report += `Duration:        ${this.formatDuration(summary.duration)}\n`;

    if (summary.coverage && summary.coverage.lines.total > 0) {
      report += `\n📊 COVERAGE SUMMARY\n`;
      report += `==================\n`;
      report += `Lines:           ${summary.coverage.lines.pct}% ${summary.coverage.lines.pct >= 80 ? '✅' : '⚠️'}\n`;
      report += `Functions:       ${summary.coverage.functions.pct}% ${summary.coverage.functions.pct >= 80 ? '✅' : '⚠️'}\n`;
      report += `Statements:      ${summary.coverage.statements.pct}% ${summary.coverage.statements.pct >= 80 ? '✅' : '⚠️'}\n`;
      report += `Branches:        ${summary.coverage.branches.pct}% ${summary.coverage.branches.pct >= 70 ? '✅' : '⚠️'}\n`;
    }

    report += '\n';

    console.log(report);
    fs.writeFileSync('test-console-report.txt', report);
    console.log('✅ Console report generated: test-console-report.txt');
  }

  /**
   * Generate Slack-formatted report
   */
  async generateSlackReport() {
    console.log('💬 Generating Slack report...');

    const { summary } = this.results;
    const status = summary.failedTests === 0 ? 'success' : 'failure';
    const emoji = status === 'success' ? '✅' : '❌';
    const color = status === 'success' ? 'good' : 'danger';

    const slackPayload = {
      text: `${emoji} Test Results Summary`,
      attachments: [
        {
          color: color,
          fields: [
            {
              title: 'Total Tests',
              value: summary.totalTests.toString(),
              short: true
            },
            {
              title: 'Passed',
              value: summary.passedTests.toString(),
              short: true
            },
            {
              title: 'Failed',
              value: summary.failedTests.toString(),
              short: true
            },
            {
              title: 'Success Rate',
              value: `${summary.successRate}%`,
              short: true
            }
          ]
        }
      ]
    };

    if (summary.coverage && summary.coverage.lines.total > 0) {
      slackPayload.attachments.push({
        color: summary.coverage.lines.pct >= 80 ? 'good' : 'warning',
        title: 'Coverage Summary',
        fields: [
          {
            title: 'Lines',
            value: `${summary.coverage.lines.pct}%`,
            short: true
          },
          {
            title: 'Functions',
            value: `${summary.coverage.functions.pct}%`,
            short: true
          }
        ]
      });
    }

    fs.writeFileSync('slack-report.json', JSON.stringify(slackPayload, null, 2));
    console.log('✅ Slack report generated: slack-report.json');
  }

  /**
   * Evaluate quality gates
   */
  evaluateQualityGates(summary) {
    const gates = [];

    // Test success rate
    gates.push({
      name: 'Test Success Rate',
      status: summary.successRate >= 95 ? '✅' : '❌',
      message: `${summary.successRate}% (threshold: 95%)`
    });

    // Coverage gates
    if (summary.coverage && summary.coverage.lines.total > 0) {
      gates.push({
        name: 'Line Coverage',
        status: summary.coverage.lines.pct >= 80 ? '✅' : '❌',
        message: `${summary.coverage.lines.pct}% (threshold: 80%)`
      });

      gates.push({
        name: 'Function Coverage',
        status: summary.coverage.functions.pct >= 80 ? '✅' : '❌',
        message: `${summary.coverage.functions.pct}% (threshold: 80%)`
      });
    }

    // Failed tests
    gates.push({
      name: 'No Test Failures',
      status: summary.failedTests === 0 ? '✅' : '❌',
      message: summary.failedTests === 0 ? 'All tests passed' : `${summary.failedTests} tests failed`
    });

    return gates;
  }

  /**
   * Generate recommendations
   */
  generateRecommendations(summary, failures, performance) {
    const recommendations = [];

    if (summary.failedTests > 0) {
      recommendations.push('🔧 Fix failing tests to improve reliability');
    }

    if (summary.coverage && summary.coverage.lines.pct < 80) {
      recommendations.push('📊 Increase test coverage to meet quality standards');
    }

    if (performance && performance.slowestTests && performance.slowestTests.length > 0) {
      recommendations.push('⚡ Optimize slow-running tests to improve CI performance');
    }

    if (performance && performance.flakyTests && performance.flakyTests.length > 0) {
      recommendations.push('🎲 Investigate and fix flaky tests for better reliability');
    }

    if (summary.duration > 600000) { // > 10 minutes
      recommendations.push('⏱️ Consider parallelizing tests to reduce execution time');
    }

    if (recommendations.length === 0) {
      recommendations.push('🎉 Great job! All quality metrics are meeting targets');
    }

    return recommendations;
  }

  /**
   * Helper methods
   */
  getStatusIcon(condition) {
    return condition ? '✅' : '❌';
  }

  formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${Math.round(ms / 1000)}s`;
    return `${Math.round(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
  }

  escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  getHTMLStyles() {
    return `
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            line-height: 1.6;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            color: #2d3748;
        }
        .meta {
            color: #718096;
            font-size: 14px;
        }
        .section {
            background: white;
            margin-bottom: 20px;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .metric-card {
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e2e8f0;
        }
        .metric-card.success {
            border-color: #48bb78;
            background-color: #f0fff4;
        }
        .metric-card.failure {
            border-color: #f56565;
            background-color: #fff5f5;
        }
        .metric-card.warning {
            border-color: #ed8936;
            background-color: #fffaf0;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .metric-label {
            color: #718096;
            font-size: 14px;
        }
        .coverage-bars {
            margin-top: 20px;
        }
        .coverage-bar {
            margin-bottom: 15px;
        }
        .coverage-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-weight: 500;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        .progress-fill.high {
            background-color: #48bb78;
        }
        .progress-fill.medium {
            background-color: #ed8936;
        }
        .progress-fill.low {
            background-color: #f56565;
        }
        .failures {
            margin-top: 20px;
        }
        .failure-item {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            background-color: #fff5f5;
        }
        .failure-item h4 {
            margin: 0 0 10px 0;
            color: #c53030;
        }
        .error-message {
            background-color: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            margin: 0;
        }
        .footer {
            text-align: center;
            color: #718096;
            margin-top: 40px;
            padding: 20px;
        }
    </style>`;
  }

  generateCoverageBar(label, percentage) {
    const level = percentage >= 80 ? 'high' : percentage >= 60 ? 'medium' : 'low';
    return `
            <div class="coverage-bar">
                <div class="coverage-label">
                    <span>${label}</span>
                    <span>${percentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill ${level}" style="width: ${percentage}%"></div>
                </div>
            </div>`;
  }
}

// Main execution
async function main() {
  console.log('📝 Test Report Generator');
  console.log('========================');

  const generator = new TestReportGenerator();
  await generator.generateReports();

  console.log('\n✅ Test report generation completed!');
  console.log('📄 Generated files:');
  console.log('  - test-summary-report.md (Markdown)');
  console.log('  - test-report.html (HTML)');
  console.log('  - test-console-report.txt (Console)');
  console.log('  - slack-report.json (Slack)');
}

if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

module.exports = TestReportGenerator;