/**
 * Real-time Compliance Monitoring System
 * Monitors trading activities for regulatory compliance
 */

import { EventEmitter } from 'events';

export interface ComplianceMonitorConfig {
  reportingInterval: number; // minutes
  oversightThreshold: number; // risk score threshold
  realTimeAlerts: boolean;
  maxPositionSize?: number;
  maxDailyTurnover?: number;
  maxLeverage?: number;
  restrictedSymbols?: string[];
}

export interface ComplianceViolation {
  id: string;
  type: 'POSITION_LIMIT' | 'RISK_THRESHOLD' | 'RESTRICTED_SYMBOL' | 'LEVERAGE_LIMIT' | 'TURNOVER_LIMIT' | 'HUMAN_OVERSIGHT_REQUIRED';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  data: any;
  timestamp: string;
  resolved: boolean;
  resolutionTimestamp?: string;
}

export interface TradingActivity {
  id: string;
  symbol: string;
  action: 'BUY' | 'SELL' | 'HOLD';
  quantity: number;
  price: number;
  value: number;
  riskScore: number;
  modelId: string;
  timestamp: string;
  accountId?: string;
}

export interface ComplianceMetrics {
  totalTrades: number;
  totalVolume: number;
  averageRiskScore: number;
  violationCount: number;
  oversightTriggers: number;
  lastReportTime: string;
}

export class ComplianceMonitor extends EventEmitter {
  private config: ComplianceMonitorConfig;
  private violations: Map<string, ComplianceViolation> = new Map();
  private activities: TradingActivity[] = [];
  private metrics: ComplianceMetrics;
  private positions: Map<string, { quantity: number; value: number }> = new Map();
  private dailyTurnover: number = 0;
  private reportingTimer?: NodeJS.Timeout;

  constructor(config: ComplianceMonitorConfig) {
    super();
    this.config = {
      maxPositionSize: 1000000, // $1M default
      maxDailyTurnover: 10000000, // $10M default
      maxLeverage: 3, // 3:1 default
      restrictedSymbols: [],
      ...config
    };

    this.metrics = {
      totalTrades: 0,
      totalVolume: 0,
      averageRiskScore: 0,
      violationCount: 0,
      oversightTriggers: 0,
      lastReportTime: new Date().toISOString()
    };

    this.startPeriodicReporting();
    this.resetDailyCounters();
  }

  private startPeriodicReporting(): void {
    if (this.reportingTimer) {
      clearInterval(this.reportingTimer);
    }

    this.reportingTimer = setInterval(() => {
      this.generatePeriodicReport();
    }, this.config.reportingInterval * 60 * 1000);
  }

  private resetDailyCounters(): void {
    // Reset daily counters at midnight
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);

    const msUntilMidnight = tomorrow.getTime() - now.getTime();

    setTimeout(() => {
      this.dailyTurnover = 0;
      this.resetDailyCounters(); // Schedule next reset
    }, msUntilMidnight);
  }

  /**
   * Monitor trading activity for compliance violations
   */
  public async monitorActivity(activity: TradingActivity): Promise<void> {
    // Store activity
    this.activities.push(activity);
    this.updateMetrics(activity);

    // Update position tracking
    this.updatePositions(activity);

    // Check for compliance violations
    await this.checkCompliance(activity);

    // Emit monitoring event
    this.emit('monitor:activity_processed', {
      activityId: activity.id,
      symbol: activity.symbol,
      riskScore: activity.riskScore,
      timestamp: activity.timestamp
    });
  }

  private updateMetrics(activity: TradingActivity): void {
    this.metrics.totalTrades++;
    this.metrics.totalVolume += activity.value;

    // Update average risk score
    const totalRiskScore = (this.metrics.averageRiskScore * (this.metrics.totalTrades - 1)) + activity.riskScore;
    this.metrics.averageRiskScore = totalRiskScore / this.metrics.totalTrades;

    // Update daily turnover
    this.dailyTurnover += activity.value;
  }

  private updatePositions(activity: TradingActivity): void {
    const currentPosition = this.positions.get(activity.symbol) || { quantity: 0, value: 0 };

    if (activity.action === 'BUY') {
      currentPosition.quantity += activity.quantity;
      currentPosition.value += activity.value;
    } else if (activity.action === 'SELL') {
      currentPosition.quantity -= activity.quantity;
      currentPosition.value -= activity.value;
    }

    // Remove position if quantity is zero or near zero
    if (Math.abs(currentPosition.quantity) < 0.0001) {
      this.positions.delete(activity.symbol);
    } else {
      this.positions.set(activity.symbol, currentPosition);
    }
  }

  private async checkCompliance(activity: TradingActivity): Promise<void> {
    // Check position size limits
    await this.checkPositionLimits(activity);

    // Check risk thresholds
    await this.checkRiskThresholds(activity);

    // Check restricted symbols
    await this.checkRestrictedSymbols(activity);

    // Check leverage limits
    await this.checkLeverageLimits(activity);

    // Check daily turnover limits
    await this.checkTurnoverLimits(activity);

    // Check if human oversight is required
    await this.checkOversightRequirements(activity);
  }

  private async checkPositionLimits(activity: TradingActivity): Promise<void> {
    const position = this.positions.get(activity.symbol);
    if (!position) return;

    if (Math.abs(position.value) > this.config.maxPositionSize!) {
      await this.createViolation({
        type: 'POSITION_LIMIT',
        severity: 'HIGH',
        description: `Position size $${Math.abs(position.value).toLocaleString()} exceeds limit $${this.config.maxPositionSize!.toLocaleString()} for ${activity.symbol}`,
        data: {
          symbol: activity.symbol,
          positionValue: position.value,
          limit: this.config.maxPositionSize,
          activity
        }
      });
    }
  }

  private async checkRiskThresholds(activity: TradingActivity): Promise<void> {
    if (activity.riskScore > this.config.oversightThreshold) {
      await this.createViolation({
        type: 'RISK_THRESHOLD',
        severity: activity.riskScore > this.config.oversightThreshold * 1.5 ? 'CRITICAL' : 'HIGH',
        description: `Risk score ${activity.riskScore} exceeds threshold ${this.config.oversightThreshold}`,
        data: {
          riskScore: activity.riskScore,
          threshold: this.config.oversightThreshold,
          activity
        }
      });
    }
  }

  private async checkRestrictedSymbols(activity: TradingActivity): Promise<void> {
    if (this.config.restrictedSymbols!.includes(activity.symbol)) {
      await this.createViolation({
        type: 'RESTRICTED_SYMBOL',
        severity: 'CRITICAL',
        description: `Trading in restricted symbol ${activity.symbol}`,
        data: {
          symbol: activity.symbol,
          restrictedList: this.config.restrictedSymbols,
          activity
        }
      });
    }
  }

  private async checkLeverageLimits(activity: TradingActivity): Promise<void> {
    // Calculate current leverage (simplified)
    const totalPositionValue = Array.from(this.positions.values()).reduce((sum, pos) => sum + Math.abs(pos.value), 0);
    const assumedCapital = totalPositionValue / (this.config.maxLeverage! || 1); // Simplified calculation
    const leverage = totalPositionValue / Math.max(assumedCapital, 1);

    if (leverage > this.config.maxLeverage!) {
      await this.createViolation({
        type: 'LEVERAGE_LIMIT',
        severity: 'HIGH',
        description: `Leverage ratio ${leverage.toFixed(2)} exceeds limit ${this.config.maxLeverage}`,
        data: {
          currentLeverage: leverage,
          limit: this.config.maxLeverage,
          totalPositionValue,
          activity
        }
      });
    }
  }

  private async checkTurnoverLimits(activity: TradingActivity): Promise<void> {
    if (this.dailyTurnover > this.config.maxDailyTurnover!) {
      await this.createViolation({
        type: 'TURNOVER_LIMIT',
        severity: 'MEDIUM',
        description: `Daily turnover $${this.dailyTurnover.toLocaleString()} exceeds limit $${this.config.maxDailyTurnover!.toLocaleString()}`,
        data: {
          dailyTurnover: this.dailyTurnover,
          limit: this.config.maxDailyTurnover,
          activity
        }
      });
    }
  }

  private async checkOversightRequirements(activity: TradingActivity): Promise<void> {
    if (activity.riskScore > this.config.oversightThreshold) {
      this.metrics.oversightTriggers++;

      await this.createViolation({
        type: 'HUMAN_OVERSIGHT_REQUIRED',
        severity: 'MEDIUM',
        description: `Human oversight required for high-risk trade (risk score: ${activity.riskScore})`,
        data: {
          riskScore: activity.riskScore,
          threshold: this.config.oversightThreshold,
          requiresApproval: true,
          activity
        }
      });

      this.emit('compliance:human_oversight_required', {
        activity,
        riskScore: activity.riskScore,
        threshold: this.config.oversightThreshold
      });
    }
  }

  private async createViolation(violationData: {
    type: ComplianceViolation['type'];
    severity: ComplianceViolation['severity'];
    description: string;
    data: any;
  }): Promise<void> {
    const violation: ComplianceViolation = {
      id: `CV_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ...violationData,
      timestamp: new Date().toISOString(),
      resolved: false
    };

    this.violations.set(violation.id, violation);
    this.metrics.violationCount++;

    // Emit violation event
    this.emit('compliance:violation', violation);

    // Send real-time alert if enabled
    if (this.config.realTimeAlerts) {
      this.emit('compliance:alert', {
        violation,
        alertType: 'REAL_TIME',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Resolve a compliance violation
   */
  public async resolveViolation(violationId: string, resolution: string): Promise<void> {
    const violation = this.violations.get(violationId);
    if (!violation) {
      throw new Error(`Violation not found: ${violationId}`);
    }

    violation.resolved = true;
    violation.resolutionTimestamp = new Date().toISOString();
    violation.data.resolution = resolution;

    this.emit('compliance:violation_resolved', {
      violationId,
      resolution,
      timestamp: violation.resolutionTimestamp
    });
  }

  /**
   * Get current compliance violations
   */
  public getViolations(includeResolved: boolean = false): ComplianceViolation[] {
    const violations = Array.from(this.violations.values());
    return includeResolved ? violations : violations.filter(v => !v.resolved);
  }

  /**
   * Get compliance metrics
   */
  public getMetrics(): ComplianceMetrics {
    return { ...this.metrics };
  }

  /**
   * Get current positions
   */
  public getPositions(): Array<{ symbol: string; quantity: number; value: number }> {
    return Array.from(this.positions.entries()).map(([symbol, position]) => ({
      symbol,
      ...position
    }));
  }

  /**
   * Generate periodic compliance report
   */
  private generatePeriodicReport(): void {
    const report = {
      reportId: `CM_${Date.now()}`,
      timestamp: new Date().toISOString(),
      period: this.config.reportingInterval,
      metrics: this.getMetrics(),
      violations: this.getViolations(),
      positions: this.getPositions(),
      activities: this.activities.slice(-100), // Last 100 activities
      summary: {
        totalViolations: this.violations.size,
        unresolvedViolations: this.getViolations().length,
        riskLevel: this.calculateRiskLevel(),
        complianceScore: this.calculateComplianceScore()
      }
    };

    this.metrics.lastReportTime = report.timestamp;

    this.emit('compliance:periodic_report', report);
  }

  private calculateRiskLevel(): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    const unresolvedViolations = this.getViolations();
    const criticalViolations = unresolvedViolations.filter(v => v.severity === 'CRITICAL').length;
    const highViolations = unresolvedViolations.filter(v => v.severity === 'HIGH').length;

    if (criticalViolations > 0) return 'CRITICAL';
    if (highViolations > 2) return 'HIGH';
    if (unresolvedViolations.length > 5) return 'MEDIUM';
    return 'LOW';
  }

  private calculateComplianceScore(): number {
    // Score from 0-100 based on violations and metrics
    const baseScore = 100;
    const unresolvedViolations = this.getViolations();

    let deductions = 0;
    unresolvedViolations.forEach(violation => {
      switch (violation.severity) {
        case 'CRITICAL': deductions += 20; break;
        case 'HIGH': deductions += 10; break;
        case 'MEDIUM': deductions += 5; break;
        case 'LOW': deductions += 2; break;
      }
    });

    // Additional deductions for high average risk score
    if (this.metrics.averageRiskScore > this.config.oversightThreshold) {
      deductions += 10;
    }

    return Math.max(0, baseScore - deductions);
  }

  /**
   * Generate compliance dashboard data
   */
  public getDashboardData(): any {
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const recentActivities = this.activities.filter(a => new Date(a.timestamp) > oneDayAgo);
    const recentViolations = Array.from(this.violations.values())
      .filter(v => new Date(v.timestamp) > oneWeekAgo);

    return {
      summary: {
        complianceScore: this.calculateComplianceScore(),
        riskLevel: this.calculateRiskLevel(),
        totalPositions: this.positions.size,
        dailyTurnover: this.dailyTurnover,
        oversightTriggers: this.metrics.oversightTriggers
      },
      metrics: this.getMetrics(),
      recentActivity: {
        trades24h: recentActivities.length,
        avgRiskScore24h: recentActivities.length > 0
          ? recentActivities.reduce((sum, a) => sum + a.riskScore, 0) / recentActivities.length
          : 0,
        volume24h: recentActivities.reduce((sum, a) => sum + a.value, 0)
      },
      violations: {
        total: this.violations.size,
        unresolved: this.getViolations().length,
        recent: recentViolations.length,
        bySeverity: {
          critical: recentViolations.filter(v => v.severity === 'CRITICAL').length,
          high: recentViolations.filter(v => v.severity === 'HIGH').length,
          medium: recentViolations.filter(v => v.severity === 'MEDIUM').length,
          low: recentViolations.filter(v => v.severity === 'LOW').length
        }
      },
      positions: this.getPositions(),
      alerts: this.getViolations().filter(v => ['CRITICAL', 'HIGH'].includes(v.severity))
    };
  }

  /**
   * Get monitor status
   */
  public getStatus(): any {
    return {
      config: this.config,
      metrics: this.metrics,
      violationCount: this.violations.size,
      positionCount: this.positions.size,
      isMonitoring: true,
      lastActivity: this.activities.length > 0 ? this.activities[this.activities.length - 1].timestamp : null
    };
  }

  /**
   * Shutdown compliance monitor
   */
  public shutdown(): void {
    if (this.reportingTimer) {
      clearInterval(this.reportingTimer);
    }

    this.emit('compliance:monitor_shutdown', {
      timestamp: new Date().toISOString(),
      finalMetrics: this.metrics
    });
  }
}

export default ComplianceMonitor;