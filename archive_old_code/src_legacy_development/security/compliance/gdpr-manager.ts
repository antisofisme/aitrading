/**
 * GDPR Compliance Manager
 * Comprehensive data protection and privacy compliance system
 */

import { EventEmitter } from 'events';
import crypto from 'crypto';
import {
  GDPRDataSubject,
  DataCategory,
  DataProcessingRecord,
  LegalBasis,
  ThirdCountryTransfer,
  ComplianceConfig
} from '../types';

interface ConsentRecord {
  id: string;
  subjectId: string;
  purpose: string;
  consentGiven: boolean;
  consentTimestamp: Date;
  consentVersion: string;
  withdrawalTimestamp?: Date;
  ipAddress: string;
  userAgent: string;
}

interface DataRetentionPolicy {
  category: DataCategory;
  retentionPeriod: number; // days
  automaticDeletion: boolean;
  reviewRequired: boolean;
  legalBasis: LegalBasis;
}

interface PrivacyRequest {
  id: string;
  subjectId: string;
  type: 'ACCESS' | 'RECTIFICATION' | 'ERASURE' | 'PORTABILITY' | 'RESTRICTION' | 'OBJECTION';
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  requestDate: Date;
  completionDate?: Date;
  requestDetails: string;
  responseData?: any;
  rejectionReason?: string;
}

export class GDPRManager extends EventEmitter {
  private config: ComplianceConfig;
  private dataSubjects: Map<string, GDPRDataSubject> = new Map();
  private consentRecords: Map<string, ConsentRecord[]> = new Map();
  private processingRecords: Map<string, DataProcessingRecord[]> = new Map();
  private privacyRequests: Map<string, PrivacyRequest> = new Map();
  private retentionPolicies: Map<DataCategory, DataRetentionPolicy> = new Map();
  private auditLog: any[] = [];

  constructor(config: ComplianceConfig) {
    super();
    this.config = config;
    this.initializeRetentionPolicies();
    this.startAutomaticTasks();
  }

  /**
   * Register new data subject
   */
  async registerDataSubject(
    email: string,
    consentGiven: boolean,
    consentVersion: string,
    dataCategories: DataCategory[] = [],
    metadata: any = {}
  ): Promise<string> {
    const subjectId = crypto.randomUUID();

    const dataSubject: GDPRDataSubject = {
      id: subjectId,
      email,
      consentGiven,
      consentTimestamp: new Date(),
      consentVersion,
      dataCategories,
      retentionPeriod: this.calculateRetentionPeriod(dataCategories),
      lastActivity: new Date(),
      rightToBeForgotten: false,
      dataPortabilityRequested: false
    };

    this.dataSubjects.set(subjectId, dataSubject);

    // Record consent
    if (consentGiven) {
      await this.recordConsent(subjectId, 'Registration consent', consentGiven, metadata);
    }

    this.auditLog.push({
      timestamp: new Date(),
      action: 'DATA_SUBJECT_REGISTERED',
      subjectId,
      details: { email, consentGiven, dataCategories }
    });

    this.emit('subject:registered', dataSubject);
    return subjectId;
  }

  /**
   * Record or update consent
   */
  async recordConsent(
    subjectId: string,
    purpose: string,
    consentGiven: boolean,
    metadata: any = {}
  ): Promise<boolean> {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) return false;

    const consentRecord: ConsentRecord = {
      id: crypto.randomUUID(),
      subjectId,
      purpose,
      consentGiven,
      consentTimestamp: new Date(),
      consentVersion: this.getCurrentConsentVersion(),
      ipAddress: metadata.ipAddress || 'unknown',
      userAgent: metadata.userAgent || 'unknown'
    };

    if (!this.consentRecords.has(subjectId)) {
      this.consentRecords.set(subjectId, []);
    }

    this.consentRecords.get(subjectId)!.push(consentRecord);

    // Update subject consent status
    subject.consentGiven = consentGiven;
    subject.consentTimestamp = new Date();
    subject.consentVersion = consentRecord.consentVersion;

    this.auditLog.push({
      timestamp: new Date(),
      action: 'CONSENT_RECORDED',
      subjectId,
      details: { purpose, consentGiven, consentVersion: consentRecord.consentVersion }
    });

    this.emit('consent:recorded', { subjectId, consentRecord });
    return true;
  }

  /**
   * Withdraw consent
   */
  async withdrawConsent(subjectId: string, purpose?: string): Promise<boolean> {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) return false;

    const consentRecords = this.consentRecords.get(subjectId) || [];

    // Mark relevant consent records as withdrawn
    const updatedRecords = consentRecords.map(record => {
      if (!purpose || record.purpose === purpose) {
        return {
          ...record,
          consentGiven: false,
          withdrawalTimestamp: new Date()
        };
      }
      return record;
    });

    this.consentRecords.set(subjectId, updatedRecords);

    // Update subject status
    subject.consentGiven = false;
    subject.consentTimestamp = new Date();

    this.auditLog.push({
      timestamp: new Date(),
      action: 'CONSENT_WITHDRAWN',
      subjectId,
      details: { purpose }
    });

    this.emit('consent:withdrawn', { subjectId, purpose });

    // Start data minimization process
    if (this.config.dataMinimization) {
      await this.startDataMinimization(subjectId);
    }

    return true;
  }

  /**
   * Record data processing activity
   */
  async recordProcessing(
    subjectId: string,
    purpose: string,
    legalBasis: LegalBasis,
    dataCategories: DataCategory[],
    processors: string[] = [],
    thirdCountryTransfers: ThirdCountryTransfer[] = [],
    automated: boolean = false
  ): Promise<string> {
    const recordId = crypto.randomUUID();

    const processingRecord: DataProcessingRecord = {
      id: recordId,
      subjectId,
      purpose,
      legalBasis,
      dataCategories,
      processors,
      thirdCountryTransfers,
      retentionPeriod: this.calculateRetentionPeriod(dataCategories),
      timestamp: new Date(),
      automated
    };

    if (!this.processingRecords.has(subjectId)) {
      this.processingRecords.set(subjectId, []);
    }

    this.processingRecords.get(subjectId)!.push(processingRecord);

    this.auditLog.push({
      timestamp: new Date(),
      action: 'PROCESSING_RECORDED',
      subjectId,
      details: { purpose, legalBasis, dataCategories, automated }
    });

    this.emit('processing:recorded', processingRecord);
    return recordId;
  }

  /**
   * Handle privacy rights requests
   */
  async submitPrivacyRequest(
    subjectId: string,
    type: PrivacyRequest['type'],
    requestDetails: string,
    metadata: any = {}
  ): Promise<string> {
    const requestId = crypto.randomUUID();

    const privacyRequest: PrivacyRequest = {
      id: requestId,
      subjectId,
      type,
      status: 'PENDING',
      requestDate: new Date(),
      requestDetails,
    };

    this.privacyRequests.set(requestId, privacyRequest);

    this.auditLog.push({
      timestamp: new Date(),
      action: 'PRIVACY_REQUEST_SUBMITTED',
      subjectId,
      details: { type, requestId, requestDetails }
    });

    this.emit('privacy:request_submitted', privacyRequest);

    // Auto-process certain requests if enabled
    if (this.config.automaticDeletion && type === 'ERASURE') {
      setImmediate(() => this.processPrivacyRequest(requestId));
    }

    return requestId;
  }

  /**
   * Process privacy rights request
   */
  async processPrivacyRequest(requestId: string): Promise<boolean> {
    const request = this.privacyRequests.get(requestId);
    if (!request || request.status !== 'PENDING') return false;

    request.status = 'IN_PROGRESS';
    this.emit('privacy:request_processing', request);

    try {
      switch (request.type) {
        case 'ACCESS':
          request.responseData = await this.generateDataAccess(request.subjectId);
          break;

        case 'ERASURE':
          await this.processDataErasure(request.subjectId);
          break;

        case 'PORTABILITY':
          request.responseData = await this.generateDataPortability(request.subjectId);
          break;

        case 'RECTIFICATION':
          // Placeholder for data rectification
          break;

        case 'RESTRICTION':
          await this.restrictDataProcessing(request.subjectId);
          break;

        case 'OBJECTION':
          await this.handleProcessingObjection(request.subjectId);
          break;
      }

      request.status = 'COMPLETED';
      request.completionDate = new Date();

      this.auditLog.push({
        timestamp: new Date(),
        action: 'PRIVACY_REQUEST_COMPLETED',
        subjectId: request.subjectId,
        details: { type: request.type, requestId }
      });

      this.emit('privacy:request_completed', request);
      return true;

    } catch (error) {
      request.status = 'REJECTED';
      request.rejectionReason = error.message;

      this.auditLog.push({
        timestamp: new Date(),
        action: 'PRIVACY_REQUEST_REJECTED',
        subjectId: request.subjectId,
        details: { type: request.type, requestId, reason: error.message }
      });

      this.emit('privacy:request_rejected', request);
      return false;
    }
  }

  /**
   * Generate data access report (Article 15)
   */
  private async generateDataAccess(subjectId: string): Promise<any> {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) throw new Error('Data subject not found');

    const consentRecords = this.consentRecords.get(subjectId) || [];
    const processingRecords = this.processingRecords.get(subjectId) || [];

    return {
      personalData: {
        subjectId: subject.id,
        email: subject.email,
        dataCategories: subject.dataCategories,
        registrationDate: subject.consentTimestamp,
        lastActivity: subject.lastActivity
      },
      consentHistory: consentRecords.map(record => ({
        purpose: record.purpose,
        consentGiven: record.consentGiven,
        timestamp: record.consentTimestamp,
        version: record.consentVersion,
        withdrawalDate: record.withdrawalTimestamp
      })),
      processingActivities: processingRecords.map(record => ({
        purpose: record.purpose,
        legalBasis: record.legalBasis,
        dataCategories: record.dataCategories,
        processors: record.processors,
        timestamp: record.timestamp,
        retentionPeriod: record.retentionPeriod
      })),
      retentionInfo: {
        retentionPeriod: subject.retentionPeriod,
        dataMinimizationApplied: this.config.dataMinimization
      },
      generatedAt: new Date()
    };
  }

  /**
   * Process data erasure request (Right to be forgotten)
   */
  private async processDataErasure(subjectId: string): Promise<void> {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) throw new Error('Data subject not found');

    // Mark for erasure
    subject.rightToBeForgotten = true;

    // Remove or anonymize data based on legal requirements
    // In a real implementation, this would coordinate with all data stores
    await this.anonymizeSubjectData(subjectId);

    // Keep minimal audit record for compliance
    this.auditLog.push({
      timestamp: new Date(),
      action: 'DATA_ERASED',
      subjectId,
      details: { erasureReason: 'Right to be forgotten request' }
    });

    this.emit('data:erased', { subjectId });
  }

  /**
   * Generate data portability export (Article 20)
   */
  private async generateDataPortability(subjectId: string): Promise<any> {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) throw new Error('Data subject not found');

    subject.dataPortabilityRequested = true;

    // Generate structured data export
    const exportData = await this.generateDataAccess(subjectId);

    // Add portability-specific formatting
    exportData.exportFormat = 'JSON';
    exportData.exportVersion = '1.0';
    exportData.machineReadable = true;

    return exportData;
  }

  /**
   * Check if processing is lawful for data subject
   */
  isProcessingLawful(subjectId: string, purpose: string): boolean {
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) return false;

    // Check consent
    if (subject.consentGiven) return true;

    // Check other legal bases
    const processingRecords = this.processingRecords.get(subjectId) || [];
    const relevantRecord = processingRecords.find(r => r.purpose === purpose);

    if (relevantRecord) {
      switch (relevantRecord.legalBasis) {
        case LegalBasis.CONTRACT:
        case LegalBasis.LEGAL_OBLIGATION:
        case LegalBasis.VITAL_INTERESTS:
        case LegalBasis.PUBLIC_TASK:
        case LegalBasis.LEGITIMATE_INTERESTS:
          return true;
        default:
          return false;
      }
    }

    return false;
  }

  /**
   * Get compliance status for data subject
   */
  getComplianceStatus(subjectId: string): {
    isCompliant: boolean;
    issues: string[];
    recommendations: string[];
  } {
    const subject = this.dataSubjects.get(subjectId);
    const issues: string[] = [];
    const recommendations: string[] = [];

    if (!subject) {
      return { isCompliant: false, issues: ['Data subject not found'], recommendations: [] };
    }

    // Check consent validity
    if (!subject.consentGiven && !this.hasAlternateLegalBasis(subjectId)) {
      issues.push('No valid consent or legal basis for processing');
    }

    // Check data retention
    const daysSinceLastActivity = Math.floor(
      (Date.now() - subject.lastActivity.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (daysSinceLastActivity > subject.retentionPeriod) {
      issues.push('Data retention period exceeded');
      recommendations.push('Consider data deletion or renewal of legal basis');
    }

    // Check if consent is up to date
    const consentAge = Math.floor(
      (Date.now() - subject.consentTimestamp.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (consentAge > 365) {
      recommendations.push('Consider refreshing consent (older than 1 year)');
    }

    return {
      isCompliant: issues.length === 0,
      issues,
      recommendations
    };
  }

  /**
   * Generate compliance report
   */
  generateComplianceReport(timeWindow?: { start: Date; end: Date }): {
    totalSubjects: number;
    activeConsents: number;
    withdrawnConsents: number;
    privacyRequests: Record<string, number>;
    complianceIssues: number;
    dataRetentionStatus: any;
    auditSummary: any;
  } {
    const subjects = Array.from(this.dataSubjects.values());
    const requests = Array.from(this.privacyRequests.values());

    let filteredSubjects = subjects;
    let filteredRequests = requests;

    if (timeWindow) {
      filteredSubjects = subjects.filter(s =>
        s.consentTimestamp >= timeWindow.start && s.consentTimestamp <= timeWindow.end
      );
      filteredRequests = requests.filter(r =>
        r.requestDate >= timeWindow.start && r.requestDate <= timeWindow.end
      );
    }

    const activeConsents = filteredSubjects.filter(s => s.consentGiven).length;
    const withdrawnConsents = filteredSubjects.length - activeConsents;

    const privacyRequestCounts = filteredRequests.reduce((counts, request) => {
      counts[request.type] = (counts[request.type] || 0) + 1;
      return counts;
    }, {} as Record<string, number>);

    const complianceIssues = filteredSubjects.filter(s => {
      const status = this.getComplianceStatus(s.id);
      return !status.isCompliant;
    }).length;

    return {
      totalSubjects: filteredSubjects.length,
      activeConsents,
      withdrawnConsents,
      privacyRequests: privacyRequestCounts,
      complianceIssues,
      dataRetentionStatus: this.getDataRetentionStatus(),
      auditSummary: this.getAuditSummary(timeWindow)
    };
  }

  private initializeRetentionPolicies(): void {
    // Default retention policies by data category
    const policies: Array<[DataCategory, DataRetentionPolicy]> = [
      [DataCategory.PERSONAL_IDENTIFIERS, {
        category: DataCategory.PERSONAL_IDENTIFIERS,
        retentionPeriod: 2555, // 7 years
        automaticDeletion: true,
        reviewRequired: false,
        legalBasis: LegalBasis.LEGITIMATE_INTERESTS
      }],
      [DataCategory.FINANCIAL_DATA, {
        category: DataCategory.FINANCIAL_DATA,
        retentionPeriod: 2555, // 7 years (regulatory requirement)
        automaticDeletion: false,
        reviewRequired: true,
        legalBasis: LegalBasis.LEGAL_OBLIGATION
      }],
      [DataCategory.BEHAVIORAL_DATA, {
        category: DataCategory.BEHAVIORAL_DATA,
        retentionPeriod: 365, // 1 year
        automaticDeletion: true,
        reviewRequired: false,
        legalBasis: LegalBasis.LEGITIMATE_INTERESTS
      }]
    ];

    for (const [category, policy] of policies) {
      this.retentionPolicies.set(category, policy);
    }
  }

  private calculateRetentionPeriod(dataCategories: DataCategory[]): number {
    if (dataCategories.length === 0) return 365; // Default 1 year

    // Return the longest retention period for any category
    return Math.max(...dataCategories.map(category => {
      const policy = this.retentionPolicies.get(category);
      return policy ? policy.retentionPeriod : 365;
    }));
  }

  private getCurrentConsentVersion(): string {
    return '2024-01-01'; // Version should be updated when privacy policy changes
  }

  private hasAlternateLegalBasis(subjectId: string): boolean {
    const processingRecords = this.processingRecords.get(subjectId) || [];
    return processingRecords.some(record => record.legalBasis !== LegalBasis.CONSENT);
  }

  private async startDataMinimization(subjectId: string): Promise<void> {
    // Remove unnecessary data when consent is withdrawn
    const subject = this.dataSubjects.get(subjectId);
    if (!subject) return;

    // Keep only data required by legal obligations
    const legallyRequired = this.getDataRequiredByLaw(subjectId);

    // Implement data minimization logic
    this.emit('data:minimization_started', { subjectId, legallyRequired });
  }

  private getDataRequiredByLaw(subjectId: string): DataCategory[] {
    const processingRecords = this.processingRecords.get(subjectId) || [];

    return processingRecords
      .filter(record => record.legalBasis === LegalBasis.LEGAL_OBLIGATION)
      .flatMap(record => record.dataCategories);
  }

  private async anonymizeSubjectData(subjectId: string): Promise<void> {
    // In a real implementation, this would anonymize data across all systems
    const subject = this.dataSubjects.get(subjectId);
    if (subject) {
      subject.email = `anonymized-${crypto.randomUUID()}@deleted.local`;
      subject.dataCategories = [];
    }
  }

  private async restrictDataProcessing(subjectId: string): Promise<void> {
    // Mark data for restricted processing
    const subject = this.dataSubjects.get(subjectId);
    if (subject) {
      // Add restriction flag (would need to be implemented in data structure)
      this.emit('data:processing_restricted', { subjectId });
    }
  }

  private async handleProcessingObjection(subjectId: string): Promise<void> {
    // Handle objection to processing
    const subject = this.dataSubjects.get(subjectId);
    if (subject) {
      // Evaluate if processing can continue under other legal bases
      this.emit('data:processing_objection', { subjectId });
    }
  }

  private getDataRetentionStatus(): any {
    const subjects = Array.from(this.dataSubjects.values());
    const now = new Date();

    return {
      totalSubjects: subjects.length,
      subjectsNearingRetention: subjects.filter(s => {
        const daysSinceActivity = (now.getTime() - s.lastActivity.getTime()) / (1000 * 60 * 60 * 24);
        return daysSinceActivity > (s.retentionPeriod - 30); // Within 30 days of retention limit
      }).length,
      subjectsExceedingRetention: subjects.filter(s => {
        const daysSinceActivity = (now.getTime() - s.lastActivity.getTime()) / (1000 * 60 * 60 * 24);
        return daysSinceActivity > s.retentionPeriod;
      }).length
    };
  }

  private getAuditSummary(timeWindow?: { start: Date; end: Date }): any {
    let filteredAuditLog = this.auditLog;

    if (timeWindow) {
      filteredAuditLog = this.auditLog.filter(entry =>
        entry.timestamp >= timeWindow.start && entry.timestamp <= timeWindow.end
      );
    }

    const actionCounts = filteredAuditLog.reduce((counts, entry) => {
      counts[entry.action] = (counts[entry.action] || 0) + 1;
      return counts;
    }, {} as Record<string, number>);

    return {
      totalActions: filteredAuditLog.length,
      actionBreakdown: actionCounts,
      recentActivity: filteredAuditLog.slice(-10) // Last 10 actions
    };
  }

  private startAutomaticTasks(): void {
    // Run daily cleanup tasks
    setInterval(async () => {
      if (this.config.automaticDeletion) {
        await this.performAutomaticDeletion();
      }
    }, 24 * 60 * 60 * 1000); // Every 24 hours
  }

  private async performAutomaticDeletion(): Promise<void> {
    const subjects = Array.from(this.dataSubjects.values());
    const now = new Date();

    for (const subject of subjects) {
      const daysSinceActivity = (now.getTime() - subject.lastActivity.getTime()) / (1000 * 60 * 60 * 24);

      if (daysSinceActivity > subject.retentionPeriod && subject.rightToBeForgotten) {
        await this.anonymizeSubjectData(subject.id);
        this.emit('data:automatic_deletion', { subjectId: subject.id });
      }
    }
  }

  /**
   * Update data subject activity
   */
  updateLastActivity(subjectId: string): void {
    const subject = this.dataSubjects.get(subjectId);
    if (subject) {
      subject.lastActivity = new Date();
    }
  }

  /**
   * Get data subject by email
   */
  getDataSubjectByEmail(email: string): GDPRDataSubject | undefined {
    return Array.from(this.dataSubjects.values()).find(subject => subject.email === email);
  }

  /**
   * Export audit log for compliance reporting
   */
  exportAuditLog(timeWindow?: { start: Date; end: Date }): any[] {
    let filteredLog = this.auditLog;

    if (timeWindow) {
      filteredLog = this.auditLog.filter(entry =>
        entry.timestamp >= timeWindow.start && entry.timestamp <= timeWindow.end
      );
    }

    return filteredLog;
  }

  shutdown(): void {
    this.emit('gdpr:shutdown');
  }
}