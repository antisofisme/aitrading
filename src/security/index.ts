/**
 * Security System Main Entry Point
 * Centralized initialization and coordination of all security components
 */

import { EventEmitter } from 'events';
import { ZeroTrustFramework } from './auth/zero-trust';
import { IntelligentLogger } from './logging/intelligent-logger';
import { ErrorDNASystem } from './logging/error-dna';
import { GDPRManager } from './compliance/gdpr-manager';
import { ThreatDetector } from './monitoring/threat-detector';
import { AuditTrail } from './audit/audit-trail';
import { OptimizedStorage } from './storage/optimized-storage';
import { SecurityConfigManager } from './config/security-config';
import {
  SecurityConfig,
  SecurityContext,
  LogEntry,
  LogLevel,
  LogCategory,
  ThreatEvent,
  AuditEvent,
  ErrorDNA
} from './types';

export interface SecuritySystemOptions {
  config?: Partial<SecurityConfig>;
  basePath?: string;
  loadFromEnv?: boolean;
}

export class SecuritySystem extends EventEmitter {
  private configManager: SecurityConfigManager;
  private zeroTrust: ZeroTrustFramework;
  private logger: IntelligentLogger;
  private errorDNA: ErrorDNASystem;
  private gdprManager: GDPRManager;
  private threatDetector: ThreatDetector;
  private auditTrail: AuditTrail;
  private storage: OptimizedStorage;
  private initialized: boolean = false;
  private metrics: {
    totalEvents: number;
    threatsDetected: number;
    complianceViolations: number;
    costSavings: number;
    uptime: Date;
  };

  constructor(options: SecuritySystemOptions = {}) {
    super();

    // Initialize configuration manager
    this.configManager = new SecurityConfigManager(options.config);

    if (options.loadFromEnv) {
      this.configManager.loadFromEnvironment();
    }

    // Initialize metrics
    this.metrics = {
      totalEvents: 0,
      threatsDetected: 0,
      complianceViolations: 0,
      costSavings: 0,
      uptime: new Date()
    };

    // Initialize all components
    this.initializeComponents(options.basePath);

    // Set up component coordination
    this.setupComponentCoordination();

    this.initialized = true;
    this.emit('security:initialized');
  }

  /**
   * Authenticate user and establish security context
   */
  async authenticate(credentials: any): Promise<SecurityContext> {
    if (!this.initialized) {
      throw new Error('Security system not initialized');
    }

    try {
      const context = await this.zeroTrust.authenticate(credentials);

      // Log authentication event
      await this.logger.logAuthenticationEvent(
        true,
        context.userId,
        {
          ipAddress: context.ipAddress,
          userAgent: context.userAgent,
          trustScore: context.trustScore,
          riskLevel: context.riskLevel
        }
      );

      // Record audit event
      await this.auditTrail.recordAuthenticationEvent(
        context.userId,
        'LOGIN',
        'SUCCESS',
        {
          ipAddress: context.ipAddress,
          userAgent: context.userAgent,
          mfaVerified: context.mfaVerified
        },
        context
      );

      // Check for threats
      const threats = await this.threatDetector.analyzeSecurityContext(context);
      if (threats.length > 0) {
        this.metrics.threatsDetected += threats.length;
        this.emit('security:threats_detected', { context, threats });
      }

      return context;

    } catch (error) {
      // Log failed authentication
      await this.logger.logAuthenticationEvent(
        false,
        credentials.userId || 'unknown',
        {
          ipAddress: credentials.ipAddress,
          userAgent: credentials.userAgent,
          error: error.message
        }
      );

      // Record audit event
      await this.auditTrail.recordAuthenticationEvent(
        credentials.userId || 'unknown',
        'LOGIN',
        'FAILURE',
        {
          ipAddress: credentials.ipAddress,
          userAgent: credentials.userAgent,
          error: error.message
        }
      );

      throw error;
    }
  }

  /**
   * Authorize access to resource
   */
  async authorize(sessionId: string, resource: string, action: string): Promise<boolean> {
    try {
      const authorized = await this.zeroTrust.authorize(sessionId, resource, action);
      const context = this.zeroTrust.getSecurityContext(sessionId);

      // Log authorization event
      await this.logger.logAuthorizationEvent(
        authorized,
        context?.userId || 'unknown',
        resource,
        action,
        {
          sessionId,
          riskLevel: context?.riskLevel
        }
      );

      // Record audit event
      if (context) {
        await this.auditTrail.recordEvent(
          context.userId,
          'user',
          `AUTHORIZE_${action}`,
          resource,
          authorized ? 'SUCCESS' : 'FAILURE',
          { sessionId, action },
          context
        );
      }

      return authorized;

    } catch (error) {
      await this.logger.error(`Authorization error: ${error.message}`, {
        sessionId,
        resource,
        action
      });

      return false;
    }
  }

  /**
   * Log security event
   */
  async logSecurityEvent(
    level: LogLevel,
    category: LogCategory,
    message: string,
    metadata: Record<string, any> = {},
    component: string = 'security'
  ): Promise<string> {
    this.metrics.totalEvents++;

    // Log the event
    const logId = await this.logger.log(level, category, message, metadata, component);

    // Get the log entry for analysis
    const logEntry = await this.getLogEntry(logId);
    if (logEntry) {
      // Analyze for threats
      const threats = await this.threatDetector.analyzeLogEntry(logEntry);
      if (threats.length > 0) {
        this.metrics.threatsDetected += threats.length;
        this.emit('security:threats_detected', { logEntry, threats });
      }

      // Analyze for errors if applicable
      if ([LogLevel.ERROR, LogLevel.CRITICAL].includes(level)) {
        const errorDNA = await this.errorDNA.analyzeError(logEntry);
        this.emit('security:error_analyzed', { logEntry, errorDNA });
      }
    }

    return logId;
  }

  /**
   * Report security incident
   */
  async reportIncident(
    description: string,
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    context?: SecurityContext,
    metadata: Record<string, any> = {}
  ): Promise<string> {
    // Log the incident
    const logId = await this.logSecurityEvent(
      LogLevel.CRITICAL,
      LogCategory.SECURITY,
      `SECURITY INCIDENT: ${description}`,
      {
        ...metadata,
        severity,
        incidentType: 'MANUAL_REPORT',
        reportedAt: new Date()
      },
      'incident_reporting'
    );

    // Record audit event
    if (context) {
      await this.auditTrail.recordSecurityEvent(
        'INCIDENT_REPORTED',
        'SUCCESS',
        {
          description,
          severity,
          ...metadata
        },
        context
      );
    }

    this.emit('security:incident_reported', {
      logId,
      description,
      severity,
      context,
      metadata
    });

    return logId;
  }

  /**
   * Get system security status
   */
  getSecurityStatus(): {
    systemHealth: 'HEALTHY' | 'WARNING' | 'CRITICAL';
    componentsStatus: Record<string, boolean>;
    metrics: typeof this.metrics;
    configStatus: any;
    activeThreats: number;
    complianceStatus: string;
  } {
    const configStatus = this.configManager.getConfigStatus();
    const activeThreats = this.threatDetector.getActiveThreats().length;

    // Determine system health
    let systemHealth: 'HEALTHY' | 'WARNING' | 'CRITICAL' = 'HEALTHY';
    if (activeThreats > 10) systemHealth = 'CRITICAL';
    else if (activeThreats > 0) systemHealth = 'WARNING';

    const componentsStatus = {
      zeroTrust: this.configManager.getZeroTrustConfig().enabled,
      logging: true, // Always enabled
      errorDNA: true, // Always enabled
      gdpr: this.configManager.getComplianceConfig().gdprEnabled,
      threatDetection: this.configManager.getMonitoringConfig().threatDetection,
      audit: this.configManager.getAuditConfig().enabled,
      storage: this.configManager.getStorageConfig().tieredStorage
    };

    return {
      systemHealth,
      componentsStatus,
      metrics: { ...this.metrics },
      configStatus,
      activeThreats,
      complianceStatus: 'COMPLIANT' // Simplified for demo
    };
  }

  /**
   * Generate security report
   */
  async generateSecurityReport(
    timeRange: { start: Date; end: Date },
    reportType: 'SECURITY' | 'COMPLIANCE' | 'PERFORMANCE' | 'COMPREHENSIVE' = 'COMPREHENSIVE'
  ): Promise<any> {
    const report: any = {
      reportType,
      timeRange,
      generatedAt: new Date(),
      generatedBy: 'security-system'
    };

    if (reportType === 'SECURITY' || reportType === 'COMPREHENSIVE') {
      // Security metrics
      report.security = {
        threatStatistics: this.threatDetector.getThreatStatistics(timeRange),
        errorTrends: this.errorDNA.getErrorTrends(timeRange),
        authenticationMetrics: await this.getAuthenticationMetrics(timeRange)
      };
    }

    if (reportType === 'COMPLIANCE' || reportType === 'COMPREHENSIVE') {
      // Compliance metrics
      report.compliance = this.gdprManager.generateComplianceReport(timeRange);
      report.audit = await this.auditTrail.generateComplianceReport(timeRange);
    }

    if (reportType === 'PERFORMANCE' || reportType === 'COMPREHENSIVE') {
      // Performance metrics
      report.performance = {
        storageMetrics: this.storage.getMetrics(),
        systemPerformance: this.getSystemPerformanceMetrics()
      };
    }

    this.emit('security:report_generated', report);
    return report;
  }

  /**
   * Handle data subject request (GDPR)
   */
  async handleDataSubjectRequest(
    email: string,
    requestType: 'ACCESS' | 'ERASURE' | 'PORTABILITY' | 'RECTIFICATION',
    requestDetails: string = ''
  ): Promise<string> {
    const subject = this.gdprManager.getDataSubjectByEmail(email);
    if (!subject) {
      throw new Error('Data subject not found');
    }

    const requestId = await this.gdprManager.submitPrivacyRequest(
      subject.id,
      requestType,
      requestDetails
    );

    // Log the request
    await this.logSecurityEvent(
      LogLevel.INFO,
      LogCategory.COMPLIANCE,
      `GDPR ${requestType} request submitted`,
      {
        email,
        requestId,
        requestType,
        requestDetails
      },
      'gdpr'
    );

    // Record audit event
    await this.auditTrail.recordEvent(
      'system',
      'system',
      `GDPR_${requestType}_REQUEST`,
      'data_protection',
      'SUCCESS',
      {
        email,
        requestId,
        requestType
      }
    );

    return requestId;
  }

  /**
   * Update security configuration
   */
  updateConfiguration(updates: Partial<SecurityConfig>): void {
    this.configManager.updateConfig(updates);

    // Reinitialize components if necessary
    this.reinitializeComponents(updates);

    this.emit('security:configuration_updated', updates);
  }

  /**
   * Export all security data
   */
  async exportSecurityData(
    format: 'JSON' | 'CSV',
    timeRange: { start: Date; end: Date },
    includePersonalData: boolean = false
  ): Promise<string> {
    const exportData: any = {
      exportedAt: new Date(),
      timeRange,
      format,
      includePersonalData
    };

    // Export logs
    exportData.logs = await this.logger.queryLogs({
      startDate: timeRange.start,
      endDate: timeRange.end,
      limit: 10000
    });

    // Export audit trail
    exportData.auditTrail = await this.auditTrail.exportAuditData(
      format,
      timeRange,
      true // Include hashes for integrity
    );

    // Export threat data
    exportData.threats = this.threatDetector.getThreatStatistics(timeRange);

    // Export compliance data (if personal data is included)
    if (includePersonalData) {
      exportData.compliance = this.gdprManager.generateComplianceReport(timeRange);
    }

    return format === 'JSON'
      ? JSON.stringify(exportData, null, 2)
      : this.convertToCSV(exportData);
  }

  /**
   * Shutdown security system gracefully
   */
  async shutdown(): Promise<void> {
    this.emit('security:shutting_down');

    // Shutdown all components
    await this.logger.shutdown();
    this.errorDNA.shutdown();
    this.gdprManager.shutdown();
    this.threatDetector.shutdown();
    this.auditTrail.shutdown();
    this.storage.shutdown();

    this.initialized = false;
    this.emit('security:shutdown_complete');
  }

  private initializeComponents(basePath: string = './security-data'): void {
    const config = this.configManager.getConfig();

    // Initialize Zero-Trust Framework
    this.zeroTrust = new ZeroTrustFramework(config.zeroTrust);

    // Initialize Intelligent Logger
    this.logger = new IntelligentLogger(config.logging);

    // Initialize ErrorDNA System
    this.errorDNA = new ErrorDNASystem();

    // Initialize GDPR Manager
    this.gdprManager = new GDPRManager(config.compliance);

    // Initialize Threat Detector
    this.threatDetector = new ThreatDetector(config.monitoring);

    // Initialize Audit Trail
    this.auditTrail = new AuditTrail(config.audit);

    // Initialize Optimized Storage
    this.storage = new OptimizedStorage(config.storage, basePath);
  }

  private setupComponentCoordination(): void {
    // Forward events from components
    this.zeroTrust.on('authentication:success', (data) =>
      this.emit('security:authentication_success', data));

    this.zeroTrust.on('authorization:denied', (data) =>
      this.emit('security:authorization_denied', data));

    this.threatDetector.on('threat:detected', (threat) => {
      this.metrics.threatsDetected++;
      this.emit('security:threat_detected', threat);
    });

    this.errorDNA.on('error:alert', (data) =>
      this.emit('security:error_alert', data));

    this.gdprManager.on('privacy:request_submitted', (data) =>
      this.emit('security:privacy_request', data));

    this.auditTrail.on('audit:compliance_report_generated', (report) =>
      this.emit('security:compliance_report', report));

    this.storage.on('storage:optimization_complete', (data) => {
      this.metrics.costSavings += data.costSavings;
      this.emit('security:storage_optimized', data);
    });
  }

  private reinitializeComponents(updates: Partial<SecurityConfig>): void {
    // Reinitialize components that were updated
    if (updates.zeroTrust) {
      // Zero-trust configuration changed - create new instance
      this.zeroTrust = new ZeroTrustFramework(this.configManager.getZeroTrustConfig());
    }

    if (updates.logging) {
      // Logging configuration changed - update logger
      this.logger = new IntelligentLogger(this.configManager.getLoggingConfig());
    }

    // Re-setup coordination
    this.setupComponentCoordination();
  }

  private async getLogEntry(logId: string): Promise<LogEntry | null> {
    // This would query the actual log storage in production
    // For now, return null as placeholder
    return null;
  }

  private async getAuthenticationMetrics(timeRange: { start: Date; end: Date }): Promise<any> {
    // Query authentication logs
    const authLogs = await this.logger.queryLogs({
      category: LogCategory.AUTHENTICATION,
      startDate: timeRange.start,
      endDate: timeRange.end
    });

    const successful = authLogs.logs.filter(log => log.message.includes('successful')).length;
    const failed = authLogs.logs.filter(log => log.message.includes('failed')).length;

    return {
      totalAttempts: successful + failed,
      successfulLogins: successful,
      failedLogins: failed,
      successRate: successful / (successful + failed) || 0
    };
  }

  private getSystemPerformanceMetrics(): any {
    const uptime = Date.now() - this.metrics.uptime.getTime();

    return {
      uptime: uptime,
      eventsPerSecond: this.metrics.totalEvents / (uptime / 1000),
      threatsDetectedPerDay: (this.metrics.threatsDetected / (uptime / (1000 * 60 * 60 * 24))),
      memoryUsage: process.memoryUsage(),
      cpuUsage: process.cpuUsage()
    };
  }

  private convertToCSV(data: any): string {
    // Simplified CSV conversion for demo
    return JSON.stringify(data);
  }
}

// Export all types and components for external use
export * from './types';
export * from './auth/zero-trust';
export * from './logging/intelligent-logger';
export * from './logging/error-dna';
export * from './compliance/gdpr-manager';
export * from './monitoring/threat-detector';
export * from './audit/audit-trail';
export * from './storage/optimized-storage';
export * from './config/security-config';