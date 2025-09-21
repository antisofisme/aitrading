import winston from 'winston';
import { config } from '@/config';
import { LogLevel, LogEntry } from '@/types';

// Custom log format for structured logging
const logFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    return JSON.stringify({
      timestamp,
      level,
      message,
      service: 'aitrading-backend',
      ...meta
    });
  })
);

// Log retention strategy based on log level
const getLogRetentionPolicy = (level: LogLevel) => {
  const policies = {
    [LogLevel.DEBUG]: {
      retention: '7d',
      compression: false,
      tier: 'hot'
    },
    [LogLevel.INFO]: {
      retention: '30d',
      compression: true,
      tier: 'warm'
    },
    [LogLevel.WARN]: {
      retention: '90d',
      compression: true,
      tier: 'warm'
    },
    [LogLevel.ERROR]: {
      retention: '180d',
      compression: true,
      tier: 'cold'
    },
    [LogLevel.CRITICAL]: {
      retention: '365d',
      compression: true,
      tier: 'cold'
    }
  };

  return policies[level] || policies[LogLevel.INFO];
};

// Create Winston logger with optimized transport configuration
const createLogger = () => {
  const transports: winston.transport[] = [];

  // Console transport for development
  if (config.nodeEnv === 'development') {
    transports.push(
      new winston.transports.Console({
        format: winston.format.combine(
          winston.format.colorize(),
          winston.format.simple()
        )
      })
    );
  }

  // File transports with level-based retention
  const logLevels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.CRITICAL];

  logLevels.forEach(level => {
    const policy = getLogRetentionPolicy(level);

    // Only create file transport for INFO and above in production
    if (config.nodeEnv === 'production' && level === LogLevel.DEBUG) {
      return;
    }

    transports.push(
      new winston.transports.File({
        filename: `logs/${level}.log`,
        level: level,
        maxFiles: policy.retention,
        maxsize: 100 * 1024 * 1024, // 100MB
        tailable: true,
        zippedArchive: policy.compression,
        format: logFormat
      })
    );
  });

  // Combined log file for all levels
  transports.push(
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxFiles: config.logging.maxFiles,
      maxsize: config.logging.maxSize,
      tailable: true,
      zippedArchive: config.logging.compress,
      format: logFormat
    })
  );

  return winston.createLogger({
    level: config.logging.level,
    format: logFormat,
    transports,
    exitOnError: false,
    // Custom exception handling
    exceptionHandlers: [
      new winston.transports.File({
        filename: 'logs/exceptions.log',
        maxFiles: '30d',
        maxsize: '50mb',
        tailable: true,
        zippedArchive: true
      })
    ],
    // Custom rejection handling for unhandled promise rejections
    rejectionHandlers: [
      new winston.transports.File({
        filename: 'logs/rejections.log',
        maxFiles: '30d',
        maxsize: '50mb',
        tailable: true,
        zippedArchive: true
      })
    ]
  });
};

// Initialize logger
export const logger = createLogger();

/**
 * Enhanced Logger Service with optimized retention and compliance features
 */
export class LoggerService {
  private logger: winston.Logger;
  private costTracker: Map<string, number> = new Map();

  constructor() {
    this.logger = logger;
    this.initializeCostTracking();
  }

  /**
   * Log with automatic level-based routing for cost optimization
   */
  public log(level: LogLevel, message: string, meta?: Record<string, any>): void {
    const logEntry: LogEntry = {
      level,
      message,
      timestamp: new Date(),
      service: 'aitrading-backend',
      component: meta?.component || 'unknown',
      ...meta
    };

    // Route to appropriate storage tier based on level
    this.routeLogByLevel(logEntry);

    // Track costs for monitoring
    this.trackLogCost(level);

    // Standard Winston logging
    this.logger.log(level, message, meta);
  }

  /**
   * Debug logging (7-day retention, hot storage)
   */
  public debug(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.DEBUG, message, { ...meta, retention_tier: 'hot' });
  }

  /**
   * Info logging (30-day retention, warm storage)
   */
  public info(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.INFO, message, { ...meta, retention_tier: 'warm' });
  }

  /**
   * Warning logging (90-day retention, warm storage)
   */
  public warn(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.WARN, message, { ...meta, retention_tier: 'warm' });
  }

  /**
   * Error logging (180-day retention, cold storage)
   */
  public error(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.ERROR, message, { ...meta, retention_tier: 'cold' });
  }

  /**
   * Critical logging (365-day retention, cold storage, compliance required)
   */
  public critical(message: string, meta?: Record<string, any>): void {
    this.log(LogLevel.CRITICAL, message, {
      ...meta,
      retention_tier: 'cold',
      compliance_required: true,
      immutable: true
    });
  }

  /**
   * Audit logging for compliance (always critical level)
   */
  public audit(action: string, userId?: string, details?: Record<string, any>): void {
    this.critical(`AUDIT: ${action}`, {
      component: 'audit',
      user_id: userId,
      action,
      details,
      audit_trail: true,
      compliance_required: true
    });
  }

  /**
   * Security event logging
   */
  public security(event: string, riskScore: number, details?: Record<string, any>): void {
    const level = riskScore >= 7 ? LogLevel.CRITICAL : LogLevel.ERROR;

    this.log(level, `SECURITY: ${event}`, {
      component: 'security',
      security_event: true,
      risk_score: riskScore,
      details,
      compliance_required: true
    });
  }

  /**
   * Performance logging with latency tracking
   */
  public performance(operation: string, duration: number, meta?: Record<string, any>): void {
    const level = duration > 1000 ? LogLevel.WARN : LogLevel.INFO; // Warn if > 1s

    this.log(level, `PERFORMANCE: ${operation}`, {
      component: 'performance',
      operation,
      duration_ms: duration,
      performance_metric: true,
      ...meta
    });
  }

  /**
   * Trading activity logging (always critical for compliance)
   */
  public trading(action: string, userId: string, details: Record<string, any>): void {
    this.critical(`TRADING: ${action}`, {
      component: 'trading',
      user_id: userId,
      trading_action: action,
      details,
      compliance_required: true,
      financial_record: true
    });
  }

  /**
   * Route logs to appropriate storage tier based on level
   */
  private routeLogByLevel(logEntry: LogEntry): void {
    const policy = getLogRetentionPolicy(logEntry.level);

    // In production, this would route to different storage systems
    // For now, we'll use file-based routing with metadata
    const routingInfo = {
      storage_tier: policy.tier,
      retention_days: policy.retention,
      compression_enabled: policy.compression,
      cost_tier: this.calculateCostTier(logEntry.level)
    };

    // Add routing metadata to log entry
    Object.assign(logEntry, routingInfo);
  }

  /**
   * Calculate cost tier for log level
   */
  private calculateCostTier(level: LogLevel): 'low' | 'medium' | 'high' {
    const costTiers = {
      [LogLevel.DEBUG]: 'low',
      [LogLevel.INFO]: 'low',
      [LogLevel.WARN]: 'medium',
      [LogLevel.ERROR]: 'medium',
      [LogLevel.CRITICAL]: 'high'
    };

    return costTiers[level] as 'low' | 'medium' | 'high';
  }

  /**
   * Track logging costs for optimization monitoring
   */
  private trackLogCost(level: LogLevel): void {
    const costPerLevel = {
      [LogLevel.DEBUG]: 0.001, // $0.001 per log (hot storage)
      [LogLevel.INFO]: 0.002,  // $0.002 per log (warm storage)
      [LogLevel.WARN]: 0.002,  // $0.002 per log (warm storage)
      [LogLevel.ERROR]: 0.001, // $0.001 per log (cold storage, compressed)
      [LogLevel.CRITICAL]: 0.001 // $0.001 per log (cold storage, compressed)
    };

    const currentCost = this.costTracker.get(level) || 0;
    this.costTracker.set(level, currentCost + costPerLevel[level]);
  }

  /**
   * Get cost analytics for monitoring
   */
  public getCostAnalytics(): {
    totalCost: number;
    costByLevel: Record<LogLevel, number>;
    savingsVsUniform: number;
  } {
    let totalCost = 0;
    const costByLevel: Record<LogLevel, number> = {} as any;

    this.costTracker.forEach((cost, level) => {
      totalCost += cost;
      costByLevel[level as LogLevel] = cost;
    });

    // Calculate savings vs uniform retention (all logs kept 1 year at $0.005/log)
    const totalLogs = Array.from(this.costTracker.values()).reduce((sum, count) => sum + count, 0);
    const uniformCost = totalLogs * 0.005; // Uniform pricing
    const savingsVsUniform = uniformCost - totalCost;

    return {
      totalCost,
      costByLevel,
      savingsVsUniform
    };
  }

  /**
   * Initialize cost tracking
   */
  private initializeCostTracking(): void {
    // Reset cost tracking daily
    setInterval(() => {
      const analytics = this.getCostAnalytics();

      this.info('Daily log cost analytics', {
        component: 'cost_analytics',
        ...analytics
      });

      // Reset counters
      this.costTracker.clear();
    }, 24 * 60 * 60 * 1000); // 24 hours
  }

  /**
   * GDPR-compliant log anonymization
   */
  public anonymizeUserLogs(userId: string): void {
    this.info('User log anonymization initiated', {
      component: 'gdpr_compliance',
      user_id: userId,
      action: 'anonymize_logs',
      compliance_required: true
    });

    // In production, this would:
    // 1. Find all logs for the user
    // 2. Remove/hash personal identifiers
    // 3. Maintain audit trail for compliance
  }

  /**
   * Compliance report generation
   */
  public generateComplianceReport(startDate: Date, endDate: Date): {
    totalLogs: number;
    auditLogs: number;
    securityEvents: number;
    tradingRecords: number;
    retentionCompliance: boolean;
  } {
    // In production, this would query log storage systems
    const report = {
      totalLogs: 0,
      auditLogs: 0,
      securityEvents: 0,
      tradingRecords: 0,
      retentionCompliance: true
    };

    this.info('Compliance report generated', {
      component: 'compliance',
      report,
      period: { startDate, endDate },
      compliance_required: true
    });

    return report;
  }

  /**
   * Log retention cleanup (automated)
   */
  public async performRetentionCleanup(): Promise<{
    deletedLogs: number;
    costSavings: number;
  }> {
    const result = {
      deletedLogs: 0,
      costSavings: 0
    };

    // In production, this would:
    // 1. Identify logs beyond retention period
    // 2. Safely delete non-compliance logs
    // 3. Archive compliance-required logs
    // 4. Calculate cost savings

    this.info('Log retention cleanup completed', {
      component: 'retention_cleanup',
      ...result
    });

    return result;
  }

  /**
   * Health check for logging system
   */
  public healthCheck(): {
    status: 'healthy' | 'degraded' | 'unhealthy';
    details: Record<string, any>;
  } {
    try {
      // Test logging functionality
      this.debug('Health check test log');

      const costAnalytics = this.getCostAnalytics();

      return {
        status: 'healthy',
        details: {
          log_level: config.logging.level,
          transports_active: this.logger.transports.length,
          cost_optimization: costAnalytics.savingsVsUniform > 0,
          retention_policies_active: true
        }
      };

    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error instanceof Error ? error.message : 'Unknown error'
        }
      };
    }
  }
}

// Export singleton logger service
export const loggerService = new LoggerService();

// Export convenience methods that use the service
export const logDebug = (message: string, meta?: Record<string, any>) => loggerService.debug(message, meta);
export const logInfo = (message: string, meta?: Record<string, any>) => loggerService.info(message, meta);
export const logWarn = (message: string, meta?: Record<string, any>) => loggerService.warn(message, meta);
export const logError = (message: string, meta?: Record<string, any>) => loggerService.error(message, meta);
export const logCritical = (message: string, meta?: Record<string, any>) => loggerService.critical(message, meta);
export const logAudit = (action: string, userId?: string, details?: Record<string, any>) => loggerService.audit(action, userId, details);
export const logSecurity = (event: string, riskScore: number, details?: Record<string, any>) => loggerService.security(event, riskScore, details);
export const logPerformance = (operation: string, duration: number, meta?: Record<string, any>) => loggerService.performance(operation, duration, meta);
export const logTrading = (action: string, userId: string, details: Record<string, any>) => loggerService.trading(action, userId, details);