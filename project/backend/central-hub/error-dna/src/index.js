const express = require('express');
const path = require('path');
const cron = require('node-cron');

// Import ErrorDNA components
const ErrorCategorizer = require('./categorizer');
const PatternDetector = require('./pattern-detector');
const ErrorStorage = require('./storage');
const ErrorLogger = require('./logger');
const ErrorNotifier = require('./notifier');
const ErrorRecovery = require('./recovery');
const SystemIntegration = require('./integration');

// Import configuration
const config = require('../config/config');

class ErrorDNA {
  constructor(customConfig = {}) {
    this.config = { ...config, ...customConfig };
    this.isInitialized = false;
    this.startTime = Date.now();

    // Initialize components
    this.categorizer = null;
    this.patternDetector = null;
    this.storage = null;
    this.logger = null;
    this.notifier = null;
    this.recovery = null;
    this.integration = null;

    // Express app for API
    this.app = express();
    this.server = null;

    // Metrics
    this.metrics = {
      errorsProcessed: 0,
      patternsDetected: 0,
      recoveriesAttempted: 0,
      notificationsSent: 0,
      uptime: 0
    };
  }

  /**
   * Initialize ErrorDNA system
   */
  async init() {
    try {
      console.log('Initializing ErrorDNA system...');

      // Initialize components
      await this._initializeComponents();

      // Setup Express API
      this._setupAPI();

      // Setup scheduled tasks
      this._setupScheduledTasks();

      // Register with external systems
      await this._registerWithSystems();

      this.isInitialized = true;
      console.log('ErrorDNA system initialized successfully');

      return { success: true };
    } catch (error) {
      console.error('Failed to initialize ErrorDNA:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Start the ErrorDNA service
   */
  async start() {
    if (!this.isInitialized) {
      const initResult = await this.init();
      if (!initResult.success) {
        throw new Error('Failed to initialize ErrorDNA');
      }
    }

    return new Promise((resolve, reject) => {
      this.server = this.app.listen(this.config.service.port, (error) => {
        if (error) {
          reject(error);
        } else {
          console.log(`ErrorDNA service running on port ${this.config.service.port}`);
          this.logger.logEvent('service_started', {
            port: this.config.service.port,
            environment: this.config.service.environment
          });
          resolve({ port: this.config.service.port });
        }
      });
    });
  }

  /**
   * Stop the ErrorDNA service
   */
  async stop() {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          console.log('ErrorDNA service stopped');
          this.logger?.logEvent('service_stopped');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }

  /**
   * Process an error through the ErrorDNA pipeline
   * @param {Object} error - Error object to process
   * @param {Object} context - Additional context
   * @returns {Promise<Object>} - Processing result
   */
  async processError(error, context = {}) {
    try {
      const errorId = this._generateErrorId();
      const processingStart = Date.now();

      console.log(`Processing error ${errorId}:`, error.message || 'Unknown error');

      // Step 1: Categorize the error
      const categorization = this.categorizer.categorize(error);

      // Step 2: Detect patterns
      const patternResult = this.patternDetector.addError({
        id: errorId,
        originalError: error,
        categorization,
        context
      });

      // Step 3: Attempt recovery if enabled
      let recoveryResult = null;
      if (this.config.recovery.enabled && categorization.severity !== 'LOW') {
        recoveryResult = await this.recovery.attemptRecovery(
          { id: errorId, originalError: error, categorization },
          context
        );
        this.metrics.recoveriesAttempted++;
      }

      // Step 4: Store error data
      const errorData = {
        id: errorId,
        originalError: error,
        categorization,
        patterns: [
          ...patternResult.newPatterns,
          ...patternResult.existingPatterns
        ],
        recovery: recoveryResult,
        context,
        metadata: {
          processingTime: Date.now() - processingStart,
          timestamp: new Date().toISOString()
        }
      };

      await this.storage.storeError(errorData);

      // Step 5: Log the error
      this.logger.logError(errorData);

      // Step 6: Send notifications if needed
      if (this._shouldNotify(categorization, patternResult)) {
        const notificationResult = await this.notifier.notify(errorData);
        if (notificationResult.success) {
          this.metrics.notificationsSent++;
        }
      }

      // Step 7: Send to external systems
      if (this.integration) {
        await this.integration.sendErrorToCentralHub(errorData);
      }

      // Update metrics
      this.metrics.errorsProcessed++;
      if (patternResult.newPatterns.length > 0) {
        this.metrics.patternsDetected++;
      }

      return {
        success: true,
        errorId,
        categorization,
        patterns: patternResult,
        recovery: recoveryResult,
        processingTime: Date.now() - processingStart
      };

    } catch (processingError) {
      console.error('Error processing failed:', processingError);
      return {
        success: false,
        error: processingError.message
      };
    }
  }

  /**
   * Get system health status
   */
  async getHealth() {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: Date.now() - this.startTime,
      metrics: { ...this.metrics, uptime: Date.now() - this.startTime },
      components: {},
      integrations: {}
    };

    try {
      // Check storage health
      health.components.storage = await this.storage.getHealthStatus();

      // Check pattern detector
      health.components.patternDetector = {
        status: 'healthy',
        patternsCount: this.patternDetector.getPatterns().length,
        errorHistoryCount: this.patternDetector.getErrorHistory().length
      };

      // Check recovery system
      health.components.recovery = {
        status: 'healthy',
        stats: this.recovery.getStats()
      };

      // Check notifier
      health.components.notifier = {
        status: 'healthy',
        queueStatus: this.notifier.getQueueStatus()
      };

      // Check integrations
      if (this.integration) {
        health.integrations = await this.integration.checkIntegrationHealth();
      }

      // Determine overall health
      const componentStatuses = Object.values(health.components).map(c => c.status);
      const integrationStatuses = Object.values(health.integrations).map(i => i.status);

      if ([...componentStatuses, ...integrationStatuses].some(status => status === 'unhealthy')) {
        health.status = 'degraded';
      }

    } catch (error) {
      health.status = 'unhealthy';
      health.error = error.message;
    }

    return health;
  }

  // Private methods

  /**
   * Initialize all ErrorDNA components
   * @private
   */
  async _initializeComponents() {
    // Initialize categorizer
    this.categorizer = new ErrorCategorizer();
    await this.categorizer.init();

    // Initialize pattern detector
    this.patternDetector = new PatternDetector(this.config.patternDetection);

    // Initialize storage
    this.storage = new ErrorStorage(this.config.storage);
    await this.storage.init();

    // Initialize logger
    this.logger = new ErrorLogger(this.config.logging);

    // Initialize notifier
    this.notifier = new ErrorNotifier(this.config.notifications);

    // Initialize recovery
    this.recovery = new ErrorRecovery(this.config.recovery);

    // Initialize integration
    this.integration = new SystemIntegration(this.config.integration);
  }

  /**
   * Setup Express API routes
   * @private
   */
  _setupAPI() {
    this.app.use(express.json());

    // Health endpoint
    this.app.get('/health', async (req, res) => {
      const health = await this.getHealth();
      res.status(health.status === 'healthy' ? 200 : 503).json(health);
    });

    // Process error endpoint
    this.app.post('/api/errors', async (req, res) => {
      try {
        const result = await this.processError(req.body.error, req.body.context);
        res.json(result);
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Get errors endpoint
    this.app.get('/api/errors', async (req, res) => {
      try {
        const errors = await this.storage.getErrors(req.query);
        res.json({ success: true, errors });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Get patterns endpoint
    this.app.get('/api/patterns', async (req, res) => {
      try {
        const patterns = this.patternDetector.getPatterns();
        res.json({ success: true, patterns });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Get metrics endpoint
    this.app.get('/api/metrics', async (req, res) => {
      try {
        const metrics = {
          ...this.metrics,
          uptime: Date.now() - this.startTime,
          storage: await this.storage.getErrorStats(),
          patterns: this.patternDetector.getPatternStats(),
          recovery: this.recovery.getStats(),
          integrations: this.integration.getIntegrationStats()
        };
        res.json({ success: true, metrics });
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Import error endpoint (for Import Manager integration)
    this.app.post('/api/import-errors', async (req, res) => {
      try {
        const result = await this.integration.handleImportError(req.body);
        if (result.success) {
          // Process the standardized error
          const processResult = await this.processError(result.standardError.originalError, result.standardError.context);
          res.json({ success: true, processResult, acknowledgment: result.acknowledgment });
        } else {
          res.status(500).json(result);
        }
      } catch (error) {
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Error handler
    this.app.use((error, req, res, next) => {
      console.error('API Error:', error);
      res.status(500).json({ success: false, error: 'Internal server error' });
    });
  }

  /**
   * Setup scheduled tasks
   * @private
   */
  _setupScheduledTasks() {
    // Cleanup old data daily
    cron.schedule('0 2 * * *', async () => {
      try {
        const cleanupResult = await this.storage.cleanup();
        this.logger.logEvent('scheduled_cleanup', cleanupResult);
      } catch (error) {
        console.error('Scheduled cleanup failed:', error);
      }
    });

    // Send health status every 5 minutes
    cron.schedule('*/5 * * * *', async () => {
      try {
        const health = await this.getHealth();
        if (this.integration) {
          await this.integration.sendHealthStatus(health);
        }
      } catch (error) {
        console.error('Health status update failed:', error);
      }
    });

    // Store patterns every hour
    cron.schedule('0 * * * *', async () => {
      try {
        const patterns = this.patternDetector.getPatterns();
        await this.storage.storePatterns(patterns);
        this.logger.logEvent('patterns_stored', { count: patterns.length });
      } catch (error) {
        console.error('Pattern storage failed:', error);
      }
    });
  }

  /**
   * Register with external systems
   * @private
   */
  async _registerWithSystems() {
    if (!this.integration) return;

    try {
      // Register with Central Hub
      const centralHubResult = await this.integration.registerWithCentralHub();
      if (centralHubResult.success) {
        this.logger.logEvent('registered_with_central_hub', centralHubResult);
      }

      // Register with Import Manager
      const importManagerResult = await this.integration.registerWithImportManager();
      if (importManagerResult.success) {
        this.logger.logEvent('registered_with_import_manager', importManagerResult);
      }
    } catch (error) {
      console.warn('System registration failed:', error.message);
    }
  }

  /**
   * Determine if notification should be sent
   * @private
   */
  _shouldNotify(categorization, patternResult) {
    const severity = categorization?.severity;
    const severityConfig = this.config.notifications.channels;

    // Always notify for critical errors
    if (severity === 'CRITICAL') return true;

    // Notify for new patterns
    if (patternResult.newPatterns.length > 0) return true;

    // Notify for anomalies
    if (patternResult.anomalies.length > 0) return true;

    // Check severity thresholds (simplified)
    return severity === 'HIGH';
  }

  /**
   * Generate unique error ID
   * @private
   */
  _generateErrorId() {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export both the class and a default instance
module.exports = ErrorDNA;

// If this file is run directly, start the service
if (require.main === module) {
  const errorDNA = new ErrorDNA();

  errorDNA.start()
    .then(result => {
      console.log('ErrorDNA service started successfully:', result);
    })
    .catch(error => {
      console.error('Failed to start ErrorDNA service:', error);
      process.exit(1);
    });

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\nShutting down ErrorDNA service...');
    await errorDNA.stop();
    process.exit(0);
  });

  process.on('SIGTERM', async () => {
    console.log('\nShutting down ErrorDNA service...');
    await errorDNA.stop();
    process.exit(0);
  });
}