/**
 * Coverage System Main Orchestrator
 * Coordinates all coverage system components and provides unified API
 */

import { CoverageAnalyzer, CoverageData, CoverageAnalysis } from './core/coverage-analyzer';
import { CoverageConfigManager, CoverageConfig } from './config/coverage-config';
import { HTMLReporter } from './reporters/html-reporter';
import { TrendAnalyzer, TrendAnalysis } from './analyzers/trend-analyzer';
import { RecommendationEngine, EnhancedRecommendation, RecommendationContext } from './analyzers/recommendation-engine';
import { ModuleLevelTracker } from './analyzers/module-tracker';
import { CoverageMonitor, MonitoringConfig } from './monitoring/coverage-monitor';
import { CICDIntegration, CICDConfig, CICDResult } from './integrations/ci-cd-integration';
import { promises as fs } from 'fs';
import * as path from 'path';

export interface CoverageSystemConfig {
  coverage: CoverageConfig;
  monitoring: MonitoringConfig;
  cicd: CICDConfig;
  reporting: ReportingOptions;
  context: RecommendationContext;
}

export interface ReportingOptions {
  formats: Array<'html' | 'json' | 'markdown' | 'xml' | 'lcov'>;
  outputDir: string;
  includeVisualizations: boolean;
  includeSourceCode: boolean;
  generateTrendReports: boolean;
  generateRecommendationReports: boolean;
}

export interface CoverageSystemResult {
  success: boolean;
  coverage: CoverageAnalysis;
  trends?: TrendAnalysis;
  recommendations: EnhancedRecommendation[];
  reports: GeneratedReport[];
  cicdResult?: CICDResult;
  monitoring?: {
    eventsGenerated: number;
    alertsSent: number;
  };
  metadata: {
    timestamp: Date;
    duration: number;
    version: string;
    filesAnalyzed: number;
    modulesAnalyzed: number;
  };
}

export interface GeneratedReport {
  format: string;
  path: string;
  size: number;
  generated: Date;
}

export class CoverageSystem {
  private config: CoverageSystemConfig;
  private configManager: CoverageConfigManager;
  private analyzer: CoverageAnalyzer;
  private trendAnalyzer: TrendAnalyzer;
  private recommendationEngine: RecommendationEngine;
  private moduleTracker: ModuleLevelTracker;
  private monitor: CoverageMonitor;
  private cicdIntegration: CICDIntegration;
  private htmlReporter: HTMLReporter;

  constructor(config: CoverageSystemConfig) {
    this.config = config;
    this.initializeComponents();
  }

  private initializeComponents(): void {
    // Initialize configuration manager
    this.configManager = CoverageConfigManager.getInstance();
    this.configManager.updateConfig(this.config.coverage);

    // Initialize core analyzer
    this.analyzer = new CoverageAnalyzer();

    // Initialize trend analyzer
    this.trendAnalyzer = new TrendAnalyzer();

    // Initialize recommendation engine
    this.recommendationEngine = new RecommendationEngine(this.config.context);

    // Initialize module tracker
    this.moduleTracker = new ModuleLevelTracker(this.config.coverage.modules);

    // Initialize monitoring system
    this.monitor = new CoverageMonitor(this.config.monitoring);

    // Initialize CI/CD integration
    this.cicdIntegration = new CICDIntegration(this.config.cicd, this.config.coverage);

    // Initialize HTML reporter
    this.htmlReporter = new HTMLReporter({
      outputDir: path.join(this.config.reporting.outputDir, 'html'),
      includeSourceCode: this.config.reporting.includeSourceCode,
      includeCharts: this.config.reporting.includeVisualizations
    });
  }

  async initialize(): Promise<void> {
    console.log('Initializing Coverage System...');

    // Load historical data
    await this.trendAnalyzer.loadHistoricalData();

    // Start monitoring if enabled
    if (this.config.monitoring.enabled) {
      await this.monitor.start();
    }

    console.log('Coverage System initialized successfully');
  }

  async shutdown(): Promise<void> {
    console.log('Shutting down Coverage System...');

    // Stop monitoring
    if (this.monitor.isRunning()) {
      await this.monitor.stop();
    }

    console.log('Coverage System shutdown complete');
  }

  async analyzeCoverage(coverageFilePath: string): Promise<CoverageSystemResult> {
    const startTime = Date.now();
    console.log(`Starting comprehensive coverage analysis...`);

    try {
      // Step 1: Load and parse coverage data
      console.log('Loading coverage data...');
      const coverageData = await this.analyzer.loadCoverageData(coverageFilePath);

      // Step 2: Perform detailed analysis
      console.log('Performing coverage analysis...');
      const modules = this.configManager.getConfig().modules;
      const qualityGates = this.configManager.getActiveQualityGates();
      const analysis = await this.analyzer.analyzeComplete(modules, qualityGates);

      // Step 3: Analyze trends (if historical data available)
      console.log('Analyzing trends...');
      await this.trendAnalyzer.addDataPoint(coverageData);
      const trendAnalysis = this.trendAnalyzer.analyzeComplete();

      // Step 4: Track module-level coverage
      console.log('Tracking module-level coverage...');
      const modulePromises = modules.map(module =>
        this.moduleTracker.analyzeModule(module, coverageData.files)
      );
      await Promise.all(modulePromises);

      // Step 5: Generate recommendations
      console.log('Generating recommendations...');
      const recommendations = await this.recommendationEngine.generateRecommendations(
        analysis,
        trendAnalysis
      );

      // Step 6: Process monitoring and alerts
      let monitoringResult;
      if (this.monitor.isRunning()) {
        console.log('Processing monitoring events...');
        await this.monitor.processCoverageData(coverageData, analysis, trendAnalysis);
        monitoringResult = {
          eventsGenerated: this.monitor.getRecentEvents(10).length,
          alertsSent: this.monitor.getRecentAlerts(5).length
        };
      }

      // Step 7: Generate reports
      console.log('Generating reports...');
      const reports = await this.generateReports(coverageData, analysis, trendAnalysis, recommendations);

      // Step 8: CI/CD integration
      let cicdResult;
      if (this.config.cicd.enabled) {
        console.log('Processing CI/CD integration...');
        cicdResult = await this.cicdIntegration.processCovarage(coverageData, analysis);
      }

      // Step 9: Build result
      const duration = Date.now() - startTime;
      const result: CoverageSystemResult = {
        success: true,
        coverage: analysis,
        trends: trendAnalysis,
        recommendations,
        reports,
        cicdResult,
        monitoring: monitoringResult,
        metadata: {
          timestamp: new Date(),
          duration,
          version: '1.0.0',
          filesAnalyzed: coverageData.files.size,
          modulesAnalyzed: modules.length
        }
      };

      console.log(`Coverage analysis completed in ${duration}ms`);
      console.log(`- Files analyzed: ${coverageData.files.size}`);
      console.log(`- Modules analyzed: ${modules.length}`);
      console.log(`- Overall coverage: ${analysis.summary.lines.lines}%`);
      console.log(`- Quality gates passed: ${analysis.qualityGateResults.filter(qg => qg.passed).length}/${analysis.qualityGateResults.length}`);
      console.log(`- Recommendations generated: ${recommendations.length}`);
      console.log(`- Reports generated: ${reports.length}`);

      return result;

    } catch (error) {
      console.error('Coverage analysis failed:', error);
      throw new Error(`Coverage analysis failed: ${error.message}`);
    }
  }

  private async generateReports(
    coverageData: CoverageData,
    analysis: CoverageAnalysis,
    trendAnalysis: TrendAnalysis,
    recommendations: EnhancedRecommendation[]
  ): Promise<GeneratedReport[]> {
    const reports: GeneratedReport[] = [];
    const outputDir = this.config.reporting.outputDir;

    // Ensure output directory exists
    await this.ensureDirectory(outputDir);

    try {
      // Generate HTML report
      if (this.config.reporting.formats.includes('html')) {
        const htmlPath = await this.htmlReporter.generateReport(
          coverageData,
          analysis,
          this.config.coverage
        );
        const stats = await fs.stat(htmlPath);
        reports.push({
          format: 'html',
          path: htmlPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate JSON report
      if (this.config.reporting.formats.includes('json')) {
        const jsonPath = path.join(outputDir, 'coverage-report.json');
        const jsonData = {
          coverage: analysis,
          trends: trendAnalysis,
          recommendations,
          metadata: {
            generated: new Date().toISOString(),
            version: '1.0.0'
          }
        };
        await fs.writeFile(jsonPath, JSON.stringify(jsonData, null, 2), 'utf-8');
        const stats = await fs.stat(jsonPath);
        reports.push({
          format: 'json',
          path: jsonPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate Markdown report
      if (this.config.reporting.formats.includes('markdown')) {
        const markdownPath = path.join(outputDir, 'coverage-report.md');
        const markdown = this.generateMarkdownReport(analysis, trendAnalysis, recommendations);
        await fs.writeFile(markdownPath, markdown, 'utf-8');
        const stats = await fs.stat(markdownPath);
        reports.push({
          format: 'markdown',
          path: markdownPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate LCOV report
      if (this.config.reporting.formats.includes('lcov')) {
        const lcovPath = path.join(outputDir, 'lcov.info');
        const lcov = this.generateLCOVReport(coverageData);
        await fs.writeFile(lcovPath, lcov, 'utf-8');
        const stats = await fs.stat(lcovPath);
        reports.push({
          format: 'lcov',
          path: lcovPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate XML report
      if (this.config.reporting.formats.includes('xml')) {
        const xmlPath = path.join(outputDir, 'coverage-report.xml');
        const xml = this.generateXMLReport(analysis);
        await fs.writeFile(xmlPath, xml, 'utf-8');
        const stats = await fs.stat(xmlPath);
        reports.push({
          format: 'xml',
          path: xmlPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate trend report (if enabled)
      if (this.config.reporting.generateTrendReports) {
        const trendPath = path.join(outputDir, 'trend-analysis.json');
        await fs.writeFile(trendPath, JSON.stringify(trendAnalysis, null, 2), 'utf-8');
        const stats = await fs.stat(trendPath);
        reports.push({
          format: 'trend-json',
          path: trendPath,
          size: stats.size,
          generated: new Date()
        });
      }

      // Generate recommendations report (if enabled)
      if (this.config.reporting.generateRecommendationReports) {
        const recPath = path.join(outputDir, 'recommendations.json');
        await fs.writeFile(recPath, JSON.stringify(recommendations, null, 2), 'utf-8');
        const stats = await fs.stat(recPath);
        reports.push({
          format: 'recommendations-json',
          path: recPath,
          size: stats.size,
          generated: new Date()
        });
      }

    } catch (error) {
      console.error('Error generating reports:', error);
      throw error;
    }

    return reports;
  }

  private generateMarkdownReport(
    analysis: CoverageAnalysis,
    trendAnalysis: TrendAnalysis,
    recommendations: EnhancedRecommendation[]
  ): string {
    const lines = analysis.summary.lines.lines;
    const functions = analysis.summary.functions.functions;
    const branches = analysis.summary.branches.branches;
    const statements = analysis.summary.statements.statements;

    const trendEmoji = trendAnalysis.trend.overall === 'improving' ? '📈' :
                      trendAnalysis.trend.overall === 'declining' ? '📉' : '📊';

    return `# Coverage Report

Generated: ${new Date().toLocaleString()}

## Summary

| Metric | Coverage | Status |
|--------|----------|--------|
| Lines | ${lines}% | ${this.getCoverageStatus(lines)} |
| Functions | ${functions}% | ${this.getCoverageStatus(functions)} |
| Branches | ${branches}% | ${this.getCoverageStatus(branches)} |
| Statements | ${statements}% | ${this.getCoverageStatus(statements)} |

## Quality Gates

${analysis.qualityGateResults.map(qg =>
  `- ${qg.passed ? '✅' : '❌'} **${qg.gate.name}**: ${qg.passed ? 'PASSED' : 'FAILED'}`
).join('\n')}

## Trend Analysis ${trendEmoji}

- **Overall Trend**: ${trendAnalysis.trend.overall}
- **Monthly Change**: ${trendAnalysis.velocity.monthlyChange >= 0 ? '+' : ''}${trendAnalysis.velocity.monthlyChange.toFixed(2)}%
- **Data Points**: ${trendAnalysis.dataPoints}
- **Confidence**: ${trendAnalysis.trend.confidence.toFixed(1)}%

## Top Recommendations

${recommendations.slice(0, 5).map((rec, index) =>
  `${index + 1}. **${rec.title}** (${rec.priority} priority)
   - ${rec.description}
   - Impact: ${rec.impact} | Effort: ${rec.effort}
   - Timeline: ${rec.timeline}`
).join('\n\n')}

## Coverage Hotspots

${analysis.hotspots.slice(0, 10).map(hotspot =>
  `- \`${hotspot.file}\`: ${hotspot.coverage}% coverage (${hotspot.severity} severity)`
).join('\n')}

---
*Generated by AI Trading Platform Coverage System*
`;
  }

  private generateLCOVReport(coverageData: CoverageData): string {
    const lines: string[] = [];

    for (const [filePath, fileCoverage] of coverageData.files.entries()) {
      lines.push('TN:'); // Test name (empty)
      lines.push(`SF:${filePath}`); // Source file

      // Function coverage
      for (let i = 0; i < fileCoverage.functions.total; i++) {
        lines.push(`FN:${i + 1},function_${i}`);
      }
      lines.push(`FNF:${fileCoverage.functions.total}`);
      lines.push(`FNH:${fileCoverage.functions.covered}`);

      // Line coverage
      for (let i = 1; i <= fileCoverage.lines.total; i++) {
        const covered = !fileCoverage.lines.uncoveredLines.includes(i) ? 1 : 0;
        lines.push(`DA:${i},${covered}`);
      }
      lines.push(`LF:${fileCoverage.lines.total}`);
      lines.push(`LH:${fileCoverage.lines.covered}`);

      // Branch coverage
      fileCoverage.branches.uncoveredBranches.forEach((branch, index) => {
        lines.push(`BDA:${branch.line},${index},${branch.taken ? 1 : 0}`);
      });
      lines.push(`BRF:${fileCoverage.branches.total}`);
      lines.push(`BRH:${fileCoverage.branches.covered}`);

      lines.push('end_of_record');
    }

    return lines.join('\n');
  }

  private generateXMLReport(analysis: CoverageAnalysis): string {
    return `<?xml version="1.0" encoding="UTF-8"?>
<coverage line-rate="${(analysis.summary.lines.lines / 100).toFixed(4)}"
          branch-rate="${(analysis.summary.branches.branches / 100).toFixed(4)}"
          lines-covered="${analysis.summary.lines.lines}"
          lines-valid="100"
          branches-covered="${analysis.summary.branches.branches}"
          branches-valid="100"
          complexity="0"
          version="1.0"
          timestamp="${Date.now()}">
  <sources>
    <source>src/</source>
  </sources>
  <packages>
    <package name="coverage" line-rate="${(analysis.summary.lines.lines / 100).toFixed(4)}"
             branch-rate="${(analysis.summary.branches.branches / 100).toFixed(4)}"
             complexity="0">
      <classes>
        <!-- File details would go here -->
      </classes>
    </package>
  </packages>
</coverage>`;
  }

  private getCoverageStatus(coverage: number): string {
    if (coverage >= 90) return '🟢 Excellent';
    if (coverage >= 80) return '🟡 Good';
    if (coverage >= 70) return '🟠 Fair';
    return '🔴 Poor';
  }

  private async ensureDirectory(dir: string): Promise<void> {
    try {
      await fs.access(dir);
    } catch {
      await fs.mkdir(dir, { recursive: true });
    }
  }

  // Public API methods for external integration

  async updateConfiguration(updates: Partial<CoverageSystemConfig>): Promise<void> {
    this.config = { ...this.config, ...updates };

    if (updates.coverage) {
      this.configManager.updateConfig(updates.coverage);
    }

    // Reinitialize components if needed
    if (updates.monitoring || updates.cicd || updates.context) {
      this.initializeComponents();
    }
  }

  getConfiguration(): CoverageSystemConfig {
    return { ...this.config };
  }

  async getModuleAnalysis(moduleId: string) {
    return this.moduleTracker.getModule(moduleId);
  }

  async compareModules(moduleIds: string[]) {
    return this.moduleTracker.compareModules(moduleIds);
  }

  getTrendAnalysis(timespan: string = '30days'): TrendAnalysis {
    return this.trendAnalyzer.analyzeComplete(timespan);
  }

  getMonitoringMetrics() {
    return this.monitor.getMetrics();
  }

  getRecentAlerts(limit: number = 10) {
    return this.monitor.getRecentAlerts(limit);
  }

  async exportTrendData(outputPath: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    return this.trendAnalyzer.exportTrendData(outputPath, format);
  }

  async generateCustomReport(
    coverageData: CoverageData,
    options: Partial<ReportingOptions>
  ): Promise<GeneratedReport[]> {
    const analysis = await this.analyzer.analyzeComplete(
      this.config.coverage.modules,
      this.config.coverage.qualityGates
    );

    const trendAnalysis = this.trendAnalyzer.analyzeComplete();
    const recommendations = await this.recommendationEngine.generateRecommendations(analysis, trendAnalysis);

    const tempConfig = { ...this.config.reporting, ...options };
    const originalConfig = this.config.reporting;
    this.config.reporting = tempConfig;

    try {
      return await this.generateReports(coverageData, analysis, trendAnalysis, recommendations);
    } finally {
      this.config.reporting = originalConfig;
    }
  }

  // Static factory methods

  static createDefault(context: RecommendationContext): CoverageSystem {
    const config: CoverageSystemConfig = {
      coverage: CoverageConfigManager.getInstance().getConfig(),
      monitoring: {
        enabled: true,
        interval: 60000, // 1 minute
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
          enabled: false,
          actions: [],
          permissions: {
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
      },
      cicd: {
        provider: 'github',
        environment: 'development'
      },
      reporting: {
        formats: ['html', 'json'],
        outputDir: 'coverage-reports',
        includeVisualizations: true,
        includeSourceCode: true,
        generateTrendReports: true,
        generateRecommendationReports: true
      },
      context
    };

    return new CoverageSystem(config);
  }

  static createForCI(context: RecommendationContext): CoverageSystem {
    const system = this.createDefault(context);

    // CI-specific configuration
    system.config.reporting.formats = ['json', 'lcov', 'xml'];
    system.config.monitoring.enabled = false;
    system.config.cicd.enabled = true;
    system.config.cicd.failOnThreshold = true;
    system.config.cicd.generateArtifacts = true;

    return system;
  }
}

// Export all major types and classes
export {
  CoverageAnalyzer,
  CoverageData,
  CoverageAnalysis,
  CoverageConfigManager,
  CoverageConfig,
  HTMLReporter,
  TrendAnalyzer,
  TrendAnalysis,
  RecommendationEngine,
  EnhancedRecommendation,
  RecommendationContext,
  ModuleLevelTracker,
  CoverageMonitor,
  MonitoringConfig,
  CICDIntegration,
  CICDConfig,
  CICDResult
};

// Default export
export default CoverageSystem;