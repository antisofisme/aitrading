/**
 * Comprehensive Compliance Framework for AI Trading Systems
 * Addresses 2024 SEC Algorithmic Trading Accountability Act and EU Digital Markets Act
 */

import { EventEmitter } from 'events';
import { AuditTrail } from './AuditTrail';
import { StressTesting } from './StressTesting';
import { CircuitBreaker } from './CircuitBreaker';
import { ComplianceMonitor } from './ComplianceMonitor';
import { RegulatoryReporting } from './RegulatoryReporting';

export interface ComplianceConfiguration {
  // SEC 2024 Requirements
  algorithmicAccountability: {
    enabled: boolean;
    reportingInterval: number; // minutes
    decisionLoggingLevel: 'minimal' | 'standard' | 'comprehensive';
    humanOversightThreshold: number; // risk score threshold
  };

  // EU Digital Markets Act Requirements
  circuitBreakers: {
    enabled: boolean;
    priceDeviationThreshold: number; // percentage
    volumeThreshold: number;
    timeWindowMs: number;
    cooldownPeriodMs: number;
  };

  // Stress Testing Requirements
  stressTesting: {
    enabled: boolean;
    frequency: 'daily' | 'weekly' | 'monthly';
    scenarios: string[];
    confidenceThreshold: number;
    maxDrawdownLimit: number;
  };

  // Documentation and Audit Requirements
  auditTrail: {
    enabled: boolean;
    retentionPeriodDays: number;
    compressionEnabled: boolean;
    encryptionEnabled: boolean;
    immutableStorage: boolean;
  };

  // Reporting Requirements
  reporting: {
    enabled: boolean;
    secReportingEndpoint?: string;
    euReportingEndpoint?: string;
    reportingSchedule: string; // cron expression
    realTimeAlertsEnabled: boolean;
  };
}

export class ComplianceFramework extends EventEmitter {
  private config: ComplianceConfiguration;
  private auditTrail: AuditTrail;
  private stressTesting: StressTesting;
  private circuitBreaker: CircuitBreaker;
  private complianceMonitor: ComplianceMonitor;
  private regulatoryReporting: RegulatoryReporting;
  private isInitialized: boolean = false;

  constructor(config: ComplianceConfiguration) {
    super();
    this.config = config;
    this.initializeComponents();
  }

  private initializeComponents(): void {
    try {
      // Initialize Audit Trail System
      this.auditTrail = new AuditTrail({
        retentionPeriod: this.config.auditTrail.retentionPeriodDays,
        encryption: this.config.auditTrail.encryptionEnabled,
        compression: this.config.auditTrail.compressionEnabled,
        immutable: this.config.auditTrail.immutableStorage
      });

      // Initialize Circuit Breaker System
      this.circuitBreaker = new CircuitBreaker({
        priceDeviation: this.config.circuitBreakers.priceDeviationThreshold,
        volumeThreshold: this.config.circuitBreakers.volumeThreshold,
        timeWindow: this.config.circuitBreakers.timeWindowMs,
        cooldownPeriod: this.config.circuitBreakers.cooldownPeriodMs
      });

      // Initialize Stress Testing Framework
      this.stressTesting = new StressTesting({
        frequency: this.config.stressTesting.frequency,
        scenarios: this.config.stressTesting.scenarios,
        confidenceThreshold: this.config.stressTesting.confidenceThreshold,
        maxDrawdown: this.config.stressTesting.maxDrawdownLimit
      });

      // Initialize Compliance Monitor
      this.complianceMonitor = new ComplianceMonitor({
        reportingInterval: this.config.algorithmicAccountability.reportingInterval,
        oversightThreshold: this.config.algorithmicAccountability.humanOversightThreshold,
        realTimeAlerts: this.config.reporting.realTimeAlertsEnabled
      });

      // Initialize Regulatory Reporting
      this.regulatoryReporting = new RegulatoryReporting({
        secEndpoint: this.config.reporting.secReportingEndpoint,
        euEndpoint: this.config.reporting.euReportingEndpoint,
        schedule: this.config.reporting.reportingSchedule
      });

      this.setupEventHandlers();
      this.isInitialized = true;

      this.emit('compliance:initialized', {
        timestamp: new Date().toISOString(),
        components: ['auditTrail', 'circuitBreaker', 'stressTesting', 'monitor', 'reporting']
      });

    } catch (error) {
      this.emit('compliance:error', {
        error: error.message,
        component: 'framework',
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  private setupEventHandlers(): void {
    // Circuit Breaker Events
    this.circuitBreaker.on('circuit:triggered', (data) => {
      this.auditTrail.logEvent('CIRCUIT_BREAKER_TRIGGERED', data);
      this.emit('compliance:circuit_breaker', data);
    });

    // Stress Testing Events
    this.stressTesting.on('stress_test:completed', (results) => {
      this.auditTrail.logEvent('STRESS_TEST_COMPLETED', results);
      if (results.failed) {
        this.emit('compliance:stress_test_failure', results);
      }
    });

    // Compliance Monitor Events
    this.complianceMonitor.on('compliance:violation', (violation) => {
      this.auditTrail.logEvent('COMPLIANCE_VIOLATION', violation);
      this.emit('compliance:violation', violation);
    });
  }

  /**
   * Log AI trading decision for SEC accountability requirements
   */
  public async logTradingDecision(decision: {
    symbol: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    quantity: number;
    price: number;
    confidence: number;
    modelId: string;
    reasoning: string;
    riskScore: number;
    timestamp: string;
  }): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('Compliance framework not initialized');
    }

    // Log to audit trail
    await this.auditTrail.logEvent('TRADING_DECISION', {
      ...decision,
      complianceLevel: this.config.algorithmicAccountability.decisionLoggingLevel
    });

    // Check if human oversight is required
    if (decision.riskScore > this.config.algorithmicAccountability.humanOversightThreshold) {
      this.emit('compliance:human_oversight_required', {
        decision,
        reason: 'Risk score exceeds threshold',
        threshold: this.config.algorithmicAccountability.humanOversightThreshold
      });
    }

    // Monitor for circuit breaker conditions
    await this.circuitBreaker.checkConditions({
      symbol: decision.symbol,
      price: decision.price,
      volume: decision.quantity,
      timestamp: decision.timestamp
    });
  }

  /**
   * Execute compliance stress test
   */
  public async executeStressTest(scenario?: string): Promise<any> {
    if (!this.isInitialized) {
      throw new Error('Compliance framework not initialized');
    }

    const results = await this.stressTesting.executeTest(scenario);

    // Log stress test execution
    await this.auditTrail.logEvent('STRESS_TEST_EXECUTED', {
      scenario: scenario || 'default',
      results,
      timestamp: new Date().toISOString()
    });

    return results;
  }

  /**
   * Generate regulatory compliance report
   */
  public async generateComplianceReport(startDate: Date, endDate: Date): Promise<any> {
    if (!this.isInitialized) {
      throw new Error('Compliance framework not initialized');
    }

    const report = await this.regulatoryReporting.generateReport(startDate, endDate);

    // Log report generation
    await this.auditTrail.logEvent('COMPLIANCE_REPORT_GENERATED', {
      startDate: startDate.toISOString(),
      endDate: endDate.toISOString(),
      reportId: report.id,
      timestamp: new Date().toISOString()
    });

    return report;
  }

  /**
   * Get current compliance status
   */
  public getComplianceStatus(): any {
    if (!this.isInitialized) {
      return { status: 'not_initialized' };
    }

    return {
      status: 'active',
      auditTrail: this.auditTrail.getStatus(),
      circuitBreaker: this.circuitBreaker.getStatus(),
      stressTesting: this.stressTesting.getStatus(),
      monitor: this.complianceMonitor.getStatus(),
      reporting: this.regulatoryReporting.getStatus(),
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * Shutdown compliance framework
   */
  public async shutdown(): Promise<void> {
    if (this.isInitialized) {
      await this.auditTrail.flush();
      await this.regulatoryReporting.flush();
      this.circuitBreaker.reset();
      this.isInitialized = false;

      this.emit('compliance:shutdown', {
        timestamp: new Date().toISOString()
      });
    }
  }
}

export default ComplianceFramework;