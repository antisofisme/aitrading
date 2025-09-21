const fs = require('fs-extra');
const path = require('path');
const winston = require('winston');

class ErrorStorage {
  constructor(config = {}) {
    this.config = {
      baseDir: config.baseDir || path.join(__dirname, '..', 'storage'),
      errorLogFile: config.errorLogFile || 'errors.json',
      patternFile: config.patternFile || 'patterns.json',
      metricsFile: config.metricsFile || 'metrics.json',
      maxFileSize: config.maxFileSize || '10MB',
      retentionDays: config.retentionDays || 30,
      ...config
    };

    this.errorLogPath = path.join(this.config.baseDir, this.config.errorLogFile);
    this.patternPath = path.join(this.config.baseDir, this.config.patternFile);
    this.metricsPath = path.join(this.config.baseDir, this.config.metricsFile);

    this.logger = this._setupLogger();
    this.init();
  }

  /**
   * Initialize storage system
   */
  async init() {
    try {
      // Ensure storage directory exists
      await fs.ensureDir(this.config.baseDir);

      // Initialize storage files if they don't exist
      await this._initializeStorageFiles();

      console.log('ErrorStorage initialized successfully');
    } catch (error) {
      console.error('Failed to initialize ErrorStorage:', error);
      throw error;
    }
  }

  /**
   * Store an error with categorization and pattern info
   * @param {Object} errorData - Complete error data
   * @returns {Promise<string>} - Stored error ID
   */
  async storeError(errorData) {
    try {
      const errorEntry = {
        id: errorData.id || this._generateId(),
        timestamp: new Date().toISOString(),
        originalError: errorData.originalError,
        categorization: errorData.categorization,
        patterns: errorData.patterns || [],
        metadata: {
          ...errorData.metadata,
          stored: true,
          storageVersion: '1.0'
        }
      };

      // Store in JSON file
      await this._appendToFile(this.errorLogPath, errorEntry);

      // Log to Winston
      this.logger.error('Error stored', {
        errorId: errorEntry.id,
        category: errorData.categorization?.category,
        severity: errorData.categorization?.severity,
        message: errorData.originalError?.message
      });

      return errorEntry.id;
    } catch (error) {
      console.error('Failed to store error:', error);
      throw error;
    }
  }

  /**
   * Store detected patterns
   * @param {Array} patterns - Array of pattern objects
   * @returns {Promise<boolean>} - Success status
   */
  async storePatterns(patterns) {
    try {
      const patternData = {
        timestamp: new Date().toISOString(),
        patterns: patterns,
        metadata: {
          version: '1.0',
          totalPatterns: patterns.length
        }
      };

      await this._writeToFile(this.patternPath, patternData);
      return true;
    } catch (error) {
      console.error('Failed to store patterns:', error);
      return false;
    }
  }

  /**
   * Store metrics data
   * @param {Object} metrics - Metrics object
   * @returns {Promise<boolean>} - Success status
   */
  async storeMetrics(metrics) {
    try {
      const metricsEntry = {
        timestamp: new Date().toISOString(),
        ...metrics
      };

      await this._appendToFile(this.metricsPath, metricsEntry);
      return true;
    } catch (error) {
      console.error('Failed to store metrics:', error);
      return false;
    }
  }

  /**
   * Retrieve errors with filtering options
   * @param {Object} filters - Filter options
   * @returns {Promise<Array>} - Array of filtered errors
   */
  async getErrors(filters = {}) {
    try {
      const errors = await this._readFromFile(this.errorLogPath, true);

      return this._filterErrors(errors, filters);
    } catch (error) {
      console.error('Failed to retrieve errors:', error);
      return [];
    }
  }

  /**
   * Retrieve stored patterns
   * @returns {Promise<Array>} - Array of patterns
   */
  async getPatterns() {
    try {
      const patternData = await this._readFromFile(this.patternPath);
      return patternData?.patterns || [];
    } catch (error) {
      console.error('Failed to retrieve patterns:', error);
      return [];
    }
  }

  /**
   * Retrieve metrics data
   * @param {Object} options - Query options
   * @returns {Promise<Array>} - Array of metrics
   */
  async getMetrics(options = {}) {
    try {
      const metrics = await this._readFromFile(this.metricsPath, true);

      if (options.limit) {
        return metrics.slice(-options.limit);
      }

      return metrics;
    } catch (error) {
      console.error('Failed to retrieve metrics:', error);
      return [];
    }
  }

  /**
   * Get error statistics
   * @param {Object} timeRange - Time range for statistics
   * @returns {Promise<Object>} - Statistics object
   */
  async getErrorStats(timeRange = {}) {
    try {
      const errors = await this.getErrors(timeRange);

      const stats = {
        total: errors.length,
        byCategory: {},
        bySeverity: {},
        byTimeRange: {},
        patterns: 0
      };

      errors.forEach(error => {
        const cat = error.categorization?.category || 'UNKNOWN';
        const severity = error.categorization?.severity || 'UNKNOWN';

        stats.byCategory[cat] = (stats.byCategory[cat] || 0) + 1;
        stats.bySeverity[severity] = (stats.bySeverity[severity] || 0) + 1;

        if (error.patterns && error.patterns.length > 0) {
          stats.patterns++;
        }
      });

      return stats;
    } catch (error) {
      console.error('Failed to get error statistics:', error);
      return {};
    }
  }

  /**
   * Clean up old data based on retention policy
   * @returns {Promise<Object>} - Cleanup result
   */
  async cleanup() {
    try {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - this.config.retentionDays);

      const errors = await this._readFromFile(this.errorLogPath, true);
      const metrics = await this._readFromFile(this.metricsPath, true);

      const filteredErrors = errors.filter(error =>
        new Date(error.timestamp) > cutoffDate
      );

      const filteredMetrics = metrics.filter(metric =>
        new Date(metric.timestamp) > cutoffDate
      );

      // Write filtered data back
      await this._writeToFile(this.errorLogPath, filteredErrors, true);
      await this._writeToFile(this.metricsPath, filteredMetrics, true);

      return {
        errorsRemoved: errors.length - filteredErrors.length,
        metricsRemoved: metrics.length - filteredMetrics.length,
        cutoffDate: cutoffDate.toISOString()
      };
    } catch (error) {
      console.error('Failed to cleanup old data:', error);
      return { error: error.message };
    }
  }

  /**
   * Search errors by text query
   * @param {string} query - Search query
   * @param {Object} options - Search options
   * @returns {Promise<Array>} - Array of matching errors
   */
  async searchErrors(query, options = {}) {
    try {
      const errors = await this.getErrors();
      const searchFields = options.fields || ['originalError.message', 'categorization.category'];

      return errors.filter(error => {
        return searchFields.some(field => {
          const value = this._getNestedValue(error, field);
          return value && value.toLowerCase().includes(query.toLowerCase());
        });
      });
    } catch (error) {
      console.error('Failed to search errors:', error);
      return [];
    }
  }

  /**
   * Export data for backup or analysis
   * @param {string} format - Export format (json, csv)
   * @returns {Promise<string>} - Export data
   */
  async exportData(format = 'json') {
    try {
      const data = {
        errors: await this.getErrors(),
        patterns: await this.getPatterns(),
        metrics: await this.getMetrics(),
        exportTimestamp: new Date().toISOString()
      };

      if (format === 'json') {
        return JSON.stringify(data, null, 2);
      }

      // Add CSV export logic if needed
      throw new Error(`Export format '${format}' not supported`);
    } catch (error) {
      console.error('Failed to export data:', error);
      throw error;
    }
  }

  /**
   * Get storage health status
   * @returns {Promise<Object>} - Health status
   */
  async getHealthStatus() {
    try {
      const stats = await Promise.all([
        fs.stat(this.errorLogPath).catch(() => null),
        fs.stat(this.patternPath).catch(() => null),
        fs.stat(this.metricsPath).catch(() => null)
      ]);

      return {
        status: 'healthy',
        files: {
          errors: {
            exists: !!stats[0],
            size: stats[0]?.size || 0,
            lastModified: stats[0]?.mtime || null
          },
          patterns: {
            exists: !!stats[1],
            size: stats[1]?.size || 0,
            lastModified: stats[1]?.mtime || null
          },
          metrics: {
            exists: !!stats[2],
            size: stats[2]?.size || 0,
            lastModified: stats[2]?.mtime || null
          }
        },
        diskSpace: await this._getDiskSpace()
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message
      };
    }
  }

  // Private methods

  /**
   * Setup Winston logger
   */
  _setupLogger() {
    return winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.File({
          filename: path.join(this.config.baseDir, 'error-dna.log'),
          maxsize: 10 * 1024 * 1024, // 10MB
          maxFiles: 5
        })
      ]
    });
  }

  /**
   * Initialize storage files
   */
  async _initializeStorageFiles() {
    const files = [
      { path: this.errorLogPath, content: [] },
      { path: this.patternPath, content: { patterns: [] } },
      { path: this.metricsPath, content: [] }
    ];

    for (const file of files) {
      if (!(await fs.pathExists(file.path))) {
        await this._writeToFile(file.path, file.content, Array.isArray(file.content));
      }
    }
  }

  /**
   * Append data to a JSON file
   */
  async _appendToFile(filePath, data) {
    const existing = await this._readFromFile(filePath, true);
    existing.push(data);
    await this._writeToFile(filePath, existing, true);
  }

  /**
   * Write data to a JSON file
   */
  async _writeToFile(filePath, data, isArray = false) {
    const content = isArray ? data : data;
    await fs.writeJson(filePath, content, { spaces: 2 });
  }

  /**
   * Read data from a JSON file
   */
  async _readFromFile(filePath, isArray = false) {
    try {
      if (!(await fs.pathExists(filePath))) {
        return isArray ? [] : {};
      }

      return await fs.readJson(filePath);
    } catch (error) {
      console.warn(`Failed to read file ${filePath}:`, error.message);
      return isArray ? [] : {};
    }
  }

  /**
   * Filter errors based on criteria
   */
  _filterErrors(errors, filters) {
    return errors.filter(error => {
      // Time range filter
      if (filters.startTime && new Date(error.timestamp) < new Date(filters.startTime)) {
        return false;
      }
      if (filters.endTime && new Date(error.timestamp) > new Date(filters.endTime)) {
        return false;
      }

      // Category filter
      if (filters.category && error.categorization?.category !== filters.category) {
        return false;
      }

      // Severity filter
      if (filters.severity && error.categorization?.severity !== filters.severity) {
        return false;
      }

      // Pattern filter
      if (filters.hasPatterns !== undefined) {
        const hasPatterns = error.patterns && error.patterns.length > 0;
        if (filters.hasPatterns !== hasPatterns) {
          return false;
        }
      }

      return true;
    });
  }

  /**
   * Get nested object value by path
   */
  _getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  /**
   * Generate unique ID
   */
  _generateId() {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get disk space information
   */
  async _getDiskSpace() {
    try {
      const stats = await fs.statSync(this.config.baseDir);
      return {
        available: 'unknown', // Would need additional library for accurate disk space
        total: 'unknown'
      };
    } catch (error) {
      return { error: error.message };
    }
  }
}

module.exports = ErrorStorage;