/**
 * Database Manager Interface
 * Unified interface for all database types in the multi-database architecture
 */

class IDatabaseManager {
  constructor() {
    if (this.constructor === IDatabaseManager) {
      throw new Error('IDatabaseManager is an abstract class and cannot be instantiated directly');
    }
  }

  /**
   * Initialize database connection
   * @returns {Promise<void>}
   */
  async initialize() {
    throw new Error('initialize() method must be implemented');
  }

  /**
   * Execute query/operation
   * @param {string|Object} query - Query string or query object
   * @param {Array} params - Query parameters
   * @returns {Promise<any>}
   */
  async query(query, params = []) {
    throw new Error('query() method must be implemented');
  }

  /**
   * Get database connection client
   * @returns {Promise<any>}
   */
  async getClient() {
    throw new Error('getClient() method must be implemented');
  }

  /**
   * Close database connection
   * @returns {Promise<void>}
   */
  async close() {
    throw new Error('close() method must be implemented');
  }

  /**
   * Get database health status
   * @returns {Object}
   */
  getStatus() {
    throw new Error('getStatus() method must be implemented');
  }

  /**
   * Perform health check
   * @returns {Promise<Object>}
   */
  async healthCheck() {
    throw new Error('healthCheck() method must be implemented');
  }

  /**
   * Get database type identifier
   * @returns {string}
   */
  getType() {
    throw new Error('getType() method must be implemented');
  }

  /**
   * Get connection configuration
   * @returns {Object}
   */
  getConfig() {
    throw new Error('getConfig() method must be implemented');
  }

  /**
   * Begin transaction (if supported)
   * @returns {Promise<any>}
   */
  async beginTransaction() {
    throw new Error('beginTransaction() method must be implemented');
  }

  /**
   * Commit transaction (if supported)
   * @param {any} transaction - Transaction object
   * @returns {Promise<void>}
   */
  async commitTransaction(transaction) {
    throw new Error('commitTransaction() method must be implemented');
  }

  /**
   * Rollback transaction (if supported)
   * @param {any} transaction - Transaction object
   * @returns {Promise<void>}
   */
  async rollbackTransaction(transaction) {
    throw new Error('rollbackTransaction() method must be implemented');
  }
}

module.exports = IDatabaseManager;