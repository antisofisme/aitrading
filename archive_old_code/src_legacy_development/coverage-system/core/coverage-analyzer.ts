/**
 * Coverage Analysis Engine
 * Processes coverage data and generates detailed insights
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { CoverageThreshold, ModuleCoverageConfig, QualityGate } from '../config/coverage-config';

export interface CoverageData {
  files: Map<string, FileCoverage>;
  summary: CoverageSummary;
  timestamp: Date;
  metadata: CoverageMetadata;
}

export interface FileCoverage {
  path: string;
  lines: LineCoverage;
  functions: FunctionCoverage;
  branches: BranchCoverage;
  statements: StatementCoverage;
  complexity: number;
  size: number;
  lastModified: Date;
}

export interface LineCoverage {
  total: number;
  covered: number;
  percentage: number;
  uncoveredLines: number[];
  partiallyCovaeredLines: number[];
}

export interface FunctionCoverage {
  total: number;
  covered: number;
  percentage: number;
  uncoveredFunctions: string[];
  partiallyCovaeredFunctions: string[];
}

export interface BranchCoverage {
  total: number;
  covered: number;
  percentage: number;
  uncoveredBranches: BranchInfo[];
}

export interface StatementCoverage {
  total: number;
  covered: number;
  percentage: number;
  uncoveredStatements: number[];
}

export interface BranchInfo {
  line: number;
  branch: number;
  taken: boolean;
  condition: string;
}

export interface CoverageSummary {
  lines: CoverageThreshold;
  functions: CoverageThreshold;
  branches: CoverageThreshold;
  statements: CoverageThreshold;
  files: number;
  totalSize: number;
  averageComplexity: number;
}

export interface CoverageMetadata {
  testSuite: string;
  version: string;
  branch: string;
  commit: string;
  buildId: string;
  environment: string;
  duration: number;
}

export interface CoverageAnalysis {
  summary: CoverageSummary;
  moduleAnalysis: ModuleAnalysis[];
  qualityGateResults: QualityGateResult[];
  trends: TrendAnalysis;
  recommendations: Recommendation[];
  hotspots: CoverageHotspot[];
}

export interface ModuleAnalysis {
  module: ModuleCoverageConfig;
  coverage: CoverageSummary;
  files: FileCoverage[];
  passed: boolean;
  violations: ThresholdViolation[];
  score: number;
}

export interface QualityGateResult {
  gate: QualityGate;
  passed: boolean;
  conditions: ConditionResult[];
  score: number;
}

export interface ConditionResult {
  condition: any;
  passed: boolean;
  actualValue: number;
  expectedValue: number;
  message: string;
}

export interface TrendAnalysis {
  historical: HistoricalPoint[];
  trend: 'improving' | 'stable' | 'declining';
  changePercent: number;
  changeAbsolute: number;
  prediction: number;
}

export interface HistoricalPoint {
  timestamp: Date;
  coverage: CoverageSummary;
  version: string;
  commit: string;
}

export interface Recommendation {
  type: 'improvement' | 'warning' | 'critical';
  category: 'coverage' | 'quality' | 'performance' | 'maintenance';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  effort: 'high' | 'medium' | 'low';
  files: string[];
  priority: number;
  actionItems: ActionItem[];
}

export interface ActionItem {
  description: string;
  file?: string;
  line?: number;
  effort: string;
  impact: string;
}

export interface CoverageHotspot {
  file: string;
  type: 'low-coverage' | 'high-complexity' | 'large-uncovered' | 'critical-path';
  severity: 'high' | 'medium' | 'low';
  coverage: number;
  complexity: number;
  size: number;
  priority: number;
  description: string;
}

export class CoverageAnalyzer {
  private coverageData: CoverageData | null = null;
  private historicalData: HistoricalPoint[] = [];

  async loadCoverageData(coverageFilePath: string): Promise<CoverageData> {
    try {
      const rawData = await fs.readFile(coverageFilePath, 'utf-8');
      this.coverageData = this.parseCoverageData(rawData);
      return this.coverageData;
    } catch (error) {
      throw new Error(`Failed to load coverage data: ${error.message}`);
    }
  }

  private parseCoverageData(rawData: string): CoverageData {
    const parsed = JSON.parse(rawData);
    const files = new Map<string, FileCoverage>();

    // Parse file-level coverage data
    for (const [filePath, fileData] of Object.entries(parsed.files || {})) {
      files.set(filePath, this.parseFileCoverage(filePath, fileData as any));
    }

    return {
      files,
      summary: this.calculateSummary(files),
      timestamp: new Date(parsed.timestamp || Date.now()),
      metadata: parsed.metadata || {}
    };
  }

  private parseFileCoverage(filePath: string, fileData: any): FileCoverage {
    return {
      path: filePath,
      lines: {
        total: fileData.lines?.total || 0,
        covered: fileData.lines?.covered || 0,
        percentage: this.calculatePercentage(fileData.lines?.covered || 0, fileData.lines?.total || 0),
        uncoveredLines: fileData.lines?.uncovered || [],
        partiallyCovaeredLines: fileData.lines?.partial || []
      },
      functions: {
        total: fileData.functions?.total || 0,
        covered: fileData.functions?.covered || 0,
        percentage: this.calculatePercentage(fileData.functions?.covered || 0, fileData.functions?.total || 0),
        uncoveredFunctions: fileData.functions?.uncovered || [],
        partiallyCovaeredFunctions: fileData.functions?.partial || []
      },
      branches: {
        total: fileData.branches?.total || 0,
        covered: fileData.branches?.covered || 0,
        percentage: this.calculatePercentage(fileData.branches?.covered || 0, fileData.branches?.total || 0),
        uncoveredBranches: fileData.branches?.uncovered || []
      },
      statements: {
        total: fileData.statements?.total || 0,
        covered: fileData.statements?.covered || 0,
        percentage: this.calculatePercentage(fileData.statements?.covered || 0, fileData.statements?.total || 0),
        uncoveredStatements: fileData.statements?.uncovered || []
      },
      complexity: fileData.complexity || 0,
      size: fileData.size || 0,
      lastModified: new Date(fileData.lastModified || Date.now())
    };
  }

  private calculatePercentage(covered: number, total: number): number {
    return total === 0 ? 100 : Math.round((covered / total) * 100 * 100) / 100;
  }

  private calculateSummary(files: Map<string, FileCoverage>): CoverageSummary {
    let totalLines = 0, coveredLines = 0;
    let totalFunctions = 0, coveredFunctions = 0;
    let totalBranches = 0, coveredBranches = 0;
    let totalStatements = 0, coveredStatements = 0;
    let totalSize = 0, totalComplexity = 0;

    for (const file of files.values()) {
      totalLines += file.lines.total;
      coveredLines += file.lines.covered;
      totalFunctions += file.functions.total;
      coveredFunctions += file.functions.covered;
      totalBranches += file.branches.total;
      coveredBranches += file.branches.covered;
      totalStatements += file.statements.total;
      coveredStatements += file.statements.covered;
      totalSize += file.size;
      totalComplexity += file.complexity;
    }

    return {
      lines: {
        lines: this.calculatePercentage(coveredLines, totalLines),
        functions: 0,
        branches: 0,
        statements: 0
      },
      functions: {
        lines: 0,
        functions: this.calculatePercentage(coveredFunctions, totalFunctions),
        branches: 0,
        statements: 0
      },
      branches: {
        lines: 0,
        functions: 0,
        branches: this.calculatePercentage(coveredBranches, totalBranches),
        statements: 0
      },
      statements: {
        lines: 0,
        functions: 0,
        branches: 0,
        statements: this.calculatePercentage(coveredStatements, totalStatements)
      },
      files: files.size,
      totalSize,
      averageComplexity: files.size > 0 ? totalComplexity / files.size : 0
    };
  }

  async analyzeComplete(modules: ModuleCoverageConfig[], qualityGates: QualityGate[]): Promise<CoverageAnalysis> {
    if (!this.coverageData) {
      throw new Error('No coverage data loaded. Call loadCoverageData first.');
    }

    const moduleAnalysis = await this.analyzeModules(modules);
    const qualityGateResults = await this.evaluateQualityGates(qualityGates);
    const trends = await this.analyzeTrends();
    const recommendations = await this.generateRecommendations();
    const hotspots = await this.identifyHotspots();

    return {
      summary: this.coverageData.summary,
      moduleAnalysis,
      qualityGateResults,
      trends,
      recommendations,
      hotspots
    };
  }

  private async analyzeModules(modules: ModuleCoverageConfig[]): Promise<ModuleAnalysis[]> {
    const results: ModuleAnalysis[] = [];

    for (const module of modules) {
      const moduleFiles = Array.from(this.coverageData!.files.entries())
        .filter(([filePath]) => filePath.startsWith(module.path))
        .map(([, file]) => file);

      const moduleCoverage = this.calculateModuleSummary(moduleFiles);
      const violations = this.checkThresholdViolations(moduleCoverage, module.thresholds);
      const passed = violations.length === 0;
      const score = this.calculateModuleScore(moduleCoverage, module.thresholds);

      results.push({
        module,
        coverage: moduleCoverage,
        files: moduleFiles,
        passed,
        violations,
        score
      });
    }

    return results;
  }

  private calculateModuleSummary(files: FileCoverage[]): CoverageSummary {
    // Implementation similar to calculateSummary but for specific files
    return this.calculateSummary(new Map(files.map(f => [f.path, f])));
  }

  private checkThresholdViolations(coverage: CoverageSummary, thresholds: CoverageThreshold): ThresholdViolation[] {
    const violations: ThresholdViolation[] = [];

    if (coverage.lines.lines < thresholds.lines) {
      violations.push({
        metric: 'lines',
        actual: coverage.lines.lines,
        expected: thresholds.lines,
        severity: 'error'
      });
    }

    if (coverage.functions.functions < thresholds.functions) {
      violations.push({
        metric: 'functions',
        actual: coverage.functions.functions,
        expected: thresholds.functions,
        severity: 'error'
      });
    }

    if (coverage.branches.branches < thresholds.branches) {
      violations.push({
        metric: 'branches',
        actual: coverage.branches.branches,
        expected: thresholds.branches,
        severity: 'error'
      });
    }

    if (coverage.statements.statements < thresholds.statements) {
      violations.push({
        metric: 'statements',
        actual: coverage.statements.statements,
        expected: thresholds.statements,
        severity: 'error'
      });
    }

    return violations;
  }

  private calculateModuleScore(coverage: CoverageSummary, thresholds: CoverageThreshold): number {
    const lineScore = Math.min(coverage.lines.lines / thresholds.lines, 1);
    const functionScore = Math.min(coverage.functions.functions / thresholds.functions, 1);
    const branchScore = Math.min(coverage.branches.branches / thresholds.branches, 1);
    const statementScore = Math.min(coverage.statements.statements / thresholds.statements, 1);

    return Math.round((lineScore + functionScore + branchScore + statementScore) / 4 * 100);
  }

  private async evaluateQualityGates(qualityGates: QualityGate[]): Promise<QualityGateResult[]> {
    const results: QualityGateResult[] = [];

    for (const gate of qualityGates) {
      const conditions: ConditionResult[] = [];
      let gateScore = 0;

      for (const condition of gate.conditions) {
        const result = await this.evaluateCondition(condition);
        conditions.push(result);
        if (result.passed) gateScore += 25; // Each condition worth 25 points
      }

      results.push({
        gate,
        passed: conditions.every(c => c.passed),
        conditions,
        score: Math.min(gateScore, 100)
      });
    }

    return results;
  }

  private async evaluateCondition(condition: any): Promise<ConditionResult> {
    let actualValue = 0;

    switch (condition.metric) {
      case 'coverage':
        actualValue = this.coverageData!.summary.lines.lines;
        break;
      case 'trend':
        actualValue = (await this.analyzeTrends()).changePercent;
        break;
      default:
        actualValue = 0;
    }

    const passed = this.evaluateOperator(actualValue, condition.operator, condition.value);

    return {
      condition,
      passed,
      actualValue,
      expectedValue: condition.value,
      message: `${condition.metric} is ${actualValue}, expected ${condition.operator} ${condition.value}`
    };
  }

  private evaluateOperator(actual: number, operator: string, expected: number): boolean {
    switch (operator) {
      case 'gt': return actual > expected;
      case 'gte': return actual >= expected;
      case 'lt': return actual < expected;
      case 'lte': return actual <= expected;
      case 'eq': return actual === expected;
      default: return false;
    }
  }

  private async analyzeTrends(): Promise<TrendAnalysis> {
    if (this.historicalData.length < 2) {
      return {
        historical: this.historicalData,
        trend: 'stable',
        changePercent: 0,
        changeAbsolute: 0,
        prediction: this.coverageData?.summary.lines.lines || 0
      };
    }

    const current = this.coverageData!.summary.lines.lines;
    const previous = this.historicalData[this.historicalData.length - 1].coverage.lines.lines;
    const changeAbsolute = current - previous;
    const changePercent = (changeAbsolute / previous) * 100;

    let trend: 'improving' | 'stable' | 'declining' = 'stable';
    if (changePercent > 1) trend = 'improving';
    else if (changePercent < -1) trend = 'declining';

    // Simple linear prediction based on recent trend
    const prediction = this.predictNextCoverage();

    return {
      historical: this.historicalData,
      trend,
      changePercent,
      changeAbsolute,
      prediction
    };
  }

  private predictNextCoverage(): number {
    if (this.historicalData.length < 3) {
      return this.coverageData?.summary.lines.lines || 0;
    }

    // Simple linear regression prediction
    const recentPoints = this.historicalData.slice(-5);
    const n = recentPoints.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;

    recentPoints.forEach((point, index) => {
      const x = index;
      const y = point.coverage.lines.lines;
      sumX += x;
      sumY += y;
      sumXY += x * y;
      sumXX += x * x;
    });

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return slope * n + intercept;
  }

  private async generateRecommendations(): Promise<Recommendation[]> {
    const recommendations: Recommendation[] = [];

    // Low coverage files
    const lowCoverageFiles = Array.from(this.coverageData!.files.entries())
      .filter(([, file]) => file.lines.percentage < 70)
      .sort((a, b) => a[1].lines.percentage - b[1].lines.percentage);

    if (lowCoverageFiles.length > 0) {
      recommendations.push({
        type: 'critical',
        category: 'coverage',
        title: 'Low Coverage Files Detected',
        description: `${lowCoverageFiles.length} files have coverage below 70%`,
        impact: 'high',
        effort: 'medium',
        files: lowCoverageFiles.slice(0, 10).map(([path]) => path),
        priority: 100,
        actionItems: lowCoverageFiles.slice(0, 5).map(([path, file]) => ({
          description: `Add tests to improve coverage for ${path}`,
          file: path,
          effort: 'medium',
          impact: 'high'
        }))
      });
    }

    // High complexity files
    const highComplexityFiles = Array.from(this.coverageData!.files.entries())
      .filter(([, file]) => file.complexity > 10)
      .sort((a, b) => b[1].complexity - a[1].complexity);

    if (highComplexityFiles.length > 0) {
      recommendations.push({
        type: 'warning',
        category: 'quality',
        title: 'High Complexity Files',
        description: `${highComplexityFiles.length} files have high complexity`,
        impact: 'medium',
        effort: 'high',
        files: highComplexityFiles.slice(0, 10).map(([path]) => path),
        priority: 80,
        actionItems: highComplexityFiles.slice(0, 3).map(([path, file]) => ({
          description: `Refactor ${path} to reduce complexity (current: ${file.complexity})`,
          file: path,
          effort: 'high',
          impact: 'medium'
        }))
      });
    }

    return recommendations;
  }

  private async identifyHotspots(): Promise<CoverageHotspot[]> {
    const hotspots: CoverageHotspot[] = [];

    for (const [filePath, file] of this.coverageData!.files.entries()) {
      let priority = 0;
      let type: CoverageHotspot['type'] = 'low-coverage';
      let severity: CoverageHotspot['severity'] = 'low';

      // Low coverage hotspot
      if (file.lines.percentage < 50) {
        priority += 50;
        type = 'low-coverage';
        severity = 'high';
      } else if (file.lines.percentage < 70) {
        priority += 30;
        type = 'low-coverage';
        severity = 'medium';
      }

      // High complexity hotspot
      if (file.complexity > 15) {
        priority += 40;
        type = 'high-complexity';
        if (severity === 'low') severity = 'medium';
      }

      // Large uncovered sections
      if (file.lines.uncoveredLines.length > 50) {
        priority += 35;
        type = 'large-uncovered';
        if (severity === 'low') severity = 'medium';
      }

      if (priority > 30) {
        hotspots.push({
          file: filePath,
          type,
          severity,
          coverage: file.lines.percentage,
          complexity: file.complexity,
          size: file.size,
          priority,
          description: this.generateHotspotDescription(file, type)
        });
      }
    }

    return hotspots.sort((a, b) => b.priority - a.priority);
  }

  private generateHotspotDescription(file: FileCoverage, type: CoverageHotspot['type']): string {
    switch (type) {
      case 'low-coverage':
        return `Low coverage (${file.lines.percentage}%) with ${file.lines.uncoveredLines.length} uncovered lines`;
      case 'high-complexity':
        return `High complexity (${file.complexity}) requiring refactoring`;
      case 'large-uncovered':
        return `Large uncovered sections with ${file.lines.uncoveredLines.length} uncovered lines`;
      case 'critical-path':
        return `Critical path with insufficient test coverage`;
      default:
        return 'Coverage hotspot requiring attention';
    }
  }

  async loadHistoricalData(historicalDataPath: string): Promise<void> {
    try {
      const data = await fs.readFile(historicalDataPath, 'utf-8');
      this.historicalData = JSON.parse(data);
    } catch (error) {
      // Historical data is optional
      this.historicalData = [];
    }
  }

  async saveHistoricalPoint(): Promise<void> {
    if (!this.coverageData) return;

    const point: HistoricalPoint = {
      timestamp: this.coverageData.timestamp,
      coverage: this.coverageData.summary,
      version: this.coverageData.metadata.version || 'unknown',
      commit: this.coverageData.metadata.commit || 'unknown'
    };

    this.historicalData.push(point);

    // Keep only last 100 points
    if (this.historicalData.length > 100) {
      this.historicalData = this.historicalData.slice(-100);
    }
  }
}

export interface ThresholdViolation {
  metric: string;
  actual: number;
  expected: number;
  severity: 'error' | 'warning';
}