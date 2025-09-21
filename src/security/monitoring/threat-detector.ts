/**
 * Security Monitoring and Threat Detection System
 * Real-time threat detection with behavioral analysis and automated response
 */

import { EventEmitter } from 'events';
import crypto from 'crypto';
import {
  ThreatEvent,
  ThreatType,
  ThreatSeverity,
  ThreatSource,
  ThreatIndicator,
  MitigationAction,
  Geolocation,
  MonitoringConfig,
  LogEntry,
  SecurityContext
} from '../types';

interface BehaviorProfile {
  userId: string;
  baselineMetrics: {
    averageSessionDuration: number;
    typicalLoginTimes: number[];
    commonLocations: Geolocation[];
    normalApiUsage: Record<string, number>;
    deviceFingerprints: string[];
  };
  currentMetrics: {
    sessionDuration: number;
    loginTime: number;
    location?: Geolocation;
    apiUsage: Record<string, number>;
    deviceFingerprint: string;
  };
  anomalyScore: number;
  lastUpdated: Date;
}

interface AttackPattern {
  id: string;
  name: string;
  indicators: ThreatIndicator[];
  threshold: number;
  timeWindow: number; // minutes
  severity: ThreatSeverity;
  automaticMitigation: boolean;
}

interface ThreatIntelligence {
  maliciousIps: Set<string>;
  knownAttackers: Set<string>;
  compromisedCredentials: Set<string>;
  botSignatures: Set<string>;
  lastUpdated: Date;
}

export class ThreatDetector extends EventEmitter {
  private config: MonitoringConfig;
  private behaviorProfiles: Map<string, BehaviorProfile> = new Map();
  private attackPatterns: Map<string, AttackPattern> = new Map();
  private threatIntelligence: ThreatIntelligence;
  private activeThreats: Map<string, ThreatEvent> = new Map();
  private ipRateLimit: Map<string, { count: number; lastReset: Date }> = new Map();
  private userRateLimit: Map<string, { count: number; lastReset: Date }> = new Map();
  private mlModel: ThreatMLModel;

  constructor(config: MonitoringConfig) {
    super();
    this.config = config;
    this.mlModel = new ThreatMLModel();
    this.threatIntelligence = {
      maliciousIps: new Set(),
      knownAttackers: new Set(),
      compromisedCredentials: new Set(),
      botSignatures: new Set(),
      lastUpdated: new Date()
    };

    this.initializeAttackPatterns();
    this.startThreatIntelligenceUpdates();
    this.startPeriodicAnalysis();
  }

  /**
   * Analyze log entry for security threats
   */
  async analyzeLogEntry(logEntry: LogEntry): Promise<ThreatEvent[]> {
    const threats: ThreatEvent[] = [];

    // Check for immediate threat indicators
    const immediateThreats = await this.detectImmediateThreats(logEntry);
    threats.push(...immediateThreats);

    // Behavioral analysis for authenticated users
    if (logEntry.userId) {
      const behaviorThreats = await this.analyzeBehavior(logEntry);
      threats.push(...behaviorThreats);
    }

    // Pattern-based detection
    const patternThreats = await this.detectAttackPatterns(logEntry);
    threats.push(...patternThreats);

    // ML-based anomaly detection
    if (this.config.mlModelsEnabled) {
      const mlThreats = await this.mlModel.detectAnomalies(logEntry);
      threats.push(...mlThreats);
    }

    // Process detected threats
    for (const threat of threats) {
      await this.processThreat(threat);
    }

    return threats;
  }

  /**
   * Analyze security context for threats
   */
  async analyzeSecurityContext(context: SecurityContext): Promise<ThreatEvent[]> {
    const threats: ThreatEvent[] = [];

    // Check IP reputation
    const ipThreat = await this.checkIpReputation(context);
    if (ipThreat) threats.push(ipThreat);

    // Check device fingerprint
    const deviceThreat = await this.checkDeviceFingerprint(context);
    if (deviceThreat) threats.push(deviceThreat);

    // Geolocation analysis
    const geoThreat = await this.analyzeGeolocation(context);
    if (geoThreat) threats.push(geoThreat);

    // Rate limiting checks
    const rateLimitThreat = await this.checkRateLimits(context);
    if (rateLimitThreat) threats.push(rateLimitThreat);

    return threats;
  }

  /**
   * Report suspicious activity manually
   */
  async reportSuspiciousActivity(
    description: string,
    source: ThreatSource,
    severity: ThreatSeverity,
    indicators: ThreatIndicator[] = []
  ): Promise<string> {
    const threat: ThreatEvent = {
      id: crypto.randomUUID(),
      timestamp: new Date(),
      type: ThreatType.SUSPICIOUS_BEHAVIOR,
      severity,
      source,
      target: 'manual_report',
      description,
      indicators,
      mitigationActions: [],
      resolved: false,
      falsePositive: false
    };

    await this.processThreat(threat);
    return threat.id;
  }

  /**
   * Get active threats
   */
  getActiveThreats(severity?: ThreatSeverity): ThreatEvent[] {
    const threats = Array.from(this.activeThreats.values())
      .filter(threat => !threat.resolved);

    if (severity) {
      return threats.filter(threat => threat.severity === severity);
    }

    return threats;
  }

  /**
   * Mark threat as resolved
   */
  resolveThreat(threatId: string, resolutionNotes?: string): boolean {
    const threat = this.activeThreats.get(threatId);
    if (threat) {
      threat.resolved = true;
      threat.mitigationActions.push({
        action: 'MANUAL_RESOLUTION',
        timestamp: new Date(),
        automated: false,
        effectiveness: 1.0,
        description: resolutionNotes || 'Manually resolved'
      });

      this.emit('threat:resolved', { threat, resolutionNotes });
      return true;
    }
    return false;
  }

  /**
   * Mark threat as false positive
   */
  markFalsePositive(threatId: string, reason?: string): boolean {
    const threat = this.activeThreats.get(threatId);
    if (threat) {
      threat.falsePositive = true;
      threat.resolved = true;

      // Update ML model with false positive feedback
      if (this.config.falsePositiveReduction) {
        this.mlModel.recordFalsePositive(threat, reason);
      }

      this.emit('threat:false_positive', { threat, reason });
      return true;
    }
    return false;
  }

  /**
   * Get threat statistics
   */
  getThreatStatistics(timeWindow?: { start: Date; end: Date }): {
    totalThreats: number;
    threatsBySeverity: Record<ThreatSeverity, number>;
    threatsByType: Record<ThreatType, number>;
    resolvedThreats: number;
    falsePositives: number;
    averageResolutionTime: number;
    topSources: Array<{ source: string; count: number }>;
  } {
    const threats = Array.from(this.activeThreats.values());
    let filteredThreats = threats;

    if (timeWindow) {
      filteredThreats = threats.filter(threat =>
        threat.timestamp >= timeWindow.start && threat.timestamp <= timeWindow.end
      );
    }

    const threatsBySeverity = filteredThreats.reduce((counts, threat) => {
      counts[threat.severity] = (counts[threat.severity] || 0) + 1;
      return counts;
    }, {} as Record<ThreatSeverity, number>);

    const threatsByType = filteredThreats.reduce((counts, threat) => {
      counts[threat.type] = (counts[threat.type] || 0) + 1;
      return counts;
    }, {} as Record<ThreatType, number>);

    const resolvedThreats = filteredThreats.filter(t => t.resolved).length;
    const falsePositives = filteredThreats.filter(t => t.falsePositive).length;

    // Calculate average resolution time
    const resolvedWithTime = filteredThreats.filter(t => t.resolved && t.mitigationActions.length > 0);
    const totalResolutionTime = resolvedWithTime.reduce((sum, threat) => {
      const firstAction = threat.mitigationActions[0];
      return sum + (firstAction.timestamp.getTime() - threat.timestamp.getTime());
    }, 0);
    const averageResolutionTime = resolvedWithTime.length > 0
      ? totalResolutionTime / resolvedWithTime.length
      : 0;

    // Top threat sources
    const sourceCounts = new Map<string, number>();
    filteredThreats.forEach(threat => {
      const sourceKey = threat.source.ip || threat.source.userId || 'unknown';
      sourceCounts.set(sourceKey, (sourceCounts.get(sourceKey) || 0) + 1);
    });

    const topSources = Array.from(sourceCounts.entries())
      .map(([source, count]) => ({ source, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      totalThreats: filteredThreats.length,
      threatsBySeverity,
      threatsByType,
      resolvedThreats,
      falsePositives,
      averageResolutionTime,
      topSources
    };
  }

  private async detectImmediateThreats(logEntry: LogEntry): Promise<ThreatEvent[]> {
    const threats: ThreatEvent[] = [];
    const message = logEntry.message.toLowerCase();

    // SQL Injection detection
    if (this.isSqlInjectionAttempt(message)) {
      threats.push(await this.createThreatEvent(
        ThreatType.SQL_INJECTION,
        ThreatSeverity.HIGH,
        logEntry,
        'SQL injection attempt detected',
        [{ type: 'pattern', value: 'sql_injection', confidence: 0.9, source: 'rule_engine' }]
      ));
    }

    // XSS detection
    if (this.isXssAttempt(message)) {
      threats.push(await this.createThreatEvent(
        ThreatType.XSS_ATTACK,
        ThreatSeverity.MEDIUM,
        logEntry,
        'Cross-site scripting attempt detected',
        [{ type: 'pattern', value: 'xss_attempt', confidence: 0.8, source: 'rule_engine' }]
      ));
    }

    // Brute force detection
    if (logEntry.category === 'AUTHENTICATION' && message.includes('failed')) {
      const bruteForceCheck = await this.checkBruteForce(logEntry);
      if (bruteForceCheck) {
        threats.push(bruteForceCheck);
      }
    }

    // Malicious IP check
    const ip = logEntry.metadata.ipAddress;
    if (ip && this.threatIntelligence.maliciousIps.has(ip)) {
      threats.push(await this.createThreatEvent(
        ThreatType.SUSPICIOUS_BEHAVIOR,
        ThreatSeverity.HIGH,
        logEntry,
        'Request from known malicious IP',
        [{ type: 'ip_reputation', value: ip, confidence: 1.0, source: 'threat_intelligence' }]
      ));
    }

    return threats;
  }

  private async analyzeBehavior(logEntry: LogEntry): Promise<ThreatEvent[]> {
    const threats: ThreatEvent[] = [];
    const userId = logEntry.userId!;

    // Get or create behavior profile
    let profile = this.behaviorProfiles.get(userId);
    if (!profile) {
      profile = await this.createBehaviorProfile(userId, logEntry);
      this.behaviorProfiles.set(userId, profile);
    }

    // Update current metrics
    this.updateCurrentMetrics(profile, logEntry);

    // Calculate anomaly score
    const anomalyScore = this.calculateAnomalyScore(profile);
    profile.anomalyScore = anomalyScore;

    // Check for behavioral anomalies
    if (anomalyScore > 0.7) {
      threats.push(await this.createThreatEvent(
        ThreatType.SUSPICIOUS_BEHAVIOR,
        this.severityFromAnomalyScore(anomalyScore),
        logEntry,
        `Behavioral anomaly detected (score: ${anomalyScore.toFixed(2)})`,
        [{ type: 'behavior_anomaly', value: anomalyScore.toString(), confidence: anomalyScore, source: 'behavior_analysis' }]
      ));
    }

    // Update baseline (gradual learning)
    this.updateBaseline(profile, logEntry);

    return threats;
  }

  private async detectAttackPatterns(logEntry: LogEntry): Promise<ThreatEvent[]> {
    const threats: ThreatEvent[] = [];

    for (const pattern of this.attackPatterns.values()) {
      const matchScore = this.calculatePatternMatch(pattern, logEntry);

      if (matchScore >= pattern.threshold) {
        threats.push(await this.createThreatEvent(
          ThreatType.SUSPICIOUS_BEHAVIOR,
          pattern.severity,
          logEntry,
          `Attack pattern detected: ${pattern.name}`,
          [{ type: 'attack_pattern', value: pattern.id, confidence: matchScore, source: 'pattern_engine' }]
        ));
      }
    }

    return threats;
  }

  private async processThreat(threat: ThreatEvent): Promise<void> {
    this.activeThreats.set(threat.id, threat);
    this.emit('threat:detected', threat);

    // Automatic mitigation if enabled
    if (this.config.automaticMitigation) {
      await this.automaticMitigation(threat);
    }

    // Real-time alerts for high severity threats
    if (this.config.realTimeAlerts && threat.severity >= ThreatSeverity.HIGH) {
      this.emit('threat:alert', {
        threat,
        alertType: 'REAL_TIME',
        urgency: this.calculateUrgency(threat)
      });
    }
  }

  private async automaticMitigation(threat: ThreatEvent): Promise<void> {
    const mitigationActions: MitigationAction[] = [];

    switch (threat.type) {
      case ThreatType.BRUTE_FORCE_ATTACK:
        // Block IP temporarily
        mitigationActions.push(await this.blockIpAddress(threat.source.ip, 3600)); // 1 hour
        break;

      case ThreatType.SQL_INJECTION:
      case ThreatType.XSS_ATTACK:
        // Block IP and alert security team
        mitigationActions.push(await this.blockIpAddress(threat.source.ip, 86400)); // 24 hours
        break;

      case ThreatType.SUSPICIOUS_BEHAVIOR:
        if (threat.severity >= ThreatSeverity.HIGH) {
          // Require additional authentication
          mitigationActions.push(await this.requireStepUpAuth(threat.source.userId));
        }
        break;

      case ThreatType.DDoS_ATTACK:
        // Implement rate limiting
        mitigationActions.push(await this.implementRateLimiting(threat.source.ip));
        break;
    }

    threat.mitigationActions.push(...mitigationActions);
  }

  private async createThreatEvent(
    type: ThreatType,
    severity: ThreatSeverity,
    logEntry: LogEntry,
    description: string,
    indicators: ThreatIndicator[]
  ): Promise<ThreatEvent> {
    const source: ThreatSource = {
      ip: logEntry.metadata.ipAddress || 'unknown',
      userId: logEntry.userId,
      userAgent: logEntry.metadata.userAgent,
      reputation: await this.calculateSourceReputation(logEntry.metadata.ipAddress),
      previousThreatHistory: await this.hasPreviousThreatHistory(logEntry.metadata.ipAddress)
    };

    if (logEntry.metadata.geolocation) {
      source.geolocation = logEntry.metadata.geolocation;
    }

    return {
      id: crypto.randomUUID(),
      timestamp: logEntry.timestamp,
      type,
      severity,
      source,
      target: logEntry.sourceComponent,
      description,
      indicators,
      mitigationActions: [],
      resolved: false,
      falsePositive: false
    };
  }

  private isSqlInjectionAttempt(message: string): boolean {
    const sqlPatterns = [
      /union\s+select/i,
      /1\s*=\s*1/i,
      /'\s*or\s*'1'\s*=\s*'1/i,
      /drop\s+table/i,
      /insert\s+into/i,
      /delete\s+from/i,
      /update\s+.*\s+set/i,
      /exec\s*\(/i
    ];

    return sqlPatterns.some(pattern => pattern.test(message));
  }

  private isXssAttempt(message: string): boolean {
    const xssPatterns = [
      /<script[^>]*>/i,
      /javascript:/i,
      /on\w+\s*=/i,
      /<iframe[^>]*>/i,
      /document\.cookie/i,
      /alert\s*\(/i,
      /<img[^>]*onerror/i
    ];

    return xssPatterns.some(pattern => pattern.test(message));
  }

  private async checkBruteForce(logEntry: LogEntry): Promise<ThreatEvent | null> {
    const ip = logEntry.metadata.ipAddress;
    if (!ip) return null;

    const key = `brute_force_${ip}`;
    const now = new Date();
    const windowMinutes = 15;

    // This would typically be stored in Redis or similar
    // For demo, using in-memory tracking
    const attempts = this.getAttemptCount(key, windowMinutes);

    if (attempts > 10) { // More than 10 failed attempts in 15 minutes
      return await this.createThreatEvent(
        ThreatType.BRUTE_FORCE_ATTACK,
        ThreatSeverity.HIGH,
        logEntry,
        `Brute force attack detected: ${attempts} failed attempts`,
        [{ type: 'attempt_count', value: attempts.toString(), confidence: 0.9, source: 'rate_limiter' }]
      );
    }

    return null;
  }

  private async createBehaviorProfile(userId: string, logEntry: LogEntry): Promise<BehaviorProfile> {
    return {
      userId,
      baselineMetrics: {
        averageSessionDuration: 1800, // 30 minutes default
        typicalLoginTimes: [9, 17], // 9 AM to 5 PM default
        commonLocations: [],
        normalApiUsage: {},
        deviceFingerprints: []
      },
      currentMetrics: {
        sessionDuration: 0,
        loginTime: logEntry.timestamp.getHours(),
        apiUsage: {},
        deviceFingerprint: logEntry.metadata.deviceFingerprint || 'unknown'
      },
      anomalyScore: 0,
      lastUpdated: new Date()
    };
  }

  private updateCurrentMetrics(profile: BehaviorProfile, logEntry: LogEntry): void {
    profile.currentMetrics.loginTime = logEntry.timestamp.getHours();

    if (logEntry.metadata.deviceFingerprint) {
      profile.currentMetrics.deviceFingerprint = logEntry.metadata.deviceFingerprint;
    }

    // Update API usage patterns
    const endpoint = logEntry.metadata.endpoint || 'unknown';
    profile.currentMetrics.apiUsage[endpoint] = (profile.currentMetrics.apiUsage[endpoint] || 0) + 1;

    profile.lastUpdated = new Date();
  }

  private calculateAnomalyScore(profile: BehaviorProfile): number {
    let anomalyScore = 0;

    // Time-based anomaly (outside normal hours)
    const currentHour = profile.currentMetrics.loginTime;
    const isNormalHour = profile.baselineMetrics.typicalLoginTimes.some(hour =>
      Math.abs(currentHour - hour) <= 1
    );
    if (!isNormalHour) anomalyScore += 0.3;

    // Device fingerprint anomaly
    if (!profile.baselineMetrics.deviceFingerprints.includes(profile.currentMetrics.deviceFingerprint)) {
      anomalyScore += 0.4;
    }

    // API usage pattern anomaly
    const currentApiUsage = Object.keys(profile.currentMetrics.apiUsage).length;
    const normalApiUsage = Object.keys(profile.baselineMetrics.normalApiUsage).length;
    if (currentApiUsage > normalApiUsage * 2) {
      anomalyScore += 0.3;
    }

    return Math.min(anomalyScore, 1.0);
  }

  private severityFromAnomalyScore(score: number): ThreatSeverity {
    if (score >= 0.9) return ThreatSeverity.CRITICAL;
    if (score >= 0.7) return ThreatSeverity.HIGH;
    if (score >= 0.5) return ThreatSeverity.MEDIUM;
    return ThreatSeverity.LOW;
  }

  private updateBaseline(profile: BehaviorProfile, logEntry: LogEntry): void {
    // Gradual learning - update baseline with current behavior
    const learningRate = 0.1;

    // Update typical login times
    const currentHour = logEntry.timestamp.getHours();
    if (!profile.baselineMetrics.typicalLoginTimes.includes(currentHour)) {
      profile.baselineMetrics.typicalLoginTimes.push(currentHour);
    }

    // Update device fingerprints
    const fingerprint = logEntry.metadata.deviceFingerprint;
    if (fingerprint && !profile.baselineMetrics.deviceFingerprints.includes(fingerprint)) {
      profile.baselineMetrics.deviceFingerprints.push(fingerprint);
    }

    // Update API usage patterns
    for (const [endpoint, count] of Object.entries(profile.currentMetrics.apiUsage)) {
      const baselineCount = profile.baselineMetrics.normalApiUsage[endpoint] || 0;
      profile.baselineMetrics.normalApiUsage[endpoint] =
        baselineCount + (count - baselineCount) * learningRate;
    }
  }

  private calculatePatternMatch(pattern: AttackPattern, logEntry: LogEntry): number {
    let matchScore = 0;
    const totalIndicators = pattern.indicators.length;

    for (const indicator of pattern.indicators) {
      if (this.matchesIndicator(indicator, logEntry)) {
        matchScore += indicator.confidence;
      }
    }

    return totalIndicators > 0 ? matchScore / totalIndicators : 0;
  }

  private matchesIndicator(indicator: ThreatIndicator, logEntry: LogEntry): boolean {
    switch (indicator.type) {
      case 'ip_pattern':
        return logEntry.metadata.ipAddress === indicator.value;
      case 'user_agent_pattern':
        return logEntry.metadata.userAgent?.includes(indicator.value) || false;
      case 'message_pattern':
        return logEntry.message.toLowerCase().includes(indicator.value.toLowerCase());
      case 'endpoint_pattern':
        return logEntry.metadata.endpoint?.includes(indicator.value) || false;
      default:
        return false;
    }
  }

  private async checkIpReputation(context: SecurityContext): Promise<ThreatEvent | null> {
    // Implementation would check against threat intelligence feeds
    return null;
  }

  private async checkDeviceFingerprint(context: SecurityContext): Promise<ThreatEvent | null> {
    // Check if device fingerprint is known or suspicious
    return null;
  }

  private async analyzeGeolocation(context: SecurityContext): Promise<ThreatEvent | null> {
    // Analyze if location is consistent with user's normal behavior
    return null;
  }

  private async checkRateLimits(context: SecurityContext): Promise<ThreatEvent | null> {
    // Check API rate limits and suspicious activity patterns
    return null;
  }

  private async calculateSourceReputation(ip?: string): Promise<number> {
    if (!ip) return 0.5;

    // Check threat intelligence
    if (this.threatIntelligence.maliciousIps.has(ip)) return 0.1;

    // Default neutral reputation
    return 0.5;
  }

  private async hasPreviousThreatHistory(ip?: string): Promise<boolean> {
    if (!ip) return false;

    return Array.from(this.activeThreats.values())
      .some(threat => threat.source.ip === ip);
  }

  private calculateUrgency(threat: ThreatEvent): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
    if (threat.severity >= ThreatSeverity.CRITICAL) return 'CRITICAL';
    if (threat.severity >= ThreatSeverity.HIGH) return 'HIGH';
    if (threat.severity >= ThreatSeverity.MEDIUM) return 'MEDIUM';
    return 'LOW';
  }

  private getAttemptCount(key: string, windowMinutes: number): number {
    // Simplified implementation - in production would use Redis
    return Math.floor(Math.random() * 15); // Mock data
  }

  private async blockIpAddress(ip: string, durationSeconds: number): Promise<MitigationAction> {
    // Implementation would add IP to firewall/WAF block list
    return {
      action: `BLOCK_IP`,
      timestamp: new Date(),
      automated: true,
      effectiveness: 0.9,
      description: `Blocked IP ${ip} for ${durationSeconds} seconds`
    };
  }

  private async requireStepUpAuth(userId?: string): Promise<MitigationAction> {
    // Implementation would trigger additional authentication requirements
    return {
      action: 'REQUIRE_STEP_UP_AUTH',
      timestamp: new Date(),
      automated: true,
      effectiveness: 0.8,
      description: `Required step-up authentication for user ${userId || 'unknown'}`
    };
  }

  private async implementRateLimiting(ip: string): Promise<MitigationAction> {
    // Implementation would configure rate limiting rules
    return {
      action: 'RATE_LIMIT',
      timestamp: new Date(),
      automated: true,
      effectiveness: 0.7,
      description: `Implemented rate limiting for IP ${ip}`
    };
  }

  private initializeAttackPatterns(): void {
    // Initialize common attack patterns
    const patterns: AttackPattern[] = [
      {
        id: 'sql_injection_pattern',
        name: 'SQL Injection Pattern',
        indicators: [
          { type: 'message_pattern', value: 'union select', confidence: 0.9, source: 'rule_engine' },
          { type: 'message_pattern', value: "1=1", confidence: 0.8, source: 'rule_engine' }
        ],
        threshold: 0.7,
        timeWindow: 5,
        severity: ThreatSeverity.HIGH,
        automaticMitigation: true
      },
      {
        id: 'brute_force_pattern',
        name: 'Brute Force Pattern',
        indicators: [
          { type: 'message_pattern', value: 'authentication failed', confidence: 0.7, source: 'rule_engine' }
        ],
        threshold: 0.6,
        timeWindow: 15,
        severity: ThreatSeverity.MEDIUM,
        automaticMitigation: true
      }
    ];

    for (const pattern of patterns) {
      this.attackPatterns.set(pattern.id, pattern);
    }
  }

  private startThreatIntelligenceUpdates(): void {
    // Update threat intelligence every hour
    setInterval(async () => {
      await this.updateThreatIntelligence();
    }, 60 * 60 * 1000);
  }

  private async updateThreatIntelligence(): Promise<void> {
    // In production, this would fetch from threat intelligence feeds
    this.threatIntelligence.lastUpdated = new Date();
    this.emit('threat_intelligence:updated');
  }

  private startPeriodicAnalysis(): void {
    // Run periodic analysis every 5 minutes
    setInterval(async () => {
      await this.performPeriodicAnalysis();
    }, 5 * 60 * 1000);
  }

  private async performPeriodicAnalysis(): Promise<void> {
    // Analyze trends, update baselines, cleanup old data
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    // Clean up old resolved threats
    for (const [id, threat] of this.activeThreats) {
      if (threat.resolved && threat.timestamp < oneDayAgo) {
        this.activeThreats.delete(id);
      }
    }

    this.emit('analysis:periodic_complete');
  }

  shutdown(): void {
    this.emit('threat_detector:shutdown');
  }
}

// Placeholder ML Model for Threat Detection
class ThreatMLModel {
  async detectAnomalies(logEntry: LogEntry): Promise<ThreatEvent[]> {
    // In a real implementation, this would use trained ML models
    // for advanced threat detection
    return [];
  }

  recordFalsePositive(threat: ThreatEvent, reason?: string): void {
    // Record false positive for model improvement
  }
}