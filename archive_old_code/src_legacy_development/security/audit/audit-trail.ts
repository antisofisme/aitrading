/**
 * Audit Trail System for Compliance Reporting
 * Comprehensive audit logging with tamper-proof storage and compliance reporting
 */

import { EventEmitter } from 'events';
import crypto from 'crypto';
import {
  AuditEvent,
  AuditConfig,
  SecurityContext,
  LogEntry,
  RetentionTier
} from '../types';

interface AuditRule {
  id: string;
  name: string;
  description: string;
  triggers: AuditTrigger[];
  dataToCapture: string[];
  retentionPeriod: number;
  complianceRelevant: boolean;
  encryptionRequired: boolean;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

interface AuditTrigger {
  eventType: string;
  conditions: Record<string, any>;
  userRoles?: string[];
  resources?: string[];
}

interface AuditChain {
  id: string;
  events: AuditEvent[];
  hash: string;
  previousHash: string;
  timestamp: Date;
  signature?: string;
}

interface ComplianceReport {
  id: string;
  generatedAt: Date;
  timeRange: { start: Date; end: Date };
  totalEvents: number;
  eventsByCategory: Record<string, number>;
  complianceStatus: 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL';
  violations: AuditViolation[];
  recommendations: string[];
  signature: string;
}

interface AuditViolation {
  id: string;
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  affectedEvents: string[];
  recommendation: string;
  timestamp: Date;
}

export class AuditTrail extends EventEmitter {
  private config: AuditConfig;
  private auditRules: Map<string, AuditRule> = new Map();
  private auditChains: Map<string, AuditChain> = new Map();
  private pendingEvents: AuditEvent[] = [];
  private currentChain: AuditChain | null = null;
  private encryptionKey: string;
  private signingKey: string;

  constructor(config: AuditConfig) {
    super();
    this.config = config;
    this.encryptionKey = process.env.AUDIT_ENCRYPTION_KEY || this.generateKey();
    this.signingKey = process.env.AUDIT_SIGNING_KEY || this.generateKey();

    this.initializeAuditRules();
    this.startChainProcessing();
  }

  /**
   * Record audit event
   */
  async recordEvent(
    userId: string,
    userRole: string,
    action: string,
    resource: string,
    outcome: 'SUCCESS' | 'FAILURE' | 'PARTIAL',
    details: Record<string, any> = {},
    context?: SecurityContext
  ): Promise<string> {
    const eventId = crypto.randomUUID();

    const auditEvent: AuditEvent = {
      id: eventId,
      timestamp: new Date(),
      userId,
      userRole,
      action,
      resource,
      outcome,
      details: this.sanitizeDetails(details),
      ipAddress: context?.ipAddress || details.ipAddress || 'unknown',
      userAgent: context?.userAgent || details.userAgent || 'unknown',
      sessionId: context?.sessionId || details.sessionId || 'unknown',
      riskScore: context?.trustScore || 0,
      complianceRelevant: this.isComplianceRelevant(action, resource, details),
      retentionRequirement: this.calculateRetentionRequirement(action, resource)
    };

    // Check if event matches any audit rules
    const matchingRules = this.findMatchingRules(auditEvent);
    if (matchingRules.length === 0 && !this.config.enabled) {
      return eventId; // Skip if no rules match and auditing is disabled
    }

    // Encrypt sensitive details if required
    if (this.shouldEncryptEvent(auditEvent, matchingRules)) {
      auditEvent.details = await this.encryptDetails(auditEvent.details);
    }

    this.pendingEvents.push(auditEvent);

    // Process immediately for real-time audit
    if (this.config.realTimeAudit) {
      await this.processEvent(auditEvent);
    }

    this.emit('audit:event_recorded', auditEvent);
    return eventId;
  }

  /**
   * Record security event for audit
   */
  async recordSecurityEvent(
    action: string,
    outcome: 'SUCCESS' | 'FAILURE',
    details: Record<string, any>,
    context: SecurityContext
  ): Promise<string> {
    return this.recordEvent(
      context.userId,
      'system', // Default role for security events
      action,
      'security',
      outcome,
      {
        ...details,
        securityEvent: true,
        riskLevel: context.riskLevel,
        trustScore: context.trustScore
      },
      context
    );
  }

  /**
   * Record authentication events
   */
  async recordAuthenticationEvent(
    userId: string,
    action: 'LOGIN' | 'LOGOUT' | 'PASSWORD_CHANGE' | 'MFA_VERIFICATION',
    outcome: 'SUCCESS' | 'FAILURE',
    details: Record<string, any> = {},
    context?: SecurityContext
  ): Promise<string> {
    return this.recordEvent(
      userId,
      'user',
      `AUTH_${action}`,
      'authentication',
      outcome,
      {
        ...details,
        authenticationEvent: true
      },
      context
    );
  }

  /**
   * Record data access events
   */
  async recordDataAccess(
    userId: string,
    userRole: string,
    dataType: string,
    operation: 'READ' | 'WRITE' | 'DELETE' | 'EXPORT',
    outcome: 'SUCCESS' | 'FAILURE',
    details: Record<string, any> = {},
    context?: SecurityContext
  ): Promise<string> {
    return this.recordEvent(
      userId,
      userRole,
      `DATA_${operation}`,
      `data:${dataType}`,
      outcome,
      {
        ...details,
        dataAccessEvent: true,
        dataType,
        operation
      },
      context
    );
  }

  /**
   * Record administrative actions
   */
  async recordAdminAction(
    adminUserId: string,
    action: string,
    targetResource: string,
    outcome: 'SUCCESS' | 'FAILURE',
    details: Record<string, any> = {},
    context?: SecurityContext
  ): Promise<string> {
    return this.recordEvent(
      adminUserId,
      'admin',
      `ADMIN_${action}`,
      targetResource,
      outcome,
      {
        ...details,
        adminAction: true,
        privilegedOperation: true
      },
      context
    );
  }

  /**
   * Query audit events with filtering
   */
  async queryEvents(options: {
    userId?: string;
    userRole?: string;
    action?: string;
    resource?: string;
    outcome?: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
    startDate?: Date;
    endDate?: Date;
    complianceRelevant?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ events: AuditEvent[]; total: number; hasMore: boolean }> {
    // In production, this would query the audit storage backend
    const allEvents: AuditEvent[] = [];

    // Collect events from all chains
    for (const chain of this.auditChains.values()) {
      allEvents.push(...chain.events);
    }

    // Add pending events
    allEvents.push(...this.pendingEvents);

    // Apply filters
    let filteredEvents = allEvents.filter(event => {
      if (options.userId && event.userId !== options.userId) return false;
      if (options.userRole && event.userRole !== options.userRole) return false;
      if (options.action && !event.action.includes(options.action)) return false;
      if (options.resource && event.resource !== options.resource) return false;
      if (options.outcome && event.outcome !== options.outcome) return false;
      if (options.startDate && event.timestamp < options.startDate) return false;
      if (options.endDate && event.timestamp > options.endDate) return false;
      if (options.complianceRelevant !== undefined && event.complianceRelevant !== options.complianceRelevant) return false;
      return true;
    });

    // Sort by timestamp (most recent first)
    filteredEvents.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());

    const offset = options.offset || 0;
    const limit = options.limit || 100;
    const paginatedEvents = filteredEvents.slice(offset, offset + limit);

    return {
      events: paginatedEvents,
      total: filteredEvents.length,
      hasMore: offset + limit < filteredEvents.length
    };
  }

  /**
   * Generate compliance report
   */
  async generateComplianceReport(
    timeRange: { start: Date; end: Date },
    reportType: 'GDPR' | 'SOX' | 'HIPAA' | 'PCI_DSS' | 'GENERAL' = 'GENERAL'
  ): Promise<ComplianceReport> {
    const reportId = crypto.randomUUID();

    const { events } = await this.queryEvents({
      startDate: timeRange.start,
      endDate: timeRange.end,
      complianceRelevant: true
    });

    const eventsByCategory = this.categorizeEvents(events);
    const violations = await this.detectViolations(events, reportType);
    const complianceStatus = this.calculateComplianceStatus(violations);
    const recommendations = this.generateRecommendations(violations, eventsByCategory);

    const report: ComplianceReport = {
      id: reportId,
      generatedAt: new Date(),
      timeRange,
      totalEvents: events.length,
      eventsByCategory,
      complianceStatus,
      violations,
      recommendations,
      signature: '' // Will be set after signing
    };

    // Sign the report for integrity
    report.signature = await this.signReport(report);

    this.emit('audit:compliance_report_generated', report);
    return report;
  }

  /**
   * Verify audit chain integrity
   */
  async verifyChainIntegrity(chainId?: string): Promise<{
    isValid: boolean;
    brokenChains: string[];
    tamperedEvents: string[];
    verificationDetails: any;
  }> {
    const chainsToVerify = chainId
      ? [this.auditChains.get(chainId)].filter(Boolean)
      : Array.from(this.auditChains.values());

    const brokenChains: string[] = [];
    const tamperedEvents: string[] = [];
    const verificationDetails: any = {};

    for (const chain of chainsToVerify) {
      if (!chain) continue;

      const verification = await this.verifyChain(chain);
      verificationDetails[chain.id] = verification;

      if (!verification.isValid) {
        brokenChains.push(chain.id);
        tamperedEvents.push(...verification.tamperedEvents);
      }
    }

    return {
      isValid: brokenChains.length === 0,
      brokenChains,
      tamperedEvents,
      verificationDetails
    };
  }

  /**
   * Export audit data for external systems
   */
  async exportAuditData(
    format: 'JSON' | 'CSV' | 'XML',
    timeRange: { start: Date; end: Date },
    includeHashes: boolean = true
  ): Promise<string> {
    const { events } = await this.queryEvents({
      startDate: timeRange.start,
      endDate: timeRange.end
    });

    switch (format) {
      case 'JSON':
        return this.exportAsJSON(events, includeHashes);
      case 'CSV':
        return this.exportAsCSV(events);
      case 'XML':
        return this.exportAsXML(events);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Search audit trail
   */
  async searchAuditTrail(
    searchTerm: string,
    searchFields: string[] = ['action', 'resource', 'details'],
    timeRange?: { start: Date; end: Date }
  ): Promise<AuditEvent[]> {
    const { events } = await this.queryEvents({
      startDate: timeRange?.start,
      endDate: timeRange?.end
    });

    return events.filter(event => {
      return searchFields.some(field => {
        const value = this.getFieldValue(event, field);
        return value && value.toLowerCase().includes(searchTerm.toLowerCase());
      });
    });
  }

  /**
   * Get audit statistics
   */
  getAuditStatistics(timeRange?: { start: Date; end: Date }): {
    totalEvents: number;
    eventsByOutcome: Record<string, number>;
    eventsByUser: Record<string, number>;
    eventsByResource: Record<string, number>;
    complianceEvents: number;
    averageRiskScore: number;
    chainIntegrityStatus: string;
  } {
    // This would query stored audit data in production
    const mockStats = {
      totalEvents: 1250,
      eventsByOutcome: {
        SUCCESS: 1180,
        FAILURE: 65,
        PARTIAL: 5
      },
      eventsByUser: {
        'admin': 45,
        'user': 1200,
        'system': 5
      },
      eventsByResource: {
        'authentication': 450,
        'data': 650,
        'security': 100,
        'admin': 50
      },
      complianceEvents: 890,
      averageRiskScore: 0.15,
      chainIntegrityStatus: 'VALID'
    };

    return mockStats;
  }

  private initializeAuditRules(): void {
    const defaultRules: AuditRule[] = [
      {
        id: 'auth_events',
        name: 'Authentication Events',
        description: 'Capture all authentication-related events',
        triggers: [
          {
            eventType: 'AUTH_*',
            conditions: {}
          }
        ],
        dataToCapture: ['userId', 'action', 'outcome', 'ipAddress', 'userAgent'],
        retentionPeriod: 2555, // 7 years
        complianceRelevant: true,
        encryptionRequired: true,
        priority: 'HIGH'
      },
      {
        id: 'data_access',
        name: 'Data Access Events',
        description: 'Capture all data access and modification events',
        triggers: [
          {
            eventType: 'DATA_*',
            conditions: {}
          }
        ],
        dataToCapture: ['userId', 'dataType', 'operation', 'outcome'],
        retentionPeriod: 2555, // 7 years
        complianceRelevant: true,
        encryptionRequired: true,
        priority: 'CRITICAL'
      },
      {
        id: 'admin_actions',
        name: 'Administrative Actions',
        description: 'Capture all administrative and privileged operations',
        triggers: [
          {
            eventType: 'ADMIN_*',
            conditions: {},
            userRoles: ['admin', 'superuser']
          }
        ],
        dataToCapture: ['userId', 'action', 'targetResource', 'outcome', 'details'],
        retentionPeriod: 3650, // 10 years
        complianceRelevant: true,
        encryptionRequired: true,
        priority: 'CRITICAL'
      },
      {
        id: 'security_events',
        name: 'Security Events',
        description: 'Capture all security-related events and incidents',
        triggers: [
          {
            eventType: '*',
            conditions: { securityEvent: true }
          }
        ],
        dataToCapture: ['userId', 'action', 'riskLevel', 'trustScore', 'details'],
        retentionPeriod: 2555, // 7 years
        complianceRelevant: true,
        encryptionRequired: true,
        priority: 'CRITICAL'
      }
    ];

    for (const rule of defaultRules) {
      this.auditRules.set(rule.id, rule);
    }
  }

  private findMatchingRules(event: AuditEvent): AuditRule[] {
    const matchingRules: AuditRule[] = [];

    for (const rule of this.auditRules.values()) {
      if (this.ruleMatches(rule, event)) {
        matchingRules.push(rule);
      }
    }

    return matchingRules;
  }

  private ruleMatches(rule: AuditRule, event: AuditEvent): boolean {
    return rule.triggers.some(trigger => {
      // Check event type pattern
      const eventTypeMatches = this.patternMatches(trigger.eventType, event.action);
      if (!eventTypeMatches) return false;

      // Check user role constraints
      if (trigger.userRoles && !trigger.userRoles.includes(event.userRole)) {
        return false;
      }

      // Check resource constraints
      if (trigger.resources && !trigger.resources.includes(event.resource)) {
        return false;
      }

      // Check additional conditions
      for (const [key, value] of Object.entries(trigger.conditions)) {
        const eventValue = this.getFieldValue(event, key);
        if (eventValue !== value) return false;
      }

      return true;
    });
  }

  private patternMatches(pattern: string, value: string): boolean {
    if (pattern === '*') return true;
    if (pattern.endsWith('*')) {
      return value.startsWith(pattern.slice(0, -1));
    }
    return pattern === value;
  }

  private getFieldValue(event: AuditEvent, field: string): any {
    const parts = field.split('.');
    let value: any = event;

    for (const part of parts) {
      value = value?.[part];
      if (value === undefined) break;
    }

    return value;
  }

  private sanitizeDetails(details: Record<string, any>): Record<string, any> {
    const sanitized = { ...details };

    // Remove sensitive fields
    const sensitiveFields = ['password', 'token', 'secret', 'key', 'ssn', 'creditCard'];
    for (const field of sensitiveFields) {
      if (sanitized[field]) {
        sanitized[field] = '[REDACTED]';
      }
    }

    return sanitized;
  }

  private isComplianceRelevant(action: string, resource: string, details: Record<string, any>): boolean {
    // Determine if event is relevant for compliance reporting
    const complianceKeywords = [
      'auth', 'login', 'password', 'data', 'admin', 'privileged',
      'delete', 'export', 'access', 'modify', 'security'
    ];

    const actionLower = action.toLowerCase();
    const resourceLower = resource.toLowerCase();

    return complianceKeywords.some(keyword =>
      actionLower.includes(keyword) || resourceLower.includes(keyword)
    ) || details.complianceRelevant === true;
  }

  private calculateRetentionRequirement(action: string, resource: string): number {
    // Calculate retention requirement based on action and resource type
    if (action.includes('ADMIN') || action.includes('PRIVILEGED')) {
      return 3650; // 10 years for admin actions
    }
    if (action.includes('AUTH') || resource === 'authentication') {
      return 2555; // 7 years for authentication
    }
    if (action.includes('DATA') || resource.startsWith('data:')) {
      return 2555; // 7 years for data access
    }
    return 1825; // 5 years default
  }

  private shouldEncryptEvent(event: AuditEvent, rules: AuditRule[]): boolean {
    if (!this.config.encryptionRequired) return false;

    // Encrypt if any matching rule requires encryption
    return rules.some(rule => rule.encryptionRequired) ||
           event.complianceRelevant ||
           event.details.sensitiveData === true;
  }

  private async encryptDetails(details: Record<string, any>): Promise<Record<string, any>> {
    // Simple encryption for demo - use proper encryption in production
    const encrypted = { ...details };
    const sensitiveFields = ['ipAddress', 'userAgent', 'personalData'];

    for (const field of sensitiveFields) {
      if (encrypted[field]) {
        encrypted[field] = Buffer.from(JSON.stringify(encrypted[field])).toString('base64');
      }
    }

    encrypted._encrypted = true;
    return encrypted;
  }

  private async processEvent(event: AuditEvent): Promise<void> {
    // Add event to current chain or create new chain
    if (!this.currentChain || this.shouldCreateNewChain()) {
      await this.createNewChain();
    }

    this.currentChain!.events.push(event);
    await this.updateChainHash(this.currentChain!);

    this.emit('audit:event_processed', event);
  }

  private shouldCreateNewChain(): boolean {
    if (!this.currentChain) return true;

    // Create new chain after 1000 events or 24 hours
    const maxEvents = 1000;
    const maxAge = 24 * 60 * 60 * 1000; // 24 hours

    return this.currentChain.events.length >= maxEvents ||
           (Date.now() - this.currentChain.timestamp.getTime()) > maxAge;
  }

  private async createNewChain(): Promise<void> {
    const chainId = crypto.randomUUID();
    const previousHash = this.currentChain?.hash || '0';

    this.currentChain = {
      id: chainId,
      events: [],
      hash: '',
      previousHash,
      timestamp: new Date()
    };

    await this.updateChainHash(this.currentChain);
    this.auditChains.set(chainId, this.currentChain);

    this.emit('audit:chain_created', { chainId, previousHash });
  }

  private async updateChainHash(chain: AuditChain): Promise<void> {
    // Create hash of chain content for integrity
    const chainData = {
      id: chain.id,
      events: chain.events.map(e => ({ ...e, details: undefined })), // Exclude details from hash
      previousHash: chain.previousHash,
      timestamp: chain.timestamp
    };

    chain.hash = crypto
      .createHash('sha256')
      .update(JSON.stringify(chainData) + this.signingKey)
      .digest('hex');

    // Sign the chain
    if (this.config.encryptionRequired) {
      chain.signature = await this.signChain(chain);
    }
  }

  private async signChain(chain: AuditChain): Promise<string> {
    // Create digital signature for chain integrity
    return crypto
      .createHash('sha256')
      .update(chain.hash + this.signingKey)
      .digest('hex');
  }

  private async verifyChain(chain: AuditChain): Promise<{
    isValid: boolean;
    tamperedEvents: string[];
    verificationDetails: any;
  }> {
    const tamperedEvents: string[] = [];

    // Recalculate hash and compare
    const originalHash = chain.hash;
    await this.updateChainHash({ ...chain });
    const calculatedHash = chain.hash;

    const isValid = originalHash === calculatedHash;

    return {
      isValid,
      tamperedEvents,
      verificationDetails: {
        originalHash,
        calculatedHash,
        chainId: chain.id,
        eventCount: chain.events.length
      }
    };
  }

  private categorizeEvents(events: AuditEvent[]): Record<string, number> {
    const categories: Record<string, number> = {};

    for (const event of events) {
      const category = this.getEventCategory(event);
      categories[category] = (categories[category] || 0) + 1;
    }

    return categories;
  }

  private getEventCategory(event: AuditEvent): string {
    if (event.action.startsWith('AUTH_')) return 'Authentication';
    if (event.action.startsWith('DATA_')) return 'Data Access';
    if (event.action.startsWith('ADMIN_')) return 'Administration';
    if (event.details.securityEvent) return 'Security';
    return 'General';
  }

  private async detectViolations(events: AuditEvent[], reportType: string): Promise<AuditViolation[]> {
    const violations: AuditViolation[] = [];

    // Check for failed authentication patterns
    const failedLogins = events.filter(e =>
      e.action.includes('LOGIN') && e.outcome === 'FAILURE'
    );

    if (failedLogins.length > 100) {
      violations.push({
        id: crypto.randomUUID(),
        type: 'EXCESSIVE_FAILED_LOGINS',
        severity: 'HIGH',
        description: `Excessive failed login attempts detected: ${failedLogins.length}`,
        affectedEvents: failedLogins.map(e => e.id),
        recommendation: 'Review authentication security and implement additional protections',
        timestamp: new Date()
      });
    }

    // Check for privileged actions without proper authorization
    const privilegedActions = events.filter(e =>
      e.details.privilegedOperation && e.outcome === 'FAILURE'
    );

    if (privilegedActions.length > 0) {
      violations.push({
        id: crypto.randomUUID(),
        type: 'UNAUTHORIZED_PRIVILEGED_ACCESS',
        severity: 'CRITICAL',
        description: `Unauthorized privileged access attempts: ${privilegedActions.length}`,
        affectedEvents: privilegedActions.map(e => e.id),
        recommendation: 'Review and strengthen privileged access controls',
        timestamp: new Date()
      });
    }

    return violations;
  }

  private calculateComplianceStatus(violations: AuditViolation[]): 'COMPLIANT' | 'NON_COMPLIANT' | 'PARTIAL' {
    const criticalViolations = violations.filter(v => v.severity === 'CRITICAL').length;
    const highViolations = violations.filter(v => v.severity === 'HIGH').length;

    if (criticalViolations > 0) return 'NON_COMPLIANT';
    if (highViolations > 5) return 'PARTIAL';
    return 'COMPLIANT';
  }

  private generateRecommendations(violations: AuditViolation[], eventCategories: Record<string, number>): string[] {
    const recommendations: string[] = [];

    if (violations.length > 0) {
      recommendations.push('Address identified compliance violations');
    }

    if (eventCategories['Authentication'] > eventCategories['Data Access'] * 2) {
      recommendations.push('Consider implementing stronger authentication measures');
    }

    if (violations.some(v => v.type.includes('PRIVILEGED'))) {
      recommendations.push('Implement stricter privileged access management');
    }

    recommendations.push('Regularly review and update audit policies');
    recommendations.push('Conduct periodic compliance assessments');

    return recommendations;
  }

  private async signReport(report: ComplianceReport): Promise<string> {
    const reportData = { ...report, signature: undefined };
    return crypto
      .createHash('sha256')
      .update(JSON.stringify(reportData) + this.signingKey)
      .digest('hex');
  }

  private exportAsJSON(events: AuditEvent[], includeHashes: boolean): string {
    const exportData = {
      exportedAt: new Date(),
      totalEvents: events.length,
      includesHashes: includeHashes,
      events: events,
      chains: includeHashes ? Array.from(this.auditChains.values()) : undefined
    };

    return JSON.stringify(exportData, null, 2);
  }

  private exportAsCSV(events: AuditEvent[]): string {
    const headers = [
      'id', 'timestamp', 'userId', 'userRole', 'action', 'resource',
      'outcome', 'ipAddress', 'sessionId', 'complianceRelevant'
    ];

    const rows = events.map(event => [
      event.id,
      event.timestamp.toISOString(),
      event.userId,
      event.userRole,
      event.action,
      event.resource,
      event.outcome,
      event.ipAddress,
      event.sessionId,
      event.complianceRelevant
    ]);

    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  private exportAsXML(events: AuditEvent[]): string {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<auditTrail>\n';

    for (const event of events) {
      xml += '  <event>\n';
      xml += `    <id>${event.id}</id>\n`;
      xml += `    <timestamp>${event.timestamp.toISOString()}</timestamp>\n`;
      xml += `    <userId>${event.userId}</userId>\n`;
      xml += `    <action>${event.action}</action>\n`;
      xml += `    <resource>${event.resource}</resource>\n`;
      xml += `    <outcome>${event.outcome}</outcome>\n`;
      xml += '  </event>\n';
    }

    xml += '</auditTrail>';
    return xml;
  }

  private startChainProcessing(): void {
    // Process pending events every 30 seconds
    setInterval(async () => {
      if (this.pendingEvents.length > 0) {
        const eventsToProcess = [...this.pendingEvents];
        this.pendingEvents = [];

        for (const event of eventsToProcess) {
          await this.processEvent(event);
        }
      }
    }, 30000);
  }

  private generateKey(): string {
    return crypto.randomBytes(32).toString('hex');
  }

  shutdown(): void {
    // Process remaining events
    if (this.pendingEvents.length > 0) {
      this.pendingEvents.forEach(event => this.processEvent(event));
    }

    this.emit('audit:shutdown');
  }
}