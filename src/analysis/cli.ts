#!/usr/bin/env node

/**
 * CLI Interface for AI Trading System Code Analysis Engine
 * Provides command-line access to analysis capabilities
 */

import { Command } from 'commander';
import { promises as fs } from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import {
  createAnalysisEngine,
  analyzeCodebase,
  generateTradingSummary,
  defaultConfig,
  defaultLogger
} from './index';
import {
  AnalysisConfig,
  DiagramType,
  ElementType,
  RelationshipType
} from './types';

const program = new Command();

// Enhanced logger with colors
const cliLogger = {
  debug: (message: string, ...args: any[]) => {
    if (process.env.DEBUG) {
      console.debug(chalk.gray(`[DEBUG] ${message}`), ...args);
    }
  },
  info: (message: string, ...args: any[]) => {
    console.info(chalk.blue(`[INFO] ${message}`), ...args);
  },
  warn: (message: string, ...args: any[]) => {
    console.warn(chalk.yellow(`[WARN] ${message}`), ...args);
  },
  error: (message: string, ...args: any[]) => {
    console.error(chalk.red(`[ERROR] ${message}`), ...args);
  }
};

program
  .name('aitrading-analysis')
  .description('AI Trading System Code Analysis Engine')
  .version('1.0.0');

// Analyze command
program
  .command('analyze')
  .description('Analyze the AI trading system codebase')
  .option('-p, --path <path>', 'Target path to analyze', '.')
  .option('-c, --config <config>', 'Configuration file path')
  .option('-o, --output <output>', 'Output directory', './analysis-output')
  .option('--no-cache', 'Disable caching')
  .option('--no-hooks', 'Disable Claude Flow hooks')
  .option('-f, --format <formats...>', 'Output formats (json, mermaid, yaml)', ['json', 'mermaid'])
  .option('-w, --watch', 'Watch for file changes')
  .option('--trading-only', 'Analyze only trading-related components')
  .action(async (options) => {
    const spinner = ora('Initializing analysis engine...').start();

    try {
      // Load configuration
      let config = { ...defaultConfig };
      if (options.config) {
        const configPath = path.resolve(options.config);
        const configContent = await fs.readFile(configPath, 'utf-8');
        const userConfig = JSON.parse(configContent);
        config = { ...config, ...userConfig };
      }

      // Apply CLI options
      if (!options.cache) {
        config.cache.enabled = false;
      }
      if (!options.hooks) {
        config.hooks.enabled = false;
      }
      config.output.directory = options.output;
      config.output.formats = options.format;

      // Filter for trading components only
      if (options.tradingOnly) {
        config.parsers = config.parsers.filter(p =>
          ['trading-pattern', 'typescript', 'javascript'].includes(p.name)
        );
        config.analyzers = config.analyzers.filter(a =>
          ['trading-patterns', 'risk-assessment'].includes(a.name)
        );
      }

      spinner.text = 'Creating analysis engine...';
      const engine = createAnalysisEngine(config, cliLogger);

      spinner.text = 'Initializing...';
      await engine.initialize();

      if (options.watch) {
        spinner.succeed('Analysis engine initialized in watch mode');
        console.log(chalk.green('👁  Watching for file changes...'));

        await engine.startWatching(options.path);

        // Keep the process running
        process.on('SIGINT', async () => {
          console.log(chalk.yellow('\n⏹  Stopping watch mode...'));
          await engine.stopWatching();
          await engine.dispose();
          process.exit(0);
        });

        // Perform initial analysis
        spinner.start('Performing initial analysis...');
        const result = await engine.analyze(options.path);
        await saveResults(result, config.output.directory, config.output.formats);
        spinner.succeed(`Initial analysis complete. Results saved to ${config.output.directory}`);

      } else {
        spinner.text = 'Analyzing codebase...';
        const result = await engine.analyze(options.path);

        spinner.text = 'Saving results...';
        await saveResults(result, config.output.directory, config.output.formats);

        spinner.succeed('Analysis complete!');
        await engine.dispose();

        // Display summary
        displaySummary(result);
      }

    } catch (error) {
      spinner.fail('Analysis failed');
      cliLogger.error('Analysis error:', error);
      process.exit(1);
    }
  });

// Summary command
program
  .command('summary')
  .description('Generate a trading system analysis summary')
  .option('-p, --path <path>', 'Target path to analyze', '.')
  .option('-c, --config <config>', 'Configuration file path')
  .option('-o, --output <output>', 'Output file path')
  .action(async (options) => {
    const spinner = ora('Generating summary...').start();

    try {
      let config = { ...defaultConfig };
      if (options.config) {
        const configPath = path.resolve(options.config);
        const configContent = await fs.readFile(configPath, 'utf-8');
        const userConfig = JSON.parse(configContent);
        config = { ...config, ...userConfig };
      }

      const summary = await generateTradingSummary(options.path, config, cliLogger);

      if (options.output) {
        await fs.writeFile(options.output, summary);
        spinner.succeed(`Summary saved to ${options.output}`);
      } else {
        spinner.succeed('Summary generated');
        console.log('\n' + summary);
      }

    } catch (error) {
      spinner.fail('Summary generation failed');
      cliLogger.error('Summary error:', error);
      process.exit(1);
    }
  });

// Diagrams command
program
  .command('diagrams')
  .description('Generate specific diagram types')
  .option('-p, --path <path>', 'Target path to analyze', '.')
  .option('-t, --type <type>', 'Diagram type', 'all')
  .option('-o, --output <output>', 'Output directory', './diagrams')
  .option('--theme <theme>', 'Mermaid theme (default, dark, forest, neutral)', 'default')
  .action(async (options) => {
    const spinner = ora('Generating diagrams...').start();

    try {
      const engine = createAnalysisEngine(defaultConfig, cliLogger);
      await engine.initialize();

      spinner.text = 'Analyzing codebase...';
      const result = await engine.analyze(options.path);

      spinner.text = 'Generating diagrams...';
      await fs.mkdir(options.output, { recursive: true });

      const diagramsToGenerate = options.type === 'all'
        ? result.diagrams
        : result.diagrams.filter(d => d.type === options.type);

      for (const diagram of diagramsToGenerate) {
        const fileName = `${diagram.type}-${diagram.id}.mmd`;
        const filePath = path.join(options.output, fileName);
        await fs.writeFile(filePath, diagram.content);
      }

      await engine.dispose();
      spinner.succeed(`Generated ${diagramsToGenerate.length} diagrams in ${options.output}`);

    } catch (error) {
      spinner.fail('Diagram generation failed');
      cliLogger.error('Diagram error:', error);
      process.exit(1);
    }
  });

// Interactive command
program
  .command('interactive')
  .alias('i')
  .description('Interactive analysis configuration')
  .action(async () => {
    console.log(chalk.cyan('🔍 AI Trading System Analysis - Interactive Mode\n'));

    try {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'path',
          message: 'Enter the path to analyze:',
          default: '.'
        },
        {
          type: 'checkbox',
          name: 'parsers',
          message: 'Select parsers to enable:',
          choices: [
            { name: 'TypeScript Parser', value: 'typescript', checked: true },
            { name: 'JavaScript Parser', value: 'javascript', checked: true },
            { name: 'Trading Pattern Parser', value: 'trading-pattern', checked: true },
            { name: 'Database Schema Parser', value: 'database-schema', checked: false },
            { name: 'API Endpoint Parser', value: 'api-endpoint', checked: false }
          ]
        },
        {
          type: 'checkbox',
          name: 'analyzers',
          message: 'Select analyzers to enable:',
          choices: [
            { name: 'Complexity Analysis', value: 'complexity', checked: true },
            { name: 'Dependency Analysis', value: 'dependencies', checked: true },
            { name: 'Trading Patterns', value: 'trading-patterns', checked: true },
            { name: 'Risk Assessment', value: 'risk-assessment', checked: true }
          ]
        },
        {
          type: 'checkbox',
          name: 'diagrams',
          message: 'Select diagram types to generate:',
          choices: [
            { name: 'Class Diagram', value: 'classDiagram', checked: true },
            { name: 'Flow Chart', value: 'flowchart', checked: true },
            { name: 'Trading Flow', value: 'tradingFlow', checked: true },
            { name: 'Risk Diagram', value: 'riskDiagram', checked: true },
            { name: 'Data Flow', value: 'dataFlow', checked: false },
            { name: 'ER Diagram', value: 'erDiagram', checked: false },
            { name: 'Sequence Diagram', value: 'sequenceDiagram', checked: false }
          ]
        },
        {
          type: 'confirm',
          name: 'enableCache',
          message: 'Enable caching?',
          default: true
        },
        {
          type: 'confirm',
          name: 'enableHooks',
          message: 'Enable Claude Flow hooks?',
          default: true
        },
        {
          type: 'input',
          name: 'output',
          message: 'Output directory:',
          default: './analysis-output'
        }
      ]);

      // Build configuration
      const config = { ...defaultConfig };

      config.parsers = config.parsers.map(p => ({
        ...p,
        enabled: answers.parsers.includes(p.name)
      }));

      config.analyzers = config.analyzers.map(a => ({
        ...a,
        enabled: answers.analyzers.includes(a.name)
      }));

      config.cache.enabled = answers.enableCache;
      config.hooks.enabled = answers.enableHooks;
      config.output.directory = answers.output;

      // Run analysis
      const spinner = ora('Running interactive analysis...').start();

      const engine = createAnalysisEngine(config, cliLogger);
      await engine.initialize();

      const result = await engine.analyze(answers.path);
      await saveResults(result, config.output.directory, ['json', 'mermaid']);

      await engine.dispose();
      spinner.succeed('Interactive analysis complete!');

      displaySummary(result);

    } catch (error) {
      cliLogger.error('Interactive analysis failed:', error);
      process.exit(1);
    }
  });

// Config command
program
  .command('config')
  .description('Generate or validate configuration file')
  .option('-g, --generate', 'Generate default configuration file')
  .option('-v, --validate <config>', 'Validate configuration file')
  .option('-o, --output <output>', 'Output configuration file', 'analysis.config.json')
  .action(async (options) => {
    if (options.generate) {
      const spinner = ora('Generating configuration file...').start();

      try {
        const configContent = JSON.stringify(defaultConfig, null, 2);
        await fs.writeFile(options.output, configContent);
        spinner.succeed(`Configuration file generated: ${options.output}`);

        console.log(chalk.green('\n📝 Configuration file contents:'));
        console.log(configContent);

      } catch (error) {
        spinner.fail('Failed to generate configuration file');
        cliLogger.error('Config generation error:', error);
        process.exit(1);
      }

    } else if (options.validate) {
      const spinner = ora('Validating configuration file...').start();

      try {
        const configPath = path.resolve(options.validate);
        const configContent = await fs.readFile(configPath, 'utf-8');
        const config = JSON.parse(configContent);

        // Basic validation
        const requiredFields = ['include', 'exclude', 'parsers', 'analyzers', 'cache', 'hooks', 'output'];
        const missingFields = requiredFields.filter(field => !(field in config));

        if (missingFields.length > 0) {
          throw new Error(`Missing required fields: ${missingFields.join(', ')}`);
        }

        spinner.succeed('Configuration file is valid');
        console.log(chalk.green('\n✅ Configuration validation passed'));

      } catch (error) {
        spinner.fail('Configuration validation failed');
        cliLogger.error('Config validation error:', error);
        process.exit(1);
      }

    } else {
      console.log(chalk.yellow('Please specify --generate or --validate option'));
      program.help();
    }
  });

// Utility functions

async function saveResults(result: any, outputDir: string, formats: string[]): Promise<void> {
  await fs.mkdir(outputDir, { recursive: true });

  for (const format of formats) {
    switch (format) {
      case 'json':
        const jsonPath = path.join(outputDir, 'analysis-result.json');
        await fs.writeFile(jsonPath, JSON.stringify(result, null, 2));
        break;

      case 'mermaid':
        const mermaidDir = path.join(outputDir, 'diagrams');
        await fs.mkdir(mermaidDir, { recursive: true });

        for (const diagram of result.diagrams) {
          const fileName = `${diagram.type}-${diagram.id}.mmd`;
          const filePath = path.join(mermaidDir, fileName);
          await fs.writeFile(filePath, diagram.content);
        }
        break;

      case 'yaml':
        const yamlPath = path.join(outputDir, 'analysis-result.yaml');
        // Convert to YAML (simplified)
        const yamlContent = JSON.stringify(result, null, 2)
          .replace(/"/g, '')
          .replace(/,$/gm, '')
          .replace(/{$/gm, '')
          .replace(/}$/gm, '');
        await fs.writeFile(yamlPath, yamlContent);
        break;
    }
  }

  // Save summary
  const summaryPath = path.join(outputDir, 'summary.md');
  const summaryContent = generateMarkdownSummary(result);
  await fs.writeFile(summaryPath, summaryContent);
}

function displaySummary(result: any): void {
  console.log('\n' + chalk.cyan('📊 Analysis Summary'));
  console.log(chalk.cyan('=' + '='.repeat(50)));

  console.log(`${chalk.bold('Elements Found:')} ${result.graph.elements.size}`);
  console.log(`${chalk.bold('Relationships:')} ${result.graph.relationships.size}`);
  console.log(`${chalk.bold('Diagrams Generated:')} ${result.diagrams.length}`);
  console.log(`${chalk.bold('Recommendations:')} ${result.recommendations.length}`);

  if (result.graph.metadata.tradingSystemMetrics) {
    const metrics = result.graph.metadata.tradingSystemMetrics;
    console.log('\n' + chalk.yellow('🏦 Trading System Metrics'));
    console.log(chalk.yellow('-'.repeat(30)));
    console.log(`${chalk.bold('Strategies:')} ${metrics.strategyCount}`);
    console.log(`${chalk.bold('Risk Components:')} ${metrics.riskComponentCount}`);
    console.log(`${chalk.bold('API Endpoints:')} ${metrics.apiEndpointCount}`);
    console.log(`${chalk.bold('Complexity Score:')} ${metrics.complexityScore.toFixed(2)}`);
    console.log(`${chalk.bold('Risk Score:')} ${metrics.riskScore.toFixed(2)}`);
  }

  if (result.recommendations.length > 0) {
    console.log('\n' + chalk.red('⚠️  Top Recommendations'));
    console.log(chalk.red('-'.repeat(30)));
    result.recommendations.slice(0, 3).forEach((rec: any, index: number) => {
      console.log(`${index + 1}. ${chalk.bold(rec.title)} (${rec.severity})`);
      console.log(`   ${rec.description}`);
    });
  }

  console.log('\n' + chalk.green('✅ Analysis completed successfully!'));
}

function generateMarkdownSummary(result: any): string {
  return `# AI Trading System Analysis Summary

## Overview
- **Analysis Date**: ${new Date().toISOString()}
- **Elements Found**: ${result.graph.elements.size}
- **Relationships**: ${result.graph.relationships.size}
- **Diagrams Generated**: ${result.diagrams.length}

## Trading System Metrics
${result.graph.metadata.tradingSystemMetrics ? `
- **Trading Strategies**: ${result.graph.metadata.tradingSystemMetrics.strategyCount}
- **Risk Components**: ${result.graph.metadata.tradingSystemMetrics.riskComponentCount}
- **API Endpoints**: ${result.graph.metadata.tradingSystemMetrics.apiEndpointCount}
- **Data Sources**: ${result.graph.metadata.tradingSystemMetrics.dataSourceCount}
- **Notification Handlers**: ${result.graph.metadata.tradingSystemMetrics.notificationHandlerCount}
- **Complexity Score**: ${result.graph.metadata.tradingSystemMetrics.complexityScore.toFixed(2)}
- **Risk Score**: ${result.graph.metadata.tradingSystemMetrics.riskScore.toFixed(2)}
` : 'No trading metrics available'}

## Performance Metrics
- **Parse Time**: ${result.metrics.parseTime}ms
- **Analysis Time**: ${result.metrics.analysisTime}ms
- **Files Processed**: ${result.metrics.filesProcessed}
- **Cache Hit Rate**: ${(result.metrics.cacheHitRate * 100).toFixed(1)}%

## Generated Diagrams
${result.diagrams.map((d: any) => `- **${d.type}**: ${d.title} (${d.metadata.elementCount} elements)`).join('\n')}

## Recommendations
${result.recommendations.map((r: any, i: number) => `${i + 1}. **${r.severity.toUpperCase()}**: ${r.title}\n   ${r.description}`).join('\n\n')}

---
Generated by AI Trading System Code Analysis Engine v1.0.0
`;
}

// Error handling
process.on('unhandledRejection', (error) => {
  cliLogger.error('Unhandled rejection:', error);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  cliLogger.error('Uncaught exception:', error);
  process.exit(1);
});

// Parse command line arguments
program.parse(process.argv);

// Show help if no command provided
if (!process.argv.slice(2).length) {
  program.help();
}