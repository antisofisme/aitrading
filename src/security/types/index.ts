/**
 * Zero-Trust Security Architecture Types
 * Comprehensive type definitions for security framework
 */

// Core Security Types
export interface SecurityContext {
  userId: string;
  sessionId: string;
  deviceFingerprint: string;
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  trustScore: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  permissions: Permission[];
  mfaVerified: boolean;
  lastVerification: Date;
}

export interface Permission {
  resource: string;
  action: string;
  conditions?: Record<string, any>;
  expiresAt?: Date;
  grantedBy: string;
  grantedAt: Date;
}

// Zero-Trust Framework
export interface ZeroTrustPolicy {
  id: string;
  name: string;
  description: string;
  conditions: PolicyCondition[];
  actions: PolicyAction[];
  priority: number;
  enabled: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface PolicyCondition {
  type: 'USER' | 'DEVICE' | 'LOCATION' | 'TIME' | 'BEHAVIOR' | 'RISK_SCORE';
  operator: 'EQUALS' | 'NOT_EQUALS' | 'GREATER_THAN' | 'LESS_THAN' | 'CONTAINS' | 'IN' | 'NOT_IN';
  value: any;
  negate?: boolean;
}

export interface PolicyAction {
  type: 'ALLOW' | 'DENY' | 'REQUIRE_MFA' | 'STEP_UP_AUTH' | 'LOG' | 'ALERT' | 'QUARANTINE';
  parameters?: Record<string, any>;
}

// Logging System Types
export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  category: LogCategory;
  message: string;
  metadata: Record<string, any>;
  userId?: string;
  sessionId?: string;
  sourceComponent: string;
  environment: string;
  retentionTier: RetentionTier;
  encrypted: boolean;
  errorDNA?: ErrorDNA;
}

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR',
  CRITICAL = 'CRITICAL'
}

export enum LogCategory {
  SECURITY = 'SECURITY',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  PERFORMANCE = 'PERFORMANCE',
  BUSINESS = 'BUSINESS',
  SYSTEM = 'SYSTEM',
  AUDIT = 'AUDIT',
  COMPLIANCE = 'COMPLIANCE'
}

export enum RetentionTier {
  HOT = 'HOT',      // Immediate access - 7 days for DEBUG, 30 days for INFO
  WARM = 'WARM',    // Slower access - 90 days for WARNING
  COLD = 'COLD',    // Archive access - 180 days for ERROR
  FROZEN = 'FROZEN' // Deep archive - 365 days for CRITICAL
}

// ErrorDNA System
export interface ErrorDNA {
  id: string;
  pattern: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  frequency: number;
  firstOccurrence: Date;
  lastOccurrence: Date;
  affectedComponents: string[];
  rootCauseAnalysis?: RootCauseAnalysis;
  resolutionSteps?: string[];
  preventionStrategy?: string;
  businessImpact: BusinessImpact;
}

export enum ErrorCategory {
  AUTHENTICATION_FAILURE = 'AUTHENTICATION_FAILURE',
  AUTHORIZATION_DENIED = 'AUTHORIZATION_DENIED',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  SYSTEM_ERROR = 'SYSTEM_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  DATABASE_ERROR = 'DATABASE_ERROR',
  EXTERNAL_SERVICE_ERROR = 'EXTERNAL_SERVICE_ERROR',
  PERFORMANCE_DEGRADATION = 'PERFORMANCE_DEGRADATION',
  SECURITY_THREAT = 'SECURITY_THREAT',
  COMPLIANCE_VIOLATION = 'COMPLIANCE_VIOLATION'
}

export enum ErrorSeverity {
  LOW = 1,
  MEDIUM = 2,
  HIGH = 3,
  CRITICAL = 4,
  CATASTROPHIC = 5
}

export interface RootCauseAnalysis {
  primaryCause: string;
  contributingFactors: string[];
  timeline: TimelineEvent[];
  affectedSystems: string[];
  dataLoss: boolean;
  securityImpact: boolean;
}

export interface TimelineEvent {
  timestamp: Date;
  event: string;
  component: string;
  impact: string;
}

export interface BusinessImpact {
  usersAffected: number;
  revenueImpact: number;
  reputationRisk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  complianceRisk: boolean;
  slaViolation: boolean;
}

// GDPR Compliance
export interface GDPRDataSubject {
  id: string;
  email: string;
  consentGiven: boolean;
  consentTimestamp: Date;
  consentVersion: string;
  dataCategories: DataCategory[];
  retentionPeriod: number;
  lastActivity: Date;
  rightToBeForgotten: boolean;
  dataPortabilityRequested: boolean;
}

export enum DataCategory {
  PERSONAL_IDENTIFIERS = 'PERSONAL_IDENTIFIERS',
  CONTACT_INFORMATION = 'CONTACT_INFORMATION',
  BEHAVIORAL_DATA = 'BEHAVIORAL_DATA',
  FINANCIAL_DATA = 'FINANCIAL_DATA',
  LOCATION_DATA = 'LOCATION_DATA',
  BIOMETRIC_DATA = 'BIOMETRIC_DATA',
  HEALTH_DATA = 'HEALTH_DATA',
  GENETIC_DATA = 'GENETIC_DATA'
}

export interface DataProcessingRecord {
  id: string;
  subjectId: string;
  purpose: string;
  legalBasis: LegalBasis;
  dataCategories: DataCategory[];
  processors: string[];
  thirdCountryTransfers: ThirdCountryTransfer[];
  retentionPeriod: number;
  timestamp: Date;
  automated: boolean;
}

export enum LegalBasis {
  CONSENT = 'CONSENT',
  CONTRACT = 'CONTRACT',
  LEGAL_OBLIGATION = 'LEGAL_OBLIGATION',
  VITAL_INTERESTS = 'VITAL_INTERESTS',
  PUBLIC_TASK = 'PUBLIC_TASK',
  LEGITIMATE_INTERESTS = 'LEGITIMATE_INTERESTS'
}

export interface ThirdCountryTransfer {
  country: string;
  adequacyDecision: boolean;
  safeguards: string[];
  timestamp: Date;
}

// Security Monitoring
export interface ThreatEvent {
  id: string;
  timestamp: Date;
  type: ThreatType;
  severity: ThreatSeverity;
  source: ThreatSource;
  target: string;
  description: string;
  indicators: ThreatIndicator[];
  mitigationActions: MitigationAction[];
  resolved: boolean;
  falsePositive: boolean;
}

export enum ThreatType {
  BRUTE_FORCE_ATTACK = 'BRUTE_FORCE_ATTACK',
  SQL_INJECTION = 'SQL_INJECTION',
  XSS_ATTACK = 'XSS_ATTACK',
  CSRF_ATTACK = 'CSRF_ATTACK',
  DATA_EXFILTRATION = 'DATA_EXFILTRATION',
  PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION',
  MALWARE_DETECTED = 'MALWARE_DETECTED',
  SUSPICIOUS_BEHAVIOR = 'SUSPICIOUS_BEHAVIOR',
  UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS',
  DDoS_ATTACK = 'DDoS_ATTACK'
}

export enum ThreatSeverity {
  INFO = 'INFO',
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export interface ThreatSource {
  ip: string;
  geolocation?: Geolocation;
  userAgent?: string;
  userId?: string;
  reputation: number;
  previousThreatHistory: boolean;
}

export interface Geolocation {
  country: string;
  region: string;
  city: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export interface ThreatIndicator {
  type: string;
  value: string;
  confidence: number;
  source: string;
}

export interface MitigationAction {
  action: string;
  timestamp: Date;
  automated: boolean;
  effectiveness: number;
  description: string;
}

// Audit Trail
export interface AuditEvent {
  id: string;
  timestamp: Date;
  userId: string;
  userRole: string;
  action: string;
  resource: string;
  outcome: 'SUCCESS' | 'FAILURE' | 'PARTIAL';
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  sessionId: string;
  riskScore: number;
  complianceRelevant: boolean;
  retentionRequirement: number;
}

// Cost Optimization
export interface StorageMetrics {
  totalSize: number;
  compressedSize: number;
  compressionRatio: number;
  tierDistribution: Record<RetentionTier, number>;
  costPerTier: Record<RetentionTier, number>;
  totalCost: number;
  costReduction: number;
  accessPatterns: AccessPattern[];
}

export interface AccessPattern {
  tier: RetentionTier;
  accessFrequency: number;
  averageAccessTime: number;
  peakAccessHours: number[];
  accessCost: number;
}

// Configuration Types
export interface SecurityConfig {
  zeroTrust: ZeroTrustConfig;
  logging: LoggingConfig;
  compliance: ComplianceConfig;
  monitoring: MonitoringConfig;
  audit: AuditConfig;
  storage: StorageConfig;
}

export interface ZeroTrustConfig {
  enabled: boolean;
  strictMode: boolean;
  defaultPolicy: 'DENY' | 'ALLOW_WITH_CONDITIONS';
  sessionTimeout: number;
  mfaRequired: boolean;
  deviceTrustRequired: boolean;
  riskThresholds: Record<string, number>;
}

export interface LoggingConfig {
  retentionPeriods: Record<LogLevel, number>;
  encryptionEnabled: boolean;
  compressionEnabled: boolean;
  realTimeAnalysis: boolean;
  batchSize: number;
  flushInterval: number;
}

export interface ComplianceConfig {
  gdprEnabled: boolean;
  dataMinimization: boolean;
  automaticDeletion: boolean;
  consentManagement: boolean;
  dataPortability: boolean;
  rightToBeForgotten: boolean;
}

export interface MonitoringConfig {
  threatDetection: boolean;
  anomalyDetection: boolean;
  realTimeAlerts: boolean;
  automaticMitigation: boolean;
  falsePositiveReduction: boolean;
  mlModelsEnabled: boolean;
}

export interface AuditConfig {
  enabled: boolean;
  realTimeAudit: boolean;
  complianceReporting: boolean;
  automaticReports: boolean;
  retentionPeriod: number;
  encryptionRequired: boolean;
}

export interface StorageConfig {
  tieredStorage: boolean;
  compression: boolean;
  encryption: boolean;
  costOptimization: boolean;
  archivalPolicy: ArchivalPolicy;
}

export interface ArchivalPolicy {
  autoArchive: boolean;
  archiveAfterDays: number;
  deleteAfterDays: number;
  compressionLevel: number;
}