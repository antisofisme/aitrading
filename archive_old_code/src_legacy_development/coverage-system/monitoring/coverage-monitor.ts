/**
 * Automated Coverage Monitoring and Alerting System
 * Provides real-time monitoring, alerting, and automated responses to coverage changes
 */

import { EventEmitter } from 'events';
import { promises as fs } from 'fs';
import * as path from 'path';
import { CoverageData, CoverageAnalysis } from '../core/coverage-analyzer';
import { TrendAnalysis } from '../analyzers/trend-analyzer';
import { AlertConfig } from '../config/coverage-config';

export interface MonitoringConfig {
  enabled: boolean;
  interval: number; // in milliseconds
  thresholds: MonitoringThresholds;
  alerts: AlertConfiguration;
  automation: AutomationConfig;
  retention: RetentionConfig;
}

export interface MonitoringThresholds {
  coverageDecrease: number; // percentage points
  qualityGateFailures: number;
  consecutiveFailures: number;
  trendDeclining: number; // days
  hotspotIncrease: number;
  responseTimeThreshold: number; // milliseconds
}

export interface AlertConfiguration {
  channels: AlertChannel[];
  severity: SeverityConfig;
  throttling: ThrottlingConfig;
  escalation: EscalationConfig;
}

export interface AlertChannel {
  type: 'email' | 'slack' | 'webhook' | 'github' | 'pagerduty' | 'teams';
  config: any;
  enabled: boolean;
  severityFilter: AlertSeverity[];
}

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface SeverityConfig {
  coverageDecrease: AlertSeverity;
  qualityGateFail: AlertSeverity;
  trendDeclining: AlertSeverity;
  hotspotCritical: AlertSeverity;
  systemError: AlertSeverity;
}

export interface ThrottlingConfig {
  enabled: boolean;
  window: number; // minutes
  maxAlerts: number;
  backoffMultiplier: number;
}

export interface EscalationConfig {
  enabled: boolean;
  levels: EscalationLevel[];
}

export interface EscalationLevel {
  level: number;
  delay: number; // minutes
  channels: string[];
  conditions: string[];
}

export interface AutomationConfig {
  enabled: boolean;
  actions: AutomationAction[];
  permissions: AutomationPermissions;
}

export interface AutomationAction {
  trigger: AutomationTrigger;
  action: AutomationActionType;
  conditions: AutomationCondition[];
  enabled: boolean;
  rateLimit: number; // max executions per hour
}

export interface AutomationTrigger {
  event: 'coverage-decrease' | 'quality-gate-fail' | 'trend-declining' | 'hotspot-critical';
  threshold: any;
}

export interface AutomationActionType {
  type: 'create-issue' | 'create-pr' | 'notify-team' | 'run-script' | 'block-merge' | 'schedule-review';
  config: any;
}

export interface AutomationCondition {
  field: string;
  operator: 'equals' | 'greater' | 'less' | 'contains';
  value: any;
}

export interface AutomationPermissions {
  createIssues: boolean;
  createPRs: boolean;
  blockMerges: boolean;
  runScripts: boolean;
  notifyTeams: boolean;
}

export interface RetentionConfig {
  alerts: number; // days
  metrics: number; // days
  events: number; // days
  reports: number; // days
}

export interface MonitoringEvent {
  id: string;
  timestamp: Date;
  type: MonitoringEventType;
  severity: AlertSeverity;
  source: string;
  data: any;
  handled: boolean;
  suppressed: boolean;
}

export type MonitoringEventType =
  | 'coverage-analyzed'
  | 'coverage-decreased'
  | 'quality-gate-failed'
  | 'trend-declining'
  | 'hotspot-detected'
  | 'alert-sent'
  | 'automation-triggered'
  | 'system-error';

export interface AlertEvent {
  id: string;
  timestamp: Date;
  severity: AlertSeverity;
  title: string;
  message: string;
  data: any;
  channels: string[];
  sent: boolean;
  error?: string;
}

export interface MonitoringMetrics {
  uptime: number;
  eventsProcessed: number;
  alertsSent: number;
  automationRuns: number;
  errorRate: number;
  responseTime: number;
  lastUpdate: Date;
}

export interface MonitoringReport {
  period: string;
  events: MonitoringEvent[];
  alerts: AlertEvent[];
  metrics: MonitoringMetrics;
  insights: MonitoringInsight[];
  recommendations: string[];
}

export interface MonitoringInsight {
  type: 'pattern' | 'anomaly' | 'trend' | 'performance';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  confidence: number;
  data: any;
}

export class CoverageMonitor extends EventEmitter {
  private config: MonitoringConfig;
  private isRunning: boolean = false;
  private intervalId: NodeJS.Timeout | null = null;
  private events: MonitoringEvent[] = [];
  private alerts: AlertEvent[] = [];
  private metrics: MonitoringMetrics;
  private lastCoverageData: CoverageData | null = null;
  private consecutiveFailures: number = 0;
  private alertThrottling: Map<string, Date> = new Map();

  constructor(config: MonitoringConfig) {
    super();
    this.config = config;
    this.metrics = this.initializeMetrics();
    this.setupEventHandlers();
  }

  async start(): Promise<void> {
    if (this.isRunning) {
      console.log('Coverage monitor is already running');
      return;
    }

    console.log('Starting coverage monitor...');
    this.isRunning = true;

    // Load historical data
    await this.loadHistoricalData();

    // Start monitoring interval
    if (this.config.interval > 0) {
      this.intervalId = setInterval(() => {
        this.performMonitoringCycle().catch(error => {
          this.recordEvent('system-error', 'error', 'monitor', { error: error.message });
        });
      }, this.config.interval);
    }

    // Emit start event
    this.recordEvent('coverage-analyzed', 'info', 'monitor', { message: 'Monitor started' });
    this.emit('started');

    console.log(`Coverage monitor started with ${this.config.interval}ms interval`);
  }

  async stop(): Promise<void> {
    if (!this.isRunning) {
      console.log('Coverage monitor is not running');
      return;
    }

    console.log('Stopping coverage monitor...');
    this.isRunning = false;

    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }

    // Save current state
    await this.saveHistoricalData();

    this.emit('stopped');
    console.log('Coverage monitor stopped');
  }

  async processCoverageData(
    coverageData: CoverageData,
    analysis: CoverageAnalysis,
    trendAnalysis?: TrendAnalysis
  ): Promise<void> {
    const startTime = Date.now();

    try {
      // Record coverage analysis event
      this.recordEvent('coverage-analyzed', 'info', 'analyzer', {
        coverage: analysis.summary.lines.lines,
        qualityGates: analysis.qualityGateResults.length,
        hotspots: analysis.hotspots.length
      });

      // Check for coverage decrease
      await this.checkCoverageDecrease(coverageData, analysis);

      // Check quality gates
      await this.checkQualityGates(analysis);

      // Check trends
      if (trendAnalysis) {
        await this.checkTrends(trendAnalysis);
      }

      // Check hotspots
      await this.checkHotspots(analysis);

      // Update metrics
      this.updateMetrics(Date.now() - startTime);

      // Store current data for comparison
      this.lastCoverageData = coverageData;

      // Reset consecutive failures if everything is okay
      if (this.isHealthy(analysis)) {
        this.consecutiveFailures = 0;
      }

    } catch (error) {
      this.recordEvent('system-error', 'error', 'monitor', { error: error.message });
      this.metrics.errorRate += 1;
    }
  }

  private async performMonitoringCycle(): Promise<void> {
    // This would typically trigger a coverage analysis
    // For now, just perform health checks
    await this.performHealthChecks();
    await this.cleanupOldData();
    await this.generatePeriodicReports();
  }

  private async checkCoverageDecrease(coverageData: CoverageData, analysis: CoverageAnalysis): Promise<void> {
    if (!this.lastCoverageData) return;

    const currentCoverage = analysis.summary.lines.lines;
    const previousCoverage = this.lastCoverageData.summary.lines.lines;
    const decrease = previousCoverage - currentCoverage;

    if (decrease > this.config.thresholds.coverageDecrease) {
      this.recordEvent('coverage-decreased', this.config.alerts.severity.coverageDecrease, 'analyzer', {
        current: currentCoverage,
        previous: previousCoverage,
        decrease
      });

      await this.sendAlert({
        severity: this.config.alerts.severity.coverageDecrease,
        title: 'Coverage Decrease Detected',
        message: `Coverage decreased by ${decrease.toFixed(2)}% (${previousCoverage}% → ${currentCoverage}%)`,
        data: { current: currentCoverage, previous: previousCoverage, decrease }
      });

      await this.triggerAutomation('coverage-decrease', { decrease, current: currentCoverage });
    }
  }

  private async checkQualityGates(analysis: CoverageAnalysis): Promise<void> {
    const failedGates = analysis.qualityGateResults.filter(qg => !qg.passed);

    if (failedGates.length > 0) {
      this.consecutiveFailures++;

      this.recordEvent('quality-gate-failed', this.config.alerts.severity.qualityGateFail, 'analyzer', {
        failedCount: failedGates.length,
        totalGates: analysis.qualityGateResults.length,
        consecutiveFailures: this.consecutiveFailures
      });

      if (failedGates.length >= this.config.thresholds.qualityGateFailures ||
          this.consecutiveFailures >= this.config.thresholds.consecutiveFailures) {

        await this.sendAlert({
          severity: this.config.alerts.severity.qualityGateFail,
          title: 'Quality Gate Failures',
          message: `${failedGates.length} quality gates failed (${this.consecutiveFailures} consecutive failures)`,
          data: { failedGates: failedGates.map(fg => fg.gate.name), consecutiveFailures: this.consecutiveFailures }
        });

        await this.triggerAutomation('quality-gate-fail', { failedCount: failedGates.length });
      }
    }
  }

  private async checkTrends(trendAnalysis: TrendAnalysis): Promise<void> {
    if (trendAnalysis.trend.overall === 'declining') {
      const decliningDays = this.calculateDecliningDays(trendAnalysis);

      if (decliningDays >= this.config.thresholds.trendDeclining) {
        this.recordEvent('trend-declining', this.config.alerts.severity.trendDeclining, 'trend-analyzer', {
          trend: trendAnalysis.trend.overall,
          days: decliningDays,
          changePercent: trendAnalysis.velocity.monthlyChange
        });

        await this.sendAlert({
          severity: this.config.alerts.severity.trendDeclining,
          title: 'Declining Coverage Trend',
          message: `Coverage has been declining for ${decliningDays} days (${trendAnalysis.velocity.monthlyChange.toFixed(2)}% monthly change)`,
          data: { days: decliningDays, trend: trendAnalysis.trend, velocity: trendAnalysis.velocity }
        });

        await this.triggerAutomation('trend-declining', { days: decliningDays });
      }
    }
  }

  private async checkHotspots(analysis: CoverageAnalysis): Promise<void> {
    const criticalHotspots = analysis.hotspots.filter(h => h.severity === 'high');

    if (criticalHotspots.length > this.config.thresholds.hotspotIncrease) {
      this.recordEvent('hotspot-detected', this.config.alerts.severity.hotspotCritical, 'analyzer', {
        count: criticalHotspots.length,
        threshold: this.config.thresholds.hotspotIncrease
      });

      await this.sendAlert({
        severity: this.config.alerts.severity.hotspotCritical,
        title: 'Critical Coverage Hotspots',
        message: `${criticalHotspots.length} critical coverage hotspots detected`,
        data: { hotspots: criticalHotspots.map(h => ({ file: h.file, coverage: h.coverage })) }
      });

      await this.triggerAutomation('hotspot-critical', { count: criticalHotspots.length });
    }
  }

  private async sendAlert(alertData: Omit<AlertEvent, 'id' | 'timestamp' | 'channels' | 'sent' | 'error'>): Promise<void> {
    const alertId = this.generateAlertId();
    const alert: AlertEvent = {
      id: alertId,
      timestamp: new Date(),
      channels: [],
      sent: false,
      ...alertData
    };

    // Check throttling
    if (this.isThrottled(alertData.title)) {
      console.log(`Alert throttled: ${alertData.title}`);
      return;
    }

    try {
      // Send to configured channels
      const enabledChannels = this.config.alerts.channels.filter(
        channel => channel.enabled && channel.severityFilter.includes(alertData.severity)
      );

      for (const channel of enabledChannels) {
        try {
          await this.sendToChannel(channel, alert);
          alert.channels.push(channel.type);
        } catch (error) {
          console.error(`Failed to send alert to ${channel.type}:`, error.message);
          alert.error = error.message;
        }
      }

      alert.sent = alert.channels.length > 0;
      this.alerts.push(alert);

      // Update throttling
      this.updateThrottling(alertData.title);

      // Record alert event
      this.recordEvent('alert-sent', 'info', 'monitor', {
        alertId,
        severity: alertData.severity,
        channels: alert.channels.length
      });

      this.emit('alert', alert);

    } catch (error) {
      alert.error = error.message;
      this.alerts.push(alert);
      console.error('Failed to send alert:', error);
    }
  }

  private async sendToChannel(channel: AlertChannel, alert: AlertEvent): Promise<void> {
    switch (channel.type) {
      case 'slack':
        await this.sendSlackAlert(channel.config, alert);
        break;
      case 'email':
        await this.sendEmailAlert(channel.config, alert);
        break;
      case 'webhook':
        await this.sendWebhookAlert(channel.config, alert);
        break;
      case 'github':
        await this.sendGitHubAlert(channel.config, alert);
        break;
      case 'pagerduty':
        await this.sendPagerDutyAlert(channel.config, alert);
        break;
      case 'teams':
        await this.sendTeamsAlert(channel.config, alert);
        break;
      default:
        throw new Error(`Unsupported channel type: ${channel.type}`);
    }
  }

  private async sendSlackAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would use Slack API
    console.log(`[SLACK] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async sendEmailAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would use email service
    console.log(`[EMAIL] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async sendWebhookAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would send HTTP POST to webhook URL
    console.log(`[WEBHOOK] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async sendGitHubAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would create GitHub issue or comment
    console.log(`[GITHUB] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async sendPagerDutyAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would use PagerDuty API
    console.log(`[PAGERDUTY] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async sendTeamsAlert(config: any, alert: AlertEvent): Promise<void> {
    // Implementation would use Microsoft Teams webhook
    console.log(`[TEAMS] ${alert.severity.toUpperCase()}: ${alert.title} - ${alert.message}`);
  }

  private async triggerAutomation(triggerType: string, data: any): Promise<void> {
    if (!this.config.automation.enabled) return;

    const relevantActions = this.config.automation.actions.filter(
      action => action.enabled && action.trigger.event === triggerType
    );

    for (const action of relevantActions) {
      try {
        // Check conditions
        if (!this.evaluateConditions(action.conditions, data)) {
          continue;
        }

        // Check rate limiting
        if (!this.checkRateLimit(action)) {
          continue;
        }

        await this.executeAutomationAction(action, data);

        this.recordEvent('automation-triggered', 'info', 'automation', {
          actionType: action.action.type,
          trigger: triggerType,
          data
        });

        this.metrics.automationRuns++;

      } catch (error) {
        console.error(`Automation action failed:`, error);
        this.recordEvent('system-error', 'error', 'automation', { error: error.message });
      }
    }
  }

  private async executeAutomationAction(action: AutomationAction, data: any): Promise<void> {
    switch (action.action.type) {
      case 'create-issue':
        await this.createIssue(action.action.config, data);
        break;
      case 'create-pr':
        await this.createPR(action.action.config, data);
        break;
      case 'notify-team':
        await this.notifyTeam(action.action.config, data);
        break;
      case 'run-script':
        await this.runScript(action.action.config, data);
        break;
      case 'block-merge':
        await this.blockMerge(action.action.config, data);
        break;
      case 'schedule-review':
        await this.scheduleReview(action.action.config, data);
        break;
      default:
        throw new Error(`Unsupported automation action: ${action.action.type}`);
    }
  }

  private async createIssue(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Creating issue:', config, data);
  }

  private async createPR(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Creating PR:', config, data);
  }

  private async notifyTeam(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Notifying team:', config, data);
  }

  private async runScript(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Running script:', config, data);
  }

  private async blockMerge(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Blocking merge:', config, data);
  }

  private async scheduleReview(config: any, data: any): Promise<void> {
    console.log('[AUTOMATION] Scheduling review:', config, data);
  }

  private evaluateConditions(conditions: AutomationCondition[], data: any): boolean {
    return conditions.every(condition => {
      const value = this.getDataValue(data, condition.field);

      switch (condition.operator) {
        case 'equals':
          return value === condition.value;
        case 'greater':
          return value > condition.value;
        case 'less':
          return value < condition.value;
        case 'contains':
          return String(value).includes(String(condition.value));
        default:
          return false;
      }
    });
  }

  private getDataValue(data: any, field: string): any {
    const parts = field.split('.');
    let value = data;

    for (const part of parts) {
      value = value?.[part];
    }

    return value;
  }

  private checkRateLimit(action: AutomationAction): boolean {
    // Simple rate limiting implementation
    return true; // TODO: Implement proper rate limiting
  }

  private isThrottled(alertType: string): boolean {
    if (!this.config.alerts.throttling.enabled) return false;

    const lastAlert = this.alertThrottling.get(alertType);
    if (!lastAlert) return false;

    const windowMs = this.config.alerts.throttling.window * 60 * 1000;
    return (Date.now() - lastAlert.getTime()) < windowMs;
  }

  private updateThrottling(alertType: string): void {
    if (this.config.alerts.throttling.enabled) {
      this.alertThrottling.set(alertType, new Date());
    }
  }

  private isHealthy(analysis: CoverageAnalysis): boolean {
    const failedGates = analysis.qualityGateResults.filter(qg => !qg.passed);
    const criticalHotspots = analysis.hotspots.filter(h => h.severity === 'high');

    return failedGates.length === 0 && criticalHotspots.length <= this.config.thresholds.hotspotIncrease;
  }

  private calculateDecliningDays(trendAnalysis: TrendAnalysis): number {
    // Simplified calculation - would need more sophisticated analysis
    if (trendAnalysis.velocity.monthlyChange < -2) return 30;
    if (trendAnalysis.velocity.weeklyChange < -1) return 7;
    return 0;
  }

  private recordEvent(type: MonitoringEventType, severity: AlertSeverity, source: string, data: any): void {
    const event: MonitoringEvent = {
      id: this.generateEventId(),
      timestamp: new Date(),
      type,
      severity,
      source,
      data,
      handled: false,
      suppressed: false
    };

    this.events.push(event);
    this.emit('event', event);

    // Keep only recent events to prevent memory issues
    if (this.events.length > 10000) {
      this.events = this.events.slice(-5000);
    }
  }

  private updateMetrics(responseTime: number): void {
    this.metrics.eventsProcessed++;
    this.metrics.responseTime = (this.metrics.responseTime + responseTime) / 2;
    this.metrics.lastUpdate = new Date();
  }

  private async performHealthChecks(): Promise<void> {
    // Check system health
    const memUsage = process.memoryUsage();
    if (memUsage.heapUsed > 500 * 1024 * 1024) { // 500MB
      this.recordEvent('system-error', 'warning', 'monitor', {
        message: 'High memory usage',
        memoryUsage: memUsage
      });
    }

    // Check response time
    if (this.metrics.responseTime > this.config.thresholds.responseTimeThreshold) {
      this.recordEvent('system-error', 'warning', 'monitor', {
        message: 'High response time',
        responseTime: this.metrics.responseTime
      });
    }
  }

  private async cleanupOldData(): Promise<void> {
    const now = Date.now();
    const retentionMs = {
      alerts: this.config.retention.alerts * 24 * 60 * 60 * 1000,
      events: this.config.retention.events * 24 * 60 * 60 * 1000
    };

    // Clean old alerts
    this.alerts = this.alerts.filter(alert =>
      (now - alert.timestamp.getTime()) < retentionMs.alerts
    );

    // Clean old events
    this.events = this.events.filter(event =>
      (now - event.timestamp.getTime()) < retentionMs.events
    );
  }

  private async generatePeriodicReports(): Promise<void> {
    // Generate daily/weekly reports
    const now = new Date();
    const isNewDay = now.getHours() === 0 && now.getMinutes() < 5;
    const isNewWeek = isNewDay && now.getDay() === 1;

    if (isNewDay) {
      await this.generateDailyReport();
    }

    if (isNewWeek) {
      await this.generateWeeklyReport();
    }
  }

  private async generateDailyReport(): Promise<void> {
    const report = await this.generateReport('daily');
    this.emit('report', report);
  }

  private async generateWeeklyReport(): Promise<void> {
    const report = await this.generateReport('weekly');
    this.emit('report', report);
  }

  private async generateReport(period: string): Promise<MonitoringReport> {
    const periodMs = period === 'daily' ? 24 * 60 * 60 * 1000 : 7 * 24 * 60 * 60 * 1000;
    const cutoff = new Date(Date.now() - periodMs);

    const events = this.events.filter(e => e.timestamp >= cutoff);
    const alerts = this.alerts.filter(a => a.timestamp >= cutoff);

    const insights = this.generateInsights(events, alerts);
    const recommendations = this.generateRecommendations(insights);

    return {
      period,
      events,
      alerts,
      metrics: { ...this.metrics },
      insights,
      recommendations
    };
  }

  private generateInsights(events: MonitoringEvent[], alerts: AlertEvent[]): MonitoringInsight[] {
    const insights: MonitoringInsight[] = [];

    // Alert frequency pattern
    const alertsByHour = new Map<number, number>();
    alerts.forEach(alert => {
      const hour = alert.timestamp.getHours();
      alertsByHour.set(hour, (alertsByHour.get(hour) || 0) + 1);
    });

    const peakHour = Array.from(alertsByHour.entries())
      .sort((a, b) => b[1] - a[1])[0];

    if (peakHour && peakHour[1] > 2) {
      insights.push({
        type: 'pattern',
        title: 'Alert Concentration Pattern',
        description: `Most alerts occur around ${peakHour[0]}:00 (${peakHour[1]} alerts)`,
        impact: 'medium',
        confidence: 75,
        data: { peakHour: peakHour[0], count: peakHour[1] }
      });
    }

    // Error rate analysis
    const errorEvents = events.filter(e => e.severity === 'error').length;
    const errorRate = errorEvents / Math.max(1, events.length);

    if (errorRate > 0.1) {
      insights.push({
        type: 'anomaly',
        title: 'High Error Rate',
        description: `Error rate is ${(errorRate * 100).toFixed(1)}% (${errorEvents}/${events.length})`,
        impact: 'high',
        confidence: 90,
        data: { errorRate, errorEvents, totalEvents: events.length }
      });
    }

    return insights;
  }

  private generateRecommendations(insights: MonitoringInsight[]): string[] {
    const recommendations: string[] = [];

    insights.forEach(insight => {
      switch (insight.type) {
        case 'pattern':
          if (insight.title.includes('Alert Concentration')) {
            recommendations.push('Consider investigating why alerts cluster at specific times');
          }
          break;
        case 'anomaly':
          if (insight.title.includes('High Error Rate')) {
            recommendations.push('Review system logs and improve error handling');
          }
          break;
        case 'performance':
          recommendations.push('Optimize monitoring performance and reduce resource usage');
          break;
      }
    });

    return recommendations;
  }

  private async loadHistoricalData(): Promise<void> {
    try {
      const dataPath = path.join(process.cwd(), 'coverage-monitoring.json');
      const data = await fs.readFile(dataPath, 'utf-8');
      const parsed = JSON.parse(data);

      this.events = parsed.events?.map((e: any) => ({
        ...e,
        timestamp: new Date(e.timestamp)
      })) || [];

      this.alerts = parsed.alerts?.map((a: any) => ({
        ...a,
        timestamp: new Date(a.timestamp)
      })) || [];

      this.metrics = { ...this.metrics, ...parsed.metrics };

    } catch (error) {
      // No historical data available
      this.events = [];
      this.alerts = [];
    }
  }

  private async saveHistoricalData(): Promise<void> {
    try {
      const dataPath = path.join(process.cwd(), 'coverage-monitoring.json');
      const data = {
        events: this.events.slice(-1000), // Keep last 1000 events
        alerts: this.alerts.slice(-100),   // Keep last 100 alerts
        metrics: this.metrics
      };

      await fs.writeFile(dataPath, JSON.stringify(data, null, 2), 'utf-8');
    } catch (error) {
      console.error('Failed to save monitoring data:', error);
    }
  }

  private setupEventHandlers(): void {
    this.on('event', (event: MonitoringEvent) => {
      // Handle specific events
      if (event.severity === 'critical') {
        console.warn(`[CRITICAL EVENT] ${event.type}: ${JSON.stringify(event.data)}`);
      }
    });

    this.on('alert', (alert: AlertEvent) => {
      console.log(`[ALERT] ${alert.severity.toUpperCase()}: ${alert.title}`);
    });
  }

  private initializeMetrics(): MonitoringMetrics {
    return {
      uptime: 0,
      eventsProcessed: 0,
      alertsSent: 0,
      automationRuns: 0,
      errorRate: 0,
      responseTime: 0,
      lastUpdate: new Date()
    };
  }

  private generateEventId(): string {
    return `event-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateAlertId(): string {
    return `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Public API
  getMetrics(): MonitoringMetrics {
    this.metrics.uptime = Date.now() - (this.metrics.lastUpdate?.getTime() || Date.now());
    return { ...this.metrics };
  }

  getRecentEvents(limit: number = 100): MonitoringEvent[] {
    return this.events.slice(-limit);
  }

  getRecentAlerts(limit: number = 50): AlertEvent[] {
    return this.alerts.slice(-limit);
  }

  async getReport(period: string): Promise<MonitoringReport> {
    return this.generateReport(period);
  }

  isRunning(): boolean {
    return this.isRunning;
  }
}