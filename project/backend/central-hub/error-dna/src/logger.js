const winston = require('winston');
const path = require('path');

class ErrorLogger {
  constructor(config = {}) {
    this.config = {
      level: config.level || 'info',
      format: config.format || 'json',
      maxFiles: config.maxFiles || 5,
      maxSize: config.maxSize || '10m',
      datePattern: config.datePattern || 'YYYY-MM-DD',
      filename: config.filename || 'error-dna-%DATE%.log',
      baseDir: config.baseDir || path.join(__dirname, '..', 'storage'),
      ...config
    };

    this.logger = this._createLogger();
  }

  /**
   * Log an error with full context
   * @param {Object} errorData - Complete error data
   */
  logError(errorData) {
    const logEntry = {
      level: 'error',
      message: errorData.originalError?.message || 'Unknown error',
      timestamp: new Date().toISOString(),
      errorId: errorData.id,
      category: errorData.categorization?.category,
      subcategory: errorData.categorization?.subcategory,
      severity: errorData.categorization?.severity,
      patterns: errorData.patterns?.map(p => p.id) || [],
      metadata: {
        source: errorData.categorization?.metadata?.source,
        confidence: errorData.categorization?.confidence,
        tags: errorData.categorization?.tags,
        ...errorData.metadata
      },
      originalError: {
        name: errorData.originalError?.name,
        message: errorData.originalError?.message,
        code: errorData.originalError?.code,
        stack: errorData.originalError?.stack
      }
    };

    this.logger.error(logEntry);
  }

  /**
   * Log pattern detection events
   * @param {Object} patternData - Pattern detection result
   */
  logPattern(patternData) {
    const logEntry = {
      level: 'info',
      message: 'Pattern detected',
      timestamp: new Date().toISOString(),
      event: 'pattern_detection',
      patterns: {
        new: patternData.newPatterns?.length || 0,
        existing: patternData.existingPatterns?.length || 0,
        anomalies: patternData.anomalies?.length || 0
      },
      details: patternData
    };

    this.logger.info(logEntry);
  }

  /**
   * Log system events and metrics
   * @param {string} event - Event name
   * @param {Object} data - Event data
   * @param {string} level - Log level
   */
  logEvent(event, data = {}, level = 'info') {
    const logEntry = {
      level,
      message: `System event: ${event}`,
      timestamp: new Date().toISOString(),
      event,
      ...data
    };

    this.logger.log(level, logEntry);
  }

  /**
   * Log recovery attempts and results
   * @param {Object} recoveryData - Recovery attempt data
   */
  logRecovery(recoveryData) {
    const logEntry = {
      level: recoveryData.success ? 'info' : 'warn',
      message: `Recovery attempt ${recoveryData.success ? 'successful' : 'failed'}`,
      timestamp: new Date().toISOString(),
      event: 'error_recovery',
      strategy: recoveryData.strategy,
      attempt: recoveryData.attempt,
      success: recoveryData.success,
      errorId: recoveryData.errorId,
      details: recoveryData.details
    };

    this.logger.log(logEntry.level, logEntry);
  }

  /**
   * Log notification events
   * @param {Object} notificationData - Notification data
   */
  logNotification(notificationData) {
    const logEntry = {
      level: 'info',
      message: 'Notification sent',
      timestamp: new Date().toISOString(),
      event: 'notification',
      channel: notificationData.channel,
      recipient: notificationData.recipient,
      success: notificationData.success,
      errorId: notificationData.errorId,
      details: notificationData.details
    };

    this.logger.info(logEntry);
  }

  /**
   * Log performance metrics
   * @param {Object} metrics - Performance metrics
   */
  logMetrics(metrics) {
    const logEntry = {
      level: 'info',
      message: 'Performance metrics',
      timestamp: new Date().toISOString(),
      event: 'metrics',
      ...metrics
    };

    this.logger.info(logEntry);
  }

  /**
   * Log integration events (Central Hub, Import Manager)
   * @param {string} service - Service name
   * @param {string} operation - Operation performed
   * @param {Object} result - Operation result
   */
  logIntegration(service, operation, result) {
    const logEntry = {
      level: result.success ? 'info' : 'error',
      message: `Integration ${operation} with ${service}`,
      timestamp: new Date().toISOString(),
      event: 'integration',
      service,
      operation,
      success: result.success,
      duration: result.duration,
      details: result.details
    };

    this.logger.log(logEntry.level, logEntry);
  }

  /**
   * Get recent logs
   * @param {Object} options - Query options
   * @returns {Promise<Array>} - Array of log entries
   */
  async getRecentLogs(options = {}) {
    // This is a simplified implementation
    // In a real scenario, you might want to query log files or use a log aggregation service
    return [];
  }

  /**
   * Create Winston logger instance
   * @private
   */
  _createLogger() {
    const logDir = this.config.baseDir;

    return winston.createLogger({
      level: this.config.level,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        this.config.format === 'json'
          ? winston.format.json()
          : winston.format.simple()
      ),
      transports: [
        // Console transport for development
        new winston.transports.Console({
          level: 'debug',
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),

        // File transport for errors
        new winston.transports.File({
          filename: path.join(logDir, 'error.log'),
          level: 'error',
          maxsize: this._parseSize(this.config.maxSize),
          maxFiles: this.config.maxFiles
        }),

        // File transport for all logs
        new winston.transports.File({
          filename: path.join(logDir, 'combined.log'),
          maxsize: this._parseSize(this.config.maxSize),
          maxFiles: this.config.maxFiles
        })
      ],

      // Handle uncaught exceptions
      exceptionHandlers: [
        new winston.transports.File({
          filename: path.join(logDir, 'exceptions.log')
        })
      ],

      // Handle unhandled promise rejections
      rejectionHandlers: [
        new winston.transports.File({
          filename: path.join(logDir, 'rejections.log')
        })
      ]
    });
  }

  /**
   * Parse size string to bytes
   * @private
   */
  _parseSize(sizeStr) {
    const units = {
      'b': 1,
      'k': 1024,
      'm': 1024 * 1024,
      'g': 1024 * 1024 * 1024
    };

    const match = sizeStr.toLowerCase().match(/^(\d+)([bkmg]?)$/);
    if (!match) return 10 * 1024 * 1024; // Default 10MB

    const size = parseInt(match[1]);
    const unit = match[2] || 'b';

    return size * units[unit];
  }

  /**
   * Get logger instance for external use
   */
  getLogger() {
    return this.logger;
  }
}

module.exports = ErrorLogger;