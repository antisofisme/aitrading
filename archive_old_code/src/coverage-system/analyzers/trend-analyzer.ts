/**
 * Historical Trend Analysis System
 * Tracks coverage trends over time and provides predictive insights
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { CoverageSummary, CoverageData } from '../core/coverage-analyzer';

export interface TrendPoint {
  timestamp: Date;
  coverage: CoverageSummary;
  metadata: TrendMetadata;
  version: string;
  commit: string;
  branch: string;
  buildId: string;
}

export interface TrendMetadata {
  testCount: number;
  fileCount: number;
  complexityScore: number;
  technicalDebt: number;
  buildDuration: number;
  environment: string;
}

export interface TrendAnalysis {
  timespan: string;
  dataPoints: number;
  trend: TrendDirection;
  velocity: TrendVelocity;
  patterns: TrendPattern[];
  predictions: TrendPrediction[];
  insights: TrendInsight[];
  recommendations: TrendRecommendation[];
}

export interface TrendDirection {
  overall: 'improving' | 'stable' | 'declining';
  lines: 'improving' | 'stable' | 'declining';
  functions: 'improving' | 'stable' | 'declining';
  branches: 'improving' | 'stable' | 'declining';
  statements: 'improving' | 'stable' | 'declining';
  confidence: number;
}

export interface TrendVelocity {
  dailyChange: number;
  weeklyChange: number;
  monthlyChange: number;
  acceleration: number;
  volatility: number;
}

export interface TrendPattern {
  type: 'seasonal' | 'cyclical' | 'linear' | 'exponential' | 'regression';
  description: string;
  strength: number;
  period?: number;
  confidence: number;
}

export interface TrendPrediction {
  timeframe: '1day' | '1week' | '1month' | '3months';
  predicted: CoverageSummary;
  confidence: number;
  scenario: 'best' | 'likely' | 'worst';
  factors: string[];
}

export interface TrendInsight {
  type: 'achievement' | 'concern' | 'opportunity' | 'anomaly';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  timeframe: string;
  data: any;
}

export interface TrendRecommendation {
  category: 'process' | 'technical' | 'organizational' | 'tooling';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  expectedImpact: string;
  effort: 'high' | 'medium' | 'low';
  timeline: string;
}

export class TrendAnalyzer {
  private historicalData: TrendPoint[] = [];
  private dataFile: string;

  constructor(dataFilePath?: string) {
    this.dataFile = dataFilePath || path.join(process.cwd(), 'coverage-trends.json');
  }

  async loadHistoricalData(): Promise<void> {
    try {
      const data = await fs.readFile(this.dataFile, 'utf-8');
      const parsed = JSON.parse(data);
      this.historicalData = parsed.map((point: any) => ({
        ...point,
        timestamp: new Date(point.timestamp)
      }));

      console.log(`Loaded ${this.historicalData.length} historical data points`);
    } catch (error) {
      console.log('No historical data found, starting fresh');
      this.historicalData = [];
    }
  }

  async addDataPoint(coverageData: CoverageData): Promise<void> {
    const point: TrendPoint = {
      timestamp: coverageData.timestamp,
      coverage: coverageData.summary,
      metadata: {
        testCount: 0, // Will be populated from test results
        fileCount: coverageData.files.size,
        complexityScore: coverageData.summary.averageComplexity,
        technicalDebt: 0, // Will be calculated
        buildDuration: 0, // From CI/CD metadata
        environment: coverageData.metadata.environment || 'unknown'
      },
      version: coverageData.metadata.version || 'unknown',
      commit: coverageData.metadata.commit || 'unknown',
      branch: coverageData.metadata.branch || 'main',
      buildId: coverageData.metadata.buildId || 'unknown'
    };

    this.historicalData.push(point);
    this.historicalData.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

    // Keep only last 1000 points to manage storage
    if (this.historicalData.length > 1000) {
      this.historicalData = this.historicalData.slice(-1000);
    }

    await this.saveHistoricalData();
  }

  private async saveHistoricalData(): Promise<void> {
    try {
      await fs.writeFile(this.dataFile, JSON.stringify(this.historicalData, null, 2), 'utf-8');
    } catch (error) {
      console.error('Failed to save historical data:', error);
    }
  }

  analyzeComplete(timespan: string = '30days'): TrendAnalysis {
    const relevantData = this.getRelevantData(timespan);

    if (relevantData.length < 2) {
      return this.createEmptyAnalysis(timespan);
    }

    const trend = this.calculateTrend(relevantData);
    const velocity = this.calculateVelocity(relevantData);
    const patterns = this.identifyPatterns(relevantData);
    const predictions = this.generatePredictions(relevantData, patterns);
    const insights = this.generateInsights(relevantData, trend, velocity);
    const recommendations = this.generateRecommendations(insights, trend);

    return {
      timespan,
      dataPoints: relevantData.length,
      trend,
      velocity,
      patterns,
      predictions,
      insights,
      recommendations
    };
  }

  private getRelevantData(timespan: string): TrendPoint[] {
    const now = new Date();
    let cutoffDate: Date;

    switch (timespan) {
      case '7days':
        cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30days':
        cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '90days':
        cutoffDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000);
        break;
      case '1year':
        cutoffDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
    }

    return this.historicalData.filter(point => point.timestamp >= cutoffDate);
  }

  private createEmptyAnalysis(timespan: string): TrendAnalysis {
    return {
      timespan,
      dataPoints: 0,
      trend: {
        overall: 'stable',
        lines: 'stable',
        functions: 'stable',
        branches: 'stable',
        statements: 'stable',
        confidence: 0
      },
      velocity: {
        dailyChange: 0,
        weeklyChange: 0,
        monthlyChange: 0,
        acceleration: 0,
        volatility: 0
      },
      patterns: [],
      predictions: [],
      insights: [{
        type: 'concern',
        title: 'Insufficient Historical Data',
        description: 'Not enough data points to perform trend analysis',
        impact: 'medium',
        timeframe: 'current',
        data: { dataPoints: this.historicalData.length }
      }],
      recommendations: [{
        category: 'process',
        priority: 'medium',
        title: 'Establish Coverage Tracking',
        description: 'Set up regular coverage measurement to build historical trends',
        expectedImpact: 'Better visibility into coverage evolution',
        effort: 'low',
        timeline: '1 week'
      }]
    };
  }

  private calculateTrend(data: TrendPoint[]): TrendDirection {
    const first = data[0];
    const last = data[data.length - 1];

    const linesChange = last.coverage.lines.lines - first.coverage.lines.lines;
    const functionsChange = last.coverage.functions.functions - first.coverage.functions.functions;
    const branchesChange = last.coverage.branches.branches - first.coverage.branches.branches;
    const statementsChange = last.coverage.statements.statements - first.coverage.statements.statements;

    const overallChange = (linesChange + functionsChange + branchesChange + statementsChange) / 4;

    // Calculate linear regression for confidence
    const confidence = this.calculateTrendConfidence(data);

    return {
      overall: this.classifyChange(overallChange),
      lines: this.classifyChange(linesChange),
      functions: this.classifyChange(functionsChange),
      branches: this.classifyChange(branchesChange),
      statements: this.classifyChange(statementsChange),
      confidence
    };
  }

  private classifyChange(change: number): 'improving' | 'stable' | 'declining' {
    if (change > 1) return 'improving';
    if (change < -1) return 'declining';
    return 'stable';
  }

  private calculateTrendConfidence(data: TrendPoint[]): number {
    if (data.length < 3) return 0;

    // Calculate R-squared for line coverage trend
    const n = data.length;
    const x = data.map((_, i) => i);
    const y = data.map(point => point.coverage.lines.lines);

    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumXX = x.reduce((sum, xi) => sum + xi * xi, 0);
    const sumYY = y.reduce((sum, yi) => sum + yi * yi, 0);

    const denominator = Math.sqrt((n * sumXX - sumX * sumX) * (n * sumYY - sumY * sumY));
    if (denominator === 0) return 0;

    const correlation = (n * sumXY - sumX * sumY) / denominator;
    return Math.abs(correlation) * 100; // Convert to percentage
  }

  private calculateVelocity(data: TrendPoint[]): TrendVelocity {
    if (data.length < 2) {
      return {
        dailyChange: 0,
        weeklyChange: 0,
        monthlyChange: 0,
        acceleration: 0,
        volatility: 0
      };
    }

    const timeSpan = data[data.length - 1].timestamp.getTime() - data[0].timestamp.getTime();
    const days = timeSpan / (24 * 60 * 60 * 1000);

    const firstCoverage = data[0].coverage.lines.lines;
    const lastCoverage = data[data.length - 1].coverage.lines.lines;
    const totalChange = lastCoverage - firstCoverage;

    const dailyChange = days > 0 ? totalChange / days : 0;
    const weeklyChange = dailyChange * 7;
    const monthlyChange = dailyChange * 30;

    // Calculate acceleration (change in velocity)
    const acceleration = this.calculateAcceleration(data);

    // Calculate volatility (standard deviation of changes)
    const volatility = this.calculateVolatility(data);

    return {
      dailyChange,
      weeklyChange,
      monthlyChange,
      acceleration,
      volatility
    };
  }

  private calculateAcceleration(data: TrendPoint[]): number {
    if (data.length < 3) return 0;

    const velocities: number[] = [];

    for (let i = 1; i < data.length; i++) {
      const timeDiff = (data[i].timestamp.getTime() - data[i - 1].timestamp.getTime()) / (24 * 60 * 60 * 1000);
      const coverageChange = data[i].coverage.lines.lines - data[i - 1].coverage.lines.lines;
      velocities.push(timeDiff > 0 ? coverageChange / timeDiff : 0);
    }

    // Calculate change in velocity (acceleration)
    if (velocities.length < 2) return 0;

    return velocities[velocities.length - 1] - velocities[0];
  }

  private calculateVolatility(data: TrendPoint[]): number {
    if (data.length < 3) return 0;

    const changes: number[] = [];

    for (let i = 1; i < data.length; i++) {
      changes.push(data[i].coverage.lines.lines - data[i - 1].coverage.lines.lines);
    }

    const mean = changes.reduce((sum, change) => sum + change, 0) / changes.length;
    const variance = changes.reduce((sum, change) => sum + Math.pow(change - mean, 2), 0) / changes.length;

    return Math.sqrt(variance);
  }

  private identifyPatterns(data: TrendPoint[]): TrendPattern[] {
    const patterns: TrendPattern[] = [];

    // Linear trend
    const linearPattern = this.identifyLinearPattern(data);
    if (linearPattern.strength > 0.3) {
      patterns.push(linearPattern);
    }

    // Cyclical patterns
    const cyclicalPattern = this.identifyCyclicalPattern(data);
    if (cyclicalPattern.strength > 0.3) {
      patterns.push(cyclicalPattern);
    }

    // Seasonal patterns
    const seasonalPattern = this.identifySeasonalPattern(data);
    if (seasonalPattern.strength > 0.3) {
      patterns.push(seasonalPattern);
    }

    // Regression patterns
    const regressionPattern = this.identifyRegressionPattern(data);
    if (regressionPattern.strength > 0.3) {
      patterns.push(regressionPattern);
    }

    return patterns;
  }

  private identifyLinearPattern(data: TrendPoint[]): TrendPattern {
    const confidence = this.calculateTrendConfidence(data);

    return {
      type: 'linear',
      description: confidence > 70 ? 'Strong linear trend detected' : confidence > 40 ? 'Moderate linear trend' : 'Weak linear trend',
      strength: confidence / 100,
      confidence
    };
  }

  private identifyCyclicalPattern(data: TrendPoint[]): TrendPattern {
    // Simple cyclical detection based on local maxima/minima
    if (data.length < 6) {
      return {
        type: 'cyclical',
        description: 'Insufficient data for cyclical analysis',
        strength: 0,
        confidence: 0
      };
    }

    const peaks: number[] = [];
    const valleys: number[] = [];

    for (let i = 1; i < data.length - 1; i++) {
      const prev = data[i - 1].coverage.lines.lines;
      const curr = data[i].coverage.lines.lines;
      const next = data[i + 1].coverage.lines.lines;

      if (curr > prev && curr > next) {
        peaks.push(i);
      } else if (curr < prev && curr < next) {
        valleys.push(i);
      }
    }

    const totalTurningPoints = peaks.length + valleys.length;
    const strength = Math.min(totalTurningPoints / (data.length * 0.3), 1);

    return {
      type: 'cyclical',
      description: `${totalTurningPoints} turning points detected`,
      strength,
      confidence: strength * 100
    };
  }

  private identifySeasonalPattern(data: TrendPoint[]): TrendPattern {
    // Group by day of week or month to identify seasonal patterns
    const dayOfWeekData: { [key: number]: number[] } = {};

    data.forEach(point => {
      const dayOfWeek = point.timestamp.getDay();
      if (!dayOfWeekData[dayOfWeek]) {
        dayOfWeekData[dayOfWeek] = [];
      }
      dayOfWeekData[dayOfWeek].push(point.coverage.lines.lines);
    });

    // Calculate variance between different days
    const dayAverages = Object.keys(dayOfWeekData).map(day => {
      const values = dayOfWeekData[parseInt(day)];
      return values.reduce((sum, val) => sum + val, 0) / values.length;
    });

    const overallAverage = dayAverages.reduce((sum, avg) => sum + avg, 0) / dayAverages.length;
    const variance = dayAverages.reduce((sum, avg) => sum + Math.pow(avg - overallAverage, 2), 0) / dayAverages.length;
    const strength = Math.min(variance / 100, 1);

    return {
      type: 'seasonal',
      description: strength > 0.5 ? 'Strong day-of-week pattern' : 'Weak seasonal pattern',
      strength,
      period: 7,
      confidence: strength * 100
    };
  }

  private identifyRegressionPattern(data: TrendPoint[]): TrendPattern {
    // Identify periods of significant regression (declining coverage)
    let regressionPeriods = 0;
    let consecutiveDeclines = 0;
    let maxConsecutiveDeclines = 0;

    for (let i = 1; i < data.length; i++) {
      const change = data[i].coverage.lines.lines - data[i - 1].coverage.lines.lines;

      if (change < -0.5) {
        consecutiveDeclines++;
        maxConsecutiveDeclines = Math.max(maxConsecutiveDeclines, consecutiveDeclines);
      } else {
        if (consecutiveDeclines >= 2) {
          regressionPeriods++;
        }
        consecutiveDeclines = 0;
      }
    }

    const strength = Math.min((regressionPeriods * 2 + maxConsecutiveDeclines) / data.length, 1);

    return {
      type: 'regression',
      description: `${regressionPeriods} regression periods, max consecutive declines: ${maxConsecutiveDeclines}`,
      strength,
      confidence: strength * 100
    };
  }

  private generatePredictions(data: TrendPoint[], patterns: TrendPattern[]): TrendPrediction[] {
    if (data.length < 3) return [];

    const predictions: TrendPrediction[] = [];
    const currentCoverage = data[data.length - 1].coverage;

    // Linear prediction based on recent trend
    const recentData = data.slice(-Math.min(10, data.length));
    const linearTrend = this.calculateLinearTrend(recentData);

    const timeframes: Array<'1day' | '1week' | '1month' | '3months'> = ['1day', '1week', '1month', '3months'];
    const scenarios: Array<'best' | 'likely' | 'worst'> = ['best', 'likely', 'worst'];

    timeframes.forEach(timeframe => {
      const days = this.timeframeToDays(timeframe);

      scenarios.forEach(scenario => {
        const multiplier = scenario === 'best' ? 1.2 : scenario === 'worst' ? 0.8 : 1.0;
        const change = linearTrend * days * multiplier;

        const predicted: CoverageSummary = {
          lines: {
            lines: Math.max(0, Math.min(100, currentCoverage.lines.lines + change)),
            functions: 0,
            branches: 0,
            statements: 0
          },
          functions: {
            lines: 0,
            functions: Math.max(0, Math.min(100, currentCoverage.functions.functions + change)),
            branches: 0,
            statements: 0
          },
          branches: {
            lines: 0,
            functions: 0,
            branches: Math.max(0, Math.min(100, currentCoverage.branches.branches + change)),
            statements: 0
          },
          statements: {
            lines: 0,
            functions: 0,
            branches: 0,
            statements: Math.max(0, Math.min(100, currentCoverage.statements.statements + change))
          },
          files: currentCoverage.files,
          totalSize: currentCoverage.totalSize,
          averageComplexity: currentCoverage.averageComplexity
        };

        const confidence = this.calculatePredictionConfidence(data, patterns, timeframe);

        predictions.push({
          timeframe,
          predicted,
          confidence,
          scenario,
          factors: this.getPredictionFactors(patterns, scenario)
        });
      });
    });

    return predictions;
  }

  private timeframeToDays(timeframe: string): number {
    switch (timeframe) {
      case '1day': return 1;
      case '1week': return 7;
      case '1month': return 30;
      case '3months': return 90;
      default: return 30;
    }
  }

  private calculateLinearTrend(data: TrendPoint[]): number {
    if (data.length < 2) return 0;

    const timeSpan = data[data.length - 1].timestamp.getTime() - data[0].timestamp.getTime();
    const days = timeSpan / (24 * 60 * 60 * 1000);
    const coverageChange = data[data.length - 1].coverage.lines.lines - data[0].coverage.lines.lines;

    return days > 0 ? coverageChange / days : 0;
  }

  private calculatePredictionConfidence(data: TrendPoint[], patterns: TrendPattern[], timeframe: string): number {
    let confidence = 50; // Base confidence

    // Adjust based on data points
    confidence += Math.min(data.length * 2, 30);

    // Adjust based on pattern strength
    const strongPatterns = patterns.filter(p => p.strength > 0.6);
    confidence += strongPatterns.length * 10;

    // Adjust based on timeframe (shorter predictions more confident)
    const timeframeDays = this.timeframeToDays(timeframe);
    confidence -= Math.min(timeframeDays * 0.5, 25);

    return Math.max(10, Math.min(95, confidence));
  }

  private getPredictionFactors(patterns: TrendPattern[], scenario: string): string[] {
    const factors: string[] = [];

    if (scenario === 'best') {
      factors.push('Increased testing efforts', 'Code quality improvements', 'Developer training');
    } else if (scenario === 'worst') {
      factors.push('Technical debt accumulation', 'Rapid development pressure', 'Resource constraints');
    } else {
      factors.push('Current development pace', 'Existing quality processes');
    }

    patterns.forEach(pattern => {
      switch (pattern.type) {
        case 'linear':
          factors.push('Consistent development practices');
          break;
        case 'cyclical':
          factors.push('Sprint/release cycle effects');
          break;
        case 'seasonal':
          factors.push('Team schedule variations');
          break;
        case 'regression':
          factors.push('Previous regression patterns');
          break;
      }
    });

    return factors;
  }

  private generateInsights(data: TrendPoint[], trend: TrendDirection, velocity: TrendVelocity): TrendInsight[] {
    const insights: TrendInsight[] = [];

    // Achievement insights
    if (trend.overall === 'improving' && velocity.monthlyChange > 2) {
      insights.push({
        type: 'achievement',
        title: 'Strong Coverage Improvement',
        description: `Coverage has improved by ${velocity.monthlyChange.toFixed(1)}% per month`,
        impact: 'high',
        timeframe: 'recent',
        data: { monthlyChange: velocity.monthlyChange, confidence: trend.confidence }
      });
    }

    // Concern insights
    if (trend.overall === 'declining' && velocity.monthlyChange < -1) {
      insights.push({
        type: 'concern',
        title: 'Coverage Decline',
        description: `Coverage is declining at ${Math.abs(velocity.monthlyChange).toFixed(1)}% per month`,
        impact: 'high',
        timeframe: 'recent',
        data: { monthlyChange: velocity.monthlyChange, confidence: trend.confidence }
      });
    }

    // Volatility insights
    if (velocity.volatility > 5) {
      insights.push({
        type: 'concern',
        title: 'High Coverage Volatility',
        description: 'Coverage shows high variability, indicating inconsistent testing practices',
        impact: 'medium',
        timeframe: 'ongoing',
        data: { volatility: velocity.volatility }
      });
    }

    // Opportunity insights
    if (trend.overall === 'stable' && velocity.acceleration > 0.1) {
      insights.push({
        type: 'opportunity',
        title: 'Accelerating Coverage',
        description: 'Recent data shows accelerating coverage improvement',
        impact: 'medium',
        timeframe: 'emerging',
        data: { acceleration: velocity.acceleration }
      });
    }

    // Anomaly detection
    const recentPoints = data.slice(-5);
    if (recentPoints.length >= 5) {
      const recentAvg = recentPoints.reduce((sum, p) => sum + p.coverage.lines.lines, 0) / recentPoints.length;
      const historicalAvg = data.slice(0, -5).reduce((sum, p) => sum + p.coverage.lines.lines, 0) / Math.max(1, data.length - 5);

      if (Math.abs(recentAvg - historicalAvg) > 10) {
        insights.push({
          type: 'anomaly',
          title: 'Significant Coverage Shift',
          description: `Recent coverage differs significantly from historical average`,
          impact: 'high',
          timeframe: 'recent',
          data: { recentAvg, historicalAvg, difference: recentAvg - historicalAvg }
        });
      }
    }

    return insights;
  }

  private generateRecommendations(insights: TrendInsight[], trend: TrendDirection): TrendRecommendation[] {
    const recommendations: TrendRecommendation[] = [];

    // Based on trend direction
    if (trend.overall === 'declining') {
      recommendations.push({
        category: 'process',
        priority: 'high',
        title: 'Implement Coverage Quality Gates',
        description: 'Set up automated quality gates to prevent coverage regression',
        expectedImpact: 'Prevent further coverage decline',
        effort: 'medium',
        timeline: '2 weeks'
      });

      recommendations.push({
        category: 'technical',
        priority: 'high',
        title: 'Review Testing Strategy',
        description: 'Conduct comprehensive review of current testing practices',
        expectedImpact: 'Identify gaps in testing approach',
        effort: 'high',
        timeline: '1 month'
      });
    }

    // Based on insights
    insights.forEach(insight => {
      switch (insight.type) {
        case 'concern':
          if (insight.title.includes('Volatility')) {
            recommendations.push({
              category: 'process',
              priority: 'medium',
              title: 'Standardize Testing Practices',
              description: 'Establish consistent testing guidelines across teams',
              expectedImpact: 'Reduce coverage variability',
              effort: 'medium',
              timeline: '3 weeks'
            });
          }
          break;

        case 'opportunity':
          recommendations.push({
            category: 'organizational',
            priority: 'medium',
            title: 'Capitalize on Positive Momentum',
            description: 'Share successful practices and scale improvements',
            expectedImpact: 'Accelerate overall improvement',
            effort: 'low',
            timeline: '2 weeks'
          });
          break;

        case 'anomaly':
          recommendations.push({
            category: 'technical',
            priority: 'high',
            title: 'Investigate Coverage Anomaly',
            description: 'Deep dive into recent changes causing coverage shift',
            expectedImpact: 'Understand and control coverage variations',
            effort: 'medium',
            timeline: '1 week'
          });
          break;
      }
    });

    // General recommendations
    if (trend.confidence < 50) {
      recommendations.push({
        category: 'tooling',
        priority: 'medium',
        title: 'Improve Coverage Measurement',
        description: 'Enhance coverage data collection for better trend analysis',
        expectedImpact: 'More reliable trend insights',
        effort: 'medium',
        timeline: '2 weeks'
      });
    }

    return recommendations;
  }

  async exportTrendData(outputPath: string, format: 'json' | 'csv' = 'json'): Promise<void> {
    if (format === 'json') {
      await fs.writeFile(outputPath, JSON.stringify(this.historicalData, null, 2), 'utf-8');
    } else {
      const csv = this.convertToCSV(this.historicalData);
      await fs.writeFile(outputPath, csv, 'utf-8');
    }
  }

  private convertToCSV(data: TrendPoint[]): string {
    const headers = [
      'timestamp', 'lines', 'functions', 'branches', 'statements',
      'fileCount', 'complexityScore', 'version', 'commit', 'branch'
    ];

    const rows = data.map(point => [
      point.timestamp.toISOString(),
      point.coverage.lines.lines,
      point.coverage.functions.functions,
      point.coverage.branches.branches,
      point.coverage.statements.statements,
      point.metadata.fileCount,
      point.metadata.complexityScore,
      point.version,
      point.commit,
      point.branch
    ]);

    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  }

  getDataPointsCount(): number {
    return this.historicalData.length;
  }

  getTimeSpan(): { start: Date | null; end: Date | null } {
    if (this.historicalData.length === 0) {
      return { start: null, end: null };
    }

    return {
      start: this.historicalData[0].timestamp,
      end: this.historicalData[this.historicalData.length - 1].timestamp
    };
  }

  clearHistoricalData(): void {
    this.historicalData = [];
  }
}