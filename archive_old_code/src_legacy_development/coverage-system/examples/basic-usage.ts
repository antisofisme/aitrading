/**
 * Basic Usage Examples for Coverage System
 * Demonstrates how to use the coverage system in different scenarios
 */

import CoverageSystem, { RecommendationContext } from '../index';
import { CoverageConfigManager } from '../config/coverage-config';

// Example 1: Basic Coverage Analysis
async function basicCoverageAnalysis() {
  console.log('=== Basic Coverage Analysis ===\n');

  // Define project context
  const context: RecommendationContext = {
    projectType: 'api',
    teamSize: 'medium',
    developmentStage: 'growth',
    testingMaturity: 'intermediate',
    codebaseSize: 'medium',
    domainCriticality: 'high'
  };

  // Create coverage system
  const coverageSystem = CoverageSystem.createDefault(context);

  try {
    // Initialize system
    await coverageSystem.initialize();

    // Analyze coverage from Jest output
    const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');

    console.log('Coverage Analysis Results:');
    console.log(`- Overall Coverage: ${result.coverage.summary.lines.lines}%`);
    console.log(`- Quality Gates Passed: ${result.coverage.qualityGateResults.filter(qg => qg.passed).length}/${result.coverage.qualityGateResults.length}`);
    console.log(`- Recommendations: ${result.recommendations.length}`);
    console.log(`- Reports Generated: ${result.reports.length}`);

    // Print top recommendations
    console.log('\nTop Recommendations:');
    result.recommendations.slice(0, 3).forEach((rec, index) => {
      console.log(`${index + 1}. ${rec.title} (${rec.priority} priority)`);
      console.log(`   ${rec.description}`);
    });

    // Shutdown system
    await coverageSystem.shutdown();

  } catch (error) {
    console.error('Coverage analysis failed:', error.message);
  }
}

// Example 2: CI/CD Integration
async function cicdIntegration() {
  console.log('\n=== CI/CD Integration ===\n');

  const context: RecommendationContext = {
    projectType: 'microservice',
    teamSize: 'large',
    developmentStage: 'mature',
    testingMaturity: 'advanced',
    codebaseSize: 'large',
    domainCriticality: 'critical'
  };

  // Create CI-optimized system
  const coverageSystem = CoverageSystem.createForCI(context);

  // Update CI/CD configuration
  await coverageSystem.updateConfiguration({
    cicd: {
      provider: 'github',
      repository: 'aitrading-platform/aitrading',
      branch: 'main',
      pullRequestId: process.env.PR_NUMBER,
      buildId: process.env.BUILD_ID,
      environment: 'staging'
    }
  });

  try {
    await coverageSystem.initialize();

    const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');

    // Check CI/CD result
    if (result.cicdResult?.success) {
      console.log('✅ CI/CD Quality Gates: PASSED');
      process.exit(0);
    } else {
      console.log('❌ CI/CD Quality Gates: FAILED');
      console.log(`Blocked by: ${result.cicdResult?.blockedByQualityGates ? 'Quality Gates' : 'Thresholds'}`);

      // Print failed quality gates
      result.cicdResult?.qualityGateResults
        .filter(qg => !qg.passed)
        .forEach(qg => {
          console.log(`- ${qg.gate.name}: ${qg.message}`);
        });

      process.exit(1);
    }

  } catch (error) {
    console.error('CI/CD integration failed:', error.message);
    process.exit(1);
  }
}

// Example 3: Custom Configuration
async function customConfiguration() {
  console.log('\n=== Custom Configuration ===\n');

  // Get configuration manager
  const configManager = CoverageConfigManager.getInstance();

  // Customize configuration
  const customConfig = configManager.getConfig();

  // Add custom modules
  customConfig.modules.push({
    path: 'src/trading-engine',
    name: 'Trading Engine',
    thresholds: { lines: 95, functions: 95, branches: 90, statements: 95 },
    critical: true,
    priority: 'high',
    tags: ['trading', 'business-critical', 'financial']
  });

  // Add custom quality gate
  customConfig.qualityGates.push({
    id: 'trading-gate',
    name: 'Trading Module Quality Gate',
    description: 'Ensures trading modules meet strict coverage requirements',
    enforced: true,
    blocking: true,
    conditions: [
      {
        metric: 'coverage',
        operator: 'gte',
        value: 95,
        threshold: 95,
        severity: 'blocker'
      }
    ]
  });

  // Update configuration
  configManager.updateConfig(customConfig);

  const context: RecommendationContext = {
    projectType: 'api',
    teamSize: 'medium',
    developmentStage: 'growth',
    testingMaturity: 'intermediate',
    codebaseSize: 'medium',
    domainCriticality: 'critical'
  };

  const coverageSystem = CoverageSystem.createDefault(context);

  try {
    await coverageSystem.initialize();

    const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');

    console.log('Custom Configuration Results:');
    console.log(`- Custom modules analyzed: ${result.metadata.modulesAnalyzed}`);
    console.log(`- Trading gate status: ${result.coverage.qualityGateResults.find(qg => qg.gate.id === 'trading-gate')?.passed ? 'PASSED' : 'FAILED'}`);

    await coverageSystem.shutdown();

  } catch (error) {
    console.error('Custom configuration failed:', error.message);
  }
}

// Example 4: Monitoring and Alerting
async function monitoringExample() {
  console.log('\n=== Monitoring and Alerting ===\n');

  const context: RecommendationContext = {
    projectType: 'web',
    teamSize: 'small',
    developmentStage: 'startup',
    testingMaturity: 'beginner',
    codebaseSize: 'small',
    domainCriticality: 'medium'
  };

  const coverageSystem = CoverageSystem.createDefault(context);

  // Configure monitoring with Slack alerts
  await coverageSystem.updateConfiguration({
    monitoring: {
      enabled: true,
      interval: 30000, // 30 seconds for demo
      thresholds: {
        coverageDecrease: 3, // Alert on 3% decrease
        qualityGateFailures: 1,
        consecutiveFailures: 1,
        trendDeclining: 3,
        hotspotIncrease: 2,
        responseTimeThreshold: 3000
      },
      alerts: {
        channels: [
          {
            type: 'slack',
            config: { webhook: process.env.SLACK_WEBHOOK },
            enabled: true,
            severityFilter: ['warning', 'error', 'critical']
          }
        ],
        severity: {
          coverageDecrease: 'warning',
          qualityGateFail: 'error',
          trendDeclining: 'warning',
          hotspotCritical: 'error',
          systemError: 'error'
        },
        throttling: {
          enabled: true,
          window: 10, // 10 minutes
          maxAlerts: 3,
          backoffMultiplier: 2
        },
        escalation: {
          enabled: false,
          levels: []
        }
      },
      automation: {
        enabled: true,
        actions: [
          {
            trigger: {
              event: 'coverage-decrease',
              threshold: { decrease: 5 }
            },
            action: {
              type: 'create-issue',
              config: {
                repository: 'owner/repo',
                title: 'Coverage Decrease Alert',
                template: 'coverage-decrease'
              }
            },
            conditions: [],
            enabled: true,
            rateLimit: 1 // Max 1 per hour
          }
        ],
        permissions: {
          createIssues: true,
          createPRs: false,
          blockMerges: false,
          runScripts: false,
          notifyTeams: true
        }
      },
      retention: {
        alerts: 30,
        metrics: 90,
        events: 7,
        reports: 30
      }
    }
  });

  try {
    await coverageSystem.initialize();

    // Set up event listeners
    const monitor = (coverageSystem as any).monitor;

    monitor.on('alert', (alert: any) => {
      console.log(`🚨 Alert: ${alert.title} (${alert.severity})`);
      console.log(`   ${alert.message}`);
    });

    monitor.on('event', (event: any) => {
      if (event.severity === 'error' || event.severity === 'critical') {
        console.log(`📊 Event: ${event.type} (${event.severity})`);
      }
    });

    // Analyze coverage multiple times to demonstrate monitoring
    console.log('Running monitoring demo...');

    for (let i = 0; i < 3; i++) {
      console.log(`\nAnalysis ${i + 1}:`);
      const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');
      console.log(`Coverage: ${result.coverage.summary.lines.lines}%`);

      // Wait between analyses
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    // Get monitoring metrics
    const metrics = coverageSystem.getMonitoringMetrics();
    console.log('\nMonitoring Metrics:');
    console.log(`- Events processed: ${metrics.eventsProcessed}`);
    console.log(`- Alerts sent: ${metrics.alertsSent}`);
    console.log(`- Automation runs: ${metrics.automationRuns}`);

    await coverageSystem.shutdown();

  } catch (error) {
    console.error('Monitoring example failed:', error.message);
  }
}

// Example 5: Module-Level Analysis
async function moduleAnalysis() {
  console.log('\n=== Module-Level Analysis ===\n');

  const context: RecommendationContext = {
    projectType: 'api',
    teamSize: 'medium',
    developmentStage: 'growth',
    testingMaturity: 'intermediate',
    codebaseSize: 'medium',
    domainCriticality: 'high'
  };

  const coverageSystem = CoverageSystem.createDefault(context);

  try {
    await coverageSystem.initialize();

    const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');

    // Analyze specific modules
    console.log('Module Analysis:');

    for (const moduleAnalysis of result.coverage.moduleAnalysis) {
      console.log(`\n📦 ${moduleAnalysis.module.name}:`);
      console.log(`   Coverage: ${moduleAnalysis.coverage.lines.lines}%`);
      console.log(`   Status: ${moduleAnalysis.passed ? '✅ PASSED' : '❌ FAILED'}`);
      console.log(`   Files: ${moduleAnalysis.files.length}`);
      console.log(`   Score: ${moduleAnalysis.score}/100`);

      if (moduleAnalysis.violations.length > 0) {
        console.log(`   Violations: ${moduleAnalysis.violations.map(v => v.metric).join(', ')}`);
      }
    }

    // Compare modules
    const moduleIds = result.coverage.moduleAnalysis.map(ma => ma.module.name.toLowerCase().replace(/\s+/g, '-'));
    const comparison = await coverageSystem.compareModules(moduleIds.slice(0, 3));

    console.log('\nModule Comparison:');
    comparison.rankings
      .filter(r => r.category === 'coverage')
      .forEach(ranking => {
        console.log(`${ranking.rank}. ${ranking.moduleId}: ${ranking.score.toFixed(1)}% (${ranking.percentile.toFixed(0)}th percentile)`);
      });

    await coverageSystem.shutdown();

  } catch (error) {
    console.error('Module analysis failed:', error.message);
  }
}

// Example 6: Trend Analysis and Predictions
async function trendAnalysis() {
  console.log('\n=== Trend Analysis and Predictions ===\n');

  const context: RecommendationContext = {
    projectType: 'api',
    teamSize: 'medium',
    developmentStage: 'mature',
    testingMaturity: 'advanced',
    codebaseSize: 'large',
    domainCriticality: 'high'
  };

  const coverageSystem = CoverageSystem.createDefault(context);

  try {
    await coverageSystem.initialize();

    // Analyze coverage to populate trend data
    const result = await coverageSystem.analyzeCoverage('./coverage/coverage-final.json');

    if (result.trends) {
      console.log('Trend Analysis:');
      console.log(`- Overall trend: ${result.trends.trend.overall} (${result.trends.trend.confidence.toFixed(1)}% confidence)`);
      console.log(`- Data points: ${result.trends.dataPoints}`);
      console.log(`- Monthly change: ${result.trends.velocity.monthlyChange >= 0 ? '+' : ''}${result.trends.velocity.monthlyChange.toFixed(2)}%`);
      console.log(`- Volatility: ${result.trends.velocity.volatility.toFixed(2)}`);

      // Show patterns
      if (result.trends.patterns.length > 0) {
        console.log('\nDetected Patterns:');
        result.trends.patterns.forEach(pattern => {
          console.log(`- ${pattern.type}: ${pattern.description} (${(pattern.strength * 100).toFixed(1)}% strength)`);
        });
      }

      // Show predictions
      if (result.trends.predictions.length > 0) {
        console.log('\nPredictions:');
        const likelyPredictions = result.trends.predictions.filter(p => p.scenario === 'likely');
        likelyPredictions.forEach(prediction => {
          console.log(`- ${prediction.timeframe}: ${prediction.predicted.lines.lines.toFixed(1)}% (${prediction.confidence.toFixed(0)}% confidence)`);
        });
      }

      // Show insights
      if (result.trends.insights.length > 0) {
        console.log('\nInsights:');
        result.trends.insights.forEach(insight => {
          console.log(`- ${insight.title}: ${insight.description}`);
        });
      }
    }

    // Export trend data
    await coverageSystem.exportTrendData('./coverage-trends.json', 'json');
    console.log('\nTrend data exported to coverage-trends.json');

    await coverageSystem.shutdown();

  } catch (error) {
    console.error('Trend analysis failed:', error.message);
  }
}

// Main execution function
async function runExamples() {
  console.log('🎯 Coverage System Examples\n');

  const examples = [
    { name: 'Basic Coverage Analysis', fn: basicCoverageAnalysis },
    { name: 'CI/CD Integration', fn: cicdIntegration },
    { name: 'Custom Configuration', fn: customConfiguration },
    { name: 'Monitoring and Alerting', fn: monitoringExample },
    { name: 'Module-Level Analysis', fn: moduleAnalysis },
    { name: 'Trend Analysis and Predictions', fn: trendAnalysis }
  ];

  // Get example to run from command line argument
  const exampleName = process.argv[2];

  if (exampleName) {
    const example = examples.find(ex =>
      ex.name.toLowerCase().replace(/\s+/g, '-') === exampleName.toLowerCase()
    );

    if (example) {
      await example.fn();
    } else {
      console.log('Available examples:');
      examples.forEach(ex => {
        console.log(`- ${ex.name.toLowerCase().replace(/\s+/g, '-')}`);
      });
    }
  } else {
    // Run all examples
    for (const example of examples) {
      try {
        await example.fn();
      } catch (error) {
        console.error(`Example "${example.name}" failed:`, error.message);
      }
    }
  }
}

// Export for use as library
export {
  basicCoverageAnalysis,
  cicdIntegration,
  customConfiguration,
  monitoringExample,
  moduleAnalysis,
  trendAnalysis
};

// Run examples if called directly
if (require.main === module) {
  runExamples().catch(console.error);
}