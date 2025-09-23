/**
 * Performance monitoring and metrics collection for AI adapters
 */

import { AIProvider, AIInput, AIOutput, HealthStatus } from '../core/types.js';

export interface PerformanceMetrics {
  /** Adapter/provider name */
  provider: string;
  /** Request timing metrics */
  timing: {
    averageResponseTime: number;
    p50ResponseTime: number;
    p95ResponseTime: number;
    p99ResponseTime: number;
    minResponseTime: number;
    maxResponseTime: number;
  };
  /** Request success/failure rates */
  reliability: {
    totalRequests: number;
    successfulRequests: number;
    failedRequests: number;
    successRate: number;
    errorRate: number;
  };
  /** Cost and usage metrics */
  usage: {
    totalTokens: number;
    inputTokens: number;
    outputTokens: number;
    totalCost: number;
    averageCostPerRequest: number;
    averageCostPerToken: number;
  };
  /** Throughput metrics */
  throughput: {
    requestsPerMinute: number;
    tokensPerMinute: number;
    peakRequestsPerMinute: number;
    peakTokensPerMinute: number;
  };
  /** Error distribution */
  errors: Record<string, number>;
  /** Time period for metrics */
  period: {
    start: Date;
    end: Date;
    duration: number;
  };
}

export interface RequestMetric {
  provider: string;
  timestamp: Date;
  responseTime: number;
  success: boolean;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  cost: number;
  errorType?: string;
  errorMessage?: string;
  model?: string;
}

export interface AlertRule {
  id: string;
  name: string;
  condition: {
    metric: keyof PerformanceMetrics['timing'] | keyof PerformanceMetrics['reliability'] | 'cost';
    operator: '>' | '<' | '>=' | '<=' | '=' | '!=';
    value: number;
    duration?: number; // Time window in seconds
  };
  action: 'log' | 'email' | 'webhook' | 'disable_provider';
  enabled: boolean;
}

export interface PerformanceAlert {
  id: string;
  ruleId: string;
  provider: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: Date;
  value: number;
  acknowledged: boolean;
}

export class PerformanceMonitor {
  private metrics: RequestMetric[] = [];
  private alerts: PerformanceAlert[] = [];
  private alertRules: AlertRule[] = [];
  private monitoringInterval?: NodeJS.Timeout;

  constructor(
    private config: {
      /** Maximum number of metrics to store */
      maxMetrics?: number;
      /** How often to check alert rules (ms) */
      alertCheckInterval?: number;
      /** Enable automatic cleanup of old metrics */
      autoCleanup?: boolean;
      /** Days to keep metrics */
      retentionDays?: number;
    } = {}
  ) {
    this.config = {
      maxMetrics: 10000,
      alertCheckInterval: 60000, // 1 minute
      autoCleanup: true,
      retentionDays: 30,
      ...config
    };

    if (this.config.alertCheckInterval) {
      this.startMonitoring();
    }
  }

  /**
   * Record a request metric
   */
  recordRequest(
    provider: string,
    responseTime: number,
    success: boolean,
    tokens: { input: number; output: number; total: number },
    cost: number,
    error?: { type: string; message: string },
    model?: string
  ): void {
    const metric: RequestMetric = {
      provider,
      timestamp: new Date(),
      responseTime,
      success,
      tokens,
      cost,
      errorType: error?.type,
      errorMessage: error?.message,
      model
    };

    this.metrics.push(metric);

    // Cleanup old metrics if necessary
    if (this.config.maxMetrics && this.metrics.length > this.config.maxMetrics) {
      this.metrics = this.metrics.slice(-this.config.maxMetrics);
    }

    // Auto cleanup based on retention
    if (this.config.autoCleanup) {
      this.cleanupOldMetrics();
    }
  }

  /**
   * Get performance metrics for a provider
   */
  getMetrics(
    provider?: string,
    startDate?: Date,
    endDate?: Date
  ): PerformanceMetrics | Record<string, PerformanceMetrics> {
    const filteredMetrics = this.getFilteredMetrics(provider, startDate, endDate);

    if (provider) {
      return this.calculateMetricsForProvider(provider, filteredMetrics);
    }

    // Return metrics for all providers
    const allProviders = [...new Set(filteredMetrics.map(m => m.provider))];
    const result: Record<string, PerformanceMetrics> = {};

    for (const p of allProviders) {
      const providerMetrics = filteredMetrics.filter(m => m.provider === p);
      result[p] = this.calculateMetricsForProvider(p, providerMetrics);
    }

    return result;
  }

  /**
   * Get real-time performance summary
   */
  getRealTimeMetrics(windowMinutes: number = 5): Record<string, {
    requestsPerMinute: number;
    averageResponseTime: number;
    successRate: number;
    tokensPerMinute: number;
  }> {
    const now = new Date();
    const windowStart = new Date(now.getTime() - windowMinutes * 60 * 1000);

    const recentMetrics = this.metrics.filter(m => m.timestamp >= windowStart);
    const providers = [...new Set(recentMetrics.map(m => m.provider))];

    const result: Record<string, any> = {};

    for (const provider of providers) {
      const providerMetrics = recentMetrics.filter(m => m.provider === provider);

      if (providerMetrics.length === 0) continue;

      const totalRequests = providerMetrics.length;
      const successfulRequests = providerMetrics.filter(m => m.success).length;
      const totalResponseTime = providerMetrics.reduce((sum, m) => sum + m.responseTime, 0);
      const totalTokens = providerMetrics.reduce((sum, m) => sum + m.tokens.total, 0);

      result[provider] = {
        requestsPerMinute: totalRequests / windowMinutes,
        averageResponseTime: totalResponseTime / totalRequests,
        successRate: (successfulRequests / totalRequests) * 100,
        tokensPerMinute: totalTokens / windowMinutes
      };
    }

    return result;
  }

  /**
   * Add alert rule
   */
  addAlertRule(rule: Omit<AlertRule, 'id'>): string {
    const id = `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.alertRules.push({ ...rule, id });
    return id;
  }

  /**
   * Remove alert rule
   */
  removeAlertRule(ruleId: string): boolean {
    const index = this.alertRules.findIndex(r => r.id === ruleId);
    if (index !== -1) {
      this.alertRules.splice(index, 1);
      return true;
    }
    return false;
  }

  /**
   * Get alert rules
   */
  getAlertRules(): AlertRule[] {
    return [...this.alertRules];
  }

  /**
   * Get alerts
   */
  getAlerts(acknowledged?: boolean): PerformanceAlert[] {
    return this.alerts
      .filter(a => acknowledged === undefined || a.acknowledged === acknowledged)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  /**
   * Acknowledge alert
   */
  acknowledgeAlert(alertId: string): boolean {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      return true;
    }
    return false;
  }

  /**
   * Generate performance report
   */
  generateReport(
    startDate?: Date,
    endDate?: Date,
    format: 'text' | 'json' | 'html' = 'text'
  ): string {
    const metrics = this.getMetrics(undefined, startDate, endDate) as Record<string, PerformanceMetrics>;

    if (format === 'json') {
      return JSON.stringify({
        metrics,
        alerts: this.getAlerts(),
        generatedAt: new Date().toISOString()
      }, null, 2);
    }

    if (format === 'html') {
      return this.generateHtmlReport(metrics);
    }

    // Text format
    let report = 'AI Adapter Performance Report\n';
    report += '================================\n\n';

    for (const [provider, metric] of Object.entries(metrics)) {
      report += `Provider: ${provider}\n`;
      report += `  Requests: ${metric.reliability.totalRequests} (${metric.reliability.successRate.toFixed(1)}% success)\n`;
      report += `  Avg Response Time: ${metric.timing.averageResponseTime.toFixed(0)}ms\n`;
      report += `  Total Cost: $${metric.usage.totalCost.toFixed(4)}\n`;
      report += `  Tokens: ${metric.usage.totalTokens.toLocaleString()}\n`;
      report += `  Throughput: ${metric.throughput.requestsPerMinute.toFixed(1)} req/min\n\n`;
    }

    const unacknowledgedAlerts = this.getAlerts(false);
    if (unacknowledgedAlerts.length > 0) {
      report += 'Active Alerts:\n';
      report += '==============\n';
      for (const alert of unacknowledgedAlerts) {
        report += `  ${alert.severity.toUpperCase()}: ${alert.message}\n`;
      }
      report += '\n';
    }

    return report;
  }

  /**
   * Compare providers
   */
  compareProviders(providers: string[], startDate?: Date, endDate?: Date): {
    comparison: Record<string, PerformanceMetrics>;
    ranking: {
      bySpeed: string[];
      byReliability: string[];
      byCost: string[];
    };
  } {
    const comparison: Record<string, PerformanceMetrics> = {};

    for (const provider of providers) {
      const metrics = this.getMetrics(provider, startDate, endDate) as PerformanceMetrics;
      comparison[provider] = metrics;
    }

    // Create rankings
    const ranking = {
      bySpeed: providers.sort((a, b) =>
        comparison[a].timing.averageResponseTime - comparison[b].timing.averageResponseTime
      ),
      byReliability: providers.sort((a, b) =>
        comparison[b].reliability.successRate - comparison[a].reliability.successRate
      ),
      byCost: providers.sort((a, b) =>
        comparison[a].usage.averageCostPerToken - comparison[b].usage.averageCostPerToken
      )
    };

    return { comparison, ranking };
  }

  /**
   * Get health trend
   */
  getHealthTrend(provider: string, hours: number = 24): {
    hourly: Array<{
      hour: Date;
      requests: number;
      averageResponseTime: number;
      successRate: number;
      cost: number;
    }>;
    trend: 'improving' | 'stable' | 'degrading';
  } {
    const now = new Date();
    const startTime = new Date(now.getTime() - hours * 60 * 60 * 1000);

    const metrics = this.getFilteredMetrics(provider, startTime);
    const hourlyData: Array<any> = [];

    for (let i = 0; i < hours; i++) {
      const hourStart = new Date(startTime.getTime() + i * 60 * 60 * 1000);
      const hourEnd = new Date(hourStart.getTime() + 60 * 60 * 1000);

      const hourMetrics = metrics.filter(m =>
        m.timestamp >= hourStart && m.timestamp < hourEnd
      );

      if (hourMetrics.length === 0) {
        hourlyData.push({
          hour: hourStart,
          requests: 0,
          averageResponseTime: 0,
          successRate: 0,
          cost: 0
        });
        continue;
      }

      const successCount = hourMetrics.filter(m => m.success).length;
      const totalResponseTime = hourMetrics.reduce((sum, m) => sum + m.responseTime, 0);
      const totalCost = hourMetrics.reduce((sum, m) => sum + m.cost, 0);

      hourlyData.push({
        hour: hourStart,
        requests: hourMetrics.length,
        averageResponseTime: totalResponseTime / hourMetrics.length,
        successRate: (successCount / hourMetrics.length) * 100,
        cost: totalCost
      });
    }

    // Determine trend
    const recentHours = hourlyData.slice(-6); // Last 6 hours
    const earlierHours = hourlyData.slice(-12, -6); // 6 hours before that

    const recentAvgResponseTime = recentHours.reduce((sum, h) => sum + h.averageResponseTime, 0) / recentHours.length;
    const earlierAvgResponseTime = earlierHours.reduce((sum, h) => sum + h.averageResponseTime, 0) / earlierHours.length;

    const recentAvgSuccessRate = recentHours.reduce((sum, h) => sum + h.successRate, 0) / recentHours.length;
    const earlierAvgSuccessRate = earlierHours.reduce((sum, h) => sum + h.successRate, 0) / earlierHours.length;

    let trend: 'improving' | 'stable' | 'degrading' = 'stable';

    const responseTimeImprovement = (earlierAvgResponseTime - recentAvgResponseTime) / earlierAvgResponseTime;
    const successRateImprovement = (recentAvgSuccessRate - earlierAvgSuccessRate) / 100;

    if (responseTimeImprovement > 0.1 || successRateImprovement > 0.05) {
      trend = 'improving';
    } else if (responseTimeImprovement < -0.1 || successRateImprovement < -0.05) {
      trend = 'degrading';
    }

    return { hourly: hourlyData, trend };
  }

  /**
   * Clean up old metrics
   */
  cleanupOldMetrics(): void {
    if (!this.config.retentionDays) return;

    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - this.config.retentionDays);

    this.metrics = this.metrics.filter(m => m.timestamp >= cutoffDate);
  }

  /**
   * Stop monitoring
   */
  destroy(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }
  }

  /**
   * Start alert monitoring
   */
  private startMonitoring(): void {
    if (this.monitoringInterval) return;

    this.monitoringInterval = setInterval(() => {
      this.checkAlertRules();
    }, this.config.alertCheckInterval);
  }

  /**
   * Check alert rules
   */
  private checkAlertRules(): void {
    for (const rule of this.alertRules) {
      if (!rule.enabled) continue;

      const providers = [...new Set(this.metrics.map(m => m.provider))];

      for (const provider of providers) {
        const windowStart = new Date();
        if (rule.condition.duration) {
          windowStart.setSeconds(windowStart.getSeconds() - rule.condition.duration);
        }

        const metrics = this.getMetrics(provider, windowStart) as PerformanceMetrics;
        const value = this.getMetricValue(metrics, rule.condition.metric);

        if (this.evaluateCondition(value, rule.condition.operator, rule.condition.value)) {
          this.triggerAlert(rule, provider, value);
        }
      }
    }
  }

  private getMetricValue(metrics: PerformanceMetrics, metricPath: string): number {
    const parts = metricPath.split('.');
    let value: any = metrics;

    for (const part of parts) {
      value = value[part];
      if (value === undefined) return 0;
    }

    return typeof value === 'number' ? value : 0;
  }

  private evaluateCondition(value: number, operator: string, threshold: number): boolean {
    switch (operator) {
      case '>': return value > threshold;
      case '<': return value < threshold;
      case '>=': return value >= threshold;
      case '<=': return value <= threshold;
      case '=': return value === threshold;
      case '!=': return value !== threshold;
      default: return false;
    }
  }

  private triggerAlert(rule: AlertRule, provider: string, value: number): void {
    // Check if alert already exists for this rule and provider
    const existingAlert = this.alerts.find(a =>
      a.ruleId === rule.id &&
      a.provider === provider &&
      !a.acknowledged &&
      a.timestamp.getTime() > Date.now() - 5 * 60 * 1000 // Last 5 minutes
    );

    if (existingAlert) return; // Don't duplicate recent alerts

    const severity = this.determineSeverity(rule.condition.metric, value);

    const alert: PerformanceAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      ruleId: rule.id,
      provider,
      message: `${rule.name}: ${rule.condition.metric} is ${value} (threshold: ${rule.condition.value})`,
      severity,
      timestamp: new Date(),
      value,
      acknowledged: false
    };

    this.alerts.push(alert);

    // Execute alert action
    this.executeAlertAction(rule.action, alert);
  }

  private determineSeverity(metric: string, value: number): 'low' | 'medium' | 'high' | 'critical' {
    // Simple heuristics - could be made configurable
    if (metric.includes('errorRate') && value > 20) return 'critical';
    if (metric.includes('responseTime') && value > 10000) return 'high';
    if (metric.includes('successRate') && value < 80) return 'high';
    return 'medium';
  }

  private executeAlertAction(action: string, alert: PerformanceAlert): void {
    switch (action) {
      case 'log':
        console.warn(`[Performance Alert] ${alert.message}`);
        break;
      case 'email':
        // Email implementation would go here
        console.log(`[Email Alert] ${alert.message}`);
        break;
      case 'webhook':
        // Webhook implementation would go here
        console.log(`[Webhook Alert] ${alert.message}`);
        break;
      case 'disable_provider':
        console.error(`[Provider Disabled] ${alert.provider} disabled due to: ${alert.message}`);
        // Provider disabling logic would go here
        break;
    }
  }

  private getFilteredMetrics(provider?: string, startDate?: Date, endDate?: Date): RequestMetric[] {
    return this.metrics.filter(m => {
      if (provider && m.provider !== provider) return false;
      if (startDate && m.timestamp < startDate) return false;
      if (endDate && m.timestamp > endDate) return false;
      return true;
    });
  }

  private calculateMetricsForProvider(provider: string, metrics: RequestMetric[]): PerformanceMetrics {
    if (metrics.length === 0) {
      return this.getEmptyMetrics(provider);
    }

    const responseTimes = metrics.map(m => m.responseTime).sort((a, b) => a - b);
    const successfulRequests = metrics.filter(m => m.success).length;
    const totalTokens = metrics.reduce((sum, m) => sum + m.tokens.total, 0);
    const inputTokens = metrics.reduce((sum, m) => sum + m.tokens.input, 0);
    const outputTokens = metrics.reduce((sum, m) => sum + m.tokens.output, 0);
    const totalCost = metrics.reduce((sum, m) => sum + m.cost, 0);

    // Calculate percentiles
    const p50Index = Math.floor(responseTimes.length * 0.5);
    const p95Index = Math.floor(responseTimes.length * 0.95);
    const p99Index = Math.floor(responseTimes.length * 0.99);

    // Calculate throughput
    const timeSpan = (metrics[metrics.length - 1].timestamp.getTime() - metrics[0].timestamp.getTime()) / 60000; // minutes
    const requestsPerMinute = timeSpan > 0 ? metrics.length / timeSpan : 0;
    const tokensPerMinute = timeSpan > 0 ? totalTokens / timeSpan : 0;

    // Error distribution
    const errors: Record<string, number> = {};
    for (const metric of metrics) {
      if (!metric.success && metric.errorType) {
        errors[metric.errorType] = (errors[metric.errorType] || 0) + 1;
      }
    }

    return {
      provider,
      timing: {
        averageResponseTime: responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length,
        p50ResponseTime: responseTimes[p50Index] || 0,
        p95ResponseTime: responseTimes[p95Index] || 0,
        p99ResponseTime: responseTimes[p99Index] || 0,
        minResponseTime: responseTimes[0] || 0,
        maxResponseTime: responseTimes[responseTimes.length - 1] || 0
      },
      reliability: {
        totalRequests: metrics.length,
        successfulRequests,
        failedRequests: metrics.length - successfulRequests,
        successRate: (successfulRequests / metrics.length) * 100,
        errorRate: ((metrics.length - successfulRequests) / metrics.length) * 100
      },
      usage: {
        totalTokens,
        inputTokens,
        outputTokens,
        totalCost,
        averageCostPerRequest: totalCost / metrics.length,
        averageCostPerToken: totalTokens > 0 ? totalCost / totalTokens : 0
      },
      throughput: {
        requestsPerMinute,
        tokensPerMinute,
        peakRequestsPerMinute: requestsPerMinute, // Simplified - could track actual peaks
        peakTokensPerMinute: tokensPerMinute // Simplified - could track actual peaks
      },
      errors,
      period: {
        start: metrics[0].timestamp,
        end: metrics[metrics.length - 1].timestamp,
        duration: metrics[metrics.length - 1].timestamp.getTime() - metrics[0].timestamp.getTime()
      }
    };
  }

  private getEmptyMetrics(provider: string): PerformanceMetrics {
    const now = new Date();
    return {
      provider,
      timing: {
        averageResponseTime: 0,
        p50ResponseTime: 0,
        p95ResponseTime: 0,
        p99ResponseTime: 0,
        minResponseTime: 0,
        maxResponseTime: 0
      },
      reliability: {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        successRate: 0,
        errorRate: 0
      },
      usage: {
        totalTokens: 0,
        inputTokens: 0,
        outputTokens: 0,
        totalCost: 0,
        averageCostPerRequest: 0,
        averageCostPerToken: 0
      },
      throughput: {
        requestsPerMinute: 0,
        tokensPerMinute: 0,
        peakRequestsPerMinute: 0,
        peakTokensPerMinute: 0
      },
      errors: {},
      period: {
        start: now,
        end: now,
        duration: 0
      }
    };
  }

  private generateHtmlReport(metrics: Record<string, PerformanceMetrics>): string {
    // Basic HTML report template
    return `
<!DOCTYPE html>
<html>
<head>
    <title>AI Adapter Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .provider { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; }
        .alerts { background: #fff2cd; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>AI Adapter Performance Report</h1>
    <p>Generated: ${new Date().toISOString()}</p>

    ${Object.entries(metrics).map(([provider, metric]) => `
        <div class="provider">
            <h2>${provider}</h2>
            <div class="metric">
                <strong>Requests:</strong> ${metric.reliability.totalRequests}<br>
                <strong>Success Rate:</strong> ${metric.reliability.successRate.toFixed(1)}%
            </div>
            <div class="metric">
                <strong>Avg Response:</strong> ${metric.timing.averageResponseTime.toFixed(0)}ms<br>
                <strong>P95 Response:</strong> ${metric.timing.p95ResponseTime.toFixed(0)}ms
            </div>
            <div class="metric">
                <strong>Total Cost:</strong> $${metric.usage.totalCost.toFixed(4)}<br>
                <strong>Tokens:</strong> ${metric.usage.totalTokens.toLocaleString()}
            </div>
            <div class="metric">
                <strong>Throughput:</strong> ${metric.throughput.requestsPerMinute.toFixed(1)} req/min<br>
                <strong>Token Rate:</strong> ${metric.throughput.tokensPerMinute.toFixed(0)} tok/min
            </div>
        </div>
    `).join('')}

    ${this.getAlerts(false).length > 0 ? `
        <div class="alerts">
            <h3>Active Alerts</h3>
            ${this.getAlerts(false).map(alert => `
                <p><strong>${alert.severity.toUpperCase()}:</strong> ${alert.message}</p>
            `).join('')}
        </div>
    ` : ''}
</body>
</html>
    `.trim();
  }
}