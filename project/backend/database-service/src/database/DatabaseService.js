/**
 * Main Database Service
 * Central orchestrator for the multi-database architecture
 */

const UnifiedDatabaseInterface = require('./UnifiedDatabaseInterface');
const HealthMonitor = require('./health/HealthMonitor');
const ConnectionPoolManager = require('./utils/ConnectionPoolManager');
const TransactionCoordinator = require('./utils/TransactionCoordinator');
const DatabaseFactory = require('./factories/DatabaseFactory');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/database-service.log' })
  ]
});

class DatabaseService {
  constructor() {
    this.factory = new DatabaseFactory();
    this.unifiedInterface = new UnifiedDatabaseInterface();
    this.healthMonitor = new HealthMonitor(this.factory);
    this.poolManager = new ConnectionPoolManager();
    this.transactionCoordinator = new TransactionCoordinator(this.factory);

    this.initialized = false;
    this.services = {
      healthMonitoring: false,
      poolManagement: false,
      transactionCoordination: true
    };

    this.setupEventHandlers();
  }

  /**
   * Initialize the database service
   * @param {Object} options - Initialization options
   */
  async initialize(options = {}) {
    try {
      logger.info('Initializing Database Service...');

      // Initialize core components
      await this.factory.initializeAll();
      await this.unifiedInterface.initialize();

      // Register pools with pool manager
      this.factory.getAllDatabases().forEach((database, type) => {
        this.poolManager.registerPool(type, database);
      });

      // Start optional services
      if (options.enableHealthMonitoring !== false) {
        this.healthMonitor.startMonitoring(options.healthCheckInterval);
        this.services.healthMonitoring = true;
      }

      if (options.enablePoolManagement !== false) {
        this.poolManager.startMonitoring(options.poolMonitoringInterval);
        this.services.poolManagement = true;
      }

      this.initialized = true;

      logger.info('Database Service initialized successfully', {
        databases: this.factory.getSupportedTypes(),
        services: this.services
      });

      return {
        success: true,
        databases: this.factory.getSupportedTypes(),
        services: this.services
      };
    } catch (error) {
      logger.error('Failed to initialize Database Service:', error);
      throw error;
    }
  }

  /**
   * Setup event handlers for monitoring and coordination
   */
  setupEventHandlers() {
    // Health monitoring events
    this.healthMonitor.on('database_alert', (alert) => {
      logger.warn('Database health alert:', alert);
      this.handleHealthAlert(alert);
    });

    this.healthMonitor.on('health_check_completed', (summary) => {
      logger.debug('Health check completed:', {
        healthy: summary.healthy,
        unhealthy: summary.unhealthy,
        degraded: summary.degraded
      });
    });

    // Pool management events
    this.poolManager.on('pool_alert', (alert) => {
      logger.warn('Pool management alert:', alert);
      this.handlePoolAlert(alert);
    });

    // Transaction coordination events
    this.transactionCoordinator.on('transaction_partially_committed', (event) => {
      logger.error('Critical: Transaction partially committed:', event);
      // Implement recovery procedures
    });

    this.transactionCoordinator.on('transaction_timeout', (event) => {
      logger.warn('Transaction timeout:', event);
    });
  }

  /**
   * Handle health alerts
   */
  async handleHealthAlert(alert) {
    switch (alert.type) {
      case 'consecutive_failures':
        if (alert.severity === 'critical') {
          // Attempt to reinitialize the database connection
          await this.reinitializeDatabase(alert.database);
        }
        break;

      case 'high_response_time':
        // Could trigger pool optimization
        this.optimizePoolForDatabase(alert.database);
        break;

      case 'database_unhealthy':
        // Mark database as unavailable in routing
        this.markDatabaseUnavailable(alert.database);
        break;
    }
  }

  /**
   * Handle pool alerts
   */
  async handlePoolAlert(alert) {
    if (alert.type === 'pool_health' && alert.severity === 'critical') {
      const optimization = this.poolManager.optimizePoolConfiguration(alert.database);
      if (optimization && optimization.recommendations.length > 0) {
        logger.info(`Auto-optimizing pool for ${alert.database}:`, optimization.recommendations);
        this.poolManager.applyConfiguration(alert.database, optimization.recommendedConfig);
      }
    }
  }

  /**
   * Reinitialize a specific database
   */
  async reinitializeDatabase(databaseType) {
    try {
      logger.info(`Reinitializing database: ${databaseType}`);

      const database = this.factory.getDatabase(databaseType);
      await database.close();
      await database.initialize();

      logger.info(`Successfully reinitialized ${databaseType}`);
    } catch (error) {
      logger.error(`Failed to reinitialize ${databaseType}:`, error);
    }
  }

  /**
   * Optimize pool for a specific database
   */
  optimizePoolForDatabase(databaseType) {
    const optimization = this.poolManager.optimizePoolConfiguration(databaseType);
    if (optimization && optimization.recommendations.length > 0) {
      logger.info(`Pool optimization suggestions for ${databaseType}:`, optimization.recommendations);
    }
  }

  /**
   * Mark database as unavailable (would integrate with query router)
   */
  markDatabaseUnavailable(databaseType) {
    // This would be implemented with the query router to temporarily
    // route queries away from unhealthy databases
    logger.warn(`Marking ${databaseType} as temporarily unavailable`);
  }

  // === Public API Methods ===

  /**
   * Execute query through unified interface
   */
  async query(queryRequest) {
    if (!this.initialized) {
      throw new Error('Database Service not initialized');
    }
    return await this.unifiedInterface.execute(queryRequest);
  }

  /**
   * Execute cross-database operation
   */
  async executeCrossDatabase(operation) {
    if (!this.initialized) {
      throw new Error('Database Service not initialized');
    }
    return await this.unifiedInterface.executeCrossDatabase(operation);
  }

  /**
   * Begin distributed transaction
   */
  async beginTransaction(databases, options = {}) {
    if (!this.initialized) {
      throw new Error('Database Service not initialized');
    }
    return await this.transactionCoordinator.beginDistributedTransaction(databases, options);
  }

  /**
   * Add operation to transaction
   */
  async addTransactionOperation(transactionId, database, operation, compensation) {
    return await this.transactionCoordinator.addOperation(transactionId, database, operation, compensation);
  }

  /**
   * Commit transaction
   */
  async commitTransaction(transactionId) {
    return await this.transactionCoordinator.commitTransaction(transactionId);
  }

  /**
   * Rollback transaction
   */
  async rollbackTransaction(transactionId) {
    return await this.transactionCoordinator.rollbackTransaction(transactionId);
  }

  /**
   * Get specific database instance
   */
  getDatabase(type) {
    return this.factory.getDatabase(type);
  }

  /**
   * Get service status
   */
  getStatus() {
    if (!this.initialized) {
      return { initialized: false };
    }

    return {
      initialized: this.initialized,
      services: this.services,
      databases: this.factory.getStatus(),
      health: this.healthMonitor.getHealthStatus(),
      pools: this.poolManager.getAllPoolStatuses(),
      transactions: this.transactionCoordinator.getActiveTransactions()
    };
  }

  /**
   * Get comprehensive health status
   */
  async getHealthStatus() {
    if (!this.initialized) {
      return { status: 'not_initialized' };
    }

    const health = await this.factory.healthCheckAll();
    const poolStatus = this.poolManager.getAllPoolStatuses();

    return {
      overall: health.overall,
      timestamp: health.timestamp,
      databases: health.databases,
      pools: poolStatus,
      services: this.services,
      activeTransactions: Object.keys(this.transactionCoordinator.getActiveTransactions()).length
    };
  }

  /**
   * Generate performance report
   */
  generatePerformanceReport() {
    if (!this.initialized) {
      return { error: 'Service not initialized' };
    }

    return {
      timestamp: new Date().toISOString(),
      service: this.getStatus(),
      health: this.healthMonitor.generateHealthReport(),
      pools: this.poolManager.generatePerformanceReport(),
      recommendations: this.generateOptimizationRecommendations()
    };
  }

  /**
   * Generate optimization recommendations
   */
  generateOptimizationRecommendations() {
    const recommendations = [];

    // Analyze pool performance
    this.factory.getSupportedTypes().forEach(type => {
      const optimization = this.poolManager.optimizePoolConfiguration(type);
      if (optimization && optimization.recommendations.length > 0) {
        recommendations.push({
          category: 'connection_pool',
          database: type,
          recommendations: optimization.recommendations,
          priority: 'medium'
        });
      }
    });

    // Analyze health metrics
    const healthMetrics = this.healthMonitor.getHealthMetrics();
    Object.entries(healthMetrics.uptime).forEach(([type, uptime]) => {
      if (uptime < 95) {
        recommendations.push({
          category: 'reliability',
          database: type,
          recommendations: [`Improve reliability for ${type} (current uptime: ${uptime.toFixed(2)}%)`],
          priority: 'high'
        });
      }
    });

    return recommendations;
  }

  /**
   * Shutdown database service
   */
  async shutdown() {
    logger.info('Shutting down Database Service...');

    try {
      // Stop monitoring services
      this.healthMonitor.stopMonitoring();
      this.poolManager.stopMonitoring();

      // Close all database connections
      await this.factory.closeAll();

      // Cleanup
      this.healthMonitor.destroy();
      this.poolManager.destroy();

      this.initialized = false;
      logger.info('Database Service shutdown completed');
    } catch (error) {
      logger.error('Error during Database Service shutdown:', error);
      throw error;
    }
  }

  // === Convenience Methods ===

  async store(data, options = {}) {
    return await this.unifiedInterface.store(data, options);
  }

  async retrieve(criteria, options = {}) {
    return await this.unifiedInterface.retrieve(criteria, options);
  }

  async update(criteria, data, options = {}) {
    return await this.unifiedInterface.update(criteria, data, options);
  }

  async delete(criteria, options = {}) {
    return await this.unifiedInterface.delete(criteria, options);
  }

  async search(query, options = {}) {
    return await this.unifiedInterface.search(query, options);
  }

  async analyze(dataset, analysis, options = {}) {
    return await this.unifiedInterface.analyze(dataset, analysis, options);
  }

  async cache(key, value, ttl = 3600) {
    return await this.unifiedInterface.cache(key, value, ttl);
  }

  async vectorSearch(vector, options = {}) {
    return await this.unifiedInterface.vectorSearch(vector, options);
  }

  async graphQuery(query, options = {}) {
    return await this.unifiedInterface.graphQuery(query, options);
  }

  async timeSeriesQuery(query, options = {}) {
    return await this.unifiedInterface.timeSeriesQuery(query, options);
  }
}

module.exports = DatabaseService;