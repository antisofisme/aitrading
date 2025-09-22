/**
 * ErrorDNA System - Intelligent Error Categorization and Analysis
 * Advanced error pattern recognition and root cause analysis
 */

import { EventEmitter } from 'events';
import crypto from 'crypto';
import {
  ErrorDNA,
  ErrorCategory,
  ErrorSeverity,
  RootCauseAnalysis,
  TimelineEvent,
  BusinessImpact,
  LogEntry
} from '../types';

interface ErrorPattern {
  pattern: string;
  frequency: number;
  components: Set<string>;
  firstSeen: Date;
  lastSeen: Date;
  resolved: boolean;
  similarErrors: string[];
}

interface ErrorCluster {
  id: string;
  patterns: ErrorPattern[];
  rootCause?: string;
  affectedSystems: string[];
  timeWindow: { start: Date; end: Date };
  severity: ErrorSeverity;
}

export class ErrorDNASystem extends EventEmitter {
  private errorPatterns: Map<string, ErrorPattern> = new Map();
  private errorClusters: Map<string, ErrorCluster> = new Map();
  private analysisQueue: LogEntry[] = [];
  private processingInterval: NodeJS.Timeout;
  private mlModel: ErrorMLModel;

  constructor() {
    super();
    this.mlModel = new ErrorMLModel();
    this.startProcessing();
  }

  /**
   * Analyze error and generate ErrorDNA
   */
  async analyzeError(logEntry: LogEntry): Promise<ErrorDNA> {
    const pattern = this.extractErrorPattern(logEntry);
    const category = await this.categorizeError(logEntry);
    const severity = await this.calculateSeverity(logEntry);
    const businessImpact = await this.assessBusinessImpact(logEntry);

    const errorDNA: ErrorDNA = {
      id: crypto.randomUUID(),
      pattern,
      category,
      severity,
      frequency: 1,
      firstOccurrence: logEntry.timestamp,
      lastOccurrence: logEntry.timestamp,
      affectedComponents: [logEntry.sourceComponent],
      businessImpact
    };

    // Check if this pattern exists
    const existingPattern = this.errorPatterns.get(pattern);
    if (existingPattern) {
      existingPattern.frequency++;
      existingPattern.lastSeen = logEntry.timestamp;
      existingPattern.components.add(logEntry.sourceComponent);

      errorDNA.frequency = existingPattern.frequency;
      errorDNA.firstOccurrence = existingPattern.firstSeen;
      errorDNA.affectedComponents = Array.from(existingPattern.components);

      // Update similar errors using ML
      existingPattern.similarErrors = await this.findSimilarErrors(pattern);
    } else {
      this.errorPatterns.set(pattern, {
        pattern,
        frequency: 1,
        components: new Set([logEntry.sourceComponent]),
        firstSeen: logEntry.timestamp,
        lastSeen: logEntry.timestamp,
        resolved: false,
        similarErrors: []
      });
    }

    // Perform root cause analysis for high-impact errors
    if (severity >= ErrorSeverity.HIGH || errorDNA.frequency > 5) {
      errorDNA.rootCauseAnalysis = await this.performRootCauseAnalysis(logEntry, errorDNA);
      errorDNA.resolutionSteps = await this.generateResolutionSteps(errorDNA);
      errorDNA.preventionStrategy = await this.generatePreventionStrategy(errorDNA);
    }

    // Add to cluster analysis
    await this.updateErrorClusters(errorDNA, logEntry);

    this.emit('error:analyzed', errorDNA);

    // Trigger alerts for critical patterns
    if (this.shouldTriggerAlert(errorDNA)) {
      this.emit('error:alert', {
        errorDNA,
        alertType: this.determineAlertType(errorDNA),
        urgency: this.calculateUrgency(errorDNA)
      });
    }

    return errorDNA;
  }

  /**
   * Get error patterns by category or severity
   */
  getErrorPatterns(options: {
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    component?: string;
    timeWindow?: { start: Date; end: Date };
    onlyUnresolved?: boolean;
  } = {}): ErrorPattern[] {
    const patterns = Array.from(this.errorPatterns.values());

    return patterns.filter(pattern => {
      if (options.onlyUnresolved && pattern.resolved) return false;
      if (options.component && !pattern.components.has(options.component)) return false;
      if (options.timeWindow) {
        if (pattern.lastSeen < options.timeWindow.start || pattern.firstSeen > options.timeWindow.end) {
          return false;
        }
      }
      return true;
    });
  }

  /**
   * Get error clusters for trend analysis
   */
  getErrorClusters(timeWindow?: { start: Date; end: Date }): ErrorCluster[] {
    const clusters = Array.from(this.errorClusters.values());

    if (timeWindow) {
      return clusters.filter(cluster => {
        return cluster.timeWindow.end >= timeWindow.start && cluster.timeWindow.start <= timeWindow.end;
      });
    }

    return clusters;
  }

  /**
   * Mark error pattern as resolved
   */
  markPatternResolved(pattern: string, resolutionNotes?: string): boolean {
    const errorPattern = this.errorPatterns.get(pattern);
    if (errorPattern) {
      errorPattern.resolved = true;
      this.emit('error:resolved', { pattern, resolutionNotes });
      return true;
    }
    return false;
  }

  /**
   * Get error trends and statistics
   */
  getErrorTrends(timeWindow: { start: Date; end: Date }): {
    totalErrors: number;
    errorsByCategory: Record<ErrorCategory, number>;
    errorsBySeverity: Record<ErrorSeverity, number>;
    topComponents: Array<{ component: string; count: number }>;
    trendDirection: 'INCREASING' | 'DECREASING' | 'STABLE';
    criticalPatterns: ErrorPattern[];
  } {
    const patterns = this.getErrorPatterns({ timeWindow });

    const totalErrors = patterns.reduce((sum, p) => sum + p.frequency, 0);

    // Count by category and severity (simplified for demo)
    const errorsByCategory = {} as Record<ErrorCategory, number>;
    const errorsBySeverity = {} as Record<ErrorSeverity, number>;

    // Component analysis
    const componentCounts = new Map<string, number>();
    patterns.forEach(p => {
      p.components.forEach(component => {
        componentCounts.set(component, (componentCounts.get(component) || 0) + p.frequency);
      });
    });

    const topComponents = Array.from(componentCounts.entries())
      .map(([component, count]) => ({ component, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    // Calculate trend (simplified)
    const trendDirection = this.calculateTrendDirection(patterns, timeWindow);

    // Critical patterns
    const criticalPatterns = patterns.filter(p => p.frequency > 10 && !p.resolved);

    return {
      totalErrors,
      errorsByCategory,
      errorsBySeverity,
      topComponents,
      trendDirection,
      criticalPatterns
    };
  }

  /**
   * Generate error report for specific component
   */
  async generateComponentReport(component: string, timeWindow: { start: Date; end: Date }): Promise<{
    component: string;
    totalErrors: number;
    patterns: ErrorPattern[];
    recommendations: string[];
    healthScore: number;
    trends: any;
  }> {
    const patterns = this.getErrorPatterns({ component, timeWindow });
    const totalErrors = patterns.reduce((sum, p) => sum + p.frequency, 0);

    const healthScore = this.calculateComponentHealthScore(component, patterns);
    const recommendations = await this.generateComponentRecommendations(component, patterns);
    const trends = this.analyzeComponentTrends(component, patterns);

    return {
      component,
      totalErrors,
      patterns,
      recommendations,
      healthScore,
      trends
    };
  }

  private extractErrorPattern(logEntry: LogEntry): string {
    // Extract meaningful pattern from error message
    let message = logEntry.message;

    // Remove timestamps, IDs, and other variable data
    message = message.replace(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/g, 'TIMESTAMP');
    message = message.replace(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/gi, 'UUID');
    message = message.replace(/\b\d+\b/g, 'NUMBER');
    message = message.replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, 'EMAIL');
    message = message.replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, 'IPADDR');

    // Normalize whitespace
    message = message.replace(/\s+/g, ' ').trim();

    // Generate hash of normalized message + component
    return crypto
      .createHash('sha256')
      .update(message + '|' + logEntry.sourceComponent)
      .digest('hex')
      .substring(0, 16);
  }

  private async categorizeError(logEntry: LogEntry): Promise<ErrorCategory> {
    const message = logEntry.message.toLowerCase();
    const metadata = logEntry.metadata;

    // Use ML model for classification
    const mlCategory = await this.mlModel.categorizeError(logEntry);
    if (mlCategory) return mlCategory;

    // Fallback to rule-based classification
    if (message.includes('auth') || message.includes('login') || message.includes('credential')) {
      return ErrorCategory.AUTHENTICATION_FAILURE;
    }
    if (message.includes('permission') || message.includes('access') || message.includes('forbidden')) {
      return ErrorCategory.AUTHORIZATION_DENIED;
    }
    if (message.includes('validation') || message.includes('invalid') || message.includes('format')) {
      return ErrorCategory.VALIDATION_ERROR;
    }
    if (message.includes('database') || message.includes('sql') || message.includes('query')) {
      return ErrorCategory.DATABASE_ERROR;
    }
    if (message.includes('network') || message.includes('timeout') || message.includes('connection')) {
      return ErrorCategory.NETWORK_ERROR;
    }
    if (message.includes('external') || message.includes('api') || message.includes('service')) {
      return ErrorCategory.EXTERNAL_SERVICE_ERROR;
    }
    if (message.includes('performance') || message.includes('slow') || message.includes('latency')) {
      return ErrorCategory.PERFORMANCE_DEGRADATION;
    }
    if (message.includes('security') || message.includes('threat') || message.includes('attack')) {
      return ErrorCategory.SECURITY_THREAT;
    }
    if (message.includes('compliance') || message.includes('regulation') || message.includes('policy')) {
      return ErrorCategory.COMPLIANCE_VIOLATION;
    }

    return ErrorCategory.SYSTEM_ERROR;
  }

  private async calculateSeverity(logEntry: LogEntry): Promise<ErrorSeverity> {
    let severity = ErrorSeverity.LOW;

    // Base severity on log level
    switch (logEntry.level) {
      case 'CRITICAL':
        severity = ErrorSeverity.CATASTROPHIC;
        break;
      case 'ERROR':
        severity = ErrorSeverity.HIGH;
        break;
      case 'WARNING':
        severity = ErrorSeverity.MEDIUM;
        break;
      default:
        severity = ErrorSeverity.LOW;
    }

    // Adjust based on impact indicators
    const message = logEntry.message.toLowerCase();
    if (message.includes('critical') || message.includes('fatal') || message.includes('crash')) {
      severity = Math.max(severity, ErrorSeverity.CATASTROPHIC);
    }
    if (message.includes('security') || message.includes('breach') || message.includes('compromise')) {
      severity = Math.max(severity, ErrorSeverity.CRITICAL);
    }
    if (message.includes('data') && (message.includes('loss') || message.includes('corruption'))) {
      severity = Math.max(severity, ErrorSeverity.CRITICAL);
    }

    // Consider business impact
    const businessImpact = logEntry.metadata.businessImpact;
    if (businessImpact) {
      if (businessImpact.usersAffected > 1000) severity = Math.max(severity, ErrorSeverity.HIGH);
      if (businessImpact.revenueImpact > 10000) severity = Math.max(severity, ErrorSeverity.CRITICAL);
      if (businessImpact.complianceRisk) severity = Math.max(severity, ErrorSeverity.HIGH);
    }

    return severity;
  }

  private async assessBusinessImpact(logEntry: LogEntry): Promise<BusinessImpact> {
    const metadata = logEntry.metadata;
    const message = logEntry.message.toLowerCase();

    return {
      usersAffected: metadata.usersAffected || 0,
      revenueImpact: metadata.revenueImpact || 0,
      reputationRisk: this.assessReputationRisk(message, metadata),
      complianceRisk: this.assessComplianceRisk(message, metadata),
      slaViolation: this.checkSLAViolation(logEntry)
    };
  }

  private assessReputationRisk(message: string, metadata: any): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (message.includes('security') || message.includes('breach') || message.includes('leak')) {
      return 'CRITICAL';
    }
    if (message.includes('downtime') || message.includes('outage')) {
      return 'HIGH';
    }
    if (message.includes('performance') || message.includes('slow')) {
      return 'MEDIUM';
    }
    return 'LOW';
  }

  private assessComplianceRisk(message: string, metadata: any): boolean {
    const complianceKeywords = [
      'gdpr', 'pii', 'personal', 'data protection', 'privacy',
      'audit', 'regulation', 'compliance', 'policy violation'
    ];

    return complianceKeywords.some(keyword => message.includes(keyword));
  }

  private checkSLAViolation(logEntry: LogEntry): boolean {
    // Check response time thresholds
    const responseTime = logEntry.metadata.responseTime;
    if (responseTime && responseTime > 5000) return true; // 5 second threshold

    // Check error rate thresholds
    const errorRate = logEntry.metadata.errorRate;
    if (errorRate && errorRate > 0.05) return true; // 5% error rate

    return false;
  }

  private async performRootCauseAnalysis(logEntry: LogEntry, errorDNA: ErrorDNA): Promise<RootCauseAnalysis> {
    // Gather related events and timeline
    const timeline = await this.buildErrorTimeline(errorDNA.pattern, logEntry.timestamp);
    const affectedSystems = await this.identifyAffectedSystems(logEntry);

    // Analyze primary cause using ML and rules
    const primaryCause = await this.identifyPrimaryCause(logEntry, timeline);
    const contributingFactors = await this.identifyContributingFactors(logEntry, timeline);

    return {
      primaryCause,
      contributingFactors,
      timeline,
      affectedSystems,
      dataLoss: this.checkDataLoss(logEntry),
      securityImpact: this.checkSecurityImpact(logEntry)
    };
  }

  private async generateResolutionSteps(errorDNA: ErrorDNA): Promise<string[]> {
    const steps: string[] = [];

    switch (errorDNA.category) {
      case ErrorCategory.AUTHENTICATION_FAILURE:
        steps.push('Verify user credentials and account status');
        steps.push('Check authentication service availability');
        steps.push('Review recent security policy changes');
        break;

      case ErrorCategory.DATABASE_ERROR:
        steps.push('Check database connectivity and status');
        steps.push('Review recent schema changes');
        steps.push('Analyze query performance and optimization');
        break;

      case ErrorCategory.NETWORK_ERROR:
        steps.push('Verify network connectivity between services');
        steps.push('Check firewall and security group configurations');
        steps.push('Review DNS resolution and routing');
        break;

      case ErrorCategory.PERFORMANCE_DEGRADATION:
        steps.push('Analyze system resource utilization');
        steps.push('Review recent code deployments');
        steps.push('Check database query performance');
        steps.push('Verify external service dependencies');
        break;

      default:
        steps.push('Review error logs and stack traces');
        steps.push('Check system health and resource availability');
        steps.push('Verify recent configuration changes');
    }

    return steps;
  }

  private async generatePreventionStrategy(errorDNA: ErrorDNA): Promise<string> {
    const strategies: string[] = [];

    if (errorDNA.frequency > 10) {
      strategies.push('Implement automated monitoring and alerting');
    }

    if (errorDNA.severity >= ErrorSeverity.HIGH) {
      strategies.push('Add circuit breaker pattern');
      strategies.push('Implement graceful degradation');
    }

    if (errorDNA.category === ErrorCategory.VALIDATION_ERROR) {
      strategies.push('Enhance input validation and sanitization');
    }

    if (errorDNA.category === ErrorCategory.PERFORMANCE_DEGRADATION) {
      strategies.push('Implement caching and optimization');
      strategies.push('Add performance monitoring');
    }

    return strategies.join('; ');
  }

  private async updateErrorClusters(errorDNA: ErrorDNA, logEntry: LogEntry): Promise<void> {
    // Find existing cluster or create new one
    const clusterId = this.findOrCreateCluster(errorDNA, logEntry);
    const cluster = this.errorClusters.get(clusterId);

    if (cluster) {
      cluster.timeWindow.end = new Date(Math.max(cluster.timeWindow.end.getTime(), logEntry.timestamp.getTime()));

      if (!cluster.affectedSystems.includes(logEntry.sourceComponent)) {
        cluster.affectedSystems.push(logEntry.sourceComponent);
      }

      // Update severity to highest in cluster
      cluster.severity = Math.max(cluster.severity, errorDNA.severity);
    }
  }

  private findOrCreateCluster(errorDNA: ErrorDNA, logEntry: LogEntry): string {
    // Simple clustering by time window and component
    const timeWindow = 5 * 60 * 1000; // 5 minutes
    const component = logEntry.sourceComponent;

    for (const [clusterId, cluster] of this.errorClusters) {
      const timeDiff = Math.abs(logEntry.timestamp.getTime() - cluster.timeWindow.start.getTime());
      if (timeDiff <= timeWindow && cluster.affectedSystems.includes(component)) {
        return clusterId;
      }
    }

    // Create new cluster
    const clusterId = crypto.randomUUID();
    this.errorClusters.set(clusterId, {
      id: clusterId,
      patterns: [],
      affectedSystems: [component],
      timeWindow: { start: logEntry.timestamp, end: logEntry.timestamp },
      severity: errorDNA.severity
    });

    return clusterId;
  }

  private shouldTriggerAlert(errorDNA: ErrorDNA): boolean {
    // Alert on critical severity
    if (errorDNA.severity >= ErrorSeverity.CRITICAL) return true;

    // Alert on high frequency
    if (errorDNA.frequency > 5) return true;

    // Alert on security threats
    if (errorDNA.category === ErrorCategory.SECURITY_THREAT) return true;

    // Alert on compliance violations
    if (errorDNA.category === ErrorCategory.COMPLIANCE_VIOLATION) return true;

    return false;
  }

  private determineAlertType(errorDNA: ErrorDNA): string {
    if (errorDNA.category === ErrorCategory.SECURITY_THREAT) return 'SECURITY';
    if (errorDNA.severity >= ErrorSeverity.CRITICAL) return 'CRITICAL';
    if (errorDNA.frequency > 10) return 'FREQUENCY';
    return 'STANDARD';
  }

  private calculateUrgency(errorDNA: ErrorDNA): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (errorDNA.severity >= ErrorSeverity.CATASTROPHIC) return 'CRITICAL';
    if (errorDNA.severity >= ErrorSeverity.CRITICAL) return 'HIGH';
    if (errorDNA.frequency > 10) return 'HIGH';
    if (errorDNA.severity >= ErrorSeverity.HIGH) return 'MEDIUM';
    return 'LOW';
  }

  private calculateTrendDirection(patterns: ErrorPattern[], timeWindow: { start: Date; end: Date }): 'INCREASING' | 'DECREASING' | 'STABLE' {
    // Simplified trend calculation
    const midpoint = new Date((timeWindow.start.getTime() + timeWindow.end.getTime()) / 2);

    const firstHalf = patterns.filter(p => p.lastSeen <= midpoint).reduce((sum, p) => sum + p.frequency, 0);
    const secondHalf = patterns.filter(p => p.lastSeen > midpoint).reduce((sum, p) => sum + p.frequency, 0);

    const changePercent = firstHalf === 0 ? 100 : ((secondHalf - firstHalf) / firstHalf) * 100;

    if (changePercent > 20) return 'INCREASING';
    if (changePercent < -20) return 'DECREASING';
    return 'STABLE';
  }

  private calculateComponentHealthScore(component: string, patterns: ErrorPattern[]): number {
    // Simple health score calculation (0-100)
    const totalErrors = patterns.reduce((sum, p) => sum + p.frequency, 0);
    const unresolvedErrors = patterns.filter(p => !p.resolved).length;

    let score = 100;
    score -= Math.min(totalErrors * 2, 50); // Reduce by error count
    score -= unresolvedErrors * 10; // Reduce by unresolved patterns

    return Math.max(score, 0);
  }

  private async generateComponentRecommendations(component: string, patterns: ErrorPattern[]): Promise<string[]> {
    const recommendations: string[] = [];

    if (patterns.length > 5) {
      recommendations.push('Consider implementing better error handling');
    }

    const unresolvedCount = patterns.filter(p => !p.resolved).length;
    if (unresolvedCount > 2) {
      recommendations.push('Address unresolved error patterns');
    }

    return recommendations;
  }

  private analyzeComponentTrends(component: string, patterns: ErrorPattern[]): any {
    // Simplified trend analysis
    return {
      totalPatterns: patterns.length,
      resolvedPatterns: patterns.filter(p => p.resolved).length,
      averageFrequency: patterns.reduce((sum, p) => sum + p.frequency, 0) / patterns.length || 0
    };
  }

  private startProcessing(): void {
    this.processingInterval = setInterval(async () => {
      if (this.analysisQueue.length > 0) {
        const logEntry = this.analysisQueue.shift();
        if (logEntry) {
          await this.analyzeError(logEntry);
        }
      }
    }, 1000); // Process every second
  }

  // Helper methods (simplified implementations)
  private async findSimilarErrors(pattern: string): Promise<string[]> {
    return []; // ML-based similarity search
  }

  private async buildErrorTimeline(pattern: string, timestamp: Date): Promise<TimelineEvent[]> {
    return []; // Build timeline of related events
  }

  private async identifyAffectedSystems(logEntry: LogEntry): Promise<string[]> {
    return [logEntry.sourceComponent]; // Identify dependent systems
  }

  private async identifyPrimaryCause(logEntry: LogEntry, timeline: TimelineEvent[]): Promise<string> {
    return 'Root cause analysis in progress';
  }

  private async identifyContributingFactors(logEntry: LogEntry, timeline: TimelineEvent[]): Promise<string[]> {
    return ['Contributing factor analysis in progress'];
  }

  private checkDataLoss(logEntry: LogEntry): boolean {
    return logEntry.message.toLowerCase().includes('data loss') ||
           logEntry.message.toLowerCase().includes('corruption');
  }

  private checkSecurityImpact(logEntry: LogEntry): boolean {
    return logEntry.category === 'SECURITY' ||
           logEntry.message.toLowerCase().includes('security');
  }

  shutdown(): void {
    if (this.processingInterval) {
      clearInterval(this.processingInterval);
    }
  }
}

// Placeholder ML Model for Error Classification
class ErrorMLModel {
  async categorizeError(logEntry: LogEntry): Promise<ErrorCategory | null> {
    // In a real implementation, this would use trained ML models
    // for intelligent error categorization
    return null;
  }
}