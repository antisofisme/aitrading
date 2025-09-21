/**
 * Legacy Database Configuration
 * This file is kept for backward compatibility
 * New implementations should use the DatabaseService from ../database/DatabaseService.js
 */

const DatabaseService = require('../database/DatabaseService');
const winston = require('winston');

// Logger configuration
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/database.log' })
  ]
});

// Legacy wrapper for backward compatibility
class DatabaseConfig {
  constructor() {
    this.databaseService = new DatabaseService();
    this.isConnected = false;
    this.postgresDb = null;

    logger.warn('Using legacy DatabaseConfig - consider migrating to DatabaseService for multi-database support');
  }

  async initialize() {
    try {
      await this.databaseService.initialize();
      this.postgresDb = this.databaseService.getDatabase('postgresql');
      this.isConnected = true;

      logger.info('Legacy database connection established successfully');
      return this.postgresDb;
    } catch (error) {
      logger.error('Failed to initialize legacy database connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async query(text, params) {
    if (!this.isConnected || !this.postgresDb) {
      throw new Error('Database not connected');
    }

    try {
      const result = await this.postgresDb.query(text, params);
      return {
        rows: result.rows,
        rowCount: result.rowCount,
        fields: result.fields,
        command: result.command,
        oid: result.oid
      };
    } catch (error) {
      logger.error('Query error:', { error: error.message, query: text });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected || !this.postgresDb) {
      throw new Error('Database not connected');
    }
    return await this.postgresDb.getClient();
  }

  async close() {
    if (this.databaseService) {
      await this.databaseService.shutdown();
      this.isConnected = false;
      logger.info('Legacy database connection closed');
    }
  }

  getStatus() {
    if (!this.isConnected || !this.postgresDb) {
      return {
        connected: false,
        totalCount: 0,
        idleCount: 0,
        waitingCount: 0
      };
    }

    const status = this.postgresDb.getStatus();
    return {
      connected: status.connected,
      totalCount: status.totalCount || 0,
      idleCount: status.idleCount || 0,
      waitingCount: status.waitingCount || 0
    };
  }

  // Expose the full database service for advanced usage
  getDatabaseService() {
    return this.databaseService;
  }
}

module.exports = DatabaseConfig;