#!/usr/bin/env node

/**
 * Coverage System CLI
 * Command-line interface for the coverage system
 */

import * as fs from 'fs';
import * as path from 'path';
import { program } from 'commander';
import CoverageSystem, { RecommendationContext } from '../index';

// Version from package.json
const packageJson = JSON.parse(fs.readFileSync(path.join(__dirname, '../../../package.json'), 'utf-8'));
const version = packageJson.version;

program
  .name('coverage-system')
  .description('AI Trading Platform Coverage System CLI')
  .version(version);

// Default context (can be overridden via config file)
const defaultContext: RecommendationContext = {
  projectType: 'api',
  teamSize: 'medium',
  developmentStage: 'growth',
  testingMaturity: 'intermediate',
  codebaseSize: 'medium',
  domainCriticality: 'high'
};

// Analyze command
program
  .command('analyze')
  .description('Analyze coverage from a coverage file')
  .option('-i, --input <path>', 'Coverage input file path', './coverage/coverage-final.json')
  .option('-o, --output <path>', 'Output directory for reports', './coverage-reports')
  .option('-f, --format <formats>', 'Report formats (comma-separated)', 'html,json')
  .option('-c, --config <path>', 'Configuration file path', './coverage-system.config.json')
  .option('--ci', 'Run in CI mode with quality gates')
  .option('--fail-on-threshold', 'Fail if coverage thresholds are not met')
  .option('--no-reports', 'Skip report generation')
  .action(async (options) => {
    try {
      console.log('🎯 Starting coverage analysis...\n');

      // Load configuration
      const config = await loadConfiguration(options.config);
      const context = config.context || defaultContext;

      // Create coverage system
      const coverageSystem = options.ci
        ? CoverageSystem.createForCI(context)
        : CoverageSystem.createDefault(context);

      // Update configuration with CLI options
      if (options.output || options.format) {
        await coverageSystem.updateConfiguration({
          reporting: {
            formats: options.format.split(','),
            outputDir: options.output,
            includeVisualizations: true,
            includeSourceCode: true,
            generateTrendReports: true,
            generateRecommendationReports: true
          }
        });
      }

      // Initialize and analyze
      await coverageSystem.initialize();
      const result = await coverageSystem.analyzeCoverage(options.input);

      // Print results
      console.log('📊 Analysis Results:');
      console.log(`   Overall Coverage: ${result.coverage.summary.lines.lines}%`);
      console.log(`   Quality Gates: ${result.coverage.qualityGateResults.filter(qg => qg.passed).length}/${result.coverage.qualityGateResults.length} passed`);
      console.log(`   Recommendations: ${result.recommendations.length}`);
      console.log(`   Files Analyzed: ${result.metadata.filesAnalyzed}`);
      console.log(`   Duration: ${result.metadata.duration}ms`);

      if (!options.noReports) {
        console.log(`\n📄 Reports Generated:`);
        result.reports.forEach(report => {
          console.log(`   ${report.format.toUpperCase()}: ${report.path}`);
        });
      }

      // Show critical recommendations
      const criticalRecs = result.recommendations.filter(r => r.priority === 'critical');
      if (criticalRecs.length > 0) {
        console.log(`\n🚨 Critical Recommendations:`);
        criticalRecs.forEach((rec, index) => {
          console.log(`   ${index + 1}. ${rec.title}`);
          console.log(`      ${rec.description}`);
        });
      }

      // Handle CI mode
      if (options.ci && result.cicdResult) {
        if (!result.cicdResult.success) {
          console.error('\n❌ CI/CD Quality Gates Failed');
          if (result.cicdResult.blockedByQualityGates) {
            console.error('   Blocked by quality gate failures');
          }
          process.exit(1);
        } else {
          console.log('\n✅ CI/CD Quality Gates Passed');
        }
      }

      // Handle fail on threshold
      if (options.failOnThreshold) {
        const failedGates = result.coverage.qualityGateResults.filter(qg => !qg.passed);
        if (failedGates.length > 0) {
          console.error(`\n❌ ${failedGates.length} quality gates failed`);
          process.exit(1);
        }
      }

      await coverageSystem.shutdown();

    } catch (error) {
      console.error('❌ Coverage analysis failed:', error.message);
      process.exit(1);
    }
  });

// Monitor command
program
  .command('monitor')
  .description('Start coverage monitoring daemon')
  .option('-i, --interval <ms>', 'Monitoring interval in milliseconds', '60000')
  .option('-c, --config <path>', 'Configuration file path', './coverage-system.config.json')
  .option('--alerts', 'Enable alerts (requires configuration)')
  .option('--automation', 'Enable automation actions')
  .action(async (options) => {
    try {
      console.log('🔍 Starting coverage monitoring...\n');

      // Load configuration
      const config = await loadConfiguration(options.config);
      const context = config.context || defaultContext;

      // Create coverage system
      const coverageSystem = CoverageSystem.createDefault(context);

      // Configure monitoring
      await coverageSystem.updateConfiguration({
        monitoring: {
          enabled: true,
          interval: parseInt(options.interval),
          thresholds: config.monitoring?.thresholds || {
            coverageDecrease: 5,
            qualityGateFailures: 1,
            consecutiveFailures: 2,
            trendDeclining: 7,
            hotspotIncrease: 3,
            responseTimeThreshold: 5000
          },
          alerts: config.monitoring?.alerts || {
            channels: [],
            severity: {
              coverageDecrease: 'warning',
              qualityGateFail: 'error',
              trendDeclining: 'warning',
              hotspotCritical: 'error',
              systemError: 'error'
            },
            throttling: {
              enabled: true,
              window: 30,
              maxAlerts: 5,
              backoffMultiplier: 2
            },
            escalation: {
              enabled: false,
              levels: []
            }
          },
          automation: {
            enabled: options.automation,
            actions: config.monitoring?.automation?.actions || [],
            permissions: config.monitoring?.automation?.permissions || {
              createIssues: false,
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

      // Initialize and start monitoring
      await coverageSystem.initialize();

      // Set up event listeners
      const monitor = (coverageSystem as any).monitor;

      monitor.on('alert', (alert: any) => {
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] 🚨 ALERT: ${alert.title} (${alert.severity})`);
        console.log(`             ${alert.message}`);
      });

      monitor.on('event', (event: any) => {
        if (event.severity === 'error' || event.severity === 'critical') {
          const timestamp = new Date().toLocaleTimeString();
          console.log(`[${timestamp}] 📊 EVENT: ${event.type} (${event.severity})`);
        }
      });

      console.log(`✅ Monitoring started (interval: ${options.interval}ms)`);
      console.log('📡 Listening for coverage events...');
      console.log('🔄 Press Ctrl+C to stop monitoring\n');

      // Handle graceful shutdown
      process.on('SIGINT', async () => {
        console.log('\n🛑 Stopping coverage monitoring...');
        await coverageSystem.shutdown();
        console.log('✅ Monitoring stopped');
        process.exit(0);
      });

      // Keep the process running
      await new Promise(() => {}); // Run indefinitely

    } catch (error) {
      console.error('❌ Monitoring failed:', error.message);
      process.exit(1);
    }
  });

// Report command
program
  .command('report')
  .description('Generate coverage reports from existing data')
  .option('-i, --input <path>', 'Coverage input file path', './coverage/coverage-final.json')
  .option('-o, --output <path>', 'Output directory for reports', './coverage-reports')
  .option('-f, --format <formats>', 'Report formats (comma-separated)', 'html,json,markdown')
  .option('-c, --config <path>', 'Configuration file path', './coverage-system.config.json')
  .option('--trends', 'Include trend analysis')
  .option('--recommendations', 'Include recommendations')
  .option('--no-charts', 'Disable chart generation')
  .action(async (options) => {
    try {
      console.log('📄 Generating coverage reports...\n');

      // Load configuration
      const config = await loadConfiguration(options.config);
      const context = config.context || defaultContext;

      // Create coverage system
      const coverageSystem = CoverageSystem.createDefault(context);

      // Configure reporting
      await coverageSystem.updateConfiguration({
        reporting: {
          formats: options.format.split(','),
          outputDir: options.output,
          includeVisualizations: !options.noCharts,
          includeSourceCode: true,
          generateTrendReports: options.trends,
          generateRecommendationReports: options.recommendations
        }
      });

      // Initialize and generate reports
      await coverageSystem.initialize();

      // Load coverage data for custom report generation
      const { CoverageAnalyzer } = await import('../core/coverage-analyzer');
      const analyzer = new CoverageAnalyzer();
      const coverageData = await analyzer.loadCoverageData(options.input);

      const reports = await coverageSystem.generateCustomReport(coverageData, {
        formats: options.format.split(','),
        outputDir: options.output,
        includeVisualizations: !options.noCharts,
        generateTrendReports: options.trends,
        generateRecommendationReports: options.recommendations
      });

      console.log('✅ Reports generated successfully:');
      reports.forEach(report => {
        console.log(`   ${report.format.toUpperCase()}: ${report.path} (${formatBytes(report.size)})`);
      });

      await coverageSystem.shutdown();

    } catch (error) {
      console.error('❌ Report generation failed:', error.message);
      process.exit(1);
    }
  });

// Trends command
program
  .command('trends')
  .description('Analyze and display coverage trends')
  .option('-t, --timespan <period>', 'Time period for analysis', '30days')
  .option('-e, --export <path>', 'Export trends to file')
  .option('-f, --format <format>', 'Export format (json|csv)', 'json')
  .option('-c, --config <path>', 'Configuration file path', './coverage-system.config.json')
  .action(async (options) => {
    try {
      console.log('📈 Analyzing coverage trends...\n');

      // Load configuration
      const config = await loadConfiguration(options.config);
      const context = config.context || defaultContext;

      // Create coverage system
      const coverageSystem = CoverageSystem.createDefault(context);
      await coverageSystem.initialize();

      // Get trend analysis
      const trendAnalysis = coverageSystem.getTrendAnalysis(options.timespan);

      // Display results
      console.log('📊 Trend Analysis Results:');
      console.log(`   Time Period: ${trendAnalysis.timespan}`);
      console.log(`   Data Points: ${trendAnalysis.dataPoints}`);
      console.log(`   Overall Trend: ${trendAnalysis.trend.overall} (${trendAnalysis.trend.confidence.toFixed(1)}% confidence)`);
      console.log(`   Monthly Change: ${trendAnalysis.velocity.monthlyChange >= 0 ? '+' : ''}${trendAnalysis.velocity.monthlyChange.toFixed(2)}%`);
      console.log(`   Volatility: ${trendAnalysis.velocity.volatility.toFixed(2)}`);

      // Show patterns
      if (trendAnalysis.patterns.length > 0) {
        console.log('\n🔍 Detected Patterns:');
        trendAnalysis.patterns.forEach(pattern => {
          console.log(`   ${pattern.type}: ${pattern.description} (${(pattern.strength * 100).toFixed(1)}% strength)`);
        });
      }

      // Show predictions
      const likelyPredictions = trendAnalysis.predictions.filter(p => p.scenario === 'likely');
      if (likelyPredictions.length > 0) {
        console.log('\n🔮 Predictions:');
        likelyPredictions.forEach(prediction => {
          console.log(`   ${prediction.timeframe}: ${prediction.predicted.lines.lines.toFixed(1)}% (${prediction.confidence.toFixed(0)}% confidence)`);
        });
      }

      // Show insights
      if (trendAnalysis.insights.length > 0) {
        console.log('\n💡 Insights:');
        trendAnalysis.insights.forEach(insight => {
          console.log(`   ${insight.title}: ${insight.description}`);
        });
      }

      // Export if requested
      if (options.export) {
        await coverageSystem.exportTrendData(options.export, options.format);
        console.log(`\n💾 Trends exported to: ${options.export}`);
      }

      await coverageSystem.shutdown();

    } catch (error) {
      console.error('❌ Trend analysis failed:', error.message);
      process.exit(1);
    }
  });

// Config command
program
  .command('config')
  .description('Manage coverage system configuration')
  .option('--init', 'Initialize default configuration file')
  .option('--validate <path>', 'Validate configuration file')
  .option('--export <path>', 'Export current configuration')
  .action(async (options) => {
    try {
      if (options.init) {
        await initializeConfig();
      } else if (options.validate) {
        await validateConfig(options.validate);
      } else if (options.export) {
        await exportConfig(options.export);
      } else {
        console.log('Please specify an action: --init, --validate, or --export');
      }
    } catch (error) {
      console.error('❌ Configuration operation failed:', error.message);
      process.exit(1);
    }
  });

// Examples command
program
  .command('examples')
  .description('Run coverage system examples')
  .option('-e, --example <name>', 'Specific example to run')
  .action(async (options) => {
    try {
      const examplesPath = path.join(__dirname, '../examples/basic-usage.js');

      if (options.example) {
        const { spawn } = require('child_process');
        const child = spawn('node', [examplesPath, options.example], { stdio: 'inherit' });

        child.on('close', (code) => {
          process.exit(code);
        });
      } else {
        console.log('📚 Available examples:');
        console.log('   - basic-coverage-analysis');
        console.log('   - ci-cd-integration');
        console.log('   - custom-configuration');
        console.log('   - monitoring-and-alerting');
        console.log('   - module-level-analysis');
        console.log('   - trend-analysis-and-predictions');
        console.log('\nRun with: coverage-system examples --example <name>');
      }
    } catch (error) {
      console.error('❌ Examples failed:', error.message);
      process.exit(1);
    }
  });

// Helper functions
async function loadConfiguration(configPath: string): Promise<any> {
  try {
    if (fs.existsSync(configPath)) {
      const configContent = fs.readFileSync(configPath, 'utf-8');
      return JSON.parse(configContent);
    }
  } catch (error) {
    console.warn(`⚠️  Could not load configuration from ${configPath}, using defaults`);
  }
  return {};
}

async function initializeConfig(): Promise<void> {
  const configPath = './coverage-system.config.json';

  if (fs.existsSync(configPath)) {
    console.log('⚠️  Configuration file already exists');
    return;
  }

  const defaultConfig = {
    context: defaultContext,
    coverage: {
      global: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      },
      modules: [
        {
          path: 'src/core',
          name: 'Core Module',
          thresholds: { lines: 90, functions: 90, branches: 85, statements: 90 },
          critical: true,
          priority: 'high',
          tags: ['core', 'critical']
        }
      ],
      qualityGates: [
        {
          id: 'minimum-coverage',
          name: 'Minimum Coverage Gate',
          description: 'Ensures minimum coverage standards are met',
          enforced: true,
          blocking: true,
          conditions: [
            {
              metric: 'coverage',
              operator: 'gte',
              value: 80,
              threshold: 80,
              severity: 'blocker'
            }
          ]
        }
      ]
    },
    monitoring: {
      thresholds: {
        coverageDecrease: 5,
        qualityGateFailures: 1,
        consecutiveFailures: 2,
        trendDeclining: 7,
        hotspotIncrease: 3,
        responseTimeThreshold: 5000
      },
      alerts: {
        channels: [],
        severity: {
          coverageDecrease: 'warning',
          qualityGateFail: 'error',
          trendDeclining: 'warning',
          hotspotCritical: 'error',
          systemError: 'error'
        }
      },
      automation: {
        actions: [],
        permissions: {
          createIssues: false,
          createPRs: false,
          blockMerges: false,
          runScripts: false,
          notifyTeams: true
        }
      }
    }
  };

  fs.writeFileSync(configPath, JSON.stringify(defaultConfig, null, 2));
  console.log(`✅ Configuration file created: ${configPath}`);
}

async function validateConfig(configPath: string): Promise<void> {
  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));

    // Basic validation
    const required = ['context', 'coverage'];
    const missing = required.filter(field => !config[field]);

    if (missing.length > 0) {
      console.error(`❌ Missing required fields: ${missing.join(', ')}`);
      return;
    }

    console.log('✅ Configuration is valid');
  } catch (error) {
    console.error(`❌ Invalid configuration: ${error.message}`);
  }
}

async function exportConfig(outputPath: string): Promise<void> {
  const { CoverageConfigManager } = await import('../config/coverage-config');
  const configManager = CoverageConfigManager.getInstance();
  const config = configManager.exportConfig();

  fs.writeFileSync(outputPath, config);
  console.log(`✅ Configuration exported to: ${outputPath}`);
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Parse command line arguments
program.parse();

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.outputHelp();
}