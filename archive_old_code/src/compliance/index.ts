/**
 * Compliance Framework Entry Point
 * Exports all compliance components and utilities
 */

// Core Framework
export { ComplianceFramework } from './ComplianceFramework';
export type { ComplianceConfiguration } from './ComplianceFramework';

// Individual Components
export { AuditTrail } from './AuditTrail';
export type { AuditEvent, AuditTrailConfig } from './AuditTrail';

export { CircuitBreaker } from './CircuitBreaker';
export type { CircuitBreakerConfig, MarketData, CircuitBreakerEvent } from './CircuitBreaker';

export { StressTesting } from './StressTesting';
export type { StressTestConfig, StressTestScenario, StressTestResult } from './StressTesting';

export { ComplianceMonitor } from './ComplianceMonitor';
export type {
  ComplianceMonitorConfig,
  ComplianceViolation,
  TradingActivity,
  ComplianceMetrics
} from './ComplianceMonitor';

export { RegulatoryReporting } from './RegulatoryReporting';
export type {
  RegulatoryReportingConfig,
  RegulatoryReport,
  ReportSection,
  SubmissionResult
} from './RegulatoryReporting';

// Configuration
export {
  getComplianceConfig,
  DEFAULT_COMPLIANCE_CONFIG,
  DEVELOPMENT_COMPLIANCE_CONFIG,
  PRODUCTION_COMPLIANCE_CONFIG,
  RISK_THRESHOLDS,
  POSITION_LIMITS,
  REPORTING_TEMPLATES,
  ALERT_SEVERITY,
  MODEL_GOVERNANCE,
  CIRCUIT_BREAKER_CONDITIONS
} from '../config/compliance/ComplianceConfig';

// Utility Functions
export const ComplianceUtils = {
  /**
   * Validate trading decision data for compliance
   */
  validateTradingDecision: (decision: any): boolean => {
    const requiredFields = ['symbol', 'action', 'quantity', 'price', 'confidence', 'modelId', 'reasoning', 'riskScore', 'timestamp'];
    return requiredFields.every(field => decision.hasOwnProperty(field) && decision[field] !== null && decision[field] !== undefined);
  },

  /**
   * Calculate risk level based on score
   */
  getRiskLevel: (riskScore: number): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' => {
    if (riskScore >= 0.95) return 'CRITICAL';
    if (riskScore >= 0.8) return 'HIGH';
    if (riskScore >= 0.6) return 'MEDIUM';
    return 'LOW';
  },

  /**
   * Format violation severity for display
   */
  formatSeverity: (severity: string): string => {
    return severity.toLowerCase().replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  },

  /**
   * Calculate compliance score from violations
   */
  calculateComplianceScore: (violations: any[]): number => {
    let score = 100;
    violations.forEach(violation => {
      switch (violation.severity) {
        case 'CRITICAL': score -= 20; break;
        case 'HIGH': score -= 10; break;
        case 'MEDIUM': score -= 5; break;
        case 'LOW': score -= 2; break;
      }
    });
    return Math.max(0, score);
  },

  /**
   * Generate unique compliance ID
   */
  generateComplianceId: (prefix: string = 'COMP'): string => {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Validate report data structure
   */
  validateReportStructure: (report: any): boolean => {
    const requiredFields = ['id', 'type', 'period', 'sections', 'summary', 'certifications', 'signatures'];
    return requiredFields.every(field => report.hasOwnProperty(field));
  },

  /**
   * Format currency values for display
   */
  formatCurrency: (value: number, currency: string = 'USD'): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(value);
  },

  /**
   * Format percentage values for display
   */
  formatPercentage: (value: number, decimals: number = 2): string => {
    return `${(value * 100).toFixed(decimals)}%`;
  },

  /**
   * Calculate days between dates
   */
  daysBetween: (startDate: Date, endDate: Date): number => {
    const timeDiff = endDate.getTime() - startDate.getTime();
    return Math.ceil(timeDiff / (1000 * 3600 * 24));
  },

  /**
   * Check if date is within retention period
   */
  isWithinRetention: (date: Date, retentionDays: number): boolean => {
    const now = new Date();
    const daysDiff = ComplianceUtils.daysBetween(date, now);
    return daysDiff <= retentionDays;
  },

  /**
   * Sanitize data for logging
   */
  sanitizeForLogging: (data: any): any => {
    const sensitiveFields = ['password', 'secret', 'key', 'token', 'credential'];
    const sanitized = { ...data };

    const sanitizeObject = (obj: any): any => {
      if (typeof obj !== 'object' || obj === null) return obj;

      const result: any = Array.isArray(obj) ? [] : {};

      for (const [key, value] of Object.entries(obj)) {
        if (sensitiveFields.some(field => key.toLowerCase().includes(field))) {
          result[key] = '[REDACTED]';
        } else if (typeof value === 'object') {
          result[key] = sanitizeObject(value);
        } else {
          result[key] = value;
        }
      }

      return result;
    };

    return sanitizeObject(sanitized);
  }
};

// Event Types for Type Safety
export interface ComplianceEvents {
  'compliance:initialized': { timestamp: string; components: string[] };
  'compliance:circuit_breaker': any;
  'compliance:violation': any;
  'compliance:human_oversight_required': any;
  'compliance:stress_test_failure': any;
  'compliance:shutdown': { timestamp: string };
  'audit:event_logged': { eventId: string; eventType: string; timestamp: string };
  'circuit:triggered': any;
  'circuit:reset': any;
  'stress_test:completed': any;
  'monitor:activity_processed': any;
  'reporting:report_generated': any;
}

// Constants
export const COMPLIANCE_CONSTANTS = {
  VERSION: '1.0.0',
  MIN_RETENTION_DAYS: 1825, // 5 years minimum
  SEC_RETENTION_DAYS: 2555, // 7 years for SEC
  MAX_RISK_SCORE: 1.0,
  DEFAULT_REPORT_TIMEOUT: 30000, // 30 seconds
  MAX_VIOLATION_AGE_HOURS: 24,
  STRESS_TEST_SCENARIOS: [
    'market_crash_2008',
    'flash_crash_2010',
    'covid_crash_2020',
    'interest_rate_shock',
    'geopolitical_crisis',
    'cyber_attack'
  ]
} as const;

export default ComplianceFramework;