/**
 * Compliance Framework Configuration
 * Central configuration for all compliance components
 */

import { ComplianceConfiguration } from '../../src/compliance/ComplianceFramework';

export const DEFAULT_COMPLIANCE_CONFIG: ComplianceConfiguration = {
  // SEC 2024 Algorithmic Trading Accountability Act Requirements
  algorithmicAccountability: {
    enabled: true,
    reportingInterval: 60, // Report every hour
    decisionLoggingLevel: 'comprehensive', // Full logging for regulatory compliance
    humanOversightThreshold: 0.8 // Risk score threshold requiring human oversight
  },

  // EU Digital Markets Act Circuit Breaker Requirements
  circuitBreakers: {
    enabled: true,
    priceDeviationThreshold: 5.0, // 5% price deviation triggers circuit breaker
    volumeThreshold: 3.0, // 3x normal volume triggers circuit breaker
    timeWindowMs: 300000, // 5-minute monitoring window
    cooldownPeriodMs: 900000 // 15-minute cooldown period
  },

  // Stress Testing Mandates
  stressTesting: {
    enabled: true,
    frequency: 'weekly', // Weekly stress tests as required
    scenarios: [
      'market_crash_2008',
      'flash_crash_2010',
      'covid_crash_2020',
      'interest_rate_shock',
      'geopolitical_crisis',
      'cyber_attack'
    ],
    confidenceThreshold: 0.95, // 95% confidence level
    maxDrawdownLimit: 15 // Maximum 15% drawdown allowed
  },

  // Audit Trail Requirements
  auditTrail: {
    enabled: true,
    retentionPeriodDays: 2555, // 7 years retention as required by SEC
    compressionEnabled: true, // Compress old data to save storage
    encryptionEnabled: true, // Encrypt sensitive trading data
    immutableStorage: true // Immutable blockchain-style audit trail
  },

  // Regulatory Reporting Requirements
  reporting: {
    enabled: true,
    secReportingEndpoint: process.env.SEC_REPORTING_ENDPOINT,
    euReportingEndpoint: process.env.EU_REPORTING_ENDPOINT,
    reportingSchedule: '0 9 * * 1', // Weekly reports on Monday 9 AM
    realTimeAlertsEnabled: true // Real-time compliance alerts
  }
};

export const DEVELOPMENT_COMPLIANCE_CONFIG: ComplianceConfiguration = {
  ...DEFAULT_COMPLIANCE_CONFIG,
  algorithmicAccountability: {
    ...DEFAULT_COMPLIANCE_CONFIG.algorithmicAccountability,
    reportingInterval: 5, // More frequent reporting for testing
    decisionLoggingLevel: 'standard'
  },
  circuitBreakers: {
    ...DEFAULT_COMPLIANCE_CONFIG.circuitBreakers,
    priceDeviationThreshold: 10.0, // More lenient for development
    timeWindowMs: 60000, // 1-minute window for faster testing
    cooldownPeriodMs: 120000 // 2-minute cooldown for faster iteration
  },
  stressTesting: {
    ...DEFAULT_COMPLIANCE_CONFIG.stressTesting,
    frequency: 'daily', // Daily testing in development
    maxDrawdownLimit: 25 // More lenient for development
  },
  auditTrail: {
    ...DEFAULT_COMPLIANCE_CONFIG.auditTrail,
    retentionPeriodDays: 30, // Shorter retention for development
    compressionEnabled: false, // No compression for easier debugging
    immutableStorage: false // Not immutable for easier testing
  },
  reporting: {
    ...DEFAULT_COMPLIANCE_CONFIG.reporting,
    reportingSchedule: '0 */6 * * *', // Every 6 hours for development
    secReportingEndpoint: 'http://localhost:3001/sec-mock',
    euReportingEndpoint: 'http://localhost:3001/eu-mock'
  }
};

export const PRODUCTION_COMPLIANCE_CONFIG: ComplianceConfiguration = {
  ...DEFAULT_COMPLIANCE_CONFIG,
  algorithmicAccountability: {
    ...DEFAULT_COMPLIANCE_CONFIG.algorithmicAccountability,
    humanOversightThreshold: 0.7 // Stricter oversight in production
  },
  circuitBreakers: {
    ...DEFAULT_COMPLIANCE_CONFIG.circuitBreakers,
    priceDeviationThreshold: 3.0, // Stricter price deviation threshold
    volumeThreshold: 2.5 // Stricter volume threshold
  },
  stressTesting: {
    ...DEFAULT_COMPLIANCE_CONFIG.stressTesting,
    maxDrawdownLimit: 10 // Stricter drawdown limit in production
  }
};

/**
 * Risk Level Thresholds for Compliance
 */
export const RISK_THRESHOLDS = {
  LOW: 0.3,
  MEDIUM: 0.6,
  HIGH: 0.8,
  CRITICAL: 0.95
};

/**
 * Position Size Limits by Asset Class
 */
export const POSITION_LIMITS = {
  EQUITY: 5000000, // $5M max per equity position
  BOND: 10000000, // $10M max per bond position
  COMMODITY: 2000000, // $2M max per commodity position
  FOREX: 15000000, // $15M max per forex position
  CRYPTO: 1000000 // $1M max per crypto position
};

/**
 * Regulatory Reporting Templates
 */
export const REPORTING_TEMPLATES = {
  SEC_ALGORITHMIC: {
    requiredSections: [
      'ALGORITHMIC_DECISIONS',
      'HUMAN_OVERSIGHT',
      'RISK_MANAGEMENT',
      'MODEL_GOVERNANCE'
    ],
    submissionFrequency: 'WEEKLY',
    retentionPeriod: 2555 // 7 years
  },
  EU_CIRCUIT_BREAKER: {
    requiredSections: [
      'CIRCUIT_BREAKER_EVENTS',
      'MARKET_IMPACT_ANALYSIS',
      'TRADING_HALTS',
      'SYSTEM_MONITORING'
    ],
    submissionFrequency: 'WEEKLY',
    retentionPeriod: 1825 // 5 years
  },
  STRESS_TEST: {
    requiredSections: [
      'TEST_SCENARIOS',
      'RESULTS_ANALYSIS',
      'REMEDIATION_ACTIONS',
      'MODEL_VALIDATION'
    ],
    submissionFrequency: 'MONTHLY',
    retentionPeriod: 1825 // 5 years
  }
};

/**
 * Compliance Alert Severity Levels
 */
export const ALERT_SEVERITY = {
  INFO: 'INFO',
  WARNING: 'WARNING',
  ERROR: 'ERROR',
  CRITICAL: 'CRITICAL'
};

/**
 * Model Governance Requirements
 */
export const MODEL_GOVERNANCE = {
  VALIDATION_FREQUENCY: 'QUARTERLY',
  BACKTESTING_PERIOD: 252, // 1 year of trading days
  MIN_SHARPE_RATIO: 0.5,
  MAX_DRAWDOWN: 0.15,
  MIN_WIN_RATE: 0.45
};

/**
 * Circuit Breaker Market Conditions
 */
export const CIRCUIT_BREAKER_CONDITIONS = {
  PRICE_DEVIATION: {
    LEVEL_1: 5.0, // 5% deviation
    LEVEL_2: 10.0, // 10% deviation
    LEVEL_3: 20.0 // 20% deviation (market halt)
  },
  VOLUME_SPIKE: {
    LEVEL_1: 3.0, // 3x normal volume
    LEVEL_2: 5.0, // 5x normal volume
    LEVEL_3: 10.0 // 10x normal volume
  },
  VOLATILITY_SURGE: {
    LEVEL_1: 2.0, // 2x normal volatility
    LEVEL_2: 4.0, // 4x normal volatility
    LEVEL_3: 8.0 // 8x normal volatility
  }
};

/**
 * Get configuration based on environment
 */
export function getComplianceConfig(): ComplianceConfiguration {
  const env = process.env.NODE_ENV || 'development';

  switch (env) {
    case 'production':
      return PRODUCTION_COMPLIANCE_CONFIG;
    case 'development':
      return DEVELOPMENT_COMPLIANCE_CONFIG;
    case 'test':
      return {
        ...DEVELOPMENT_COMPLIANCE_CONFIG,
        auditTrail: {
          ...DEVELOPMENT_COMPLIANCE_CONFIG.auditTrail,
          retentionPeriodDays: 1
        }
      };
    default:
      return DEFAULT_COMPLIANCE_CONFIG;
  }
}