/**
 * Security Configuration Management
 * Centralized configuration for all security components
 */

import { EventEmitter } from 'events';
import crypto from 'crypto';
import {
  SecurityConfig,
  ZeroTrustConfig,
  LoggingConfig,
  ComplianceConfig,
  MonitoringConfig,
  AuditConfig,
  StorageConfig,
  RetentionTier,
  LogLevel
} from '../types';

export class SecurityConfigManager extends EventEmitter {
  private config: SecurityConfig;
  private configHash: string;
  private configVersion: string;

  constructor(initialConfig?: Partial<SecurityConfig>) {
    super();
    this.config = this.createDefaultConfig();
    this.configVersion = '1.0.0';

    if (initialConfig) {
      this.updateConfig(initialConfig);
    }

    this.calculateConfigHash();
  }

  /**
   * Get current security configuration
   */
  getConfig(): SecurityConfig {
    return JSON.parse(JSON.stringify(this.config)); // Deep copy
  }

  /**
   * Update security configuration
   */
  updateConfig(updates: Partial<SecurityConfig>): void {
    const oldConfig = this.getConfig();
    this.config = { ...this.config, ...updates };

    // Validate configuration
    this.validateConfig();

    // Update version and hash
    this.configVersion = this.incrementVersion(this.configVersion);
    this.calculateConfigHash();

    this.emit('config:updated', {
      oldConfig,
      newConfig: this.getConfig(),
      version: this.configVersion,
      hash: this.configHash
    });
  }

  /**
   * Get zero-trust configuration
   */
  getZeroTrustConfig(): ZeroTrustConfig {
    return { ...this.config.zeroTrust };
  }

  /**
   * Update zero-trust configuration
   */
  updateZeroTrustConfig(updates: Partial<ZeroTrustConfig>): void {
    this.updateConfig({
      zeroTrust: { ...this.config.zeroTrust, ...updates }
    });
  }

  /**
   * Get logging configuration
   */
  getLoggingConfig(): LoggingConfig {
    return { ...this.config.logging };
  }

  /**
   * Update logging configuration
   */
  updateLoggingConfig(updates: Partial<LoggingConfig>): void {
    this.updateConfig({
      logging: { ...this.config.logging, ...updates }
    });
  }

  /**
   * Get compliance configuration
   */
  getComplianceConfig(): ComplianceConfig {
    return { ...this.config.compliance };
  }

  /**
   * Update compliance configuration
   */
  updateComplianceConfig(updates: Partial<ComplianceConfig>): void {
    this.updateConfig({
      compliance: { ...this.config.compliance, ...updates }
    });
  }

  /**
   * Get monitoring configuration
   */
  getMonitoringConfig(): MonitoringConfig {
    return { ...this.config.monitoring };
  }

  /**
   * Update monitoring configuration
   */
  updateMonitoringConfig(updates: Partial<MonitoringConfig>): void {
    this.updateConfig({
      monitoring: { ...this.config.monitoring, ...updates }
    });
  }

  /**
   * Get audit configuration
   */
  getAuditConfig(): AuditConfig {
    return { ...this.config.audit };
  }

  /**
   * Update audit configuration
   */
  updateAuditConfig(updates: Partial<AuditConfig>): void {
    this.updateConfig({
      audit: { ...this.config.audit, ...updates }
    });
  }

  /**
   * Get storage configuration
   */
  getStorageConfig(): StorageConfig {
    return { ...this.config.storage };
  }

  /**
   * Update storage configuration
   */
  updateStorageConfig(updates: Partial<StorageConfig>): void {
    this.updateConfig({
      storage: { ...this.config.storage, ...updates }
    });
  }

  /**
   * Load configuration from environment variables
   */
  loadFromEnvironment(): void {
    const envConfig: Partial<SecurityConfig> = {};

    // Zero-Trust Configuration
    if (process.env.ZERO_TRUST_ENABLED !== undefined) {
      envConfig.zeroTrust = {
        ...this.config.zeroTrust,
        enabled: process.env.ZERO_TRUST_ENABLED === 'true',
        strictMode: process.env.ZERO_TRUST_STRICT_MODE === 'true',
        sessionTimeout: parseInt(process.env.ZERO_TRUST_SESSION_TIMEOUT || '3600') * 1000,
        mfaRequired: process.env.ZERO_TRUST_MFA_REQUIRED === 'true',
        deviceTrustRequired: process.env.ZERO_TRUST_DEVICE_TRUST === 'true'
      };
    }

    // Logging Configuration
    if (process.env.LOGGING_ENCRYPTION_ENABLED !== undefined) {
      envConfig.logging = {
        ...this.config.logging,
        encryptionEnabled: process.env.LOGGING_ENCRYPTION_ENABLED === 'true',
        compressionEnabled: process.env.LOGGING_COMPRESSION_ENABLED === 'true',
        realTimeAnalysis: process.env.LOGGING_REALTIME_ANALYSIS === 'true',
        batchSize: parseInt(process.env.LOGGING_BATCH_SIZE || '100'),
        flushInterval: parseInt(process.env.LOGGING_FLUSH_INTERVAL || '30000')
      };
    }

    // Compliance Configuration
    if (process.env.GDPR_ENABLED !== undefined) {
      envConfig.compliance = {
        ...this.config.compliance,
        gdprEnabled: process.env.GDPR_ENABLED === 'true',
        dataMinimization: process.env.GDPR_DATA_MINIMIZATION === 'true',
        automaticDeletion: process.env.GDPR_AUTOMATIC_DELETION === 'true',
        consentManagement: process.env.GDPR_CONSENT_MANAGEMENT === 'true',
        dataPortability: process.env.GDPR_DATA_PORTABILITY === 'true',
        rightToBeForgotten: process.env.GDPR_RIGHT_TO_BE_FORGOTTEN === 'true'
      };
    }

    // Monitoring Configuration
    if (process.env.THREAT_DETECTION_ENABLED !== undefined) {
      envConfig.monitoring = {
        ...this.config.monitoring,
        threatDetection: process.env.THREAT_DETECTION_ENABLED === 'true',
        anomalyDetection: process.env.ANOMALY_DETECTION_ENABLED === 'true',
        realTimeAlerts: process.env.REALTIME_ALERTS_ENABLED === 'true',
        automaticMitigation: process.env.AUTOMATIC_MITIGATION_ENABLED === 'true',
        falsePositiveReduction: process.env.FALSE_POSITIVE_REDUCTION_ENABLED === 'true',
        mlModelsEnabled: process.env.ML_MODELS_ENABLED === 'true'
      };
    }

    // Audit Configuration
    if (process.env.AUDIT_ENABLED !== undefined) {
      envConfig.audit = {
        ...this.config.audit,
        enabled: process.env.AUDIT_ENABLED === 'true',
        realTimeAudit: process.env.AUDIT_REALTIME === 'true',
        complianceReporting: process.env.AUDIT_COMPLIANCE_REPORTING === 'true',
        automaticReports: process.env.AUDIT_AUTOMATIC_REPORTS === 'true',
        retentionPeriod: parseInt(process.env.AUDIT_RETENTION_PERIOD || '2555'),
        encryptionRequired: process.env.AUDIT_ENCRYPTION_REQUIRED === 'true'
      };
    }

    // Storage Configuration
    if (process.env.STORAGE_TIERED_ENABLED !== undefined) {
      envConfig.storage = {
        ...this.config.storage,
        tieredStorage: process.env.STORAGE_TIERED_ENABLED === 'true',
        compression: process.env.STORAGE_COMPRESSION_ENABLED === 'true',
        encryption: process.env.STORAGE_ENCRYPTION_ENABLED === 'true',
        costOptimization: process.env.STORAGE_COST_OPTIMIZATION === 'true'
      };
    }

    if (Object.keys(envConfig).length > 0) {
      this.updateConfig(envConfig);
      this.emit('config:loaded_from_environment', envConfig);
    }
  }

  /**
   * Export configuration to JSON
   */
  exportConfig(): string {
    return JSON.stringify({
      config: this.config,
      version: this.configVersion,
      hash: this.configHash,
      exportedAt: new Date().toISOString()
    }, null, 2);
  }

  /**
   * Import configuration from JSON
   */
  importConfig(configJson: string): void {
    try {
      const imported = JSON.parse(configJson);

      if (imported.config) {
        this.validateConfig(imported.config);
        this.config = imported.config;
        this.configVersion = imported.version || this.incrementVersion(this.configVersion);
        this.calculateConfigHash();

        this.emit('config:imported', {
          version: this.configVersion,
          hash: this.configHash
        });
      } else {
        throw new Error('Invalid configuration format');
      }
    } catch (error) {
      this.emit('config:import_error', { error: error.message });
      throw error;
    }
  }

  /**
   * Get configuration for specific component
   */
  getComponentConfig(component: string): any {
    switch (component) {
      case 'zero-trust':
        return this.getZeroTrustConfig();
      case 'logging':
        return this.getLoggingConfig();
      case 'compliance':
        return this.getComplianceConfig();
      case 'monitoring':
        return this.getMonitoringConfig();
      case 'audit':
        return this.getAuditConfig();
      case 'storage':
        return this.getStorageConfig();
      default:
        throw new Error(`Unknown component: ${component}`);
    }
  }

  /**
   * Validate current configuration
   */
  validateConfig(config?: SecurityConfig): boolean {
    const configToValidate = config || this.config;

    try {
      // Validate zero-trust config
      this.validateZeroTrustConfig(configToValidate.zeroTrust);

      // Validate logging config
      this.validateLoggingConfig(configToValidate.logging);

      // Validate compliance config
      this.validateComplianceConfig(configToValidate.compliance);

      // Validate monitoring config
      this.validateMonitoringConfig(configToValidate.monitoring);

      // Validate audit config
      this.validateAuditConfig(configToValidate.audit);

      // Validate storage config
      this.validateStorageConfig(configToValidate.storage);

      return true;
    } catch (error) {
      this.emit('config:validation_error', { error: error.message });
      throw error;
    }
  }

  /**
   * Get configuration status and health
   */
  getConfigStatus(): {
    version: string;
    hash: string;
    isValid: boolean;
    componentsEnabled: Record<string, boolean>;
    securityLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'MAXIMUM';
    recommendations: string[];
  } {
    const isValid = this.validateConfig();
    const componentsEnabled = {
      zeroTrust: this.config.zeroTrust.enabled,
      logging: this.config.logging.encryptionEnabled,
      compliance: this.config.compliance.gdprEnabled,
      monitoring: this.config.monitoring.threatDetection,
      audit: this.config.audit.enabled,
      storage: this.config.storage.tieredStorage
    };

    const securityLevel = this.calculateSecurityLevel();
    const recommendations = this.generateRecommendations();

    return {
      version: this.configVersion,
      hash: this.configHash,
      isValid,
      componentsEnabled,
      securityLevel,
      recommendations
    };
  }

  private createDefaultConfig(): SecurityConfig {
    return {
      zeroTrust: {
        enabled: true,
        strictMode: false,
        defaultPolicy: 'DENY',
        sessionTimeout: 3600000, // 1 hour
        mfaRequired: true,
        deviceTrustRequired: true,
        riskThresholds: {
          low: 0.3,
          medium: 0.6,
          high: 0.8,
          critical: 0.9
        }
      },
      logging: {
        retentionPeriods: {
          [LogLevel.DEBUG]: 7,
          [LogLevel.INFO]: 30,
          [LogLevel.WARNING]: 90,
          [LogLevel.ERROR]: 180,
          [LogLevel.CRITICAL]: 365
        },
        encryptionEnabled: true,
        compressionEnabled: true,
        realTimeAnalysis: true,
        batchSize: 100,
        flushInterval: 30000 // 30 seconds
      },
      compliance: {
        gdprEnabled: true,
        dataMinimization: true,
        automaticDeletion: true,
        consentManagement: true,
        dataPortability: true,
        rightToBeForgotten: true
      },
      monitoring: {
        threatDetection: true,
        anomalyDetection: true,
        realTimeAlerts: true,
        automaticMitigation: true,
        falsePositiveReduction: true,
        mlModelsEnabled: true
      },
      audit: {
        enabled: true,
        realTimeAudit: true,
        complianceReporting: true,
        automaticReports: true,
        retentionPeriod: 2555, // 7 years
        encryptionRequired: true
      },
      storage: {
        tieredStorage: true,
        compression: true,
        encryption: true,
        costOptimization: true,
        archivalPolicy: {
          autoArchive: true,
          archiveAfterDays: 90,
          deleteAfterDays: 2555,
          compressionLevel: 9
        }
      }
    };
  }

  private validateZeroTrustConfig(config: ZeroTrustConfig): void {
    if (config.sessionTimeout < 300000) { // 5 minutes minimum
      throw new Error('Session timeout must be at least 5 minutes');
    }

    if (config.riskThresholds.critical <= config.riskThresholds.high) {
      throw new Error('Critical risk threshold must be higher than high threshold');
    }
  }

  private validateLoggingConfig(config: LoggingConfig): void {
    if (config.batchSize < 1 || config.batchSize > 10000) {
      throw new Error('Batch size must be between 1 and 10000');
    }

    if (config.flushInterval < 1000) { // 1 second minimum
      throw new Error('Flush interval must be at least 1 second');
    }

    // Validate retention periods
    for (const [level, days] of Object.entries(config.retentionPeriods)) {
      if (days < 1 || days > 3650) {
        throw new Error(`Retention period for ${level} must be between 1 and 3650 days`);
      }
    }
  }

  private validateComplianceConfig(config: ComplianceConfig): void {
    if (config.gdprEnabled && !config.consentManagement) {
      throw new Error('GDPR requires consent management to be enabled');
    }
  }

  private validateMonitoringConfig(config: MonitoringConfig): void {
    if (config.automaticMitigation && !config.threatDetection) {
      throw new Error('Automatic mitigation requires threat detection to be enabled');
    }
  }

  private validateAuditConfig(config: AuditConfig): void {
    if (config.retentionPeriod < 365) {
      throw new Error('Audit retention period must be at least 1 year for compliance');
    }
  }

  private validateStorageConfig(config: StorageConfig): void {
    if (config.archivalPolicy.archiveAfterDays >= config.archivalPolicy.deleteAfterDays) {
      throw new Error('Archive period must be less than deletion period');
    }

    if (config.archivalPolicy.compressionLevel < 1 || config.archivalPolicy.compressionLevel > 9) {
      throw new Error('Compression level must be between 1 and 9');
    }
  }

  private calculateConfigHash(): void {
    this.configHash = crypto
      .createHash('sha256')
      .update(JSON.stringify(this.config))
      .digest('hex')
      .substring(0, 16);
  }

  private incrementVersion(version: string): string {
    const parts = version.split('.');
    const patch = parseInt(parts[2]) + 1;
    return `${parts[0]}.${parts[1]}.${patch}`;
  }

  private calculateSecurityLevel(): 'LOW' | 'MEDIUM' | 'HIGH' | 'MAXIMUM' {
    let score = 0;

    // Zero-trust scoring
    if (this.config.zeroTrust.enabled) score += 20;
    if (this.config.zeroTrust.strictMode) score += 10;
    if (this.config.zeroTrust.mfaRequired) score += 15;
    if (this.config.zeroTrust.deviceTrustRequired) score += 10;

    // Logging scoring
    if (this.config.logging.encryptionEnabled) score += 10;
    if (this.config.logging.realTimeAnalysis) score += 5;

    // Monitoring scoring
    if (this.config.monitoring.threatDetection) score += 15;
    if (this.config.monitoring.anomalyDetection) score += 10;
    if (this.config.monitoring.automaticMitigation) score += 5;

    // Audit scoring
    if (this.config.audit.enabled) score += 10;
    if (this.config.audit.encryptionRequired) score += 5;

    if (score >= 90) return 'MAXIMUM';
    if (score >= 70) return 'HIGH';
    if (score >= 50) return 'MEDIUM';
    return 'LOW';
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    if (!this.config.zeroTrust.strictMode) {
      recommendations.push('Enable zero-trust strict mode for maximum security');
    }

    if (!this.config.monitoring.mlModelsEnabled) {
      recommendations.push('Enable ML models for improved threat detection');
    }

    if (!this.config.storage.costOptimization) {
      recommendations.push('Enable storage cost optimization to reduce expenses');
    }

    if (this.config.logging.flushInterval > 60000) {
      recommendations.push('Consider reducing log flush interval for better real-time monitoring');
    }

    if (!this.config.compliance.dataMinimization) {
      recommendations.push('Enable data minimization for better privacy compliance');
    }

    return recommendations;
  }

  /**
   * Reset to default configuration
   */
  resetToDefaults(): void {
    const oldConfig = this.getConfig();
    this.config = this.createDefaultConfig();
    this.configVersion = '1.0.0';
    this.calculateConfigHash();

    this.emit('config:reset_to_defaults', {
      oldConfig,
      newConfig: this.getConfig()
    });
  }

  /**
   * Get configuration differences
   */
  compareConfigs(otherConfig: SecurityConfig): {
    differences: Record<string, { current: any; other: any }>;
    identical: boolean;
  } {
    const differences: Record<string, { current: any; other: any }> = {};
    const identical = this.findDifferences('', this.config, otherConfig, differences);

    return { differences, identical: Object.keys(differences).length === 0 };
  }

  private findDifferences(
    path: string,
    current: any,
    other: any,
    differences: Record<string, { current: any; other: any }>
  ): boolean {
    if (typeof current !== typeof other) {
      differences[path] = { current, other };
      return false;
    }

    if (typeof current === 'object' && current !== null) {
      const currentKeys = Object.keys(current);
      const otherKeys = Object.keys(other);

      const allKeys = new Set([...currentKeys, ...otherKeys]);

      for (const key of allKeys) {
        const newPath = path ? `${path}.${key}` : key;

        if (!(key in current)) {
          differences[newPath] = { current: undefined, other: other[key] };
        } else if (!(key in other)) {
          differences[newPath] = { current: current[key], other: undefined };
        } else {
          this.findDifferences(newPath, current[key], other[key], differences);
        }
      }
    } else if (current !== other) {
      differences[path] = { current, other };
    }

    return Object.keys(differences).length === 0;
  }

  /**
   * Get current configuration version
   */
  getVersion(): string {
    return this.configVersion;
  }

  /**
   * Get current configuration hash
   */
  getHash(): string {
    return this.configHash;
  }
}